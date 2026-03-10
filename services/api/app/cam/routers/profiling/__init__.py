"""
CAM Profiling Router

Perimeter profiling toolpath generation with holding tabs.

Endpoints (under /api/cam/profiling):
    POST /gcode        - Generate profiling G-code with tabs
    POST /preview      - Preview tab positions on profile
    GET  /info         - Get profiling operation info
"""

from fastapi import APIRouter

from .profile_router import router as profile_router

# Aggregate profiling routers
router = APIRouter()
router.include_router(profile_router)

__all__ = ["router"]
