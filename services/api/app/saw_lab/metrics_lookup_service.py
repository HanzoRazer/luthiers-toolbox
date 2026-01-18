from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple


def _as_dict(x: Any) -> Dict[str, Any]:
    return x if isinstance(x, dict) else {}


def _as_list(x: Any) -> List[Any]:
    return x if isinstance(x, list) else []


def _kind(a: Dict[str, Any]) -> str:
    return str(a.get("kind") or _as_dict(a.get("index_meta")).get("kind") or "")


def _id(a: Dict[str, Any]) -> Optional[str]:
    v = a.get("id") or a.get("artifact_id")
    return str(v) if v else None


def _created_utc(a: Dict[str, Any]) -> str:
    if isinstance(a.get("created_utc"), str):
        return a["created_utc"]
    p = _as_dict(a.get("payload") or a.get("data"))
    if isinstance(p.get("created_utc"), str):
        return p["created_utc"]
    return ""


def _links(a: Dict[str, Any]) -> Dict[str, Any]:
    return _as_dict(_as_dict(a.get("index_meta")).get("links"))


def _payload(a: Dict[str, Any]) -> Dict[str, Any]:
    return _as_dict(a.get("payload") or a.get("data"))


def _is_execution_for_decision(a: Dict[str, Any], decision_artifact_id: str) -> bool:
    if not decision_artifact_id:
        return False
    p = _payload(a)
    l = _links(a)
    # common linkage fields across bundles
    for k in (
        "parent_decision_artifact_id",
        "decision_artifact_id",
        "batch_decision_artifact_id",
    ):
        v = p.get(k) or l.get(k)
        if v and str(v) == str(decision_artifact_id):
            return True
    # also allow parent_id directly
    pid = a.get("parent_id")
    if pid and str(pid) == str(decision_artifact_id):
        return True
    return False


def _is_metrics_for_execution(a: Dict[str, Any], execution_artifact_id: str) -> bool:
    if not execution_artifact_id:
        return False
    p = _payload(a)
    l = _links(a)
    v = p.get("batch_execution_artifact_id") or l.get("batch_execution_artifact_id")
    if v and str(v) == str(execution_artifact_id):
        return True
    pid = a.get("parent_id")
    if pid and str(pid) == str(execution_artifact_id):
        return True
    return False


def resolve_latest_execution_for_decision(
    *,
    decision_artifact_id: str,
    session_id: Optional[str] = None,
    batch_label: Optional[str] = None,
    tool_kind: str = "saw",
    limit: int = 20000,
) -> Optional[Dict[str, Any]]:
    """
    Returns the latest batch execution artifact for a given decision.
    """
    from app.rmos.runs_v2 import store as runs_store

    res = runs_store.list_runs_filtered(
        session_id=session_id or None,
        batch_label=batch_label or None,
        tool_kind=tool_kind,
        limit=limit,
    )
    items = res.get("items") if isinstance(res, dict) else res
    items = items if isinstance(items, list) else []

    execs: List[Dict[str, Any]] = []
    for a in items:
        if not isinstance(a, dict):
            continue
        if "execution" not in _kind(a).lower():
            continue
        if _is_execution_for_decision(a, decision_artifact_id):
            execs.append(a)

    if not execs:
        return None

    execs.sort(key=lambda a: (_created_utc(a) or "9999", str(_id(a) or "")), reverse=True)
    return execs[0]


def resolve_latest_metrics_for_execution(
    *,
    batch_execution_artifact_id: str,
    session_id: Optional[str] = None,
    batch_label: Optional[str] = None,
    tool_kind: str = "saw",
    limit: int = 20000,
) -> Optional[Dict[str, Any]]:
    """
    Returns the latest saw_batch_execution_metrics artifact for an execution.
    """
    from app.rmos.runs_v2 import store as runs_store

    res = runs_store.list_runs_filtered(
        session_id=session_id or None,
        batch_label=batch_label or None,
        tool_kind=tool_kind,
        limit=limit,
    )
    items = res.get("items") if isinstance(res, dict) else res
    items = items if isinstance(items, list) else []

    metrics: List[Dict[str, Any]] = []
    for a in items:
        if not isinstance(a, dict):
            continue
        if "execution_metrics" not in _kind(a).lower() and "batch_execution_metrics" not in _kind(a).lower():
            continue
        if _is_metrics_for_execution(a, batch_execution_artifact_id):
            metrics.append(a)

    if not metrics:
        return None

    metrics.sort(key=lambda a: (_created_utc(a) or "9999", str(_id(a) or "")), reverse=True)
    return metrics[0]


def resolve_latest_metrics_by_decision(
    *,
    decision_artifact_id: str,
    session_id: Optional[str] = None,
    batch_label: Optional[str] = None,
    tool_kind: str = "saw",
) -> Dict[str, Any]:
    """
    decision -> latest execution -> latest metrics (for that execution)
    """
    ex = resolve_latest_execution_for_decision(
        decision_artifact_id=decision_artifact_id,
        session_id=session_id,
        batch_label=batch_label,
        tool_kind=tool_kind,
    )
    ex_id = _id(ex) if ex else None
    mx = (
        resolve_latest_metrics_for_execution(
            batch_execution_artifact_id=ex_id,
            session_id=session_id,
            batch_label=batch_label,
            tool_kind=tool_kind,
        )
        if ex_id
        else None
    )

    mx_payload = _payload(mx) if mx else {}
    return {
        "decision_artifact_id": decision_artifact_id,
        "latest_execution_artifact_id": ex_id,
        "latest_metrics_artifact_id": _id(mx) if mx else None,
        "kpis": mx_payload.get("kpis") if isinstance(mx_payload.get("kpis"), dict) else None,
    }
