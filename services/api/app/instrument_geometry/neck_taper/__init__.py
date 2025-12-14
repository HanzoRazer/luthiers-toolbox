"""
Neck Taper Suite

Wave 17 - Instrument Geometry Integration

Mathematical engine for distance-based neck taper calculations with DXF export.

Modules:
    taper_math: Core formulas (TaperInputs, FretWidth, width_at_fret)
    neck_outline_generator: Convert taper table to 2D polyline outline
    dxf_exporter: R12-safe DXF POLYLINE export
    api_router: FastAPI endpoints for JSON and DXF output

Usage:
    from instrument_geometry.neck_taper import TaperInputs, generate_neck_outline
    
    inputs = TaperInputs(scale_length=647.7, nut_width=42.0,
                         end_fret=12, end_width=57.0)
    outline = generate_neck_outline(inputs, range(0, 13))
"""

from .taper_math import TaperInputs, FretWidth, width_at_fret, compute_taper_table
from .neck_outline_generator import generate_neck_outline
from .dxf_exporter import export_neck_outline_to_dxf, build_r12_polyline_dxf
from .api_router import router

__all__ = [
    "TaperInputs",
    "FretWidth",
    "width_at_fret",
    "compute_taper_table",
    "generate_neck_outline",
    "export_neck_outline_to_dxf",
    "build_r12_polyline_dxf",
    "router",
]
