from __future__ import annotations

from typing import Any, Dict, List, Optional


def _get_meta(it: Dict[str, Any]) -> Dict[str, Any]:
    m = it.get("index_meta")
    return m if isinstance(m, dict) else {}


def list_executions_for_decision(
    *,
    batch_decision_artifact_id: str,
    limit: int = 25,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """
    Retrieve parent execution artifacts for a given batch decision.
    Newest-first (best-effort by created_utc).

    Note: This is intentionally lightweight (filters in-memory after a kind query).
    A DB-backed index can optimize later without changing the API contract.
    """
    from app.rmos.run_artifacts.store import query_run_artifacts

    # Use store-level meta filter (still lightweight; DB index can optimize later)
    items = query_run_artifacts(
        kind="saw_batch_execution",
        parent_batch_decision_artifact_id=batch_decision_artifact_id,
        limit=max(limit, 50),
        offset=0,
    )
    items.sort(key=lambda x: str(x.get("created_utc") or ""), reverse=True)
    return items[offset : offset + limit]


def latest_execution_for_decision(batch_decision_artifact_id: str) -> Optional[Dict[str, Any]]:
    items = list_executions_for_decision(
        batch_decision_artifact_id=batch_decision_artifact_id,
        limit=1,
        offset=0,
    )
    return items[0] if items else None
