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
