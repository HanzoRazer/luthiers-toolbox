# services/api/app/art_studio/api/design_first_workflow_routes.py
"""
Design-First Workflow API Routes (Bundle 32.7.0)

Lightweight workflow binding for Art Studio:
- Design → Review → Approve → "CAM handoff intent"
- Does NOT execute CAM or create run authority

Prefix: /api/art/design-first-workflow
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

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
    from app.art_studio.services.design_first_workflow_service import (
        build_promotion_intent,
        get_session,
        start_session,
        transition_session,
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
    from art_studio.services.design_first_workflow_service import (
        build_promotion_intent,
        get_session,
        start_session,
        transition_session,
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
