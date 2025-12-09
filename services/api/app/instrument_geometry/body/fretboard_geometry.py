"""
Instrument Geometry: Fretboard Geometry

Functions for computing fretboard outlines, widths, and tapers.

See docs/KnowledgeBase/Instrument_Geometry/Fretboard_Geometry.md
for theory and references.

Moved from: instrument_geometry/fretboard_geometry.py (Wave 14 reorg)
"""

from __future__ import annotations

from typing import List, Tuple, Optional

from ..neck.fret_math import compute_fret_positions_mm
from ..neck.neck_profiles import FretboardSpec


def compute_fretboard_outline(
    nut_width_mm: float,
    heel_width_mm: float,
    scale_length_mm: float,
    fret_count: int,
    extension_mm: float = 0.0,
) -> List[Tuple[float, float]]:
    """
    Compute the 2D outline of a fretboard in mm (local coordinate system).

    The coordinate system:
    - Origin (0, 0) is at the center of the nut
    - X-axis runs along the fretboard length (positive toward bridge)
    - Y-axis runs across the fretboard width

    Args:
        nut_width_mm: Width of the fretboard at the nut.
        heel_width_mm: Width of the fretboard at the last fret/heel.
        scale_length_mm: Full scale length in mm.
        fret_count: Number of frets.
        extension_mm: Extra length past the last fret (common on acoustics).

    Returns:
        List of (x, y) points forming the fretboard outline (closed polygon).
        Points are in order: nut left, heel left, heel right, nut right.

    Example:
        >>> outline = compute_fretboard_outline(42.0, 56.0, 648.0, 22)
        >>> len(outline)
        4
    """
    if scale_length_mm <= 0 or fret_count <= 0:
        raise ValueError("scale_length_mm and fret_count must be > 0")

    # Get position of last fret
    fret_positions = compute_fret_positions_mm(scale_length_mm, fret_count)
    heel_position = fret_positions[-1] + extension_mm

    # Half-widths
    half_nut = nut_width_mm / 2.0
    half_heel = heel_width_mm / 2.0

    # Outline points (counterclockwise from top-left)
    outline = [
        (0.0, -half_nut),           # Nut left (bass side)
        (heel_position, -half_heel), # Heel left
        (heel_position, half_heel),  # Heel right (treble side)
        (0.0, half_nut),            # Nut right
    ]

    return outline


def compute_width_at_position_mm(
    nut_width_mm: float,
    heel_width_mm: float,
    scale_length_mm: float,
    fret_count: int,
    position_mm: float,
) -> float:
    """
    Compute the fretboard width at a specific position along its length.

    Uses linear taper from nut to heel.

    Args:
        nut_width_mm: Width at the nut.
        heel_width_mm: Width at the heel.
        scale_length_mm: Full scale length.
        fret_count: Number of frets.
        position_mm: Distance from the nut.

    Returns:
        Width in mm at the specified position.
    """
    fret_positions = compute_fret_positions_mm(scale_length_mm, fret_count)
    heel_position = fret_positions[-1]

    if heel_position <= 0:
        return nut_width_mm

    # Linear interpolation
    ratio = min(1.0, max(0.0, position_mm / heel_position))
    return nut_width_mm + (heel_width_mm - nut_width_mm) * ratio


def compute_fret_slot_lines(
    spec: FretboardSpec,
) -> List[Tuple[Tuple[float, float], Tuple[float, float]]]:
    """
    Compute the start and end points for each fret slot.

    Each fret slot is a line segment perpendicular to the fretboard
    centerline, extending across the full width at that position.

    Args:
        spec: FretboardSpec with nut_width, heel_width, scale_length, fret_count.

    Returns:
        List of ((x1, y1), (x2, y2)) tuples, one per fret.
        Each tuple defines the bass-side and treble-side endpoints of the slot.

    Example:
        >>> spec = FretboardSpec(42.0, 56.0, 648.0, 22)
        >>> slots = compute_fret_slot_lines(spec)
        >>> len(slots)
        22
    """
    fret_positions = compute_fret_positions_mm(spec.scale_length_mm, spec.fret_count)
    slots: List[Tuple[Tuple[float, float], Tuple[float, float]]] = []

    for pos in fret_positions:
        width = compute_width_at_position_mm(
            spec.nut_width_mm,
            spec.heel_width_mm,
            spec.scale_length_mm,
            spec.fret_count,
            pos,
        )
        half_width = width / 2.0

        # Slot endpoints (perpendicular to centerline)
        bass_point = (pos, -half_width)
        treble_point = (pos, half_width)
        slots.append((bass_point, treble_point))

    return slots


def compute_string_spacing_at_position(
    nut_width_mm: float,
    heel_width_mm: float,
    scale_length_mm: float,
    fret_count: int,
    string_count: int,
    position_mm: float,
    edge_offset_mm: float = 3.0,
) -> List[float]:
    """
    Compute the Y-positions of each string at a given fretboard position.

    Args:
        nut_width_mm: Width at the nut.
        heel_width_mm: Width at the heel.
        scale_length_mm: Full scale length.
        fret_count: Number of frets.
        string_count: Number of strings.
        position_mm: Distance from the nut.
        edge_offset_mm: Distance from edge to first/last string.

    Returns:
        List of Y-positions for each string (bass to treble).
    """
    width = compute_width_at_position_mm(
        nut_width_mm, heel_width_mm, scale_length_mm, fret_count, position_mm
    )

    usable_width = width - (2 * edge_offset_mm)
    half_width = width / 2.0

    if string_count <= 1:
        return [0.0]

    string_positions: List[float] = []
    spacing = usable_width / (string_count - 1)

    for i in range(string_count):
        y = -half_width + edge_offset_mm + (i * spacing)
        string_positions.append(y)

    return string_positions


def compute_compound_radius_at_position(
    base_radius_mm: Optional[float],
    end_radius_mm: Optional[float],
    position_mm: float,
    scale_length_mm: float,
) -> Optional[float]:
    """
    Compute fretboard radius at a specific position for compound radius boards.

    Compound radius fretboards taper from a tighter curve at the nut
    (e.g., 9.5" or 241.3mm) to a flatter curve at the heel (e.g., 12" or 304.8mm).
    This provides comfortable chord playing at lower frets and easier bending
    at higher frets.

    Uses linear interpolation between base and end radii.

    Args:
        base_radius_mm: Radius at the nut (e.g., 241.3mm for 9.5").
        end_radius_mm: Radius at the heel (e.g., 304.8mm for 12").
        position_mm: Distance from the nut to the point of interest.
        scale_length_mm: Full scale length for normalization.

    Returns:
        Interpolated radius in mm at the specified position.
        Returns None if base_radius_mm is None (flat fretboard).

    Example:
        >>> # Compound 9.5" → 12" radius on 25.5" scale
        >>> radius_at_12th = compute_compound_radius_at_position(
        ...     241.3, 304.8, 324.0, 648.0
        ... )
        >>> round(radius_at_12th, 1)
        273.1  # Halfway blend at 12th fret

    Notes:
        - If end_radius_mm is None, returns base_radius_mm (constant radius).
        - Position beyond scale_length returns end_radius_mm.
        - Common presets:
            * Vintage Fender: 7.25" constant (184.2mm)
            * Modern Fender: 9.5" constant (241.3mm)
            * PRS Compound: 10" → 13.5" (254mm → 342.9mm)
            * Ibanez Wizard: 15.75" → 17" (400mm → 431.8mm)

    Wave 17 Phase C Enhancement (December 2025)
    """
    if base_radius_mm is None:
        return None

    if end_radius_mm is None:
        return base_radius_mm

    # Normalize position (0.0 at nut, 1.0 at scale length)
    if scale_length_mm <= 0:
        return base_radius_mm

    blend_ratio = min(1.0, max(0.0, position_mm / scale_length_mm))

    # Linear interpolation
    current_radius = base_radius_mm + (end_radius_mm - base_radius_mm) * blend_ratio

    return current_radius
