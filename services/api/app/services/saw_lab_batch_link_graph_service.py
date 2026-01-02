from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple


def _id(it: Dict[str, Any]) -> Optional[str]:
    return it.get("artifact_id") or it.get("id")


def _meta(it: Dict[str, Any]) -> Dict[str, Any]:
    m = it.get("index_meta")
    return m if isinstance(m, dict) else {}


def _sort_newest_first(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    items.sort(key=lambda x: str(x.get("created_utc") or ""), reverse=True)
    return items


def build_batch_link_graph(
    *,
    batch_label: Optional[str],
    session_id: Optional[str],
    limit_each: int = 25,
) -> Dict[str, Any]:
    """
    Returns a minimal "link graph" summary for UI navigation:
      spec -> plan -> decision -> execution
    Uses /api/rmos/runs store queries; stays lightweight.
    """
    from app.rmos.run_artifacts.store import query_run_artifacts

    limit_each = max(1, min(int(limit_each), 200))

    specs = query_run_artifacts(kind="saw_batch_spec", batch_label=batch_label, session_id=session_id, limit=limit_each, offset=0)
    plans = query_run_artifacts(kind="saw_batch_plan", batch_label=batch_label, session_id=session_id, limit=limit_each, offset=0)
    decisions = query_run_artifacts(kind="saw_batch_decision", batch_label=batch_label, session_id=session_id, limit=limit_each, offset=0)
    executions = query_run_artifacts(kind="saw_batch_execution", batch_label=batch_label, session_id=session_id, limit=limit_each, offset=0)

    _sort_newest_first(specs)
    _sort_newest_first(plans)
    _sort_newest_first(decisions)
    _sort_newest_first(executions)

    spec_ids = [x for x in [_id(it) for it in specs] if x]
    plan_ids = [x for x in [_id(it) for it in plans] if x]
    decision_ids = [x for x in [_id(it) for it in decisions] if x]
    execution_ids = [x for x in [_id(it) for it in executions] if x]

    return {
        "batch_label": batch_label,
        "session_id": session_id,
        "latest_spec_artifact_id": spec_ids[0] if spec_ids else None,
        "latest_plan_artifact_id": plan_ids[0] if plan_ids else None,
        "latest_decision_artifact_id": decision_ids[0] if decision_ids else None,
        "latest_execution_artifact_id": execution_ids[0] if execution_ids else None,
        "spec_artifact_ids": spec_ids,
        "plan_artifact_ids": plan_ids,
        "decision_artifact_ids": decision_ids,
        "execution_artifact_ids": execution_ids,
        "notes": {
            "spec_count": len(spec_ids),
            "plan_count": len(plan_ids),
            "decision_count": len(decision_ids),
            "execution_count": len(execution_ids),
        },
    }
