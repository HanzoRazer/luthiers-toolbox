"""
CAM V-Carve Routers

V-carve toolpath generation with production chipload calculations
and CamIntentV1 unified contract support.

Endpoints (under /api/cam/vcarve):
    POST /production/gcode    - Generate production V-carve G-code (legacy)
    POST /production/preview  - Preview V-carve parameters
    POST /intent-gcode        - Generate V-carve G-code via CamIntentV1 (canonical)
    GET  /info                - Get V-carve operation info

The /intent-gcode endpoint is the canonical path for V-Carve operations
through the unified CamIntentV1 contract. Legacy endpoints remain live
under Feature Parity Migration Policy.
"""

from fastapi import APIRouter

from .production_router import router as production_router
from .intent_router import router as intent_router

# Aggregate vcarve routers
router = APIRouter()
router.include_router(production_router, prefix="/production")
router.include_router(intent_router)  # No prefix - endpoints define their own paths

__all__ = ["router"]
