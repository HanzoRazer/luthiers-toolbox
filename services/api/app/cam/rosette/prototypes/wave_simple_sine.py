#!/usr/bin/env python3
"""
Generate a Simple Sine Wave rosette DXF + SVG + CSV.

Ported from: wave-rosette-v1.jsx

Pure sinusoidal wave model — all strands follow the same continuous sine:

    y_n(x) = n·d + A·sin(2π·x/λ + phase)

A pixel (col, row) is ON a strand if ∃ n : |row − y_n(col)| < strandW/2.

Color modes:
  bw    — alternating black/white by strand parity
  bwg   — 3-color cycling (black / white / green)
  solid — single color (all cream)

Usage:
    python -m app.cam.rosette.prototypes.wave_simple_sine
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

# ── Default parameters ────────────────────────────────────────────
COLS        = 52
ROWS        = 18
A           = 4        # amplitude (squares)
LAMBDA      = 20       # wavelength (squares)
D           = 4        # row pitch (squares, center-to-center)
STRAND_W    = 1.8      # strand half-thickness (squares)
NUM_STRANDS = 7
PHASE       = 0.0      # radians
COLOR_MODE  = "bw"     # bw | bwg | solid

# Tile repeats
_AVG_CIRC = math.pi * (INNER_R + OUTER_R)
TILE_REPEATS = round(_AVG_CIRC / (COLS * 0.5))

# Color-value → (layer_name, DXF ACI color)
COLOR_MAP = {
    0: ("SINE_BG", 250),
    1: ("SINE_A",   51),
    2: ("SINE_B",    3),
}

_SVG_FILL = {0: "#1a1008", 1: "#f0e8d0", 2: "#2d6a4f"}


# ── Grid builder ──────────────────────────────────────────────────

def build_wave_grid(
    cols: int = COLS,
    rows: int = ROWS,
    amplitude: float = A,
    wavelength: float = LAMBDA,
    d: float = D,
    strand_w: float = STRAND_W,
    num_strands: int = NUM_STRANDS,
    phase: float = PHASE,
    color_mode: str = COLOR_MODE,
) -> list[list[int]]:
    """
    Pure sinusoidal wave grid.

    y_n(x) = n·d + A·sin(2π·x/λ + phase)
    Pixel ON if |row − y_n(col)| < strandW/2.
    """
    grid: list[list[int]] = []

    for r in range(rows):
        row: list[int] = []
        for c in range(cols):
            wave = amplitude * math.sin(2 * math.pi * c / wavelength + phase)
            closest = float("inf")
            closest_n = 0
            for n in range(-num_strands, num_strands * 2 + 1):
                center = n * d + wave
                dist = abs(r - center)
                if dist < closest:
                    closest = dist
                    closest_n = n
            if closest < strand_w / 2:
                if color_mode == "bw":
                    row.append((closest_n % 2 + 2) % 2)
                elif color_mode == "bwg":
                    row.append(2 if closest_n % 3 == 0 else closest_n % 2)
                elif color_mode == "solid":
                    row.append(1)
                else:
                    row.append(1)
            else:
                row.append(0)
        grid.append(row)

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

    cells = _build_cells(grid, INNER_R, OUTER_R, TILE_REPEATS)
    for color_val, quad in cells:
        lname = COLOR_MAP[color_val][0]
        lines += _dxf_closed_poly(lname, quad)

    lines += ["0", "ENDSEC", "0", "EOF"]
    return "\n".join(lines)


# ── SVG export ────────────────────────────────────────────────────

def build_svg(grid: list[list[int]]) -> str:
    pad = 5
    vb = GREEN_OUTER + pad
    parts: list[str] = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{-vb} {-vb} {2*vb} {2*vb}" '
        f'width="{2*vb}mm" height="{2*vb}mm">',
        "<title>Simple Sine Wave Rosette</title>",
        "<desc>Generated by The Production Shop</desc>",
        f'<circle cx="0" cy="0" r="{OUTER_R}" fill="#1a1008"/>',
        f'<circle cx="0" cy="0" r="{INNER_R}" fill="#0e0b07"/>',
    ]
    cells = _build_cells(grid, INNER_R, OUTER_R, TILE_REPEATS)
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

def build_csv(grid: list[list[int]]) -> str:
    header = (
        f"# Simple Sine Wave Rosette · {len(grid[0])}×{len(grid)} · 0.5mm/sq\n"
        f"# A={A} lambda={LAMBDA} phase={PHASE} d={D} strandW={STRAND_W}\n"
        f"# 0=bg  1=strandA  2=strandB\n"
    )
    return header + "\n".join(",".join(str(v) for v in row) for row in grid)


# ── BOM ───────────────────────────────────────────────────────────

def bom_summary(grid: list[list[int]]) -> str:
    counts = {0: 0, 1: 0, 2: 0}
    for row in grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    total = len(grid) * len(grid[0])
    mm_w = len(grid[0]) * 0.5
    mm_h = len(grid) * 0.5
    lines = [
        "Veneer BOM — Simple Sine Wave",
        f"  Grid: {len(grid[0])}×{len(grid)}  ({mm_w}×{mm_h} mm tile)",
        f"  Background cells: {counts[0]}  ({counts[0]/total*100:.1f}%)",
        f"  Strand A cells:   {counts[1]}  ({counts[1]/total*100:.1f}%)",
        f"  Strand B cells:   {counts.get(2,0)}  ({counts.get(2,0)/total*100:.1f}%)",
        f"  Total cells: {total}",
        f"  Tile repeats: {TILE_REPEATS}× around ring",
    ]

    # Row-by-row run-length encoding
    labels = {0: "B", 1: "S", 2: "A"}
    lines.append("\nRow-by-row strip cuts:")
    for i, row in enumerate(grid):
        parts = []
        cur, run = row[0], 1
        for c in range(1, len(row)):
            if row[c] == cur:
                run += 1
            else:
                parts.append(f"{run}{labels.get(cur, '?')}")
                cur, run = row[c], 1
        parts.append(f"{run}{labels.get(cur, '?')}")
        lines.append(f"  Row {i+1:2d} ({(i+1)*0.5:.1f}mm): {' '.join(parts)}")

    return "\n".join(lines)


# ── Main ──────────────────────────────────────────────────────────

def main() -> None:
    grid = build_wave_grid()
    out_dir = Path(os.environ.get("ROSETTE_OUT", Path(__file__).resolve().parent.parent.parent.parent.parent.parent / "docs"))

    dxf_path = out_dir / "sine_wave_rosette.dxf"
    dxf_content = build_dxf(grid)
    dxf_path.write_text(dxf_content, encoding="utf-8")
    print(f"DXF saved: {dxf_path}  ({dxf_content.count(chr(10)) + 1} lines)")

    svg_path = out_dir / "sine_wave_rosette.svg"
    svg_content = build_svg(grid)
    svg_path.write_text(svg_content, encoding="utf-8")
    print(f"SVG saved: {svg_path}")

    csv_path = out_dir / "sine_wave_rosette.csv"
    csv_content = build_csv(grid)
    csv_path.write_text(csv_content, encoding="utf-8")
    print(f"CSV saved: {csv_path}")

    print(f"\n{bom_summary(grid)}")


if __name__ == "__main__":
    main()
