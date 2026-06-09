"""
CAM Pocketing Router

Adaptive pocket-clearing via CamIntentV1 (Dev Order 8J). The intent lane is the
only pocketing route (no legacy consolidated router); mounted by the CAM aggregator
at prefix /api/cam/pocketing -> POST /api/cam/pocketing/intent-gcode.
"""
from fastapi import APIRouter

from .intent_router import router as intent_router

router = APIRouter()
router.include_router(intent_router)

__all__ = ["router"]
