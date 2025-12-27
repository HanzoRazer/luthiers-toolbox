"""
Saw Lab: Toolpaths Lookup Service

Provides convenience lookup for toolpaths artifacts by decision_artifact_id.
Returns the latest toolpaths artifact that has parent_decision_artifact_id in index_meta.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional


def _get_meta(it: Dict[str, Any]) -> Dict[str, Any]:
    m = it.get("index_meta")
    return m if isinstance(m, dict) else {}


def list_toolpaths_for_decision(
    *,
    decision_artifact_id: str,
    limit: int = 25,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """
    Retrieve toolpaths artifacts for a given decision by filtering index_meta.
    Returns newest-first (assuming your run index is already newest-first).
    """
    from app.rmos.runs_v2.store import query_runs

    # Query toolpaths artifacts broadly, then filter by parent_decision_artifact_id.
    # This avoids requiring new store-level filters.
    items = query_runs(
        kind="saw_compare_toolpaths",
        limit=max(limit, 50),   # grab enough to filter
        offset=0,
    )

    filtered = [
        it for it in items
        if isinstance(it, dict) and _get_meta(it).get("parent_decision_artifact_id") == decision_artifact_id
    ]

    # Ensure newest-first ordering if created_utc exists
    filtered.sort(key=lambda x: str(x.get("created_utc") or ""), reverse=True)

    return filtered[offset : offset + limit]


def latest_toolpaths_for_decision(decision_artifact_id: str) -> Optional[Dict[str, Any]]:
    items = list_toolpaths_for_decision(decision_artifact_id=decision_artifact_id, limit=1, offset=0)
    return items[0] if items else None
