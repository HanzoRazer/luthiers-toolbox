# services/api/app/calculators/bridge_break_angle.py

"""
Bridge Break Angle Calculator
==============================

Calculates the string break angle over an acoustic guitar saddle crown
given the pin-to-saddle center distance and saddle protrusion height.

Formula:
    break_angle_deg = arctan(saddle_protrusion_mm / pin_to_saddle_center_mm) * (180 / pi)

Industry reference:
    - Pin-to-saddle center: 5-7 mm (Martin ~5.5, Gibson ~6.5)
    - Saddle protrusion above bridge plate: 2-4 mm typical
    - Optimal break angle: 23-31 degrees
    - Below 18 deg → poor energy coupling, buzzing risk
    - Above 38 deg → excessive tension, binding risk, premature breakage

Author: The Production Shop
Version: 1.0.0
"""

from __future__ import annotations

import math
from typing import List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Thresholds (from bridge_templates.json break_angle_geometry.risk_thresholds)
# ---------------------------------------------------------------------------

TOO_SHALLOW_DEG = 18.0
OPTIMAL_MIN_DEG = 23.0
OPTIMAL_MAX_DEG = 31.0
TOO_STEEP_DEG = 38.0


# ---------------------------------------------------------------------------
# Input / Output models
# ---------------------------------------------------------------------------

class BreakAngleInput(BaseModel):
    """Input parameters for break angle calculation."""

    pin_to_saddle_center_mm: float = Field(
        default=6.0,
        gt=0,
        description="Horizontal distance from bridge pin center to saddle crown center (mm). Industry range: 5-7 mm.",
    )
    saddle_protrusion_mm: float = Field(
        default=3.0,
        gt=0,
        description="Height of saddle crown above the bridge plate surface (mm). Typical: 2-4 mm.",
    )
    saddle_slot_depth_mm: float = Field(
        default=10.0,
        gt=0,
        description="Total saddle slot depth (mm). Used to validate saddle blank has enough material.",
    )
    saddle_blank_height_mm: float = Field(
        default=12.0,
        gt=0,
        description="Saddle blank total height before shaping (mm). Standard bone blank: 12 mm.",
    )


class RiskFlag(BaseModel):
    """A single risk or advisory flag."""

    code: str
    severity: str  # "info" | "warning" | "critical"
    message: str


class BreakAngleResult(BaseModel):
    """Output of the break angle calculation."""

    break_angle_deg: float = Field(description="Computed string break angle over saddle crown (degrees).")
    rating: str = Field(description="Overall rating: optimal | acceptable | too_shallow | too_steep.")
    pin_to_saddle_center_mm: float
    saddle_protrusion_mm: float
    energy_coupling: str = Field(description="Qualitative energy transfer rating: excellent | good | fair | poor.")
    risk_flags: List[RiskFlag] = Field(default_factory=list)
    recommendation: Optional[str] = Field(default=None, description="Plain-language recommendation if geometry is out of spec.")


# ---------------------------------------------------------------------------
# Core calculation
# ---------------------------------------------------------------------------

def calculate_break_angle(inp: BreakAngleInput) -> BreakAngleResult:
    """
    Compute break angle and assess energy coupling quality.

    Parameters
    ----------
    inp : BreakAngleInput
        Bridge pin / saddle geometry.

    Returns
    -------
    BreakAngleResult
        Angle, rating, energy coupling quality, and any risk flags.
    """
    angle_rad = math.atan2(inp.saddle_protrusion_mm, inp.pin_to_saddle_center_mm)
    angle_deg = math.degrees(angle_rad)

    flags: list[RiskFlag] = []

    # --- Rating & energy coupling ---
    if angle_deg < TOO_SHALLOW_DEG:
        rating = "too_shallow"
        energy = "poor"
        flags.append(RiskFlag(
            code="SHALLOW_ANGLE",
            severity="warning",
            message=(
                f"Break angle {angle_deg:.1f}° is below {TOO_SHALLOW_DEG}°. "
                "Strings may buzz or lift off the saddle crown. "
                "Consider increasing saddle height or reducing pin-to-saddle distance."
            ),
        ))
    elif angle_deg > TOO_STEEP_DEG:
        rating = "too_steep"
        energy = "fair"
        flags.append(RiskFlag(
            code="STEEP_ANGLE",
            severity="critical",
            message=(
                f"Break angle {angle_deg:.1f}° exceeds {TOO_STEEP_DEG}°. "
                "Excessive downward force on the saddle can cause string binding, "
                "premature breakage, and saddle slot wear. "
                "Consider lowering saddle height or increasing pin-to-saddle distance."
            ),
        ))
    elif OPTIMAL_MIN_DEG <= angle_deg <= OPTIMAL_MAX_DEG:
        rating = "optimal"
        energy = "excellent"
    else:
        rating = "acceptable"
        energy = "good"

    # --- Saddle material check ---
    seated_depth = inp.saddle_blank_height_mm - inp.saddle_protrusion_mm
    if seated_depth < inp.saddle_slot_depth_mm * 0.5:
        flags.append(RiskFlag(
            code="LOW_SEAT_DEPTH",
            severity="warning",
            message=(
                f"Saddle seated depth ({seated_depth:.1f} mm) is less than 50% of "
                f"slot depth ({inp.saddle_slot_depth_mm:.1f} mm). "
                "Saddle may rock or pop out under string tension."
            ),
        ))

    # --- Recommendation ---
    recommendation = None
    if rating == "too_shallow":
        target_protrusion = inp.pin_to_saddle_center_mm * math.tan(math.radians(OPTIMAL_MIN_DEG))
        recommendation = (
            f"Raise saddle protrusion to ~{target_protrusion:.1f} mm to reach "
            f"the optimal {OPTIMAL_MIN_DEG}° minimum."
        )
    elif rating == "too_steep":
        target_protrusion = inp.pin_to_saddle_center_mm * math.tan(math.radians(OPTIMAL_MAX_DEG))
        recommendation = (
            f"Lower saddle protrusion to ~{target_protrusion:.1f} mm to stay within "
            f"the optimal {OPTIMAL_MAX_DEG}° maximum."
        )

    return BreakAngleResult(
        break_angle_deg=round(angle_deg, 2),
        rating=rating,
        pin_to_saddle_center_mm=inp.pin_to_saddle_center_mm,
        saddle_protrusion_mm=inp.saddle_protrusion_mm,
        energy_coupling=energy,
        risk_flags=flags,
        recommendation=recommendation,
    )
