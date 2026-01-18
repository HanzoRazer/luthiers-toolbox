from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple


def _as_dict(x: Any) -> Dict[str, Any]:
    return x if isinstance(x, dict) else {}


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


def _payload(a: Dict[str, Any]) -> Dict[str, Any]:
    return _as_dict(a.get("payload") or a.get("data"))


def _is_approved_decision(a: Dict[str, Any]) -> bool:
    if "decision" not in _kind(a).lower():
        return False
    p = _payload(a)
    st = p.get("state")
    if isinstance(st, str):
        return st.strip().upper() == "APPROVED"
    # if state not present, still allow (best-effort)
    return True


def resolve_latest_approved_decision_for_batch(
    *,
    session_id: str,
    batch_label: str,
    tool_kind: str = "saw",
    limit: int = 20000,
) -> Optional[Dict[str, Any]]:
    """
    Returns latest APPROVED decision artifact for a batch (best-effort).
    """
    from app.rmos.runs_v2 import store as runs_store

    res = runs_store.list_runs_filtered(
        session_id=session_id,
        batch_label=batch_label,
        tool_kind=tool_kind,
        limit=limit,
    )
    items = res.get("items") if isinstance(res, dict) else res
    items = items if isinstance(items, list) else []

    decisions: List[Dict[str, Any]] = []
    for a in items:
        if not isinstance(a, dict):
            continue
        if "decision" not in _kind(a).lower():
            continue
        if _is_approved_decision(a):
            decisions.append(a)

    if not decisions:
        return None
    decisions.sort(key=lambda a: (_created_utc(a) or "9999", str(_id(a) or "")), reverse=True)
    return decisions[0]


def resolve_latest_execution_for_batch(
    *,
    session_id: str,
    batch_label: str,
    tool_kind: str = "saw",
    limit: int = 20000,
) -> Optional[Dict[str, Any]]:
    """
    Latest execution for the batch (does not require decision id).
    """
    from app.rmos.runs_v2 import store as runs_store

    res = runs_store.list_runs_filtered(
        session_id=session_id,
        batch_label=batch_label,
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
        execs.append(a)

    if not execs:
        return None
    execs.sort(key=lambda a: (_created_utc(a) or "9999", str(_id(a) or "")), reverse=True)
    return execs[0]


def resolve_latest_metrics_for_batch(
    *,
    session_id: str,
    batch_label: str,
    tool_kind: str = "saw",
) -> Dict[str, Any]:
    """
    No decision id required:
      - prefer latest execution in batch
      - return latest metrics for that execution
      - also include latest approved decision (if present) for UI context
    """
    from app.saw_lab.metrics_lookup_service import resolve_latest_metrics_for_execution

    dec = resolve_latest_approved_decision_for_batch(
        session_id=session_id,
        batch_label=batch_label,
        tool_kind=tool_kind,
    )
    dec_id = _id(dec) if dec else None

    ex = resolve_latest_execution_for_batch(
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
    mx_id = _id(mx) if mx else None
    kpis = _payload(mx).get("kpis") if mx and isinstance(_payload(mx).get("kpis"), dict) else None

    return {
        "session_id": session_id,
        "batch_label": batch_label,
        "tool_kind": tool_kind,
        "latest_approved_decision_artifact_id": dec_id,
        "latest_execution_artifact_id": ex_id,
        "latest_metrics_artifact_id": mx_id,
        "kpis": kpis,
    }
