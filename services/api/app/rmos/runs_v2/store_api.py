"""RMOS Run Store v2 — module-level convenience API."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import uuid4

from .schemas import RunArtifact, AdvisoryInputRef
from .store import RunStoreV2

_default_store: Optional[RunStoreV2] = None


def _get_default_store() -> RunStoreV2:
    """Get or create the default store instance."""
    global _default_store
    if _default_store is None:
        _default_store = RunStoreV2()
    return _default_store


def create_run_id() -> str:
    """Generate a new run ID per governance contract."""
    return f"run_{uuid4().hex}"


def persist_run(artifact: RunArtifact) -> RunArtifact:
    """Persist a run artifact to the default store."""
    store = _get_default_store()
    store.put(artifact)
    return artifact


def store_artifact(
    *,
    kind: str,
    payload: Dict[str, Any],
    parent_id: str,
    session_id: str,
) -> str:
    """
    Helper to create and persist a run artifact with minimal boilerplate.
    Returns the generated run_id.
    """
    from .schemas import RunArtifact, utc_now

    run_id = create_run_id()
    artifact = RunArtifact(
        run_id=run_id,
        event_type=kind,
        status="OK",
        created_at_utc=utc_now(),
        payload=payload,
        meta={
            "parent_id": parent_id,
            "session_id": session_id,
        },
    )
    persist_run(artifact)
    return run_id


def update_run(artifact: RunArtifact) -> RunArtifact:
    """Update mutable fields of an existing run artifact."""
    store = _get_default_store()
    store.update_mutable_fields(artifact)
    return artifact


def get_run(run_id: str) -> Optional[RunArtifact]:
    """Retrieve a run artifact from the default store."""
    store = _get_default_store()
    return store.get(run_id)


def list_runs_filtered(
    *,
    limit: int = 50,
    offset: int = 0,
    event_type: Optional[str] = None,
    kind: Optional[str] = None,  # Alias for event_type
    status: Optional[str] = None,
    tool_id: Optional[str] = None,
    mode: Optional[str] = None,
    workflow_session_id: Optional[str] = None,
    batch_label: Optional[str] = None,
    session_id: Optional[str] = None,
    parent_plan_run_id: Optional[str] = None,  # Bundle 10: lineage filtering
    parent_batch_plan_artifact_id: Optional[str] = None,
    parent_batch_spec_artifact_id: Optional[str] = None,
) -> List[RunArtifact]:
    """List runs with optional filtering from the default store."""
    store = _get_default_store()
    return store.list_runs_filtered(
        limit=limit,
        offset=offset,
        event_type=event_type,
        kind=kind,
        status=status,
        tool_id=tool_id,
        mode=mode,
        workflow_session_id=workflow_session_id,
        batch_label=batch_label,
        session_id=session_id,
        parent_plan_run_id=parent_plan_run_id,
        parent_batch_plan_artifact_id=parent_batch_plan_artifact_id,
        parent_batch_spec_artifact_id=parent_batch_spec_artifact_id,
    )


def count_runs_filtered(
    *,
    event_type: Optional[str] = None,
    status: Optional[str] = None,
    tool_id: Optional[str] = None,
    mode: Optional[str] = None,
    workflow_session_id: Optional[str] = None,
) -> int:
    """Count runs matching filters from the default store."""
    store = _get_default_store()
    return store.count_runs_filtered(
        event_type=event_type,
        status=status,
        tool_id=tool_id,
        mode=mode,
        workflow_session_id=workflow_session_id,
    )


def rebuild_index() -> int:
    """Rebuild the global index from the default store."""
    store = _get_default_store()
    return store.rebuild_index()


def attach_advisory(
    run_id: str,
    advisory_id: str,
    kind: str = "unknown",
    engine_id: Optional[str] = None,
    engine_version: Optional[str] = None,
    request_id: Optional[str] = None,
) -> Optional[AdvisoryInputRef]:
    """Attach an advisory to a run in the default store."""
    store = _get_default_store()
    return store.attach_advisory(
        run_id=run_id,
        advisory_id=advisory_id,
        kind=kind,
        engine_id=engine_id,
        engine_version=engine_version,
        request_id=request_id,
    )


def delete_run(
    run_id: str,
    *,
    mode: str = "soft",
    reason: str,
    actor: Optional[str] = None,
    request_id: Optional[str] = None,
    rate_limit_key: Optional[str] = None,
    cascade: bool = True,
) -> Dict[str, Any]:
    """Delete a run artifact from the default store with audit logging."""
    store = _get_default_store()
    return store.delete_run(
        run_id,
        mode=mode,
        reason=reason,
        actor=actor,
        request_id=request_id,
        rate_limit_key=rate_limit_key,
        cascade=cascade,
    )




def _norm(s: Any) -> str:
    """Normalize a value to lowercase string for comparison."""
    return str(s or "").strip().lower()


def _get_nested(d: Dict[str, Any], path: str) -> Any:
    """Get a nested value from a dict using dot notation."""
    cur: Any = d
    for part in path.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    return cur


def _extract_sort_key(run: Dict[str, Any]) -> tuple:
    """
    Returns (created_at_utc, run_id) for stable sort.
    """
    ts = (
        _get_nested(run, "created_at_utc")
        or _get_nested(run, "meta.created_at_utc")
        or _get_nested(run, "request_summary.created_at_utc")
        or ""
    )
    # Handle datetime objects
    if hasattr(ts, 'isoformat'):
        ts = ts.isoformat()
    rid = str(run.get("run_id") or "")
    return (str(ts), rid)


def query_runs(
    *,
    kind: Optional[str] = None,
    mode: Optional[str] = None,
    tool_id: Optional[str] = None,
    status: Optional[str] = None,
    batch_label: Optional[str] = None,
    session_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """Query runs with filtering, returning dicts for convenience."""
    runs = list_runs_filtered(
        event_type=kind,
        mode=mode,
        tool_id=tool_id,
        status=status,
        batch_label=batch_label,
        session_id=session_id,
        limit=limit,
        offset=offset,
    )
    return [r.model_dump() for r in runs]


def query_recent(
    *,
    limit: int = 50,
    cursor: Optional[str] = None,
    mode: Optional[str] = None,
    tool_id: Optional[str] = None,
    risk_level: Optional[str] = None,
    status: Optional[str] = None,
    source: Optional[str] = None,
) -> Dict[str, Any]:
    """Query recent runs with cursor-based pagination and server-side filtering."""
    store = _get_default_store()
    limit = max(1, min(int(limit or 50), 500))

    # Over-fetch to allow for filtering
    fetch_n = limit * 8

    # Get runs as dicts
    runs = store.list_runs(limit=fetch_n)
    items = [r.model_dump() for r in runs]

    # Sort newest first using (ts, run_id)
    items.sort(key=_extract_sort_key, reverse=True)

    # Parse cursor
    cursor_ts = cursor_id = None
    if cursor:
        try:
            cursor_ts, cursor_id = cursor.split("|", 1)
        except (ValueError, TypeError):  # WP-1: narrowed from except Exception
            cursor_ts, cursor_id = None, None

    def is_older_than_cursor(r: Dict[str, Any]) -> bool:
        if not cursor_ts:
            return True
        ts, rid = _extract_sort_key(r)
        # strictly older than cursor
        if ts < cursor_ts:
            return True
        if ts == cursor_ts and rid < (cursor_id or ""):
            return True
        return False

    def match(r: Dict[str, Any]) -> bool:
        if mode and _norm(r.get("mode")) != _norm(mode):
            return False

        if status and _norm(r.get("status")) != _norm(status):
            return False

        if tool_id:
            v = _get_nested(r, "request_summary.tool_id") or r.get("tool_id")
            if _norm(v) != _norm(tool_id):
                return False

        if source:
            v = _get_nested(r, "request_summary.source") or _get_nested(r, "meta.source") or r.get("source")
            if _norm(v) != _norm(source):
                return False

        if risk_level:
            v = (
                _get_nested(r, "decision.risk_level")
                or _get_nested(r, "decision.risk_bucket")
                or _get_nested(r, "feasibility.risk_level")
                or _get_nested(r, "feasibility.risk_bucket")
            )
            if _norm(v) != _norm(risk_level):
                return False

        return True

    out: List[Dict[str, Any]] = []
    for r in items:
        if not is_older_than_cursor(r):
            continue
        if not match(r):
            continue
        out.append(r)
        if len(out) >= limit:
            break

    next_cursor = None
    if out:
        ts, rid = _extract_sort_key(out[-1])
        if ts and rid:
            next_cursor = f"{ts}|{rid}"

    return {"items": out, "next_cursor": next_cursor}
