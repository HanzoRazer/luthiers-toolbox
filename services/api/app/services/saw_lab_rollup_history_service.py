from __future__ import annotations

from typing import Any, Dict, List, Optional


def list_execution_rollups(
    *,
    batch_execution_artifact_id: str,
    limit: int = 50,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """
    History of execution rollup artifacts for a single execution.
    """
    from app.rmos.run_artifacts.store import query_run_artifacts

    limit = max(1, min(int(limit), 500))
    offset = max(0, int(offset))

    items = query_run_artifacts(
        kind="saw_batch_execution_metrics_rollup",
        parent_batch_execution_artifact_id=batch_execution_artifact_id,
        limit=max(limit + offset, 100),
        offset=0,
    )
    items.sort(key=lambda x: str(x.get("created_utc") or ""), reverse=True)
    return items[offset : offset + limit]


def list_decision_rollups(
    *,
    batch_decision_artifact_id: str,
    limit: int = 50,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """
    History of decision rollup artifacts for a single decision.
    """
    from app.rmos.run_artifacts.store import query_run_artifacts

    limit = max(1, min(int(limit), 500))
    offset = max(0, int(offset))

    items = query_run_artifacts(
        kind="saw_batch_decision_metrics_rollup",
        parent_batch_decision_artifact_id=batch_decision_artifact_id,
        limit=max(limit + offset, 100),
        offset=0,
    )
    items.sort(key=lambda x: str(x.get("created_utc") or ""), reverse=True)
    return items[offset : offset + limit]


def latest_vs_previous_decision_rollup(
    *,
    batch_decision_artifact_id: str,
) -> Dict[str, Any]:
    """
    Convenience helper for UI:
      - returns latest and previous decision rollup artifacts (if they exist)
    """
    items = list_decision_rollups(batch_decision_artifact_id=batch_decision_artifact_id, limit=2, offset=0)
    latest = items[0] if len(items) >= 1 else None
    prev = items[1] if len(items) >= 2 else None
    return {
        "batch_decision_artifact_id": batch_decision_artifact_id,
        "latest": latest,
        "previous": prev,
        "has_previous": prev is not None,
    }
