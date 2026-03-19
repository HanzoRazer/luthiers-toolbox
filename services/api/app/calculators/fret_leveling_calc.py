"""
Fret leveling geometry calculator (CONSTRUCTION-003).

Analyzes fret heights to determine which frets are high,
computes leveling plane, and estimates material removal.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


# ─── Constants ───────────────────────────────────────────────────────────────

# Tolerance for "high" fret detection (mm)
HIGH_FRET_TOLERANCE_MM = 0.03

# Minimum playable fret crown height (mm)
MIN_PLAYABLE_HEIGHT_MM = 0.5

# Typical relief range (mm) - concave bow measured at 8th fret
RELIEF_MIN_MM = 0.1
RELIEF_MAX_MM = 0.3
RELIEF_DEFAULT_MM = 0.2


@dataclass
class FretProfile:
    """Profile of a single fret's leveling status."""

    fret_number: int
    height_mm: float          # measured from fretboard
    deviation_mm: float       # from ideal plane (positive = high)
    status: str               # "high" / "low" / "ok"

    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "fret_number": self.fret_number,
            "height_mm": round(self.height_mm, 3),
            "deviation_mm": round(self.deviation_mm, 3),
            "status": self.status,
        }


@dataclass
class LevelingPlan:
    """Complete fret leveling analysis result."""

    frets: List[FretProfile]
    high_fret_count: int
    low_fret_count: int
    max_deviation_mm: float       # worst case high fret
    material_removal_mm: float    # amount to remove from highest fret
    replacement_needed: List[int]  # fret numbers that need replacement
    leveling_radius_mm: float     # radius of leveling beam arc
    gate: str                     # GREEN/YELLOW/RED
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "frets": [f.to_dict() for f in self.frets],
            "high_fret_count": self.high_fret_count,
            "low_fret_count": self.low_fret_count,
            "max_deviation_mm": round(self.max_deviation_mm, 3),
            "material_removal_mm": round(self.material_removal_mm, 3),
            "replacement_needed": self.replacement_needed,
            "leveling_radius_mm": round(self.leveling_radius_mm, 1),
            "gate": self.gate,
            "notes": self.notes,
        }


def _compute_fret_positions(scale_length_mm: float, fret_count: int) -> List[float]:
    """
    Compute fret positions from nut using 12-TET formula.

    Position of fret n = scale_length × (1 - 2^(-n/12))
    """
    positions = []
    for n in range(1, fret_count + 1):
        pos = scale_length_mm * (1 - 2 ** (-n / 12))
        positions.append(pos)
    return positions


def _compute_ideal_heights(
    fret_positions: List[float],
    base_height: float,
    relief_mm: float,
    scale_length_mm: float,
) -> List[float]:
    """
    Compute ideal fret heights accounting for neck relief.

    Relief creates a slight concave curve (lowest at ~8th fret).
    The relief curve is modeled as a parabola with apex at scale midpoint.
    """
    # Relief apex is typically around 7th-8th fret position
    # Model as parabola: height = base - relief × 4 × x × (1-x)
    # where x = position / scale_length (normalized 0-1)

    ideal_heights = []
    for pos in fret_positions:
        x = pos / scale_length_mm
        # Parabola with maximum dip at x=0.5
        relief_at_pos = relief_mm * 4 * x * (1 - x)
        ideal_height = base_height - relief_at_pos
        ideal_heights.append(ideal_height)

    return ideal_heights


def _linear_regression(x_vals: List[float], y_vals: List[float]) -> Tuple[float, float]:
    """
    Simple linear regression: y = mx + b
    Returns (slope, intercept).
    """
    n = len(x_vals)
    if n < 2:
        return 0.0, y_vals[0] if y_vals else 0.0

    sum_x = sum(x_vals)
    sum_y = sum(y_vals)
    sum_xy = sum(x * y for x, y in zip(x_vals, y_vals))
    sum_x2 = sum(x * x for x in x_vals)

    denom = n * sum_x2 - sum_x * sum_x
    if abs(denom) < 1e-10:
        return 0.0, sum_y / n

    slope = (n * sum_xy - sum_x * sum_y) / denom
    intercept = (sum_y - slope * sum_x) / n

    return slope, intercept


def compute_leveling_radius(
    scale_length_mm: float,
    relief_mm: float,
) -> float:
    """
    Compute the radius of the leveling beam arc.

    The leveling beam should follow the relief curve.
    For a parabolic relief, the radius at the apex is:
    R = L² / (8 × relief)
    where L is the chord length (approximately scale length).

    Args:
        scale_length_mm: Scale length in mm
        relief_mm: Target relief at 8th fret in mm

    Returns:
        Radius of leveling beam arc in mm
    """
    if relief_mm <= 0:
        return float('inf')  # Flat beam for zero relief

    # Approximate radius using circular arc formula
    # For small relief, this approximates the parabola well
    radius = (scale_length_mm ** 2) / (8 * relief_mm)
    return radius


def analyze_fret_heights(
    heights_mm: List[float],
    scale_length_mm: float,
    relief_mm: float = RELIEF_DEFAULT_MM,
    tolerance_mm: float = HIGH_FRET_TOLERANCE_MM,
) -> LevelingPlan:
    """
    Analyze measured fret heights to create a leveling plan.

    Args:
        heights_mm: Measured height at each fret (index 0 = fret 1)
        scale_length_mm: Scale length in mm
        relief_mm: Target neck relief in mm (default 0.2)
        tolerance_mm: Tolerance for high fret detection (default 0.03)

    Returns:
        LevelingPlan with analysis results
    """
    notes: List[str] = []
    gate = "GREEN"

    fret_count = len(heights_mm)
    if fret_count == 0:
        return LevelingPlan(
            frets=[],
            high_fret_count=0,
            low_fret_count=0,
            max_deviation_mm=0.0,
            material_removal_mm=0.0,
            replacement_needed=[],
            leveling_radius_mm=0.0,
            gate="RED",
            notes=["No fret heights provided"],
        )

    # Compute fret positions
    fret_positions = _compute_fret_positions(scale_length_mm, fret_count)

    # Fit a line to the measured heights (best-fit plane)
    slope, intercept = _linear_regression(fret_positions, heights_mm)

    # Compute fitted heights at each position
    fitted_heights = [slope * pos + intercept for pos in fret_positions]

    # Compute ideal heights with relief
    base_height = max(heights_mm)  # Use highest measured as baseline
    ideal_heights = _compute_ideal_heights(
        fret_positions, base_height, relief_mm, scale_length_mm
    )

    # Analyze each fret
    fret_profiles: List[FretProfile] = []
    high_frets: List[int] = []
    low_frets: List[int] = []
    replacement_needed: List[int] = []
    max_deviation = 0.0

    for i, (measured, fitted, ideal) in enumerate(zip(heights_mm, fitted_heights, ideal_heights)):
        fret_num = i + 1

        # Deviation from fitted plane (positive = high)
        deviation = measured - fitted

        # Determine status
        if deviation > tolerance_mm:
            status = "high"
            high_frets.append(fret_num)
            if deviation > max_deviation:
                max_deviation = deviation
        elif deviation < -tolerance_mm:
            status = "low"
            low_frets.append(fret_num)
        else:
            status = "ok"

        # Check if fret needs replacement (too low after leveling)
        post_level_height = measured - max_deviation
        if post_level_height < MIN_PLAYABLE_HEIGHT_MM:
            replacement_needed.append(fret_num)

        fret_profiles.append(FretProfile(
            fret_number=fret_num,
            height_mm=measured,
            deviation_mm=deviation,
            status=status,
        ))

    # Compute leveling radius
    leveling_radius = compute_leveling_radius(scale_length_mm, relief_mm)

    # Determine gate status and notes
    material_removal = max_deviation if max_deviation > 0 else 0.0

    if len(replacement_needed) > 0:
        gate = "RED"
        notes.append(f"Frets {replacement_needed} need replacement (too low after leveling)")
    elif len(high_frets) > fret_count * 0.3:
        gate = "YELLOW"
        notes.append(f"{len(high_frets)} high frets detected — significant leveling needed")
    elif material_removal > 0.15:
        gate = "YELLOW"
        notes.append(f"Material removal {material_removal:.2f}mm exceeds typical 0.15mm")

    if len(high_frets) == 0 and len(low_frets) == 0:
        notes.append("All frets within tolerance — no leveling needed")
    elif len(high_frets) > 0:
        notes.append(f"High frets: {high_frets}")

    if relief_mm < RELIEF_MIN_MM:
        notes.append(f"Relief {relief_mm}mm below typical minimum ({RELIEF_MIN_MM}mm)")
    elif relief_mm > RELIEF_MAX_MM:
        notes.append(f"Relief {relief_mm}mm above typical maximum ({RELIEF_MAX_MM}mm)")

    return LevelingPlan(
        frets=fret_profiles,
        high_fret_count=len(high_frets),
        low_fret_count=len(low_frets),
        max_deviation_mm=max_deviation,
        material_removal_mm=material_removal,
        replacement_needed=replacement_needed,
        leveling_radius_mm=leveling_radius,
        gate=gate,
        notes=notes,
    )


def check_single_fret(
    fret_height: float,
    neighbor_avg: float,
    tolerance_mm: float = HIGH_FRET_TOLERANCE_MM,
) -> str:
    """
    Check if a single fret is high relative to its neighbors.

    Args:
        fret_height: Height of the fret being checked
        neighbor_avg: Average height of adjacent frets
        tolerance_mm: Tolerance for high detection

    Returns:
        Status: "high", "low", or "ok"
    """
    deviation = fret_height - neighbor_avg
    if deviation > tolerance_mm:
        return "high"
    elif deviation < -tolerance_mm:
        return "low"
    return "ok"
