from __future__ import annotations

from typing import Any, Dict, List, Optional


def list_executions_by_decision(
    *,
    batch_decision_artifact_id: str,
    limit: int = 50,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """
    Convenience lookup:
      - fetch saw_batch_execution artifacts parented to a specific decision id
    """
    from app.rmos.run_artifacts.store import query_run_artifacts

    limit = max(1, min(int(limit), 500))
    offset = max(0, int(offset))

    items = query_run_artifacts(
        kind="saw_batch_execution",
        parent_batch_decision_artifact_id=batch_decision_artifact_id,
        limit=max(limit + offset, 100),
        offset=0,
    )
    items.sort(key=lambda x: str(x.get("created_utc") or ""), reverse=True)
    return items[offset : offset + limit]


def list_executions_with_learning_applied(
    *,
    batch_label: Optional[str] = None,
    session_id: Optional[str] = None,
    only_applied: bool = True,
    limit: int = 50,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """
    Find executions that did/did-not apply learning (based on index_meta stamp).

    This uses the index_meta stamp written by the execution service:
      index_meta.learning_apply_enabled (flag state)
      payload.learning.tuning_stamp.applied (actual applied)

    We filter best-effort using available store filters + in-memory refinement.
    """
    from app.rmos.run_artifacts.store import query_run_artifacts

    limit = max(1, min(int(limit), 500))
    offset = max(0, int(offset))

    # Pull a window and filter in-memory (store may not support "applied" as first-class filter)
    items = query_run_artifacts(
        kind="saw_batch_execution",
        batch_label=batch_label,
        session_id=session_id,
        limit=max(limit + offset, 200),
        offset=0,
    )
    items.sort(key=lambda x: str(x.get("created_utc") or ""), reverse=True)

    def _is_applied(it: Dict[str, Any]) -> bool:
        payload = it.get("payload") or {}
        if isinstance(payload, dict):
            learning = payload.get("learning") or {}
            if isinstance(learning, dict):
                stamp = learning.get("tuning_stamp") or {}
                if isinstance(stamp, dict) and stamp.get("applied") is True:
                    return True
        return False

    filtered = [it for it in items if (_is_applied(it) if only_applied else True)]
    return filtered[offset : offset + limit]
