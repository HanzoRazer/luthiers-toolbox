from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple


DEFAULT_OVERRIDES_PATH = "services/api/data/saw_lab/learned_overrides.jsonl"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_overrides_path() -> str:
    """
    Configurable learned overrides sink.
    Keep this file in deterministic pathing for CI/test isolation.
    """
    return os.getenv("SAW_LAB_LEARNED_OVERRIDES_PATH", DEFAULT_OVERRIDES_PATH)


def _ensure_parent_dir(p: Path) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)


def _as_dict(x: Any) -> Any:
    if hasattr(x, "model_dump"):
        return x.model_dump()
    if hasattr(x, "dict"):
        return x.dict()
    return x


def _meta(it: Dict[str, Any]) -> Dict[str, Any]:
    m = it.get("index_meta")
    return m if isinstance(m, dict) else {}


def _pick(d: Dict[str, Any], *keys: str, default: Any = None) -> Any:
    for k in keys:
        if k in d and d[k] is not None:
            return d[k]
    return default


def record_operator_feedback_event(
    *,
    job_log_artifact: Dict[str, Any],
    execution_artifact: Dict[str, Any],
    decision_artifact: Optional[Dict[str, Any]] = None,
    policy_decision: str = "PROPOSE",
) -> Dict[str, Any]:
    """
    Convert an operator job log into a small "learning event".

    This does NOT change any production settings automatically.
    It produces:
      - a persisted RunArtifact(kind='saw_lab_learning_event')
      - a JSONL row appended to SAW_LAB_LEARNED_OVERRIDES_PATH (optional, best-effort)
    """
    from app.rmos.run_artifacts.store import write_run_artifact

    jl_payload = job_log_artifact.get("payload") or {}
    if not isinstance(jl_payload, dict):
        jl_payload = {}
    jl_meta = _meta(job_log_artifact)

    ex_payload = execution_artifact.get("payload") or {}
    if not isinstance(ex_payload, dict):
        ex_payload = {}
    ex_meta = _meta(execution_artifact)

    # Canonical IDs
    job_log_id = job_log_artifact.get("artifact_id") or job_log_artifact.get("id")
    exec_id = execution_artifact.get("artifact_id") or execution_artifact.get("id")
    decision_id = None
    if decision_artifact:
        decision_id = decision_artifact.get("artifact_id") or decision_artifact.get("id")
    if not decision_id:
        decision_id = ex_meta.get("parent_batch_decision_artifact_id") or ex_payload.get("batch_decision_artifact_id")

    # Aggregate quick signals
    metrics = jl_payload.get("metrics") or {}
    if not isinstance(metrics, dict):
        metrics = {}

    notes = str(jl_payload.get("notes") or "")
    status = str(_pick(jl_payload, "status", default=job_log_artifact.get("status") or "UNKNOWN")).upper()
    operator = str(_pick(jl_payload, "operator", default=jl_meta.get("operator") or "unknown"))

    # Heuristic flags (simple + transparent; ML comes later)
    burn = bool(metrics.get("burn")) or ("burn" in notes.lower()) or ("scorch" in notes.lower())
    tearout = bool(metrics.get("tearout")) or ("tearout" in notes.lower()) or ("tear out" in notes.lower())
    kickback = bool(metrics.get("kickback_event")) or ("kickback" in notes.lower())

    parts_ok = metrics.get("parts_ok")
    parts_scrap = metrics.get("parts_scrap") or metrics.get("scrap_count")

    # Pull some "context" hints if available (best-effort)
    # We try to find child op toolpaths in execution payload and extract feed/rpm overrides candidates.
    child_summaries = ex_payload.get("results") or []
    if not isinstance(child_summaries, list):
        child_summaries = []

    # Candidate suggestion (super conservative): if burn -> propose slower rpm or higher feed depending on your policy.
    # For now, we only "record" the suggestion in the event.
    suggested = {}
    if burn:
        suggested["hint"] = "burn_detected"
        suggested["suggestion"] = {"spindle_rpm_mult": 0.9, "feed_rate_mult": 1.05}
    elif tearout:
        suggested["hint"] = "tearout_detected"
        suggested["suggestion"] = {"spindle_rpm_mult": 1.05, "feed_rate_mult": 0.95}
    elif kickback:
        suggested["hint"] = "kickback_detected"
        suggested["suggestion"] = {"doc_mult": 0.8, "feed_rate_mult": 0.9}

    event_payload: Dict[str, Any] = {
        "created_utc": _utc_now_iso(),
        "policy_decision": policy_decision,  # PROPOSE | ACCEPT | REJECT (platform can enforce gates later)
        "operator": operator,
        "status": status,
        "signals": {
            "burn": burn,
            "tearout": tearout,
            "kickback": kickback,
        },
        "metrics": {
            "parts_ok": parts_ok,
            "parts_scrap": parts_scrap,
            # keep extra metrics small
            "cut_time_s": metrics.get("cut_time_s") or metrics.get("cut_time_sec"),
            "setup_time_s": metrics.get("setup_time_s") or metrics.get("setup_time_sec"),
        },
        "notes": notes[:2000],
        "suggested_override": suggested or None,
        "refs": {
            "job_log_artifact_id": job_log_id,
            "batch_execution_artifact_id": exec_id,
            "batch_decision_artifact_id": decision_id,
            "batch_plan_artifact_id": ex_meta.get("parent_batch_plan_artifact_id") or ex_payload.get("batch_plan_artifact_id"),
            "batch_spec_artifact_id": ex_meta.get("parent_batch_spec_artifact_id") or ex_payload.get("batch_spec_artifact_id"),
            "batch_label": ex_meta.get("batch_label"),
            "session_id": ex_meta.get("session_id"),
        },
    }

    # Optional: include tool/material hints if the execution payload carries them later.
    # This is forward-compatible and safe to ignore.
    try:
        event_payload["refs"]["tool_id"] = (ex_payload.get("tool_id") if isinstance(ex_payload, dict) else None) or event_payload["refs"].get("tool_id")
        event_payload["refs"]["material_id"] = (ex_payload.get("material_id") if isinstance(ex_payload, dict) else None) or event_payload["refs"].get("material_id")
        event_payload["refs"]["thickness_mm"] = (ex_payload.get("thickness_mm") if isinstance(ex_payload, dict) else None) or event_payload["refs"].get("thickness_mm")
    except (KeyError, TypeError, AttributeError):  # WP-1: narrowed from except Exception
        pass

    art = write_run_artifact(
        kind="saw_lab_learning_event",
        status="OK",
        session_id=ex_meta.get("session_id"),
        index_meta={
            "tool_kind": "saw_lab",
            "kind_group": "learning",
            "batch_label": ex_meta.get("batch_label"),
            "session_id": ex_meta.get("session_id"),
            "parent_batch_execution_artifact_id": exec_id,
            "parent_batch_decision_artifact_id": decision_id,
            "parent_job_log_artifact_id": job_log_id,
            "operator": operator,
            "signal_burn": burn,
            "signal_tearout": tearout,
            "signal_kickback": kickback,
        },
        payload=event_payload,
    )

    # Best-effort JSONL append (never fail the request because the file can't be written)
    try:
        path = Path(_get_overrides_path())
        _ensure_parent_dir(path)
        row = {
            "ts_utc": event_payload["created_utc"],
            "operator": operator,
            "signals": event_payload["signals"],
            "suggested_override": event_payload["suggested_override"],
            "refs": event_payload["refs"],
        }
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        event_payload["jsonl_written_to"] = str(path)
    except (OSError, ValueError, TypeError) as e:  # WP-1: narrowed from except Exception
        event_payload["jsonl_write_error"] = f"{type(e).__name__}: {e}"

    return art if isinstance(art, dict) else art.__dict__
