"""
Inlay Pattern Generators — Ten Pure-Function Generators

Ported from the V1/V2/V3 React prototypes plus Vine/Girih/Celtic HTML
prototypes.  Each generator is a pure function:
    (params: dict) → GeometryCollection

All coordinates in mm.  Generators are stateless, deterministic, and
language-agnostic (the math is the source of truth).

Shapes
------
1. herringbone    — alternating rectangular tiles (linear, tileable)
2. diamond        — wave/lean diamond marquetry (linear, tileable)
3. greek_key      — meander border pattern (linear, tileable)
4. spiral         — Archimedean spiral with true normal-vector offsets (radial)
5. sunburst       — wedge rays between inner/outer radii (radial)
6. feather        — layered fan blades (radial)
7. celtic_motif   — SVG motif library (11 motifs) → tessellated geometry
8. vine_scroll    — freq-modulated sine backbone with teardrop leaves
9. girih_rosette  — 5-tile Girih rosette (Decagon+Pentagon+Rhombus+Bowtie+Hexagon)
10. binding_flow  — Catmull-Rom spline contour with vine wrapping
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Tuple

from .inlay_geometry import (
    GeometryCollection,
    GeometryElement,
    Polyline,
    Pt,
    catmull_rom,
    make_poly,
    offset_polygon,
    offset_polyline,
    offset_polyline_strip,
    sample_spline,
    tessellate_path_d,
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
# 7. Celtic Motif (SVG motif library → tessellated geometry)
# ---------------------------------------------------------------------------

# Built-in motif metadata.  Each entry has:
#   paths: list of SVG path 'd' strings
#   vb_w, vb_h: viewBox dimensions (unitless, for scaling)
#   recommend_mm: suggested physical size
#   name / use_case: descriptive
_CELTIC_MOTIFS: Dict[str, Dict[str, Any]] = {
    "lotus": {
        "name": "Lotus Flower",
        "vb_w": 1000, "vb_h": 1000,
        "recommend_mm": 18,
        "use_case": "Fret dot, headstock logo",
        "paths": [
            "M 443.76,176.41 Q 422.20,114.76 500.00,40.00 Q 577.80,114.76 556.24,176.41 Z",
            "M 573.09,180.92 Q 585.24,116.75 690.00,90.91 Q 720.00,194.56 670.50,237.16 Z",
            "M 682.84,249.50 Q 725.44,200.00 829.09,230.00 Q 803.25,334.76 739.08,346.91 Z",
            "M 743.59,363.76 Q 805.24,342.20 880.00,420.00 Q 805.24,497.80 743.59,476.24 Z",
            "M 739.08,493.09 Q 803.25,505.24 829.09,610.00 Q 725.44,640.00 682.84,590.50 Z",
            "M 670.50,602.84 Q 720.00,645.44 690.00,749.09 Q 585.24,723.25 573.09,659.08 Z",
            "M 556.24,663.59 Q 577.80,725.24 500.00,800.00 Q 422.20,725.24 443.76,663.59 Z",
            "M 426.91,659.08 Q 414.76,723.25 310.00,749.09 Q 280.00,645.44 329.50,602.84 Z",
            "M 317.16,590.50 Q 274.56,640.00 170.91,610.00 Q 196.75,505.24 260.92,493.09 Z",
            "M 256.41,476.24 Q 194.76,497.80 120.00,420.00 Q 194.76,342.20 256.41,363.76 Z",
            "M 260.92,346.91 Q 196.75,334.76 170.91,230.00 Q 274.56,200.00 317.16,249.50 Z",
            "M 329.50,237.16 Q 280.00,194.56 310.00,90.91 Q 414.76,116.75 426.91,180.92 Z",
        ],
    },
    "celtic_cross": {
        "name": "Celtic Cross",
        "vb_w": 544, "vb_h": 548,
        "recommend_mm": 25,
        "use_case": "Headstock, body inlay",
        "paths": [
            "M 269.0 8.0 L 244.0 21.0 L 197.0 26.0 L 190.0 39.0 L 136.0 63.0 L 87.0 105.0 "
            "L 52.0 155.0 L 35.0 203.0 L 21.0 211.0 L 23.0 249.0 L 8.0 273.0 L 23.0 295.0 "
            "L 21.0 329.0 L 35.0 336.0 L 55.0 390.0 L 88.0 436.0 L 143.0 481.0 L 191.0 500.0 "
            "L 198.0 521.0 L 241.0 523.0 L 274.0 539.0 L 301.0 523.0 L 344.0 521.0 L 352.0 499.0 "
            "L 412.0 473.0 L 457.0 433.0 L 487.0 390.0 L 507.0 337.0 L 522.0 329.0 L 519.0 295.0 "
            "L 535.0 270.0 L 519.0 247.0 L 522.0 212.0 L 507.0 203.0 L 485.0 146.0 L 442.0 92.0 "
            "L 397.0 58.0 L 352.0 39.0 L 344.0 25.0 L 303.0 22.0 Z",
        ],
    },
    "triquetra": {
        "name": "Triquetra Knot",
        "vb_w": 604, "vb_h": 545,
        "recommend_mm": 20,
        "use_case": "Fret markers, body",
        "paths": [
            "M 507.0 384.0 L 481.0 356.0 L 469.0 396.0 L 447.0 432.0 L 414.0 465.0 "
            "L 382.0 485.0 L 351.0 496.0 L 323.0 501.0 L 298.0 502.0 L 257.0 497.0 "
            "L 218.0 515.0 L 255.0 528.0 L 301.0 535.0 L 349.0 530.0 L 392.0 516.0 "
            "L 432.0 493.0 L 466.0 462.0 L 490.0 428.0 Z",
        ],
    },
}


def celtic_motif(params: Dict[str, Any]) -> GeometryCollection:
    """Celtic / Floral motif from the built-in SVG library.

    Params
    ------
    motif_id  : str   — key into _CELTIC_MOTIFS, default "lotus"
    scale_mm  : float — target size (largest axis), default uses motif recommend_mm
    svg_paths : list  — optional list of SVG 'd' strings (overrides motif_id)
    material  : int   — material_index for all elements, default 0
    """
    motif_id = str(params.get("motif_id", "lotus"))
    material = int(params.get("material", 0))

    svg_paths: List[str] | None = params.get("svg_paths")
    if svg_paths is not None:
        # Custom SVG paths supplied directly
        vb_w = float(params.get("vb_w", 1000))
        vb_h = float(params.get("vb_h", 1000))
        scale_mm = float(params.get("scale_mm", 20))
    else:
        motif = _CELTIC_MOTIFS.get(motif_id)
        if motif is None:
            raise ValueError(
                f"Unknown motif: {motif_id!r}. "
                f"Available: {', '.join(_CELTIC_MOTIFS)}"
            )
        svg_paths = motif["paths"]
        vb_w = motif["vb_w"]
        vb_h = motif["vb_h"]
        scale_mm = float(params.get("scale_mm", motif["recommend_mm"]))

    # Scale factor: fit the larger viewBox axis to scale_mm
    vb_max = max(vb_w, vb_h, 1)
    sf = scale_mm / vb_max

    elements: List[GeometryElement] = []
    for d_str in svg_paths:
        sub_paths = tessellate_path_d(d_str, tol=0.5)
        for sp in sub_paths:
            if len(sp) < 2:
                continue
            scaled: List[Pt] = [(x * sf, y * sf) for x, y in sp]
            # Detect closed (first ≈ last)
            closed = (
                math.hypot(
                    scaled[-1][0] - scaled[0][0],
                    scaled[-1][1] - scaled[0][1],
                ) < 0.5
            )
            elements.append(GeometryElement(
                kind="polygon" if closed else "polyline",
                points=scaled[:-1] if closed else scaled,
                material_index=material,
                stroke_width=0.25,
            ))

    w_mm = vb_w * sf
    h_mm = vb_h * sf
    return GeometryCollection(
        elements=elements,
        width_mm=w_mm,
        height_mm=h_mm,
        origin_x=w_mm / 2,
        origin_y=h_mm / 2,
        radial=True,
    )


# ---------------------------------------------------------------------------
# 8. Vine Scroll (parametric freq-modulated sine with teardrop leaves)
# ---------------------------------------------------------------------------

def vine_scroll(params: Dict[str, Any]) -> GeometryCollection:
    """Parametric vine scroll with alternating teardrop leaves.

    Params
    ------
    curl      : float — frequency modulation amplitude, default 3.0
    leaves    : int   — number of leaves, default 8
    growth    : float — growth factor 0.5–2, default 1.0
    phase     : float — starting phase offset (radians), default 0
    vwidth    : float — vine stem width (mm), default 1.5
    leafsize  : float — leaf scale (mm), default 6
    length_mm : float — total length of the vine (mm), default 120
    segments  : int   — backbone segments, default 28
    """
    curl = float(params.get("curl", 3.0))
    n_leaves = int(params.get("leaves", 8))
    growth_f = float(params.get("growth", 1.0))
    phase = float(params.get("phase", 0))
    vwidth = float(params.get("vwidth", 1.5))
    leafsize = float(params.get("leafsize", 6))
    length_mm = float(params.get("length_mm", 120))
    segments = int(params.get("segments", 28))

    # Build backbone (freq-modulated sine curve)
    seg_len = length_mm / segments
    backbone: Polyline = [(-length_mm / 2, 0.0)]
    heading = math.pi / 2 + phase
    x, y = backbone[0]
    for i in range(segments):
        step = seg_len * growth_f
        x += math.cos(heading) * step
        y += math.sin(heading) * step
        backbone.append((x, y))
        heading += math.sin(i * 0.38) * curl * 0.4

    elements: List[GeometryElement] = []

    # Stem as dual-rail strip
    stem_strip = offset_polyline_strip(backbone, vwidth / 2)
    elements.append(GeometryElement(
        kind="polygon",
        points=stem_strip,
        material_index=0,
        stroke_width=0.25,
    ))

    # Leaves — teardrop shape at intervals along backbone
    if n_leaves > 0:
        leaf_step = max(1, segments // n_leaves)
    for li in range(n_leaves):
        idx = min((li + 1) * leaf_step, len(backbone) - 2)
        px, py = backbone[idx]
        nx_pt, ny_pt = backbone[min(idx + 1, len(backbone) - 1)]
        tang = math.atan2(ny_pt - py, nx_pt - px)
        side = 1 if li % 2 == 0 else -1
        leaf_angle = tang + side * 1.4

        # Teardrop: base, tip, and two bulge points
        ls = leafsize
        tip = (px + math.cos(leaf_angle) * ls, py + math.sin(leaf_angle) * ls)
        perp = leaf_angle + math.pi / 2
        mid_x = px + math.cos(leaf_angle) * ls * 0.4
        mid_y = py + math.sin(leaf_angle) * ls * 0.4
        bulge = ls * 0.35
        b1 = (mid_x + math.cos(perp) * bulge, mid_y + math.sin(perp) * bulge)
        b2 = (mid_x - math.cos(perp) * bulge, mid_y - math.sin(perp) * bulge)
        leaf_pts: List[Pt] = [(px, py), b1, tip, b2]
        elements.append(GeometryElement(
            kind="polygon",
            points=leaf_pts,
            material_index=1,
            stroke_width=0.2,
        ))

    # Bounding box
    all_x = [p[0] for e in elements for p in e.points]
    all_y = [p[1] for e in elements for p in e.points]
    min_x, max_x = min(all_x, default=0), max(all_x, default=0)
    min_y, max_y = min(all_y, default=0), max(all_y, default=0)
    w = max_x - min_x
    h = max_y - min_y

    return GeometryCollection(
        elements=elements,
        width_mm=w,
        height_mm=h,
        origin_x=-min_x,
        origin_y=-min_y,
        radial=False,
    )


# ---------------------------------------------------------------------------
# 9. Girih Rosette (5-tile Islamic geometry)
# ---------------------------------------------------------------------------

# Girih tile definitions (unit edge = 1)
_GIRIH_TILES: Dict[str, Dict[str, Any]] = {}


def _init_girih_tiles() -> None:
    """Build Girih tile vertex data on first use (lazy)."""
    if _GIRIH_TILES:
        return

    sin_pi10 = math.sin(math.pi / 10)
    sin_pi5 = math.sin(math.pi / 5)

    # Decagon — regular 10-gon, circumradius = 1/(2*sin(π/10))
    r_dec = 1.0 / (2.0 * sin_pi10)
    dec_verts: Polyline = []
    for i in range(10):
        a = 2 * math.pi * i / 10
        dec_verts.append((r_dec * math.cos(a), r_dec * math.sin(a)))
    _GIRIH_TILES["decagon"] = {"verts": dec_verts, "r": r_dec}

    # Pentagon — regular 5-gon
    r_pent = 1.0 / (2.0 * sin_pi5)
    pent_verts: Polyline = []
    for i in range(5):
        a = 2 * math.pi * i / 5
        pent_verts.append((r_pent * math.cos(a), r_pent * math.sin(a)))
    _GIRIH_TILES["pentagon"] = {"verts": pent_verts, "r": r_pent}

    # Hexagon (108, 108, 144, 108, 108, 144)
    _GIRIH_TILES["hexagon"] = {
        "verts": make_poly([108, 108, 144, 108, 108, 144]),
        "r": 0.0,  # computed from verts
    }

    # Rhombus (72, 108, 72, 108)
    _GIRIH_TILES["rhombus"] = {
        "verts": make_poly([72, 108, 72, 108]),
        "r": 0.0,
    }

    # Bowtie — non-convex 6-gon
    _GIRIH_TILES["bowtie"] = {
        "verts": make_poly([72, 72, 216, 72, 72, 216]),
        "r": 0.0,
    }


def _place_tile(
    tile_key: str,
    edge_mm: float,
    cx: float, cy: float,
    rot_deg: float,
    mat_idx: int,
) -> GeometryElement:
    """Place a Girih tile scaled and rotated at (cx, cy)."""
    _init_girih_tiles()
    tile = _GIRIH_TILES[tile_key]
    a = math.radians(rot_deg)
    ca, sa = math.cos(a), math.sin(a)
    pts: List[Pt] = []
    for vx, vy in tile["verts"]:
        sx, sy = vx * edge_mm, vy * edge_mm
        pts.append((cx + sx * ca - sy * sa, cy + sx * sa + sy * ca))
    return GeometryElement(
        kind="polygon", points=pts, material_index=mat_idx, stroke_width=0.25,
    )


def girih_rosette(params: Dict[str, Any]) -> GeometryCollection:
    """Five-tile Girih rosette (Decagon → Pentagon → Rhombus → Bowtie → Hexagon).

    Params
    ------
    edge_mm      : float — tile edge length (mm), default 10
    rotation_deg : float — global rotation (degrees), default 0
    """
    edge_mm = float(params.get("edge_mm", 10))
    rot_deg = float(params.get("rotation_deg", 0))

    _init_girih_tiles()
    sin_pi10 = math.sin(math.pi / 10)
    sin_pi5 = math.sin(math.pi / 5)

    r_dec = edge_mm / (2.0 * sin_pi10)
    r_pent = edge_mm / (2.0 * sin_pi5)

    # Apothem = circumradius * cos(π/n)
    a_dec = r_dec * math.cos(math.pi / 10)
    a_pent = r_pent * math.cos(math.pi / 5)

    elements: List[GeometryElement] = []

    # Layer 0: central decagon
    elements.append(_place_tile("decagon", edge_mm, 0, 0, rot_deg, 0))

    # Layer 1: 10 pentagons around the decagon
    pent_dist = a_dec + a_pent
    for i in range(10):
        a = rot_deg + i * 36
        rad = math.radians(a)
        px = pent_dist * math.cos(rad)
        py = pent_dist * math.sin(rad)
        elements.append(_place_tile("pentagon", edge_mm, px, py, a + 180, 1))

    # Layer 2: 5 rhombuses
    rhomb_dist = pent_dist + r_pent * 0.95
    for i in range(5):
        a = rot_deg + i * 72 + 18
        rad = math.radians(a)
        rx = rhomb_dist * math.cos(rad)
        ry = rhomb_dist * math.sin(rad)
        elements.append(_place_tile("rhombus", edge_mm, rx, ry, a, 2))

    # Layer 3: 5 bowties
    bow_dist = pent_dist + r_pent * 1.4
    for i in range(5):
        a = rot_deg + i * 72 + 54
        rad = math.radians(a)
        bx = bow_dist * math.cos(rad)
        by = bow_dist * math.sin(rad)
        elements.append(_place_tile("bowtie", edge_mm, bx, by, a, 3 % 4))

    # Layer 4: 5 hexagons
    hex_dist = pent_dist + r_pent * 1.1
    for i in range(5):
        a = rot_deg + i * 72
        rad = math.radians(a)
        hx = hex_dist * math.cos(rad)
        hy = hex_dist * math.sin(rad)
        elements.append(_place_tile("hexagon", edge_mm, hx, hy, a + 36, 0))

    # Bounding box
    all_x = [p[0] for e in elements for p in e.points]
    all_y = [p[1] for e in elements for p in e.points]
    r_outer = max(
        max(abs(v) for v in all_x) if all_x else 0,
        max(abs(v) for v in all_y) if all_y else 0,
    )
    size = r_outer * 2

    return GeometryCollection(
        elements=elements,
        width_mm=size,
        height_mm=size,
        origin_x=r_outer,
        origin_y=r_outer,
        radial=True,
    )


# ---------------------------------------------------------------------------
# 10. Binding Flow (Catmull-Rom contour with vine wrapping)
# ---------------------------------------------------------------------------

# Built-in guitar contour (40-point oval approximation, 380 × 280 mm)
_OVAL_CONTOUR: Polyline = []


def _init_oval_contour() -> None:
    if _OVAL_CONTOUR:
        return
    hw, hh = 190.0, 140.0  # half-width, half-height
    n = 40
    for i in range(n):
        a = 2 * math.pi * i / n
        _OVAL_CONTOUR.append((hw * math.cos(a), hh * math.sin(a)))


def binding_flow(params: Dict[str, Any]) -> GeometryCollection:
    """Vine wrapping along a guitar body contour (Catmull-Rom spline).

    Params
    ------
    contour      : list  — optional list of [x,y] points for the body contour
    density      : int   — spline sample density, default 200
    band_width   : float — binding band width (mm), default 3
    leaves       : int   — number of leaves along contour, default 12
    leafsize     : float — leaf scale (mm), default 4
    """
    raw_contour = params.get("contour")
    density = int(params.get("density", 200))
    band_w = float(params.get("band_width", 3))
    n_leaves = int(params.get("leaves", 12))
    leafsize = float(params.get("leafsize", 4))

    if raw_contour and len(raw_contour) >= 4:
        contour: Polyline = [(float(p[0]), float(p[1])) for p in raw_contour]
    else:
        _init_oval_contour()
        contour = list(_OVAL_CONTOUR)

    # Close the contour for spline
    closed_contour = contour + contour[:3]
    sampled = sample_spline(closed_contour, density)

    elements: List[GeometryElement] = []

    # Body outline
    elements.append(GeometryElement(
        kind="polygon",
        points=sampled,
        material_index=0,
        stroke_width=0.3,
    ))

    # Binding strip (outer offset)
    binding_strip = offset_polyline_strip(sampled, band_w / 2)
    elements.append(GeometryElement(
        kind="polygon",
        points=binding_strip,
        material_index=1,
        stroke_width=0.2,
    ))

    # Leaves along contour
    n_pts = len(sampled)
    leaf_step = max(1, n_pts // n_leaves)
    for li in range(n_leaves):
        idx = (li * leaf_step) % n_pts
        px, py = sampled[idx]
        nx_idx = (idx + 1) % n_pts
        nx_pt, ny_pt = sampled[nx_idx]
        tang = math.atan2(ny_pt - py, nx_pt - px)
        # Outward normal
        normal = tang + math.pi / 2
        side = 1 if li % 2 == 0 else -1
        leaf_angle = normal * side

        ls = leafsize
        tip = (
            px + math.cos(leaf_angle) * ls,
            py + math.sin(leaf_angle) * ls,
        )
        perp = leaf_angle + math.pi / 2
        mid_x = px + math.cos(leaf_angle) * ls * 0.4
        mid_y = py + math.sin(leaf_angle) * ls * 0.4
        bulge = ls * 0.3
        b1 = (mid_x + math.cos(perp) * bulge, mid_y + math.sin(perp) * bulge)
        b2 = (mid_x - math.cos(perp) * bulge, mid_y - math.sin(perp) * bulge)
        elements.append(GeometryElement(
            kind="polygon",
            points=[(px, py), b1, tip, b2],
            material_index=2,
            stroke_width=0.2,
        ))

    all_x = [p[0] for e in elements for p in e.points]
    all_y = [p[1] for e in elements for p in e.points]
    min_x, max_x = min(all_x, default=0), max(all_x, default=0)
    min_y, max_y = min(all_y, default=0), max(all_y, default=0)
    w = max_x - min_x
    h = max_y - min_y

    return GeometryCollection(
        elements=elements,
        width_mm=w,
        height_mm=h,
        origin_x=(max_x + min_x) / 2,
        origin_y=(max_y + min_y) / 2,
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
    "celtic_motif": {
        "fn": celtic_motif,
        "name": "Celtic Motif",
        "description": "SVG motif library (lotus, celtic cross, triquetra, etc.)",
        "linear": False,
    },
    "vine_scroll": {
        "fn": vine_scroll,
        "name": "Vine Scroll",
        "description": "Parametric freq-modulated vine with teardrop leaves",
        "linear": False,
    },
    "girih_rosette": {
        "fn": girih_rosette,
        "name": "Girih Rosette",
        "description": "Five-tile Islamic geometry rosette",
        "linear": False,
    },
    "binding_flow": {
        "fn": binding_flow,
        "name": "Binding Flow",
        "description": "Catmull-Rom contour with vine wrapping for binding channels",
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
