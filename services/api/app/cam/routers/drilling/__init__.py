"""
CAM Drilling Routers Package
============================

Modal drilling (G81, G83), pattern drilling, and governed preview operations.

Sub-modules:
- drill_modal_router.py (2 routes: /gcode, /info)
- drill_pattern_router.py (2 routes: /pattern/gcode, /pattern/info)
- drilling_preview_router.py (1 route: /preview) [GOVERNED PREVIEW - 5E]
- intent_router.py (1 route: /intent-gcode) [CamIntentV1 lane - 8I]

Total: 6 routes under /api/cam/drilling
"""
from fastapi import APIRouter

# Import the focused sub-routers directly.
from .drill_modal_router import router as drill_router
from .drill_pattern_router import router as pattern_router
from .drilling_preview_router import router as preview_router
from .intent_router import router as intent_router

# Re-export models (they originate in the focused sub-routers).
from .drill_modal_router import Hole, DrillReq
from .drill_pattern_router import (
    GridSpec,
    CircleSpec,
    LineSpec,
    Pattern,
    DrillParams,
)

# WP-002-C3: build the legacy consolidated drilling aggregate directly from the three
# focused sub-routers. Previously this routed through the deprecated
# drilling_consolidated_router wrapper (now retired from wiring); that wrapper only
# re-exported these same APIRouter(tags=["CAM", "Drilling"]) + include_router() calls,
# so endpoint paths, methods, and tags are unchanged.
_drilling_router = APIRouter(tags=["CAM", "Drilling"])
_drilling_router.include_router(drill_router)
_drilling_router.include_router(pattern_router)
_drilling_router.include_router(preview_router)

# Aggregate legacy consolidated drilling routes + the CamIntentV1 intent lane (8I).
# Mounted by the CAM aggregator at prefix /api/cam/drilling; intent_router defines
# its own /intent-gcode path -> POST /api/cam/drilling/intent-gcode.
router = APIRouter()
router.include_router(_drilling_router)
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
