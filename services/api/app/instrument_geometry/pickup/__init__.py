# services/api/app/instrument_geometry/pickup/__init__.py

"""
Pickup Geometry Module

Provides pickup cavity placement and geometry calculations for CNC operations.

Modules:
- cavity_placement: Maps pickup positions to CNC-ready coordinates (PHYS-03)
"""

from .cavity_placement import (
    compute_pickup_cavity_coordinates,
    CavityCoordinates,
    CavityPlacementResult,
    BridgeReference,
)

__all__ = [
    "compute_pickup_cavity_coordinates",
    "CavityCoordinates",
    "CavityPlacementResult",
    "BridgeReference",
]
