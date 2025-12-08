"""
Compatibility shim for instrument_geometry/fretboard_geometry.py

This module is kept temporarily to avoid breaking existing imports.
New code should import from `instrument_geometry.body.fretboard_geometry` instead.

Wave 14 Migration: This file will be removed in a future cleanup phase.
"""

# Re-export everything from the new location
from .body.fretboard_geometry import (  # noqa: F401
    compute_fretboard_outline,
    compute_width_at_position_mm,
    compute_fret_slot_lines,
    compute_string_spacing_at_position,
)

__all__ = [
    "compute_fretboard_outline",
    "compute_width_at_position_mm",
    "compute_fret_slot_lines",
    "compute_string_spacing_at_position",
]
