#!/usr/bin/env python3
"""
Generate a parametric Spanish Ladder rosette DXF + SVG.

Ported from: spanish-ladder-rosette.jsx

Unlike the static 23×15 grid in generate_spanish_rosette.py, this generator
builds the ladder grid PARAMETRICALLY from configurable strip widths:

    buildLadderGrid({numPairs, blackWidth, whiteWidth, sectionRows,
                     numSections, hasBorder, hasRung, hasOuterAccent})

Grid values: 0=black, 1=white, 2=accent, 3=border-black.

Veneer species defaults (from JSX):
    Ebony:    0.6mm, #1a1008
    Maple:    0.6mm, #f5efe0
    Rosewood: 0.6mm, #8b4513
    Holly:    0.6mm, #f0f0e8

Accent color presets: Green, Red, Gold, Blue, White, Purple.

Usage:
    python -m app.cam.rosette.prototypes.spanish_ladder_parametric
"""

import math
import os
from pathlib import Path

# ── Ring dimensions (mm) ──────────────────────────────────────────
SOUNDHOLE_R = 40.8
INNER_R     = 41.8
OUTER_R     = 47.8
EBONY_INNER = 47.8
EBONY_OUTER = 49.3
GREEN_INNER = 49.3
GREEN_OUTER = 50.8

# ── Veneer material database ──────────────────────────────────────
VENEER_DEFAULTS = {
    "ebony":    {"thickness_mm": 0.6, "fill": "#1a1008", "label": "Black (Ebony)"},
    "maple":    {"thickness_mm": 0.6, "fill": "#f5efe0", "label": "White (Maple)"},
    "rosewood": {"thickness_mm": 0.6, "fill": "#8b4513", "label": "Rosewood"},
    "holly":    {"thickness_mm": 0.6, "fill": "#f0f0e8", "label": "Holly"},
}

ACCENT_PRESETS = [
    {"name": "Green",  "fill": "#2d6a4f"},
    {"name": "Red",    "fill": "#8b2020"},
    {"name": "Gold",   "fill": "#c8920a"},
    {"name": "Blue",   "fill": "#1e3f7a"},
    {"name": "White",  "fill": "#f0e8d0"},
    {"name": "Purple", "fill": "#4a1a6a"},
]

# ── Default ladder parameters ─────────────────────────────────────
NUM_PAIRS       = 6     # B/W column pairs
BLACK_WIDTH     = 2     # columns per black strip
WHITE_WIDTH     = 2     # columns per white strip
SECTION_ROWS    = 3     # rows of B/W stripes per section
NUM_SECTIONS    = 4     # number of ladder sections
HAS_BORDER      = True  # solid black border rows at top & bottom
HAS_RUNG        = True  # accent row between sections
HAS_OUTER_ACCENT = True # accent row just inside border

COLOR_MAP = {
    0: ("LADDER_BLACK",  250),
    1: ("LADDER_WHITE",   51),
    2: ("LADDER_ACCENT",   3),
    3: ("LADDER_BORDER", 250),
}

_SVG_FILL = {0: "#1a1008", 1: "#f5efe0", 2: "#2d6a4f", 3: "#1a1008"}


# ── Grid builder ──────────────────────────────────────────────────

def build_ladder_grid(
    num_pairs: int = NUM_PAIRS,
    black_width: int = BLACK_WIDTH,
    white_width: int = WHITE_WIDTH,
    section_rows: int = SECTION_ROWS,
    num_sections: int = NUM_SECTIONS,
    has_border: bool = HAS_BORDER,
    has_rung: bool = HAS_RUNG,
    has_outer_accent: bool = HAS_OUTER_ACCENT,
) -> list[list[int]]:
    """
    Build a parametric ladder rosette grid.

    Row types are determined first, then each row is filled with the
    appropriate column pattern.
    """
    row_types: list[str] = []

    if has_border:
        row_types.append("border")
    if has_outer_accent:
        row_types.append("accent")

    for s in range(num_sections):
        if s > 0 and has_rung:
            row_types.append("accent")
        for _ in range(section_rows):
            row_types.append("stripe")

    if has_outer_accent:
        row_types.append("accent")
    if has_border:
        row_types.append("border")

    total_cols = num_pairs * (black_width + white_width)

    # Build one stripe row pattern
    stripe_row: list[int] = []
    for _ in range(num_pairs):
        stripe_row.extend([0] * black_width)
        stripe_row.extend([1] * white_width)

    grid: list[list[int]] = []
    for rtype in row_types:
        if rtype == "stripe":
            grid.append(list(stripe_row))
        elif rtype == "accent":
            grid.append([2] * total_cols)
        elif rtype == "border":
            grid.append([3] * total_cols)
        else:
            grid.append([0] * total_cols)

    return grid


# ── Tile-cell geometry ────────────────────────────────────────────

def _build_cells(
    grid: list[list[int]], inner_r: float, outer_r: float, repeats: int,
) -> list[tuple[int, list[tuple[float, float]]]]:
    cols = len(grid[0])
    rows = len(grid)
    total_cols = cols * repeats
    angle_step = 2 * math.pi / total_cols
    radial_step = (outer_r - inner_r) / rows

    cells: list[tuple[int, list[tuple[float, float]]]] = []
    for rep in range(repeats):
        for c in range(cols):
            col_idx = rep * cols + c
            a0 = col_idx * angle_step
            a1 = (col_idx + 1) * angle_step
            for r in range(rows):
                r0 = inner_r + r * radial_step
                r1 = inner_r + (r + 1) * radial_step
                quad = [
                    (r0 * math.cos(a0), r0 * math.sin(a0)),
                    (r1 * math.cos(a0), r1 * math.sin(a0)),
                    (r1 * math.cos(a1), r1 * math.sin(a1)),
                    (r0 * math.cos(a1), r0 * math.sin(a1)),
                ]
                cells.append((grid[r][c], quad))
    return cells


# ── Tile repeats ──────────────────────────────────────────────────

def _calc_repeats(grid: list[list[int]]) -> int:
    cols = len(grid[0])
    avg_circ = math.pi * (INNER_R + OUTER_R)
    return max(1, round(avg_circ / (cols * 0.5)))


# ── DXF helpers ───────────────────────────────────────────────────

def _dxf_circle(layer: str, cx: float, cy: float, radius: float) -> list[str]:
    return ["0", "CIRCLE", "8", layer, "10", f"{cx:.6f}", "20", f"{cy:.6f}", "40", f"{radius:.6f}"]


def _dxf_closed_poly(layer: str, pts: list[tuple[float, float]]) -> list[str]:
    lines = ["0", "POLYLINE", "8", layer, "66", "1", "70", "1"]
    for x, y in pts:
        lines += ["0", "VERTEX", "8", layer, "10", f"{x:.6f}", "20", f"{y:.6f}"]
    lines += ["0", "SEQEND"]
    return lines


def build_dxf(grid: list[list[int]]) -> str:
    repeats = _calc_repeats(grid)
    lines: list[str] = [
        "0", "SECTION", "2", "HEADER",
        "9", "$ACADVER", "1", "AC1009",
        "9", "$INSUNITS", "70", "4",
        "0", "ENDSEC",
    ]
    struct_layers = [
        ("SOUNDHOLE", 7), ("INNER_BORDER", 8), ("PATTERN_ZONE", 5),
        ("EBONY_RING", 250), ("GREEN_RING", 3),
    ]
    all_layers = list(struct_layers)
    for _, (lname, aci) in COLOR_MAP.items():
        all_layers.append((lname, aci))

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

    cells = _build_cells(grid, INNER_R, OUTER_R, repeats)
    for color_val, quad in cells:
        lname = COLOR_MAP[color_val][0]
        lines += _dxf_closed_poly(lname, quad)

    lines += ["0", "ENDSEC", "0", "EOF"]
    return "\n".join(lines)


# ── SVG export ────────────────────────────────────────────────────

def build_svg(grid: list[list[int]]) -> str:
    repeats = _calc_repeats(grid)
    pad = 5
    vb = GREEN_OUTER + pad
    parts: list[str] = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{-vb} {-vb} {2*vb} {2*vb}" '
        f'width="{2*vb}mm" height="{2*vb}mm">',
        "<title>Spanish Ladder Rosette (Parametric)</title>",
        "<desc>Generated by The Production Shop</desc>",
        f'<circle cx="0" cy="0" r="{OUTER_R}" fill="#1a1008"/>',
        f'<circle cx="0" cy="0" r="{INNER_R}" fill="#0e0b07"/>',
    ]
    cells = _build_cells(grid, INNER_R, OUTER_R, repeats)
    for color_val, quad in cells:
        fill = _SVG_FILL.get(color_val, "#1a1008")
        pts = " ".join(f"{x:.3f},{y:.3f}" for x, y in quad)
        parts.append(f'<polygon points="{pts}" fill="{fill}" stroke="{fill}" stroke-width="0.02"/>')
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
    grid = build_ladder_grid()
    cols = len(grid[0])
    rows = len(grid)
    repeats = _calc_repeats(grid)
    out_dir = Path(os.environ.get("ROSETTE_OUT", Path(__file__).resolve().parent.parent.parent.parent.parent.parent / "docs"))

    dxf_path = out_dir / "spanish_ladder_parametric.dxf"
    dxf_content = build_dxf(grid)
    dxf_path.write_text(dxf_content, encoding="utf-8")
    print(f"DXF saved: {dxf_path}  ({dxf_content.count(chr(10)) + 1} lines)")

    svg_path = out_dir / "spanish_ladder_parametric.svg"
    svg_content = build_svg(grid)
    svg_path.write_text(svg_content, encoding="utf-8")
    print(f"SVG saved: {svg_path}")

    counts = {0: 0, 1: 0, 2: 0, 3: 0}
    for row in grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    total = cols * rows
    print(f"\nSpanish Ladder Rosette (Parametric)")
    print(f"  Grid: {cols}×{rows}  ({cols*0.5}×{rows*0.5} mm tile)")
    print(f"  Pairs: {NUM_PAIRS} × ({BLACK_WIDTH}B + {WHITE_WIDTH}W)")
    print(f"  Sections: {NUM_SECTIONS} × {SECTION_ROWS} rows")
    print(f"  Border: {HAS_BORDER}  Rung: {HAS_RUNG}  Outer accent: {HAS_OUTER_ACCENT}")
    print(f"  Black: {counts[0]}  White: {counts[1]}  Accent: {counts[2]}  Border: {counts[3]}")
    print(f"  Total cells: {total}")
    print(f"  Tile repeats: {repeats}×")


if __name__ == "__main__":
    main()
