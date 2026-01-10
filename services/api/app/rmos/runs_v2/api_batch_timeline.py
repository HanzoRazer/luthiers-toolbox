from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query

from .batch_timeline import BatchTimelinePorts, build_batch_timeline, get_batch_progress


router = APIRouter(prefix="/runs", tags=["runs"])


def _ports() -> BatchTimelinePorts:
    """
    Real adapters to repo store.
    """
    from . import store as runs_store

    return BatchTimelinePorts(
        list_runs_filtered=runs_store.list_runs_filtered,
        get_run=runs_store.get_run,
    )


@router.get("/batch-timeline")
def get_batch_timeline(
    session_id: str = Query(...),
    batch_label: str = Query(...),
    tool_kind: Optional[str] = Query(None),
    limit: int = Query(500, ge=1, le=2000),
):
    """
    Returns a chronological timeline of events for a batch.

    Each event represents an artifact creation with:
    - artifact_id: unique identifier
    - kind: artifact type (saw_batch_spec, saw_batch_plan, etc.)
    - phase: workflow phase (SPEC, PLAN, DECISION, TOOLPATHS, EXECUTION, RESULT)
    - created_utc: timestamp
    - status: OK, BLOCKED, ERROR
    - parent_id: parent artifact link
    - index_meta: metadata snapshot

    Also includes phase_summary with counts and time ranges per phase.
    """
    ports = _ports()
    return build_batch_timeline(
        ports,
        session_id=session_id,
        batch_label=batch_label,
        tool_kind=tool_kind,
        limit=limit,
    )


@router.get("/batch-progress")
def get_batch_progress_endpoint(
    session_id: str = Query(...),
    batch_label: str = Query(...),
    tool_kind: Optional[str] = Query(None),
):
    """
    Returns simplified progress summary for a batch.

    Useful for progress bars and status indicators.

    Returns:
    - phases_completed: list of completed phases
    - current_phase: current workflow phase
    - total_artifacts: count of artifacts in batch
    - status: overall status (NOT_STARTED, IN_PROGRESS, COMPLETED, BLOCKED, ERROR)
    """
    ports = _ports()
    return get_batch_progress(
        ports,
        session_id=session_id,
        batch_label=batch_label,
        tool_kind=tool_kind,
    )
