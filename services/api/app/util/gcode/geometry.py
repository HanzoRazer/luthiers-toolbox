"""
G-code Geometry Helpers

Arc calculations, distance functions, and interpolation for G2/G3 arcs.
"""
from __future__ import annotations

import math
from typing import List, Optional, Tuple


def dist2d(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    """Calculate 2D Euclidean distance."""
    return math.hypot(b[0] - a[0], b[1] - a[1])


def dist3d(a: Tuple[float, float, float], b: Tuple[float, float, float]) -> float:
    """Calculate 3D Euclidean distance."""
    return math.dist(a, b)


def arc_center_from_ijk(p: Tuple[float, float], i: float, j: float) -> Tuple[float, float]:
    """Calculate arc center from current point and IJ offsets."""
    return (p[0] + i, p[1] + j)


def arc_len(
    center: Tuple[float, float],
    a: Tuple[float, float],
    b: Tuple[float, float],
    cw: bool,
) -> float:
    """
    Calculate arc length from point a to point b around center.

    Args:
        center: Arc center point (cx, cy)
        a: Start point (x1, y1)
        b: End point (x2, y2)
        cw: True for clockwise (G2), False for counterclockwise (G3)

    Returns:
        Arc length in current units
    """
    ax, ay = a[0] - center[0], a[1] - center[1]
    bx, by = b[0] - center[0], b[1] - center[1]

    ra = math.atan2(ay, ax)
    rb = math.atan2(by, bx)
    d = rb - ra

    # Check for full circle (start==end within tolerance)
    dist_start_to_end = math.hypot(b[0] - a[0], b[1] - a[1])
    r = math.hypot(ax, ay)

    if dist_start_to_end < 1e-6 and r > 1e-6:
        # Full circle: return full circumference
        return 2 * math.pi * r

    # Adjust angle based on direction
    if cw:
        if d > 0:
            d -= 2 * math.pi
    else:
        if d < 0:
            d += 2 * math.pi

    return abs(d) * r


def arc_center_from_r(
    sx: float, sy: float,
    ex: float, ey: float,
    r: float,
    cw: bool,
) -> Optional[Tuple[float, float]]:
    """
    Compute arc center point from R-mode G2/G3.

    Returns (cx, cy) center, or None if radius is geometrically invalid.
    """
    dx, dy = ex - sx, ey - sy
    chord = math.hypot(dx, dy)

    if chord < 1e-6:
        # R-notation cannot legally express a full circle (start == end gives an
        # ambiguous/arbitrary center). Reject so the caller can fall back rather
        # than drawing a bogus circle in an arbitrary location. (finding Y3)
        return None

    half_chord = chord / 2.0
    if abs(r) < half_chord - 1e-6:
        return None  # Radius too small to bridge the chord

    h = math.sqrt(max(0.0, r * r - half_chord * half_chord))

    # Perpendicular unit vector (90° CCW from chord)
    ux, uy = -dy / chord, dx / chord
    mx, my = (sx + ex) / 2.0, (sy + ey) / 2.0

    c1 = (mx + h * ux, my + h * uy)
    c2 = (mx - h * ux, my - h * uy)

    def _sweep_for(c: Tuple[float, float]) -> float:
        a_start = math.atan2(sy - c[1], sx - c[0])
        a_end = math.atan2(ey - c[1], ex - c[0])
        s = a_end - a_start
        if cw:
            if s > 0:
                s -= 2 * math.pi
        else:
            if s < 0:
                s += 2 * math.pi
        return s

    s1 = _sweep_for(c1)
    want_minor = r > 0
    c1_is_minor = abs(s1) <= math.pi + 1e-6

    return c1 if (want_minor == c1_is_minor) else c2


def interpolate_arc_points(
    from_pos: Tuple[float, float, float],
    to_pos: Tuple[float, float, float],
    center: Tuple[float, float],
    cw: bool,
    arc_resolution_deg: float = 5.0,
) -> List[Tuple[float, float, float]]:
    """
    Interpolate an XY arc into a list of 3D waypoints.
    Z is linearly interpolated from from_pos[2] to to_pos[2] across the sweep.
    """
    sx, sy, sz = from_pos
    ex, ey, ez = to_pos
    cx, cy = center

    r = math.hypot(sx - cx, sy - cy)
    if r < 1e-6:
        return [to_pos]

    a_start = math.atan2(sy - cy, sx - cx)
    a_end = math.atan2(ey - cy, ex - cx)

    is_full_circle = math.hypot(ex - sx, ey - sy) < 1e-6 and r > 1e-6

    if is_full_circle:
        sweep = -(2 * math.pi) if cw else (2 * math.pi)
    else:
        sweep = a_end - a_start
        if cw:
            if sweep > 0:
                sweep -= 2 * math.pi
        else:
            if sweep < 0:
                sweep += 2 * math.pi

    num_steps = max(1, int(abs(math.degrees(sweep)) / max(0.1, arc_resolution_deg)))

    points: List[Tuple[float, float, float]] = []
    for k in range(1, num_steps + 1):
        t = k / num_steps
        angle = a_start + sweep * t
        wx = cx + r * math.cos(angle)
        wy = cy + r * math.sin(angle)
        wz = sz + (ez - sz) * t
        points.append((wx, wy, wz))

    return points


# Map G17/G18/G19 to the two in-plane axis indices (a, b) and the linear
# (helical / out-of-plane) axis index. X=0, Y=1, Z=2.
_PLANE_AXES = {
    17: (0, 1, 2),  # XY plane, Z is the helical axis
    18: (0, 2, 1),  # XZ plane, Y is the helical axis
    19: (1, 2, 0),  # YZ plane, X is the helical axis
}


def interpolate_arc(
    from_pos: Tuple[float, float, float],
    to_pos: Tuple[float, float, float],
    center2: Tuple[float, float],
    cw: bool,
    plane: int = 17,
    arc_resolution_deg: float = 5.0,
) -> List[Tuple[float, float, float]]:
    """Interpolate a G2/G3 arc in the active plane (G17/G18/G19) into 3D waypoints.

    Generalises :func:`interpolate_arc_points` (which is XY-only) so arcs in the
    XZ (G18) and YZ (G19) planes are supported instead of silently dropped.
    (finding Y2)

    Args:
        from_pos / to_pos: 3D start/end points.
        center2: arc center expressed in the plane's two axes (a, b).
        cw: True for G2 (clockwise), False for G3.
        plane: 17, 18, or 19. Falls back to 17 for unknown values.
        arc_resolution_deg: angular step for sub-segments.

    Returns:
        List of 3D waypoints from the first step through the endpoint. The
        out-of-plane axis is linearly interpolated across the sweep (helical).
    """
    a, b, lin = _PLANE_AXES.get(plane, _PLANE_AXES[17])

    sa, sb, slin = from_pos[a], from_pos[b], from_pos[lin]
    ea, eb, elin = to_pos[a], to_pos[b], to_pos[lin]
    ca, cb = center2

    r = math.hypot(sa - ca, sb - cb)
    if r < 1e-6:
        return [tuple(to_pos)]

    a_start = math.atan2(sb - cb, sa - ca)
    a_end = math.atan2(eb - cb, ea - ca)

    is_full_circle = math.hypot(ea - sa, eb - sb) < 1e-6 and r > 1e-6
    if is_full_circle:
        sweep = -(2 * math.pi) if cw else (2 * math.pi)
    else:
        sweep = a_end - a_start
        if cw:
            if sweep > 0:
                sweep -= 2 * math.pi
        else:
            if sweep < 0:
                sweep += 2 * math.pi

    num_steps = max(1, int(abs(math.degrees(sweep)) / max(0.1, arc_resolution_deg)))

    points: List[Tuple[float, float, float]] = []
    for k in range(1, num_steps + 1):
        t = k / num_steps
        angle = a_start + sweep * t
        pa = ca + r * math.cos(angle)
        pb = cb + r * math.sin(angle)
        plin = slin + (elin - slin) * t
        p = [0.0, 0.0, 0.0]
        p[a] = pa
        p[b] = pb
        p[lin] = plin
        points.append((p[0], p[1], p[2]))

    return points
