"""
Bridge Geometry Subpackage

Provides bridge placement, saddle positioning, and intonation compensation.

Modules:
- geometry: Core bridge geometry calculations (moved from bridge_geometry.py)
- placement: Bridge placement helpers (Wave 14)
- compensation: Intonation compensation calculations (Wave 14)
"""

from .geometry import (
    compute_bridge_location_mm,
    compute_saddle_positions_mm,
    compute_bridge_height_profile,
    compute_archtop_bridge_placement,
    compute_compensation_estimate,
    STANDARD_6_STRING_COMPENSATION,
    STANDARD_4_STRING_BASS_COMPENSATION,
)
from .placement import compute_bridge_placement
from .compensation import compute_compensated_bridge

__all__ = [
    # geometry (legacy)
    "compute_bridge_location_mm",
    "compute_saddle_positions_mm",
    "compute_bridge_height_profile",
    "compute_archtop_bridge_placement",
    "compute_compensation_estimate",
    "STANDARD_6_STRING_COMPENSATION",
    "STANDARD_4_STRING_BASS_COMPENSATION",
    # placement (Wave 14)
    "compute_bridge_placement",
    # compensation (Wave 14)
    "compute_compensated_bridge",
]
