"""
Inlay Shape Primitives

Low-level shape generators that return point lists.
Used by the 4 engines (Grid, Radial, Path, Medallion) to build patterns.

All coordinates in mm. Functions are pure and stateless.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Tuple

# Type alias for 2D point
Pt = Tuple[float, float]
Polyline = List[Pt]


# ---------------------------------------------------------------------------
# Basic Shapes
# ---------------------------------------------------------------------------

def rect_pts(cx: float, cy: float, w: float, h: float, angle: float = 0) -> List[Pt]:
    """Rectangle centered at (cx, cy) with optional rotation."""
    hw, hh = w / 2, h / 2
    corners = [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]
    if angle != 0:
        ca, sa = math.cos(angle), math.sin(angle)
        corners = [(x * ca - y * sa, x * sa + y * ca) for x, y in corners]
    return [(cx + x, cy + y) for x, y in corners]


def diamond_pts(cx: float, cy: float, w: float, h: float,
               wave: float = 0, lean: float = 0, phase: float = 0) -> List[Pt]:
    """Diamond shape with optional wave distortion and lean."""
    dy = wave * h * 0.4 * math.sin(phase)
    lx = lean * w * 0.3
    return [
        (cx + lx, cy - h / 2 + dy),
        (cx + w / 2, cy + dy),
        (cx + lx, cy + h / 2 + dy),
        (cx - w / 2, cy + dy),
    ]


def wedge_pts(cx: float, cy: float, inner_r: float, outer_r: float,
              start_angle: float, end_angle: float, n_arc_pts: int = 11) -> List[Pt]:
    """Wedge/sector shape between two radii and two angles."""
    pts: List[Pt] = []
    # Outer arc
    for i in range(n_arc_pts):
        t = start_angle + (end_angle - start_angle) * i / (n_arc_pts - 1)
        pts.append((cx + math.cos(t) * outer_r, cy + math.sin(t) * outer_r))
    # Inner arc (reversed)
    for i in range(n_arc_pts - 1, -1, -1):
        t = start_angle + (end_angle - start_angle) * i / (n_arc_pts - 1)
        pts.append((cx + math.cos(t) * inner_r, cy + math.sin(t) * inner_r))
    return pts


def kite_pts(cx: float, cy: float, inner_r: float, outer_r: float,
             half_width: float, angle: float) -> List[Pt]:
    """Kite/petal shape pointing outward from center at given angle."""
    cos_a, sin_a = math.cos(angle), math.sin(angle)
    perp = angle + math.pi / 2
    cos_p, sin_p = math.cos(perp), math.sin(perp)

    inner_tip = (cx + inner_r * cos_a, cy + inner_r * sin_a)
    outer_tip = (cx + outer_r * cos_a, cy + outer_r * sin_a)
    mid_r = (inner_r + outer_r) / 2
    mid_left = (cx + mid_r * cos_a - half_width * cos_p,
                cy + mid_r * sin_a - half_width * sin_p)
    mid_right = (cx + mid_r * cos_a + half_width * cos_p,
                 cy + mid_r * sin_a + half_width * sin_p)
    return [inner_tip, mid_left, outer_tip, mid_right]


def teardrop_pts(cx: float, cy: float, length: float, width: float,
                 angle: float) -> List[Pt]:
    """Teardrop/leaf shape pointing in direction of angle."""
    cos_a, sin_a = math.cos(angle), math.sin(angle)
    perp = angle + math.pi / 2
    cos_p, sin_p = math.cos(perp), math.sin(perp)

    base = (cx, cy)
    tip = (cx + length * cos_a, cy + length * sin_a)
    mid_x = cx + length * 0.4 * cos_a
    mid_y = cy + length * 0.4 * sin_a
    bulge = width * 0.35
    b1 = (mid_x + bulge * cos_p, mid_y + bulge * sin_p)
    b2 = (mid_x - bulge * cos_p, mid_y - bulge * sin_p)
    return [base, b1, tip, b2]


def lens_pts(cx: float, cy: float, length: float, width: float,
             angle: float, n_pts: int = 16) -> List[Pt]:
    """Lens/eye shape (two opposing arcs) for petals."""
    a = math.radians(angle) if isinstance(angle, (int, float)) and abs(angle) > 2 * math.pi else angle
    cos_a, sin_a = math.cos(a), math.sin(a)
    hl, hw = length / 2, width / 2

    def _rotate(x: float, y: float) -> Pt:
        return (cx + x * cos_a - y * sin_a, cy + x * sin_a + y * cos_a)

    left = _rotate(-hl, 0)
    right = _rotate(hl, 0)
    c_upper_l, c_upper_r = _rotate(-hl, -hw), _rotate(hl, -hw)
    c_lower_r, c_lower_l = _rotate(hl, hw), _rotate(-hl, hw)

    def _bez(p0: Pt, p1: Pt, p2: Pt, p3: Pt) -> List[Pt]:
        pts: List[Pt] = []
        for i in range(n_pts + 1):
            t = i / n_pts
            u = 1 - t
            x = u**3 * p0[0] + 3*u**2*t * p1[0] + 3*u*t**2 * p2[0] + t**3 * p3[0]
            y = u**3 * p0[1] + 3*u**2*t * p1[1] + 3*u*t**2 * p2[1] + t**3 * p3[1]
            pts.append((x, y))
        return pts

    pts: List[Pt] = []
    pts.extend(_bez(left, c_upper_l, c_upper_r, right))
    pts.extend(_bez(right, c_lower_r, c_lower_l, left)[1:])
    return pts


def circle_pts(cx: float, cy: float, r: float, n_pts: int = 24) -> List[Pt]:
    """Circle approximated as polygon."""
    return [(cx + r * math.cos(i * 2 * math.pi / n_pts),
             cy + r * math.sin(i * 2 * math.pi / n_pts))
            for i in range(n_pts)]


def arc_band_pts(cx: float, cy: float, inner_r: float, outer_r: float,
                 start_angle: float, sweep: float, n_pts: int = 24) -> List[Pt]:
    """Arc band (thick arc) between two radii."""
    end_angle = start_angle + sweep
    pts: List[Pt] = []
    # Outer arc forward
    for i in range(n_pts + 1):
        a = start_angle + sweep * i / n_pts
        pts.append((cx + outer_r * math.cos(a), cy + outer_r * math.sin(a)))
    # Inner arc reverse
    for i in range(n_pts, -1, -1):
        a = start_angle + sweep * i / n_pts
        pts.append((cx + inner_r * math.cos(a), cy + inner_r * math.sin(a)))
    return pts


def hexagon_pts(cx: float, cy: float, r: float, flat_top: bool = True) -> List[Pt]:
    """Regular hexagon."""
    offset = math.pi / 6 if flat_top else 0
    return [(cx + r * math.cos(i * math.pi / 3 + offset),
             cy + r * math.sin(i * math.pi / 3 + offset))
            for i in range(6)]


# ---------------------------------------------------------------------------
# Polygon Construction Helpers
# ---------------------------------------------------------------------------

def make_poly_from_angles(angles_deg: List[float], edge_len: float = 1.0) -> List[Pt]:
    """Build polygon from interior angles (degrees) with unit edge length."""
    pts: List[Pt] = [(0.0, 0.0)]
    heading = 0.0
    for angle in angles_deg[:-1]:  # Last vertex closes to first
        exterior = 180.0 - angle
        heading += math.radians(exterior)
        x = pts[-1][0] + edge_len * math.cos(heading)
        y = pts[-1][1] + edge_len * math.sin(heading)
        pts.append((x, y))
    return pts


def offset_polyline_strip(pts: Polyline, half_width: float) -> List[Pt]:
    """Create a closed polygon strip from a polyline by offsetting both sides."""
    if len(pts) < 2:
        return list(pts)

    left: List[Pt] = []
    right: List[Pt] = []

    for i, (x, y) in enumerate(pts):
        # Compute tangent direction
        if i == 0:
            dx, dy = pts[1][0] - x, pts[1][1] - y
        elif i == len(pts) - 1:
            dx, dy = x - pts[-2][0], y - pts[-2][1]
        else:
            dx = pts[i + 1][0] - pts[i - 1][0]
            dy = pts[i + 1][1] - pts[i - 1][1]

        length = math.hypot(dx, dy)
        if length < 1e-9:
            nx, ny = 0.0, 1.0
        else:
            nx, ny = -dy / length, dx / length

        left.append((x + nx * half_width, y + ny * half_width))
        right.append((x - nx * half_width, y - ny * half_width))

    # Combine: left forward, right backward
    return left + right[::-1]


# ---------------------------------------------------------------------------
# Bezier Curve Helpers
# ---------------------------------------------------------------------------

def cubic_bezier_point(p0: Pt, p1: Pt, p2: Pt, p3: Pt, t: float) -> Pt:
    """Evaluate cubic Bezier at parameter t."""
    u = 1 - t
    return (
        u**3 * p0[0] + 3*u**2*t * p1[0] + 3*u*t**2 * p2[0] + t**3 * p3[0],
        u**3 * p0[1] + 3*u**2*t * p1[1] + 3*u*t**2 * p2[1] + t**3 * p3[1],
    )


def cubic_bezier_tangent(p0: Pt, p1: Pt, p2: Pt, p3: Pt, t: float) -> Pt:
    """Tangent vector of cubic Bezier at t (unnormalized)."""
    u = 1 - t
    return (
        3 * (u**2 * (p1[0] - p0[0]) + 2*u*t * (p2[0] - p1[0]) + t**2 * (p3[0] - p2[0])),
        3 * (u**2 * (p1[1] - p0[1]) + 2*u*t * (p2[1] - p1[1]) + t**2 * (p3[1] - p2[1])),
    )


def sample_bezier(p0: Pt, p1: Pt, p2: Pt, p3: Pt, n_pts: int = 50) -> List[Pt]:
    """Sample cubic Bezier curve as polyline."""
    return [cubic_bezier_point(p0, p1, p2, p3, i / n_pts) for i in range(n_pts + 1)]


def catmull_rom_segment(p0: Pt, p1: Pt, p2: Pt, p3: Pt,
                        n_pts: int, tau: float = 0.5) -> List[Pt]:
    """Sample one segment of Catmull-Rom spline."""
    pts: List[Pt] = []
    for i in range(n_pts):
        t = i / n_pts
        t2, t3 = t * t, t * t * t

        x = tau * (
            (2 * p1[0]) +
            (-p0[0] + p2[0]) * t +
            (2*p0[0] - 5*p1[0] + 4*p2[0] - p3[0]) * t2 +
            (-p0[0] + 3*p1[0] - 3*p2[0] + p3[0]) * t3
        )
        y = tau * (
            (2 * p1[1]) +
            (-p0[1] + p2[1]) * t +
            (2*p0[1] - 5*p1[1] + 4*p2[1] - p3[1]) * t2 +
            (-p0[1] + 3*p1[1] - 3*p2[1] + p3[1]) * t3
        )
        pts.append((x, y))
    return pts


def sample_spline(control_pts: Polyline, density: int = 100) -> List[Pt]:
    """Sample Catmull-Rom spline through control points."""
    if len(control_pts) < 4:
        return list(control_pts)

    pts_per_seg = max(2, density // (len(control_pts) - 1))
    result: List[Pt] = []

    for i in range(len(control_pts) - 3):
        seg = catmull_rom_segment(
            control_pts[i], control_pts[i+1],
            control_pts[i+2], control_pts[i+3],
            pts_per_seg
        )
        result.extend(seg)

    result.append(control_pts[-2])
    return result


# ---------------------------------------------------------------------------
# Backbone/Centerline Generators
# ---------------------------------------------------------------------------

def straight_backbone(length: float, n_pts: int = 50) -> Polyline:
    """Straight horizontal backbone."""
    return [(i * length / n_pts, 0) for i in range(n_pts + 1)]


def sine_backbone(length: float, amplitude: float, frequency: float = 1.0,
                  n_pts: int = 50) -> Polyline:
    """Sinusoidal backbone."""
    return [(i * length / n_pts,
             amplitude * math.sin(2 * math.pi * frequency * i / n_pts))
            for i in range(n_pts + 1)]


def s_wave_backbone(length: float, amplitude: float, n_pts: int = 50) -> Polyline:
    """S-curve backbone (half sine)."""
    return [(i * length / n_pts,
             amplitude * math.sin(math.pi * i / n_pts))
            for i in range(n_pts + 1)]


def bezier_backbone(p0: Pt, p1: Pt, p2: Pt, p3: Pt, n_pts: int = 50) -> Polyline:
    """Cubic Bezier backbone."""
    return sample_bezier(p0, p1, p2, p3, n_pts)


# ---------------------------------------------------------------------------
# Material/Style Helpers
# ---------------------------------------------------------------------------

def checkerboard_material(row: int, col: int, n_materials: int = 2) -> int:
    """Checkerboard material assignment."""
    return (row + col) % n_materials


def row_stripe_material(row: int, col: int, n_materials: int = 2) -> int:
    """Row-based stripe material."""
    return row % n_materials


def radial_material(index: int, n_materials: int = 2) -> int:
    """Radial alternating material."""
    return index % n_materials
