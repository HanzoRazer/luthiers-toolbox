from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple


def _as_dict(x: Any) -> Dict[str, Any]:
    return x if isinstance(x, dict) else {}


def _created_utc(art: Dict[str, Any]) -> str:
    p = _as_dict(art.get("payload") or art.get("data"))
    if isinstance(p.get("created_utc"), str):
        return p["created_utc"]
    if isinstance(art.get("created_utc"), str):
        return art["created_utc"]
    return ""


def _artifact_id(a: Dict[str, Any]) -> Optional[str]:
    v = a.get("id") or a.get("artifact_id")
    return str(v) if v else None


def _matches_parent_decision(a: Dict[str, Any], decision_id: str) -> bool:
    p = _as_dict(a.get("payload") or a.get("data"))
    m = _as_dict(a.get("index_meta"))
    for src in (p, m):
        v = src.get("parent_batch_decision_artifact_id") or src.get("parent_decision_artifact_id")
        if v and str(v) == decision_id:
            return True
    pid = a.get("parent_id") or a.get("parent_artifact_id")
    return bool(pid and str(pid) == decision_id)


def _is_execution_kind(a: Dict[str, Any]) -> bool:
    k = str(a.get("kind") or (_as_dict(a.get("index_meta")).get("kind")) or "")
    return k == "saw_batch_execution" or "execution" in k.lower()


def _summarize_execution(a: Dict[str, Any]) -> Dict[str, Any]:
    payload = _as_dict(a.get("payload") or a.get("data"))
    meta = _as_dict(a.get("index_meta"))
    return {
        "artifact_id": _artifact_id(a),
        "kind": str(a.get("kind") or meta.get("kind") or ""),
        "created_utc": _created_utc(a),
        "status": str(payload.get("status") or payload.get("run_status") or payload.get("state") or "UNKNOWN"),
        "statistics": payload.get("statistics") or payload.get("metrics") or None,
        "risk_bucket": payload.get("risk_bucket") or meta.get("risk_bucket") or meta.get("risk_level") or None,
        "parent_batch_decision_artifact_id": (
            payload.get("parent_batch_decision_artifact_id")
            or meta.get("parent_batch_decision_artifact_id")
            or a.get("parent_id")
            or None
        ),
    }


def list_executions_for_decision(
    *,
    batch_decision_artifact_id: str,
    tool_kind: str = "saw",
    limit: int = 200,
    offset: int = 0,
    newest_first: bool = True,
    max_scan: int = 5000,
) -> Optional[Dict[str, Any]]:
    """
    decision -> all executions (summaries), paginated client-side.

    We query the batch (session_id + batch_label) then filter executions by parent decision.
    This keeps it compatible with existing store filters while remaining deterministic.
    """
    from app.rmos.runs_v2 import store as runs_store

    dec = runs_store.get_run(batch_decision_artifact_id)
    if not dec:
        return None

    dec_payload = _as_dict(dec.get("payload") or dec.get("data"))
    session_id = str(dec_payload.get("session_id") or "")
    batch_label = str(dec_payload.get("batch_label") or "")

    res = runs_store.list_runs_filtered(
        session_id=session_id or None,
        batch_label=batch_label or None,
        tool_kind=tool_kind,
        limit=max_scan,
    )
    items = res.get("items") if isinstance(res, dict) else res
    items = items if isinstance(items, list) else []

    executions: List[Dict[str, Any]] = []
    for a in items:
        if not isinstance(a, dict):
            continue
        if not _is_execution_kind(a):
            continue
        if not _matches_parent_decision(a, batch_decision_artifact_id):
            continue
        executions.append(a)

    executions.sort(key=lambda a: (_created_utc(a) or "9999", str(_artifact_id(a) or "")), reverse=newest_first)
    total = len(executions)

    start = max(0, int(offset))
    end = max(start, start + max(0, int(limit)))
    page = executions[start:end]

    return {
        "batch_decision_artifact_id": batch_decision_artifact_id,
        "session_id": session_id or None,
        "batch_label": batch_label or None,
        "tool_kind": tool_kind,
        "total": total,
        "offset": start,
        "limit": int(limit),
        "items": [_summarize_execution(x) for x in page],
    }
