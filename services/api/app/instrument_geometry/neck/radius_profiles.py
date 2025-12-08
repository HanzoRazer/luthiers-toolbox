"""
Instrument Geometry: Radius Profiles

Functions for computing fretboard and bridge radius curves.

See docs/KnowledgeBase/Instrument_Geometry/Radius_Theory_Compound.md
for theory and references.

Radius Theory:
    The fretboard radius is the radius of the cylindrical surface
    that forms the fretboard's cross-section. A smaller radius
    creates a more curved surface (easier for barre chords),
    while a larger radius is flatter (better for bending).

    Compound radius fretboards transition from a smaller radius
    at the nut to a larger radius at the higher frets, combining
    the benefits of both.

Common Radius Values:
    - 7.25" (184mm): Vintage Fender - very curved
    - 9.5" (241mm): Modern Fender - moderate curve
    - 10" (254mm): PRS, some Gibsons
    - 12" (305mm): Gibson standard - flatter
    - 14" (356mm): Ibanez JEM
    - 16" (406mm): Martin acoustic, some shred guitars
    - 20" (508mm): Very flat, almost classical feel
    - Flat/Infinite: Classical guitars

Moved from: instrument_geometry/radius_profiles.py (Wave 14 reorg)
"""

from __future__ import annotations

from math import sqrt, asin, pi
from typing import List, Tuple, Optional

from .neck_profiles import RadiusProfile


def compute_compound_radius_at_fret(
    fret_index: int,
    total_frets: int,
    start_radius_mm: float,
    end_radius_mm: float,
) -> float:
    """
    Compute the fretboard radius at a specific fret for compound radius.

    Uses linear interpolation between start and end radius.

    Args:
        fret_index: Fret number (0 = nut, 1 = first fret, etc.)
        total_frets: Total number of frets on the instrument.
        start_radius_mm: Radius at the nut.
        end_radius_mm: Radius at the last fret.

    Returns:
        Radius in mm at the specified fret.

    Example:
        >>> radius = compute_compound_radius_at_fret(12, 22, 241.3, 406.4)
        >>> round(radius, 1)
        331.4  # Roughly 13" at the 12th fret
    """
    if total_frets <= 0:
        return start_radius_mm

    ratio = fret_index / total_frets
    ratio = max(0.0, min(1.0, ratio))

    return start_radius_mm + (end_radius_mm - start_radius_mm) * ratio


def compute_radius_arc_points(
    radius_mm: float,
    width_mm: float,
    num_points: int = 50,
) -> List[Tuple[float, float]]:
    """
    Generate points along a radius arc for visualization or CNC.

    The arc is centered at (0, 0) with the center of the arc
    at (0, -radius_mm). Points span from -width/2 to +width/2.

    Args:
        radius_mm: Radius of the arc.
        width_mm: Total width to span.
        num_points: Number of points to generate.

    Returns:
        List of (x, y) points along the arc.
        X ranges from -width/2 to +width/2.
        Y is the height above the chord (0 at edges).

    Example:
        >>> points = compute_radius_arc_points(241.3, 42.0, 5)
        >>> len(points)
        5
    """
    if radius_mm <= 0 or width_mm <= 0 or num_points < 2:
        return []

    half_width = width_mm / 2.0

    # Check if width exceeds possible arc
    if half_width >= radius_mm:
        # Return a semicircle approximation
        half_width = radius_mm * 0.99

    points: List[Tuple[float, float]] = []

    for i in range(num_points):
        # X position from -half_width to +half_width
        t = i / (num_points - 1)
        x = -half_width + (width_mm * t)

        # Y position on the arc
        # Circle equation: x^2 + (y - r)^2 = r^2
        # Solving for y: y = r - sqrt(r^2 - x^2)
        y = radius_mm - sqrt(radius_mm**2 - x**2)

        points.append((x, y))

    return points


def compute_radius_drop_mm(radius_mm: float, offset_mm: float) -> float:
    """
    Compute the height drop at a given offset from center on a radius.

    This is useful for calculating how much lower the fretboard edge
    is compared to the center, or saddle height adjustments.

    Args:
        radius_mm: Radius of the curve.
        offset_mm: Distance from center (e.g., half the string spread).

    Returns:
        Height drop in mm.

    Example:
        >>> drop = compute_radius_drop_mm(241.3, 21.0)  # 9.5" radius, 42mm board
        >>> round(drop, 2)
        0.92  # Almost 1mm drop at the edge
    """
    if radius_mm <= 0 or offset_mm < 0:
        return 0.0

    if offset_mm >= radius_mm:
        # Mathematically impossible - would be past the circle
        return radius_mm

    # Height drop = r - sqrt(r^2 - x^2)
    return radius_mm - sqrt(radius_mm**2 - offset_mm**2)


def compute_fret_crown_height_mm(
    fretboard_radius_mm: float,
    fret_width_mm: float,
    fret_height_mm: float,
) -> float:
    """
    Compute the effective crown height of a fret on a radiused board.

    The actual fret crown height above the fretboard surface
    is affected by the fretboard radius - the crown appears
    slightly lower at the edges than the center.

    Args:
        fretboard_radius_mm: Fretboard radius.
        fret_width_mm: Width of the fret crown.
        fret_height_mm: Nominal fret height above the board.

    Returns:
        Crown height at center vs. the mathematical surface.
    """
    # For practical purposes, the fret follows the board radius
    # The crown height is essentially the fret height
    # This function exists for completeness and potential
    # future refinements (e.g., fret leveling calculations)
    return fret_height_mm


def compute_string_height_at_fret(
    fretboard_radius_mm: float,
    string_position_mm: float,
    action_center_mm: float,
) -> float:
    """
    Compute the string height at a given position accounting for radius.

    Args:
        fretboard_radius_mm: Fretboard radius at this fret.
        string_position_mm: Lateral position from center (signed).
        action_center_mm: Action height at the center of the fretboard.

    Returns:
        Actual string height at this position.
    """
    radius_drop = compute_radius_drop_mm(fretboard_radius_mm, abs(string_position_mm))
    return action_center_mm + radius_drop


def generate_compound_radius_profile(
    start_radius_mm: float,
    end_radius_mm: float,
    total_frets: int,
) -> RadiusProfile:
    """
    Create a RadiusProfile object for a compound radius fretboard.

    Args:
        start_radius_mm: Radius at the nut.
        end_radius_mm: Radius at the last fret.
        total_frets: Total number of frets.

    Returns:
        RadiusProfile configured for compound radius.
    """
    return RadiusProfile(
        base_radius_mm=start_radius_mm,
        end_radius_mm=end_radius_mm,
    )


# Radius conversion helpers
def inches_to_mm(inches: float) -> float:
    """Convert inches to millimeters."""
    return inches * 25.4


def mm_to_inches(mm: float) -> float:
    """Convert millimeters to inches."""
    return mm / 25.4
