"""
Instrument Body Generator (IBG) — Production Module
====================================================

Generates complete parametric body models from partial vectorizer output.

Usage:
    from app.instrument_geometry.body.ibg import InstrumentBodyGenerator

    gen = InstrumentBodyGenerator(spec_name='dreadnought')
    model = gen.complete_from_dxf('partial_outline.dxf')

Available specs: dreadnought, cuatro_venezolano, stratocaster, jumbo

Author: Production Shop
Date: 2026-04-17
"""

from .instrument_body_generator import (
    InstrumentBodyGenerator,
    INSTRUMENT_SPECS,
)
from .body_contour_solver import (
    BodyConstraints,
    BodyContourSolver,
    LandmarkPoint,
    SolvedBodyModel,
    outline_to_dxf,
    solve_high_point,
    solve_side_height,
    FAMILY_DEFAULTS,
)
from .constraint_extractor import (
    ConstraintExtractor,
    ExtractionResult,
)

__all__ = [
    # Main API
    "InstrumentBodyGenerator",
    "INSTRUMENT_SPECS",
    # Solver
    "BodyConstraints",
    "BodyContourSolver",
    "LandmarkPoint",
    "SolvedBodyModel",
    "outline_to_dxf",
    "solve_high_point",
    "solve_side_height",
    "FAMILY_DEFAULTS",
    # Extractor
    "ConstraintExtractor",
    "ExtractionResult",
]
