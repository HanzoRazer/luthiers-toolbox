"""
Instrument Geometry Router Module
=================================

Domain-specific routers for instrument geometry calculations.

Routers:
- nut_fret_router: Nut slots, compensation, fret leveling, fret wire (9 endpoints)
- bridge_router: Bridge geometry and pin positions (3 endpoints)
- body_construction_router: Side bending, blocks (5 endpoints)
- soundhole_router: Soundhole specification and position (3 endpoints)
- wood_movement_router: Wood movement from humidity (3 endpoints)
- electronics_router: Pickup cavities, control layouts (4 endpoints)
- voicing_router: Tap tone analysis and frequency prediction (4 endpoints)
- build_sequence_router: Complete build sequence (2 endpoints)
- setup_router: Instrument setup evaluation (1 endpoint)
- string_tension_router: String tension and saddle force (3 endpoints)

Total: 42 endpoints (includes 5 geometry calculator endpoints)
"""

from fastapi import APIRouter

from .geometry_calculator_router import router as geometry_calculator_router
from .nut_fret_router import router as nut_fret_router
from .bridge_router import router as bridge_router
from .body_construction_router import router as body_construction_router
from .soundhole_router import router as soundhole_router
from .wood_movement_router import router as wood_movement_router
from .electronics_router import router as electronics_router
from .voicing_router import router as voicing_router
from .build_sequence_router import router as build_sequence_router
from .setup_router import router as setup_router
from .string_tension_router import router as string_tension_router

# Combined router with /api/instrument prefix
router = APIRouter(
    prefix="/api/instrument",
    tags=["instrument-geometry"],
)

# Include all domain routers
router.include_router(geometry_calculator_router)
router.include_router(nut_fret_router)
router.include_router(bridge_router)
router.include_router(body_construction_router)
router.include_router(soundhole_router)
router.include_router(wood_movement_router)
router.include_router(electronics_router)
router.include_router(voicing_router)
router.include_router(build_sequence_router)
router.include_router(setup_router)
router.include_router(string_tension_router)

__all__ = [
    "router",
    "geometry_calculator_router",
    "nut_fret_router",
    "bridge_router",
    "body_construction_router",
    "soundhole_router",
    "wood_movement_router",
    "electronics_router",
    "voicing_router",
    "build_sequence_router",
    "setup_router",
    "string_tension_router",
]
