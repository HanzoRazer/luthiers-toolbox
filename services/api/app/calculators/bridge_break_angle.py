# services/api/app/calculators/bridge_break_angle.py

"""
Bridge Break Angle Calculator (v2 — Corrected Geometry)
========================================================

Calculates the string break angle over an acoustic guitar saddle crown.

v2 Corrections (see docs/BRIDGE_BREAK_ANGLE_DERIVATION.md):
    - Measure saddle height from bridge TOP SURFACE, not bridge plate
    - Account for slotted pin hole offset (string exits ~1-1.5mm closer to saddle)
    - Use Carruth's empirical 6 deg minimum, not fabricated 23-31 deg "optimal" range
    - Rating is binary: adequate (>=6 deg) or too_shallow (<6 deg)

Formula:
    d = pin_to_saddle_center_mm - slot_offset_mm  (effective string exit distance)
    h = saddle_projection_mm                       (height above bridge surface)
    break_angle_deg = arctan(h / d) * (180 / pi)

Thresholds (empirical):
    - Below 6 deg -> insufficient downward force, buzzing/lateral vibration risk (Carruth)
    - Above 6 deg -> adequate (no tonal gradient, energy coupling is binary)
    - Above 38 deg -> excessive tension, binding risk, premature breakage

Sources:
    - Alan Carruth: break angle testing establishing ~6 deg minimum
    - Charles (luthier): geometry correction for slotted pin holes

Author: The Production Shop
Version: 2.0.0
"""

from __future__ import annotations

import math
from typing import List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Thresholds (v2 — empirically grounded)
# ---------------------------------------------------------------------------

# Carruth's empirical minimum — below this, string doesn't seat firmly
MINIMUM_ADEQUATE_DEG = 6.0

# Mechanical limit — excessive tension causes binding/breakage
TOO_STEEP_DEG = 38.0

# Practical minimum saddle projection (1/16" rule of thumb)
MINIMUM_PROJECTION_MM = 1.6


# ---------------------------------------------------------------------------
# Input / Output models
# ---------------------------------------------------------------------------

class BreakAngleInput(BaseModel):
    """Input parameters for break angle calculation (v2 corrected geometry)."""

    pin_to_saddle_center_mm: float = Field(
        default=5.5,
        gt=0,
        description=(
            "Horizontal distance from bridge pin center to saddle crown center (mm). "
            "Industry range: 5-7 mm (Martin ~5.5, Gibson ~6.5)."
        ),
    )
    slot_offset_mm: float = Field(
        default=1.2,
        ge=0,
        description=(
            "Offset from pin center to actual string exit point due to slotted/tapered "
            "pin hole (mm). The slot shifts the string closer to the saddle. Typical: 1.0-1.5 mm."
        ),
    )
    saddle_projection_mm: float = Field(
        default=2.5,
        gt=0,
        description=(
            "Height of saddle crown above the bridge TOP SURFACE (mm). "
            "This is the projection above the wood, NOT above the bridge plate. "
            "Practical minimum: 1.6 mm (1/16 in). Typical: 2-4 mm."
        ),
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
    """Output of the break angle calculation (v2)."""

    break_angle_deg: float = Field(description="Computed string break angle over saddle crown (degrees).")
    rating: str = Field(
        description=(
            "Overall rating: adequate | too_shallow | too_steep. "
            "Note: v2 removes 'optimal' — energy coupling is binary above 6 deg."
        )
    )
    effective_distance_mm: float = Field(
        description="Effective horizontal distance from string exit to saddle (pin center - slot offset)."
    )
    saddle_projection_mm: float
    energy_coupling: str = Field(
        description="Energy transfer: adequate (>=6 deg) | inadequate (<6 deg). Binary per Carruth testing."
    )
    risk_flags: List[RiskFlag] = Field(default_factory=list)
    recommendation: Optional[str] = Field(
        default=None, description="Plain-language recommendation if geometry is out of spec."
    )


# ---------------------------------------------------------------------------
# Core calculation
# ---------------------------------------------------------------------------

def calculate_break_angle(inp: BreakAngleInput) -> BreakAngleResult:
    """
    Compute break angle using v2 corrected geometry.

    Key corrections from v1:
        - Uses effective distance (pin center - slot offset) not raw pin center
        - Uses Carruth's 6 deg empirical minimum, not fabricated 23-31 deg range
        - Rating is binary: adequate or not (no false "optimal" gradient)

    Parameters
    ----------
    inp : BreakAngleInput
        Bridge pin / saddle geometry.

    Returns
    -------
    BreakAngleResult
        Angle, rating, energy coupling, and any risk flags.
    """
    # Effective horizontal distance (account for slotted pin hole)
    effective_distance = inp.pin_to_saddle_center_mm - inp.slot_offset_mm

    # Guard against invalid geometry
    if effective_distance <= 0:
        effective_distance = 0.1  # Avoid division by zero

    angle_rad = math.atan2(inp.saddle_projection_mm, effective_distance)
    angle_deg = math.degrees(angle_rad)

    flags: list[RiskFlag] = []

    # --- Rating & energy coupling (v2: binary above 6 deg) ---
    if angle_deg < MINIMUM_ADEQUATE_DEG:
        rating = "too_shallow"
        energy = "inadequate"
        flags.append(RiskFlag(
            code="SHALLOW_ANGLE",
            severity="warning",
            message=(
                f"Break angle {angle_deg:.1f} deg is below Carruth's {MINIMUM_ADEQUATE_DEG} deg minimum. "
                "Insufficient downward force on saddle crown — strings may buzz or vibrate "
                "laterally instead of in the intended plane. "
                "Increase saddle projection or reduce pin-to-saddle distance."
            ),
        ))
    elif angle_deg > TOO_STEEP_DEG:
        rating = "too_steep"
        energy = "adequate"  # Energy coupling is fine, but mechanical risk
        flags.append(RiskFlag(
            code="STEEP_ANGLE",
            severity="critical",
            message=(
                f"Break angle {angle_deg:.1f} deg exceeds {TOO_STEEP_DEG} deg. "
                "Excessive downward force can cause string binding at saddle crown, "
                "premature breakage, and accelerated saddle slot wear. "
                "Lower saddle projection or increase pin-to-saddle distance."
            ),
        ))
    else:
        rating = "adequate"
        energy = "adequate"

    # --- Saddle projection minimum check ---
    if inp.saddle_projection_mm < MINIMUM_PROJECTION_MM:
        flags.append(RiskFlag(
            code="LOW_PROJECTION",
            severity="warning",
            message=(
                f"Saddle projection ({inp.saddle_projection_mm:.1f} mm) is below the "
                f"practical minimum of {MINIMUM_PROJECTION_MM} mm (1/16 in). "
                "Saddle wear, string gauge variation, and crown radius shifts can "
                "push effective projection below safe limits."
            ),
        ))

    # --- Saddle material / seating check ---
    seated_depth = inp.saddle_blank_height_mm - inp.saddle_projection_mm
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
        # Target the practical minimum with safety margin
        target_projection = effective_distance * math.tan(math.radians(MINIMUM_ADEQUATE_DEG)) * 1.5
        target_projection = max(target_projection, MINIMUM_PROJECTION_MM)
        recommendation = (
            f"Raise saddle projection to at least {target_projection:.1f} mm to exceed "
            f"the {MINIMUM_ADEQUATE_DEG} deg minimum with safety margin."
        )
    elif rating == "too_steep":
        target_projection = effective_distance * math.tan(math.radians(TOO_STEEP_DEG * 0.85))
        recommendation = (
            f"Lower saddle projection to ~{target_projection:.1f} mm to stay safely below "
            f"the {TOO_STEEP_DEG} deg mechanical limit."
        )

    return BreakAngleResult(
        break_angle_deg=round(angle_deg, 2),
        rating=rating,
        effective_distance_mm=round(effective_distance, 2),
        saddle_projection_mm=inp.saddle_projection_mm,
        energy_coupling=energy,
        risk_flags=flags,
        recommendation=recommendation,
    )


# ---------------------------------------------------------------------------
# Backward compatibility aliases (v1 field names)
# ---------------------------------------------------------------------------

def calculate_break_angle_v1_compat(
    pin_to_saddle_center_mm: float = 6.0,
    saddle_protrusion_mm: float = 3.0,
    saddle_slot_depth_mm: float = 10.0,
    saddle_blank_height_mm: float = 12.0,
) -> BreakAngleResult:
    """
    v1-compatible interface (DEPRECATED).

    Maps old field names to v2 model. Note that v1 did not account for
    slot offset, so results will differ from v1 by ~3-5 degrees.

    Use calculate_break_angle() with BreakAngleInput for accurate results.
    """
    inp = BreakAngleInput(
        pin_to_saddle_center_mm=pin_to_saddle_center_mm,
        slot_offset_mm=0.0,  # v1 didn't account for this
        saddle_projection_mm=saddle_protrusion_mm,  # renamed field
        saddle_slot_depth_mm=saddle_slot_depth_mm,
        saddle_blank_height_mm=saddle_blank_height_mm,
    )
    return calculate_break_angle(inp)
