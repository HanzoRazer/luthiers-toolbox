"""WP-3: RMOS Workflow state-transition endpoints.

Extracted from rmos_workflow_router.py to reduce god-object size.
Contains all state transition endpoints (design, context, feasibility,
approve, reject, toolpaths, revision, archive).
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Header

from app.workflow.state_machine import (
    ActorRole,
    FeasibilityResult,
    ToolpathPlanRef,
    RiskBucket,
    approve,
    reject,
    set_context,
    set_design,
    request_feasibility,
    store_feasibility,
    request_toolpaths,
    store_toolpaths,
    require_revision,
    archive,
    next_step_hint,
)
from app.workflow.session_store import STORE
from app.workflow.workflow_runs_bridge import get_workflow_runs_bridge
from .rmos_workflow_schemas import (
    SetContextRequest,
    SetDesignRequest,
    StoreFeasibilityRequest,
    ApproveRequest,
    RejectRequest,
    StoreToolpathsRequest,
    RevisionRequest,
    ApproveResponse,
    TransitionResponse,
)

transitions_router = APIRouter()


# ---------------------------------------------------------------------------
# Endpoints - State Transitions
# ---------------------------------------------------------------------------

@transitions_router.post("/sessions/{session_id}/design", response_model=TransitionResponse)
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
    except HTTPException:
        raise  # WP-1: pass through HTTPException
    except Exception as e:  # WP-1: governance catch-all — HTTP endpoint
        raise HTTPException(status_code=409, detail={"error": "TRANSITION_BLOCKED", "message": str(e)})
    
    return TransitionResponse(
        session_id=session.session_id,
        state=session.state.value,
        previous_state=prev_state,
        next_step=next_step_hint(session),
    )


@transitions_router.post("/sessions/{session_id}/context", response_model=TransitionResponse)
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
    except HTTPException:
        raise  # WP-1: pass through HTTPException
    except Exception as e:  # WP-1: governance catch-all — HTTP endpoint
        raise HTTPException(status_code=409, detail={"error": "TRANSITION_BLOCKED", "message": str(e)})
    
    return TransitionResponse(
        session_id=session.session_id,
        state=session.state.value,
        previous_state=prev_state,
        next_step=next_step_hint(session),
    )


@transitions_router.post("/sessions/{session_id}/feasibility/request", response_model=TransitionResponse)
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
    except HTTPException:
        raise  # WP-1: pass through HTTPException
    except Exception as e:  # WP-1: governance catch-all — HTTP endpoint
        raise HTTPException(status_code=409, detail={"error": "TRANSITION_BLOCKED", "message": str(e)})
    
    return TransitionResponse(
        session_id=session.session_id,
        state=session.state.value,
        previous_state=prev_state,
        next_step=next_step_hint(session),
    )


@transitions_router.post("/sessions/{session_id}/feasibility/store", response_model=TransitionResponse)
def store_session_feasibility(
    session_id: str,
    req: StoreFeasibilityRequest,
    x_request_id: Optional[str] = Header(default=None, alias="X-Request-ID"),
) -> TransitionResponse:
    """Store feasibility result."""
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
    except HTTPException:
        raise  # WP-1: pass through HTTPException
    except Exception as e:  # WP-1: governance catch-all — HTTP endpoint
        raise HTTPException(status_code=409, detail={"error": "TRANSITION_BLOCKED", "message": str(e)})
    
    return TransitionResponse(
        session_id=session.session_id,
        state=session.state.value,
        previous_state=prev_state,
        next_step=next_step_hint(session),
        run_artifact_id=artifact_ref.artifact_id if artifact_ref else None,
    )


@transitions_router.post("/approve", response_model=ApproveResponse)
def approve_session(
    req: ApproveRequest,
    x_request_id: Optional[str] = Header(default=None, alias="X-Request-ID"),
) -> ApproveResponse:
    """Approve a workflow session for toolpath generation."""
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
    except HTTPException:
        raise  # WP-1: pass through HTTPException
    except Exception as e:  # WP-1: governance catch-all — HTTP endpoint
        # Approval may be blocked by governance rules
        raise HTTPException(
            status_code=409,
            detail={
                "error": "APPROVAL_BLOCKED",
                "session_id": req.session_id,
                "message": str(e),
            }
        )


@transitions_router.post("/reject", response_model=TransitionResponse)
def reject_session(
    req: RejectRequest,
    x_request_id: Optional[str] = Header(default=None, alias="X-Request-ID"),
) -> TransitionResponse:
    """Reject a workflow session."""
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
    except HTTPException:
        raise  # WP-1: pass through HTTPException
    except Exception as e:  # WP-1: governance catch-all — HTTP endpoint
        raise HTTPException(status_code=409, detail={"error": "TRANSITION_BLOCKED", "message": str(e)})
    
    return TransitionResponse(
        session_id=session.session_id,
        state=session.state.value,
        previous_state=prev_state,
        next_step=next_step_hint(session),
        run_artifact_id=artifact_ref.artifact_id if artifact_ref else None,
    )


@transitions_router.post("/sessions/{session_id}/toolpaths/request", response_model=TransitionResponse)
def request_session_toolpaths(
    session_id: str,
    x_request_id: Optional[str] = Header(default=None, alias="X-Request-ID"),
) -> TransitionResponse:
    """Request toolpath generation."""
    session = STORE.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail={"error": "SESSION_NOT_FOUND", "session_id": session_id})
    
    prev_state = session.state.value
    try:
        request_toolpaths(session, actor=ActorRole.USER)
        STORE.put(session)
    except HTTPException:
        raise  # WP-1: pass through HTTPException
    except Exception as e:  # WP-1: governance catch-all — HTTP endpoint
        raise HTTPException(status_code=409, detail={"error": "TRANSITION_BLOCKED", "message": str(e)})
    
    return TransitionResponse(
        session_id=session.session_id,
        state=session.state.value,
        previous_state=prev_state,
        next_step=next_step_hint(session),
    )


@transitions_router.post("/sessions/{session_id}/toolpaths/store", response_model=TransitionResponse)
def store_session_toolpaths(
    session_id: str,
    req: StoreToolpathsRequest,
    x_request_id: Optional[str] = Header(default=None, alias="X-Request-ID"),
) -> TransitionResponse:
    """Store generated toolpaths."""
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
    except HTTPException:
        raise  # WP-1: pass through HTTPException
    except Exception as e:  # WP-1: governance catch-all — HTTP endpoint
        raise HTTPException(status_code=409, detail={"error": "TRANSITION_BLOCKED", "message": str(e)})
    
    return TransitionResponse(
        session_id=session.session_id,
        state=session.state.value,
        previous_state=prev_state,
        next_step=next_step_hint(session),
        run_artifact_id=artifact_ref.artifact_id if artifact_ref else None,
    )


@transitions_router.post("/sessions/{session_id}/revision", response_model=TransitionResponse)
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
    except HTTPException:
        raise  # WP-1: pass through HTTPException
    except Exception as e:  # WP-1: governance catch-all — HTTP endpoint
        raise HTTPException(status_code=409, detail={"error": "TRANSITION_BLOCKED", "message": str(e)})
    
    return TransitionResponse(
        session_id=session.session_id,
        state=session.state.value,
        previous_state=prev_state,
        next_step=next_step_hint(session),
    )


@transitions_router.post("/sessions/{session_id}/archive", response_model=TransitionResponse)
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
    except HTTPException:
        raise  # WP-1: pass through HTTPException
    except Exception as e:  # WP-1: governance catch-all — HTTP endpoint
        raise HTTPException(status_code=409, detail={"error": "TRANSITION_BLOCKED", "message": str(e)})
    
    return TransitionResponse(
        session_id=session.session_id,
        state=session.state.value,
        previous_state=prev_state,
        next_step=next_step_hint(session),
    )
