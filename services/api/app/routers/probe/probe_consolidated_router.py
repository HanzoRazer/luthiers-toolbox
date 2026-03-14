"""Consolidated Probe Pattern Router.

DEPRECATED: This module is a thin wrapper for backward compatibility.
Prefer importing directly from focused sub-modules:

    from app.routers.probe.boss_router import router as boss_router
    from app.routers.probe.corner_router import router as corner_router
    from app.routers.probe.pocket_router import router as pocket_router
    from app.routers.probe.surface_z_router import router as surface_z_router
    from app.routers.probe.vise_square_router import router as vise_square_router
    from app.routers.probe.setup_router import router as setup_router

Sub-modules:
- boss_router.py (3 routes: /boss/*)
- corner_router.py (3 routes: /corner/*)
- pocket_router.py (3 routes: /pocket/*)
- surface_z_router.py (3 routes: /surface_z/*)
- vise_square_router.py (3 routes: /vise_square/*)
- setup_router.py (2 routes: /setup_sheet/svg, /patterns)

Total: 17 routes for CNC probing operations.
"""
from __future__ import annotations

from fastapi import APIRouter

# Import sub-routers
from .boss_router import router as boss_router
from .corner_router import router as corner_router
from .pocket_router import router as pocket_router
from .surface_z_router import router as surface_z_router
from .vise_square_router import router as vise_square_router
from .setup_router import router as setup_router

# Aggregate router
router = APIRouter(tags=["probe"])

# Mount sub-routers (no additional prefix - endpoints already have paths)
router.include_router(boss_router)
router.include_router(corner_router)
router.include_router(pocket_router)
router.include_router(surface_z_router)
router.include_router(vise_square_router)
router.include_router(setup_router)


__all__ = [
    # Router
    "router",
    # Sub-routers
    "boss_router",
    "corner_router",
    "pocket_router",
    "surface_z_router",
    "vise_square_router",
    "setup_router",
]
