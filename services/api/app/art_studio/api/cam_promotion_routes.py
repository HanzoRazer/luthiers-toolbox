from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.art_studio.schemas.cam_promotion_request import CamPromotionResponse
from app.art_studio.services.cam_promotion_service import create_or_get_promotion_request
from app.art_studio.services.design_first_workflow_service import build_promotion_intent_v1_for_session_id


router = APIRouter(
    prefix="/api/art/design-first-workflow",
    tags=["Art Studio", "CAM Promotion Bridge"],
)


@router.post(
    "/sessions/{session_id}/promote_to_cam",
    response_model=CamPromotionResponse,
)
async def promote_to_cam(session_id: str) -> CamPromotionResponse:
    """
    Phase 33.0: Promotion bridge.
    Converts APPROVED PromotionIntentV1 into a queued CamPromotionRequestV1.
    """
    try:
        intent = build_promotion_intent_v1_for_session_id(session_id)
    except PermissionError as e:
        return CamPromotionResponse(ok=False, request=None, blocked_reason=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    req = create_or_get_promotion_request(intent)
    return CamPromotionResponse(ok=True, request=req, blocked_reason=None)
