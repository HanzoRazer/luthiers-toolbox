#!/usr/bin/env python3
"""
Generate a Spanish Right-Angle rosette DXF + SVG.

The 23×15 grid is tiled around the annulus as actual trapezoid cells —
23 columns map to angular divisions, 15 rows map to radial bands.
Each cell is a closed quad colored by its grid value (0=black, 1=white, 2=blue).
The tile is repeated N times around the ring to fill the circumference.

Pattern source: JSX rosette-grid-designer Spanish preset (23×15, 3 colors).
"""

import math
from pathlib import Path

# ── Ring dimensions (mm) — same as rope / wave rosettes ───────────
SOUNDHOLE_R   = 40.8
INNER_R       = 41.8
OUTER_R       = 47.8
EBONY_INNER   = 47.8
EBONY_OUTER   = 49.3
GREEN_INNER   = 49.3
GREEN_OUTER   = 50.8

# ── Spanish grid (23×15, values: 0=black, 1=white, 2=blue) ───────
GRID = [
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
]
COLS = 23
ROWS = 15

# How many times the full 23-column tile repeats around the ring.
# Average circumference ≈ π × (41.8+47.8) = ~281 mm.
# With 23 cols per tile at ~0.5 mm each ≈ 11.5 mm tile width ⇒ ~24 repeats.
TILE_REPEATS = 24

# Color-value → (layer_name, DXF ACI color)
COLOR_MAP = {
    0: ("SPANISH_0", 250),   # black
    1: ("SPANISH_1",  51),   # white
    2: ("SPANISH_2", 150),   # blue
}

# SVG fills
_SVG_FILL = {0: "#1a1008", 1: "#f5efe0", 2: "#2e6da4"}


# ── Tile-cell geometry ────────────────────────────────────────────

def _build_cells(inner_r: float, outer_r: float,
                 repeats: int) -> list[tuple[int, list[tuple[float, float]]]]:
    """
    Map the 23×15 grid onto the annulus as closed trapezoid quads.

    Returns list of (color_value, [(x,y) × 4]) for every cell.
    23 cols × repeats = total angular divisions.
    15 rows = radial bands from inner_r to outer_r.
    """
    total_cols = COLS * repeats
    angle_step = 2 * math.pi / total_cols
    radial_step = (outer_r - inner_r) / ROWS

    cells: list[tuple[int, list[tuple[float, float]]]] = []

    for rep in range(repeats):
        for c in range(COLS):
            col_idx = rep * COLS + c
            a0 = col_idx * angle_step
            a1 = (col_idx + 1) * angle_step

            for r in range(ROWS):
                color_val = GRID[r][c]
                r0 = inner_r + r * radial_step
                r1 = inner_r + (r + 1) * radial_step

                # Four corners of the trapezoid (inner-left, outer-left, outer-right, inner-right)
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
        '<title>Spanish Right-Angle Rosette</title>',
        '<desc>Generated by The Production Shop</desc>',
        # Background ring fill
        f'<circle cx="0" cy="0" r="{OUTER_R}" fill="#1a1008"/>',
        f'<circle cx="0" cy="0" r="{INNER_R}" fill="#0e0b07"/>',
    ]

    # Filled tile quads
    cells = _build_cells(INNER_R, OUTER_R, TILE_REPEATS)
    for color_val, quad in cells:
        fill = _SVG_FILL[color_val]
        pts = " ".join(f"{x:.3f},{y:.3f}" for x, y in quad)
        parts.append(
            f'<polygon points="{pts}" fill="{fill}" stroke="{fill}" stroke-width="0.02"/>'
        )

    # Structural rings on top
    parts += [
        f'<circle cx="0" cy="0" r="{SOUNDHOLE_R}" fill="#0e0b07" stroke="#3a2e1a" stroke-width="0.3"/>',
        f'<circle cx="0" cy="0" r="{INNER_R}" fill="none" stroke="#3a2e1a" stroke-width="0.3"/>',
        f'<circle cx="0" cy="0" r="{OUTER_R}" fill="none" stroke="#c8a032" stroke-width="0.3"/>',
        f'<circle cx="0" cy="0" r="{EBONY_OUTER}" fill="none" stroke="#1a1008" stroke-width="1.5"/>',
        f'<circle cx="0" cy="0" r="{GREEN_OUTER}" fill="none" stroke="#2d6a4f" stroke-width="1.5"/>',
        '</svg>',
    ]
    return "\n".join(parts)


# ── Main ──────────────────────────────────────────────────────────

def main() -> None:
    docs = Path(r"C:\Users\thepr\Downloads\luthiers-toolbox\docs")

    dxf_path = docs / "spanish_rosette.dxf"
    dxf_content = build_dxf()
    dxf_path.write_text(dxf_content, encoding="utf-8")
    dxf_lines = dxf_content.count("\n") + 1
    print(f"DXF saved: {dxf_path}  ({dxf_lines} lines)")

    svg_path = Path(r"C:\Users\thepr\Downloads") / "spanish_rosette_preview.svg"
    svg_content = build_svg()
    svg_path.write_text(svg_content, encoding="utf-8")
    print(f"SVG saved: {svg_path}")

    total_cells = COLS * ROWS * TILE_REPEATS
    print(f"\nSpanish Right-Angle Rosette (Checkerboard Tile)")
    print(f"  Grid: {COLS}×{ROWS}, 3 colors (black/white/blue)")
    print(f"  Tile repeats: {TILE_REPEATS}× around ring")
    print(f"  Total cells: {total_cells}")
    print(f"  Pattern zone: {INNER_R}–{OUTER_R} mm  (width {OUTER_R - INNER_R} mm)")
    print(f"  Layers: SPANISH_0 (black), SPANISH_1 (white), SPANISH_2 (blue)")


if __name__ == "__main__":
    main()
