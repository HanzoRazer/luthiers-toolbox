"""
Nut compensation calculator (GEOMETRY-007).

Compares traditional nut vs zero-fret systems and calculates
compensation required for accurate open string intonation.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Literal, Dict


# ─── Constants ───────────────────────────────────────────────────────────────

# Typical nut width range (mm)
NUT_WIDTH_MIN_MM = 1.5
NUT_WIDTH_MAX_MM = 6.0
NUT_WIDTH_DEFAULT_MM = 3.0

# Zero-fret offset from nut guide (mm)
ZERO_FRET_TO_NUT_GUIDE_MM = 1.5

# Fret crown width (affects zero-fret reference point)
FRET_CROWN_WIDTH_MM = 2.4

# Cents per semitone
CENTS_PER_SEMITONE = 100

NutType = Literal["traditional", "zero_fret"]


@dataclass
class NutCompSpec:
    """Nut compensation specification."""

    nut_type: str                        # "traditional" | "zero_fret"
    compensation_mm: float               # amount to shift nut/zero-fret
    effective_scale_length_mm: float     # scale length after compensation
    open_string_pitch_error_cents: float # error if no compensation applied
    gate: str                            # GREEN/YELLOW/RED
    recommendation: str                  # advice for builder

    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "nut_type": self.nut_type,
            "compensation_mm": round(self.compensation_mm, 3),
            "effective_scale_length_mm": round(self.effective_scale_length_mm, 2),
            "open_string_pitch_error_cents": round(self.open_string_pitch_error_cents, 1),
            "gate": self.gate,
            "recommendation": self.recommendation,
        }


def _cents_from_length_error(error_mm: float, scale_length_mm: float) -> float:
    """
    Calculate pitch error in cents from a length error.

    Frequency ratio = 2^(cents/1200)
    For small errors: cents ≈ 1200 × ln(1 + error/scale_length) / ln(2)
                    ≈ 1731.2 × error / scale_length
    """
    if scale_length_mm <= 0:
        return 0.0
    # Using exact formula
    ratio = 1 + (error_mm / scale_length_mm)
    if ratio <= 0:
        return 0.0
    cents = 1200 * math.log2(ratio)
    return cents


def compute_nut_compensation(
    nut_type: str,
    nut_width_mm: float,
    break_angle_deg: float,
    scale_length_mm: float,
) -> NutCompSpec:
    """
    Compute nut compensation for traditional or zero-fret system.

    Args:
        nut_type: "traditional" or "zero_fret"
        nut_width_mm: Width of nut slot (string contact to back face)
        break_angle_deg: String break angle at nut (typically 5-15°)
        scale_length_mm: Nominal scale length

    Returns:
        NutCompSpec with compensation details
    """
    gate = "GREEN"
    recommendation = ""

    # Normalize nut type
    nut_type_lower = nut_type.lower().replace("-", "_").replace(" ", "_")

    if nut_type_lower == "zero_fret":
        # Zero-fret: compensation is half the fret crown width
        # The zero-fret crown center is the reference point
        compensation_mm = FRET_CROWN_WIDTH_MM / 2

        # Effective scale length is from zero-fret crown center to saddle
        effective_scale = scale_length_mm

        # Open string pitch error without compensation is negligible
        # (the zero-fret sets the exact position)
        pitch_error = 0.0

        recommendation = (
            f"Zero-fret eliminates nut intonation issues. "
            f"Place nut guide {ZERO_FRET_TO_NUT_GUIDE_MM}mm behind zero-fret."
        )

    else:  # traditional
        # Traditional nut: compensation based on nut width and break angle
        # The string contact point is shifted from theoretical zero
        # by approximately (nut_width / 2) × (1 - cos(break_angle))

        break_angle_rad = math.radians(break_angle_deg)
        cos_factor = 1 - math.cos(break_angle_rad)

        # For very small angles, the cosine factor is tiny
        # Use a minimum factor based on string deflection
        min_factor = 0.02  # Minimum 2% of nut width

        effective_factor = max(cos_factor, min_factor)
        compensation_mm = (nut_width_mm / 2) * effective_factor

        # Add component for string stretching at nut
        # Heavier strings need more compensation (simplified model)
        stretch_component = 0.3  # Base stretch compensation

        compensation_mm += stretch_component

        # Effective scale length accounts for string contact offset
        effective_scale = scale_length_mm - compensation_mm

        # Pitch error if no compensation is applied
        # The string is effectively shorter than intended
        uncompensated_error = nut_width_mm / 2
        pitch_error = _cents_from_length_error(uncompensated_error, scale_length_mm)

        # Determine gate status
        if pitch_error > 5.0:
            gate = "YELLOW"
            recommendation = (
                f"Uncompensated pitch error of {pitch_error:.1f} cents is noticeable. "
                f"Apply {compensation_mm:.2f}mm nut compensation."
            )
        elif pitch_error > 10.0:
            gate = "RED"
            recommendation = (
                f"Uncompensated pitch error of {pitch_error:.1f} cents is severe. "
                f"Compensated nut or zero-fret strongly recommended."
            )
        else:
            recommendation = (
                f"Apply {compensation_mm:.2f}mm compensation for best intonation. "
                f"Error without compensation: {pitch_error:.1f} cents."
            )

    # Validate inputs
    if nut_width_mm < NUT_WIDTH_MIN_MM or nut_width_mm > NUT_WIDTH_MAX_MM:
        gate = "YELLOW"
        recommendation = (
            f"Nut width {nut_width_mm}mm outside typical range "
            f"({NUT_WIDTH_MIN_MM}-{NUT_WIDTH_MAX_MM}mm). " + recommendation
        )

    if break_angle_deg < 3.0:
        gate = "YELLOW" if gate == "GREEN" else gate
        recommendation = f"Break angle {break_angle_deg}° is low; may cause tuning instability. " + recommendation

    return NutCompSpec(
        nut_type=nut_type,
        compensation_mm=compensation_mm,
        effective_scale_length_mm=effective_scale,
        open_string_pitch_error_cents=pitch_error,
        gate=gate,
        recommendation=recommendation,
    )


def compare_nut_types(
    scale_length_mm: float,
    nut_width_mm: float = NUT_WIDTH_DEFAULT_MM,
    break_angle_deg: float = 10.0,
) -> Dict[str, dict]:
    """
    Compare traditional nut vs zero-fret for given parameters.

    Args:
        scale_length_mm: Scale length in mm
        nut_width_mm: Nut width in mm (default 3.0)
        break_angle_deg: Break angle in degrees (default 10.0)

    Returns:
        Dictionary with specs for both nut types
    """
    traditional = compute_nut_compensation(
        nut_type="traditional",
        nut_width_mm=nut_width_mm,
        break_angle_deg=break_angle_deg,
        scale_length_mm=scale_length_mm,
    )

    zero_fret = compute_nut_compensation(
        nut_type="zero_fret",
        nut_width_mm=nut_width_mm,
        break_angle_deg=break_angle_deg,
        scale_length_mm=scale_length_mm,
    )

    return {
        "traditional": traditional.to_dict(),
        "zero_fret": zero_fret.to_dict(),
        "comparison": {
            "pitch_error_difference_cents": round(
                traditional.open_string_pitch_error_cents - zero_fret.open_string_pitch_error_cents, 1
            ),
            "zero_fret_advantage": "Eliminates nut slot intonation errors; consistent tone open vs fretted",
            "traditional_advantage": "Simpler construction; no additional fret slot required",
        },
    }


def compute_per_string_compensation(
    gauges_mm: List[float],
    is_wound: List[bool],
    nut_width_mm: float,
    break_angle_deg: float,
) -> List[float]:
    """
    Compute compensation for each string (compensated nut).

    Heavier/wound strings need slightly more compensation.

    Args:
        gauges_mm: String gauge in mm for each string
        is_wound: Whether each string is wound
        nut_width_mm: Nut width in mm
        break_angle_deg: Break angle at nut

    Returns:
        List of compensation values (mm) per string
    """
    compensations = []

    break_angle_rad = math.radians(break_angle_deg)
    base_factor = max(0.02, 1 - math.cos(break_angle_rad))

    for gauge, wound in zip(gauges_mm, is_wound):
        # Base compensation from geometry
        base_comp = (nut_width_mm / 2) * base_factor

        # Gauge factor: heavier strings deflect more
        # Normalize to 0.010" (0.254mm) as baseline
        gauge_factor = gauge / 0.254

        # Wound strings have more mass, need slightly more compensation
        wound_factor = 1.1 if wound else 1.0

        compensation = base_comp * gauge_factor * wound_factor

        # Add minimum stretch compensation
        compensation += 0.2 * gauge_factor

        compensations.append(round(compensation, 3))

    return compensations
