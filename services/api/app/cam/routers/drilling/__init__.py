"""
CAM Drilling Routers Package
============================

Modal drilling (G81, G83), pattern drilling, and governed preview operations.

Sub-modules:
- drill_modal_router.py (2 routes: /gcode, /info)
- drill_pattern_router.py (2 routes: /pattern/gcode, /pattern/info)
- drilling_preview_router.py (1 route: /drilling/preview) [GOVERNED PREVIEW - 5E]
- intent_router.py (1 route: /intent-gcode) [CamIntentV1 - 8I]

Total: 6 routes under /api/cam/drilling
"""
from .drilling_consolidated_router import (
    router,
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

__all__ = [
    # Main router
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
