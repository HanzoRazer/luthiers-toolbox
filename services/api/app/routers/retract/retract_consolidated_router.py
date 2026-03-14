"""
Retract Routers (Consolidated)
==============================

DEPRECATED: This module is a thin wrapper for backward compatibility.
Prefer importing directly from focused sub-modules:

    from app.routers.retract.retract_info_router import router as info_router
    from app.routers.retract.retract_apply_router import router as apply_router
    from app.routers.retract.retract_gcode_router import router as gcode_router

Sub-modules:
- retract_info_router.py (2 routes: /strategies, /estimate)
- retract_apply_router.py (2 routes: /apply, /lead_in)
- retract_gcode_router.py (4 routes: /gcode, /gcode_governed, /gcode/download, /gcode/download_governed)

Total: 8 routes under /api/retract
"""
from fastapi import APIRouter

# Import sub-routers
from .retract_info_router import router as info_router
from .retract_apply_router import router as apply_router
from .retract_gcode_router import router as gcode_router

# Re-export models for backward compatibility
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

# Mount sub-routers (no additional prefix - endpoints already have paths)
router.include_router(info_router)
router.include_router(apply_router)
router.include_router(gcode_router)


__all__ = [
    # Router
    "router",
    # Sub-routers
    "info_router",
    "apply_router",
    "gcode_router",
    # Models (backward compat)
    "StrategyListOut",
    "TimeSavingsIn",
    "TimeSavingsOut",
    "RetractStrategyIn",
    "RetractStrategyOut",
    "LeadInPatternIn",
    "LeadInPatternOut",
]
