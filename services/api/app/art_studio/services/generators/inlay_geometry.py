"""
Inlay Geometry Primitives & Offset Engine

Provides GeometryCollection (the intermediate representation for all inlay
pattern generators) and the shared math infrastructure ported from the V3
spiral prototype and the Vine/Girih/Celtic HTML prototypes.

Shared math layer
-----------------
* Miter-join polygon offset (proper corner geometry)
* Dual-rail polyline strip for CNC pocketing
* De Casteljau cubic/quadratic Bézier subdivision
* SVG endpoint-arc → centre-parameter conversion (SVG spec F.6.5-6)
* Full SVG path ``d`` tokeniser (M/L/H/V/C/S/Q/T/A/Z)
* Catmull-Rom spline interpolation

All coordinates in mm.  Positive offset = outward / male, negative = inward / pocket.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

Pt = Tuple[float, float]
Polyline = List[Pt]


# ---------------------------------------------------------------------------
# Data model — language-agnostic geometry IR
# ---------------------------------------------------------------------------

@dataclass
class GeometryElement:
    """Single geometric primitive in mm coordinates."""

    kind: str  # "polygon", "polyline", "circle", "rect"
    points: List[Pt] = field(default_factory=list)
    # For circles: centre is points[0], radius stored separately
    radius: float = 0.0
    # For rects: (x, y, w, h) encoded in points as [(x,y), (x+w, y+h)]
    material_index: int = 0
    stroke_width: float = 0.25


@dataclass
class GeometryCollection:
    """Complete output of one pattern generation call.

    Fields
    ------
    elements : list[GeometryElement]
        Raw pattern geometry (the *centerline*).
    width_mm, height_mm : float
        Bounding box of the *design* region.
    origin_x, origin_y : float
        Translation applied before rendering (for radial patterns centred at 0,0).
    radial : bool
        True for patterns that centre on the origin (spiral, sunburst, feather).
    tile_w, tile_h : float | None
        For linear-tiling patterns, the single-tile footprint.
    """

    elements: List[GeometryElement] = field(default_factory=list)
    width_mm: float = 0.0
    height_mm: float = 0.0
    origin_x: float = 0.0
    origin_y: float = 0.0
    radial: bool = False
    tile_w: float | None = None
    tile_h: float | None = None


# ---------------------------------------------------------------------------
# Core math — shared infrastructure for ALL generators
# ---------------------------------------------------------------------------

def _normalize(x: float, y: float) -> Tuple[float, float]:
    length = math.hypot(x, y) or 1.0
    return x / length, y / length


def line_line_intersect(
    p1: Pt, p2: Pt, p3: Pt, p4: Pt,
) -> Optional[Pt]:
    """Determinant-based line–line intersection.

    Returns *None* if lines are (near-)parallel (det < 1e-10).
    """
    d1x, d1y = p2[0] - p1[0], p2[1] - p1[1]
    d2x, d2y = p4[0] - p3[0], p4[1] - p3[1]
    det = d1x * d2y - d1y * d2x
    if abs(det) < 1e-10:
        return None
    t = ((p3[0] - p1[0]) * d2y - (p3[1] - p1[1]) * d2x) / det
    return (p1[0] + t * d1x, p1[1] + t * d1y)


# ---------------------------------------------------------------------------
# Offset engine — miter-join polygon offset
# ---------------------------------------------------------------------------

def offset_polyline(pts: Polyline, dist: float) -> Polyline:
    """Offset an *open* polyline by ``dist`` mm using per-vertex normals.

    Positive ``dist`` offsets to the left of the travel direction.
    """
    n = len(pts)
    if n < 2:
        return list(pts)
    result: Polyline = []
    for i in range(n):
        prev = pts[max(0, i - 1)]
        nxt = pts[min(n - 1, i + 1)]
        tx, ty = _normalize(nxt[0] - prev[0], nxt[1] - prev[1])
        nx, ny = -ty, tx
        result.append((pts[i][0] + nx * dist, pts[i][1] + ny * dist))
    return result


def offset_polygon(pts: Polyline, dist: float) -> Polyline:
    """Offset a *closed* polygon by ``dist`` mm using miter-join geometry.

    For each edge, shift by the outward normal × dist, then intersect
    adjacent offset edges at miter corners.  Falls back to averaged
    normals when the intersection is degenerate.

    Positive = outward (for CCW winding).
    """
    n = len(pts)
    if n < 3:
        return list(pts)

    # Build per-edge offset segments
    edges: List[Tuple[Pt, Pt]] = []
    for i in range(n):
        p1 = pts[i]
        p2 = pts[(i + 1) % n]
        dx, dy = p2[0] - p1[0], p2[1] - p1[1]
        length = math.hypot(dx, dy) or 1.0
        # Outward normal for CCW winding: (dy, -dx) / len
        nx, ny = dy / length, -dx / length
        edges.append((
            (p1[0] + nx * dist, p1[1] + ny * dist),
            (p2[0] + nx * dist, p2[1] + ny * dist),
        ))

    result: Polyline = []
    for i in range(n):
        prev_edge = edges[(i - 1) % n]
        curr_edge = edges[i]
        hit = line_line_intersect(
            prev_edge[0], prev_edge[1],
            curr_edge[0], curr_edge[1],
        )
        if hit is not None:
            result.append(hit)
        else:
            # Fallback: midpoint of the two offset endpoints
            result.append((
                (prev_edge[1][0] + curr_edge[0][0]) * 0.5,
                (prev_edge[1][1] + curr_edge[0][1]) * 0.5,
            ))
    return result


def offset_polyline_strip(pts: Polyline, dist: float) -> Polyline:
    """Dual-rail closed strip around an open polyline.

    Returns a closed polygon: outer rail forward → inner rail reversed.
    Used for CNC pocket boundaries around vine stems, binding paths, etc.
    """
    if len(pts) < 2:
        return list(pts)
    outer = offset_polyline(pts, dist)
    inner = offset_polyline(pts, -dist)
    return outer + list(reversed(inner))


# ---------------------------------------------------------------------------
# Bézier subdivision — De Casteljau
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# SVG arc conversion — SVG spec F.6.5-6
# ---------------------------------------------------------------------------

def arc_to_center_param(
    x1: float, y1: float,
    rx: float, ry: float,
    phi_deg: float,
    fa: int, fs: int,
    x2: float, y2: float,
) -> Tuple[float, float, float, float, float, float]:
    """Convert SVG endpoint-arc to centre parameterisation.

    Returns (cx, cy, rx_corr, ry_corr, theta1, dtheta).
    """
    phi = math.radians(phi_deg)
    cos_phi, sin_phi = math.cos(phi), math.sin(phi)

    # Step 1: compute (x1', y')
    dx2, dy2 = (x1 - x2) / 2, (y1 - y2) / 2
    x1p = cos_phi * dx2 + sin_phi * dy2
    y1p = -sin_phi * dx2 + cos_phi * dy2

    # Radius correction (SVG spec: ensure radii are large enough)
    rx, ry = abs(rx), abs(ry)
    lam = (x1p * x1p) / (rx * rx) + (y1p * y1p) / (ry * ry)
    if lam > 1.0:
        s = math.sqrt(lam)
        rx *= s
        ry *= s

    # Step 2: compute (cx', cy')
    num = max(0.0, rx * rx * ry * ry - rx * rx * y1p * y1p - ry * ry * x1p * x1p)
    den = rx * rx * y1p * y1p + ry * ry * x1p * x1p
    sq = math.sqrt(num / den) if den > 0 else 0.0
    if fa == fs:
        sq = -sq
    cxp = sq * rx * y1p / ry
    cyp = -sq * ry * x1p / rx

    # Step 3: compute (cx, cy) from (cx', cy')
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    cx = cos_phi * cxp - sin_phi * cyp + mx
    cy = sin_phi * cxp + cos_phi * cyp + my

    # Step 4: compute theta1, dtheta
    def _angle(ux: float, uy: float, vx: float, vy: float) -> float:
        dot = ux * vx + uy * vy
        det = ux * vy - uy * vx
        return math.atan2(det, dot)

    theta1 = _angle(1.0, 0.0, (x1p - cxp) / rx, (y1p - cyp) / ry)
    dtheta = _angle(
        (x1p - cxp) / rx, (y1p - cyp) / ry,
        (-x1p - cxp) / rx, (-y1p - cyp) / ry,
    )
    # Clamp dtheta per SVG spec
    if fs == 0 and dtheta > 0:
        dtheta -= 2 * math.pi
    elif fs == 1 and dtheta < 0:
        dtheta += 2 * math.pi

    return (cx, cy, rx, ry, theta1, dtheta)


def tessellate_arc(
    x1: float, y1: float,
    rx: float, ry: float,
    x_rot_deg: float,
    fa: int, fs: int,
    x2: float, y2: float,
    tol: float = 0.5,
) -> Polyline:
    """Tessellate an SVG elliptical arc to line segments."""
    if rx < 1e-10 or ry < 1e-10:
        return [(x2, y2)]

    cx, cy, rx, ry, theta1, dtheta = arc_to_center_param(
        x1, y1, rx, ry, x_rot_deg, fa, fs, x2, y2,
    )
    phi = math.radians(x_rot_deg)
    cos_phi, sin_phi = math.cos(phi), math.sin(phi)

    # Dynamic step count based on arc extent and radius
    steps = max(4, int(abs(dtheta) * max(rx, ry) / tol))
    pts: Polyline = []
    for i in range(1, steps + 1):
        t = theta1 + dtheta * i / steps
        cos_t, sin_t = math.cos(t), math.sin(t)
        px = cos_phi * rx * cos_t - sin_phi * ry * sin_t + cx
        py = sin_phi * rx * cos_t + cos_phi * ry * sin_t + cy
        pts.append((px, py))
    return pts


# ---------------------------------------------------------------------------
# SVG path ``d`` tokeniser / tessellator
# ---------------------------------------------------------------------------

_SVG_CMD_RE = re.compile(r'([MmLlHhVvCcSsQqTtAaZz])')
_SVG_NUM_RE = re.compile(
    r'[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?',
)


def tessellate_path_d(d: str, tol: float = 0.5) -> List[Polyline]:
    """Parse an SVG path ``d`` string and return sub-paths as point arrays.

    Handles all SVG path commands: M/m, L/l, H/h, V/v, C/c, S/s, Q/q, T/t,
    A/a, Z/z.  Curves are adaptively subdivided to *tol* mm.
    """
    tokens = _SVG_CMD_RE.split(d)
    sub_paths: List[Polyline] = []
    current: Polyline = []
    cx, cy = 0.0, 0.0  # current point
    sx, sy = 0.0, 0.0  # subpath start
    last_cp: Optional[Pt] = None  # last control point for S/T reflection
    last_cmd = ""

    i = 0
    while i < len(tokens):
        tok = tokens[i].strip()
        i += 1
        if not tok:
            continue

        if tok in "MmLlHhVvCcSsQqTtAaZz":
            cmd = tok
            nums_str = tokens[i].strip() if i < len(tokens) else ""
            i += 1
            nums = [float(m) for m in _SVG_NUM_RE.findall(nums_str)]
        else:
            continue

        j = 0
        rel = cmd.islower()

        if cmd in "Mm":
            while j < len(nums) - 1:
                x, y = nums[j], nums[j + 1]
                j += 2
                if rel:
                    x += cx; y += cy
                if j == 2:  # first pair is moveTo
                    if current:
                        sub_paths.append(current)
                    current = [(x, y)]
                    sx, sy = x, y
                else:  # subsequent pairs are implicit lineTo
                    current.append((x, y))
                cx, cy = x, y
            last_cp = None

        elif cmd in "Ll":
            while j < len(nums) - 1:
                x, y = nums[j], nums[j + 1]
                j += 2
                if rel:
                    x += cx; y += cy
                current.append((x, y))
                cx, cy = x, y
            last_cp = None

        elif cmd in "Hh":
            while j < len(nums):
                x = nums[j]
                j += 1
                if rel:
                    x += cx
                current.append((x, cy))
                cx = x
            last_cp = None

        elif cmd in "Vv":
            while j < len(nums):
                y = nums[j]
                j += 1
                if rel:
                    y += cy
                current.append((cx, y))
                cy = y
            last_cp = None

        elif cmd in "Cc":
            while j < len(nums) - 5:
                x1, y1, x2, y2, x, y = nums[j:j + 6]
                j += 6
                if rel:
                    x1 += cx; y1 += cy; x2 += cx; y2 += cy; x += cx; y += cy
                pts = subdivide_cubic((cx, cy), (x1, y1), (x2, y2), (x, y), tol)
                current.extend(pts[1:])
                last_cp = (x2, y2)
                cx, cy = x, y

        elif cmd in "Ss":
            while j < len(nums) - 3:
                x2, y2, x, y = nums[j:j + 4]
                j += 4
                if rel:
                    x2 += cx; y2 += cy; x += cx; y += cy
                # Reflect previous control point
                if last_cp is not None and last_cmd in "CcSs":
                    x1 = 2 * cx - last_cp[0]
                    y1 = 2 * cy - last_cp[1]
                else:
                    x1, y1 = cx, cy
                pts = subdivide_cubic((cx, cy), (x1, y1), (x2, y2), (x, y), tol)
                current.extend(pts[1:])
                last_cp = (x2, y2)
                cx, cy = x, y

        elif cmd in "Qq":
            while j < len(nums) - 3:
                x1, y1, x, y = nums[j:j + 4]
                j += 4
                if rel:
                    x1 += cx; y1 += cy; x += cx; y += cy
                pts = subdivide_quadratic((cx, cy), (x1, y1), (x, y), tol)
                current.extend(pts[1:])
                last_cp = (x1, y1)
                cx, cy = x, y

        elif cmd in "Tt":
            while j < len(nums) - 1:
                x, y = nums[j], nums[j + 1]
                j += 2
                if rel:
                    x += cx; y += cy
                if last_cp is not None and last_cmd in "QqTt":
                    x1 = 2 * cx - last_cp[0]
                    y1 = 2 * cy - last_cp[1]
                else:
                    x1, y1 = cx, cy
                pts = subdivide_quadratic((cx, cy), (x1, y1), (x, y), tol)
                current.extend(pts[1:])
                last_cp = (x1, y1)
                cx, cy = x, y

        elif cmd in "Aa":
            while j < len(nums) - 6:
                arx, ary = nums[j], nums[j + 1]
                x_rot = nums[j + 2]
                fa_v, fs_v = int(nums[j + 3]), int(nums[j + 4])
                x, y = nums[j + 5], nums[j + 6]
                j += 7
                if rel:
                    x += cx; y += cy
                arc_pts = tessellate_arc(
                    cx, cy, arx, ary, x_rot, fa_v, fs_v, x, y, tol,
                )
                current.extend(arc_pts)
                cx, cy = x, y
            last_cp = None

        elif cmd in "Zz":
            if current:
                current.append((sx, sy))
                sub_paths.append(current)
                current = []
            cx, cy = sx, sy
            last_cp = None

        last_cmd = cmd

    if current:
        sub_paths.append(current)

    return sub_paths


def points_to_path_d(pts: Polyline, closed: bool = False) -> str:
    """Convert a point array to an SVG path ``d`` string."""
    if not pts:
        return ""
    parts = [f"M {pts[0][0]:.4f},{pts[0][1]:.4f}"]
    parts.extend(f"L {x:.4f},{y:.4f}" for x, y in pts[1:])
    if closed:
        parts.append("Z")
    return " ".join(parts)


def offset_path_d(
    d: str, offset_mm: float, tol: float = 0.5,
) -> str:
    """End-to-end pipeline: tessellate SVG path → offset → back to ``d``."""
    sub_paths = tessellate_path_d(d, tol)
    parts: List[str] = []
    for sp in sub_paths:
        if len(sp) < 2:
            continue
        # Detect closed: first ≈ last
        closed = (
            math.hypot(sp[-1][0] - sp[0][0], sp[-1][1] - sp[0][1]) < tol
        )
        if closed:
            off = offset_polygon(sp[:-1], offset_mm)
        else:
            off = offset_polyline(sp, offset_mm)
        parts.append(points_to_path_d(off, closed))
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Catmull-Rom spline
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Polygon construction helpers (Girih tiles)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Rope / band math — tangent, normal, arc-length, strand generation
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Collection-level offset (delegates to per-element functions above)
# ---------------------------------------------------------------------------

def offset_collection(
    geo: GeometryCollection,
    amount_mm: float,
) -> GeometryCollection:
    """Return a new collection with every element offset by *amount_mm*.

    * Polygons  → ``offset_polygon``
    * Polylines → ``offset_polyline``
    * Circles   → radius adjusted (clamped ≥ 0)
    * Rects     → expanded/contracted symmetrically
    """
    out_elements: List[GeometryElement] = []
    for el in geo.elements:
        if el.kind == "polygon" and len(el.points) >= 3:
            new_pts = offset_polygon(el.points, amount_mm)
            out_elements.append(GeometryElement(
                kind="polygon",
                points=new_pts,
                material_index=el.material_index,
                stroke_width=el.stroke_width,
            ))
        elif el.kind == "polyline" and len(el.points) >= 2:
            new_pts = offset_polyline(el.points, amount_mm)
            out_elements.append(GeometryElement(
                kind="polyline",
                points=new_pts,
                material_index=el.material_index,
                stroke_width=el.stroke_width,
            ))
        elif el.kind == "circle" and el.points:
            new_r = max(0.0, el.radius + amount_mm)
            out_elements.append(GeometryElement(
                kind="circle",
                points=list(el.points),
                radius=new_r,
                material_index=el.material_index,
                stroke_width=el.stroke_width,
            ))
        elif el.kind == "rect" and len(el.points) >= 2:
            (x0, y0), (x1, y1) = el.points[0], el.points[1]
            out_elements.append(GeometryElement(
                kind="rect",
                points=[
                    (x0 - amount_mm, y0 - amount_mm),
                    (x1 + amount_mm, y1 + amount_mm),
                ],
                material_index=el.material_index,
                stroke_width=el.stroke_width,
            ))
        else:
            out_elements.append(el)

    return GeometryCollection(
        elements=out_elements,
        width_mm=geo.width_mm,
        height_mm=geo.height_mm,
        origin_x=geo.origin_x,
        origin_y=geo.origin_y,
        radial=geo.radial,
        tile_w=geo.tile_w,
        tile_h=geo.tile_h,
    )


# ---------------------------------------------------------------------------
# SVG rendering helpers
# ---------------------------------------------------------------------------

MATERIALS = {
    "mop":       {"name": "MOP White",      "color": "#ddeef8", "grain": "#c0d0dc"},
    "abalone":   {"name": "Abalone",        "color": "#58a87a", "grain": "#3a7858"},
    "black_mop": {"name": "Black MOP",      "color": "#28283a", "grain": "#181828"},
    "gold_mop":  {"name": "Gold MOP",       "color": "#d4a030", "grain": "#a87818"},
    "paua":      {"name": "Paua Abalone",   "color": "#3858a0", "grain": "#283878"},
    "ebony":     {"name": "Ebony",          "color": "#181008", "grain": "#0c0804"},
    "maple":     {"name": "Maple",          "color": "#eee0b0", "grain": "#d4c080"},
    "rosewood":  {"name": "Rosewood",       "color": "#481c10", "grain": "#341008"},
    "koa":       {"name": "Koa",            "color": "#c07020", "grain": "#a05010"},
    "bloodwood": {"name": "Bloodwood",      "color": "#981e10", "grain": "#781208"},
    "holly":     {"name": "Holly",          "color": "#f0f0e0", "grain": "#dcdcc8"},
    "walnut":    {"name": "Walnut",         "color": "#6a3c18", "grain": "#4a2810"},
    "bone":      {"name": "Bone",           "color": "#f0e8d0", "grain": "#e0d8c0"},
    "cedar":     {"name": "Cedar",          "color": "#c07040", "grain": "#a06030"},
}

MATERIAL_KEYS = list(MATERIALS.keys())


def mat_color(key: str) -> str:
    return MATERIALS.get(key, {}).get("color", "#888888")


def _pts_to_d(pts: Polyline, close: bool = False) -> str:
    if not pts:
        return ""
    parts = [f"M {pts[0][0]:.4f},{pts[0][1]:.4f}"]
    parts.extend(f"L {x:.4f},{y:.4f}" for x, y in pts[1:])
    if close:
        parts.append("Z")
    return " ".join(parts)


def element_to_svg(
    el: GeometryElement,
    mat_colors: List[str],
    line_color: str = "#00000033",
) -> str:
    """Render a single GeometryElement to an SVG fragment string."""
    fill = mat_colors[el.material_index % len(mat_colors)] if mat_colors else "#888"
    sw = f"{el.stroke_width:.3f}"

    if el.kind == "polygon":
        d = _pts_to_d(el.points, close=True)
        return (
            f'<path d="{d}" fill="{fill}" stroke="{line_color}" '
            f'stroke-width="{sw}" stroke-linejoin="round"/>'
        )
    if el.kind == "polyline":
        d = _pts_to_d(el.points, close=False)
        return (
            f'<path d="{d}" fill="none" stroke="{fill}" '
            f'stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round"/>'
        )
    if el.kind == "circle" and el.points:
        cx, cy = el.points[0]
        return (
            f'<circle cx="{cx:.4f}" cy="{cy:.4f}" r="{el.radius:.4f}" '
            f'fill="{fill}" stroke="{line_color}" stroke-width="{sw}"/>'
        )
    if el.kind == "rect" and len(el.points) >= 2:
        (x0, y0), (x1, y1) = el.points[0], el.points[1]
        w, h = x1 - x0, y1 - y0
        return (
            f'<rect x="{x0:.4f}" y="{y0:.4f}" width="{w:.4f}" height="{h:.4f}" '
            f'fill="{fill}" stroke="{line_color}" stroke-width="{sw}"/>'
        )
    return ""


def collection_to_svg(
    geo: GeometryCollection,
    materials: List[str] | None = None,
    bg_material: str = "ebony",
    line_color: str = "#00000033",
    for_export: bool = False,
) -> str:
    """Render a full GeometryCollection to SVG.

    When *for_export* is True the root ``<svg>`` carries mm width/height
    attributes suitable for CAD import.
    """
    materials = materials or ["mop", "ebony", "koa"]
    mc = [mat_color(m) for m in materials]
    bg = mat_color(bg_material)
    W, H = geo.width_mm, geo.height_mm

    dims = (
        f'width="{W:.3f}mm" height="{H:.3f}mm"'
        if for_export
        else 'width="100%" height="100%"'
    )
    transform = ""
    if geo.origin_x or geo.origin_y:
        transform = f' transform="translate({geo.origin_x:.3f},{geo.origin_y:.3f})"'

    body = "\n    ".join(element_to_svg(el, mc, line_color) for el in geo.elements)

    comment = (
        "\n  <!-- The Production Shop · Inlay Pattern Generator · mm coordinates -->"
        if for_export
        else ""
    )

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {W:.3f} {H:.3f}" {dims}>{comment}\n'
        f'  <rect width="{W:.3f}" height="{H:.3f}" fill="{bg}"/>\n'
        f'  <clipPath id="bounds"><rect width="{W:.3f}" height="{H:.3f}"/></clipPath>\n'
        f'  <g clip-path="url(#bounds)"{transform}>\n'
        f"    {body}\n"
        f"  </g>\n"
        f"</svg>"
    )


def collection_to_layered_svg(
    centerline: GeometryCollection,
    male_offset_mm: float = 0.10,
    pocket_offset_mm: float = 0.10,
    materials: List[str] | None = None,
    bg_material: str = "ebony",
) -> str:
    """Export SVG with three layer groups: design, male_cut, pocket_cut.

    Each layer is a ``<g id="...">`` block so CAM tools can isolate them.
    """
    materials = materials or ["mop", "ebony", "koa"]
    mc = [mat_color(m) for m in materials]
    bg = mat_color(bg_material)
    W, H = centerline.width_mm, centerline.height_mm

    male = offset_collection(centerline, male_offset_mm)
    pocket = offset_collection(centerline, -pocket_offset_mm)

    transform = ""
    if centerline.origin_x or centerline.origin_y:
        transform = (
            f' transform="translate({centerline.origin_x:.3f},'
            f'{centerline.origin_y:.3f})"'
        )

    def _layer(geo: GeometryCollection, color: str) -> str:
        return "\n      ".join(
            element_to_svg(el, mc, color) for el in geo.elements
        )

    center_body = _layer(centerline, "#00000033")
    male_body = _layer(male, "#00000033")
    pocket_body = _layer(pocket, "#00000033")

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {W:.3f} {H:.3f}" '
        f'width="{W:.3f}mm" height="{H:.3f}mm">\n'
        f"  <!-- The Production Shop · Inlay Pattern Generator · mm coordinates -->\n"
        f'  <rect width="{W:.3f}" height="{H:.3f}" fill="{bg}"/>\n'
        f'  <g id="centerline" data-layer="centerline"{transform}>\n'
        f"      {center_body}\n"
        f"  </g>\n"
        f'  <g id="male_cut" data-layer="male_cut" '
        f'data-offset-mm="{male_offset_mm:.3f}"{transform}>\n'
        f"      {male_body}\n"
        f"  </g>\n"
        f'  <g id="pocket_cut" data-layer="pocket_cut" '
        f'data-offset-mm="{pocket_offset_mm:.3f}"{transform}>\n'
        f"      {pocket_body}\n"
        f"  </g>\n"
        f"</svg>"
    )
