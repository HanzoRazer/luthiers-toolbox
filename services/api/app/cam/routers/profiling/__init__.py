"""
CAM Profiling Router

Perimeter profiling toolpath generation with holding tabs.

Endpoints (under /api/cam/profiling):
    POST /gcode        - Generate profiling G-code with tabs (legacy)
    POST /preview      - Preview tab positions on profile
    GET  /info         - Get profiling operation info
    POST /intent-gcode - Generate profiling G-code via CamIntentV1 (canonical)

The /intent-gcode endpoint is the canonical path for Profile operations
through the unified CamIntentV1 contract. Legacy endpoints remain live
under Feature Parity Migration Policy.
"""

from fastapi import APIRouter

from .profile_router import router as profile_router
from .intent_router import router as intent_router

# Aggregate profiling routers
router = APIRouter()
router.include_router(profile_router)
router.include_router(intent_router)  # No prefix - endpoints define their own paths

__all__ = ["router"]
