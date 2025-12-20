"""
Art Studio Workflow Routes

API endpoints for Art Studio workflow integration with Pattern Library.

Endpoints:
- Create workflow from pattern, generator, or snapshot
- Session management (list, get, update design)
- Feasibility evaluation
- Approval/rejection workflow
- Snapshot save/restore

Prefix: /api/art-studio/workflow
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

# Conditional imports for FastAPI context
try:
    from app.art_studio.services.workflow_integration import (
        # Request/Response models
        CreateFromPatternRequest,
        CreateFromGeneratorRequest,
        CreateFromSnapshotRequest,
        EvaluateFeasibilityRequest,
        ApproveSessionRequest,
        RejectSessionRequest,
        RequestRevisionRequest,
        UpdateDesignRequest,
        SaveSnapshotRequest,
        SessionStatusResponse,
        WorkflowCreatedResponse,
        FeasibilityResponse,
        ApprovalResponse,
        SnapshotCreatedResponse,
        GeneratorInfo,
        # Service functions
        create_workflow_from_pattern,
        create_workflow_from_generator,
        create_workflow_from_snapshot,
        evaluate_session_feasibility,
        approve_session,
        reject_session,
        request_session_revision,
        update_session_design,
        save_session_as_snapshot,
        list_active_sessions,
        get_session_status,
        get_available_generators,
    )
except ImportError:
    from art_studio.services.workflow_integration import (
        CreateFromPatternRequest,
        CreateFromGeneratorRequest,
        CreateFromSnapshotRequest,
        EvaluateFeasibilityRequest,
        ApproveSessionRequest,
        RejectSessionRequest,
        RequestRevisionRequest,
        UpdateDesignRequest,
        SaveSnapshotRequest,
        SessionStatusResponse,
        WorkflowCreatedResponse,
        FeasibilityResponse,
        ApprovalResponse,
        SnapshotCreatedResponse,
        GeneratorInfo,
        create_workflow_from_pattern,
        create_workflow_from_generator,
        create_workflow_from_snapshot,
        evaluate_session_feasibility,
        approve_session,
        reject_session,
        request_session_revision,
        update_session_design,
        save_session_as_snapshot,
        list_active_sessions,
        get_session_status,
        get_available_generators,
    )


router = APIRouter(
    prefix="/api/art-studio/workflow",
    tags=["art-studio-workflow"],
)


# =============================================================================
# Session Creation Endpoints
# =============================================================================

@router.post(
    "/from-pattern",
    response_model=WorkflowCreatedResponse,
    summary="Create workflow from pattern",
    description="Create a new workflow session from a saved pattern library item.",
)
def api_create_from_pattern(request: CreateFromPatternRequest) -> WorkflowCreatedResponse:
    """
    Create workflow session from a pattern library item.
    
    1. Loads pattern from store
    2. Generates RosetteParamSpec using pattern's generator
    3. Creates workflow session in DRAFT state
    4. Sets design and context
    5. Returns session ready for feasibility evaluation
    """
    try:
        return create_workflow_from_pattern(request)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create workflow: {str(e)}")


@router.post(
    "/from-generator",
    response_model=WorkflowCreatedResponse,
    summary="Create workflow from generator",
    description="Create a new workflow session directly from a parametric generator.",
)
def api_create_from_generator(request: CreateFromGeneratorRequest) -> WorkflowCreatedResponse:
    """
    Create workflow session directly from a parametric generator.
    
    Skips pattern library - generates spec directly from generator params.
    """
    try:
        return create_workflow_from_generator(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create workflow: {str(e)}")


@router.post(
    "/from-snapshot",
    response_model=WorkflowCreatedResponse,
    summary="Create workflow from snapshot",
    description="Restore a workflow session from a saved snapshot.",
)
def api_create_from_snapshot(request: CreateFromSnapshotRequest) -> WorkflowCreatedResponse:
    """
    Create workflow session from a saved snapshot.
    
    Restores design parameters, context refs, and optionally feasibility.
    """
    try:
        return create_workflow_from_snapshot(request)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to restore snapshot: {str(e)}")


# =============================================================================
# Session Management Endpoints
# =============================================================================

@router.get(
    "/sessions",
    response_model=List[SessionStatusResponse],
    summary="List active sessions",
    description="List all non-archived workflow sessions.",
)
def api_list_sessions(
    limit: int = Query(default=50, ge=1, le=200),
    state: Optional[str] = Query(default=None, description="Filter by state"),
) -> List[SessionStatusResponse]:
    """List active workflow sessions."""
    return list_active_sessions(limit=limit, state_filter=state)


@router.get(
    "/sessions/{session_id}",
    response_model=SessionStatusResponse,
    summary="Get session status",
    description="Get detailed status for a workflow session.",
)
def api_get_session(session_id: str) -> SessionStatusResponse:
    """Get detailed session status."""
    try:
        return get_session_status(session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put(
    "/sessions/{session_id}/design",
    response_model=SessionStatusResponse,
    summary="Update session design",
    description="Update the design parameters for a session.",
)
def api_update_design(session_id: str, request: UpdateDesignRequest) -> SessionStatusResponse:
    """
    Update design parameters for a session.
    
    This clears any existing feasibility and requires re-evaluation.
    """
    try:
        return update_session_design(session_id, request)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# Feasibility & Approval Endpoints
# =============================================================================

@router.post(
    "/sessions/{session_id}/feasibility",
    response_model=FeasibilityResponse,
    summary="Evaluate feasibility",
    description="Run server-side feasibility evaluation for a session.",
)
def api_evaluate_feasibility(
    session_id: str,
    request: Optional[EvaluateFeasibilityRequest] = None,
) -> FeasibilityResponse:
    """
    Evaluate feasibility for a session using RMOS feasibility engine.
    
    1. Requests feasibility (state transition)
    2. Computes feasibility server-side
    3. Stores result (state transition)
    4. Creates run artifact via bridge
    """
    try:
        return evaluate_session_feasibility(session_id, request)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/sessions/{session_id}/approve",
    response_model=ApprovalResponse,
    summary="Approve session",
    description="Approve a session for toolpath generation.",
)
def api_approve_session(session_id: str, request: ApproveSessionRequest) -> ApprovalResponse:
    """
    Approve a session for toolpath generation.
    
    Enforces governance rules (score threshold, risk level).
    """
    try:
        return approve_session(session_id, request)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/sessions/{session_id}/reject",
    response_model=ApprovalResponse,
    summary="Reject session",
    description="Reject a session.",
)
def api_reject_session(session_id: str, request: RejectSessionRequest) -> ApprovalResponse:
    """Reject a session."""
    try:
        return reject_session(session_id, request)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/sessions/{session_id}/request-revision",
    response_model=SessionStatusResponse,
    summary="Request revision",
    description="Request design revision for a session.",
)
def api_request_revision(
    session_id: str,
    request: RequestRevisionRequest,
) -> SessionStatusResponse:
    """
    Request design revision for a session.
    
    Transitions to DESIGN_REVISION_REQUIRED state.
    """
    try:
        return request_session_revision(session_id, request)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# Snapshot Endpoints
# =============================================================================

@router.post(
    "/sessions/{session_id}/save-snapshot",
    response_model=SnapshotCreatedResponse,
    summary="Save as snapshot",
    description="Save current session state as a snapshot.",
)
def api_save_snapshot(session_id: str, request: SaveSnapshotRequest) -> SnapshotCreatedResponse:
    """
    Save current session state as a snapshot.
    
    Captures design parameters, context refs, and feasibility.
    """
    try:
        return save_session_as_snapshot(session_id, request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save snapshot: {str(e)}")


# =============================================================================
# Generator Endpoints
# =============================================================================

@router.get(
    "/generators",
    response_model=List[GeneratorInfo],
    summary="List generators",
    description="List available parametric generators.",
)
def api_list_generators() -> List[GeneratorInfo]:
    """List available parametric generators for UI."""
    return get_available_generators()
