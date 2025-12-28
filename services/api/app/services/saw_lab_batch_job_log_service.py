from __future__ import annotations

from typing import Any, Dict, Optional


def write_job_log(
    *,
    batch_execution_artifact_id: str,
    operator: str,
    notes: str,
    status: str,
    metrics: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Persist an operator-facing job log tied to a batch execution.
    """
    from app.rmos.run_artifacts.store import read_run_artifact, write_run_artifact

    parent = read_run_artifact(batch_execution_artifact_id)
    if str(getattr(parent, "kind", parent.get("kind", ""))) != "saw_batch_execution":
        raise ValueError("batch_execution_artifact_id must reference saw_batch_execution")

    meta = parent.index_meta if hasattr(parent, "index_meta") else parent.get("index_meta", {})
    meta = meta or {}

    art = write_run_artifact(
        kind="saw_batch_job_log",
        status=status,
        session_id=meta.get("session_id"),
        index_meta={
            "tool_kind": "saw_lab",
            "kind_group": "batch",
            "batch_label": meta.get("batch_label"),
            "session_id": meta.get("session_id"),
            "parent_batch_execution_artifact_id": batch_execution_artifact_id,
            "parent_batch_decision_artifact_id": meta.get("parent_batch_decision_artifact_id"),
            "operator": operator,
        },
        payload={
            "batch_execution_artifact_id": batch_execution_artifact_id,
            "operator": operator,
            "notes": notes,
            "status": status,
            "metrics": metrics or {},
        },
    )

    return art if isinstance(art, dict) else art.__dict__
