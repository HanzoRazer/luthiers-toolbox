"""
Retract Router Package
======================

Retract pattern optimization for CNC toolpath generation.

Sub-modules:
- retract_info_router.py (2 routes: /strategies, /estimate)
- retract_apply_router.py (2 routes: /apply, /lead_in)
- retract_gcode_router.py (4 routes: /gcode, /gcode_governed, /gcode/download, /gcode/download_governed)

Total: 8 routes under /api/cam/retract
"""
from fastapi import APIRouter
from pydantic import BaseModel

# Import sub-routers for direct access
from .retract_info_router import router as info_router
from .retract_apply_router import router as apply_router
from .retract_gcode_router import router as gcode_router

# Re-export models (they originate in the focused sub-routers)
from .retract_info_router import (
    StrategyListOut,
    TimeSavingsIn,
    TimeSavingsOut,
)
from .retract_apply_router import (
    RetractStrategyIn,
    RetractStrategyOut,
    LeadInPatternIn,
    LeadInPatternOut,
)

# Aggregate router
router = APIRouter(tags=["Retract"])

# WP-002-C2: mount the focused sub-routers directly. Previously this routed through the
# deprecated retract_consolidated_router aggregate wrapper (now retired from wiring); that
# wrapper only re-exported these same three include_router() calls, so endpoint paths and
# behavior are unchanged.
router.include_router(info_router)
router.include_router(apply_router)
router.include_router(gcode_router)


class Point3DModel(BaseModel):
    """3D point model."""
    x: float
    y: float
    z: float


__all__ = [
    # Main router
    "router",
    # Sub-routers
    "info_router",
    "apply_router",
    "gcode_router",
    # Models
    "Point3DModel",
    "StrategyListOut",
    "TimeSavingsIn",
    "TimeSavingsOut",
    "RetractStrategyIn",
    "RetractStrategyOut",
    "LeadInPatternIn",
    "LeadInPatternOut",
]
