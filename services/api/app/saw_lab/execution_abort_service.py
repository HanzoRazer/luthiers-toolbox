from __future__ import annotations

from typing import Any, Dict, Optional


def write_execution_abort_artifact(
    *,
    batch_execution_artifact_id: str,
    session_id: str,
    batch_label: str,
    reason: str,
    notes: Optional[str] = None,
    operator_id: Optional[str] = None,
    tool_kind: str = "saw",
) -> str:
    """
    Persist a first-class abort artifact.

    Artifact kind:
      - saw_batch_execution_abort

    Parent:
      - batch_execution_artifact_id
    """
    if not batch_execution_artifact_id:
        raise ValueError("batch_execution_artifact_id required")
    if not session_id:
        raise ValueError("session_id required")
    if not batch_label:
        raise ValueError("batch_label required")
    if not reason:
        raise ValueError("reason required")

    payload: Dict[str, Any] = {
        "batch_execution_artifact_id": batch_execution_artifact_id,
        "session_id": session_id,
        "batch_label": batch_label,
        "reason": reason,
        "notes": notes,
        "operator_id": operator_id,
        "state": "ABORTED",
    }

    from app.rmos.runs_v2.store import store_artifact

    abort_id = store_artifact(
        kind="saw_batch_execution_abort",
        payload=payload,
        parent_id=batch_execution_artifact_id,
        session_id=session_id,
        batch_label=batch_label,
        tool_kind=tool_kind,
    )

    return abort_id
