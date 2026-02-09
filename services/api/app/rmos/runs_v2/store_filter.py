"""Index metadata filter — shared by list_runs_filtered / count_runs_filtered."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional


def matches_index_meta(
    m: Dict[str, Any],
    *,
    event_type: Optional[str] = None,
    kind: Optional[str] = None,
    status: Optional[str] = None,
    tool_id: Optional[str] = None,
    mode: Optional[str] = None,
    workflow_session_id: Optional[str] = None,
    batch_label: Optional[str] = None,
    session_id: Optional[str] = None,
    parent_plan_run_id: Optional[str] = None,
    parent_batch_plan_artifact_id: Optional[str] = None,
    parent_batch_spec_artifact_id: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
) -> bool:
    """Return True if index meta *m* passes all supplied filters."""
    # Date filtering
    if date_from or date_to:
        created = m.get("created_at_utc")
        if created:
            try:
                created_dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                if date_from and created_dt < date_from:
                    return False
                if date_to and created_dt > date_to:
                    return False
            except (ValueError, TypeError):
                pass

    effective_event_type = event_type or kind
    if effective_event_type and m.get("event_type") != effective_event_type:
        return False
    if status and m.get("status") != status:
        return False
    if tool_id and m.get("tool_id") != tool_id:
        return False
    if mode and m.get("mode") != mode:
        return False
    if workflow_session_id and m.get("workflow_session_id") != workflow_session_id:
        return False

    nested_meta = m.get("meta") or {}
    m_batch_label = m.get("batch_label") or nested_meta.get("batch_label")
    m_session_id = m.get("session_id") or nested_meta.get("session_id")
    if batch_label and m_batch_label != batch_label:
        return False
    if session_id and m_session_id != session_id:
        return False

    # Lineage: parent_plan_run_id
    if parent_plan_run_id:
        lineage = m.get("lineage") or {}
        if lineage.get("parent_plan_run_id") != parent_plan_run_id:
            if m.get("parent_plan_run_id") != parent_plan_run_id:
                if nested_meta.get("parent_plan_run_id") != parent_plan_run_id:
                    return False

    # Lineage: parent_batch_plan_artifact_id
    if parent_batch_plan_artifact_id:
        lineage = m.get("lineage") or {}
        found = (
            m.get("parent_batch_plan_artifact_id") == parent_batch_plan_artifact_id
            or lineage.get("parent_batch_plan_artifact_id") == parent_batch_plan_artifact_id
            or nested_meta.get("parent_batch_plan_artifact_id") == parent_batch_plan_artifact_id
            or m.get("batch_plan_artifact_id") == parent_batch_plan_artifact_id
            or nested_meta.get("batch_plan_artifact_id") == parent_batch_plan_artifact_id
        )
        if not found:
            return False

    # Lineage: parent_batch_spec_artifact_id
    if parent_batch_spec_artifact_id:
        lineage = m.get("lineage") or {}
        found = (
            m.get("parent_batch_spec_artifact_id") == parent_batch_spec_artifact_id
            or lineage.get("parent_batch_spec_artifact_id") == parent_batch_spec_artifact_id
            or nested_meta.get("parent_batch_spec_artifact_id") == parent_batch_spec_artifact_id
            or m.get("batch_spec_artifact_id") == parent_batch_spec_artifact_id
            or nested_meta.get("batch_spec_artifact_id") == parent_batch_spec_artifact_id
        )
        if not found:
            return False

    return True
