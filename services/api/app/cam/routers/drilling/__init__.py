"""
CAM Drilling Routers Package
============================

Modal drilling (G81, G83), pattern drilling, and governed preview operations.

Sub-modules:
- drill_modal_router.py (2 routes: /gcode, /info)
- drill_pattern_router.py (2 routes: /pattern/gcode, /pattern/info)
- drilling_preview_router.py (1 route: /drilling/preview) [GOVERNED PREVIEW - 5E]

Total: 5 routes under /api/cam/drilling
"""
from fastapi import APIRouter

from .drilling_consolidated_router import (
    router as _consolidated_router,
    drill_router,
    pattern_router,
    preview_router,
    # Re-export models
    Hole,
    DrillReq,
    GridSpec,
    CircleSpec,
    LineSpec,
    Pattern,
    DrillParams,
)
from .intent_router import router as intent_router

# Aggregate legacy consolidated drilling routes + the CamIntentV1 intent lane (8I).
# Mounted by the CAM aggregator at prefix /api/cam/drilling; intent_router defines
# its own /intent-gcode path -> POST /api/cam/drilling/intent-gcode.
router = APIRouter()
router.include_router(_consolidated_router)
router.include_router(intent_router)

__all__ = [
    # Main router
    "router",
    # Sub-routers
    "drill_router",
    "pattern_router",
    "preview_router",
    # Models (backward compat)
    "Hole",
    "DrillReq",
    "GridSpec",
    "CircleSpec",
    "LineSpec",
    "Pattern",
    "DrillParams",
]
