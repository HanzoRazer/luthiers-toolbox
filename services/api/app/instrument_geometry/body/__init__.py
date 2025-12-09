"""
Body Geometry Subpackage

Provides body outlines and fretboard geometry calculations.

Modules:
- outlines: Body outline primitives (Wave 14)
- fretboard_geometry: Fretboard outline, slot layout, string spacing
"""

from .fretboard_geometry import (
    compute_fretboard_outline,
    compute_width_at_position_mm,
    compute_fret_slot_lines,
    compute_string_spacing_at_position,
)
from .outlines import get_body_outline

__all__ = [
    # fretboard_geometry
    "compute_fretboard_outline",
    "compute_width_at_position_mm",
    "compute_fret_slot_lines",
    "compute_string_spacing_at_position",
    # outlines
    "get_body_outline",
]
