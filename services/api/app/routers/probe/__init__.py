"""
Probe Router Package
====================

Probing pattern generation and SVG setup sheets.
REST API for CNC work offset establishment using touch probes.

Endpoints (17 total):
- /corner/* - Corner probing (outside/inside)
- /boss/* - Boss/hole circular probing
- /surface_z/* - Surface Z touch-off
- /pocket/* - Pocket/inside probing
- /vise_square/* - Vise squareness check
- /setup_sheet/svg - SVG setup sheet generation
- /patterns - List available patterns

Consolidated from 6 separate routers into probe_consolidated_router.py
"""
from fastapi import APIRouter

from .probe_consolidated_router import router as probe_router

router = APIRouter(prefix="/probe", tags=["probe"])

router.include_router(probe_router)

__all__ = ["router"]
