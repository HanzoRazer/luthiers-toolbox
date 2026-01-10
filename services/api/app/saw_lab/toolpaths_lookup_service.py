from __future__ import annotations

from typing import Any, Dict, List, Optional


def _as_dict(x: Any) -> Dict[str, Any]:
    return x if isinstance(x, dict) else {}


def _created_utc(art: Dict[str, Any]) -> str:
    p = _as_dict(art.get("payload") or art.get("data"))
    if isinstance(p.get("created_utc"), str):
        return p["created_utc"]
    if isinstance(art.get("created_utc"), str):
        return art["created_utc"]
    return ""


def _pick_latest(items: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not items:
        return None
    items = [x for x in items if isinstance(x, dict)]
    items.sort(key=lambda a: (_created_utc(a) or "9999", str(a.get("id") or a.get("artifact_id") or "")), reverse=True)
    return items[0]


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
    # fallback: some stores keep parent_id at top-level
    pid = a.get("parent_id") or a.get("parent_artifact_id")
    return bool(pid and str(pid) == decision_id)


def get_latest_toolpaths_for_decision(
    *,
    batch_decision_artifact_id: str,
    tool_kind: str = "saw",
    limit: int = 500,
) -> Optional[Dict[str, Any]]:
    """
    Lookup alias: decision -> latest toolpaths artifact.
    Best-effort and governance-safe (read-only).
    """
    from app.rmos.runs_v2 import store as runs_store

    dec = runs_store.get_run(batch_decision_artifact_id)
    if not dec:
        return None

    dec_payload = _as_dict(dec.get("payload") or dec.get("data"))
    session_id = str(dec_payload.get("session_id") or "")
    batch_label = str(dec_payload.get("batch_label") or "")

    # Prefer narrow query when possible
    res = runs_store.list_runs_filtered(
        session_id=session_id or None,
        batch_label=batch_label or None,
        tool_kind=tool_kind,
        limit=limit,
    )
    items = res.get("items") if isinstance(res, dict) else res
    items = items if isinstance(items, list) else []

    candidates: List[Dict[str, Any]] = []
    for a in items:
        if not isinstance(a, dict):
            continue
        k = str(a.get("kind") or (a.get("index_meta") or {}).get("kind") or "")
        if k != "saw_batch_toolpaths" and "toolpaths" not in k.lower():
            continue
        if _matches_parent_decision(a, batch_decision_artifact_id):
            candidates.append(a)

    latest = _pick_latest(candidates)
    if not latest:
        return None

    aid = _artifact_id(latest)
    payload = _as_dict(latest.get("payload") or latest.get("data"))
    stats = _as_dict(payload.get("statistics") or _as_dict(payload.get("toolpaths")).get("statistics"))
    return {
        "batch_decision_artifact_id": batch_decision_artifact_id,
        "batch_toolpaths_artifact_id": aid,
        "status": str(payload.get("status") or payload.get("run_status") or "UNKNOWN"),
        "created_utc": _created_utc(latest),
        "statistics": stats or None,
        "session_id": session_id or None,
        "batch_label": batch_label or None,
    }
