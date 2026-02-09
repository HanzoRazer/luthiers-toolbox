"""RMOS Workflow Router - Session Management API

WP-3: State transition endpoints extracted to rmos_workflow_transitions.py.
This module retains session lifecycle, list, generators, and snapshot endpoints.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Header

from app.workflow.state_machine import (
    ActorRole,
    WorkflowMode,
    WorkflowSession,
    WorkflowState,
    new_session,
    next_step_hint,
    to_comparable_snapshot,
)
from app.workflow.session_store import STORE
from app.workflow.workflow_runs_bridge import get_workflow_runs_bridge
from .rmos_workflow_schemas import (
    GeneratorInfo,
    GeneratorsListResponse,
    SaveSnapshotRequest,
    SaveSnapshotResponse,
    CreateSessionRequest,
    CreateSessionResponse,
    SessionStateResponse,
)
from .rmos_workflow_transitions import transitions_router

router = APIRouter(prefix="/api/rmos/workflow", tags=["RMOS", "Workflow"])
router.include_router(transitions_router)


# ---------------------------------------------------------------------------
# Endpoints - Session Lifecycle
# ---------------------------------------------------------------------------

@router.post("/sessions", response_model=CreateSessionResponse)
def create_session(req: CreateSessionRequest) -> CreateSessionResponse:
    """
    Create a new workflow session.

    Initializes session in DRAFT state with the specified mode.
    """
    index_meta = {}
    if req.tool_id:
        index_meta["tool_id"] = req.tool_id
    if req.material_id:
        index_meta["material_id"] = req.material_id
    if req.machine_id:
        index_meta["machine_id"] = req.machine_id

    session = new_session(req.mode, index_meta=index_meta)
    STORE.put(session)

    return CreateSessionResponse(
        session_id=session.session_id,
        mode=session.mode.value,
        state=session.state.value,
        next_step=next_step_hint(session),
    )


@router.get("/sessions/{session_id}", response_model=SessionStateResponse)
def get_session(session_id: str) -> SessionStateResponse:
    """
    Get current state of a workflow session.
    """
    session = STORE.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail={"error": "SESSION_NOT_FOUND", "session_id": session_id})

    return SessionStateResponse(
        session_id=session.session_id,
        mode=session.mode.value,
        state=session.state.value,
        next_step=next_step_hint(session),
        events_count=len(session.events),
        last_feasibility_artifact_id=(
            session.last_feasibility_artifact.artifact_id
            if session.last_feasibility_artifact else None
        ),
        last_toolpaths_artifact_id=(
            session.last_toolpaths_artifact.artifact_id
            if session.last_toolpaths_artifact else None
        ),
    )


@router.get("/sessions/{session_id}/snapshot")
def get_session_snapshot(session_id: str):
    """
    Get a diff-viewer compatible snapshot of the session.
    """
    session = STORE.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail={"error": "SESSION_NOT_FOUND", "session_id": session_id})
    
    snapshot = to_comparable_snapshot(session)
    return snapshot.model_dump()


@router.get("/sessions/{session_id}/events")
def get_session_events(session_id: str):
    """
    Get the event audit log for a session.
    """
    session = STORE.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail={"error": "SESSION_NOT_FOUND", "session_id": session_id})

    return {
        "session_id": session.session_id,
        "events": [
            {
                "ts_utc": e.ts_utc.isoformat(),
                "actor": e.actor.value,
                "action": e.action,
                "from_state": e.from_state.value,
                "to_state": e.to_state.value,
                "summary": e.summary,
                "details": e.details,
            }
            for e in session.events
        ],
    }


# ---------------------------------------------------------------------------
# List Endpoints
# ---------------------------------------------------------------------------

@router.get("/sessions")
def list_sessions(
    limit: int = 50,
    state: Optional[str] = None,
):
    """
    List all workflow sessions.
    """
    sessions = STORE.list_all()

    if state:
        try:
            state_enum = WorkflowState(state)
            sessions = [s for s in sessions if s.state == state_enum]
        except ValueError:
            pass

    return {
        "sessions": [
            {
                "session_id": s.session_id,
                "mode": s.mode.value,
                "state": s.state.value,
                "events_count": len(s.events),
                "feasibility_artifact_id": (
                    s.last_feasibility_artifact.artifact_id
                    if s.last_feasibility_artifact else None
                ),
                "toolpaths_artifact_id": (
                    s.last_toolpaths_artifact.artifact_id
                    if s.last_toolpaths_artifact else None
                ),
            }
            for s in sessions[:limit]
        ],
        "total": len(sessions),
    }


# ---------------------------------------------------------------------------
# Generators Endpoint
# ---------------------------------------------------------------------------

# Registry of available workflow generators
_WORKFLOW_GENERATORS: list[GeneratorInfo] = [
    GeneratorInfo(
        key="rosette-traditional",
        name="Traditional Rosette",
        description="Classic rosette pattern generator with historical templates",
        category="rosette",
        version="1.0.0",
    ),
    GeneratorInfo(
        key="rosette-modern",
        name="Modern Rosette",
        description="Contemporary rosette designs with parametric variations",
        category="rosette",
        version="1.0.0",
    ),
    GeneratorInfo(
        key="strip-banding",
        name="Strip Banding",
        description="Decorative strip and banding pattern generator",
        category="strip",
        version="1.0.0",
    ),
    GeneratorInfo(
        key="purfling",
        name="Purfling Lines",
        description="Edge purfling and binding pattern generator",
        category="purfling",
        version="1.0.0",
    ),
]


@router.get("/generators", response_model=GeneratorsListResponse)
def list_generators() -> GeneratorsListResponse:
    """List available workflow generators."""
    return GeneratorsListResponse(
        generators=_WORKFLOW_GENERATORS,
        count=len(_WORKFLOW_GENERATORS),
    )


# ---------------------------------------------------------------------------
# Snapshot Save Endpoint
# ---------------------------------------------------------------------------

@router.post("/sessions/{session_id}/save-snapshot", response_model=SaveSnapshotResponse)
def save_session_snapshot(
    session_id: str,
    req: SaveSnapshotRequest,
    x_request_id: Optional[str] = Header(default=None, alias="X-Request-ID"),
) -> SaveSnapshotResponse:
    """Save the current session state as a named snapshot."""
    from datetime import datetime, timezone
    import uuid

    session = STORE.get(session_id)
    if session is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "SESSION_NOT_FOUND", "session_id": session_id}
        )

    # Generate snapshot ID and timestamp
    snapshot_id = f"snap_{uuid.uuid4().hex[:12]}"
    created_at = datetime.now(timezone.utc)

    # Build snapshot name
    snapshot_name = req.name or f"Snapshot {created_at.strftime('%Y-%m-%d %H:%M')}"

    # Get comparable snapshot data
    snapshot_data = to_comparable_snapshot(session)

    # Create RunArtifact via bridge to persist the snapshot
    bridge = get_workflow_runs_bridge()
    artifact_ref = bridge.on_snapshot_saved(
        session,
        snapshot_id=snapshot_id,
        snapshot_name=snapshot_name,
        snapshot_data=snapshot_data.model_dump(),
        tags=req.tags,
        request_id=x_request_id,
    )

    # Use artifact ID as snapshot ID if bridge returned one
    if artifact_ref:
        snapshot_id = artifact_ref.artifact_id

    return SaveSnapshotResponse(
        session_id=session.session_id,
        snapshot_id=snapshot_id,
        name=snapshot_name,
        created_at=created_at.isoformat().replace("+00:00", "Z"),
    )

