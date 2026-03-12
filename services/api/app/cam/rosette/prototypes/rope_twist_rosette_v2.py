#!/usr/bin/env python3
"""
Generate a Rope rosette DXF + SVG + CSV.

The 7×5 diagonal-staircase grid is tiled around the annulus as trapezoid cells.
Alternate tile repeats are mirrored horizontally to create the full rope twist
illusion (left-leaning / right-leaning alternation).

Pattern source: JSX rosette-grid-designer Rope preset (7×5, 2 colors).
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

# ── Rope grid (7×5, values: 0=black, 1=white) ───────────────────
GRID = [
    [0, 0, 0, 0, 0, 1, 1],
    [0, 0, 0, 0, 1, 1, 0],
    [0, 0, 0, 1, 1, 0, 0],
    [0, 0, 1, 1, 0, 0, 1],
    [0, 1, 1, 0, 0, 1, 0],
]
# Mirrored version (columns reversed) for rope twist alternation
GRID_MIRROR = [list(reversed(row)) for row in GRID]

COLS = 7
ROWS = 5

# Average circumference ≈ π × (41.8+47.8) ≈ 281 mm.
# With 7 cols × 0.5 mm/cell ≈ 3.5 mm tile width ⇒ ~80 repeats.
# Use even number so mirror alternation works cleanly.
_AVG_CIRC = math.pi * (INNER_R + OUTER_R)
TILE_REPEATS = round(_AVG_CIRC / (COLS * 0.5))
if TILE_REPEATS % 2 != 0:
    TILE_REPEATS += 1  # ensure even for clean mirror alternation

# Color-value → (layer_name, DXF ACI color)
COLOR_MAP = {
    0: ("ROPE_0", 250),   # black
    1: ("ROPE_1",  51),   # white/cream
}

# SVG fills
_SVG_FILL = {0: "#1a1008", 1: "#f5efe0"}


# ── Tile-cell geometry ────────────────────────────────────────────

def _build_cells(inner_r: float, outer_r: float,
                 repeats: int) -> list[tuple[int, list[tuple[float, float]]]]:
    """
    Map the 7×5 grid onto the annulus as closed trapezoid quads.
    Alternate repeats use the mirrored grid for rope twist effect.
    """
    total_cols = COLS * repeats
    angle_step = 2 * math.pi / total_cols
    radial_step = (outer_r - inner_r) / ROWS

    cells: list[tuple[int, list[tuple[float, float]]]] = []

    for rep in range(repeats):
        # Alternate between normal and mirrored grid
        grid = GRID if rep % 2 == 0 else GRID_MIRROR

        for c in range(COLS):
            col_idx = rep * COLS + c
            a0 = col_idx * angle_step
            a1 = (col_idx + 1) * angle_step

            for r in range(ROWS):
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


def build_dxf() -> str:
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
    cells = _build_cells(INNER_R, OUTER_R, TILE_REPEATS)
    for color_val, quad in cells:
        lname = COLOR_MAP[color_val][0]
        lines += _dxf_closed_poly(lname, quad)

    lines += ["0", "ENDSEC", "0", "EOF"]
    return "\n".join(lines)


# ── SVG export ────────────────────────────────────────────────────

def build_svg() -> str:
    """Build an SVG preview with filled tile quads."""
    pad = 5
    vb = GREEN_OUTER + pad
    parts: list[str] = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="{-vb} {-vb} {2*vb} {2*vb}" '
        f'width="{2*vb}mm" height="{2*vb}mm">',
        '<title>Rope Rosette (Diagonal Staircase)</title>',
        '<desc>Generated by The Production Shop</desc>',
        f'<circle cx="0" cy="0" r="{OUTER_R}" fill="#1a1008"/>',
        f'<circle cx="0" cy="0" r="{INNER_R}" fill="#0e0b07"/>',
    ]

    cells = _build_cells(INNER_R, OUTER_R, TILE_REPEATS)
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
        # Dimension guide arcs (dashed gold)
        f'<circle cx="0" cy="0" r="{INNER_R}" fill="none" stroke="#c8a032" stroke-width="0.3" stroke-dasharray="2,2"/>',
        f'<circle cx="0" cy="0" r="{OUTER_R}" fill="none" stroke="#c8a032" stroke-width="0.3" stroke-dasharray="2,2"/>',
        # Band width label
        f'<text x="{INNER_R + 0.5:.1f}" y="-1.5" font-size="2.5" fill="#c8a032" font-family="monospace">'
        f'{OUTER_R - INNER_R:.1f}mm rope band</text>',
        # Ring radii labels
        f'<text x="{INNER_R + 0.3:.1f}" y="2.5" font-size="2" fill="#7a5c2e" font-family="monospace">'
        f'r={INNER_R}mm</text>',
        f'<text x="{OUTER_R + 0.3:.1f}" y="2.5" font-size="2" fill="#7a5c2e" font-family="monospace">'
        f'r={OUTER_R}mm</text>',
        # Tile repeat count
        f'<text x="{-vb + 1:.1f}" y="{-vb + 4:.1f}" font-size="2.2" fill="#4a3010" font-family="monospace">'
        f'{TILE_REPEATS} repeats ({TILE_REPEATS//2} normal + {TILE_REPEATS//2} mirrored)</text>',
        # Scale bar 10mm
        f'<line x1="{-vb+1:.1f}" y1="{vb-3:.1f}" x2="{-vb+21:.1f}" y2="{vb-3:.1f}" stroke="#c8a032" stroke-width="0.4"/>',
        f'<text x="{-vb+4:.1f}" y="{vb-1:.1f}" font-size="2" fill="#c8a032" font-family="monospace">10mm</text>',
        '</svg>',
    ]
    return "\n".join(parts)


# ── CSV export ────────────────────────────────────────────────────

def build_csv() -> str:
    """Build CSV with header metadata, veneer BOM, and run-length encoding."""
    mm_w = COLS * 0.5
    mm_h = ROWS * 0.5

    total_cells = COLS * ROWS
    white_total = sum(v for row in GRID for v in row)
    black_total = total_cells - white_total

    header_lines = [
        f"# Rope Rosette Tile · {COLS}x{ROWS} · 0.5mm/sq",
        f"# Diagonal staircase — alternate tiles mirrored for rope twist",
        f"# Tile: {mm_w:.1f}mm x {mm_h:.1f}mm · {TILE_REPEATS}x around ring (even/odd mirrored)",
        f"# 0=black(ebony)  1=white(maple)",
        f"# Total per tile: {black_total}B ({100*black_total/total_cells:.0f}%) / "
        f"{white_total}W ({100*white_total/total_cells:.0f}%)",
        f"#",
        f"# ── VENEER BOM ── (0.5mm/cell)",
        f"# {'Row':>3}  {'mm':>5}  {'Black':>6}  {'White':>6}  Layout",
    ]

    for r, row in enumerate(GRID):
        b = row.count(0)
        w = row.count(1)
        # Run-length encode the row
        rle = []
        cur, run = row[0], 1
        for val in row[1:]:
            if val == cur:
                run += 1
            else:
                rle.append(f"{run}{'B' if cur==0 else 'W'}")
                cur, val_prev = val, cur
                run = 1
        rle.append(f"{run}{'B' if cur==0 else 'W'}")
        header_lines.append(
            f"# {r+1:>3}  {(r+1)*0.5:>5.1f}  {b:>6}  {w:>6}  {' '.join(rle)}"
        )

    header_lines += [
        f"#",
        f"# Mirror tile BOM (odd repeats — columns reversed)",
        f"# {'Row':>3}  {'mm':>5}  {'Black':>6}  {'White':>6}  Layout",
    ]
    for r, row in enumerate(GRID_MIRROR):
        b = row.count(0)
        w = row.count(1)
        rle = []
        cur, run = row[0], 1
        for val in row[1:]:
            if val == cur:
                run += 1
            else:
                rle.append(f"{run}{'B' if cur==0 else 'W'}")
                cur = val
                run = 1
        rle.append(f"{run}{'B' if cur==0 else 'W'}")
        header_lines.append(
            f"# {r+1:>3}  {(r+1)*0.5:>5.1f}  {b:>6}  {w:>6}  {' '.join(rle)}"
        )

    header_lines += [
        f"#",
        f"# ── RING TOTALS (×{TILE_REPEATS} repeats) ──",
        f"# Black: {black_total * TILE_REPEATS:,} cells",
        f"# White: {white_total * TILE_REPEATS:,} cells",
        f"# Total: {total_cells * TILE_REPEATS:,} cells",
        f"#",
        f"# ── GRID DATA ──",
        f"# --- Normal tile (even repeats) ---",
    ]
    for row in GRID:
        header_lines.append(",".join(str(v) for v in row))
    header_lines.append("# --- Mirrored tile (odd repeats) ---")
    for row in GRID_MIRROR:
        header_lines.append(",".join(str(v) for v in row))

    return "\n".join(header_lines) + "\n"


# ── Main ──────────────────────────────────────────────────────────

def main() -> None:
    import os
    # Portable: write next to this script, or override with env var ROSETTE_OUT
    _out = os.environ.get("ROSETTE_OUT", str(Path(__file__).parent))
    docs = Path(_out)
    dl   = Path(_out)
    docs.mkdir(parents=True, exist_ok=True)

    total = COLS * ROWS
    white_count = sum(v for row in GRID for v in row)
    black_count = total - white_count
    total_ring = COLS * ROWS * TILE_REPEATS

    print(f"\n{'='*60}")
    print(f"  ROPE ROSETTE — Diagonal Staircase + Mirror Twist")
    print(f"{'='*60}")
    print(f"  Grid: {COLS}x{ROWS} · 2 colors (black/white)")
    print(f"  Tile: {COLS*0.5:.1f}mm x {ROWS*0.5:.1f}mm")
    print(f"  Black cells  = {black_count:>3}  ({100*black_count/total:.1f}%)")
    print(f"  White cells  = {white_count:>3}  ({100*white_count/total:.1f}%)")
    print(f"  Mirror: alternate tiles flipped horizontally")
    print(f"  Ring: {INNER_R}-{OUTER_R}mm ({OUTER_R-INNER_R}mm band)")
    print(f"  Tile repeats = {TILE_REPEATS}x ({TILE_REPEATS//2} normal + {TILE_REPEATS//2} mirrored)")
    print(f"  Total cells  = {total_ring:,}")
    print(f"{'='*60}")

    # DXF
    print("\nGenerating DXF...")
    dxf_path = docs / "rope_rosette.dxf"
    dxf_content = build_dxf()
    dxf_path.write_text(dxf_content, encoding="utf-8")
    dxf_lines = dxf_content.count("\n") + 1
    print(f"  DXF saved: {dxf_path}  ({dxf_lines:,} lines)")

    # SVG
    print("Generating SVG preview...")
    svg_path = dl / "rope_rosette_preview.svg"
    svg_content = build_svg()
    svg_path.write_text(svg_content, encoding="utf-8")
    print(f"  SVG saved: {svg_path}")

    # CSV
    print("Generating CSV export...")
    csv_path = dl / f"rope_rosette_{COLS}x{ROWS}.csv"
    csv_content = build_csv()
    csv_path.write_text(csv_content, encoding="utf-8")
    print(f"  CSV saved: {csv_path}")

    print(f"\nLayers: ROPE_0 (black), ROPE_1 (white)")
    print("Done.")


if __name__ == "__main__":
    main()
