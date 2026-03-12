#!/usr/bin/env python3
"""
Generate Celtic / Parametric Knot rosettes DXF + SVG + CSV.

Ported from: rosette-grid-designer-v2.jsx, rosette-grid-designer-v4-mothership.jsx

Two generation modes:

1. STATIC TILES — Pre-defined celtic tile grids tiled around the annulus.
   6 tiles (v2 full set): simple4, square8, braid8, step12, tricolor12, rosette16.

2. PARAMETRIC KNOTS — Algorithmic generation using trigonometric formulas:
   - sine:    |sin(2π·i/N)| + |cos(2π·j/N)| > threshold
   - braid:   |sin(2π·(i+j·0.5)/N)| + |cos(2π·(j+i·0.5)/N)| > threshold
   - diamond: |sin(2π·(i-j)/N)| + |sin(2π·(i+j)/N)| > threshold

Grid utilities from mothership:
   - mirror_points(r, c, rows, cols, mode) — H/V/4-way symmetry
   - count_row(grid, row) — per-row material count
   - count_totals(grid) — total material count

Usage:
    python -m app.cam.rosette.prototypes.celtic_parametric_knots
    python -m app.cam.rosette.prototypes.celtic_parametric_knots --tile braid8
    python -m app.cam.rosette.prototypes.celtic_parametric_knots --parametric --mode diamond --size 16
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

# ── Celtic tile library (full v2 set — 6 tiles) ──────────────────

CELTIC_TILES: dict[str, dict] = {
    "simple4": {
        "label": "Simple 4x4 Knot",
        "desc": "Basic interlace — toy example from paper",
        "grid": [
            [0, 1, 1, 0],
            [1, 1, 1, 1],
            [1, 1, 1, 1],
            [0, 1, 1, 0],
        ],
    },
    "square8": {
        "label": "Square Interlace 8x8",
        "desc": "Single-band square knot, repeatable",
        "grid": [
            [0, 0, 1, 1, 1, 1, 0, 0],
            [0, 1, 1, 0, 0, 1, 1, 0],
            [1, 1, 0, 0, 0, 0, 1, 1],
            [1, 0, 0, 1, 1, 0, 0, 1],
            [1, 0, 0, 1, 1, 0, 0, 1],
            [1, 1, 0, 0, 0, 0, 1, 1],
            [0, 1, 1, 0, 0, 1, 1, 0],
            [0, 0, 1, 1, 1, 1, 0, 0],
        ],
    },
    "braid8": {
        "label": "3-Strand Braid 8x8",
        "desc": "Vertical braid with over/under accents",
        "grid": [
            [1, 1, 0, 1, 1, 0, 1, 1],
            [1, 0, 0, 1, 0, 0, 1, 0],
            [0, 0, 1, 0, 0, 1, 0, 0],
            [0, 1, 1, 0, 1, 1, 0, 1],
            [1, 1, 0, 1, 1, 0, 1, 1],
            [1, 0, 0, 1, 0, 0, 1, 0],
            [0, 0, 1, 0, 0, 1, 0, 0],
            [0, 1, 1, 0, 1, 1, 0, 1],
        ],
    },
    "step12": {
        "label": "Step / Key Pattern 12x12",
        "desc": "Greek-key derived step pattern",
        "grid": [
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
            [0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0],
            [0, 1, 0, 1, 1, 1, 1, 1, 1, 0, 1, 0],
            [0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0],
            [0, 1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0],
            [0, 1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0],
            [0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0],
            [0, 1, 0, 1, 1, 1, 1, 1, 1, 0, 1, 0],
            [0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0],
            [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        ],
    },
    "tricolor12": {
        "label": "Tri-color Weave 12x12",
        "desc": "Over/under strands with accent color",
        "grid": [
            [0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1],
            [0, 1, 1, 0, 1, 1, 0, 1, 1, 0, 1, 1],
            [1, 1, 0, 1, 1, 2, 1, 1, 0, 1, 1, 2],
            [1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0],
            [0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1],
            [0, 1, 1, 0, 1, 1, 0, 1, 1, 0, 1, 1],
            [1, 1, 2, 1, 1, 0, 1, 1, 2, 1, 1, 0],
            [1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0],
            [0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1],
            [0, 1, 1, 0, 1, 1, 0, 1, 1, 0, 1, 1],
            [1, 1, 0, 1, 1, 2, 1, 1, 0, 1, 1, 2],
            [1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0],
        ],
    },
    "rosette16": {
        "label": "Rosette Border 16x16",
        "desc": "Full rosette tile — classic interlace ring",
        "grid": [
            [0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0],
            [0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0],
            [0, 0, 1, 1, 0, 0, 1, 1, 1, 1, 0, 0, 1, 1, 0, 0],
            [0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0],
            [1, 1, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 1, 1],
            [1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1],
            [1, 0, 1, 1, 0, 0, 1, 1, 1, 1, 0, 0, 1, 1, 0, 1],
            [1, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 1],
            [1, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 1],
            [1, 0, 1, 1, 0, 0, 1, 1, 1, 1, 0, 0, 1, 1, 0, 1],
            [1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1],
            [1, 1, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 1, 1],
            [0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0],
            [0, 0, 1, 1, 0, 0, 1, 1, 1, 1, 0, 0, 1, 1, 0, 0],
            [0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0],
            [0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0],
        ],
    },
}

COLOR_MAP = {
    0: ("CELTIC_BG",     250),
    1: ("CELTIC_STRAND",  51),
    2: ("CELTIC_ACCENT",   3),
}

_SVG_FILL = {0: "#1a1008", 1: "#f0e8d0", 2: "#2d6a4f"}


# ── Parametric knot generator ─────────────────────────────────────

def generate_parametric(
    n: int = 12,
    threshold: float = 1.0,
    mode: str = "sine",
) -> list[list[int]]:
    """
    Algorithmic celtic knot grid using trigonometric formulas.

    Modes:
        sine:    |sin(2π·i/N)| + |cos(2π·j/N)| > threshold
        braid:   |sin(2π·(i+j·0.5)/N)| + |cos(2π·(j+i·0.5)/N)| > threshold
        diamond: |sin(2π·(i-j)/N)| + |sin(2π·(i+j)/N)| > threshold
    """
    grid: list[list[int]] = []
    for i in range(n):
        row: list[int] = []
        for j in range(n):
            if mode == "sine":
                val = abs(math.sin(2 * math.pi * i / n)) + abs(math.cos(2 * math.pi * j / n))
            elif mode == "braid":
                val = (abs(math.sin(2 * math.pi * (i + j * 0.5) / n))
                       + abs(math.cos(2 * math.pi * (j + i * 0.5) / n)))
            elif mode == "diamond":
                val = (abs(math.sin(2 * math.pi * (i - j) / n))
                       + abs(math.sin(2 * math.pi * (i + j) / n)))
            else:
                val = abs(math.sin(2 * math.pi * i / n)) + abs(math.cos(2 * math.pi * j / n))
            row.append(1 if val > threshold else 0)
        grid.append(row)
    return grid


# ── Grid utilities (from mothership) ──────────────────────────────

def mirror_points(
    r: int, c: int, rows: int, cols: int, mode: str = "4",
) -> list[tuple[int, int]]:
    """
    Generate symmetric mirror points for a grid coordinate.

    Modes: H (horizontal), V (vertical), 4 (four-way).
    """
    pts = [(r, c)]
    if mode in ("H", "4"):
        pts.append((r, cols - 1 - c))
    if mode in ("V", "4"):
        pts.append((rows - 1 - r, c))
    if mode == "4":
        pts.append((rows - 1 - r, cols - 1 - c))
    # Deduplicate
    seen: set[tuple[int, int]] = set()
    unique: list[tuple[int, int]] = []
    for p in pts:
        if p not in seen:
            seen.add(p)
            unique.append(p)
    return unique


def count_row(grid: list[list[int]], row: int) -> dict[int, int]:
    """Count cells per color in a single grid row."""
    counts: dict[int, int] = {0: 0, 1: 0, 2: 0, 3: 0}
    if row < len(grid):
        for v in grid[row]:
            counts[v] = counts.get(v, 0) + 1
    return counts


def count_totals(grid: list[list[int]]) -> dict[int, int]:
    """Count total cells per color across entire grid."""
    totals: dict[int, int] = {0: 0, 1: 0, 2: 0, 3: 0}
    for r in range(len(grid)):
        rc = count_row(grid, r)
        for k in totals:
            totals[k] += rc.get(k, 0)
    return totals


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
        lname = COLOR_MAP.get(color_val, COLOR_MAP[0])[0]
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
        "<title>Celtic Knot Rosette</title>",
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


# ── CSV export ────────────────────────────────────────────────────

def build_csv(grid: list[list[int]], label: str = "celtic") -> str:
    cols = len(grid[0])
    rows = len(grid)
    header = (
        f"# Celtic Knot Rosette ({label}) · {cols}×{rows} · 0.5mm/sq\n"
        f"# 0=bg  1=strand  2=accent\n"
    )
    return header + "\n".join(",".join(str(v) for v in row) for row in grid)


# ── Main ──────────────────────────────────────────────────────────

def main() -> None:
    import sys

    # Parse simple CLI args
    tile_name = "square8"
    parametric = False
    para_mode = "sine"
    para_size = 12
    para_threshold = 1.0

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--tile" and i + 1 < len(args):
            tile_name = args[i + 1]
            i += 2
        elif args[i] == "--parametric":
            parametric = True
            i += 1
        elif args[i] == "--mode" and i + 1 < len(args):
            para_mode = args[i + 1]
            i += 2
        elif args[i] == "--size" and i + 1 < len(args):
            para_size = int(args[i + 1])
            i += 2
        elif args[i] == "--threshold" and i + 1 < len(args):
            para_threshold = float(args[i + 1])
            i += 2
        else:
            i += 1

    if parametric:
        grid = generate_parametric(para_size, para_threshold, para_mode)
        label = f"parametric_{para_mode}_{para_size}"
    else:
        if tile_name not in CELTIC_TILES:
            print(f"Unknown tile: {tile_name}")
            print(f"Available: {', '.join(CELTIC_TILES.keys())}")
            sys.exit(1)
        tile = CELTIC_TILES[tile_name]
        grid = tile["grid"]
        label = tile_name

    cols = len(grid[0])
    rows = len(grid)
    repeats = _calc_repeats(grid)
    out_dir = Path(os.environ.get("ROSETTE_OUT", Path(__file__).resolve().parent.parent.parent.parent.parent.parent / "docs"))

    dxf_path = out_dir / f"celtic_{label}_rosette.dxf"
    dxf_content = build_dxf(grid)
    dxf_path.write_text(dxf_content, encoding="utf-8")
    print(f"DXF saved: {dxf_path}  ({dxf_content.count(chr(10)) + 1} lines)")

    svg_path = out_dir / f"celtic_{label}_rosette.svg"
    svg_content = build_svg(grid)
    svg_path.write_text(svg_content, encoding="utf-8")
    print(f"SVG saved: {svg_path}")

    csv_path = out_dir / f"celtic_{label}_rosette.csv"
    csv_content = build_csv(grid, label)
    csv_path.write_text(csv_content, encoding="utf-8")
    print(f"CSV saved: {csv_path}")

    totals = count_totals(grid)
    total = cols * rows
    print(f"\nCeltic Knot Rosette ({label})")
    print(f"  Grid: {cols}×{rows}  ({cols*0.5}×{rows*0.5} mm tile)")
    if parametric:
        print(f"  Mode: {para_mode}  Threshold: {para_threshold}")
    else:
        print(f"  Tile: {CELTIC_TILES[tile_name]['label']}")
        print(f"  Desc: {CELTIC_TILES[tile_name]['desc']}")
    print(f"  Background: {totals[0]}  ({totals[0]/total*100:.1f}%)")
    print(f"  Strand: {totals[1]}  ({totals[1]/total*100:.1f}%)")
    if totals.get(2, 0) > 0:
        print(f"  Accent: {totals[2]}  ({totals[2]/total*100:.1f}%)")
    print(f"  Tile repeats: {repeats}×")


if __name__ == "__main__":
    main()
