"""
Arc and Circle Geometry Utilities

Pure math functions for arc tessellation, circle generation, and related operations.
Follows the Fortran Rule: all math operations in their own subroutines.

Extracted from multiple routers (Wave 21 Architecture Cleanup):
- adaptive_router.py
- geometry_router.py
- art_studio_rosette_router.py
- sim_validate.py

Functions:
    generate_circle_points: Generate points around a circle
    tessellate_arc: Convert arc to line segments
    arc_center_from_endpoints: Calculate arc center from start/end and radius
    arc_length: Calculate arc length
    arc_sweep: Calculate signed sweep angle
    nearest_point_distance: Find minimum distance to point cloud
"""

from __future__ import annotations

from math import pi, sin, cos, atan2, hypot, sqrt, radians
from typing import List, Tuple, Optional


Point = Tuple[float, float]


def generate_circle_points(
    radius: float,
    segments: int = 64,
    center: Point = (0.0, 0.0),
    closed: bool = True,
) -> List[Point]:
    """
    Generate points around a circle.

    Args:
        radius: Circle radius
        segments: Number of points (excluding closing point)
        center: Center point (cx, cy)
        closed: If True, append first point at end to close loop

    Returns:
        List of (x, y) points on the circle

    Example:
        >>> pts = generate_circle_points(10.0, 8)
        >>> len(pts)
        9  # 8 segments + 1 closing point
    """
    cx, cy = center
    points = []

    for i in range(segments):
        angle = (2.0 * pi * i) / segments
        x = cx + radius * cos(angle)
        y = cy + radius * sin(angle)
        points.append((x, y))

    if closed and points:
        points.append(points[0])

    return points


def tessellate_arc(
    cx: float,
    cy: float,
    radius: float,
    start_deg: float,
    end_deg: float,
    clockwise: bool = False,
    min_segments: int = 6,
    chord_tolerance: float = 1.0,
) -> List[Point]:
    """
    Convert arc to line segments (tessellation).

    Args:
        cx, cy: Arc center
        radius: Arc radius
        start_deg: Start angle in degrees
        end_deg: End angle in degrees
        clockwise: True for CW arc, False for CCW
        min_segments: Minimum number of segments
        chord_tolerance: Maximum chord deviation in mm

    Returns:
        List of (x, y) points along the arc

    Example:
        >>> pts = tessellate_arc(0, 0, 10, 0, 90, clockwise=False)
        >>> len(pts) >= 6
        True
    """
    a0 = radians(start_deg)
    a1 = radians(end_deg)

    # Normalize angle range based on direction
    if clockwise:
        while a1 > a0:
            a1 -= 2 * pi
    else:
        while a1 < a0:
            a1 += 2 * pi

    # Calculate number of segments based on arc length and chord tolerance
    sweep = abs(a1 - a0)
    arc_len = sweep * abs(radius)
    n = max(min_segments, int(arc_len / chord_tolerance))

    points = []
    for k in range(n + 1):
        t = k / n
        angle = a0 + (a1 - a0) * t
        x = cx + radius * cos(angle)
        y = cy + radius * sin(angle)
        points.append((x, y))

    return points


def tessellate_arc_radians(
    cx: float,
    cy: float,
    radius: float,
    start_rad: float,
    end_rad: float,
    clockwise: bool = False,
    steps: int = 64,
) -> List[Point]:
    """
    Convert arc to line segments using radian angles.

    Args:
        cx, cy: Arc center
        radius: Arc radius
        start_rad: Start angle in radians
        end_rad: End angle in radians
        clockwise: True for CW, False for CCW
        steps: Number of line segments

    Returns:
        List of (x, y) points along the arc
    """
    a0 = start_rad
    a1 = end_rad

    if clockwise:
        while a1 > a0:
            a1 -= 2 * pi
    else:
        while a1 < a0:
            a1 += 2 * pi

    points = []
    for k in range(steps + 1):
        t = k / steps
        angle = a0 + (a1 - a0) * t
        x = cx + radius * cos(angle)
        y = cy + radius * sin(angle)
        points.append((x, y))

    return points


def arc_center_from_endpoints(
    sx: float,
    sy: float,
    ex: float,
    ey: float,
    radius: float,
    clockwise: bool = True,
) -> Point:
    """
    Calculate arc center from start/end points and radius.

    Given two points and a radius, finds the center that produces
    the desired arc direction.

    Args:
        sx, sy: Start point
        ex, ey: End point
        radius: Arc radius
        clockwise: True for CW arc, False for CCW

    Returns:
        (cx, cy) arc center coordinates

    Example:
        >>> cx, cy = arc_center_from_endpoints(0, 0, 10, 0, 5, clockwise=True)
        >>> print(f"Center: ({cx:.1f}, {cy:.1f})")
    """
    dx = ex - sx
    dy = ey - sy
    d = hypot(dx, dy)

    if d < 1e-9:
        return (sx, sy + radius)

    # Distance from midpoint to center
    h_sq = radius * radius - (d * d) / 4.0
    h = sqrt(max(0.0, h_sq))

    # Midpoint
    mx = (sx + ex) / 2.0
    my = (sy + ey) / 2.0

    # Unit perpendicular vector
    ux, uy = -dy / d, dx / d

    # Two candidate centers
    c1 = (mx + ux * h, my + uy * h)
    c2 = (mx - ux * h, my - uy * h)

    # Select based on direction
    sweep1 = arc_signed_sweep(c1[0], c1[1], sx, sy, ex, ey)
    if (clockwise and sweep1 > 0) or (not clockwise and sweep1 < 0):
        return c2
    return c1


def arc_signed_sweep(
    cx: float,
    cy: float,
    sx: float,
    sy: float,
    ex: float,
    ey: float,
) -> float:
    """
    Calculate signed sweep angle of arc.

    Args:
        cx, cy: Arc center
        sx, sy: Start point
        ex, ey: End point

    Returns:
        Signed sweep angle in radians (-π to π)
    """
    a0 = atan2(sy - cy, sx - cx)
    a1 = atan2(ey - cy, ex - cx)
    return ((a1 - a0 + pi) % (2 * pi)) - pi


def arc_length(
    cx: float,
    cy: float,
    sx: float,
    sy: float,
    ex: float,
    ey: float,
    clockwise: bool = True,
) -> float:
    """
    Calculate arc length.

    Args:
        cx, cy: Arc center
        sx, sy: Start point
        ex, ey: End point
        clockwise: True for CW, False for CCW

    Returns:
        Arc length in same units as input coordinates

    Example:
        >>> # Quarter circle with radius 10
        >>> length = arc_length(0, 0, 10, 0, 0, 10, clockwise=False)
        >>> abs(length - 15.708) < 0.01  # π * 10 / 2
        True
    """
    a0 = atan2(sy - cy, sx - cx)
    a1 = atan2(ey - cy, ex - cx)
    radius = hypot(sx - cx, sy - cy)

    da = a1 - a0
    if clockwise:
        while da > 0:
            da -= 2 * pi
    else:
        while da < 0:
            da += 2 * pi

    return abs(da) * abs(radius)


def nearest_point_distance(
    point: Point,
    cloud: List[Point],
) -> float:
    """
    Find minimum distance from point to a cloud of points.

    Args:
        point: Query point (x, y)
        cloud: List of points to search

    Returns:
        Minimum Euclidean distance to any point in cloud

    Example:
        >>> cloud = [(0, 0), (10, 0), (5, 5)]
        >>> nearest_point_distance((0, 1), cloud)
        1.0
    """
    px, py = point
    min_dist = float('inf')

    for qx, qy in cloud:
        d = hypot(px - qx, py - qy)
        if d < min_dist:
            min_dist = d

    return min_dist


def circle_circumference(radius: float) -> float:
    """
    Calculate circle circumference.

    Args:
        radius: Circle radius

    Returns:
        Circumference (2 * π * r)
    """
    return 2.0 * pi * radius


def arc_length_from_angle(radius: float, angle_deg: float) -> float:
    """
    Calculate arc length from radius and angle.

    Args:
        radius: Arc radius
        angle_deg: Arc sweep angle in degrees

    Returns:
        Arc length in same units as radius
    """
    return 2.0 * pi * radius * (angle_deg / 360.0)


def trapezoidal_motion_time(
    distance_mm: float,
    feed_mm_min: float,
    accel_mm_s2: float,
) -> float:
    """
    Calculate motion time using trapezoidal velocity profile.

    Args:
        distance_mm: Travel distance in mm
        feed_mm_min: Target feed rate in mm/min
        accel_mm_s2: Acceleration in mm/s²

    Returns:
        Total motion time in seconds

    Note:
        Uses triangular profile if distance too short for full accel/decel.
    """
    v = max(feed_mm_min, 1e-6) / 60.0  # mm/s
    a = max(accel_mm_s2, 1e-6)

    t_acc = v / a
    d_acc = 0.5 * a * t_acc * t_acc

    if 2 * d_acc >= distance_mm:
        # Triangular profile (can't reach full speed)
        return 2.0 * sqrt(distance_mm / a)

    # Trapezoidal profile
    cruise = distance_mm - 2 * d_acc
    return 2 * t_acc + cruise / v
