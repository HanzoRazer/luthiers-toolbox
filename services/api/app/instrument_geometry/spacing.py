"""
Instrument Geometry: String Spacing Utilities

Wave 17 - Instrument Geometry Integration

Reusable utilities for calculating string positions at nut and bridge.

Supports three spacing strategies:
1. Centered spacing: Positions centered at 0.0 (bridge saddles)
2. Edge-margin spacing: Positions relative to board edges (nut layouts)
3. E-to-E spacing: Convenience wrapper for bridge spans

Usage:
    from instrument_geometry.spacing import compute_centered_spacing_mm
    
    # 6-string bridge with 52mm E-to-E
    result = compute_centered_spacing_mm(num_points=6, total_span_mm=52.0)
    # result.positions_mm = [-26.0, -15.6, -5.2, 5.2, 15.6, 26.0]
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class SpacingResult:
    """
    Generic spacing result for N points along a line.

    Attributes:
        positions_mm: List of positions in mm, relative to some origin
        
    Coordinate Conventions:
        - For centered spacing: 0.0 is centerline
            - Negative = bass side (low E)
            - Positive = treble side (high E)
            (Assumes right-handed guitar with headstock left, body right)
            
        - For nut/bridge spacing: origin convention is caller-defined
            (e.g. 0.0 at bass edge, or at centerline, etc.)
    """
    positions_mm: List[float]


def compute_centered_spacing_mm(
    num_points: int,
    total_span_mm: float,
) -> SpacingResult:
    """
    Evenly space N points across a span, centered at 0.0.

    This is useful at the bridge where you know the total E-to-E spread
    and want positions around a mechanical centerline.

    Args:
        num_points: Number of strings/points
        total_span_mm: Total span from bass-most to treble-most point

    Returns:
        SpacingResult with positions centered at 0.0

    Example:
        >>> result = compute_centered_spacing_mm(num_points=6, total_span_mm=52.0)
        >>> result.positions_mm[0]  # Low E
        -26.0
        >>> result.positions_mm[-1]  # High E
        26.0
    """
    if num_points <= 0:
        raise ValueError("num_points must be positive")
    if total_span_mm < 0.0:
        raise ValueError("total_span_mm must be non-negative")

    if num_points == 1:
        return SpacingResult(positions_mm=[0.0])

    # Distance between adjacent strings
    step = total_span_mm / float(num_points - 1)

    # Start at -span/2 and step up
    start = -total_span_mm / 2.0
    positions = [start + i * step for i in range(num_points)]
    return SpacingResult(positions_mm=positions)


def compute_edge_margin_spacing_mm(
    num_strings: int,
    nut_width_mm: float,
    bass_edge_margin_mm: float,
    treble_edge_margin_mm: float,
) -> SpacingResult:
    """
    Compute string positions across the nut with specified edge margins.

    Coordinate convention:
        0.0 = bass side edge of the nut
        nut_width_mm = treble side edge

    The positions returned are between those edges, respecting the margins.

    This matches typical "edge margin" style nut layouts where you
    want slightly more wood outside the low E vs high E.

    Args:
        num_strings: Number of strings
        nut_width_mm: Overall nut width
        bass_edge_margin_mm: Distance from bass edge to low E string
        treble_edge_margin_mm: Distance from treble edge to high E string

    Returns:
        SpacingResult with positions relative to bass edge (0.0)

    Raises:
        ValueError: If margins exceed nut width

    Example:
        >>> result = compute_edge_margin_spacing_mm(
        ...     num_strings=6,
        ...     nut_width_mm=42.0,
        ...     bass_edge_margin_mm=3.0,
        ...     treble_edge_margin_mm=2.5
        ... )
        >>> result.positions_mm[0]  # Low E
        3.0
        >>> result.positions_mm[-1]  # High E
        39.5
    """
    if num_strings <= 0:
        raise ValueError("num_strings must be positive")

    usable_span = nut_width_mm - bass_edge_margin_mm - treble_edge_margin_mm
    if usable_span <= 0.0:
        raise ValueError("Edge margins exceed nut width")

    if num_strings == 1:
        return SpacingResult(
            positions_mm=[bass_edge_margin_mm + usable_span / 2.0]
        )

    step = usable_span / float(num_strings - 1)
    positions = [
        bass_edge_margin_mm + i * step for i in range(num_strings)
    ]
    return SpacingResult(positions_mm=positions)


def compute_bridge_spacing_from_e_to_e_mm(
    num_strings: int,
    e_to_e_mm: float,
    center_at_zero: bool = True,
) -> SpacingResult:
    """
    Convenience wrapper for a bridge where you know the E-to-E span.

    Args:
        num_strings: Number of strings
        e_to_e_mm: Distance between outer strings (E-to-E)
        center_at_zero: If True, returns positions centered at 0.0.
                       If False, returns 0.0 at bass edge and e_to_e_mm at treble edge.

    Returns:
        SpacingResult

    Example (centered):
        >>> result = compute_bridge_spacing_from_e_to_e_mm(
        ...     num_strings=6,
        ...     e_to_e_mm=52.0,
        ...     center_at_zero=True
        ... )
        >>> result.positions_mm[0]  # Low E
        -26.0
        >>> result.positions_mm[-1]  # High E
        26.0

    Example (edge-based):
        >>> result = compute_bridge_spacing_from_e_to_e_mm(
        ...     num_strings=6,
        ...     e_to_e_mm=52.0,
        ...     center_at_zero=False
        ... )
        >>> result.positions_mm[0]  # Low E
        0.0
        >>> result.positions_mm[-1]  # High E
        52.0
    """
    if num_strings <= 0:
        raise ValueError("num_strings must be positive")

    if center_at_zero:
        return compute_centered_spacing_mm(
            num_points=num_strings,
            total_span_mm=e_to_e_mm,
        )

    # Edge-based coordinates: 0 at bass, e_to_e at treble
    if num_strings == 1:
        return SpacingResult(positions_mm=[e_to_e_mm / 2.0])

    step = e_to_e_mm / float(num_strings - 1)
    positions = [i * step for i in range(num_strings)]
    return SpacingResult(positions_mm=positions)
