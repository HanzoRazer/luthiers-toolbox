from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from .decision_intelligence_service import append_override_jsonl
from .schemas_decision_intelligence import TuningDelta


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass
class ArtifactStorePorts:
    list_runs_filtered: Any
    persist_run_artifact: Any


def _get_items(res: Any) -> List[Dict[str, Any]]:
    if isinstance(res, dict):
        items = res.get("items") or res.get("runs") or res.get("artifacts") or []
        return items if isinstance(items, list) else []
    return res if isinstance(res, list) else []


def find_latest_approved_tuning_decision(
    store: ArtifactStorePorts,
    *,
    tool_id: str,
    material_id: str,
    limit: int = 200,
) -> Tuple[Optional[str], Optional[TuningDelta]]:
    """
    Finds the most recent APPROVED saw_lab_tuning_decision for (tool_id, material_id).

    Requirements:
      - decision artifact kind: "saw_lab_tuning_decision"
      - index_meta.tool_id and index_meta.material_id must be present (this patch adds it when stamping)
      - payload.approved == True
      - payload.effective_delta exists
    """
    try:
        res = store.list_runs_filtered(kind="saw_lab_tuning_decision", limit=limit)
        items = _get_items(res)
    except Exception:
        items = []

    # Filter by meta keys first (fast, stable)
    candidates: List[Dict[str, Any]] = []
    for a in items:
        if not isinstance(a, dict):
            continue
        meta = a.get("index_meta") or {}
        if not isinstance(meta, dict):
            continue
        if meta.get("tool_id") != tool_id:
            continue
        if meta.get("material_id") != material_id:
            continue
        payload = a.get("payload") or a.get("data") or {}
        if not isinstance(payload, dict):
            continue
        if payload.get("approved") is not True:
            continue
        if not isinstance(payload.get("effective_delta"), dict):
            continue
        candidates.append(a)

    if not candidates:
        return None, None

    # Prefer newest by created_utc if present; else first
    def _ts(x: Dict[str, Any]) -> str:
        payload = x.get("payload") or x.get("data") or {}
        if isinstance(payload, dict) and isinstance(payload.get("created_utc"), str):
            return payload["created_utc"]
        if isinstance(x.get("created_utc"), str):
            return x["created_utc"]
        return ""

    candidates.sort(key=_ts, reverse=True)
    best = candidates[0]
    payload = best.get("payload") or best.get("data") or {}
    delta_dict = payload.get("effective_delta") if isinstance(payload, dict) else None
    try:
        delta = TuningDelta(**delta_dict) if isinstance(delta_dict, dict) else None
    except Exception:
        delta = None

    decision_id = str(best.get("id") or best.get("artifact_id") or "")
    return (decision_id if decision_id else None), delta


def persist_plan_intel_link(
    store: ArtifactStorePorts,
    *,
    batch_plan_artifact_id: str,
    tool_id: str,
    material_id: str,
    decision_artifact_id: str,
    effective_delta: TuningDelta,
    stamped_by: str,
    note: Optional[str],
    session_id: Optional[str] = None,
    batch_label: Optional[str] = None,
    write_jsonl: bool = True,
) -> Tuple[str, bool]:
    """
    Creates a governed linkage artifact:
      kind = saw_lab_plan_intel_link
      parent = batch_plan_artifact_id
    so the plan can be audited against the decision intel used.

    Also (optionally) appends a best-effort JSONL entry documenting the applied delta.
    """
    index_meta: Dict[str, Any] = {
        "tool_kind": "saw",
        "tool_id": tool_id,
        "material_id": material_id,
        "parent_batch_plan_artifact_id": batch_plan_artifact_id,
        "parent_decision_artifact_id": decision_artifact_id,
    }
    if session_id:
        index_meta["session_id"] = session_id
    if batch_label:
        index_meta["batch_label"] = batch_label

    payload: Dict[str, Any] = {
        "created_utc": _utc_now_iso(),
        "batch_plan_artifact_id": batch_plan_artifact_id,
        "decision_artifact_id": decision_artifact_id,
        "effective_delta": effective_delta.model_dump(),
        "stamped_by": stamped_by,
        "note": note,
        "policy": {"auto_apply": False, "mode": "apply_on_next_plan", "requires_explicit_approval": True},
    }

    art = store.persist_run_artifact(
        kind="saw_lab_plan_intel_link",
        payload=payload,
        index_meta=index_meta,
        parent_artifact_id=batch_plan_artifact_id,
    )
    link_id = str(art.get("id") or art.get("artifact_id") or "")

    wrote = False
    if write_jsonl:
        wrote = append_override_jsonl(
            {
                "event_type": "saw_lab_plan_delta_applied",
                "created_utc": _utc_now_iso(),
                "batch_plan_artifact_id": batch_plan_artifact_id,
                "decision_artifact_id": decision_artifact_id,
                "tool_id": tool_id,
                "material_id": material_id,
                "delta": effective_delta.model_dump(),
                "stamped_by": stamped_by,
                "note": note,
            }
        )

    return link_id, wrote
