"""Deprecated compatibility facade for retract routers.

The retract package no longer routes through this aggregate module (WP-002-C2). Import
the package router from ``app.routers.retract`` or the focused sub-routers directly
instead:

    from app.routers.retract.retract_info_router import router as info_router
    from app.routers.retract.retract_apply_router import router as apply_router
    from app.routers.retract.retract_gcode_router import router as gcode_router

This module remains import-compatible for downstream callers during the retirement
window; it must not be reintroduced into package wiring.

Sub-modules:
- retract_info_router.py (2 routes: /strategies, /estimate)
- retract_apply_router.py (2 routes: /apply, /lead_in)
- retract_gcode_router.py (4 routes: /gcode, /gcode_governed, /gcode/download, /gcode/download_governed)

Total: 8 routes under /api/cam/retract
"""
from __future__ import annotations

import warnings

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

warnings.warn(
    "app.routers.retract.retract_consolidated_router is deprecated; import "
    "app.routers.retract.router or a focused retract sub-router instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Aggregate router (facade only; not mounted into package wiring)
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
