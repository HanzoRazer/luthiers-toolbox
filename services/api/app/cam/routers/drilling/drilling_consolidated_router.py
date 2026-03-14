"""
CAM Drilling Routers (Consolidated)
====================================

DEPRECATED: This module is a thin wrapper for backward compatibility.
Prefer importing directly from focused sub-modules:

    from app.cam.routers.drilling.drill_modal_router import router as drill_router
    from app.cam.routers.drilling.drill_pattern_router import router as pattern_router

Sub-modules:
- drill_modal_router.py (2 routes: /gcode, /info)
- drill_pattern_router.py (2 routes: /pattern/gcode, /pattern/info)

Total: 4 routes under /api/cam/drilling

LANE: OPERATION (for /gcode endpoints)
LANE: UTILITY (for /info endpoints)
Reference: docs/OPERATION_EXECUTION_GOVERNANCE_v1.md
"""
from fastapi import APIRouter

# Import sub-routers
from .drill_modal_router import router as drill_router
from .drill_pattern_router import router as pattern_router

# Re-export models for backward compatibility
from .drill_modal_router import Hole, DrillReq
from .drill_pattern_router import (
    GridSpec,
    CircleSpec,
    LineSpec,
    Pattern,
    DrillParams,
)

# Aggregate router
router = APIRouter(tags=["CAM", "Drilling"])

# Mount sub-routers (no additional prefix - endpoints already have paths)
router.include_router(drill_router)
router.include_router(pattern_router)


__all__ = [
    # Router
    "router",
    # Sub-routers
    "drill_router",
    "pattern_router",
    # Models (backward compat)
    "Hole",
    "DrillReq",
    "GridSpec",
    "CircleSpec",
    "LineSpec",
    "Pattern",
    "DrillParams",
]
