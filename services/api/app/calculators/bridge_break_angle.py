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
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Thresholds (v2 — empirically grounded)
# ---------------------------------------------------------------------------

# Carruth's empirical minimum — below this, string doesn't seat firmly
CARRUTH_MIN_DEG = 6.0

# Marginal zone — may work but at risk
MARGINAL_MIN_DEG = 4.0

# Mechanical limit — excessive tension causes binding/breakage
TOO_STEEP_DEG = 38.0

# Practical minimum saddle projection (1/16" rule of thumb)
MINIMUM_PROJECTION_MM = 1.6

# Default slot offset (midpoint of 1.0-1.5mm range)
DEFAULT_SLOT_OFFSET_MM = 1.25


# ---------------------------------------------------------------------------
# Input / Output models
# ---------------------------------------------------------------------------

class BreakAngleInput(BaseModel):
    """Input parameters for break angle calculation (v2 corrected geometry)."""

    # v2 fields (preferred)
    saddle_projection_mm: Optional[float] = Field(
        default=None,
        gt=0,
        description=(
            "Height of saddle crown above the bridge TOP SURFACE (mm). "
            "This is the projection above the wood, NOT above the bridge plate. "
            "Practical minimum: 1.6 mm (1/16 in). Typical: 2-4 mm."
        ),
    )
    pin_to_saddle_mm: Optional[float] = Field(
        default=None,
        gt=0,
        description=(
            "Horizontal distance from bridge pin center to saddle slot (mm). "
            "Industry range: 5-7 mm (Martin ~5.5, Gibson ~6.5)."
        ),
    )
    slot_offset_mm: float = Field(
        default=DEFAULT_SLOT_OFFSET_MM,
        ge=0,
        description=(
            "Offset from pin center to actual string exit point due to slotted/tapered "
            "pin hole (mm). The slot shifts the string closer to the saddle. "
            "Default 1.25mm (midpoint of 1.0-1.5mm range)."
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

    # v1 backward compat fields (deprecated)
    pin_to_saddle_center_mm: Optional[float] = Field(
        default=None,
        description="DEPRECATED: Use pin_to_saddle_mm. Will be removed in v3.",
    )
    saddle_protrusion_mm: Optional[float] = Field(
        default=None,
        description="DEPRECATED: Use saddle_projection_mm. Will be removed in v3.",
    )


class RiskFlag(BaseModel):
    """A single risk or advisory flag."""

    code: str
    severity: str  # "info" | "warning" | "critical"
    message: str


class BreakAngleResult(BaseModel):
    """Output of the break angle calculation (v2)."""

    break_angle_deg: float = Field(description="Computed string break angle over saddle crown (degrees).")
    gate: Literal["GREEN", "YELLOW", "RED"] = Field(
        description=(
            "Carruth gate result: GREEN (>=6°), YELLOW (4-6° marginal), RED (<4° insufficient). "
            "Use this for go/no-go decisions."
        )
    )
    rating: str = Field(
        description=(
            "Overall rating: adequate | marginal | too_shallow | too_steep. "
            "Note: v2 removes 'optimal' — energy coupling is binary above 6 deg."
        )
    )
    effective_distance_mm: float = Field(
        description="Effective horizontal distance from string exit to saddle (pin center - slot offset)."
    )
    saddle_projection_mm: float
    carruth_min_projection_mm: float = Field(
        description="Minimum saddle projection for 6° angle at current distance: h_min = d × tan(6°)."
    )
    energy_coupling: str = Field(
        description="Energy transfer: adequate (>=6 deg) | marginal (4-6 deg) | inadequate (<4 deg)."
    )
    risk_flags: List[RiskFlag] = Field(default_factory=list)
    recommendation: Optional[str] = Field(
        default=None, description="Plain-language recommendation if geometry is out of spec."
    )
    migration_note: Optional[str] = Field(
        default=None, description="Note if v1 fields were used (deprecated)."
    )


# ---------------------------------------------------------------------------
# Core calculation
# ---------------------------------------------------------------------------

def calculate_break_angle(inp: BreakAngleInput) -> BreakAngleResult:
    """
    Compute break angle using v2 corrected geometry.

    Key corrections from v1:
        - Height measured from bridge TOP SURFACE (not bridge plate)
        - Distance measured from string EXIT POINT (not pin center)
        - Uses Carruth's 6° empirical minimum with gate result
        - Gate: GREEN (>=6°), YELLOW (4-6° marginal), RED (<4°)

    Parameters
    ----------
    inp : BreakAngleInput
        Bridge pin / saddle geometry.

    Returns
    -------
    BreakAngleResult
        Angle, gate, rating, energy coupling, h_min, and any risk flags.
    """
    # Handle backward compat fields
    migration_note: Optional[str] = None

    # Resolve saddle projection (v2 field or v1 fallback)
    saddle_projection = inp.saddle_projection_mm
    if saddle_projection is None and inp.saddle_protrusion_mm is not None:
        saddle_projection = inp.saddle_protrusion_mm
        migration_note = "Used deprecated saddle_protrusion_mm. Migrate to saddle_projection_mm."
    elif saddle_projection is None:
        saddle_projection = 2.5  # fallback default

    # Resolve pin-to-saddle distance (v2 field or v1 fallback)
    pin_to_saddle = inp.pin_to_saddle_mm
    if pin_to_saddle is None and inp.pin_to_saddle_center_mm is not None:
        pin_to_saddle = inp.pin_to_saddle_center_mm
        note = "Used deprecated pin_to_saddle_center_mm. Migrate to pin_to_saddle_mm."
        migration_note = note if migration_note is None else f"{migration_note} {note}"
    elif pin_to_saddle is None:
        pin_to_saddle = 5.5  # fallback default

    # Effective horizontal distance (account for slotted pin hole)
    # d = pin_center_to_saddle - slot_offset
    effective_distance = pin_to_saddle - inp.slot_offset_mm

    # Guard against invalid geometry
    if effective_distance <= 0:
        effective_distance = 0.1  # Avoid division by zero

    # Break angle: θ = arctan(h / d)
    angle_rad = math.atan2(saddle_projection, effective_distance)
    angle_deg = math.degrees(angle_rad)

    # Carruth minimum projection: h_min = d × tan(6°)
    carruth_min_h = effective_distance * math.tan(math.radians(CARRUTH_MIN_DEG))

    flags: list[RiskFlag] = []

    # --- Gate & Rating (v2: GREEN/YELLOW/RED) ---
    if angle_deg < MARGINAL_MIN_DEG:
        gate: Literal["GREEN", "YELLOW", "RED"] = "RED"
        rating = "too_shallow"
        energy = "inadequate"
        flags.append(RiskFlag(
            code="SHALLOW_ANGLE",
            severity="critical",
            message=(
                f"Break angle {angle_deg:.1f}° is below {MARGINAL_MIN_DEG}° — insufficient downforce. "
                "Strings will buzz or vibrate laterally. "
                f"Minimum projection for 6°: {carruth_min_h:.2f} mm."
            ),
        ))
    elif angle_deg < CARRUTH_MIN_DEG:
        gate = "YELLOW"
        rating = "marginal"
        energy = "marginal"
        flags.append(RiskFlag(
            code="MARGINAL_ANGLE",
            severity="warning",
            message=(
                f"Break angle {angle_deg:.1f}° is marginal (4-6°). "
                f"May work but at risk. Target ≥{CARRUTH_MIN_DEG}° for reliable coupling. "
                f"Minimum projection for 6°: {carruth_min_h:.2f} mm."
            ),
        ))
    elif angle_deg > TOO_STEEP_DEG:
        gate = "RED"
        rating = "too_steep"
        energy = "adequate"  # Energy coupling is fine, but mechanical risk
        flags.append(RiskFlag(
            code="STEEP_ANGLE",
            severity="critical",
            message=(
                f"Break angle {angle_deg:.1f}° exceeds {TOO_STEEP_DEG}°. "
                "Excessive downward force can cause string binding at saddle crown, "
                "premature breakage, and accelerated saddle slot wear."
            ),
        ))
    else:
        gate = "GREEN"
        rating = "adequate"
        energy = "adequate"

    # --- Saddle projection minimum check ---
    if saddle_projection < MINIMUM_PROJECTION_MM:
        flags.append(RiskFlag(
            code="LOW_PROJECTION",
            severity="warning",
            message=(
                f"Saddle projection ({saddle_projection:.1f} mm) is below the "
                f"practical minimum of {MINIMUM_PROJECTION_MM} mm (1/16 in). "
                "Saddle wear, string gauge variation, and crown radius shifts can "
                "push effective projection below safe limits."
            ),
        ))

    # --- Saddle material / seating check ---
    seated_depth = inp.saddle_blank_height_mm - saddle_projection
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
    if rating == "too_shallow" or rating == "marginal":
        # Target Carruth minimum with safety margin
        target_projection = carruth_min_h * 1.5
        target_projection = max(target_projection, MINIMUM_PROJECTION_MM)
        recommendation = (
            f"Raise saddle projection to at least {target_projection:.1f} mm to exceed "
            f"the {CARRUTH_MIN_DEG}° minimum with safety margin."
        )
    elif rating == "too_steep":
        target_projection = effective_distance * math.tan(math.radians(TOO_STEEP_DEG * 0.85))
        recommendation = (
            f"Lower saddle projection to ~{target_projection:.1f} mm to stay safely below "
            f"the {TOO_STEEP_DEG}° mechanical limit."
        )

    return BreakAngleResult(
        break_angle_deg=round(angle_deg, 2),
        gate=gate,
        rating=rating,
        effective_distance_mm=round(effective_distance, 2),
        saddle_projection_mm=saddle_projection,
        carruth_min_projection_mm=round(carruth_min_h, 2),
        energy_coupling=energy,
        risk_flags=flags,
        recommendation=recommendation,
        migration_note=migration_note,
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
        saddle_projection_mm=saddle_protrusion_mm,  # renamed field
        pin_to_saddle_mm=pin_to_saddle_center_mm,  # renamed field
        slot_offset_mm=0.0,  # v1 didn't account for this
        saddle_slot_depth_mm=saddle_slot_depth_mm,
        saddle_blank_height_mm=saddle_blank_height_mm,
    )
    return calculate_break_angle(inp)
