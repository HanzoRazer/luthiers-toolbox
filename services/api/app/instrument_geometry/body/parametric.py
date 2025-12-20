"""
Parametric Body Geometry

Pure math functions for generating guitar body outlines from dimensional inputs.
Follows the Fortran Rule: all math operations in their own subroutines.

Extracted from: routers/parametric_guitar_router.py (Wave 21 Architecture Cleanup)

Functions:
    generate_body_outline: Generate guitar body outline from dimensions
    cubic_bezier: Cubic bezier curve point calculation
    ellipse_point: Point on ellipse at given angle
"""

from __future__ import annotations

from dataclasses import dataclass
from math import pi, sin, cos
from typing import List, Tuple, Optional


@dataclass
class BodyDimensions:
    """
    Guitar body dimensional inputs for parametric generation.

    All measurements in millimeters.

    Attributes:
        body_length_mm: Total body length
        upper_width_mm: Upper bout width
        lower_width_mm: Lower bout width
        waist_width_mm: Waist width (narrowest point)
        scale_length_mm: Scale length (for reference positioning)
    """
    body_length_mm: float
    upper_width_mm: float
    lower_width_mm: float
    waist_width_mm: float
    scale_length_mm: float = 648.0


def cubic_bezier(
    t: float,
    p0: Tuple[float, float],
    p1: Tuple[float, float],
    p2: Tuple[float, float],
    p3: Tuple[float, float],
) -> Tuple[float, float]:
    """
    Calculate point on cubic bezier curve at parameter t.

    Args:
        t: Parameter value (0.0 to 1.0)
        p0: Start point (x, y)
        p1: First control point
        p2: Second control point
        p3: End point

    Returns:
        (x, y) point on curve at parameter t

    Formula:
        B(t) = (1-t)³P0 + 3(1-t)²tP1 + 3(1-t)t²P2 + t³P3
    """
    p0_x, p0_y = p0
    p1_x, p1_y = p1
    p2_x, p2_y = p2
    p3_x, p3_y = p3

    # Bernstein basis polynomials
    b0 = (1 - t) ** 3
    b1 = 3 * (1 - t) ** 2 * t
    b2 = 3 * (1 - t) * t ** 2
    b3 = t ** 3

    x = b0 * p0_x + b1 * p1_x + b2 * p2_x + b3 * p3_x
    y = b0 * p0_y + b1 * p1_y + b2 * p2_y + b3 * p3_y

    return (x, y)


def ellipse_point(
    center_x: float,
    center_y: float,
    radius_x: float,
    radius_y: float,
    angle_rad: float,
) -> Tuple[float, float]:
    """
    Calculate point on ellipse at given angle.

    Args:
        center_x: Ellipse center X coordinate
        center_y: Ellipse center Y coordinate
        radius_x: Semi-major axis (horizontal radius)
        radius_y: Semi-minor axis (vertical radius)
        angle_rad: Angle in radians (0 = right, π/2 = top)

    Returns:
        (x, y) point on ellipse
    """
    x = center_x + radius_x * cos(angle_rad)
    y = center_y + radius_y * sin(angle_rad)
    return (x, y)


def generate_body_outline(
    dimensions: BodyDimensions,
    guitar_type: str = "Acoustic",
    resolution: int = 48,
) -> List[Tuple[float, float]]:
    """
    Generate parametric body outline from dimensions.

    Uses ellipse approximations and bezier curves for organic guitar shapes.

    Algorithm:
        1. Create upper bout ellipse
        2. Create waist narrowing (bezier curve transition)
        3. Create lower bout ellipse
        4. Blend curves for smooth continuous outline

    Args:
        dimensions: BodyDimensions with all measurements in mm
        guitar_type: "Acoustic", "Electric", "Classical", "Bass"
        resolution: Points per curve segment (higher = smoother)

    Returns:
        List of (x, y) tuples forming closed polyline in mm

    Example:
        >>> dims = BodyDimensions(
        ...     body_length_mm=505,
        ...     upper_width_mm=286,
        ...     lower_width_mm=394,
        ...     waist_width_mm=240,
        ...     scale_length_mm=648
        ... )
        >>> outline = generate_body_outline(dims, "Acoustic", 48)
        >>> len(outline) > 50
        True
    """
    length = dimensions.body_length_mm
    upper_width = dimensions.upper_width_mm
    lower_width = dimensions.lower_width_mm
    waist = dimensions.waist_width_mm

    # Calculate key Y positions along body
    upper_center_y = length * 0.25  # Upper bout center at 25% from top
    waist_y = length * 0.50  # Waist at 50% (midpoint)
    lower_center_y = length * 0.75  # Lower bout center at 75% from top

    # Radii for ellipses
    upper_radius_x = upper_width / 2.0
    upper_radius_y = length * 0.20  # Upper bout height

    lower_radius_x = lower_width / 2.0
    lower_radius_y = length * 0.25  # Lower bout height (slightly larger)

    waist_half = waist / 2.0

    outline: List[Tuple[float, float]] = []

    # === RIGHT SIDE (positive X) ===

    # 1. Upper bout (right side, top to waist)
    quarter_res = resolution // 4
    for i in range(quarter_res):
        t = i / (quarter_res - 1)  # 0.0 to 1.0
        angle = pi / 2 - t * pi / 2  # 90° to 0° (top to side)
        point = ellipse_point(0, upper_center_y, upper_radius_x, upper_radius_y, angle)
        outline.append(point)

    # 2. Waist transition (right side, bezier curve)
    waist_start_y = upper_center_y - upper_radius_y * 0.5
    waist_end_y = waist_y + (lower_center_y - waist_y) * 0.3

    eighth_res = resolution // 8
    for i in range(eighth_res):
        t = i / (eighth_res - 1)
        point = cubic_bezier(
            t,
            p0=(upper_radius_x, waist_start_y),
            p1=(upper_radius_x * 0.9, waist_y - 20),
            p2=(waist_half * 1.1, waist_y + 20),
            p3=(waist_half, waist_end_y),
        )
        outline.append(point)

    # 3. Lower bout (right side, waist to bottom)
    for i in range(quarter_res):
        t = i / (quarter_res - 1)
        angle = t * pi  # 0° to 180° (side to bottom)
        point = ellipse_point(0, lower_center_y, lower_radius_x, lower_radius_y, angle)
        if point[1] < waist_end_y:  # Only add points below waist transition
            continue
        outline.append(point)

    # === LEFT SIDE (negative X, mirror right side) ===

    # 4. Lower bout (left side, bottom to waist)
    for i in range(quarter_res):
        t = i / (quarter_res - 1)
        angle = pi + t * pi  # 180° to 360° (bottom to side)
        point = ellipse_point(0, lower_center_y, lower_radius_x, lower_radius_y, angle)
        if point[1] < waist_end_y:
            continue
        outline.append(point)

    # 5. Waist transition (left side, bezier curve)
    for i in range(eighth_res):
        t = i / (eighth_res - 1)
        point = cubic_bezier(
            t,
            p0=(-waist_half, waist_end_y),
            p1=(-waist_half * 1.1, waist_y + 20),
            p2=(-upper_radius_x * 0.9, waist_y - 20),
            p3=(-upper_radius_x, waist_start_y),
        )
        outline.append(point)

    # 6. Upper bout (left side, waist to top)
    for i in range(quarter_res):
        t = i / (quarter_res - 1)
        angle = pi + t * pi / 2  # 180° to 270° (side to top)
        point = ellipse_point(0, upper_center_y, upper_radius_x, upper_radius_y, angle)
        outline.append(point)

    # Close the loop
    if outline[0] != outline[-1]:
        outline.append(outline[0])

    return outline


def compute_bounding_box(
    outline: List[Tuple[float, float]]
) -> dict:
    """
    Compute bounding box for an outline.

    Args:
        outline: List of (x, y) points

    Returns:
        Dict with min_x, max_x, min_y, max_y, width, height
    """
    if not outline:
        return {"min_x": 0, "max_x": 0, "min_y": 0, "max_y": 0, "width": 0, "height": 0}

    xs = [p[0] for p in outline]
    ys = [p[1] for p in outline]

    return {
        "min_x": min(xs),
        "max_x": max(xs),
        "min_y": min(ys),
        "max_y": max(ys),
        "width": max(xs) - min(xs),
        "height": max(ys) - min(ys),
    }
