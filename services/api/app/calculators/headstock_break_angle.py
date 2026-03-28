# services/api/app/calculators/headstock_break_angle.py
"""
DEPRECATED: Use app.calculators.headstock_break_angle_calc instead.

This module is a backward-compatibility shim. All functionality has been
merged into headstock_break_angle_calc.py which now provides both:
- Simple API: calculate_headstock_break_angle() - whole-headstock summary
- Advanced API: analyze_headstock() - per-string detailed analysis

Migration:
    # Old:
    from app.calculators.headstock_break_angle import (
        HeadstockBreakAngleInput,
        HeadstockBreakAngleResult,
        calculate_headstock_break_angle,
    )

    # New:
    from app.calculators.headstock_break_angle_calc import (
        HeadstockBreakAngleInput,
        HeadstockBreakAngleResult,
        calculate_headstock_break_angle,
    )

The shim re-exports with deprecation warnings. Update imports at your
earliest convenience.
"""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING

# Import everything from the canonical module
from app.calculators.headstock_break_angle_calc import (
    # Pydantic models (simple API)
    HeadstockBreakAngleInput as _HeadstockBreakAngleInput,
    HeadstockBreakAngleResult as _HeadstockBreakAngleResult,
    NutRiskFlag as _NutRiskFlag,
    # Simple API function
    calculate_headstock_break_angle as _calculate_headstock_break_angle,
    # Thresholds
    TOO_SHALLOW_DEG,
    OPTIMAL_MIN_DEG,
    OPTIMAL_MAX_DEG,
    TOO_STEEP_DEG,
)

_DEPRECATION_MSG = (
    "headstock_break_angle is deprecated. "
    "Use app.calculators.headstock_break_angle_calc instead."
)


# Re-export types directly (no warning for type access)
HeadstockBreakAngleInput = _HeadstockBreakAngleInput
HeadstockBreakAngleResult = _HeadstockBreakAngleResult
NutRiskFlag = _NutRiskFlag


def calculate_headstock_break_angle(
    inp: HeadstockBreakAngleInput,
) -> HeadstockBreakAngleResult:
    """
    DEPRECATED: Use headstock_break_angle_calc.calculate_headstock_break_angle().

    Compute the effective string break angle at the nut.
    """
    warnings.warn(_DEPRECATION_MSG, DeprecationWarning, stacklevel=2)
    return _calculate_headstock_break_angle(inp)


__all__ = [
    "HeadstockBreakAngleInput",
    "HeadstockBreakAngleResult",
    "NutRiskFlag",
    "calculate_headstock_break_angle",
    "TOO_SHALLOW_DEG",
    "OPTIMAL_MIN_DEG",
    "OPTIMAL_MAX_DEG",
    "TOO_STEEP_DEG",
]
