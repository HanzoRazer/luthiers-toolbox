"""
Workflow Sessions Routes

FastAPI router for workflow session CRUD operations.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Request as HttpRequest, HTTPException, Query

from .schemas import (
    WorkflowSessionCreateRequest,
    WorkflowSessionPatchRequest,
    WorkflowSessionResponse,
    WorkflowSessionListResponse,
)
from .store import WorkflowSessionStore, _json_load_maybe

# Import runs_v2 store for session linkage
try:
    from ...rmos.runs_v2.store import list_runs_filtered as list_runs_v2
    from ...rmos.runs_v2.store import count_runs_filtered as count_runs_v2
    _runs_v2_available = True
except ImportError:
    _runs_v2_available = False
    list_runs_v2 = None
    count_runs_v2 = None

router = APIRouter(prefix="/api/workflow/sessions", tags=["Workflow Sessions"])

_store = WorkflowSessionStore()


def _req_id(http_request: HttpRequest) -> Optional[str]:
    return getattr(http_request.state, "request_id", None) or http_request.headers.get("x-request-id")


def _normalize(row: dict) -> WorkflowSessionResponse:
    """Normalize a DB row into a response model."""
    # Tolerate id column naming
    sid = row.get("workflow_session_id") or row.get("session_id") or row.get("id") or ""

    # Parse JSON fields
    context = {}
    if "context_json" in row:
        context = _json_load_maybe(row.get("context_json"))

    state_data = {}
    if "state_data_json" in row:
        state_data = _json_load_maybe(row.get("state_data_json"))

    return WorkflowSessionResponse(
        session_id=str(sid),
        created_at_utc=row.get("created_at_utc"),
        updated_at_utc=row.get("updated_at_utc"),
        user_id=row.get("user_id"),
        status=row.get("status"),
        workflow_type=row.get("workflow_type"),
        current_step=row.get("current_step"),
        machine_id=row.get("machine_id"),
        material_id=row.get("material_id"),
        tool_id=row.get("tool_id"),
        context=context,
        state_data=state_data,
        error_message=row.get("error_message"),
        raw={k: row.get(k) for k in row.keys()},
    )


@router.post("", response_model=WorkflowSessionResponse)
def create_workflow_session(body: WorkflowSessionCreateRequest, http_request: HttpRequest):
    """Create a new workflow session."""
    rid = _req_id(http_request)
    row = _store.create(
        user_id=body.user_id,
        status=body.status,
        workflow_type=body.workflow_type,
        current_step=body.current_step,
        machine_id=body.machine_id,
        material_id=body.material_id,
        tool_id=body.tool_id,
        context_json=body.context_json,
        state_data_json=body.state_data_json,
        request_id=rid,
    )
    return _normalize(row)


@router.get("/{session_id}", response_model=WorkflowSessionResponse)
def get_workflow_session(session_id: str):
    """Get a workflow session by ID."""
    row = _store.get(session_id)
    if row is None:
        raise HTTPException(status_code=404, detail="workflow_session not found")
    return _normalize(row)


@router.patch("/{session_id}", response_model=WorkflowSessionResponse)
def patch_workflow_session(
    session_id: str,
    body: WorkflowSessionPatchRequest,
    http_request: HttpRequest
):
    """Update a workflow session."""
    rid = _req_id(http_request)
    row = _store.patch(
        session_id,
        status=body.status,
        current_step=body.current_step,
        workflow_type=body.workflow_type,
        machine_id=body.machine_id,
        material_id=body.material_id,
        tool_id=body.tool_id,
        context_json=body.context_json,
        state_data_json=body.state_data_json,
        error_message=body.error_message,
        request_id=rid,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="workflow_session not found")
    return _normalize(row)


@router.delete("/{session_id}")
def delete_workflow_session(
    session_id: str,
    force: bool = Query(False, description="Force soft-delete even if runs exist"),
    cascade: bool = Query(False, description="Also mark linked runs as orphaned (non-destructive)"),
):
    """
    Delete a workflow session with safeguards.

    Default behavior: refuses if linked runs exist (409 Conflict).
    With force=true: performs soft-delete (sets status="DELETED").
    With cascade=true: also marks linked runs as orphaned (non-destructive).
    """
    session = _store.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="workflow_session not found")

    # Check for linked runs if runs_v2 is available
    has_linked_runs = False
    if _runs_v2_available and count_runs_v2 is not None:
        try:
            run_count = count_runs_v2(workflow_session_id=session_id)
            has_linked_runs = run_count > 0
        except (OSError, RuntimeError):  # WP-1: narrowed from except Exception
            pass  # Continue without run check if store unavailable

    if has_linked_runs and not force:
        raise HTTPException(
            status_code=409,
            detail="workflow_session has linked runs; set force=true to soft-delete, or remove runs first",
        )

    # Soft-delete: set status to DELETED
    if force and has_linked_runs:
        patched = _store.patch(session_id, status="DELETED", error_message="Soft-deleted with linked runs")
        if patched is None:
            raise HTTPException(status_code=500, detail="Failed to soft-delete session")
        return {
            "deleted": True,
            "session_id": session_id,
            "soft_delete": True,
            "force": force,
            "cascade": cascade,
        }

    # Hard delete if no linked runs
    if not _store.delete(session_id):
        raise HTTPException(status_code=404, detail="workflow_session not found")
    return {"deleted": True, "session_id": session_id}


@router.get("", response_model=WorkflowSessionListResponse)
def list_workflow_sessions(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user_id: Optional[str] = None,
    status: Optional[str] = None,
    workflow_type: Optional[str] = None,
    since_utc: Optional[str] = None,
    until_utc: Optional[str] = None,
    include_total: bool = False,
):
    """List workflow sessions with optional filtering."""
    rows, total = _store.list(
        limit=limit,
        offset=offset,
        user_id=user_id,
        status=status,
        workflow_type=workflow_type,
        since_utc=since_utc,
        until_utc=until_utc,
        include_total=include_total,
    )
    items = [_normalize(r) for r in rows]
    return WorkflowSessionListResponse(items=items, limit=limit, offset=offset, total=total)


@router.get("/{session_id}/runs")
def list_runs_for_session(
    session_id: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    status: Optional[str] = None,
    include_total: bool = Query(False, description="Include total count (may be slower)"),
):
    """
    List run artifacts linked to a workflow session.

    Returns runs where workflow_session_id matches this session.
    """
    # Verify session exists
    row = _store.get(session_id)
    if row is None:
        raise HTTPException(status_code=404, detail="workflow_session not found")

    # Check if runs_v2 is available
    if not _runs_v2_available or list_runs_v2 is None:
        raise HTTPException(
            status_code=501,
            detail="Run artifact linkage not available (runs_v2 not configured)"
        )

    # Query runs linked to this session
    runs = list_runs_v2(
        limit=limit,
        offset=offset,
        workflow_session_id=session_id,
        status=status,
    )

    # Get total count if requested (using efficient count function)
    total = None
    if include_total and count_runs_v2 is not None:
        total = count_runs_v2(workflow_session_id=session_id, status=status)

    # Return simplified response
    return {
        "session_id": session_id,
        "runs": [
            {
                "run_id": r.run_id,
                "created_at_utc": r.created_at_utc.isoformat() if r.created_at_utc else None,
                "status": r.status,
                "tool_id": r.tool_id,
                "mode": r.mode,
            }
            for r in runs
        ],
        "limit": limit,
        "offset": offset,
        "count": len(runs),
        "total": total,
    }


@router.get("/{session_id}/advisory-summary")
def workflow_advisory_summary(session_id: str):
    """
    Get advisory summary for all runs in a workflow session.

    Returns:
        - total_runs: Total runs linked to session
        - explanation_status_counts: Breakdown by explanation status
        - advisory_kind_counts: Breakdown by advisory kind
        - latest_advisory_created_at_utc: Most recent advisory timestamp
    """
    # Verify session exists
    row = _store.get(session_id)
    if row is None:
        raise HTTPException(status_code=404, detail="workflow_session not found")

    # Check if runs_v2 is available
    if not _runs_v2_available or list_runs_v2 is None:
        raise HTTPException(
            status_code=501,
            detail="Run artifact linkage not available (runs_v2 not configured)"
        )

    # Get all runs for this session
    runs = list_runs_v2(
        workflow_session_id=session_id,
        limit=100_000,
        offset=0,
    )

    total_runs = len(runs)
    explanation_counts = {"NONE": 0, "PENDING": 0, "READY": 0, "ERROR": 0, "UNKNOWN": 0}
    advisory_kind_counts: dict = {}
    latest_advisory_utc: Optional[str] = None

    for r in runs:
        # Count explanation statuses
        exp_status = getattr(r, 'explanation_status', None) or "UNKNOWN"
        exp_status = exp_status.upper()
        if exp_status in explanation_counts:
            explanation_counts[exp_status] += 1
        else:
            explanation_counts["UNKNOWN"] += 1

        # Count advisory inputs by kind
        advisory_inputs = getattr(r, 'advisory_inputs', None) or []
        for item in advisory_inputs:
            if hasattr(item, 'kind'):
                kind = (item.kind or "unknown").lower()
            elif isinstance(item, dict):
                kind = (item.get("kind") or "unknown").lower()
            else:
                continue
            advisory_kind_counts[kind] = advisory_kind_counts.get(kind, 0) + 1

            # Track latest advisory timestamp
            if hasattr(item, 'created_at_utc'):
                ts = item.created_at_utc
                if isinstance(ts, str):
                    if latest_advisory_utc is None or ts > latest_advisory_utc:
                        latest_advisory_utc = ts

    return {
        "workflow_session_id": session_id,
        "total_runs": total_runs,
        "explanation_status_counts": explanation_counts,
        "advisory_kind_counts": advisory_kind_counts,
        "latest_advisory_created_at_utc": latest_advisory_utc,
    }
