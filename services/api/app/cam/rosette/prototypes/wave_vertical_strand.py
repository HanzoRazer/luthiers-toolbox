#!/usr/bin/env python3
"""
Generate a Vertical Single-Strand wave rosette DXF + SVG + CSV.

Ported from: wave-rosette-v4.jsx

Fundamentally different model from the horizontal multi-strand waves:
A SINGLE strand travels along Y (radial direction in annulus).
At each row y, the strand's X center is displaced by the swell/crash arch:

    x(y) = centerX + A · arch(y_local, segLen, skew)

arch:
    swell (y < peakY):  A · sin(π/2 · y/peakY)        → 0 → A
    crash (y ≥ peakY):  A · cos(π/2 · (y−peakY)/rem)   → A → 0
    gap zone:           strand absent (background)

Pixel (col, row) is ON if row is in an active segment AND |col − x(row)| < strandW/2.

When mapped to annulus: rows → radial (inner→outer), cols → angular.
The strand weaves side-to-side as it travels outward through the ring.

Usage:
    python -m app.cam.rosette.prototypes.wave_vertical_strand
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
COLS         = 30       # angular divisions
ROWS         = 52       # radial divisions (strand travels along rows)
A            = 8        # displacement amplitude (squares)
SEG_LEN      = 20       # active segment length (squares)
GAP          = 4        # gap between arch cycles (squares)
STRAND_W     = 2.0      # strand width (squares)
SKEW         = 0.72     # peak position (0–1)
CENTER_FRAC  = 0.5      # horizontal center (0–1)

PITCH = SEG_LEN + GAP

_AVG_CIRC = math.pi * (INNER_R + OUTER_R)
TILE_REPEATS = round(_AVG_CIRC / (COLS * 0.5))

COLOR_MAP = {
    0: ("VERT_BG", 250),
    1: ("VERT_STRAND", 51),
}

_SVG_FILL = {0: "#1a1008", 1: "#f0e8d0"}


# ── Arch displacement ─────────────────────────────────────────────

def arch_displace(local_y: float, seg_len: float, amplitude: float, skew: float) -> float:
    """
    Vertical swell/crash displacement (same math as horizontal archY, applied vertically).

    swell (y < peakY):  A · sin(π/2 · y/peakY)
    crash (y ≥ peakY):  A · cos(π/2 · (y−peakY) / (segLen−peakY))
    """
    peak_y = skew * seg_len
    if local_y <= peak_y:
        return amplitude * math.sin((math.pi / 2) * (local_y / max(peak_y, 0.001)))
    else:
        return amplitude * math.cos(
            (math.pi / 2) * ((local_y - peak_y) / max(seg_len - peak_y, 0.001))
        )


# ── Grid builder ──────────────────────────────────────────────────

def build_strand_grid(
    cols: int = COLS,
    rows: int = ROWS,
    amplitude: float = A,
    seg_len: int = SEG_LEN,
    gap: int = GAP,
    strand_w: float = STRAND_W,
    skew: float = SKEW,
    center_frac: float = CENTER_FRAC,
) -> list[list[int]]:
    """
    Single vertical strand with swell/crash displacement.

    Strand travels along Y. At each row, it's displaced horizontally.
    """
    pitch = seg_len + gap
    center_x = cols * center_frac
    grid: list[list[int]] = []

    for r in range(rows):
        row = [0] * cols
        local_y = r % pitch
        if local_y >= seg_len:
            # Gap zone — no strand
            grid.append(row)
            continue
        dx = arch_displace(local_y, seg_len, amplitude, skew)
        strand_x = center_x + dx
        for c in range(cols):
            if abs(c - strand_x) < strand_w / 2:
                row[c] = 1
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
        "<title>Vertical Strand Wave Rosette</title>",
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
        f"# Vertical Strand Wave Rosette · {len(grid[0])}×{len(grid)} · 0.5mm/sq\n"
        f"# A={A} segLen={SEG_LEN} gap={GAP} skew={SKEW} centerFrac={CENTER_FRAC}\n"
        f"# 0=bg  1=strand\n"
    )
    return header + "\n".join(",".join(str(v) for v in row) for row in grid)


# ── Main ──────────────────────────────────────────────────────────

def main() -> None:
    grid = build_strand_grid()
    out_dir = Path(os.environ.get("ROSETTE_OUT", Path(__file__).resolve().parent.parent.parent.parent.parent.parent / "docs"))

    dxf_path = out_dir / "vertical_strand_rosette.dxf"
    dxf_content = build_dxf(grid)
    dxf_path.write_text(dxf_content, encoding="utf-8")
    print(f"DXF saved: {dxf_path}  ({dxf_content.count(chr(10)) + 1} lines)")

    svg_path = out_dir / "vertical_strand_rosette.svg"
    svg_content = build_svg(grid)
    svg_path.write_text(svg_content, encoding="utf-8")
    print(f"SVG saved: {svg_path}")

    csv_path = out_dir / "vertical_strand_rosette.csv"
    csv_content = build_csv(grid)
    csv_path.write_text(csv_content, encoding="utf-8")
    print(f"CSV saved: {csv_path}")

    counts = {0: 0, 1: 0}
    for row in grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    total = len(grid) * len(grid[0])
    print(f"\nVertical Strand Wave Rosette")
    print(f"  Grid: {COLS}×{ROWS}  ({COLS*0.5}×{ROWS*0.5} mm tile)")
    print(f"  Strand: A={A} segLen={SEG_LEN} gap={GAP} skew={SKEW}")
    print(f"  Background: {counts[0]}  ({counts[0]/total*100:.1f}%)")
    print(f"  Strand: {counts[1]}  ({counts[1]/total*100:.1f}%)")
    print(f"  Tile repeats: {TILE_REPEATS}×")


if __name__ == "__main__":
    main()
