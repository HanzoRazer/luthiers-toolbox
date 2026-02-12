"""
Curated API v1 - Essential endpoints for luthier workflows.

This module provides a stable, curated API surface for the most common
luthier workflows. All endpoints are versioned and documented.

WORKFLOWS:
----------
1. DXF → G-code: Upload DXF, validate, plan CAM, generate G-code
2. Fret Math: Calculate fret positions, slots, temperaments
3. RMOS Safety: Check feasibility, run approval, safety gates
4. Instrument Design: Scale length, neck profiles, body geometry

DESIGN PRINCIPLES:
------------------
- Stable paths: /api/v1/* paths won't change without deprecation
- Consistent responses: All endpoints return {ok: bool, data: ..., error: ...}
- Self-documenting: Every endpoint has clear examples
- Fail-safe: Errors include recovery hints
"""

from fastapi import APIRouter

from .dxf_workflow import router as dxf_router
from .fret_math import router as fret_router
from .rmos_safety import router as rmos_router
from .instrument import router as instrument_router

# Main v1 router - aggregates all curated endpoints
router = APIRouter(prefix="/api/v1", tags=["API v1"])

# Mount sub-routers
router.include_router(dxf_router)
router.include_router(fret_router)
router.include_router(rmos_router)
router.include_router(instrument_router)

__all__ = ["router"]
