"""
CAM V-Carve Production Router

Production-quality V-carve toolpath generation with chipload calculations.

Endpoints (under /api/cam/vcarve):
    POST /production/gcode    - Generate production V-carve G-code
    POST /production/preview  - Preview V-carve parameters
    GET  /info                - Get V-carve operation info

Note: This supplements the existing /api/cam/toolpath/vcarve endpoints
with production-quality chipload-based calculations.
"""

from fastapi import APIRouter

from .production_router import router as production_router

# Aggregate vcarve routers
router = APIRouter()
router.include_router(production_router, prefix="/production")

__all__ = ["router"]
