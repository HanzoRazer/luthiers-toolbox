from __future__ import annotations

from typing import Any, Dict, Optional


def write_execution_confirmation_artifact(
    *,
    batch_execution_artifact_id: str,
    session_id: str,
    batch_label: str,
    operator_id: str,
    checks: Dict[str, bool],
    notes: Optional[str] = None,
    tool_kind: str = "saw",
) -> str:
    """
    Persist an operator confirmation artifact that gates live execution.

    Artifact kind:
      - saw_batch_execution_confirmation

    Parent:
      - batch_execution_artifact_id (always)
    """
    if not batch_execution_artifact_id:
        raise ValueError("batch_execution_artifact_id required")
    if not session_id:
        raise ValueError("session_id required")
    if not batch_label:
        raise ValueError("batch_label required")
    if not operator_id:
        raise ValueError("operator_id required")
    if not isinstance(checks, dict) or not checks:
        raise ValueError("checks must be a non-empty dict[str,bool]")

    payload: Dict[str, Any] = {
        "batch_execution_artifact_id": batch_execution_artifact_id,
        "session_id": session_id,
        "batch_label": batch_label,
        "operator_id": operator_id,
        "checks": checks,
        "notes": notes,
        "state": "CONFIRMED",
    }

    from app.rmos.runs_v2.store import store_artifact

    confirmation_id = store_artifact(
        kind="saw_batch_execution_confirmation",
        payload=payload,
        parent_id=batch_execution_artifact_id,
        session_id=session_id,
        batch_label=batch_label,
        tool_kind=tool_kind,
    )
    return confirmation_id


def get_latest_execution_confirmation(
    *,
    batch_execution_artifact_id: str,
    session_id: Optional[str] = None,
    batch_label: Optional[str] = None,
    tool_kind: str = "saw",
) -> Optional[Dict[str, Any]]:
    """
    Returns the latest confirmation artifact for an execution (best-effort).
    """
    if not batch_execution_artifact_id:
        return None

    from app.rmos.runs_v2 import store as runs_store

    # Prefer filtering by parent_id if store supports it via parent_plan_run_id/parent_id linkage;
    # otherwise fall back to scanning the batch list and matching parent_id.
    res = runs_store.list_runs_filtered(
        session_id=session_id,
        batch_label=batch_label,
        tool_kind=tool_kind,
        kind="saw_batch_execution_confirmation",
        limit=5000,
    )
    items = (res or {}).get("items") if isinstance(res, dict) else None
    if not isinstance(items, list):
        items = []

    matches = []
    for a in items:
        if not isinstance(a, dict):
            continue
        pid = a.get("parent_id") or a.get("parent_artifact_id")
        if pid and str(pid) == str(batch_execution_artifact_id):
            matches.append(a)

    # If store results are already ordered newest-first, this is fine.
    # If not, we sort by created_utc descending (best-effort).
    def _created(a: Dict[str, Any]) -> str:
        v = a.get("created_utc")
        return v if isinstance(v, str) else ""

    matches.sort(key=_created, reverse=True)
    return matches[0] if matches else None
