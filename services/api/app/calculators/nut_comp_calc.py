"""
DEPRECATED: Nut compensation calculator (geometry-based).

This module is deprecated and will be removed in a future release.
Use app.calculators.nut_compensation_calc instead:

    # Old (deprecated):
    from app.calculators.nut_comp_calc import compute_nut_compensation

    # New (recommended):
    from app.calculators.nut_compensation_calc import compute_nut_compensation_by_geometry

The geometry-based functions have been consolidated into nut_compensation_calc.py
with explicit `_by_geometry` suffix to distinguish from action-based functions.
"""
from __future__ import annotations

import warnings
from typing import Dict, List

# Re-export from canonical location under old names
from app.calculators.nut_compensation_calc import (
    NutCompSpec,
    NUT_WIDTH_MIN_MM,
    NUT_WIDTH_MAX_MM,
    NUT_WIDTH_DEFAULT_MM,
    ZERO_FRET_TO_NUT_GUIDE_MM,
    FRET_CROWN_WIDTH_MM,
    compute_nut_compensation_by_geometry as _compute_nut_compensation_by_geometry,
    compare_nut_types_by_geometry as _compare_nut_types_by_geometry,
    compute_per_string_compensation,
)

__all__ = [
    "NutCompSpec",
    "compute_nut_compensation",
    "compare_nut_types",
    "compute_per_string_compensation",
    "NUT_WIDTH_MIN_MM",
    "NUT_WIDTH_MAX_MM",
    "NUT_WIDTH_DEFAULT_MM",
    "ZERO_FRET_TO_NUT_GUIDE_MM",
    "FRET_CROWN_WIDTH_MM",
]

_DEPRECATION_MSG = (
    "nut_comp_calc is deprecated. Use nut_compensation_calc.compute_nut_compensation_by_geometry instead."
)


def compute_nut_compensation(
    nut_type: str,
    nut_width_mm: float,
    break_angle_deg: float,
    scale_length_mm: float,
) -> NutCompSpec:
    """
    DEPRECATED: Use nut_compensation_calc.compute_nut_compensation_by_geometry instead.
    """
    warnings.warn(_DEPRECATION_MSG, DeprecationWarning, stacklevel=2)
    return _compute_nut_compensation_by_geometry(
        nut_type=nut_type,
        nut_width_mm=nut_width_mm,
        break_angle_deg=break_angle_deg,
        scale_length_mm=scale_length_mm,
    )


def compare_nut_types(
    scale_length_mm: float,
    nut_width_mm: float = NUT_WIDTH_DEFAULT_MM,
    break_angle_deg: float = 10.0,
) -> Dict[str, dict]:
    """
    DEPRECATED: Use nut_compensation_calc.compare_nut_types_by_geometry instead.
    """
    warnings.warn(_DEPRECATION_MSG, DeprecationWarning, stacklevel=2)
    return _compare_nut_types_by_geometry(
        scale_length_mm=scale_length_mm,
        nut_width_mm=nut_width_mm,
        break_angle_deg=break_angle_deg,
    )
