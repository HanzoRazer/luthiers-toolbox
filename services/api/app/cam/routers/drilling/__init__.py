"""
CAM Drilling Routers

Modal drilling (G81, G83) and pattern drilling operations.

Migrated from:
    - routers/cam_drill_router.py        → drill_router.py
    - routers/cam_drill_pattern_router.py → pattern_router.py

Endpoints (under /api/cam/drilling):
    POST /gcode          - Generate drilling G-code
    GET  /info           - Get drilling operation info
    POST /pattern/gcode  - Generate pattern drilling G-code
    GET  /pattern/info   - Get pattern info
"""

from fastapi import APIRouter

from .drill_router import router as drill_router
from .pattern_router import router as pattern_router

# Aggregate all drilling routers
router = APIRouter()
router.include_router(drill_router)
router.include_router(pattern_router, prefix="/pattern")

__all__ = ["router", "drill_router", "pattern_router"]
