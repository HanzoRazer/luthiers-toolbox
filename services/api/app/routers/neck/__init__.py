"""
Neck router package - decomposed from monolithic neck_router.py

Sub-routers:
- strat_router: Stratocaster-specific endpoints
- tele_router: Telecaster-specific endpoints
- prs_router: PRS-specific endpoints
- gcode_router: G-code generation endpoints
"""
from fastapi import APIRouter

from .schemas import Point2D, NeckParameters, NeckGeometryOut
from .geometry import (
    calculate_fret_positions,
    generate_neck_profile,
    generate_fretboard_outline,
    generate_headstock_outline,
    generate_tuner_holes,
    generate_centerline,
    convert_point,
    convert_points,
    convert_value,
)
from .export import export_neck_dxf

# Import sub-routers
from . import strat_router
from . import tele_router
from . import prs_router
from . import gcode_router

__all__ = [
    "Point2D",
    "NeckParameters",
    "NeckGeometryOut",
    "calculate_fret_positions",
    "generate_neck_profile",
    "generate_fretboard_outline",
    "generate_headstock_outline",
    "generate_tuner_holes",
    "generate_centerline",
    "convert_point",
    "convert_points",
    "convert_value",
    "export_neck_dxf",
    "strat_router",
    "tele_router",
    "prs_router",
    "gcode_router",
]
