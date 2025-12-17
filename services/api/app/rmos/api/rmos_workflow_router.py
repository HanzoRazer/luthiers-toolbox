"""
RMOS Workflow Router - Session Management API

Provides HTTP endpoints for workflow session lifecycle:
- Create new sessions
- Approve sessions for toolpath generation
- Query session state

Uses in-memory store by default. Use DB-backed endpoints for production.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.workflow.state_machine import (
    ActorRole,
    WorkflowMode,
    WorkflowSession,
    WorkflowState,
    approve,
    new_session,
    next_step_hint,
)
from app.workflow.session_store import STORE

router = APIRouter(prefix="/api/rmos/workflow", tags=["RMOS", "Workflow"])


# ---------------------------------------------------------------------------
# Request/Response Models
# ---------------------------------------------------------------------------

class CreateSessionRequest(BaseModel):
    mode: WorkflowMode = Field(default=WorkflowMode.DESIGN_FIRST)
    tool_id: Optional[str] = None
    material_id: Optional[str] = None
    machine_id: Optional[str] = None


class CreateSessionResponse(BaseModel):
    session_id: str
    mode: str
    state: str
    next_step: str


class ApproveRequest(BaseModel):
    session_id: str
    actor: ActorRole = ActorRole.OPERATOR
    note: Optional[str] = None


class ApproveResponse(BaseModel):
    session_id: str
    state: str
    approved: bool
    message: str


class SessionStateResponse(BaseModel):
    session_id: str
    mode: str
    state: str
    next_step: str
    events_count: int


# ---------------------------------------------------------------------------
# Endpoints
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
    )


@router.post("/approve", response_model=ApproveResponse)
def approve_session(req: ApproveRequest) -> ApproveResponse:
    """
    Approve a workflow session for toolpath generation.

    Requires session to be in FEASIBILITY_READY state.
    Enforces governance rules (score threshold, risk level).
    """
    session = STORE.get(req.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail={"error": "SESSION_NOT_FOUND", "session_id": req.session_id})

    try:
        approve(session, actor=req.actor, note=req.note)
        STORE.put(session)
        return ApproveResponse(
            session_id=session.session_id,
            state=session.state.value,
            approved=True,
            message="Session approved for toolpath generation.",
        )
    except Exception as e:
        # Approval may be blocked by governance rules
        raise HTTPException(
            status_code=409,
            detail={
                "error": "APPROVAL_BLOCKED",
                "session_id": req.session_id,
                "message": str(e),
            }
        )


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
