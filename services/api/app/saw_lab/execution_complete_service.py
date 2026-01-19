from __future__ import annotations

from typing import Any, Dict, Optional


def write_execution_complete_artifact(
    *,
    batch_execution_artifact_id: str,
    session_id: str,
    batch_label: str,
    notes: Optional[str] = None,
    operator_id: Optional[str] = None,
    tool_kind: str = "saw",
    checklist: Optional[Dict[str, bool]] = None,
    statistics: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Persist a first-class execution complete artifact.

    Artifact kind:
      - saw_batch_execution_complete

    Parent:
      - batch_execution_artifact_id

    Checklist (optional, all must be True):
      - all_cuts_complete
      - material_removed
      - workpiece_inspected
      - area_cleared
    """
    if not batch_execution_artifact_id:
        raise ValueError("batch_execution_artifact_id required")
    if not session_id:
        raise ValueError("session_id required")
    if not batch_label:
        raise ValueError("batch_label required")

    # Validate checklist if provided
    if checklist:
        failed = [k for k, v in checklist.items() if v is not True]
        if failed:
            raise ValueError(f"checklist items not satisfied: {failed}")

    payload: Dict[str, Any] = {
        "batch_execution_artifact_id": batch_execution_artifact_id,
        "session_id": session_id,
        "batch_label": batch_label,
        "notes": notes,
        "operator_id": operator_id,
        "state": "COMPLETE",
    }

    if checklist:
        payload["checklist"] = checklist

    if statistics:
        payload["statistics"] = statistics

    from app.rmos.runs_v2.store import store_artifact

    complete_id = store_artifact(
        kind="saw_batch_execution_complete",
        payload=payload,
        parent_id=batch_execution_artifact_id,
        session_id=session_id,
        batch_label=batch_label,
        tool_kind=tool_kind,
    )

    return complete_id
