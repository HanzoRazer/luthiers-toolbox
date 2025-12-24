"""
Saw Lab Decision Lookup Service

Convenience query layer for retrieving decision artifacts.
Uses the canonical RunArtifact index query layer.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional


def list_saw_compare_decisions(
    *,
    batch_label: Optional[str] = None,
    session_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """
    Convenience query: return only compare decision artifacts.

    Uses event_type="saw_compare_decision" filter on the runs_v2 store.

    Args:
        batch_label: Filter by batch_label (from meta)
        session_id: Filter by session_id (from meta)
        limit: Max results (default 50)
        offset: Pagination offset

    Returns:
        List of decision artifact dicts, newest first
    """
    from app.rmos.runs_v2.store import list_runs_filtered

    artifacts = list_runs_filtered(
        event_type="saw_compare_decision",
        batch_label=batch_label,
        session_id=session_id,
        limit=limit,
        offset=offset,
    )

    # Convert to dicts for JSON serialization
    return [
        {
            "artifact_id": a.run_id,
            "run_id": a.run_id,
            "created_at_utc": a.created_at_utc.isoformat() if a.created_at_utc else None,
            "event_type": getattr(a, "event_type", None),
            "status": a.status,
            "batch_label": (a.meta or {}).get("batch_label"),
            "session_id": (a.meta or {}).get("session_id"),
            "parent_batch_artifact_id": (a.meta or {}).get("parent_batch_artifact_id"),
            "selected_child_artifact_id": (a.meta or {}).get("selected_child_artifact_id"),
            "approved_by": (a.meta or {}).get("approved_by"),
            "meta": a.meta,
        }
        for a in artifacts
    ]
