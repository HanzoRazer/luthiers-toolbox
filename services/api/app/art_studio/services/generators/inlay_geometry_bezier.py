"""
Inlay Geometry Bézier & Spline Math

De Casteljau cubic/quadratic Bézier subdivision and Catmull-Rom spline
interpolation for smooth curve generation.

All coordinates in mm.
"""
from __future__ import annotations

import math
from typing import List

from .inlay_geometry_core import Polyline, Pt


def subdivide_cubic(
    p0: Pt, p1: Pt, p2: Pt, p3: Pt,
    tol: float = 0.5,
    _result: Polyline | None = None,
) -> Polyline:
    """Adaptive cubic Bézier subdivision using De Casteljau.

    Returns a list of points approximating the curve within *tol* mm.
    """
    if _result is None:
        _result = [p0]

    # Flatness test: perpendicular distance of control points to baseline
    dx, dy = p3[0] - p0[0], p3[1] - p0[1]
    base_len = math.hypot(dx, dy) or 1e-12
    d1 = abs((p1[0] - p0[0]) * dy - (p1[1] - p0[1]) * dx) / base_len
    d2 = abs((p2[0] - p0[0]) * dy - (p2[1] - p0[1]) * dx) / base_len

    if d1 + d2 <= tol:
        _result.append(p3)
        return _result

    # De Casteljau split at t=0.5
    m01 = ((p0[0] + p1[0]) * 0.5, (p0[1] + p1[1]) * 0.5)
    m12 = ((p1[0] + p2[0]) * 0.5, (p1[1] + p2[1]) * 0.5)
    m23 = ((p2[0] + p3[0]) * 0.5, (p2[1] + p3[1]) * 0.5)
    m012 = ((m01[0] + m12[0]) * 0.5, (m01[1] + m12[1]) * 0.5)
    m123 = ((m12[0] + m23[0]) * 0.5, (m12[1] + m23[1]) * 0.5)
    mid = ((m012[0] + m123[0]) * 0.5, (m012[1] + m123[1]) * 0.5)

    subdivide_cubic(p0, m01, m012, mid, tol, _result)
    subdivide_cubic(mid, m123, m23, p3, tol, _result)
    return _result


def subdivide_quadratic(
    p0: Pt, p1: Pt, p2: Pt, tol: float = 0.5,
) -> Polyline:
    """Adaptive quadratic Bézier subdivision (Q → C elevation)."""
    # Elevate to cubic: C1 = Q0 + 2/3*(Q1-Q0), C2 = Q2 + 2/3*(Q1-Q2)
    c1 = (p0[0] + 2 / 3 * (p1[0] - p0[0]), p0[1] + 2 / 3 * (p1[1] - p0[1]))
    c2 = (p2[0] + 2 / 3 * (p1[0] - p2[0]), p2[1] + 2 / 3 * (p1[1] - p2[1]))
    return subdivide_cubic(p0, c1, c2, p2, tol)


def catmull_rom(pts: Polyline, t: float) -> Pt:
    """Evaluate a Catmull-Rom spline at parameter *t* ∈ [0, 1].

    Uses the standard Hermite cubic formula:
    ``0.5 * (2P1 + (-P0+P2)u + (2P0-5P1+4P2-P3)u² + (-P0+3P1-3P2+P3)u³)``
    """
    n = len(pts)
    if n == 0:
        return (0.0, 0.0)
    if n == 1:
        return pts[0]
    t = max(0.0, min(1.0, t))
    seg = int(t * (n - 1))
    seg = min(seg, n - 2)
    u = t * (n - 1) - seg
    u2, u3 = u * u, u * u * u

    p0 = pts[max(0, seg - 1)]
    p1 = pts[seg]
    p2 = pts[min(n - 1, seg + 1)]
    p3 = pts[min(n - 1, seg + 2)]

    x = 0.5 * (
        2 * p1[0]
        + (-p0[0] + p2[0]) * u
        + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * u2
        + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * u3
    )
    y = 0.5 * (
        2 * p1[1]
        + (-p0[1] + p2[1]) * u
        + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * u2
        + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * u3
    )
    return (x, y)


def sample_spline(pts: Polyline, n: int) -> Polyline:
    """Uniform sampling of a Catmull-Rom spline: *n* + 1 points."""
    if n <= 0 or len(pts) < 2:
        return list(pts)
    return [catmull_rom(pts, i / n) for i in range(n + 1)]


def make_poly(angles_deg: List[float]) -> Polyline:
    """Build a unit-edge polygon from interior angles (CCW, centred).

    Used for constructing Girih tile shapes from their defining angles.
    Each edge has length 1; scale by ``edge_mm`` afterwards.
    """
    n = len(angles_deg)
    verts: Polyline = [(0.0, 0.0)]
    heading = 0.0
    for i in range(n - 1):
        verts.append((
            verts[-1][0] + math.cos(heading),
            verts[-1][1] + math.sin(heading),
        ))
        heading += math.pi - math.radians(angles_deg[(i + 1) % n])
    # Centre on centroid
    cx = sum(v[0] for v in verts) / n
    cy = sum(v[1] for v in verts) / n
    return [(v[0] - cx, v[1] - cy) for v in verts]
