"""
Inlay Pattern Generators — Six Pure-Function Generators

Ported from the V1/V2/V3 React prototypes.  Each generator is a pure function:
    (params: dict) → GeometryCollection

All coordinates in mm.  Generators are stateless, deterministic, and
language-agnostic (the math is the source of truth).

Shapes
------
1. herringbone  — alternating rectangular tiles (linear, tileable)
2. diamond      — wave/lean diamond marquetry (linear, tileable)
3. greek_key    — meander border pattern (linear, tileable)
4. spiral       — Archimedean spiral with true normal-vector offsets (radial)
5. sunburst     — wedge rays between inner/outer radii (radial)
6. feather      — layered fan blades (radial)
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Tuple

from .inlay_geometry import (
    GeometryCollection,
    GeometryElement,
    Pt,
    offset_polyline,
)


# ---------------------------------------------------------------------------
# 1. Herringbone
# ---------------------------------------------------------------------------

def herringbone(params: Dict[str, Any]) -> GeometryCollection:
    """Alternating rectangular tile pattern.

    Params
    ------
    tooth_w : float  — tile width (mm), default 10
    tooth_h : float  — tile height (mm), default 20
    band_w  : float  — total band width (mm), default 120
    band_h  : float  — total band height (mm), default 22
    """
    tw = float(params.get("tooth_w", 10))
    th = float(params.get("tooth_h", 20))
    band_w = float(params.get("band_w", 120))
    band_h = float(params.get("band_h", 22))

    cols = math.ceil(band_w / tw) + 1
    rows = math.ceil(band_h / th) + 1

    elements: List[GeometryElement] = []
    for row in range(rows):
        for col in range(cols):
            mi = (row + col) % 2
            vert = mi == 0
            w = tw if vert else th
            h = th if vert else tw
            cx = col * tw + tw / 2
            cy = row * th + th / 2
            x0, y0 = cx - w / 2, cy - h / 2
            elements.append(GeometryElement(
                kind="rect",
                points=[(x0, y0), (x0 + w, y0 + h)],
                material_index=mi,
                stroke_width=0.25,
            ))

    return GeometryCollection(
        elements=elements,
        width_mm=band_w,
        height_mm=band_h,
        radial=False,
        tile_w=tw * 2,
        tile_h=th,
    )


# ---------------------------------------------------------------------------
# 2. Diamond
# ---------------------------------------------------------------------------

def diamond(params: Dict[str, Any]) -> GeometryCollection:
    """Wave/lean diamond marquetry.

    Params
    ------
    tile_w : float  — diamond tile width (mm), default 14
    tile_h : float  — diamond tile height (mm), default 22
    wave   : float  — vertical wave factor 0–1, default 0.35
    lean   : float  — horizontal lean factor 0–1, default 0.1
    band_w : float  — total band width (mm), default 120
    band_h : float  — total band height (mm), default 22
    """
    tw = float(params.get("tile_w", 14))
    th = float(params.get("tile_h", 22))
    wave = float(params.get("wave", 0.35))
    lean = float(params.get("lean", 0.1))
    band_w = float(params.get("band_w", 120))
    band_h = float(params.get("band_h", 22))

    cols = math.ceil(band_w / tw) + 1
    rows = math.ceil(band_h / th) + 1

    elements: List[GeometryElement] = []
    for row in range(rows):
        for col in range(cols):
            cx = col * tw + tw / 2
            cy = row * th + th / 2
            dy = wave * th * 0.4 * math.sin((col * 0.5 + row * 0.3) * math.pi)
            lx = lean * tw * 0.3
            pts: List[Pt] = [
                (cx + lx, cy - th / 2 + dy),
                (cx + tw / 2, cy + dy),
                (cx + lx, cy + th / 2 + dy),
                (cx - tw / 2, cy + dy),
            ]
            elements.append(GeometryElement(
                kind="polygon",
                points=pts,
                material_index=(row + col) % 2,
                stroke_width=0.25,
            ))

    return GeometryCollection(
        elements=elements,
        width_mm=band_w,
        height_mm=band_h,
        radial=False,
        tile_w=tw,
        tile_h=th,
    )


# ---------------------------------------------------------------------------
# 3. Greek Key
# ---------------------------------------------------------------------------

def greek_key(params: Dict[str, Any]) -> GeometryCollection:
    """Greek key / meander border.

    Params
    ------
    cell_size  : float — unit cell dimension (mm), default 10
    key_width  : float — stroke width of the meander (mm), default 1.2
    band_w     : float — total band width (mm), default 120
    band_h     : float — total band height (mm), default 22
    """
    cs = float(params.get("cell_size", 10))
    kw = float(params.get("key_width", 1.2))
    band_w = float(params.get("band_w", 120))
    band_h = float(params.get("band_h", 22))

    uw = cs * 4
    uh = cs * 4
    cols = math.ceil(band_w / uw) + 1
    rows = math.ceil(band_h / uh) + 1

    elements: List[GeometryElement] = []
    for row in range(rows):
        for col in range(cols):
            ox = col * uw
            oy = row * uh
            # Meander key outline as a closed polygon
            pts: List[Pt] = [
                (ox, oy),
                (ox + cs * 3, oy),
                (ox + cs * 3, oy + cs * 3),
                (ox + cs, oy + cs * 3),
                (ox + cs, oy + cs),
                (ox + cs * 2, oy + cs),
                (ox + cs * 2, oy + cs * 2),
                (ox, oy + cs * 2),
            ]
            elements.append(GeometryElement(
                kind="polygon",
                points=pts,
                material_index=0,
                stroke_width=kw,
            ))

    return GeometryCollection(
        elements=elements,
        width_mm=band_w,
        height_mm=band_h,
        radial=False,
        tile_w=uw,
        tile_h=uh,
    )


# ---------------------------------------------------------------------------
# 4. Spiral (Archimedean) — with true normal-vector offset paths
# ---------------------------------------------------------------------------

def spiral(params: Dict[str, Any]) -> GeometryCollection:
    """Archimedean spiral with optional symmetry arms.

    Params
    ------
    arm_dist   : float — distance between arms (mm), default 12
    circles    : float — number of full turns, default 3
    thickness  : float — arm thickness / stroke width (mm), default 1.5
    sym_count  : int   — rotational symmetry copies, default 1
    point_dist : float — spacing between sample points (mm), default 0.25
    """
    arm_dist = float(params.get("arm_dist", 12))
    circles = float(params.get("circles", 3))
    thickness = float(params.get("thickness", 1.5))
    sym_count = int(params.get("sym_count", 1))
    point_dist = float(params.get("point_dist", 0.25))

    b = arm_dist / 360.0
    angle_step = point_dist / b if b > 0 else 1.0
    max_pts = min(2000, int(circles * 360 / angle_step))

    base_pts: List[Pt] = []
    theta = 0.0
    for _ in range(max_pts):
        theta += angle_step
        r = b * theta
        rad = theta * math.pi / 180.0
        base_pts.append((r * math.cos(rad), r * math.sin(rad)))

    max_r = b * circles * 360
    elements: List[GeometryElement] = []

    for s in range(sym_count):
        ang = s * 360.0 / sym_count * math.pi / 180.0
        ca, sa = math.cos(ang), math.sin(ang)
        flip = s % 2 == 1 and sym_count > 1

        rotated: List[Pt] = []
        for px, py in base_pts:
            fy = -py if flip else py
            rotated.append((px * ca - fy * sa, px * sa + fy * ca))

        # Centre polyline
        elements.append(GeometryElement(
            kind="polyline",
            points=rotated,
            material_index=s % 2,
            stroke_width=thickness,
        ))

    return GeometryCollection(
        elements=elements,
        width_mm=max_r * 2,
        height_mm=max_r * 2,
        origin_x=max_r,
        origin_y=max_r,
        radial=True,
    )


# ---------------------------------------------------------------------------
# 5. Sunburst
# ---------------------------------------------------------------------------

def sunburst(params: Dict[str, Any]) -> GeometryCollection:
    """Sunburst wedge rays between inner and outer radii.

    Params
    ------
    rays       : int   — number of ray wedges, default 16
    inner_frac : float — inner radius as fraction of band_r, default 0.22
    outer_frac : float — outer radius as fraction of band_r, default 0.92
    alt_rays   : bool  — alternate wide/narrow rays, default True
    twist      : float — rotation offset in degrees, default 0
    band_r     : float — overall radius (mm), default 55
    """
    rays = int(params.get("rays", 16))
    inner_frac = float(params.get("inner_frac", 0.22))
    outer_frac = float(params.get("outer_frac", 0.92))
    alt_rays = bool(params.get("alt_rays", True))
    twist = float(params.get("twist", 0))
    band_r = float(params.get("band_r", 55))

    o_r = outer_frac * band_r
    i_r = inner_frac * band_r
    a_step = math.pi * 2 / rays

    elements: List[GeometryElement] = []
    for r_idx in range(rays):
        a0 = r_idx * a_step + twist * math.pi / 180.0
        w = 0.56 if (alt_rays and r_idx % 2 == 0) else 0.44
        a1 = a0 + a_step * w

        pts: List[Pt] = []
        # Outer arc
        for i in range(11):
            t = a0 + (a1 - a0) * i / 10
            pts.append((math.cos(t) * o_r, math.sin(t) * o_r))
        # Inner arc (reversed)
        for i in range(10, -1, -1):
            t = a0 + (a1 - a0) * i / 10
            pts.append((math.cos(t) * i_r, math.sin(t) * i_r))

        elements.append(GeometryElement(
            kind="polygon",
            points=pts,
            material_index=r_idx % 3,
            stroke_width=0.25,
        ))

    # Inner circle
    elements.append(GeometryElement(
        kind="circle",
        points=[(0.0, 0.0)],
        radius=i_r,
        material_index=2,
        stroke_width=0.3,
    ))

    return GeometryCollection(
        elements=elements,
        width_mm=o_r * 2,
        height_mm=o_r * 2,
        origin_x=o_r,
        origin_y=o_r,
        radial=True,
    )


# ---------------------------------------------------------------------------
# 6. Feather Fan
# ---------------------------------------------------------------------------

def feather(params: Dict[str, Any]) -> GeometryCollection:
    """Layered feather fan blades.

    Params
    ------
    blades  : int   — blades per layer, default 14
    layers  : int   — number of concentric layers, default 2
    spread  : float — angular spread in degrees, default 270
    taper   : float — inner-to-outer radius taper 0–1, default 0.42
    band_r  : float — overall radius (mm), default 55
    """
    blades = int(params.get("blades", 14))
    layers = int(params.get("layers", 2))
    spread = float(params.get("spread", 270))
    taper = float(params.get("taper", 0.42))
    band_r = float(params.get("band_r", 55))

    elements: List[GeometryElement] = []
    for layer in range(layers - 1, -1, -1):
        o_r = band_r * (1 - (layer / layers) * 0.65)
        i_r = o_r * (1 - taper * 0.8)
        a_step = spread * math.pi / 180.0 / blades
        base_a = -spread * 0.5 * math.pi / 180.0 + layer * (
            spread * 0.5 * math.pi / 180.0 / layers
        )

        for b_idx in range(blades):
            a0 = base_a + b_idx * a_step
            a1 = a0 + a_step * 0.9

            pts: List[Pt] = []
            # Outer arc
            for i in range(13):
                t = a0 + (a1 - a0) * i / 12
                pts.append((math.cos(t) * o_r, math.sin(t) * o_r))
            # Inner arc (reversed)
            for i in range(12, -1, -1):
                t = a0 + (a1 - a0) * i / 12
                pts.append((math.cos(t) * i_r, math.sin(t) * i_r))

            elements.append(GeometryElement(
                kind="polygon",
                points=pts,
                material_index=(b_idx + layer) % 3,
                stroke_width=0.2,
            ))

    return GeometryCollection(
        elements=elements,
        width_mm=band_r * 2,
        height_mm=band_r * 2,
        origin_x=band_r,
        origin_y=band_r,
        radial=True,
    )


# ---------------------------------------------------------------------------
# Tile repeat engine (for linear patterns)
# ---------------------------------------------------------------------------

def apply_tile(
    geo: GeometryCollection,
    target_w: float,
    target_h: float,
) -> GeometryCollection:
    """Tile a linear pattern to fill *target_w* x *target_h* mm.

    Only operates on non-radial patterns that have tile dimensions.
    Returns *geo* unchanged otherwise.
    """
    if geo.radial or not geo.tile_w or not geo.tile_h:
        return geo

    nx = math.ceil(target_w / geo.tile_w)
    ny = math.ceil(target_h / geo.tile_h)

    tiled: List[GeometryElement] = []
    for ty in range(ny):
        for tx in range(nx):
            dx = tx * geo.tile_w
            dy = ty * geo.tile_h
            for el in geo.elements:
                new_pts = [(x + dx, y + dy) for x, y in el.points]
                tiled.append(GeometryElement(
                    kind=el.kind,
                    points=new_pts,
                    radius=el.radius,
                    material_index=el.material_index,
                    stroke_width=el.stroke_width,
                ))

    return GeometryCollection(
        elements=tiled,
        width_mm=target_w,
        height_mm=target_h,
        radial=False,
        tile_w=geo.tile_w,
        tile_h=geo.tile_h,
    )


# ---------------------------------------------------------------------------
# Generator registry integration
# ---------------------------------------------------------------------------

INLAY_GENERATORS: Dict[str, Any] = {
    "herringbone": {
        "fn": herringbone,
        "name": "Herringbone",
        "description": "Alternating rectangular tiles (parquet pattern)",
        "linear": True,
    },
    "diamond": {
        "fn": diamond,
        "name": "Diamond Wave",
        "description": "Wave/lean diamond marquetry tiles",
        "linear": True,
    },
    "greek_key": {
        "fn": greek_key,
        "name": "Greek Key",
        "description": "Greek key / meander border pattern",
        "linear": True,
    },
    "spiral": {
        "fn": spiral,
        "name": "Archimedean Spiral",
        "description": "Archimedean spiral with true normal-vector CNC offsets",
        "linear": False,
    },
    "sunburst": {
        "fn": sunburst,
        "name": "Sunburst",
        "description": "Wedge rays between inner and outer radii",
        "linear": False,
    },
    "feather": {
        "fn": feather,
        "name": "Feather Fan",
        "description": "Layered fan blade pattern",
        "linear": False,
    },
}


def generate_inlay_pattern(
    shape: str,
    params: Dict[str, Any],
) -> GeometryCollection:
    """Top-level dispatcher — generate a pattern by shape key.

    Raises ValueError for unknown shape.
    """
    entry = INLAY_GENERATORS.get(shape)
    if entry is None:
        raise ValueError(
            f"Unknown inlay shape: {shape!r}.  "
            f"Available: {', '.join(INLAY_GENERATORS)}"
        )
    return entry["fn"](params)
