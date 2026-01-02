from __future__ import annotations

from typing import Any, Dict, Optional


def _as_dict(x: Any) -> Dict[str, Any]:
    if isinstance(x, dict):
        return x
    if hasattr(x, "model_dump"):
        return x.model_dump()
    if hasattr(x, "dict"):
        return x.dict()
    return getattr(x, "__dict__", {}) or {}


def create_learning_decision(
    *,
    learning_event_artifact_id: str,
    policy_decision: str,
    approved_by: str,
    reason: str = "",
) -> Dict[str, Any]:
    """
    Governance-safe "decision" for a learning event.
    Never mutates the original learning event artifact.

    Writes:
      kind='saw_lab_learning_decision'
    """
    from app.rmos.run_artifacts.store import read_run_artifact, write_run_artifact

    ev = read_run_artifact(learning_event_artifact_id)
    ev_d = _as_dict(ev)
    if str(ev_d.get("kind") or "") != "saw_lab_learning_event":
        raise ValueError("learning_event_artifact_id must reference kind='saw_lab_learning_event'")

    ev_meta = ev_d.get("index_meta") or {}
    if not isinstance(ev_meta, dict):
        ev_meta = {}
    ev_payload = ev_d.get("payload") or {}
    if not isinstance(ev_payload, dict):
        ev_payload = {}

    pd = str(policy_decision or "").upper().strip()
    if pd not in ("PROPOSE", "ACCEPT", "REJECT"):
        raise ValueError("policy_decision must be one of PROPOSE|ACCEPT|REJECT")

    art = write_run_artifact(
        kind="saw_lab_learning_decision",
        status="OK",
        session_id=ev_meta.get("session_id"),
        index_meta={
            "tool_kind": "saw_lab",
            "kind_group": "learning",
            "batch_label": ev_meta.get("batch_label") or (ev_payload.get("refs") or {}).get("batch_label"),
            "session_id": ev_meta.get("session_id") or (ev_payload.get("refs") or {}).get("session_id"),
            "parent_learning_event_artifact_id": learning_event_artifact_id,
            "parent_batch_execution_artifact_id": ev_meta.get("parent_batch_execution_artifact_id") or (ev_payload.get("refs") or {}).get("batch_execution_artifact_id"),
            "operator": ev_meta.get("operator") or ev_payload.get("operator"),
            "policy_decision": pd,
        },
        payload={
            "learning_event_artifact_id": learning_event_artifact_id,
            "policy_decision": pd,
            "approved_by": approved_by,
            "reason": reason,
        },
    )
    return _as_dict(art)
