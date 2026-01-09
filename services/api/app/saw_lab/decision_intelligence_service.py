from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from .schemas_decision_intelligence import DecisionIntelSuggestion, TuningDelta


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def _conservative_delta_from_signals(signals: List[str]) -> Tuple[TuningDelta, List[str], float]:
    """
    Heuristic (not ML) — conservative deltas only.
    Signals are expected to be normalized strings like:
      burn, tearout, kickback, chatter, overheating
    """
    signals_set = {s.strip().lower() for s in signals if s}
    rationale: List[str] = []

    rpm_mul = 1.0
    feed_mul = 1.0
    doc_mul = 1.0
    confidence = 0.55

    # Burn typically improves with: reduce RPM a bit, increase feed slightly, reduce DOC slightly
    if "burn" in signals_set or "overheating" in signals_set:
        rpm_mul *= 0.92
        feed_mul *= 1.06
        doc_mul *= 0.92
        rationale.append("Burn/heat signal: reduce RPM slightly, increase feed slightly, reduce DOC slightly.")
        confidence += 0.10

    # Tearout often improves with: reduce feed slightly, reduce DOC slightly
    if "tearout" in signals_set:
        feed_mul *= 0.92
        doc_mul *= 0.92
        rationale.append("Tearout signal: reduce feed and DOC slightly.")
        confidence += 0.08

    # Kickback risk: reduce DOC & feed, and optionally reduce RPM modestly
    if "kickback" in signals_set:
        feed_mul *= 0.90
        doc_mul *= 0.85
        rpm_mul *= 0.95
        rationale.append("Kickback signal: reduce feed and DOC (primary), reduce RPM modestly.")
        confidence += 0.12

    # Chatter/instability: reduce RPM modestly, reduce DOC modestly
    if "chatter" in signals_set:
        rpm_mul *= 0.95
        doc_mul *= 0.92
        rationale.append("Chatter signal: reduce RPM and DOC slightly.")
        confidence += 0.06

    # Conservative clamp ±20%
    delta = TuningDelta(
        rpm_mul=_clamp(rpm_mul, 0.70, 1.20),
        feed_mul=_clamp(feed_mul, 0.70, 1.20),
        doc_mul=_clamp(doc_mul, 0.70, 1.20),
    )
    confidence = _clamp(confidence, 0.0, 1.0)
    if not rationale:
        rationale = ["No strong adverse signals detected; keep baseline tuning (delta = 1.0)."]
        confidence = 0.40
    return delta, rationale, confidence


def _extract_signals_from_job_log(job_log_artifact: Dict[str, Any]) -> List[str]:
    """
    Best-effort extraction from job log artifact payload.
    Expected common shapes:
      payload.metrics.burn == True
      payload.metrics.tearout == True
      payload.notes contains keywords
    """
    signals: List[str] = []
    payload = job_log_artifact.get("payload") or job_log_artifact.get("data") or {}
    if isinstance(payload, dict):
        metrics = payload.get("metrics") or {}
        if isinstance(metrics, dict):
            for k in ("burn", "tearout", "kickback", "chatter", "overheating"):
                if metrics.get(k) is True:
                    signals.append(k)
        notes = payload.get("notes") or payload.get("operator_notes") or ""
        if isinstance(notes, str) and notes:
            low = notes.lower()
            for k in ("burn", "tearout", "kickback", "chatter", "overheat", "overheating"):
                if k in low:
                    signals.append("overheating" if k == "overheat" else k)
    # de-dupe stable order
    out: List[str] = []
    seen = set()
    for s in signals:
        if s not in seen:
            out.append(s)
            seen.add(s)
    return out


def _overrides_path() -> str:
    # already used elsewhere in your repo; default to an innocuous local path if unset
    return os.getenv("SAW_LAB_LEARNED_OVERRIDES_PATH", "services/api/data/saw_lab_learned_overrides.jsonl")


def append_override_jsonl(event: Dict[str, Any]) -> bool:
    """
    Best-effort append to JSONL. Never throws.
    """
    try:
        path = _overrides_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, sort_keys=True) + "\n")
        return True
    except Exception:
        return False


@dataclass
class ArtifactStorePorts:
    """
    Minimal store interface this service needs.
    Your repo already has a RunArtifact store; the router adapts to it.
    """

    list_runs_filtered: Any  # callable(**filters) -> list[dict] OR dict with items
    persist_run_artifact: Any  # callable(kind, payload, index_meta, parent_artifact_id=...) -> dict


def build_suggestion_for_execution(
    store: ArtifactStorePorts,
    *,
    batch_execution_artifact_id: str,
    session_id: Optional[str] = None,
    batch_label: Optional[str] = None,
) -> DecisionIntelSuggestion:
    """
    Reads recent job logs for a given execution id and proposes a conservative tuning delta.
    """
    # Query job logs by parent execution (preferred) or filter by session/batch
    job_logs: List[Dict[str, Any]] = []

    # Try direct filter if available
    try:
        res = store.list_runs_filtered(kind="saw_batch_job_log", parent_artifact_id=batch_execution_artifact_id, limit=50)
        if isinstance(res, dict):
            job_logs = res.get("items") or res.get("runs") or []
        elif isinstance(res, list):
            job_logs = res
    except Exception:
        job_logs = []

    # Fallback: filter by session/batch then choose those with matching parent
    if not job_logs and (session_id or batch_label):
        try:
            res = store.list_runs_filtered(session_id=session_id, batch_label=batch_label, limit=200)
            items = res.get("items") if isinstance(res, dict) else res
            items = items or []
            for a in items:
                if not isinstance(a, dict):
                    continue
                if (a.get("kind") == "saw_batch_job_log") and (
                    (a.get("index_meta") or {}).get("parent_batch_execution_artifact_id") == batch_execution_artifact_id
                    or (a.get("index_meta") or {}).get("parent_artifact_id") == batch_execution_artifact_id
                ):
                    job_logs.append(a)
        except Exception:
            pass

    signals: List[str] = []
    for jl in job_logs:
        for s in _extract_signals_from_job_log(jl):
            if s not in signals:
                signals.append(s)

    delta, rationale, confidence = _conservative_delta_from_signals(signals)

    # Extract material/tool if present in index_meta
    # (execution artifacts usually carry it; if not, still fine)
    # The router can also pass these in.
    return DecisionIntelSuggestion(
        suggestion_id=f"sugg_{batch_execution_artifact_id}",
        batch_execution_artifact_id=batch_execution_artifact_id,
        material_id=None,
        tool_id=None,
        signals=signals,
        rationale=rationale,
        delta=delta,
        confidence=confidence,
    )


def persist_suggestion_artifact(
    store: ArtifactStorePorts,
    *,
    suggestion: DecisionIntelSuggestion,
    index_meta: Dict[str, Any],
    parent_artifact_id: str,
) -> str:
    """
    Persists a governed suggestion artifact (does not change tuning).
    """
    payload = suggestion.model_dump()
    payload["created_utc"] = _utc_now_iso()
    payload["policy"] = {"mode": "decision_intelligence", "auto_apply": False}

    art = store.persist_run_artifact(
        kind="saw_lab_tuning_suggestion",
        payload=payload,
        index_meta=index_meta,
        parent_artifact_id=parent_artifact_id,
    )
    return str(art.get("id") or art.get("artifact_id") or "")


def persist_decision_artifact(
    store: ArtifactStorePorts,
    *,
    suggestion_artifact_id: str,
    approved: bool,
    approved_by: str,
    note: Optional[str],
    effective_delta: Optional[TuningDelta],
    index_meta: Dict[str, Any],
) -> Tuple[str, bool]:
    """
    Persists operator decision. If approved, also appends a JSONL override (best-effort).
    """
    payload: Dict[str, Any] = {
        "created_utc": _utc_now_iso(),
        "approved": approved,
        "approved_by": approved_by,
        "note": note,
        "effective_delta": effective_delta.model_dump() if effective_delta else None,
        "policy": {"auto_apply": False, "requires_explicit_approval": True},
    }

    art = store.persist_run_artifact(
        kind="saw_lab_tuning_decision",
        payload=payload,
        index_meta=index_meta,
        parent_artifact_id=suggestion_artifact_id,
    )
    decision_id = str(art.get("id") or art.get("artifact_id") or "")

    wrote = False
    if approved and effective_delta:
        # Best-effort JSONL — never changes toolpaths automatically.
        wrote = append_override_jsonl(
            {
                "event_type": "saw_lab_override_approved",
                "created_utc": _utc_now_iso(),
                "suggestion_artifact_id": suggestion_artifact_id,
                "decision_artifact_id": decision_id,
                "approved_by": approved_by,
                "delta": effective_delta.model_dump(),
                "index_meta": index_meta,
            }
        )
    return decision_id, wrote


def enrich_index_meta_with_tool_material(index_meta: Dict[str, Any], tool_id: Optional[str], material_id: Optional[str]) -> Dict[str, Any]:
    """
    Small helper so all intel artifacts can be queried by (tool_id, material_id).
    """
    if tool_id:
        index_meta["tool_id"] = tool_id
    if material_id:
        index_meta["material_id"] = material_id
    return index_meta
