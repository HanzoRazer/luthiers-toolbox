# services/api/app/calculators/headstock_break_angle.py

"""
Headstock / Nut Break Angle Calculator
========================================

Calculates the string break angle at the nut for both angled headstocks
(Gibson-style) and flat headstocks (Fender-style with string trees).

The break angle at the nut determines downward force on the nut slots,
which affects tuning stability, sustain, and open-string tone clarity.

Angled headstock geometry:
    The headstock pitches back at angle α (typically 13-17°).
    The effective break angle at the nut depends on:
      - headstock_angle_deg: the pitch-back angle
      - nut_to_tuner_mm: distance from nut to the tuner post
      - tuner_post_height_mm: height of the tuner post above headstock face
      - nut_slot_depth_mm: how deep the string sits in the nut slot

    For an angled headstock, the string descends from the nut into the
    headstock plane. The effective break angle ≈ headstock_angle minus
    the upward correction from the tuner post height:

        effective_angle = arctan(
            (nut_to_tuner_mm * sin(α) - tuner_post_height_mm)
            / (nut_to_tuner_mm * cos(α))
        )

Flat headstock geometry (Fender-style):
    Without a string tree, there is effectively 0° break angle on the
    outer strings (G, D on a 6-inline). String trees push strings down
    to create the needed angle:

        break_angle = arctan(string_tree_depression_mm / nut_to_tree_mm)

Industry references:
    - Gibson: 14-17° headstock pitch → ~7-10° effective nut break angle
    - PRS: 10° headstock pitch → ~5-7° effective
    - Fender (with tree): ~7-8° on B & high-E via string tree
    - Fender (no tree): ~2-3° on low-E, A (adequate from tuner stagger)
    - Optimal nut break angle: 5-10°
    - Below 3° → poor nut contact, buzzing, sitar-like tone
    - Above 15° → excessive slot wear, tuning friction, string pinching

Author: Luthier's Toolbox
Version: 1.0.0
"""

from __future__ import annotations

import math
from typing import List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------------

TOO_SHALLOW_DEG = 3.0
OPTIMAL_MIN_DEG = 5.0
OPTIMAL_MAX_DEG = 10.0
TOO_STEEP_DEG = 15.0


# ---------------------------------------------------------------------------
# Input / Output models
# ---------------------------------------------------------------------------

class HeadstockBreakAngleInput(BaseModel):
    """Input parameters for nut break angle calculation."""

    headstock_type: str = Field(
        default="angled",
        description="Headstock type: 'angled' (Gibson/PRS) or 'flat' (Fender).",
    )

    # --- Angled headstock params ---
    headstock_angle_deg: float = Field(
        default=14.0,
        ge=0,
        le=25,
        description="Headstock pitch-back angle in degrees. Gibson: 14-17, PRS: 10, Fender: 0.",
    )
    nut_to_tuner_mm: float = Field(
        default=100.0,
        gt=0,
        description="Distance from nut to tuner post along headstock face (mm). Varies per string.",
    )
    tuner_post_height_mm: float = Field(
        default=6.0,
        ge=0,
        description="Height of tuner post capstan above headstock face (mm). Typically 5-8 mm.",
    )

    # --- Flat headstock / string tree params ---
    string_tree_depression_mm: float = Field(
        default=0.0,
        ge=0,
        description="How far the string tree pushes the string below the headstock plane (mm). Typical: 3-5 mm.",
    )
    nut_to_string_tree_mm: float = Field(
        default=40.0,
        gt=0,
        description="Distance from nut to the string tree (mm). Fender typical: 35-45 mm.",
    )

    # --- Common params ---
    nut_slot_depth_mm: float = Field(
        default=0.5,
        ge=0,
        description="How deep the string sits in the nut slot (mm). Half the string diameter is typical.",
    )


class NutRiskFlag(BaseModel):
    """A single risk or advisory flag."""

    code: str
    severity: str  # "info" | "warning" | "critical"
    message: str


class HeadstockBreakAngleResult(BaseModel):
    """Output of the nut break angle calculation."""

    break_angle_deg: float = Field(description="Effective string break angle at the nut (degrees).")
    rating: str = Field(description="Rating: optimal | acceptable | too_shallow | too_steep.")
    headstock_type: str
    headstock_angle_deg: float
    nut_downforce_quality: str = Field(description="Qualitative nut contact rating: excellent | good | fair | poor.")
    risk_flags: List[NutRiskFlag] = Field(default_factory=list)
    recommendation: Optional[str] = Field(default=None)
    needs_string_tree: bool = Field(
        default=False,
        description="True if a string tree is recommended (flat headstocks with shallow angle).",
    )


# ---------------------------------------------------------------------------
# Core calculation
# ---------------------------------------------------------------------------

def calculate_headstock_break_angle(inp: HeadstockBreakAngleInput) -> HeadstockBreakAngleResult:
    """
    Compute the effective string break angle at the nut.

    For angled headstocks, the geometry is:
        The string goes from the fretboard side, over the nut, and down to
        the tuner post on the angled headstock face. The effective angle is
        how steeply the string drops away behind the nut.

    For flat headstocks with string trees:
        The break angle comes from the string tree pushing the string
        down below the nut plane.
    """
    flags: list[NutRiskFlag] = []

    if inp.headstock_type == "flat":
        angle_deg = _calc_flat_headstock(inp, flags)
    else:
        angle_deg = _calc_angled_headstock(inp, flags)

    # --- Rating & nut downforce quality ---
    if angle_deg < TOO_SHALLOW_DEG:
        rating = "too_shallow"
        quality = "poor"
        flags.append(NutRiskFlag(
            code="SHALLOW_NUT_ANGLE",
            severity="warning",
            message=(
                f"Nut break angle {angle_deg:.1f}° is below {TOO_SHALLOW_DEG}°. "
                "Strings may buzz in the nut slots or produce a sitar-like tone. "
                "Open strings may lack clarity and sustain."
            ),
        ))
    elif angle_deg > TOO_STEEP_DEG:
        rating = "too_steep"
        quality = "fair"
        flags.append(NutRiskFlag(
            code="STEEP_NUT_ANGLE",
            severity="warning",
            message=(
                f"Nut break angle {angle_deg:.1f}° exceeds {TOO_STEEP_DEG}°. "
                "Excessive downward force can cause nut slot wear, tuning friction, "
                "and string pinching at the nut. Consider reducing headstock angle "
                "or raising tuner post height."
            ),
        ))
    elif OPTIMAL_MIN_DEG <= angle_deg <= OPTIMAL_MAX_DEG:
        rating = "optimal"
        quality = "excellent"
    else:
        rating = "acceptable"
        quality = "good"

    # --- String tree recommendation for flat headstocks ---
    needs_tree = False
    if inp.headstock_type == "flat" and inp.string_tree_depression_mm == 0.0:
        if angle_deg < OPTIMAL_MIN_DEG:
            needs_tree = True
            flags.append(NutRiskFlag(
                code="NEEDS_STRING_TREE",
                severity="info",
                message=(
                    "Flat headstock without string tree produces insufficient "
                    f"nut break angle ({angle_deg:.1f}°). A string tree providing "
                    f"3-5 mm depression is recommended."
                ),
            ))

    # --- Recommendation ---
    recommendation = None
    if rating == "too_shallow":
        if inp.headstock_type == "flat":
            recommendation = (
                "Add a string tree to increase nut break angle, or use "
                "staggered-height tuner posts."
            )
        else:
            target_angle = OPTIMAL_MIN_DEG
            recommendation = (
                f"Increase headstock angle to achieve at least {target_angle}° "
                f"nut break angle. Current headstock pitch: {inp.headstock_angle_deg}°."
            )
    elif rating == "too_steep":
        recommendation = (
            "Consider using taller tuner posts or reducing the headstock "
            f"pitch angle (currently {inp.headstock_angle_deg}°) to bring the "
            f"nut break angle below {TOO_STEEP_DEG}°."
        )

    return HeadstockBreakAngleResult(
        break_angle_deg=round(angle_deg, 2),
        rating=rating,
        headstock_type=inp.headstock_type,
        headstock_angle_deg=inp.headstock_angle_deg,
        nut_downforce_quality=quality,
        risk_flags=flags,
        recommendation=recommendation,
        needs_string_tree=needs_tree,
    )


# ---------------------------------------------------------------------------
# Internal geometry helpers
# ---------------------------------------------------------------------------

def _calc_angled_headstock(
    inp: HeadstockBreakAngleInput,
    flags: list[NutRiskFlag],
) -> float:
    """
    For an angled headstock the string path is:
        fretboard → nut crown → tuner post on the pitched-back face.

    The drop below the nut plane at the tuner post is:
        drop = nut_to_tuner * sin(headstock_angle) - tuner_post_height

    The horizontal run is:
        run = nut_to_tuner * cos(headstock_angle)

    The effective break angle = arctan(drop / run).
    If the tuner post is tall enough to bring the string above the nut
    plane, the effective angle goes negative (bad — string lifts off nut).
    """
    alpha = math.radians(inp.headstock_angle_deg)
    drop = inp.nut_to_tuner_mm * math.sin(alpha) - inp.tuner_post_height_mm
    run = inp.nut_to_tuner_mm * math.cos(alpha)

    if drop <= 0:
        flags.append(NutRiskFlag(
            code="STRING_ABOVE_NUT",
            severity="critical",
            message=(
                "Tuner post height exceeds the headstock drop at this distance. "
                "The string would lift off the nut slot — the nut cannot function. "
                "Lower the tuner posts or increase the headstock angle."
            ),
        ))
        return 0.0

    angle_deg = math.degrees(math.atan2(drop, run))
    return angle_deg


def _calc_flat_headstock(
    inp: HeadstockBreakAngleInput,
    flags: list[NutRiskFlag],
) -> float:
    """
    For a flat headstock (Fender-style), the headstock is co-planar with
    the fretboard (or has a very slight angle from the neck pocket).

    Without a string tree the only break angle comes from tuner post
    stagger (height differences between posts). With a string tree the
    depression provides the angle:

        angle = arctan(depression / distance_to_tree)

    If no string tree and no headstock angle, the break angle comes
    purely from any small headstock_angle_deg (Fender sometimes uses
    ~1° via the neck pocket tilt) plus tuner post geometry.
    """
    if inp.string_tree_depression_mm > 0:
        angle_deg = math.degrees(
            math.atan2(inp.string_tree_depression_mm, inp.nut_to_string_tree_mm)
        )
    elif inp.headstock_angle_deg > 0:
        # Slight angle (some Fender necks have 1-3° from pocket tilt)
        alpha = math.radians(inp.headstock_angle_deg)
        drop = inp.nut_to_tuner_mm * math.sin(alpha) - inp.tuner_post_height_mm
        run = inp.nut_to_tuner_mm * math.cos(alpha)
        if drop <= 0:
            return 0.0
        angle_deg = math.degrees(math.atan2(drop, run))
    else:
        # True flat headstock, no string tree — minimal angle from gravity only
        angle_deg = 0.0

    return angle_deg
