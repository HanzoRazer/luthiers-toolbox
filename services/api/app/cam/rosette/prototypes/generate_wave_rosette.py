#!/usr/bin/env python3
"""
Generate a Crashing Wave rosette DXF + SVG + CSV.

Uses the asymmetric arch formula from the Wave Rosette V3 JSX designer:

    swell side (x < peakX):  y = A · sin(π/2 · x / peakX)
    crash side (x ≥ peakX):  y = A · cos(π/2 · (x − peakX) / (segLen − peakX))

Grid is generated procedurally via buildCrashGrid (52×18, tri-color).
The grid is then tiled around the annulus as actual trapezoid cells.

Preset: Torres / Ramirez (classical guitar standard).
"""

import math
from pathlib import Path

# ── Ring dimensions (mm) — same as all rosettes ──────────────────
SOUNDHOLE_R = 40.8
INNER_R     = 41.8
OUTER_R     = 47.8
EBONY_INNER = 47.8
EBONY_OUTER = 49.3
GREEN_INNER = 49.3
GREEN_OUTER = 50.8

# ── Torres / Ramirez preset ──────────────────────────────────────
A          = 6        # arch height (squares)
SEG_LEN    = 18       # wave segment length (squares)
GAP        = 2        # air between waves (squares)
SKEW       = 0.72     # peak position (0–1), 0.72 = steep crash face
CHASE      = 13       # row stagger (squares) — in-phase ≈ skew × segLen
D          = 4        # row pitch (squares, center-to-center)
STRAND_W   = 1.8      # strand width (squares)
NUM_STRANDS = 7       # number of strand rows
COLS       = 52       # tile columns
ROWS       = 18       # tile rows
COLOR_MODE = "tri"    # tri = 3-color cycling

PITCH = SEG_LEN + GAP

# In-phase check: chase ≈ skew × segLen
_OPTIMAL_CHASE = round(SKEW * SEG_LEN)
IN_PHASE = abs(CHASE - _OPTIMAL_CHASE) <= 1

# How many times the full tile repeats around the ring.
# Average circumference ≈ π × (41.8+47.8) ≈ 281 mm.
# With 52 cols × 0.5 mm/cell ≈ 26 mm tile width ⇒ ~11 repeats.
_AVG_CIRC = math.pi * (INNER_R + OUTER_R)
TILE_REPEATS = round(_AVG_CIRC / (COLS * 0.5))

# Color-value → (layer_name, DXF ACI color)
COLOR_MAP = {
    0: ("WAVE_BG", 250),   # background (black)
    1: ("WAVE_A",   51),   # strand A (cream)
    2: ("WAVE_B",    1),   # strand B (red)
    3: ("WAVE_C",    3),   # strand C (green)
}

# SVG fills (from JSX defaults)
_SVG_FILL = {
    0: "#1a1008",   # background
    1: "#f0e8d0",   # strand A (cream)
    2: "#8b2020",   # strand B (red)
    3: "#2d6a4f",   # strand C (green)
}


# ── Crashing wave formula ────────────────────────────────────────

def arch_y(local_x: float, seg_len: float, amplitude: float, skew: float) -> float:
    """
    Asymmetric arch — the crashing wave profile.

    Swell side (x < peakX):  A · sin(π/2 · x / peakX)       — gradual rise
    Crash side (x ≥ peakX):  A · cos(π/2 · (x-peakX) / rem) — steep fall
    """
    peak_x = skew * seg_len
    if peak_x <= 0 or seg_len <= 0:
        return 0.0
    if local_x <= peak_x:
        return amplitude * math.sin((math.pi / 2) * (local_x / peak_x))
    else:
        return amplitude * math.cos(
            (math.pi / 2) * ((local_x - peak_x) / (seg_len - peak_x))
        )


def build_crash_grid() -> list[list[int]]:
    """
    Procedurally generate the wave grid using the crashing wave formula.

    Each strand row follows an asymmetric arch, staggered by `chase` squares.
    Color assignment uses tri-color cycling: strand n → color (n % 3) mapped
    to values 1/2/3, background = 0.
    """
    grid: list[list[int]] = []

    for r in range(ROWS):
        row: list[int] = []
        for c in range(COLS):
            hit = False
            hit_n = 0

            for n in range(-2, NUM_STRANDS + 3):
                # Each strand row n is chased forward by n·chase squares
                offset = ((n * CHASE) % PITCH + PITCH * 100) % PITCH
                x_shifted = ((c - offset) % PITCH + PITCH * 100) % PITCH
                in_seg = x_shifted < SEG_LEN
                if not in_seg:
                    continue

                cy = n * D + arch_y(x_shifted, SEG_LEN, A, SKEW)
                if abs(r - cy) < STRAND_W / 2:
                    hit = True
                    hit_n = n
                    break

            if hit:
                idx = ((hit_n % 3) + 3) % 3
                if COLOR_MODE == "bw":
                    row.append(1 if ((hit_n % 2) + 2) % 2 == 0 else 2)
                elif COLOR_MODE == "mono":
                    row.append(1)
                elif COLOR_MODE == "tri":
                    row.append(1 if idx == 0 else (2 if idx == 1 else 3))
                else:
                    row.append(1)
            else:
                row.append(0)
        grid.append(row)

    return grid


# ── Tile-cell geometry ────────────────────────────────────────────

def _build_cells(grid: list[list[int]], inner_r: float, outer_r: float,
                 repeats: int) -> list[tuple[int, list[tuple[float, float]]]]:
    """
    Map the grid onto the annulus as closed trapezoid quads.
    Cols → angular divisions, rows → radial bands.
    """
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
                color_val = grid[r][c]
                r0 = inner_r + r * radial_step
                r1 = inner_r + (r + 1) * radial_step

                quad = [
                    (r0 * math.cos(a0), r0 * math.sin(a0)),
                    (r1 * math.cos(a0), r1 * math.sin(a0)),
                    (r1 * math.cos(a1), r1 * math.sin(a1)),
                    (r0 * math.cos(a1), r0 * math.sin(a1)),
                ]
                cells.append((color_val, quad))

    return cells


# ── DXF helpers ───────────────────────────────────────────────────

def _dxf_circle(layer: str, cx: float, cy: float, radius: float) -> list[str]:
    return [
        "0", "CIRCLE",
        "8", layer,
        "10", f"{cx:.6f}",
        "20", f"{cy:.6f}",
        "40", f"{radius:.6f}",
    ]


def _dxf_closed_poly(layer: str, pts: list[tuple[float, float]]) -> list[str]:
    """Closed POLYLINE (flag 1) for a tile quad."""
    lines = ["0", "POLYLINE", "8", layer, "66", "1", "70", "1"]
    for x, y in pts:
        lines += ["0", "VERTEX", "8", layer, "10", f"{x:.6f}", "20", f"{y:.6f}"]
    lines += ["0", "SEQEND"]
    return lines


def build_dxf(grid: list[list[int]]) -> str:
    """Build the complete DXF R12 string."""
    lines: list[str] = []

    # Header
    lines += [
        "0", "SECTION", "2", "HEADER",
        "9", "$ACADVER", "1", "AC1009",
        "9", "$INSUNITS", "70", "4",
        "0", "ENDSEC",
    ]

    # Layer table
    struct_layers = [
        ("SOUNDHOLE",    7),
        ("INNER_BORDER", 8),
        ("PATTERN_ZONE", 5),
        ("EBONY_RING",   250),
        ("GREEN_RING",   3),
    ]
    all_layers = list(struct_layers)
    for _, (lname, aci) in COLOR_MAP.items():
        all_layers.append((lname, aci))

    lines += ["0", "SECTION", "2", "TABLES", "0", "TABLE", "2", "LAYER"]
    for lname, aci in all_layers:
        lines += [
            "0", "LAYER", "2", lname,
            "70", "0", "62", str(aci), "6", "CONTINUOUS",
        ]
    lines += ["0", "ENDTAB", "0", "ENDSEC"]

    # Entities
    lines += ["0", "SECTION", "2", "ENTITIES"]

    # Concentric ring circles
    lines += _dxf_circle("SOUNDHOLE",    0, 0, SOUNDHOLE_R)
    lines += _dxf_circle("INNER_BORDER", 0, 0, SOUNDHOLE_R)
    lines += _dxf_circle("INNER_BORDER", 0, 0, INNER_R)
    lines += _dxf_circle("PATTERN_ZONE", 0, 0, INNER_R)
    lines += _dxf_circle("PATTERN_ZONE", 0, 0, OUTER_R)
    lines += _dxf_circle("EBONY_RING",   0, 0, EBONY_INNER)
    lines += _dxf_circle("EBONY_RING",   0, 0, EBONY_OUTER)
    lines += _dxf_circle("GREEN_RING",   0, 0, GREEN_INNER)
    lines += _dxf_circle("GREEN_RING",   0, 0, GREEN_OUTER)

    # Tile cells
    cells = _build_cells(grid, INNER_R, OUTER_R, TILE_REPEATS)
    for color_val, quad in cells:
        lname = COLOR_MAP[color_val][0]
        lines += _dxf_closed_poly(lname, quad)

    lines += ["0", "ENDSEC", "0", "EOF"]
    return "\n".join(lines)


# ── SVG export ────────────────────────────────────────────────────

def build_svg(grid: list[list[int]]) -> str:
    """Build an SVG preview with filled tile quads."""
    pad = 5
    vb = GREEN_OUTER + pad
    parts: list[str] = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="{-vb} {-vb} {2*vb} {2*vb}" '
        f'width="{2*vb}mm" height="{2*vb}mm">',
        '<title>Crashing Wave Rosette (Torres / Ramirez)</title>',
        '<desc>Generated by The Production Shop</desc>',
        f'<circle cx="0" cy="0" r="{OUTER_R}" fill="#1a1008"/>',
        f'<circle cx="0" cy="0" r="{INNER_R}" fill="#0e0b07"/>',
    ]

    cells = _build_cells(grid, INNER_R, OUTER_R, TILE_REPEATS)
    for color_val, quad in cells:
        fill = _SVG_FILL[color_val]
        pts = " ".join(f"{x:.3f},{y:.3f}" for x, y in quad)
        parts.append(
            f'<polygon points="{pts}" fill="{fill}" stroke="{fill}" stroke-width="0.02"/>'
        )

    parts += [
        f'<circle cx="0" cy="0" r="{SOUNDHOLE_R}" fill="#0e0b07" stroke="#3a2e1a" stroke-width="0.3"/>',
        f'<circle cx="0" cy="0" r="{INNER_R}" fill="none" stroke="#3a2e1a" stroke-width="0.3"/>',
        f'<circle cx="0" cy="0" r="{OUTER_R}" fill="none" stroke="#c8a032" stroke-width="0.3"/>',
        f'<circle cx="0" cy="0" r="{EBONY_OUTER}" fill="none" stroke="#1a1008" stroke-width="1.5"/>',
        f'<circle cx="0" cy="0" r="{GREEN_OUTER}" fill="none" stroke="#2d6a4f" stroke-width="1.5"/>',
        '</svg>',
    ]
    return "\n".join(parts)


# ── CSV export ────────────────────────────────────────────────────

def build_csv(grid: list[list[int]]) -> str:
    """
    Build CSV export with header metadata — Fusion 360 / CNC ready.
    Matches the JSX CSV export tab format.
    """
    mm_w = COLS * 0.5
    mm_h = ROWS * 0.5
    peak_pct = round(SKEW * 100)
    swell_mm = SKEW * SEG_LEN * 0.5
    crash_mm = (1 - SKEW) * SEG_LEN * 0.5
    phase_tag = "in-phase" if IN_PHASE else f"off-phase (optimal={_OPTIMAL_CHASE})"

    header_lines = [
        f"# Crashing Wave Rosette Tile · {COLS}x{ROWS} · 0.5mm/sq",
        f"# Preset: Torres / Ramirez",
        f"# A={A} segLen={SEG_LEN} gap={GAP} skew={SKEW} chase={CHASE} d={D} strandW={STRAND_W}",
        f"# Peak at {peak_pct}% · swell={swell_mm:.1f}mm · crash={crash_mm:.1f}mm",
        f"# Chase: {CHASE} sq/row · {phase_tag}",
        f"# Tile: {mm_w:.1f}mm x {mm_h:.1f}mm · {TILE_REPEATS}x around ring",
        f"# 0=bg  1=strandA  2=strandB  3=strandC",
    ]

    data_lines = [",".join(str(v) for v in row) for row in grid]
    return "\n".join(header_lines + data_lines) + "\n"


# ── Main ──────────────────────────────────────────────────────────

def main() -> None:
    docs = Path(r"C:\Users\thepr\Downloads\luthiers-toolbox\docs")
    dl = Path(r"C:\Users\thepr\Downloads")

    # Generate grid procedurally
    print("Building crash grid...")
    grid = build_crash_grid()

    # Count cells by color
    counts: dict[int, int] = {}
    for row in grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    total = COLS * ROWS

    # Wave anatomy
    peak_pct = round(SKEW * 100)
    swell_mm = SKEW * SEG_LEN * 0.5
    crash_mm = (1 - SKEW) * SEG_LEN * 0.5
    crash_angle = math.degrees(math.atan(A / ((1 - SKEW) * SEG_LEN)))

    print(f"\n{'='*60}")
    print(f"  CRASHING WAVE ROSETTE — Torres / Ramirez Preset")
    print(f"{'='*60}")
    print(f"  Formula: swell = A·sin(π/2 · x/peakX)")
    print(f"           crash = A·cos(π/2 · (x-peakX)/(segLen-peakX))")
    print(f"")
    print(f"  Wave shape:")
    print(f"    A (arch height)  = {A} sq ({A*0.5:.1f}mm)")
    print(f"    segLen           = {SEG_LEN} sq ({SEG_LEN*0.5:.1f}mm)")
    print(f"    gap              = {GAP} sq ({GAP*0.5:.1f}mm)")
    print(f"    pitch            = {PITCH} sq ({PITCH*0.5:.1f}mm)")
    print(f"    skew (peak)      = {peak_pct}%")
    print(f"    swell length     = {swell_mm:.1f}mm (gradual rise)")
    print(f"    crash face       = {crash_mm:.1f}mm (steep fall)")
    print(f"    crash angle      = {crash_angle:.1f}° from horizontal")
    print(f"    swell/crash ratio= {SKEW/(1-SKEW):.2f}:1")
    print(f"")
    print(f"  Strand array:")
    print(f"    d (row pitch)    = {D} sq ({D*0.5:.1f}mm)")
    print(f"    strandW          = {STRAND_W} sq ({STRAND_W*0.5:.1f}mm)")
    print(f"    numStrands       = {NUM_STRANDS}")
    phase_str = "✓ in-phase (≈ swell length)" if IN_PHASE else f"off-phase (optimal={_OPTIMAL_CHASE})"
    print(f"    chase            = {CHASE} sq/row · {phase_str}")
    print(f"")
    print(f"  Grid: {COLS}x{ROWS} · {total} cells")
    print(f"    BG (0)     = {counts.get(0,0):>5}  ({100*counts.get(0,0)/total:.1f}%)")
    print(f"    Strand A   = {counts.get(1,0):>5}  ({100*counts.get(1,0)/total:.1f}%)")
    print(f"    Strand B   = {counts.get(2,0):>5}  ({100*counts.get(2,0)/total:.1f}%)")
    print(f"    Strand C   = {counts.get(3,0):>5}  ({100*counts.get(3,0)/total:.1f}%)")
    print(f"")
    print(f"  Ring: {INNER_R}-{OUTER_R}mm ({OUTER_R-INNER_R}mm band)")
    print(f"    Tile repeats     = {TILE_REPEATS}x around ring")
    total_cells = COLS * ROWS * TILE_REPEATS
    print(f"    Total ring cells = {total_cells:,}")
    print(f"{'='*60}")

    # DXF
    print("\nGenerating DXF...")
    dxf_path = docs / "wave_rosette.dxf"
    dxf_content = build_dxf(grid)
    dxf_path.write_text(dxf_content, encoding="utf-8")
    dxf_lines = dxf_content.count("\n") + 1
    print(f"  DXF saved: {dxf_path}  ({dxf_lines:,} lines)")

    # SVG
    print("Generating SVG preview...")
    svg_path = dl / "wave_rosette_preview.svg"
    svg_content = build_svg(grid)
    svg_path.write_text(svg_content, encoding="utf-8")
    print(f"  SVG saved: {svg_path}")

    # CSV
    print("Generating CSV export...")
    csv_name = f"wave_rosette_{COLS}x{ROWS}_A{A}_skew{round(SKEW*100)}_chase{CHASE}.csv"
    csv_path = dl / csv_name
    csv_content = build_csv(grid)
    csv_path.write_text(csv_content, encoding="utf-8")
    print(f"  CSV saved: {csv_path}")

    print(f"\nLayers: WAVE_BG (black), WAVE_A (cream), WAVE_B (red), WAVE_C (green)")
    print("Done.")


if __name__ == "__main__":
    main()
