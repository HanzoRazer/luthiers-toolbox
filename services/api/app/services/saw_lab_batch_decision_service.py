"""
Saw Lab Batch Decision Service

Creates decision artifacts when an operator approves a batch plan
with a specific setup/op execution order.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_batch_plan_decision(
    *,
    batch_plan_artifact_id: str,
    approved_by: str,
    reason: Optional[str] = None,
    setup_order: Optional[List[str]] = None,
    op_order: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Create a decision artifact recording operator approval of a batch plan.

    Args:
        batch_plan_artifact_id: The plan artifact being approved
        approved_by: Who approved it
        reason: Optional reason for approval
        setup_order: Ordered list of setup_keys
        op_order: Ordered list of op_ids

    Returns:
        Dict with batch_decision_artifact_id and metadata
    """
    from app.rmos.run_artifacts.store import read_run_artifact, write_run_artifact

    # Read the plan to get metadata
    plan = read_run_artifact(batch_plan_artifact_id)
    plan_payload = plan.get("payload") or {}
    plan_meta = plan.get("index_meta") or {}

    batch_label = plan_meta.get("batch_label") or plan_payload.get("batch_label")
    session_id = plan_meta.get("session_id") or plan_payload.get("session_id")
    spec_id = plan_meta.get("parent_batch_spec_artifact_id") or plan_payload.get("batch_spec_artifact_id")

    payload = {
        "created_utc": _utc_now_iso(),
        "batch_plan_artifact_id": batch_plan_artifact_id,
        "batch_spec_artifact_id": spec_id,
        "batch_label": batch_label,
        "session_id": session_id,
        "approved_by": approved_by,
        "reason": reason,
        "chosen_order": {
            "setup_order": setup_order or [],
            "op_order": op_order or [],
        },
    }

    art = write_run_artifact(
        kind="saw_batch_decision",
        status="OK",
        session_id=session_id,
        index_meta={
            "tool_kind": "saw_lab",
            "kind_group": "batch",
            "batch_label": batch_label,
            "session_id": session_id,
            "parent_batch_plan_artifact_id": batch_plan_artifact_id,
            "parent_batch_spec_artifact_id": spec_id,
            "approved_by": approved_by,
        },
        payload=payload,
    )

    artifact_id = art.get("artifact_id") if isinstance(art, dict) else getattr(art, "artifact_id", None)

    return {
        "batch_decision_artifact_id": artifact_id,
        "batch_plan_artifact_id": batch_plan_artifact_id,
        "batch_spec_artifact_id": spec_id,
        "batch_label": batch_label,
        "session_id": session_id,
        "status": "OK",
    }
