"""
Biarc and Fillet Mathematics

Pure math functions for arc fitting, corner filleting, and G-code geometry.
Follows the Fortran Rule: all math operations in their own subroutines.

Extracted from: routers/cam_post_v155_router.py (Wave 21 Architecture Cleanup)

Functions:
    vec_dot: Vector dot product
    vec_len: Vector length
    vec_normalize: Normalize vector to unit length
    fillet_between: Calculate fillet arc between three points
    angle_to_point: Angle from center to point
    arc_center_from_radius: Calculate arc center from endpoints and radius
"""

from __future__ import annotations

from math import hypot, acos, tan, sin, cos, atan2, sqrt, pi
from typing import Tuple, Optional

Point = Tuple[float, float]


def vec_dot(ax: float, ay: float, bx: float, by: float) -> float:
    """
    Compute dot product of two 2D vectors.

    Args:
        ax, ay: First vector components
        bx, by: Second vector components

    Returns:
        Scalar dot product (ax*bx + ay*by)
    """
    return ax * bx + ay * by


def vec_len(x: float, y: float) -> float:
    """
    Compute length (magnitude) of 2D vector.

    Args:
        x, y: Vector components

    Returns:
        Vector length: sqrt(x² + y²)
    """
    return hypot(x, y)


def vec_normalize(x: float, y: float) -> Tuple[float, float]:
    """
    Normalize vector to unit length.

    Args:
        x, y: Vector components

    Returns:
        (ux, uy) unit vector, or (0, 0) if zero-length
    """
    length = hypot(x, y)
    if length < 1e-12:
        return (0.0, 0.0)
    return (x / length, y / length)


def angle_to_point(cx: float, cy: float, p: Point) -> float:
    """
    Calculate angle from center to point.

    Args:
        cx, cy: Center coordinates
        p: Target point (x, y)

    Returns:
        Angle in radians from center to point
    """
    return atan2(p[1] - cy, p[0] - cx)


def fillet_between(
    a: Point,
    b: Point,
    c: Point,
    radius: float,
) -> Optional[Tuple[Point, Point, float, float, str]]:
    """
    Calculate fillet arc between three points.

    Given three consecutive points (a, b, c) on a polyline, compute the
    fillet arc parameters to smooth the corner at point b.

    Args:
        a: First point (preceding corner)
        b: Corner point to fillet
        c: Third point (following corner)
        radius: Desired fillet radius

    Returns:
        Tuple of (p1, p2, cx, cy, direction) where:
        - p1: Trim point on segment ab (start of arc)
        - p2: Trim point on segment bc (end of arc)
        - cx, cy: Arc center coordinates
        - direction: "CW" or "CCW" (arc direction)

        Returns None if fillet cannot be computed (collinear points,
        segments too short, etc.)

    Example:
        >>> a, b, c = (0, 0), (10, 0), (10, 10)  # Right angle corner
        >>> result = fillet_between(a, b, c, 2.0)
        >>> p1, p2, cx, cy, direction = result
        >>> print(f"Arc from {p1} to {p2}, center ({cx:.2f}, {cy:.2f}), {direction}")
    """
    x1, y1 = a
    x2, y2 = b
    x3, y3 = c

    # Vectors from corner B to neighbors A and C
    v1x, v1y = x1 - x2, y1 - y2  # BA
    v2x, v2y = x3 - x2, y3 - y2  # BC

    L1 = vec_len(v1x, v1y)
    L2 = vec_len(v2x, v2y)

    if L1 < 1e-9 or L2 < 1e-9:
        return None

    # Normalize vectors
    v1x /= L1
    v1y /= L1
    v2x /= L2
    v2y /= L2

    # Interior angle at B: angle between -v1 (toward A from B) and v2 (toward C from B)
    cos_theta = vec_dot(-v1x, -v1y, v2x, v2y)
    cos_theta = max(-1.0, min(1.0, cos_theta))  # Clamp for numerical stability
    theta = acos(cos_theta)

    # Check for degenerate cases (collinear or near-collinear)
    if theta < 1e-6 or theta > pi - 1e-6:
        return None

    # Distance from corner to tangent points along each segment
    t = radius * tan(theta / 2.0)

    # Check if segments are long enough
    if t > L1 - 1e-6 or t > L2 - 1e-6:
        return None

    # Tangent points
    p1 = (x2 + (-v1x) * t, y2 + (-v1y) * t)  # On segment BA
    p2 = (x2 + v2x * t, y2 + v2y * t)  # On segment BC

    # Bisector direction (points toward arc center)
    bisx = -v1x + v2x
    bisy = -v1y + v2y
    bl = vec_len(bisx, bisy)

    if bl < 1e-9:
        return None

    bisx /= bl
    bisy /= bl

    # Distance from corner to arc center along bisector
    h = radius / sin(theta / 2.0)

    # Arc center
    cx = x2 + bisx * h
    cy = y2 + bisy * h

    # Determine arc direction (CW or CCW) using cross product
    u1x, u1y = p1[0] - cx, p1[1] - cy
    u2x, u2y = p2[0] - cx, p2[1] - cy
    cross = u1x * u2y - u1y * u2x
    direction = "CCW" if cross > 0 else "CW"

    return (p1, p2, cx, cy, direction)


def arc_center_from_radius(
    start: Point,
    end: Point,
    radius: float,
    clockwise: bool = True,
) -> Tuple[float, float]:
    """
    Calculate arc center from endpoints and radius.

    Given two points and a radius, compute the center of the arc.
    Assumes minor arc (sweep < 180°).

    Args:
        start: Arc start point (x, y)
        end: Arc end point (x, y)
        radius: Arc radius
        clockwise: True for CW arc, False for CCW

    Returns:
        (cx, cy) arc center coordinates

    Note:
        For a given start, end, and radius, there are two possible centers
        (one on each side of the chord). The clockwise parameter selects
        which one to return.
    """
    mx = (start[0] + end[0]) / 2
    my = (start[1] + end[1]) / 2

    dx = end[0] - start[0]
    dy = end[1] - start[1]
    d = hypot(dx, dy)

    if d < 1e-12:
        return (mx, my)

    # Height of center above chord midpoint
    h_sq = radius * radius - (d / 2) * (d / 2)
    h = sqrt(max(0.0, h_sq))

    # Normal to chord
    nx, ny = -dy / d, dx / d

    # Select side based on direction
    sign = -1.0 if clockwise else 1.0
    cx = mx + sign * h * nx
    cy = my + sign * h * ny

    return (cx, cy)


def arc_tessellate(
    start: Point,
    end: Point,
    cx: float,
    cy: float,
    radius: float,
    clockwise: bool = True,
    max_chord_error: float = 0.5,
) -> list[Point]:
    """
    Tessellate arc into line segments for preview.

    Args:
        start: Arc start point
        end: Arc end point
        cx, cy: Arc center
        radius: Arc radius
        clockwise: True for CW, False for CCW
        max_chord_error: Maximum deviation from arc (mm)

    Returns:
        List of points along the arc (excluding start, including end)
    """
    a1 = atan2(start[1] - cy, start[0] - cx)
    a2 = atan2(end[1] - cy, end[0] - cx)

    # Adjust angle range based on direction
    if clockwise:
        while a2 > a1:
            a2 -= 2 * pi
    else:
        while a2 < a1:
            a2 += 2 * pi

    # Calculate number of steps
    sweep = abs(a2 - a1)
    steps = max(6, int(sweep * radius / max_chord_error))

    points = []
    for t in range(1, steps + 1):
        ang = a1 + (a2 - a1) * t / steps
        qx = cx + radius * cos(ang)
        qy = cy + radius * sin(ang)
        points.append((qx, qy))

    return points
