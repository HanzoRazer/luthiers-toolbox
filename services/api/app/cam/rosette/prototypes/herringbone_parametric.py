#!/usr/bin/env python3
"""
Generate a Parametric Herringbone rosette DXF + SVG.

Ported from: rosette-grid-designer-v4-mothership.jsx (ParametricCanvas)

Two modes:

1. PARAMETRIC — generates herringbone tooth quads from parameters:
   Lattice vectors:   a = (2w, 0),  b = (w, 2h)
   Position:          p(i,j) = center + i·a + j·b
   Rotation parity:   θ(i,j) = +θ if (i+j)%2==0, else −θ
   Each tooth is a rotated rectangle [±w/2, ±h/2].
   Quads are clipped to the annulus (rIn, rOut).

2. EMBEDDED DXF — uses the 1,198 tile quads (596 dark + 602 light)
   extracted from the original parquet_herringbone_rosette.dxf file
   that are embedded in the mothership JSX. These are the exact
   manufactured tile geometries in mm coordinates.

Ring definitions (from DXF_RINGS):
   Soundhole:     r = 0 → 40.8mm
   Inner Border:  r = 40.8 → 41.8mm
   Pattern Zone:  r = 41.8 → 47.8mm  (this is where tiles go)
   Ebony Ring:    r = 47.8 → 49.3mm
   Green Ring:    r = 49.3 → 50.8mm

Usage:
    python -m app.cam.rosette.prototypes.herringbone_parametric
"""

import math
import os
from pathlib import Path

# ── Ring dimensions (mm)  — from DXF_RINGS in mothership ─────────
SOUNDHOLE_R = 40.8
INNER_R     = 41.8
OUTER_R     = 47.8
EBONY_INNER = 47.8
EBONY_OUTER = 49.3
GREEN_INNER = 49.3
GREEN_OUTER = 50.8

DXF_RINGS = [
    {"name": "Soundhole",    "rIn": 0,     "rOut": 40.8},
    {"name": "Inner Border", "rIn": 40.8,  "rOut": 41.8},
    {"name": "Pattern Zone", "rIn": 41.8,  "rOut": 47.8},
    {"name": "Ebony Ring",   "rIn": 47.8,  "rOut": 49.3},
    {"name": "Green Ring",   "rIn": 49.3,  "rOut": 50.8},
]

# ── Default herringbone parameters ────────────────────────────────
THETA    = 45.0    # rotation angle (degrees)
TOOTH_W  = 1.0     # tooth width (mm)
TOOTH_H  = 2.0     # tooth height (mm)

# Parity colors
DARK_COLOR  = "#1a1008"
LIGHT_COLOR = "#f0e8d0"


# ── Presets from mothership (complete with grid, colWidths, BOM) ──
PRESETS = {
    "spanish": {
        "name": "Spanish Right-Angle",
        "subtitle": "Classical · Tile Section",
        "cols": 23, "rows": 15, "colors": [0, 1, 2],
        "col_widths": [1, 1, 2, 3, 4, 5, 6, 7, 8, 9, 9, 8, 7, 6, 5, 4, 3, 2, 1, 1],
        "bom": [
            {"label": "Strip A", "items": "12 Black · 4 White"},
            {"label": "Strip B", "items": "14 Black · 6 White"},
        ],
        "note": "Build as rod billet, sliced crosswise. 23×15 @ 0.5mm = 11.5×7.5mm.",
        "grid": [
            [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
            [0,0,0,1,1,0,0,0,0,0,1,1,0,1,1,0,0,0,0,0,1,1,0],
            [0,0,1,1,0,0,0,0,0,1,1,0,0,0,1,1,0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
            [0,1,1,0,0,0,0,0,0,0,1,0,0,0,1,0,0,0,0,0,0,1,0],
            [1,1,0,0,0,1,1,0,0,2,2,0,0,0,2,2,0,0,1,1,0,0,0],
            [0,0,0,1,1,0,0,0,2,2,0,0,0,0,0,2,2,0,0,0,1,1,0],
            [0,0,0,0,0,0,0,2,2,2,1,2,2,2,2,1,2,2,2,0,0,0,0],
            [0,0,0,0,1,0,2,2,1,1,1,1,2,1,1,1,1,2,2,0,1,0,0],
            [0,0,0,0,0,0,0,2,2,2,1,2,2,2,2,1,2,2,2,0,0,0,0],
            [0,0,0,1,1,0,0,0,2,2,0,0,0,0,0,2,2,0,0,0,1,1,0],
            [1,1,0,0,0,1,1,0,0,2,2,0,0,0,2,2,0,0,1,1,0,0,0],
            [0,1,1,0,0,0,0,0,0,0,1,0,0,0,1,0,0,0,0,0,0,1,0],
            [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
            [0,0,0,1,1,0,0,0,0,0,1,1,0,1,1,0,0,0,0,0,1,1,0],
        ],
    },
    "rope": {
        "name": "Rope Rosette",
        "subtitle": "Diagonal Staircase",
        "cols": 7, "rows": 5, "colors": [0, 1],
        "col_widths": [1, 2, 2, 1, 3, 4, 5, 4, 3],
        "bom": [
            {"label": "Total Black", "items": "23 strips"},
            {"label": "Total White", "items": "12 strips"},
        ],
        "note": "Diagonal staircase creates rope illusion. Mirror alternate tiles for full twist.",
        "grid": [
            [0,0,0,0,0,1,1],
            [0,0,0,0,1,1,0],
            [0,0,0,1,1,0,0],
            [0,0,1,1,0,0,1],
            [0,1,1,0,0,1,0],
        ],
    },
    "wave": {
        "name": "Wave Tile",
        "subtitle": "Wave Motif · Red Accent",
        "cols": 9, "rows": 8, "colors": [0, 1, 3],
        "col_widths": [1, 2, 3, 4, 5, 6, 7, 8],
        "bom": [
            {"label": "White", "items": "-> count table"},
            {"label": "Black", "items": "-> count table"},
            {"label": "Red", "items": "-> count table"},
        ],
        "note": "Rows 6-8 reconstructed from partial photo. Verify before cutting.",
        "grid": [
            [0,0,0,0,0,0,1,1,3],
            [0,0,0,0,0,1,1,3,3],
            [0,0,0,0,1,1,3,3,0],
            [0,0,0,1,1,3,3,0,0],
            [0,0,1,1,0,0,0,0,0],
            [0,1,1,0,0,0,0,0,0],
            [1,1,0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0,3,3],
        ],
    },
}


def compute_bom_strip_widths(preset_key: str) -> list[dict]:
    """
    Compute BOM strip widths from preset col_widths.

    col_widths are in half-mm units. Each entry represents the width
    of one column strip in the tile.  Returns a list of dicts with
    'col_index', 'half_mm', and 'mm' for each strip.
    """
    preset = PRESETS.get(preset_key)
    if preset is None:
        raise ValueError(f"Unknown preset: {preset_key}")
    widths = preset.get("col_widths", [])
    return [
        {"col_index": i, "half_mm": w, "mm": w * 0.5}
        for i, w in enumerate(widths)
    ]


def simulate_build_and_cnc(
    preset_key: str,
    *,
    strip_thickness_mm: float = 0.6,
    strip_length_mm: float = 200.0,
    chip_length_mm: float = 2.0,
    tool_diameter_mm: float = 1.5,
    stepover_pct: float = 0.4,
    stepdown_mm: float = 0.3,
    feed_xy_mm_min: float = 600.0,
    plunge_f_mm_min: float = 150.0,
    rapid_f_mm_min: float = 3000.0,
    safe_z_mm: float = 5.0,
    cut_depth_mm: float = 1.2,
    spindle_rpm: float = 12000.0,
) -> dict:
    """
    Simulate the full build pipeline: billet assembly → CNC channel routing.

    Phase 1 — Billet Assembly (from col_widths):
        Each col_widths entry is a strip width (half-mm units).
        Strips are cut, laminated face-to-face, pressed, then sliced
        crosswise into 'chips' of chip_length_mm thickness.

    Phase 2 — CNC Channel Routing:
        Concentric-ring toolpath cuts the annular rosette channel.
        Uses rosette_cam_bridge.plan_rosette_toolpath() for move
        planning and feedtime.estimate_time() for cycle estimate.

    Returns dict with:
        preset:           preset metadata
        billet:           strip dimensions, lamination order, chip yield
        cnc:              toolpath stats, estimated cycle time
        material_summary: total veneer area and waste estimate
    """
    preset = PRESETS.get(preset_key)
    if preset is None:
        raise ValueError(f"Unknown preset: {preset_key}")

    col_widths = preset.get("col_widths", [])
    cols = preset["cols"]
    rows = preset["rows"]

    # ── Phase 1: Billet Assembly ──────────────────────────────────
    strips = []
    total_strip_area_mm2 = 0.0
    for i, half_mm in enumerate(col_widths):
        width_mm = half_mm * 0.5
        area = width_mm * strip_length_mm
        total_strip_area_mm2 += area
        strips.append({
            "col_index": i,
            "width_mm": round(width_mm, 2),
            "thickness_mm": strip_thickness_mm,
            "length_mm": strip_length_mm,
            "area_mm2": round(area, 2),
        })

    billet_width_mm = sum(s["width_mm"] for s in strips)
    billet_height_mm = rows * strip_thickness_mm
    chips_per_billet = max(1, int(strip_length_mm / chip_length_mm))

    billet = {
        "strip_count": len(strips),
        "strips": strips,
        "billet_width_mm": round(billet_width_mm, 2),
        "billet_height_mm": round(billet_height_mm, 2),
        "billet_length_mm": strip_length_mm,
        "chip_length_mm": chip_length_mm,
        "chips_per_billet": chips_per_billet,
        "lamination_steps": [
            f"1. Cut {len(strips)} strips per col_widths",
            f"2. Laminate face-to-face ({rows} rows × {cols} cols pattern)",
            f"3. Press and cure (min 4 hours)",
            f"4. Slice crosswise at {chip_length_mm}mm intervals → {chips_per_billet} chips",
            f"5. Arrange chips around annulus ({INNER_R}–{OUTER_R} mm)",
        ],
    }

    # ── Phase 2: CNC Channel Routing ─────────────────────────────
    # Use rosette_cam_bridge for toolpath planning
    from app.services.rosette_cam_bridge import (
        RosetteGeometry,
        CamParams,
        plan_rosette_toolpath,
    )
    from app.cam.feedtime import estimate_time

    geom = RosetteGeometry(
        center_x_mm=0.0,
        center_y_mm=0.0,
        inner_radius_mm=INNER_R,
        outer_radius_mm=OUTER_R,
    )
    cam = CamParams(
        tool_diameter_mm=tool_diameter_mm,
        stepover_pct=stepover_pct,
        stepdown_mm=stepdown_mm,
        feed_xy_mm_min=feed_xy_mm_min,
        safe_z_mm=safe_z_mm,
        cut_depth_mm=cut_depth_mm,
    )

    moves, stats = plan_rosette_toolpath(geom, cam)
    cycle_time_s = estimate_time(
        moves,
        feed_xy=feed_xy_mm_min,
        plunge_f=plunge_f_mm_min,
        rapid_f=rapid_f_mm_min,
    )

    cnc = {
        "tool_diameter_mm": tool_diameter_mm,
        "stepover_pct": stepover_pct,
        "stepdown_mm": stepdown_mm,
        "feed_xy_mm_min": feed_xy_mm_min,
        "plunge_f_mm_min": plunge_f_mm_min,
        "spindle_rpm": spindle_rpm,
        "cut_depth_mm": cut_depth_mm,
        "radial_rings": stats["rings"],
        "z_passes": stats["z_passes"],
        "total_path_length_mm": stats["length_mm"],
        "move_count": stats["move_count"],
        "estimated_cycle_time_s": round(cycle_time_s, 1),
        "estimated_cycle_time_min": round(cycle_time_s / 60.0, 1),
    }

    # ── Material Summary ──────────────────────────────────────────
    annulus_area_mm2 = math.pi * (OUTER_R**2 - INNER_R**2)
    waste_pct = 15.0

    material_summary = {
        "total_strip_area_mm2": round(total_strip_area_mm2, 1),
        "annulus_area_mm2": round(annulus_area_mm2, 1),
        "waste_allowance_pct": waste_pct,
        "adjusted_area_mm2": round(total_strip_area_mm2 * (1.0 + waste_pct / 100.0), 1),
        "bom_entries": preset.get("bom", []),
    }

    return {
        "preset": {
            "key": preset_key,
            "name": preset["name"],
            "cols": cols,
            "rows": rows,
            "note": preset.get("note", ""),
        },
        "billet": billet,
        "cnc": cnc,
        "material_summary": material_summary,
    }

# Named wave presets from v3-patched
WAVE_PRESETS = {
    "torres_ramirez": {
        "label": "Torres / Ramirez",
        "A": 6, "segLen": 18, "gap": 2, "skew": 0.72, "chase": 13,
        "d": 4, "strandW": 1.8, "numStrands": 7, "cols": 52, "rows": 18,
        "colorMode": "tri",
    },
    "gentle_swell": {
        "label": "Gentle Swell",
        "A": 4, "segLen": 22, "gap": 3, "skew": 0.55, "chase": 12,
        "d": 5, "strandW": 2, "numStrands": 6, "cols": 52, "rows": 18,
        "colorMode": "bw",
    },
    "tight_crash": {
        "label": "Tight Crash",
        "A": 8, "segLen": 14, "gap": 2, "skew": 0.82, "chase": 11,
        "d": 4, "strandW": 1.5, "numStrands": 8, "cols": 52, "rows": 18,
        "colorMode": "tri",
    },
}


# ── Parametric herringbone generator ──────────────────────────────

def generate_herringbone_quads(
    theta_deg: float = THETA,
    w: float = TOOTH_W,
    h: float = TOOTH_H,
    r_in: float = INNER_R,
    r_out: float = OUTER_R,
) -> list[tuple[int, list[tuple[float, float]]]]:
    """
    Generate herringbone tooth quads within the annulus.

    Returns list of (parity, [(x,y) × 4]) where parity 0=dark, 1=light.

    Lattice:
        a = (2w, 0)        — horizontal spacing
        b = (w, 2h)        — brick-offset diagonal

    Each tooth at (i,j) gets rotation:
        θ  if (i+j) % 2 == 0
       −θ  if (i+j) % 2 == 1
    """
    rad = math.radians(theta_deg)
    ax, ay = 2 * w, 0
    bx, by = w, 2 * h

    # How many steps we need to cover the annulus
    max_r = r_out + max(w, h) * 2
    steps = int(math.ceil(max_r / min(w, h))) + 6

    quads: list[tuple[int, list[tuple[float, float]]]] = []

    for i in range(-steps, steps + 1):
        for j in range(-steps, steps + 1):
            # Lattice position
            px = i * ax + j * bx
            py = j * by

            # Quick distance check
            dist = math.sqrt(px * px + py * py)
            if dist > r_out + max(w, h):
                continue
            if dist < r_in - max(w, h):
                continue

            # Parity-based rotation
            parity = (i + j) % 2
            t_angle = rad if parity == 0 else -rad
            cos_t = math.cos(t_angle)
            sin_t = math.sin(t_angle)

            # Tooth corners (local)
            corners = [(w / 2, h / 2), (w / 2, -h / 2), (-w / 2, -h / 2), (-w / 2, h / 2)]
            pts = [(px + lx * cos_t - ly * sin_t, py + lx * sin_t + ly * cos_t) for lx, ly in corners]

            # Check if any corner is within annulus
            any_in = any(r_in <= math.sqrt(x * x + y * y) <= r_out for x, y in pts)
            if not any_in:
                continue

            quads.append((parity, pts))

    return quads


# ── DXF helpers ───────────────────────────────────────────────────

def _dxf_circle(layer: str, cx: float, cy: float, radius: float) -> list[str]:
    return ["0", "CIRCLE", "8", layer, "10", f"{cx:.6f}", "20", f"{cy:.6f}", "40", f"{radius:.6f}"]


def _dxf_closed_poly(layer: str, pts: list[tuple[float, float]]) -> list[str]:
    lines = ["0", "POLYLINE", "8", layer, "66", "1", "70", "1"]
    for x, y in pts:
        lines += ["0", "VERTEX", "8", layer, "10", f"{x:.6f}", "20", f"{y:.6f}"]
    lines += ["0", "SEQEND"]
    return lines


def build_dxf(quads: list[tuple[int, list[tuple[float, float]]]]) -> str:
    lines: list[str] = [
        "0", "SECTION", "2", "HEADER",
        "9", "$ACADVER", "1", "AC1009",
        "9", "$INSUNITS", "70", "4",
        "0", "ENDSEC",
    ]
    all_layers = [
        ("SOUNDHOLE", 7), ("INNER_BORDER", 8), ("PATTERN_ZONE", 5),
        ("EBONY_RING", 250), ("GREEN_RING", 3),
        ("HERRING_DARK", 250), ("HERRING_LIGHT", 51),
    ]

    lines += ["0", "SECTION", "2", "TABLES", "0", "TABLE", "2", "LAYER"]
    for lname, aci in all_layers:
        lines += ["0", "LAYER", "2", lname, "70", "0", "62", str(aci), "6", "CONTINUOUS"]
    lines += ["0", "ENDTAB", "0", "ENDSEC"]

    lines += ["0", "SECTION", "2", "ENTITIES"]
    lines += _dxf_circle("SOUNDHOLE", 0, 0, SOUNDHOLE_R)
    lines += _dxf_circle("INNER_BORDER", 0, 0, SOUNDHOLE_R)
    lines += _dxf_circle("INNER_BORDER", 0, 0, INNER_R)
    lines += _dxf_circle("PATTERN_ZONE", 0, 0, INNER_R)
    lines += _dxf_circle("PATTERN_ZONE", 0, 0, OUTER_R)
    lines += _dxf_circle("EBONY_RING", 0, 0, EBONY_INNER)
    lines += _dxf_circle("EBONY_RING", 0, 0, EBONY_OUTER)
    lines += _dxf_circle("GREEN_RING", 0, 0, GREEN_INNER)
    lines += _dxf_circle("GREEN_RING", 0, 0, GREEN_OUTER)

    for parity, pts in quads:
        layer = "HERRING_DARK" if parity == 0 else "HERRING_LIGHT"
        lines += _dxf_closed_poly(layer, pts)

    lines += ["0", "ENDSEC", "0", "EOF"]
    return "\n".join(lines)


# ── SVG export ────────────────────────────────────────────────────

def build_svg(quads: list[tuple[int, list[tuple[float, float]]]]) -> str:
    pad = 5
    vb = GREEN_OUTER + pad
    parts: list[str] = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{-vb} {-vb} {2*vb} {2*vb}" '
        f'width="{2*vb}mm" height="{2*vb}mm">',
        "<title>Parametric Herringbone Rosette</title>",
        "<desc>Generated by The Production Shop</desc>",
        # Annulus clip path
        '<defs>'
        f'<clipPath id="annulus">'
        f'<path d="M{OUTER_R},0 A{OUTER_R},{OUTER_R} 0 1,1 -{OUTER_R},0 '
        f'A{OUTER_R},{OUTER_R} 0 1,1 {OUTER_R},0 Z '
        f'M{INNER_R},0 A{INNER_R},{INNER_R} 0 1,0 -{INNER_R},0 '
        f'A{INNER_R},{INNER_R} 0 1,0 {INNER_R},0 Z" fill-rule="evenodd"/>'
        f'</clipPath></defs>',
        f'<circle cx="0" cy="0" r="{OUTER_R}" fill="#1a1008"/>',
        f'<circle cx="0" cy="0" r="{INNER_R}" fill="#0e0b07"/>',
        '<g clip-path="url(#annulus)">',
    ]

    for parity, pts in quads:
        fill = DARK_COLOR if parity == 0 else LIGHT_COLOR
        pts_str = " ".join(f"{x:.3f},{y:.3f}" for x, y in pts)
        parts.append(f'<polygon points="{pts_str}" fill="{fill}" stroke="rgba(90,60,20,0.3)" stroke-width="0.05"/>')

    parts.append("</g>")
    parts += [
        f'<circle cx="0" cy="0" r="{SOUNDHOLE_R}" fill="#0e0b07" stroke="#3a2e1a" stroke-width="0.3"/>',
        f'<circle cx="0" cy="0" r="{INNER_R}" fill="none" stroke="#3a2e1a" stroke-width="0.3"/>',
        f'<circle cx="0" cy="0" r="{OUTER_R}" fill="none" stroke="#c8a032" stroke-width="0.3"/>',
        f'<circle cx="0" cy="0" r="{EBONY_OUTER}" fill="none" stroke="#1a1008" stroke-width="1.5"/>',
        f'<circle cx="0" cy="0" r="{GREEN_OUTER}" fill="none" stroke="#2d6a4f" stroke-width="1.5"/>',
        "</svg>",
    ]
    return "\n".join(parts)


# ── Main ──────────────────────────────────────────────────────────

def main() -> None:
    import sys

    theta = THETA
    w = TOOTH_W
    h = TOOTH_H
    mode = "parametric"  # "parametric" or "embedded"
    simulate_preset = None  # set to preset key for build/CNC simulation

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--theta" and i + 1 < len(args):
            theta = float(args[i + 1])
            i += 2
        elif args[i] == "--width" and i + 1 < len(args):
            w = float(args[i + 1])
            i += 2
        elif args[i] == "--height" and i + 1 < len(args):
            h = float(args[i + 1])
            i += 2
        elif args[i] == "--embedded":
            mode = "embedded"
            i += 1
        elif args[i] == "--simulate" and i + 1 < len(args):
            simulate_preset = args[i + 1]
            i += 2
        else:
            i += 1

    # ── Simulate build + CNC run ──────────────────────────────────
    if simulate_preset is not None:
        import json
        result = simulate_build_and_cnc(simulate_preset)
        print(json.dumps(result, indent=2))
        return

    if mode == "embedded":
        from app.cam.rosette.prototypes.herringbone_embedded_quads import get_embedded_quads
        quads = get_embedded_quads()
        label = "Embedded DXF"
    else:
        quads = generate_herringbone_quads(theta, w, h)
        label = f"Parametric (w={w}, h={h}, theta={theta})"

    out_dir = Path(os.environ.get("ROSETTE_OUT", Path(__file__).resolve().parent.parent.parent.parent.parent.parent / "docs"))

    dxf_path = out_dir / "herringbone_parametric.dxf"
    dxf_content = build_dxf(quads)
    dxf_path.write_text(dxf_content, encoding="utf-8")
    print(f"DXF saved: {dxf_path}  ({dxf_content.count(chr(10)) + 1} lines)")

    svg_path = out_dir / "herringbone_parametric.svg"
    svg_content = build_svg(quads)
    svg_path.write_text(svg_content, encoding="utf-8")
    print(f"SVG saved: {svg_path}")

    dark_count = sum(1 for p, _ in quads if p == 0)
    light_count = sum(1 for p, _ in quads if p == 1)
    print(f"\nHerringbone Rosette ({label})")
    print(f"  Annulus: {INNER_R}-{OUTER_R} mm")
    print(f"  Dark tiles: {dark_count}")
    print(f"  Light tiles: {light_count}")
    print(f"  Total quads: {len(quads)}")


if __name__ == "__main__":
    main()
