"""
Body Geometry Subpackage

Provides body outlines and fretboard geometry calculations.

Modules:
- outlines: Body outline primitives with 19 DXF-extracted bodies (Wave 1 Integration)
- fretboard_geometry: Fretboard outline, slot layout, string spacing
- detailed_outlines: High-resolution point data from DXF extraction
- j45_bulge: J-45 outline with arc bulge data for CNC toolpaths

Assets:
- dxf/electric/: 7 electric guitar body DXFs
- dxf/acoustic/: 9 acoustic guitar body DXFs  
- dxf/other/: 3 ukulele/mandolin body DXFs
- catalog.json: Body metadata index
"""

from .fretboard_geometry import (
    compute_fretboard_outline,
    compute_width_at_position_mm,
    compute_fret_slot_lines,
    compute_string_spacing_at_position,
)
from .outlines import (
    get_body_outline,
    get_body_dimensions,
    get_available_outlines,
    get_body_metadata,
    get_dxf_path,
    list_bodies_by_category,
)
from .parametric import (
    BodyDimensions,
    generate_body_outline as generate_parametric_outline,
    cubic_bezier,
    ellipse_point,
    compute_bounding_box,
)

__all__ = [
    # fretboard_geometry
    "compute_fretboard_outline",
    "compute_width_at_position_mm",
    "compute_fret_slot_lines",
    "compute_string_spacing_at_position",
    # outlines
    "get_body_outline",
    "get_body_dimensions",
    "get_available_outlines",
    "get_body_metadata",
    "get_dxf_path",
    "list_bodies_by_category",
    # parametric
    "BodyDimensions",
    "generate_parametric_outline",
    "cubic_bezier",
    "ellipse_point",
    "compute_bounding_box",
]
