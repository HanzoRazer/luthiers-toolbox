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
    parent_artifact_id: Optional[str] = None,  # Generic parent lookup
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
) -> bool:
    """Return True if index meta *m* passes all supplied filters."""
    if not _matches_date_range(m, date_from, date_to):
        return False
    if not _matches_simple_fields(m, event_type, kind, status, tool_id, mode, workflow_session_id):
        return False
    if not _matches_session_labels(m, batch_label, session_id):
        return False
    if not _matches_lineage(m, parent_plan_run_id, parent_batch_plan_artifact_id, parent_batch_spec_artifact_id, parent_artifact_id):
        return False
    return True


# ---------------------------------------------------------------------------
# Sub-matchers
# ---------------------------------------------------------------------------

def _matches_date_range(
    m: Dict[str, Any],
    date_from: Optional[datetime],
    date_to: Optional[datetime],
) -> bool:
    """Check created_at_utc falls within [date_from, date_to]."""
    if not date_from and not date_to:
        return True
    created = m.get("created_at_utc")
    if not created:
        return True
    try:
        created_dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
        if date_from and created_dt < date_from:
            return False
        if date_to and created_dt > date_to:
            return False
    except (ValueError, TypeError):
        pass
    return True


def _matches_simple_fields(
    m: Dict[str, Any],
    event_type: Optional[str],
    kind: Optional[str],
    status: Optional[str],
    tool_id: Optional[str],
    mode: Optional[str],
    workflow_session_id: Optional[str],
) -> bool:
    """Match top-level scalar fields."""
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
    return True


def _matches_session_labels(
    m: Dict[str, Any],
    batch_label: Optional[str],
    session_id: Optional[str],
) -> bool:
    """Match batch_label / session_id across top-level and nested meta."""
    if not batch_label and not session_id:
        return True
    nested_meta = m.get("meta") or {}
    if batch_label:
        m_batch_label = m.get("batch_label") or nested_meta.get("batch_label")
        if m_batch_label != batch_label:
            return False
    if session_id:
        m_session_id = m.get("session_id") or nested_meta.get("session_id")
        if m_session_id != session_id:
            return False
    return True


def _matches_lineage(
    m: Dict[str, Any],
    parent_plan_run_id: Optional[str],
    parent_batch_plan_artifact_id: Optional[str],
    parent_batch_spec_artifact_id: Optional[str],
    parent_artifact_id: Optional[str] = None,
) -> bool:
    """Match lineage fields, searching top-level, 'lineage' sub-dict, and 'meta' sub-dict."""
    if not parent_plan_run_id and not parent_batch_plan_artifact_id and not parent_batch_spec_artifact_id and not parent_artifact_id:
        return True

    nested_meta = m.get("meta") or {}
    lineage = m.get("lineage") or {}

    if parent_plan_run_id:
        if not _any_field_matches(m, lineage, nested_meta, "parent_plan_run_id", parent_plan_run_id):
            return False

    if parent_batch_plan_artifact_id:
        if not _any_field_matches(
            m, lineage, nested_meta,
            "parent_batch_plan_artifact_id", parent_batch_plan_artifact_id,
            aliases=("batch_plan_artifact_id",),
        ):
            return False

    if parent_batch_spec_artifact_id:
        if not _any_field_matches(
            m, lineage, nested_meta,
            "parent_batch_spec_artifact_id", parent_batch_spec_artifact_id,
            aliases=("batch_spec_artifact_id",),
        ):
            return False

    if parent_artifact_id:
        if not _any_field_matches(
            m, lineage, nested_meta,
            "parent_artifact_id", parent_artifact_id,
            aliases=("parent_batch_execution_artifact_id",),
        ):
            return False

    return True


def _any_field_matches(
    m: Dict[str, Any],
    lineage: Dict[str, Any],
    nested_meta: Dict[str, Any],
    field: str,
    value: str,
    aliases: tuple = (),
) -> bool:
    """Return True if *value* is found in any of the search dicts under *field* or its aliases."""
    search_keys = (field, *aliases)
    for key in search_keys:
        if m.get(key) == value:
            return True
        if lineage.get(key) == value:
            return True
        if nested_meta.get(key) == value:
            return True
    return False
