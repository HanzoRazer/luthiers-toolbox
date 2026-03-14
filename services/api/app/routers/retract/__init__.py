"""
Retract Router Package
======================

Retract pattern optimization for CNC toolpath generation.

Sub-modules:
- retract_info_router.py (2 routes: /strategies, /estimate)
- retract_apply_router.py (2 routes: /apply, /lead_in)
- retract_gcode_router.py (4 routes: /gcode, /gcode_governed, /gcode/download, /gcode/download_governed)

Total: 8 routes under /api/retract
"""
from .retract_consolidated_router import (
    router,
    info_router,
    apply_router,
    gcode_router,
    # Models
    StrategyListOut,
    TimeSavingsIn,
    TimeSavingsOut,
    RetractStrategyIn,
    RetractStrategyOut,
    LeadInPatternIn,
    LeadInPatternOut,
)

__all__ = [
    # Main router
    "router",
    # Sub-routers
    "info_router",
    "apply_router",
    "gcode_router",
    # Models
    "StrategyListOut",
    "TimeSavingsIn",
    "TimeSavingsOut",
    "RetractStrategyIn",
    "RetractStrategyOut",
    "LeadInPatternIn",
    "LeadInPatternOut",
]
