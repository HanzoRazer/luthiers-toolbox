from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.rmos.artifact_helpers import (
    as_dict as _as_dict,
    extract_created_utc as _created_utc,
    pick_latest as _pick_latest,
    get_artifact_id as _artifact_id,
    matches_parent_decision as _matches_parent_decision,
)


def get_latest_execution_for_decision(
    *,
    batch_decision_artifact_id: str,
    tool_kind: str = "saw",
    limit: int = 1000,
) -> Optional[Dict[str, Any]]:
    """
    Lookup alias: decision -> latest execution artifact.
    Read-only.
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
        limit=limit,
    )
    items = res.get("items") if isinstance(res, dict) else res
    items = items if isinstance(items, list) else []

    candidates: List[Dict[str, Any]] = []
    for a in items:
        if not isinstance(a, dict):
            continue
        k = str(a.get("kind") or (a.get("index_meta") or {}).get("kind") or "")
        if k != "saw_batch_execution" and "execution" not in k.lower():
            continue
        if _matches_parent_decision(a, batch_decision_artifact_id):
            candidates.append(a)

    latest = _pick_latest(candidates)
    if not latest:
        return None

    aid = _artifact_id(latest)
    payload = _as_dict(latest.get("payload") or latest.get("data"))
    stats = _as_dict(payload.get("statistics") or payload.get("metrics") or {})

    return {
        "batch_decision_artifact_id": batch_decision_artifact_id,
        "batch_execution_artifact_id": aid,
        "status": str(payload.get("status") or payload.get("run_status") or "UNKNOWN"),
        "created_utc": _created_utc(latest),
        "statistics": stats or None,
        "session_id": session_id or None,
        "batch_label": batch_label or None,
    }
