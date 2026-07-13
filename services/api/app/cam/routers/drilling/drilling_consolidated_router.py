"""Deprecated compatibility facade for CAM drilling routers.

The drilling package no longer routes through this aggregate module (WP-002-C3). Import
the package router from ``app.cam.routers.drilling`` or the focused sub-routers directly
instead:

    from app.cam.routers.drilling.drill_modal_router import router as drill_router
    from app.cam.routers.drilling.drill_pattern_router import router as pattern_router
    from app.cam.routers.drilling.drilling_preview_router import router as preview_router

This module remains import-compatible for downstream callers during the retirement
window; it must not be reintroduced into package wiring.

Sub-modules aggregated here (compatibility surface):
- drill_modal_router.py (2 routes: /gcode, /info)
- drill_pattern_router.py (2 routes: /pattern/gcode, /pattern/info)
- drilling_preview_router.py (1 route: /preview)

Total: 5 routes (the package also mounts intent_router's /intent-gcode separately).

LANE: OPERATION (for /gcode endpoints)
LANE: UTILITY (for /info endpoints)
Reference: docs/OPERATION_EXECUTION_GOVERNANCE_v1.md
"""
from __future__ import annotations

import warnings

from fastapi import APIRouter

# Import sub-routers
from .drill_modal_router import router as drill_router
from .drill_pattern_router import router as pattern_router
from .drilling_preview_router import router as preview_router

# Re-export models for backward compatibility
from .drill_modal_router import Hole, DrillReq
from .drill_pattern_router import (
    GridSpec,
    CircleSpec,
    LineSpec,
    Pattern,
    DrillParams,
)

warnings.warn(
    "app.cam.routers.drilling.drilling_consolidated_router is deprecated; import "
    "app.cam.routers.drilling.router or a focused drilling sub-router instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Aggregate router (facade only; not mounted into package wiring)
router = APIRouter(tags=["CAM", "Drilling"])

# Mount sub-routers (no additional prefix - endpoints already have paths)
router.include_router(drill_router)
router.include_router(pattern_router)
router.include_router(preview_router)


__all__ = [
    # Router
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
