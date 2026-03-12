#!/usr/bin/env python3
"""
Generate a Discrete Segment Arch wave rosette DXF + SVG + CSV.

Ported from: wave-rosette-v2.jsx

Each strand is a sequence of DISCRETE arched segments, NOT a continuous wave.
Segment k of strand n starts at:
    x_start(n, k) = k · (segLen + gap) + (n · rowOffset) mod pitch

Within a segment, the centerline is one of three arch shapes:
    sine:     A · sin(π · t)           — smooth half-sine arch
    triangle: A · (1 − |2t − 1|)      — sharp peaked triangle
    flat:     A · sin²(π · t)          — flattened top (squared sine)

where t = localX / segLen ∈ [0, 1].

Between segments (the gap zone): background only.

Color modes: bw (alternating), mono (cream), alt3 (3-color cycling).

Usage:
    python -m app.cam.rosette.prototypes.wave_segment_arches
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
A           = 5        # arch height (squares)
SEG_LEN     = 16       # segment length (squares)
GAP         = 4        # gap between segments (squares)
D           = 4        # row pitch (squares)
STRAND_W    = 1.8      # strand half-thickness (squares)
NUM_STRANDS = 7
ROW_OFFSET  = 10       # stagger between strands (squares)
ARCH_SHAPE  = "sine"   # sine | tri | flat
COLOR_MODE  = "bw"     # bw | mono | alt3

PITCH = SEG_LEN + GAP

_AVG_CIRC = math.pi * (INNER_R + OUTER_R)
TILE_REPEATS = round(_AVG_CIRC / (COLS * 0.5))

COLOR_MAP = {
    0: ("SEG_BG", 250),
    1: ("SEG_A",   51),
    2: ("SEG_B",    3),
    3: ("SEG_C",    1),
}

_SVG_FILL = {0: "#1a1008", 1: "#f0e8d0", 2: "#2d6a4f", 3: "#8b2020"}


# ── Arch shape functions ──────────────────────────────────────────

def _arch_value(local_x: float, seg_len: float, amplitude: float, shape: str) -> float:
    """Compute arch displacement at local_x within a segment."""
    if seg_len <= 0:
        return 0.0
    t = local_x / seg_len
    if shape == "sine":
        return amplitude * math.sin(math.pi * t)
    elif shape == "tri":
        return amplitude * (1.0 - abs(2.0 * t - 1.0))
    elif shape == "flat":
        s = math.sin(math.pi * t)
        return amplitude * s * s
    return amplitude * math.sin(math.pi * t)


# ── Grid builder ──────────────────────────────────────────────────

def build_segment_grid(
    cols: int = COLS,
    rows: int = ROWS,
    amplitude: float = A,
    seg_len: int = SEG_LEN,
    gap: int = GAP,
    d: float = D,
    strand_w: float = STRAND_W,
    num_strands: int = NUM_STRANDS,
    row_offset: int = ROW_OFFSET,
    arch_shape: str = ARCH_SHAPE,
    color_mode: str = COLOR_MODE,
) -> list[list[int]]:
    """
    Discrete segment arch grid.

    Each strand is a sequence of isolated arched segments with gaps between.
    row_offset staggers alternate strands diagonally.
    """
    pitch = seg_len + gap
    grid: list[list[int]] = []

    for r in range(rows):
        row: list[int] = []
        for c in range(cols):
            hit = False
            hit_n = 0

            for n in range(-2, num_strands + 3):
                strand_phase = (n * row_offset) % pitch
                x_shifted = ((c - strand_phase) % pitch + pitch * 100) % pitch
                in_segment = x_shifted < seg_len

                if not in_segment:
                    continue

                arch = _arch_value(x_shifted, seg_len, amplitude, arch_shape)
                center_y = n * d + arch
                dist = abs(r - center_y)

                if dist < strand_w / 2:
                    hit = True
                    hit_n = n
                    break

            if hit:
                if color_mode == "bw":
                    row.append(1 if ((hit_n % 2) + 2) % 2 == 0 else 2)
                elif color_mode == "mono":
                    row.append(1)
                elif color_mode == "alt3":
                    idx = ((hit_n % 3) + 3) % 3
                    row.append(1 if idx == 0 else (2 if idx == 1 else 3))
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
        "<title>Segment Arch Wave Rosette</title>",
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
        f"# Segment Arch Wave Rosette · {len(grid[0])}×{len(grid)} · 0.5mm/sq\n"
        f"# A={A} segLen={SEG_LEN} gap={GAP} rowOffset={ROW_OFFSET} shape={ARCH_SHAPE}\n"
        f"# 0=bg  1=strandA  2=strandB  3=strandC\n"
    )
    return header + "\n".join(",".join(str(v) for v in row) for row in grid)


# ── Main ──────────────────────────────────────────────────────────

def main() -> None:
    grid = build_segment_grid()
    out_dir = Path(os.environ.get("ROSETTE_OUT", Path(__file__).resolve().parent.parent.parent.parent.parent.parent / "docs"))

    dxf_path = out_dir / "segment_arch_rosette.dxf"
    dxf_content = build_dxf(grid)
    dxf_path.write_text(dxf_content, encoding="utf-8")
    print(f"DXF saved: {dxf_path}  ({dxf_content.count(chr(10)) + 1} lines)")

    svg_path = out_dir / "segment_arch_rosette.svg"
    svg_content = build_svg(grid)
    svg_path.write_text(svg_content, encoding="utf-8")
    print(f"SVG saved: {svg_path}")

    csv_path = out_dir / "segment_arch_rosette.csv"
    csv_content = build_csv(grid)
    csv_path.write_text(csv_content, encoding="utf-8")
    print(f"CSV saved: {csv_path}")

    # Quick BOM
    counts = {0: 0, 1: 0, 2: 0, 3: 0}
    for row in grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    total = len(grid) * len(grid[0])
    print(f"\nSegment Arch Wave Rosette ({ARCH_SHAPE} shape)")
    print(f"  Grid: {COLS}×{ROWS}  ({COLS*0.5}×{ROWS*0.5} mm tile)")
    print(f"  Segments: len={SEG_LEN} gap={GAP} offset={ROW_OFFSET}")
    print(f"  Background: {counts[0]}  ({counts[0]/total*100:.1f}%)")
    print(f"  Strand A: {counts[1]}  ({counts[1]/total*100:.1f}%)")
    print(f"  Strand B: {counts.get(2,0)}  ({counts.get(2,0)/total*100:.1f}%)")
    print(f"  Strand C: {counts.get(3,0)}  ({counts.get(3,0)/total*100:.1f}%)")
    print(f"  Tile repeats: {TILE_REPEATS}×")


if __name__ == "__main__":
    main()
