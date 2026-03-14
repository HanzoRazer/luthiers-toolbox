"""
Inlay Pattern Generators — Engine-Based Architecture

This module provides a unified registry for all inlay patterns,
delegating to four core engines:
- GridEngine: Tile repetition on 2D grids
- RadialEngine: N-fold patterns around a center
- PathEngine: Patterns along backbone curves
- MedallionEngine: Concentric layered patterns

Each generator is a pure function: (params: dict) → GeometryCollection
All coordinates in mm.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List

from .inlay_geometry import (
    GeometryCollection,
    GeometryElement,
    Polyline,
    Pt,
    tessellate_path_d,
)
from .inlay_engines import (
    GridEngine,
    MedallionEngine,
    PathEngine,
    RadialEngine,
)


# ---------------------------------------------------------------------------
# Celtic Motif — SVG library (special case, not engine-based)
# ---------------------------------------------------------------------------

_CELTIC_MOTIFS: Dict[str, Dict[str, Any]] = {
    "lotus": {
        "name": "Lotus Flower",
        "vb_w": 1000, "vb_h": 1000,
        "recommend_mm": 18,
        "use_case": "Fret dot, headstock logo",  # SCOPE_ALLOW: HOST_GEOMETRY descriptive use-case
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
        "use_case": "Headstock, body inlay",  # SCOPE_ALLOW: HOST_GEOMETRY descriptive use-case
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

    vb_max = max(vb_w, vb_h, 1)
    sf = scale_mm / vb_max

    elements: List[GeometryElement] = []
    for d_str in svg_paths:
        sub_paths = tessellate_path_d(d_str, tol=0.5)
        for sp in sub_paths:
            if len(sp) < 2:
                continue
            scaled: List[Pt] = [(x * sf, y * sf) for x, y in sp]
            closed = math.hypot(
                scaled[-1][0] - scaled[0][0],
                scaled[-1][1] - scaled[0][1],
            ) < 0.5
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
# Band Presets
# ---------------------------------------------------------------------------

BAND_PRESETS: Dict[str, Dict[str, Any]] = {
    "rosette": {
        "layers": [
            {"shape": "herringbone", "params": {"tooth_w": 6, "tooth_h": 12}, "weight": 1},
            {"shape": "diamond", "params": {"tile_w": 8, "tile_h": 14}, "weight": 1},
        ],
        "band_width_mm": 120, "band_height_mm": 18, "gap_mm": 0.5,
    },
    "body_binding": {
        "layers": [
            {"shape": "checker_chevron", "params": {"cell_w": 8}, "weight": 1},
        ],
        "band_width_mm": 150, "band_height_mm": 10, "gap_mm": 0.3,
    },
    "fretboard": {
        "layers": [
            {"shape": "greek_key", "params": {"cell_size": 5}, "weight": 1},
        ],
        "band_width_mm": 50, "band_height_mm": 8, "gap_mm": 0.2,
    },
    "headstock_band": {  # SCOPE_ALLOW: HOST_GEOMETRY preset name for inlay placement
        "layers": [
            {"shape": "vine_scroll", "params": {"leafsize": 4, "leaves": 5}, "weight": 1},
        ],
        "band_width_mm": 80, "band_height_mm": 12, "gap_mm": 0.4,
    },
}


def compose_band(params: Dict[str, Any]) -> GeometryCollection:
    """Stack multiple inlay patterns into a composite band.

    Params
    ------
    preset         : str   — preset name (rosette/body_binding/fretboard/headstock_band)  # SCOPE_ALLOW: HOST_GEOMETRY
    layers         : list  — layer dicts: [{shape, params, weight}, ...]
    band_width_mm  : float — total width (mm), default 150
    band_height_mm : float — total height (mm), default 25
    gap_mm         : float — gap between layers (mm), default 0.5
    repeats        : int   — horizontal repeats, default 1
    mirror         : bool  — mirror alternate tiles, default False
    """
    preset_name = params.get("preset")
    base: Dict[str, Any] = {}
    if preset_name and preset_name in BAND_PRESETS:
        base = dict(BAND_PRESETS[preset_name])
    base.update({k: v for k, v in params.items() if k != "preset"})

    layers_spec = base.get("layers", [])
    if not layers_spec:
        layers_spec = [
            {"shape": "herringbone", "params": {}, "weight": 1},
            {"shape": "diamond", "params": {}, "weight": 1},
        ]

    band_w = float(base.get("band_width_mm", 150))
    band_h = float(base.get("band_height_mm", 25))
    gap_mm = float(base.get("gap_mm", 0.5))
    repeats = max(1, int(base.get("repeats", 1)))
    mirror = bool(base.get("mirror", False))

    total_weight = sum(float(layer.get("weight", 1)) for layer in layers_spec)
    total_gap = gap_mm * max(0, len(layers_spec) - 1)
    usable_h = band_h - total_gap

    tile_w = band_w / repeats
    elements: List[GeometryElement] = []
    y_cursor = 0.0

    for li, layer_def in enumerate(layers_spec):
        weight = float(layer_def.get("weight", 1))
        layer_h = usable_h * weight / total_weight
        shape_key = layer_def.get("shape", "herringbone")
        layer_params = dict(layer_def.get("params", {}))

        gen_entry = INLAY_GENERATORS.get(shape_key)
        if gen_entry is None:
            continue
        layer_geo = gen_entry["fn"](layer_params)

        if layer_geo.width_mm > 0 and layer_geo.height_mm > 0:
            sx = tile_w / layer_geo.width_mm
            sy = layer_h / layer_geo.height_mm
        else:
            sx, sy = 1.0, 1.0

        for rep in range(repeats):
            rep_ox = rep * tile_w
            flip_x = mirror and rep % 2 == 1

            for el in layer_geo.elements:
                new_pts: List[Pt] = []
                for px, py in el.points:
                    nx = px * sx
                    ny = py * sy + y_cursor
                    if flip_x:
                        nx = tile_w - nx
                    nx += rep_ox
                    new_pts.append((nx, ny))
                elements.append(GeometryElement(
                    kind=el.kind, points=new_pts,
                    radius=el.radius * min(sx, sy),
                    material_index=el.material_index,
                    stroke_width=el.stroke_width,
                ))

        y_cursor += layer_h

        if li < len(layers_spec) - 1 and gap_mm > 0:
            gap_rect_pts: List[Pt] = [(0, y_cursor), (band_w, y_cursor + gap_mm)]
            elements.append(GeometryElement(
                kind="rect", points=gap_rect_pts,
                material_index=1, stroke_width=0.1,
            ))
            y_cursor += gap_mm

    return GeometryCollection(
        elements=elements,
        width_mm=band_w,
        height_mm=band_h,
        radial=False,
    )


# ---------------------------------------------------------------------------
# Tile Repeat Utility
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
# Generator Registry — Maps pattern names to engine methods
# ---------------------------------------------------------------------------

INLAY_GENERATORS: Dict[str, Any] = {
    # Grid-based patterns
    "herringbone": {
        "fn": GridEngine.herringbone,
        "name": "Herringbone",
        "description": "Alternating rectangular tiles (parquet pattern)",
        "linear": True,
    },
    "diamond": {
        "fn": GridEngine.diamond,
        "name": "Diamond Wave",
        "description": "Wave/lean diamond marquetry tiles",
        "linear": True,
    },
    "greek_key": {
        "fn": GridEngine.greek_key,
        "name": "Greek Key",
        "description": "Greek key / meander border pattern",
        "linear": True,
    },
    "checker_chevron": {
        "fn": GridEngine.checker_chevron,
        "name": "Checker Chevron",
        "description": "Diamond grid with alternating material slots",
        "linear": True,
    },
    "hex_chain": {
        "fn": GridEngine.hex_chain,
        "name": "Hex Chain",
        "description": "Vertical hex chain band pattern with cutouts and connectors",
        "linear": True,
    },
    "chevron_panel": {
        "fn": GridEngine.chevron_panel,
        "name": "Chevron Panel",
        "description": "Nested chevron band pattern",
        "linear": True,
    },
    "nested_diamond": {
        "fn": GridEngine.nested_diamond,
        "name": "Nested Diamond",
        "description": "Band of nested diamond groups with corner accents",
        "linear": True,
    },
    "block_pin": {
        "fn": GridEngine.block_pin,
        "name": "Block-Pin Column",
        "description": "Alternating columns of diamond accents and rectangular pins",
        "linear": True,
    },

    # Radial patterns
    "spiral": {
        "fn": RadialEngine.spiral,
        "name": "Archimedean Spiral",
        "description": "Archimedean spiral with true normal-vector CNC offsets",
        "linear": False,
    },
    "sunburst": {
        "fn": RadialEngine.sunburst,
        "name": "Sunburst",
        "description": "Wedge rays between inner and outer radii",
        "linear": False,
    },
    "feather": {
        "fn": RadialEngine.feather,
        "name": "Feather Fan",
        "description": "Layered fan blade pattern",
        "linear": False,
    },
    "amsterdam_flower": {
        "fn": RadialEngine.amsterdam_flower,
        "name": "Amsterdam Flower",
        "description": "N-fold kite-petal medallion with centre disc",
        "linear": False,
    },
    "spiro_arc": {
        "fn": RadialEngine.spiro_arc,
        "name": "Spiro Arc Medallion",
        "description": "Spirograph-style overlapping thick arc segments",
        "linear": False,
    },
    "sq_floral": {
        "fn": RadialEngine.sq_floral,
        "name": "Square Floral",
        "description": "Radial ring of narrow kite-shaped petals",
        "linear": False,
    },
    "open_flower_oval": {
        "fn": RadialEngine.open_flower_oval,
        "name": "Open Flower Oval",
        "description": "Hook/comma petals around elliptical frame with pip accents",
        "linear": False,
    },

    # Path-based patterns
    "vine_scroll": {
        "fn": PathEngine.vine_scroll,
        "name": "Vine Scroll",
        "description": "Parametric freq-modulated vine with teardrop leaves",
        "linear": False,
    },
    "floral_spray": {
        "fn": PathEngine.floral_spray,
        "name": "Floral Spray",
        "description": "Cubic Bézier stem with tangent-following lens petals",
        "linear": False,
    },
    "binding_flow": {
        "fn": PathEngine.binding_flow,
        "name": "Binding Flow",
        "description": "Catmull-Rom contour with vine wrapping for binding channels",
        "linear": False,
    },
    "rope_border_motif": {
        "fn": PathEngine.rope_border_motif,
        "name": "Rope Border Motif",
        "description": "Static S-curve interleaving rope border band",
        "linear": True,
    },
    "twisted_rope": {
        "fn": PathEngine.twisted_rope,
        "name": "Twisted Rope",
        "description": "Parametric N-strand twisted rope with crossing detection",
        "linear": False,
    },

    # Medallion patterns
    "oak_medallion": {
        "fn": MedallionEngine.oak_medallion,
        "name": "Oak Medallion",
        "description": "N-fold kite ring medallion with concentric layers",
        "linear": False,
    },
    "girih_rosette": {
        "fn": MedallionEngine.girih_rosette,
        "name": "Girih Rosette",
        "description": "Five-tile Islamic geometry rosette",
        "linear": False,
    },
    "parquet_panel": {
        "fn": MedallionEngine.parquet_panel,
        "name": "Parquet Panel",
        "description": "Concentric diamond panel with radiating wedges",
        "linear": False,
    },

    # Special patterns (not engine-based)
    "celtic_motif": {
        "fn": celtic_motif,
        "name": "Celtic Motif",
        "description": "SVG motif library (lotus, celtic cross, triquetra, etc.)",
        "linear": False,
    },
    "compose_band": {
        "fn": compose_band,
        "name": "Band Compositor",
        "description": "Multi-layer composite band stacking multiple patterns",
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


# ---------------------------------------------------------------------------
# Re-export backward-compatible function signatures
# ---------------------------------------------------------------------------

def herringbone(params: Dict[str, Any]) -> GeometryCollection:
    """Alternating rectangular tile pattern."""
    return GridEngine.herringbone(params)


def diamond(params: Dict[str, Any]) -> GeometryCollection:
    """Wave/lean diamond marquetry."""
    return GridEngine.diamond(params)


def greek_key(params: Dict[str, Any]) -> GeometryCollection:
    """Greek key / meander border."""
    return GridEngine.greek_key(params)


def spiral(params: Dict[str, Any]) -> GeometryCollection:
    """Archimedean spiral with optional symmetry arms."""
    return RadialEngine.spiral(params)


def sunburst(params: Dict[str, Any]) -> GeometryCollection:
    """Sunburst wedge rays between inner and outer radii."""
    return RadialEngine.sunburst(params)


def feather(params: Dict[str, Any]) -> GeometryCollection:
    """Layered feather fan blades."""
    return RadialEngine.feather(params)


def vine_scroll(params: Dict[str, Any]) -> GeometryCollection:
    """Parametric vine scroll with alternating teardrop leaves."""
    return PathEngine.vine_scroll(params)


def girih_rosette(params: Dict[str, Any]) -> GeometryCollection:
    """Five-tile Girih rosette (Islamic geometry)."""
    return MedallionEngine.girih_rosette(params)


def binding_flow(params: Dict[str, Any]) -> GeometryCollection:
    """Catmull-Rom contour with vine wrapping."""
    return PathEngine.binding_flow(params)


def checker_chevron(params: Dict[str, Any]) -> GeometryCollection:
    """Diamond grid with alternating material slots."""
    return GridEngine.checker_chevron(params)


def block_pin(params: Dict[str, Any]) -> GeometryCollection:
    """Alternating columns of diamond accents and rectangular pins."""
    return GridEngine.block_pin(params)


def amsterdam_flower(params: Dict[str, Any]) -> GeometryCollection:
    """N-fold kite-petal medallion with centre disc."""
    return RadialEngine.amsterdam_flower(params)


def spiro_arc(params: Dict[str, Any]) -> GeometryCollection:
    """Spirograph-style overlapping thick arc medallion."""
    return RadialEngine.spiro_arc(params)


def sq_floral(params: Dict[str, Any]) -> GeometryCollection:
    """Radial ring of narrow kite petals."""
    return RadialEngine.sq_floral(params)


def oak_medallion(params: Dict[str, Any]) -> GeometryCollection:
    """N-fold kite-ring medallion with concentric layers."""
    return MedallionEngine.oak_medallion(params)


def floral_spray(params: Dict[str, Any]) -> GeometryCollection:
    """Cubic Bézier stem with tangent-following lens petals."""
    return PathEngine.floral_spray(params)


def open_flower_oval(params: Dict[str, Any]) -> GeometryCollection:
    """N hook/comma petals arranged radially around an elliptical frame."""
    return RadialEngine.open_flower_oval(params)


def hex_chain(params: Dict[str, Any]) -> GeometryCollection:
    """Vertical hex chain band pattern."""
    return GridEngine.hex_chain(params)


def chevron_panel(params: Dict[str, Any]) -> GeometryCollection:
    """Nested chevron band pattern."""
    return GridEngine.chevron_panel(params)


def parquet_panel(params: Dict[str, Any]) -> GeometryCollection:
    """Parquet diamond panel with concentric layers."""
    return MedallionEngine.parquet_panel(params)


def nested_diamond(params: Dict[str, Any]) -> GeometryCollection:
    """Band of nested diamond groups with corner accents."""
    return GridEngine.nested_diamond(params)


def rope_border_motif(params: Dict[str, Any]) -> GeometryCollection:
    """Static rope border motif — interleaving S-curve strands."""
    return PathEngine.rope_border_motif(params)


def twisted_rope(params: Dict[str, Any]) -> GeometryCollection:
    """Parametric twisted rope inlay band."""
    return PathEngine.twisted_rope(params)
