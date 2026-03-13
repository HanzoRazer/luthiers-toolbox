"""
Inlay Geometry Primitives & Offset Engine

Provides GeometryCollection (the intermediate representation for all inlay
pattern generators) and the normal-vector offset engine ported from the V3
spiral prototype.

All coordinates in mm.  Positive offset = outward / male, negative = inward / pocket.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Tuple

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
# Offset engine — ported from V3 prototype normal-vector math
# ---------------------------------------------------------------------------

def _normalize(x: float, y: float) -> Tuple[float, float]:
    length = math.hypot(x, y) or 1.0
    return x / length, y / length


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
        # Normal = rotate tangent 90° CCW
        nx, ny = -ty, tx
        result.append((pts[i][0] + nx * dist, pts[i][1] + ny * dist))
    return result


def offset_polygon(pts: Polyline, dist: float) -> Polyline:
    """Offset a *closed* polygon by ``dist`` mm using vertex normals.

    Wraps neighbours at polygon seam so the first/last vertices are
    handled correctly.  Positive = outward (for CCW winding).
    """
    n = len(pts)
    if n < 3:
        return list(pts)
    result: Polyline = []
    for i in range(n):
        prev = pts[(i - 1) % n]
        nxt = pts[(i + 1) % n]
        tx, ty = _normalize(nxt[0] - prev[0], nxt[1] - prev[1])
        # Right-hand normal (outward for CCW winding)
        nx, ny = ty, -tx
        result.append((pts[i][0] + nx * dist, pts[i][1] + ny * dist))
    return result


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
    "mop":      {"name": "Mother of Pearl", "color": "#ddeef8"},
    "abalone":  {"name": "Abalone",         "color": "#60a880"},
    "ebony":    {"name": "Ebony",           "color": "#1a1008"},
    "maple":    {"name": "Maple",           "color": "#f0e4b8"},
    "rosewood": {"name": "Rosewood",        "color": "#4a1e10"},
    "koa":      {"name": "Koa",             "color": "#c87828"},
    "walnut":   {"name": "Walnut",          "color": "#5c3818"},
    "bone":     {"name": "Bone",            "color": "#f0e8d0"},
    "gold":     {"name": "Brass/Gold",      "color": "#c9a050"},
    "cedar":    {"name": "Cedar",           "color": "#c07040"},
    "red":      {"name": "Dyed Red",        "color": "#8b2020"},
    "blue":     {"name": "Dyed Blue",       "color": "#1e3d7a"},
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
