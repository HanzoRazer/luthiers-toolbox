from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from app.rmos.artifact_helpers import as_dict as _as_dict, extract_created_utc as _created_utc, get_kind as _kind, get_artifact_id as _id

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
