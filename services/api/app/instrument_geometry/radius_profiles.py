"""
Compatibility shim for instrument_geometry/radius_profiles.py

This module is kept temporarily to avoid breaking existing imports.
New code should import from `instrument_geometry.neck.radius_profiles` instead.

Wave 14 Migration: This file will be removed in a future cleanup phase.
"""

# Re-export everything from the new location
from .neck.radius_profiles import (  # noqa: F401
    compute_compound_radius_at_fret,
    compute_radius_arc_points,
    compute_radius_drop_mm,
    compute_fret_crown_height_mm,
    compute_string_height_at_fret,
    generate_compound_radius_profile,
    inches_to_mm,
    mm_to_inches,
)

__all__ = [
    "compute_compound_radius_at_fret",
    "compute_radius_arc_points",
    "compute_radius_drop_mm",
    "compute_fret_crown_height_mm",
    "compute_string_height_at_fret",
    "generate_compound_radius_profile",
    "inches_to_mm",
    "mm_to_inches",
]
