"""Soundhole geometry modules — spiral, round, oval, f-hole."""

from .spiral_geometry import (
    SpiralSpec,
    SpiralGeometry,
    DualSpiralSpec,
    DualSpiralGeometry,
    compute_spiral_geometry,
    compute_dual_geometry,
    generate_dxf,
    default_carlos_jumbo_spec,
    spec_to_dict,
    spec_from_dict,
    geo_to_dict,
    dual_geo_to_dict,
)

__all__ = [
    "SpiralSpec",
    "SpiralGeometry",
    "DualSpiralSpec",
    "DualSpiralGeometry",
    "compute_spiral_geometry",
    "compute_dual_geometry",
    "generate_dxf",
    "default_carlos_jumbo_spec",
    "spec_to_dict",
    "spec_from_dict",
    "geo_to_dict",
    "dual_geo_to_dict",
]
