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
        DesignFirstState,
        GetDesignFirstResponse,
        PromotionIntentResponse,
        PromotionIntentV1Response,
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
    from app.art_studio.schemas.cam_promotion_request import (
        CamPromotionRequestV1,
        CamPromotionResponse,
    )
    from app.art_studio.services.design_first_workflow_service import (
        build_promotion_intent,
        build_promotion_intent_v1,
        get_session,
        start_session,
        transition_session,
    )
    from app.art_studio.schemas.promotion_intent import PromotionIntentV1
    from app.art_studio.stores.design_first_workflow_store import (
        delete_session as store_delete_session,
        list_recent,
    )
    from app.art_studio.services.cam_promotion_service import (
        create_or_get_promotion_request,
        get_promotion_request,
    )
except ImportError:
    from art_studio.schemas.workflow_design_first import (
        DesignFirstState,
        GetDesignFirstResponse,
        PromotionIntentResponse,
        PromotionIntentV1Response,
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
    from art_studio.schemas.cam_promotion_request import (
        CamPromotionRequestV1,
        CamPromotionResponse,
    )
    from art_studio.services.design_first_workflow_service import (
        build_promotion_intent,
        build_promotion_intent_v1,
        get_session,
        start_session,
        transition_session,
    )
    from art_studio.schemas.promotion_intent import PromotionIntentV1
    from art_studio.stores.design_first_workflow_store import (
        delete_session as store_delete_session,
        list_recent,
    )
    from art_studio.services.cam_promotion_service import (
        create_or_get_promotion_request,
        get_promotion_request,
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
# Bundle 32.8.5: GET /promotion_intent.json - Canonical PromotionIntentV1 Export
# ==========================================================================


@router.get(
    "/sessions/{session_id}/promotion_intent.json",
    response_model=PromotionIntentV1,
)
async def workflow_promotion_intent_export(
    session_id: str,
    tool_id: Optional[str] = Query(None, description="Override tool_id in context_refs"),
    material_id: Optional[str] = Query(None, description="Override material_id in context_refs"),
    machine_profile_id: Optional[str] = Query(None, description="Override machine_profile_id in context_refs"),
    cam_profile_id: Optional[str] = Query(None, description="Override requested_cam_profile_id"),
    risk_tolerance: Optional[str] = Query(None, description="Override risk_tolerance (GREEN_ONLY or ALLOW_YELLOW)"),
) -> PromotionIntentV1:
    """
    Export canonical PromotionIntentV1 payload as JSON.
    
    This is the strict contract for CI/CD validation and downstream consumers.
    Returns the raw PromotionIntentV1 schema (no wrapper).
    
    Query params allow overriding context_refs for testing different configurations.
    """
    try:
        session = get_session(session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="design_first_session_not_found")
    
    if session.state != DesignFirstState.APPROVED:
        raise HTTPException(status_code=403, detail="workflow_not_approved")
    
    # Build context_refs from query params
    context_refs = {}
    if tool_id:
        context_refs["tool_id"] = tool_id
    if material_id:
        context_refs["material_id"] = material_id
    if machine_profile_id:
        context_refs["machine_profile_id"] = machine_profile_id
    
    # Normalize risk_tolerance
    risk_tol = None
    if risk_tolerance:
        rt_upper = risk_tolerance.upper()
        if rt_upper in ("GREEN_ONLY", "ALLOW_YELLOW"):
            risk_tol = rt_upper
    
    return build_promotion_intent_v1(
        session=session,
        requested_cam_profile_id=cam_profile_id,
        context_refs=context_refs if context_refs else None,
        risk_tolerance=risk_tol,
    )




# ==========================================================================
# Bundle 32.8.5: POST /promotion_intent_v1 - Wrapper for canonical v1
# ==========================================================================


@router.post(
    "/sessions/{session_id}/promotion_intent_v1",
    response_model=PromotionIntentV1Response,
)
async def workflow_promotion_intent_v1(
    session_id: str,
    tool_id: Optional[str] = Query(None, description="Override tool_id in context_refs"),
    material_id: Optional[str] = Query(None, description="Override material_id in context_refs"),
    machine_profile_id: Optional[str] = Query(None, description="Override machine_profile_id in context_refs"),
    cam_profile_id: Optional[str] = Query(None, description="Override requested_cam_profile_id"),
    risk_tolerance: Optional[str] = Query(None, description="Override risk_tolerance (GREEN_ONLY or ALLOW_YELLOW)"),
) -> PromotionIntentV1Response:
    """
    Generate canonical PromotionIntentV1 payload with wrapper envelope.

    Returns { ok, intent, blocked_reason } for ergonomic UI consumption.
    The intent field contains the canonical PromotionIntentV1 when approved.

    Query params allow overriding context_refs for testing different configurations.
    """
    try:
        session = get_session(session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="design_first_session_not_found")

    if session.state != DesignFirstState.APPROVED:
        return PromotionIntentV1Response(ok=False, blocked_reason="workflow_not_approved")

    # Build context_refs from query params
    context_refs = {}
    if tool_id:
        context_refs["tool_id"] = tool_id
    if material_id:
        context_refs["material_id"] = material_id
    if machine_profile_id:
        context_refs["machine_profile_id"] = machine_profile_id

    # Normalize risk_tolerance
    risk_tol = None
    if risk_tolerance:
        rt_upper = risk_tolerance.upper()
        if rt_upper in ("GREEN_ONLY", "ALLOW_YELLOW"):
            risk_tol = rt_upper

    intent = build_promotion_intent_v1(
        session=session,
        requested_cam_profile_id=cam_profile_id,
        context_refs=context_refs if context_refs else None,
        risk_tolerance=risk_tol,
    )

    return PromotionIntentV1Response(ok=True, intent=intent)

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


# ==========================================================================
# Phase 33.0: CAM Promotion Request Endpoint
# ==========================================================================


@router.post(
    "/sessions/{session_id}/promote_to_cam",
    response_model=CamPromotionResponse,
)
async def workflow_promote_to_cam(
    session_id: str,
    cam_profile_id: Optional[str] = Query(None, description="Requested CAM profile ID"),
) -> CamPromotionResponse:
    """
    Promote an approved session to a CAM request.
    
    Phase 33.0: Creates a downstream-safe CAM promotion request artifact.
    
    This does NOT:
      - Execute CAM or toolpath generation
      - Generate G-code
      - Create manufacturing authority or runs
    
    It only creates a handoff object that downstream CAM consumers may pick up.
    
    Idempotency: Re-promoting the same intent returns the same request ID.
    
    Returns:
      - ok=True + request: Promotion request created/retrieved
      - ok=False + blocked_reason: Session not approved or other gate failure
    """
    try:
        session = get_session(session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="design_first_session_not_found")
    
    # Gate: Only APPROVED sessions can promote
    if session.state != DesignFirstState.APPROVED:
        return CamPromotionResponse(ok=False, blocked_reason="workflow_not_approved")
    
    # Build the canonical v1 intent
    try:
        intent = build_promotion_intent_v1(
            session=session,
            requested_cam_profile_id=cam_profile_id,
        )
    except ValueError as e:
        return CamPromotionResponse(ok=False, blocked_reason=str(e))
    
    # Gate: Must be v1 intent
    if intent.intent_version != "v1":
        return CamPromotionResponse(ok=False, blocked_reason="unsupported_intent_version")
    
    # Create or retrieve promotion request (idempotent)
    request = create_or_get_promotion_request(intent)
    
    return CamPromotionResponse(ok=True, request=request)


@router.get(
    "/cam-promotion/requests/{request_id}",
    response_model=CamPromotionRequestV1,
)
async def get_cam_promotion_request(request_id: str) -> CamPromotionRequestV1:
    """
    Get a CAM promotion request by ID.
    
    Returns 404 if request not found.
    """
    request = get_promotion_request(request_id)
    if not request:
        raise HTTPException(status_code=404, detail="promotion_request_not_found")
    return request
