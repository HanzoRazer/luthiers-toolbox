"""
Inlay Geometry SVG Module

SVG arc conversion (SVG spec F.6.5-6), path ``d`` tokenizer/tessellator,
and SVG rendering for GeometryCollections.

All coordinates in mm.
"""
from __future__ import annotations

import math
import re
from typing import List, Optional, Tuple

from .inlay_geometry_core import (
    GeometryCollection,
    GeometryElement,
    Polyline,
    Pt,
)
from .inlay_geometry_bezier import subdivide_cubic, subdivide_quadratic
from .inlay_geometry_transforms import offset_polygon, offset_polyline, offset_collection
from .inlay_geometry_bom import MATERIALS, mat_color


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
# SVG rendering helpers
# ---------------------------------------------------------------------------

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
