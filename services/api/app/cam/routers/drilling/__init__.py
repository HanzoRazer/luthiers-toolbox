"""
CAM Drilling Routers Package
============================

Modal drilling (G81, G83) and pattern drilling operations.

Sub-modules:
- drill_modal_router.py (2 routes: /gcode, /info)
- drill_pattern_router.py (2 routes: /pattern/gcode, /pattern/info)

Total: 4 routes under /api/cam/drilling
"""
from .drilling_consolidated_router import (
    router,
    drill_router,
    pattern_router,
    # Re-export models
    Hole,
    DrillReq,
    GridSpec,
    CircleSpec,
    LineSpec,
    Pattern,
    DrillParams,
)

__all__ = [
    # Main router
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
