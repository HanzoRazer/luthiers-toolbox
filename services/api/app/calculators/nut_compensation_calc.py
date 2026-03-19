"""
GEOMETRY-007: Nut Compensation Calculator - Zero-Fret vs Traditional

Traditional nut compensation:
  The open string is effectively fretted at a point higher than fret height,
  causing sharpness. Compensation moves the nut slightly forward (toward saddle).

  nut_setback_mm = (action_at_nut_mm - fret_height_mm)
                   × scale_length_mm / 1000
                   × compensation_factor (0.5-0.8)

Zero-fret:
  Open string height equals fretted height (same contact point type).
  No compensation needed at nut - all intonation handled at saddle.

Compensated nut:
  Per-string setback like saddle compensation.
  Most accurate but requires precision manufacturing.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Literal

Gate = Literal["GREEN", "YELLOW", "RED"]
NutType = Literal["traditional", "zero_fret", "compensated"]

# Compensation factors by nut type
COMPENSATION_FACTORS = {
    "traditional": 0.65,      # Middle of 0.5-0.8 range
    "compensated": 0.75,      # More precise compensation
    "zero_fret": 0.0,         # No compensation needed
}

# Intonation error thresholds (cents)
ERROR_THRESHOLD_GREEN = 2.0   # Imperceptible
ERROR_THRESHOLD_YELLOW = 5.0  # Noticeable to trained ears


@dataclass
class NutCompensationSpec:
    """Nut compensation specification result."""

    nut_type: str
    setback_mm: float              # Nut forward of theoretical zero point
    intonation_error_cents: float  # Estimated error at open string
    gate: Gate
    recommendation: str


def _estimate_intonation_error_cents(
    action_at_nut_mm: float,
    fret_height_mm: float,
    setback_mm: float,
    nut_type: str,
) -> float:
    """
    Estimate intonation error in cents from nut configuration.

    The error comes from string stretch when fretting at fret 1.
    Higher action above fret height = more stretch = sharper pitch.

    For zero-fret, the open string height equals fret height,
    so there's no additional stretch compared to fretted notes.

    Formula approximation:
      error_cents ≈ (height_diff_mm / effective_string_length_mm) × 1200
      where height_diff is action_at_nut - fret_height after compensation
    """
    if nut_type == "zero_fret":
        # Zero-fret eliminates the height difference
        return 0.0

    # Effective height difference after compensation
    # Setback reduces the effect of the height difference
    height_diff = action_at_nut_mm - fret_height_mm

    if height_diff <= 0:
        # Action at or below fret height - no error
        return 0.0

    # Compensation reduces error proportionally
    # Each mm of setback reduces error by approximately 0.5 cents per mm of scale
    compensation_effect = setback_mm * 0.8

    # Base error from height difference (roughly 3-5 cents per 0.5mm excess)
    base_error = height_diff * 6.0

    # Net error after compensation
    net_error = max(0.0, base_error - compensation_effect)

    return round(net_error, 2)


def compute_nut_compensation(
    action_at_nut_mm: float,
    fret_height_mm: float,
    scale_length_mm: float,
    nut_type: str = "traditional",
) -> NutCompensationSpec:
    """
    Compute nut compensation for a given configuration.

    Traditional nut compensation formula:
      setback_mm = (action_at_nut_mm - fret_height_mm)
                   × scale_length_mm / 1000
                   × compensation_factor

    Args:
        action_at_nut_mm: String height at nut (bottom of string to fretboard)
        fret_height_mm: Height of frets above fretboard
        scale_length_mm: Scale length in mm
        nut_type: "traditional", "zero_fret", or "compensated"

    Returns:
        NutCompensationSpec with setback, error estimate, and recommendation
    """
    # Normalize nut type
    nut_type = nut_type.lower().strip()
    if nut_type not in COMPENSATION_FACTORS:
        nut_type = "traditional"

    # Get compensation factor
    comp_factor = COMPENSATION_FACTORS[nut_type]

    # Calculate height difference
    height_diff = max(0.0, action_at_nut_mm - fret_height_mm)

    # Calculate setback
    if nut_type == "zero_fret":
        setback_mm = 0.0
    else:
        setback_mm = height_diff * (scale_length_mm / 1000.0) * comp_factor
        setback_mm = round(setback_mm, 3)

    # Estimate intonation error
    error_cents = _estimate_intonation_error_cents(
        action_at_nut_mm=action_at_nut_mm,
        fret_height_mm=fret_height_mm,
        setback_mm=setback_mm,
        nut_type=nut_type,
    )

    # Determine gate and recommendation
    if error_cents <= ERROR_THRESHOLD_GREEN:
        gate: Gate = "GREEN"
        if nut_type == "zero_fret":
            recommendation = "Zero-fret provides optimal intonation"
        elif nut_type == "compensated":
            recommendation = "Compensated nut provides excellent intonation"
        else:
            recommendation = f"Apply {setback_mm:.3f}mm setback for good intonation"
    elif error_cents <= ERROR_THRESHOLD_YELLOW:
        gate = "YELLOW"
        recommendation = f"Estimated {error_cents:.1f} cents error - consider compensated nut"
    else:
        gate = "RED"
        recommendation = f"High intonation error ({error_cents:.1f} cents) - recommend zero-fret or compensated nut"

    return NutCompensationSpec(
        nut_type=nut_type,
        setback_mm=setback_mm,
        intonation_error_cents=error_cents,
        gate=gate,
        recommendation=recommendation,
    )


def compare_nut_types(
    action_at_nut_mm: float,
    fret_height_mm: float,
    scale_length_mm: float,
) -> List[NutCompensationSpec]:
    """
    Compare all nut types for a given configuration.

    Returns compensation specs for traditional, zero_fret, and compensated
    nuts, sorted by intonation error (best first).

    Args:
        action_at_nut_mm: String height at nut
        fret_height_mm: Height of frets above fretboard
        scale_length_mm: Scale length in mm

    Returns:
        List of NutCompensationSpec, sorted by error (lowest first)
    """
    results = []

    for nut_type in ["traditional", "zero_fret", "compensated"]:
        spec = compute_nut_compensation(
            action_at_nut_mm=action_at_nut_mm,
            fret_height_mm=fret_height_mm,
            scale_length_mm=scale_length_mm,
            nut_type=nut_type,
        )
        results.append(spec)

    # Sort by intonation error (best first)
    results.sort(key=lambda x: x.intonation_error_cents)

    return results


def compute_zero_fret_positions(
    scale_length_mm: float,
    fret_count: int,
    zero_fret_crown_width_mm: float = 1.0,
) -> dict:
    """
    Compute fret positions adjusted for zero-fret reference.

    With a zero-fret:
    - Scale length is measured from zero-fret crown center to saddle
    - All fret positions shift by half the zero-fret crown width
    - The nut becomes a string guide only (1-2mm behind zero-fret)

    Args:
        scale_length_mm: Scale length in mm
        fret_count: Number of frets (not including zero-fret)
        zero_fret_crown_width_mm: Width of zero-fret crown (typically 1.0mm)

    Returns:
        Dict with zero_fret_position, nut_guide_position, and fret_positions
    """
    # Zero-fret position (at scale origin)
    zero_fret_position = 0.0

    # Nut guide position (behind zero-fret)
    nut_guide_offset = 1.5  # mm behind zero-fret
    nut_guide_position = -nut_guide_offset

    # Calculate standard fret positions using 12-TET formula
    # Position from nut = scale_length × (1 - 2^(-fret/12))
    fret_positions = []
    for fret in range(1, fret_count + 1):
        position = scale_length_mm * (1.0 - math.pow(2, -fret / 12.0))
        fret_positions.append(round(position, 3))

    # Adjustment for zero-fret crown width
    # The string contacts at crown center, which is half the crown width
    crown_offset = zero_fret_crown_width_mm / 2.0

    return {
        "zero_fret_position_mm": zero_fret_position,
        "nut_guide_position_mm": round(nut_guide_position, 3),
        "nut_guide_offset_mm": nut_guide_offset,
        "crown_offset_mm": round(crown_offset, 3),
        "fret_positions_mm": fret_positions,
        "fret_count": fret_count,
        "scale_length_mm": scale_length_mm,
        "notes": [
            "Zero-fret replaces nut as intonation reference",
            "Nut serves as string guide only",
            f"All measurements from zero-fret crown center (+{crown_offset:.2f}mm from crown edge)",
        ],
    }


def get_nut_type_info(nut_type: str) -> dict:
    """Get information about a nut type."""
    info = {
        "traditional": {
            "name": "Traditional Nut",
            "description": "Standard bone/plastic/brass nut with slots",
            "compensation": "Single setback value for all strings",
            "pros": ["Simple to make", "Easy to replace", "Classic tone"],
            "cons": ["Intonation compromise", "Open strings slightly sharp"],
            "compensation_factor": COMPENSATION_FACTORS["traditional"],
        },
        "zero_fret": {
            "name": "Zero Fret",
            "description": "Fret at nut position, nut becomes string guide",
            "compensation": "None needed - open string height equals fretted",
            "pros": ["Perfect open string intonation", "Consistent tone open/fretted", "Eliminates nut slot precision"],
            "cons": ["Visual preference", "Extra fret to install", "Guide nut still needed"],
            "compensation_factor": COMPENSATION_FACTORS["zero_fret"],
        },
        "compensated": {
            "name": "Compensated Nut",
            "description": "Per-string setback like compensated saddle",
            "compensation": "Individual setback per string",
            "pros": ["Best intonation for traditional setup", "Per-string optimization"],
            "cons": ["Complex to manufacture", "Expensive", "Difficult to replace"],
            "compensation_factor": COMPENSATION_FACTORS["compensated"],
        },
    }
    return info.get(nut_type.lower(), info["traditional"])


def list_nut_types() -> List[str]:
    """Return list of available nut types."""
    return ["traditional", "zero_fret", "compensated"]
