# services/api/app/art_studio/api/design_first_workflow_routes.py
"""
Design-First Workflow API Routes (Bundle 32.7.0 + 32.7.6)

Lightweight workflow binding for Art Studio:
- Design → Review → Approve → "CAM handoff intent"
- Does NOT execute CAM or create run authority

Bundle 32.7.6: Added list recent + delete endpoints.

Prefix: /api/art/design-first-workflow
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

# Conditional imports
try:
    from app.art_studio.schemas.workflow_design_first import (
        GetDesignFirstResponse,
        PromotionIntentResponse,
        StartDesignFirstRequest,
        StartDesignFirstResponse,
        TransitionDesignFirstRequest,
        TransitionDesignFirstResponse,
    )
    from app.art_studio.schemas.workflow_sessions import (
        DeleteWorkflowSessionResponse,
        ListWorkflowSessionsResponse,
        WorkflowSessionSummary,
    )
    from app.art_studio.services.design_first_workflow_service import (
        build_promotion_intent,
        get_session,
        start_session,
        transition_session,
    )
    from app.art_studio.stores.design_first_workflow_store import (
        delete_session as store_delete_session,
        list_recent,
    )
except ImportError:
    from art_studio.schemas.workflow_design_first import (
        GetDesignFirstResponse,
        PromotionIntentResponse,
        StartDesignFirstRequest,
        StartDesignFirstResponse,
        TransitionDesignFirstRequest,
        TransitionDesignFirstResponse,
    )
    from art_studio.schemas.workflow_sessions import (
        DeleteWorkflowSessionResponse,
        ListWorkflowSessionsResponse,
        WorkflowSessionSummary,
    )
    from art_studio.services.design_first_workflow_service import (
        build_promotion_intent,
        get_session,
        start_session,
        transition_session,
    )
    from art_studio.stores.design_first_workflow_store import (
        delete_session as store_delete_session,
        list_recent,
    )


router = APIRouter(
    prefix="/api/art/design-first-workflow",
    tags=["Art Studio", "Design-First Workflow"],
)


@router.post("/sessions/start", response_model=StartDesignFirstResponse)
async def workflow_start(req: StartDesignFirstRequest) -> StartDesignFirstResponse:
    """
    Start a new design-first workflow session.
    
    Creates a session in DRAFT state with the provided design parameters.
    """
    sess = start_session(
        mode=req.mode,
        design=req.design,
        feasibility=req.feasibility,
    )
    return StartDesignFirstResponse(session=sess)


@router.get("/sessions/{session_id}", response_model=GetDesignFirstResponse)
async def workflow_get(session_id: str) -> GetDesignFirstResponse:
    """Get a design-first workflow session by ID."""
    try:
        sess = get_session(session_id)
        return GetDesignFirstResponse(session=sess)
    except KeyError:
        raise HTTPException(status_code=404, detail="design_first_session_not_found")


@router.post(
    "/sessions/{session_id}/transition",
    response_model=TransitionDesignFirstResponse,
)
async def workflow_transition(
    session_id: str,
    req: TransitionDesignFirstRequest,
) -> TransitionDesignFirstResponse:
    """
    Transition a session to a new state.
    
    Valid transitions:
    - DRAFT → IN_REVIEW
    - IN_REVIEW → APPROVED | REJECTED | DRAFT
    - REJECTED → DRAFT
    - APPROVED → DRAFT (reopen)
    """
    try:
        sess = transition_session(
            session_id=session_id,
            to_state=req.to_state,
            actor=req.actor,
            note=req.note,
            design=req.design,
            feasibility=req.feasibility,
        )
        return TransitionDesignFirstResponse(session=sess)
    except KeyError:
        raise HTTPException(status_code=404, detail="design_first_session_not_found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/sessions/{session_id}/promotion_intent",
    response_model=PromotionIntentResponse,
)
async def workflow_promotion_intent(session_id: str) -> PromotionIntentResponse:
    """
    Generate a CAM handoff intent payload.
    
    IMPORTANT: This does NOT execute CAM. It returns an intent payload
    that downstream CAM/RMOS lanes may consume for toolpath generation.
    
    Only available for APPROVED sessions.
    """
    try:
        intent = build_promotion_intent(session_id)
        return PromotionIntentResponse(ok=True, intent=intent)
    except KeyError:
        raise HTTPException(status_code=404, detail="design_first_session_not_found")
    except PermissionError:
        return PromotionIntentResponse(ok=False, blocked_reason="workflow_not_approved")


# ==========================================================================
# Bundle 32.7.6: List recent + Delete endpoints
# ==========================================================================


@router.get("/sessions/recent", response_model=ListWorkflowSessionsResponse)
async def workflow_list_recent(
    limit: int = Query(50, ge=1, le=200),
    cursor: Optional[str] = Query(None),
) -> ListWorkflowSessionsResponse:
    """
    List recent design-first workflow sessions ordered by updated_at desc.
    
    Supports cursor-based pagination.
    """
    items, next_cursor = list_recent(limit=limit, cursor=cursor)

    out = []
    for s in items:
        risk = None
        try:
            feas = s.feasibility or {}
            risk = feas.get("risk_bucket") or feas.get("risk") or feas.get("riskLevel")
        except Exception:
            risk = None

        out.append(
            WorkflowSessionSummary(
                session_id=s.session_id,
                mode=s.mode.value if hasattr(s.mode, "value") else str(s.mode),
                state=s.state.value if hasattr(s.state, "value") else str(s.state),
                updated_at=s.updated_at,
                created_at=s.created_at,
                risk_bucket=str(risk) if risk is not None else None,
            )
        )

    return ListWorkflowSessionsResponse(items=out, next_cursor=next_cursor)


@router.delete("/sessions/{session_id}", response_model=DeleteWorkflowSessionResponse)
async def workflow_delete(session_id: str) -> DeleteWorkflowSessionResponse:
    """
    Delete a design-first workflow session.
    
    Returns 404 if session not found.
    """
    ok = store_delete_session(session_id)
    if not ok:
        raise HTTPException(status_code=404, detail="design_first_session_not_found")
    return DeleteWorkflowSessionResponse(ok=True, session_id=session_id)
