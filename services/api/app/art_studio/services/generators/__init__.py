"""
Parametric Generators Package - Bundle 31.0.2

Generators convert pattern parameters into RosetteParamSpec.
They are pure functions with no I/O.
"""

from .registry import (
    GENERATOR_REGISTRY,
    get_generator,
    list_generators,
    generate_spec,
)
from .basic_rings import basic_rings_v1
from .mosaic_band import mosaic_band_v1

# Inlay pattern generators (V1–V3 unified backend)
from .inlay_geometry import GeometryCollection, GeometryElement, offset_collection
from .inlay_patterns import generate_inlay_pattern, INLAY_GENERATORS
from .inlay_export import geometry_to_dxf, geometry_to_dxf_bytes
from .inlay_import import parse_dxf, parse_svg, parse_csv_grid

__all__ = [
    "GENERATOR_REGISTRY",
    "get_generator",
    "list_generators",
    "generate_spec",
    "basic_rings_v1",
    "mosaic_band_v1",
    # Inlay pattern system
    "GeometryCollection",
    "GeometryElement",
    "offset_collection",
    "generate_inlay_pattern",
    "INLAY_GENERATORS",
    "geometry_to_dxf",
    "geometry_to_dxf_bytes",
    "parse_dxf",
    "parse_svg",
    "parse_csv_grid",
]
