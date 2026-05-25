"""
CAM Drilling Routers (Consolidated)
====================================

DEPRECATED: This module is a thin wrapper for backward compatibility.
Prefer importing directly from focused sub-modules:

    from app.cam.routers.drilling.drill_modal_router import router as drill_router
    from app.cam.routers.drilling.drill_pattern_router import router as pattern_router
    from app.cam.routers.drilling.intent_router import router as intent_router

Sub-modules:
- drill_modal_router.py (2 routes: /gcode, /info)
- drill_pattern_router.py (2 routes: /pattern/gcode, /pattern/info)
- drilling_preview_router.py (1 route: /drilling/preview) [GOVERNED PREVIEW - 5E]
- intent_router.py (1 route: /intent-gcode) [CamIntentV1 - 8I]

Total: 6 routes under /api/cam/drilling

LANE: OPERATION (for /gcode and /intent-gcode endpoints)
LANE: UTILITY (for /info endpoints)
Reference: docs/OPERATION_EXECUTION_GOVERNANCE_v1.md
"""
from fastapi import APIRouter

# Import sub-routers
from .drill_modal_router import router as drill_router
from .drill_pattern_router import router as pattern_router
from .drilling_preview_router import router as preview_router
from .intent_router import router as intent_router

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
router.include_router(preview_router)
router.include_router(intent_router)


__all__ = [
    # Router
    "router",
    # Sub-routers
    "drill_router",
    "pattern_router",
    "preview_router",
    "intent_router",
    # Models (backward compat)
    "Hole",
    "DrillReq",
    "GridSpec",
    "CircleSpec",
    "LineSpec",
    "Pattern",
    "DrillParams",
]
