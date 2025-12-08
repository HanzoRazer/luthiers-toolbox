"""
Compatibility shim for instrument_geometry/scale_length.py

This module is kept temporarily to avoid breaking existing imports.
New code should import from `instrument_geometry.neck.fret_math` instead.

Wave 14 Migration: This file will be removed in a future cleanup phase.
"""

# Re-export everything from the new location
from .neck.fret_math import (  # noqa: F401
    SEMITONE_RATIO,
    compute_fret_positions_mm,
    compute_fret_spacing_mm,
    compute_compensated_scale_length_mm,
    compute_fret_to_bridge_mm,
    compute_multiscale_fret_positions_mm,
    SCALE_LENGTHS_MM,
    RADIUS_VALUES_MM,
)

__all__ = [
    "SEMITONE_RATIO",
    "compute_fret_positions_mm",
    "compute_fret_spacing_mm",
    "compute_compensated_scale_length_mm",
    "compute_fret_to_bridge_mm",
    "compute_multiscale_fret_positions_mm",
    "SCALE_LENGTHS_MM",
    "RADIUS_VALUES_MM",
]
