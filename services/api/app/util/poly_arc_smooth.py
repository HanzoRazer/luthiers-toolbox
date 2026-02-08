"""Polygon arc-smoothing engine.

Extracted from poly_offset_spiral.py (WP-3) for god-object decomposition.
Phase 3 arc smoothing: corner detection and fillet insertion.
"""

from __future__ import annotations

import math
from typing import List, Sequence, Tuple

# Type aliases (same as parent module)
Point = Tuple[float, float]
Path = List[Point]


def _normalize(vx: float, vy: float) -> Tuple[float, float]:
    mag = math.hypot(vx, vy)
    if mag < 1e-9:
        return 0.0, 0.0
    return vx / mag, vy / mag


def _distance(a: Point, b: Point) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _corner_angle(prev: Point, curr: Point, nxt: Point) -> float:
    """Return interior angle in radians at curr."""
    ax, ay = prev[0] - curr[0], prev[1] - curr[1]
    bx, by = nxt[0] - curr[0], nxt[1] - curr[1]

    ax, ay = _normalize(ax, ay)
    bx, by = _normalize(bx, by)

    dot = ax * bx + ay * by
    dot = max(-1.0, min(1.0, dot))
    return math.acos(dot)


def _fillet(
    prev: Point,
    curr: Point,
    nxt: Point,
    radius: float,
    segments: int = 5,
) -> Path:
    """
    Insert a circular fillet between prev -> curr -> nxt.
    Returns small polyline approximating the arc.
    """
    # Direction vectors
    vx1, vy1 = prev[0] - curr[0], prev[1] - curr[1]
    vx2, vy2 = nxt[0] - curr[0], nxt[1] - curr[1]
    nx1, ny1 = _normalize(vx1, vy1)
    nx2, ny2 = _normalize(vx2, vy2)

    # Points offset from curr along each direction
    p1 = (curr[0] + nx1 * radius, curr[1] + ny1 * radius)
    p2 = (curr[0] + nx2 * radius, curr[1] + ny2 * radius)

    # Mid-angle interpolation for arc (simple circular transition)
    angle1 = math.atan2(nx1 * -1, ny1 * -1)  # rotate into perpendicular space
    angle2 = math.atan2(nx2 * -1, ny2 * -1)

    # Normalize sweep
    # We want smallest positive sweep
    while angle2 < angle1:
        angle2 += 2 * math.pi

    arc = []
    for i in range(segments + 1):
        t = i / segments
        ang = angle1 + (angle2 - angle1) * t
        x = curr[0] + radius * math.cos(ang)
        y = curr[1] + radius * math.sin(ang)
        arc.append((x, y))
    return arc


def smooth_with_arcs(
    path: Sequence[Point],
    corner_radius_min: float,
    corner_tol_mm: float,
) -> Path:
    """Phase 3 arc smoothing: scan corners of `path` and insert small circular"""
    if corner_radius_min is None:
        return list(path)
    if corner_tol_mm is None:
        corner_tol_mm = corner_radius_min * 0.5

    pts = list(path)
    n = len(pts)
    if n < 3:
        return pts

    out: Path = [pts[0]]

    for i in range(1, n - 1):
        prev = pts[i - 1]
        curr = pts[i]
        nxt = pts[i + 1]

        # Corner angle
        angle = _corner_angle(prev, curr, nxt)

        # If nearly straight -> skip smoothing
        if abs(angle - math.pi) < 0.1:
            out.append(curr)
            continue

        # Determine allowable radius based on adjacent segments
        d1 = _distance(prev, curr)
        d2 = _distance(curr, nxt)
        max_r = min(d1, d2) * 0.3  # keep reasonable
        r = min(max_r, corner_radius_min)

        if r < corner_radius_min * 0.5:
            # Too small to matter
            out.append(curr)
            continue

        # Insert fillet
        arc = _fillet(prev, curr, nxt, r, segments=5)
        # Replace the corner by the arc (but avoid duplicating curr)
        out.extend(arc)

    out.append(pts[-1])
    return out
