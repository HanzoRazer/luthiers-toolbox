"""
Probe Router Package
====================

Probing pattern generation and SVG setup sheets.
REST API for CNC work offset establishment using touch probes.

Endpoints:
- /corner/* - Corner probing (outside/inside)
- /boss/* - Boss/hole circular probing
- /surface_z/* - Surface Z touch-off
- /pocket/* - Pocket/inside probing
- /vise_square/* - Vise squareness check
- /setup_sheet/svg - SVG setup sheet generation
- /patterns - List available patterns
"""
from fastapi import APIRouter

from .corner_router import router as corner_router
from .boss_router import router as boss_router
from .surface_z_router import router as surface_z_router
from .pocket_router import router as pocket_router
from .vise_square_router import router as vise_square_router
from .setup_router import router as setup_router

router = APIRouter(prefix="/probe", tags=["probe"])

router.include_router(corner_router)
router.include_router(boss_router)
router.include_router(surface_z_router)
router.include_router(pocket_router)
router.include_router(vise_square_router)
router.include_router(setup_router)

__all__ = ["router"]
