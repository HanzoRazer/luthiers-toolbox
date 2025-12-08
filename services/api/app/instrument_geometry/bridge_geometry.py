"""
Compatibility shim for instrument_geometry/bridge_geometry.py

This module is kept temporarily to avoid breaking existing imports.
New code should import from `instrument_geometry.bridge.geometry` instead.

Wave 14 Migration: This file will be removed in a future cleanup phase.
"""

# Re-export everything from the new location
from .bridge.geometry import (  # noqa: F401
    compute_bridge_location_mm,
    compute_saddle_positions_mm,
    compute_bridge_height_profile,
    compute_archtop_bridge_placement,
    compute_compensation_estimate,
    STANDARD_6_STRING_COMPENSATION,
    STANDARD_4_STRING_BASS_COMPENSATION,
)

__all__ = [
    "compute_bridge_location_mm",
    "compute_saddle_positions_mm",
    "compute_bridge_height_profile",
    "compute_archtop_bridge_placement",
    "compute_compensation_estimate",
    "STANDARD_6_STRING_COMPENSATION",
    "STANDARD_4_STRING_BASS_COMPENSATION",
]
