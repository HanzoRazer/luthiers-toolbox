"""
Probe Router Package
====================

Probing pattern generation and SVG setup sheets.
REST API for CNC work offset establishment using touch probes.

Endpoints (17 total):
- /boss/* - Boss/hole circular probing (3 routes)
- /corner/* - Corner probing outside/inside (3 routes)
- /pocket/* - Pocket/inside probing (3 routes)
- /surface_z/* - Surface Z touch-off (3 routes)
- /vise_square/* - Vise squareness check (3 routes)
- /setup_sheet/svg - SVG setup sheet generation
- /patterns - List available patterns

Sub-modules:
- boss_router.py
- corner_router.py
- pocket_router.py
- surface_z_router.py
- vise_square_router.py
- setup_router.py
"""
from fastapi import APIRouter

# Import sub-routers for direct access
from .boss_router import router as boss_router
from .corner_router import router as corner_router
from .pocket_router import router as pocket_router
from .surface_z_router import router as surface_z_router
from .vise_square_router import router as vise_square_router
from .setup_router import router as setup_router

# Import aggregate router from consolidated module
from .probe_consolidated_router import router as probe_router

# Main router with /probe prefix
router = APIRouter(prefix="/probe", tags=["probe"])
router.include_router(probe_router)

__all__ = [
    # Main router
    "router",
    # Aggregate router (backward compat)
    "probe_router",
    # Sub-routers
    "boss_router",
    "corner_router",
    "pocket_router",
    "surface_z_router",
    "vise_square_router",
    "setup_router",
]
