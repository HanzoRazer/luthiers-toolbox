"""
Inlay Geometry Rope/Band Path Generation

Tangent, normal, arc-length computation and multi-strand rope generation
for twisted rope and binding patterns.

All coordinates in mm.
"""
from __future__ import annotations

import math
from typing import List, Tuple

from .inlay_geometry_core import Polyline, Pt
from .inlay_geometry_bezier import sample_spline


def _normalize(x: float, y: float) -> Tuple[float, float]:
    """Normalize a 2D vector to unit length."""
    length = math.hypot(x, y) or 1.0
    return x / length, y / length


def compute_tangent_normal_arclen(
    pts: Polyline,
) -> Tuple[List[Pt], List[Pt], List[float]]:
    """Per-vertex tangent, normal (CCW), and cumulative arc length.

    Returns (tangents, normals, arc_lengths) where arc_lengths[0] == 0.
    """
    n = len(pts)
    if n < 2:
        return ([(1.0, 0.0)], [(0.0, 1.0)], [0.0])

    tangents: List[Pt] = []
    normals: List[Pt] = []
    arc_lens: List[float] = [0.0]

    for i in range(n):
        prev = pts[max(0, i - 1)]
        nxt = pts[min(n - 1, i + 1)]
        tx, ty = _normalize(nxt[0] - prev[0], nxt[1] - prev[1])
        tangents.append((tx, ty))
        normals.append((-ty, tx))  # CCW perpendicular
        if i > 0:
            dx = pts[i][0] - pts[i - 1][0]
            dy = pts[i][1] - pts[i - 1][1]
            arc_lens.append(arc_lens[-1] + math.hypot(dx, dy))

    return tangents, normals, arc_lens


def build_centerline(
    shape: str,
    length_mm: float,
    amplitude: float = 10.0,
    custom_pts: Polyline | None = None,
    n_samples: int = 200,
) -> Polyline:
    """Build a centerline path for rope/band generation.

    Shapes
    ------
    straight : horizontal line
    cscroll  : quarter-circle arc
    swave    : sinusoidal wave
    spiral   : Archimedean spiral (2.2 turns)
    custom   : user-supplied points resampled via spline
    """
    pts: Polyline = []

    if shape == "straight":
        for i in range(n_samples):
            t = i / max(1, n_samples - 1)
            pts.append((t * length_mm, 0.0))

    elif shape == "cscroll":
        r = length_mm * 0.45
        for i in range(n_samples):
            t = i / max(1, n_samples - 1)
            a = t * math.pi * 0.5  # quarter circle
            pts.append((r * math.sin(a), -r * (1 - math.cos(a))))

    elif shape == "swave":
        amp = min(amplitude, length_mm * 0.18)
        for i in range(n_samples):
            t = i / max(1, n_samples - 1)
            x = t * length_mm
            y = amp * math.sin(t * math.pi * 2)
            pts.append((x, y))

    elif shape == "spiral":
        turns = 2.2
        max_r = length_mm * 0.4
        for i in range(n_samples):
            t = i / max(1, n_samples - 1)
            a = t * turns * 2 * math.pi
            r = max_r * (1 - t)  # inward spiral
            pts.append((r * math.cos(a), r * math.sin(a)))

    elif shape == "custom" and custom_pts and len(custom_pts) >= 2:
        pts = sample_spline(custom_pts, n_samples)

    else:
        # Default to straight
        for i in range(n_samples):
            t = i / max(1, n_samples - 1)
            pts.append((t * length_mm, 0.0))

    return pts


def generate_strand_paths(
    centerline: Polyline,
    num_strands: int,
    rope_radius_mm: float,
    twist_per_mm: float,
    strand_width_frac: float = 0.55,
    taper: float = 0.0,
) -> List[Tuple[Polyline, List[float], List[float]]]:
    """Generate all strand centerline paths with depth and width data.

    Returns list of (points, depth_per_point, width_per_point) per strand.
    """
    tangents, normals, arc_lens = compute_tangent_normal_arclen(centerline)
    strands = []

    for k in range(num_strands):
        phase_k = k * 2 * math.pi / num_strands
        pts: Polyline = []
        depths: List[float] = []
        widths: List[float] = []

        for i, (cx, cy) in enumerate(centerline):
            nx, ny = normals[i]
            s = arc_lens[i]

            lateral = math.sin(phase_k + twist_per_mm * s) * rope_radius_mm * 0.42
            depth = math.cos(phase_k + twist_per_mm * s)
            w = strand_width_frac * (1 - abs(depth) * taper * 0.4)

            pts.append((cx + nx * lateral, cy + ny * lateral))
            depths.append(depth)
            widths.append(w)

        strands.append((pts, depths, widths))

    return strands


def split_strand_at_crossings(
    pts: Polyline,
    depths: List[float],
) -> List[Tuple[Polyline, bool]]:
    """Split a strand path into segments at depth sign changes.

    Returns list of (segment_points, on_top) tuples.
    on_top is True when depth > 0 (strand is "over" others).
    """
    if len(pts) < 2:
        return [(pts, depths[0] >= 0 if depths else True)]

    segments: List[Tuple[Polyline, bool]] = []
    current_pts: Polyline = [pts[0]]
    current_on_top = depths[0] >= 0

    for i in range(1, len(pts)):
        on_top = depths[i] >= 0
        if on_top != current_on_top and len(current_pts) >= 1:
            # Linear interpolation to find crossing point
            d0, d1 = depths[i - 1], depths[i]
            denom = d0 - d1
            if abs(denom) > 1e-12:
                t = d0 / denom
                cross_x = pts[i - 1][0] + t * (pts[i][0] - pts[i - 1][0])
                cross_y = pts[i - 1][1] + t * (pts[i][1] - pts[i - 1][1])
                cross_pt = (cross_x, cross_y)
            else:
                cross_pt = pts[i]

            current_pts.append(cross_pt)
            segments.append((current_pts, current_on_top))
            current_pts = [cross_pt]
            current_on_top = on_top

        current_pts.append(pts[i])

    if current_pts:
        segments.append((current_pts, current_on_top))

    return segments
