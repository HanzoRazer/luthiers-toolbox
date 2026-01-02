from __future__ import annotations

from typing import Any, Dict, List, Optional


def _meta(it: Dict[str, Any]) -> Dict[str, Any]:
    m = it.get("index_meta")
    return m if isinstance(m, dict) else {}


def get_latest_execution_rollup_artifact(
    *,
    batch_execution_artifact_id: str,
) -> Optional[Dict[str, Any]]:
    """
    Returns the most recent:
      kind='saw_batch_execution_metrics_rollup'
    parented to a given execution artifact.
    """
    from app.rmos.run_artifacts.store import query_run_artifacts

    items = query_run_artifacts(
        kind="saw_batch_execution_metrics_rollup",
        parent_batch_execution_artifact_id=batch_execution_artifact_id,
        limit=50,
        offset=0,
    )
    items.sort(key=lambda x: str(x.get("created_utc") or ""), reverse=True)
    return items[0] if items else None


def get_latest_decision_rollup_artifact(
    *,
    batch_decision_artifact_id: str,
) -> Optional[Dict[str, Any]]:
    """
    Returns the most recent:
      kind='saw_batch_decision_metrics_rollup'
    parented to a given decision artifact.
    """
    from app.rmos.run_artifacts.store import query_run_artifacts

    items = query_run_artifacts(
        kind="saw_batch_decision_metrics_rollup",
        parent_batch_decision_artifact_id=batch_decision_artifact_id,
        limit=50,
        offset=0,
    )
    items.sort(key=lambda x: str(x.get("created_utc") or ""), reverse=True)
    return items[0] if items else None
