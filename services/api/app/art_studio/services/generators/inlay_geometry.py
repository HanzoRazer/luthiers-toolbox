"""
Inlay Geometry Primitives & Offset Engine

Provides GeometryCollection (the intermediate representation for all inlay
pattern generators) and the shared math infrastructure ported from the V3
spiral prototype and the Vine/Girih/Celtic HTML prototypes.

Shared math layer
-----------------
* Miter-join polygon offset (proper corner geometry)
* Dual-rail polyline strip for CNC pocketing
* De Casteljau cubic/quadratic Bézier subdivision
* SVG endpoint-arc → centre-parameter conversion (SVG spec F.6.5-6)
* Full SVG path ``d`` tokeniser (M/L/H/V/C/S/Q/T/A/Z)
* Catmull-Rom spline interpolation

All coordinates in mm.  Positive offset = outward / male, negative = inward / pocket.

This module re-exports from the split sub-modules for backward compatibility:
- inlay_geometry_core: GeometryElement, GeometryCollection, Pt, Polyline
- inlay_geometry_transforms: offset functions
- inlay_geometry_bezier: Bézier subdivision, spline math
- inlay_geometry_svg: SVG parsing and rendering
- inlay_geometry_rope: Rope/strand path generation
- inlay_geometry_bom: BOM calculation, materials, region shapes
"""
from __future__ import annotations

# Re-export core types
from .inlay_geometry_core import (
    GeometryCollection,
    GeometryElement,
    Polyline,
    Pt,
)

# Re-export transforms
from .inlay_geometry_transforms import (
    line_line_intersect,
    offset_collection,
    offset_polygon,
    offset_polyline,
    offset_polyline_strip,
)

# Re-export Bézier and spline math
from .inlay_geometry_bezier import (
    catmull_rom,
    make_poly,
    sample_spline,
    subdivide_cubic,
    subdivide_quadratic,
)

# Re-export SVG functions
from .inlay_geometry_svg import (
    arc_to_center_param,
    collection_to_layered_svg,
    collection_to_svg,
    element_to_svg,
    offset_path_d,
    points_to_path_d,
    tessellate_arc,
    tessellate_path_d,
)

# Re-export rope/strand generation
from .inlay_geometry_rope import (
    build_centerline,
    compute_tangent_normal_arclen,
    generate_strand_paths,
    split_strand_at_crossings,
)

# Re-export BOM and materials
from .inlay_geometry_bom import (
    BomEntry,
    MATERIAL_KEYS,
    MATERIALS,
    binding_strip,
    calculate_bom,
    fretboard_trapezoid,
    mat_color,
    rosette_ring,
)

__all__ = [
    # Core types
    "Pt",
    "Polyline",
    "GeometryElement",
    "GeometryCollection",
    # Transforms
    "line_line_intersect",
    "offset_polyline",
    "offset_polygon",
    "offset_polyline_strip",
    "offset_collection",
    # Bézier and spline
    "subdivide_cubic",
    "subdivide_quadratic",
    "catmull_rom",
    "sample_spline",
    "make_poly",
    # SVG
    "arc_to_center_param",
    "tessellate_arc",
    "tessellate_path_d",
    "points_to_path_d",
    "offset_path_d",
    "element_to_svg",
    "collection_to_svg",
    "collection_to_layered_svg",
    # Rope/strand
    "compute_tangent_normal_arclen",
    "build_centerline",
    "generate_strand_paths",
    "split_strand_at_crossings",
    # BOM and materials
    "MATERIALS",
    "MATERIAL_KEYS",
    "mat_color",
    "BomEntry",
    "calculate_bom",
    "fretboard_trapezoid",
    "rosette_ring",
    "binding_strip",
]
