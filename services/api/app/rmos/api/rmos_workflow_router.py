"""
RMOS Workflow Router - Session Management API

Provides HTTP endpoints for workflow session lifecycle:
- Create new sessions
- Set context and design
- Request and store feasibility
- Approve/reject sessions
- Request and store toolpaths

Integrated with Runs V2 via WorkflowRunsBridge.
Every significant state transition creates an immutable RunArtifact.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, Field

from app.workflow.state_machine import (
    ActorRole,
    WorkflowMode,
    WorkflowSession,
    WorkflowState,
    FeasibilityResult,
    ToolpathPlanRef,
    RiskBucket,
    approve,
    reject,
    new_session,
    set_context,
    set_design,
    request_feasibility,
    store_feasibility,
    request_toolpaths,
    store_toolpaths,
    require_revision,
    archive,
    next_step_hint,
    to_comparable_snapshot,
)
from app.workflow.session_store import STORE
from app.workflow.workflow_runs_bridge import get_workflow_runs_bridge

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


class SetContextRequest(BaseModel):
    session_id: str
    context: Dict[str, Any]


class SetDesignRequest(BaseModel):
    session_id: str
    design: Dict[str, Any]


class StoreFeasibilityRequest(BaseModel):
    session_id: str
    score: float = Field(..., ge=0.0, le=100.0)
    risk_bucket: str = Field(..., description="GREEN, YELLOW, RED, UNKNOWN")
    warnings: list[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)


class ApproveRequest(BaseModel):
    session_id: str
    actor: ActorRole = ActorRole.OPERATOR
    note: Optional[str] = None


class RejectRequest(BaseModel):
    session_id: str
    actor: ActorRole = ActorRole.OPERATOR
    reason: str


class StoreToolpathsRequest(BaseModel):
    session_id: str
    plan_id: str
    toolpaths_data: Optional[Dict[str, Any]] = None
    gcode_text: Optional[str] = None
    meta: Dict[str, Any] = Field(default_factory=dict)


class RevisionRequest(BaseModel):
    session_id: str
    actor: ActorRole = ActorRole.SYSTEM
    reason: str


class ApproveResponse(BaseModel):
    session_id: str
    state: str
    approved: bool
    message: str
    run_artifact_id: Optional[str] = None


class SessionStateResponse(BaseModel):
    session_id: str
    mode: str
    state: str
    next_step: str
    events_count: int
    last_feasibility_artifact_id: Optional[str] = None
    last_toolpaths_artifact_id: Optional[str] = None


class TransitionResponse(BaseModel):
    session_id: str
    state: str
    previous_state: str
    next_step: str
    run_artifact_id: Optional[str] = None


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
# Endpoints - State Transitions
# ---------------------------------------------------------------------------

@router.post("/sessions/{session_id}/design", response_model=TransitionResponse)
def set_session_design(
    session_id: str,
    req: SetDesignRequest,
) -> TransitionResponse:
    """
    Set design parameters for a session.
    """
    session = STORE.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail={"error": "SESSION_NOT_FOUND", "session_id": session_id})
    
    prev_state = session.state.value
    try:
        set_design(session, req.design, actor=ActorRole.USER)
        STORE.put(session)
    except Exception as e:
        raise HTTPException(status_code=409, detail={"error": "TRANSITION_BLOCKED", "message": str(e)})
    
    return TransitionResponse(
        session_id=session.session_id,
        state=session.state.value,
        previous_state=prev_state,
        next_step=next_step_hint(session),
    )


@router.post("/sessions/{session_id}/context", response_model=TransitionResponse)
def set_session_context(
    session_id: str,
    req: SetContextRequest,
) -> TransitionResponse:
    """
    Set context (tool, material, machine) for a session.
    
    Transitions from DRAFT → CONTEXT_READY.
    """
    session = STORE.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail={"error": "SESSION_NOT_FOUND", "session_id": session_id})
    
    prev_state = session.state.value
    try:
        set_context(session, req.context, actor=ActorRole.USER)
        STORE.put(session)
    except Exception as e:
        raise HTTPException(status_code=409, detail={"error": "TRANSITION_BLOCKED", "message": str(e)})
    
    return TransitionResponse(
        session_id=session.session_id,
        state=session.state.value,
        previous_state=prev_state,
        next_step=next_step_hint(session),
    )


@router.post("/sessions/{session_id}/feasibility/request", response_model=TransitionResponse)
def request_session_feasibility(
    session_id: str,
    x_request_id: Optional[str] = Header(default=None, alias="X-Request-ID"),
) -> TransitionResponse:
    """
    Request feasibility evaluation.
    
    Transitions from CONTEXT_READY → FEASIBILITY_REQUESTED.
    """
    session = STORE.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail={"error": "SESSION_NOT_FOUND", "session_id": session_id})
    
    prev_state = session.state.value
    try:
        request_feasibility(session, actor=ActorRole.USER)
        STORE.put(session)
    except Exception as e:
        raise HTTPException(status_code=409, detail={"error": "TRANSITION_BLOCKED", "message": str(e)})
    
    return TransitionResponse(
        session_id=session.session_id,
        state=session.state.value,
        previous_state=prev_state,
        next_step=next_step_hint(session),
    )


@router.post("/sessions/{session_id}/feasibility/store", response_model=TransitionResponse)
def store_session_feasibility(
    session_id: str,
    req: StoreFeasibilityRequest,
    x_request_id: Optional[str] = Header(default=None, alias="X-Request-ID"),
) -> TransitionResponse:
    """
    Store feasibility result.
    
    Transitions from FEASIBILITY_REQUESTED → FEASIBILITY_READY.
    Creates a RunArtifact for the feasibility evaluation.
    """
    session = STORE.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail={"error": "SESSION_NOT_FOUND", "session_id": session_id})
    
    # Parse risk bucket
    try:
        risk_bucket = RiskBucket(req.risk_bucket.upper())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail={"error": "INVALID_RISK_BUCKET", "valid": ["GREEN", "YELLOW", "RED", "UNKNOWN"]}
        )
    
    # Build feasibility result
    result = FeasibilityResult(
        score=req.score,
        risk_bucket=risk_bucket,
        warnings=req.warnings,
        meta=req.meta,
    )
    
    prev_state = session.state.value
    try:
        store_feasibility(session, result, actor=ActorRole.SYSTEM)
        
        # Create RunArtifact via bridge
        bridge = get_workflow_runs_bridge()
        artifact_ref = bridge.on_feasibility_stored(session, request_id=x_request_id)
        
        if artifact_ref:
            session.last_feasibility_artifact = artifact_ref
        
        STORE.put(session)
    except Exception as e:
        raise HTTPException(status_code=409, detail={"error": "TRANSITION_BLOCKED", "message": str(e)})
    
    return TransitionResponse(
        session_id=session.session_id,
        state=session.state.value,
        previous_state=prev_state,
        next_step=next_step_hint(session),
        run_artifact_id=artifact_ref.artifact_id if artifact_ref else None,
    )


@router.post("/approve", response_model=ApproveResponse)
def approve_session(
    req: ApproveRequest,
    x_request_id: Optional[str] = Header(default=None, alias="X-Request-ID"),
) -> ApproveResponse:
    """
    Approve a workflow session for toolpath generation.

    Requires session to be in FEASIBILITY_READY state.
    Enforces governance rules (score threshold, risk level).
    Creates a RunArtifact for the approval.
    """
    session = STORE.get(req.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail={"error": "SESSION_NOT_FOUND", "session_id": req.session_id})

    artifact_ref = None
    try:
        approve(session, actor=req.actor, note=req.note)
        
        # Create RunArtifact via bridge
        bridge = get_workflow_runs_bridge()
        artifact_ref = bridge.on_approved(session, request_id=x_request_id)
        
        STORE.put(session)
        return ApproveResponse(
            session_id=session.session_id,
            state=session.state.value,
            approved=True,
            message="Session approved for toolpath generation.",
            run_artifact_id=artifact_ref.artifact_id if artifact_ref else None,
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


@router.post("/reject", response_model=TransitionResponse)
def reject_session(
    req: RejectRequest,
    x_request_id: Optional[str] = Header(default=None, alias="X-Request-ID"),
) -> TransitionResponse:
    """
    Reject a workflow session.
    
    Requires session to be in FEASIBILITY_READY state.
    Creates a RunArtifact for the rejection.
    """
    session = STORE.get(req.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail={"error": "SESSION_NOT_FOUND", "session_id": req.session_id})
    
    prev_state = session.state.value
    artifact_ref = None
    
    try:
        reject(session, actor=req.actor, reason=req.reason)
        
        # Create RunArtifact via bridge
        bridge = get_workflow_runs_bridge()
        artifact_ref = bridge.on_rejected(session, reason=req.reason, request_id=x_request_id)
        
        STORE.put(session)
    except Exception as e:
        raise HTTPException(status_code=409, detail={"error": "TRANSITION_BLOCKED", "message": str(e)})
    
    return TransitionResponse(
        session_id=session.session_id,
        state=session.state.value,
        previous_state=prev_state,
        next_step=next_step_hint(session),
        run_artifact_id=artifact_ref.artifact_id if artifact_ref else None,
    )


@router.post("/sessions/{session_id}/toolpaths/request", response_model=TransitionResponse)
def request_session_toolpaths(
    session_id: str,
    x_request_id: Optional[str] = Header(default=None, alias="X-Request-ID"),
) -> TransitionResponse:
    """
    Request toolpath generation.
    
    Transitions from APPROVED → TOOLPATHS_REQUESTED.
    Enforces server-side feasibility requirement.
    """
    session = STORE.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail={"error": "SESSION_NOT_FOUND", "session_id": session_id})
    
    prev_state = session.state.value
    try:
        request_toolpaths(session, actor=ActorRole.USER)
        STORE.put(session)
    except Exception as e:
        raise HTTPException(status_code=409, detail={"error": "TRANSITION_BLOCKED", "message": str(e)})
    
    return TransitionResponse(
        session_id=session.session_id,
        state=session.state.value,
        previous_state=prev_state,
        next_step=next_step_hint(session),
    )


@router.post("/sessions/{session_id}/toolpaths/store", response_model=TransitionResponse)
def store_session_toolpaths(
    session_id: str,
    req: StoreToolpathsRequest,
    x_request_id: Optional[str] = Header(default=None, alias="X-Request-ID"),
) -> TransitionResponse:
    """
    Store generated toolpaths.
    
    Transitions from TOOLPATHS_REQUESTED → TOOLPATHS_READY.
    Creates a RunArtifact for the toolpath generation.
    """
    session = STORE.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail={"error": "SESSION_NOT_FOUND", "session_id": session_id})
    
    # Build toolpath plan reference
    plan_ref = ToolpathPlanRef(
        plan_id=req.plan_id,
        meta=req.meta,
    )
    
    prev_state = session.state.value
    try:
        store_toolpaths(session, plan_ref, actor=ActorRole.SYSTEM)
        
        # Create RunArtifact via bridge
        bridge = get_workflow_runs_bridge()
        artifact_ref = bridge.on_toolpaths_stored(
            session,
            toolpaths_data=req.toolpaths_data,
            gcode_text=req.gcode_text,
            request_id=x_request_id,
        )
        
        if artifact_ref:
            session.last_toolpaths_artifact = artifact_ref
        
        STORE.put(session)
    except Exception as e:
        raise HTTPException(status_code=409, detail={"error": "TRANSITION_BLOCKED", "message": str(e)})
    
    return TransitionResponse(
        session_id=session.session_id,
        state=session.state.value,
        previous_state=prev_state,
        next_step=next_step_hint(session),
        run_artifact_id=artifact_ref.artifact_id if artifact_ref else None,
    )


@router.post("/sessions/{session_id}/revision", response_model=TransitionResponse)
def require_session_revision(
    session_id: str,
    req: RevisionRequest,
) -> TransitionResponse:
    """
    Require design revision.
    
    Transitions from FEASIBILITY_READY → DESIGN_REVISION_REQUIRED.
    """
    session = STORE.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail={"error": "SESSION_NOT_FOUND", "session_id": session_id})
    
    prev_state = session.state.value
    try:
        require_revision(session, actor=req.actor, reason=req.reason)
        STORE.put(session)
    except Exception as e:
        raise HTTPException(status_code=409, detail={"error": "TRANSITION_BLOCKED", "message": str(e)})
    
    return TransitionResponse(
        session_id=session.session_id,
        state=session.state.value,
        previous_state=prev_state,
        next_step=next_step_hint(session),
    )


@router.post("/sessions/{session_id}/archive", response_model=TransitionResponse)
def archive_session(
    session_id: str,
    note: Optional[str] = None,
) -> TransitionResponse:
    """
    Archive a completed or rejected session.
    """
    session = STORE.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail={"error": "SESSION_NOT_FOUND", "session_id": session_id})
    
    prev_state = session.state.value
    try:
        archive(session, actor=ActorRole.USER, note=note)
        STORE.put(session)
    except Exception as e:
        raise HTTPException(status_code=409, detail={"error": "TRANSITION_BLOCKED", "message": str(e)})
    
    return TransitionResponse(
        session_id=session.session_id,
        state=session.state.value,
        previous_state=prev_state,
        next_step=next_step_hint(session),
    )


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

