"""
Instrument Routers Package (DECOMP-001)
=======================================

Domain-specific routers split from the monolithic instrument_geometry_router.py.

Each router is mounted at /api/instrument with its own endpoints:
- materials_physics_router: Side bending, wood movement
- soundhole_router: Soundhole calculations
- fretwork_router: Nut slots, fret leveling, fret wire, nut compensation
- build_workflow_router: Setup cascade, blocks, build sequence, voicing
- electronics_router: Pickup cavities, control layouts

The parent instrument_geometry_router.py retains:
- Bridge geometry endpoints
- Cantilever armrest endpoints
"""

from .materials_physics_router import router as materials_physics_router
from .soundhole_router import router as soundhole_router
from .fretwork_router import router as fretwork_router
from .build_workflow_router import router as build_workflow_router
from .electronics_router import router as electronics_router

__all__ = [
    "materials_physics_router",
    "soundhole_router",
    "fretwork_router",
    "build_workflow_router",
    "electronics_router",
]
