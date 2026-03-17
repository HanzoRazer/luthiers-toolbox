"""Pure geometry for modern rosette patterns: arc math, segment calculations, grid-to-annulus mapping."""
from __future__ import annotations

import math
from typing import Dict, List

from .pattern_schemas import PathSegment, Point2D, RingSpec


def generate_circle(
    cx: float, cy: float, radius: float, segments: int = 72
) -> List[Point2D]:
    """Generate circle as list of points."""
    points = []
    for i in range(segments + 1):
        angle = 2 * math.pi * i / segments
        points.append(
            Point2D(cx + radius * math.cos(angle), cy + radius * math.sin(angle))
        )
    return points


def grid_to_annulus_paths(
    grid: List[List[int]],
    inner_r: float,
    outer_r: float,
    repeats: int,
    color_map: Dict[int, str],
    layer_prefix: str,
    mirror_alternation: bool = False,
) -> List[PathSegment]:
    """
    Map a rectangular tile grid onto the annulus as closed trapezoid quads.

    Cols → angular divisions, rows → radial bands.
    Each cell becomes a 4-corner closed polygon (PathSegment).
    """
    rows = len(grid)
    cols = len(grid[0])
    total_cols = cols * repeats
    angle_step = 2 * math.pi / total_cols
    radial_step = (outer_r - inner_r) / rows

    mirror_grid = [list(reversed(row)) for row in grid]
    paths: List[PathSegment] = []

    for rep in range(repeats):
        use_grid = grid if (not mirror_alternation or rep % 2 == 0) else mirror_grid

        for c in range(cols):
            col_idx = rep * cols + c
            a0 = col_idx * angle_step
            a1 = (col_idx + 1) * angle_step

            for r in range(rows):
                color_val = use_grid[r][c]
                r0 = inner_r + r * radial_step
                r1 = inner_r + (r + 1) * radial_step

                points = [
                    Point2D(r0 * math.cos(a0), r0 * math.sin(a0)),
                    Point2D(r1 * math.cos(a0), r1 * math.sin(a0)),
                    Point2D(r1 * math.cos(a1), r1 * math.sin(a1)),
                    Point2D(r0 * math.cos(a1), r0 * math.sin(a1)),
                ]

                paths.append(
                    PathSegment(
                        points=points,
                        is_closed=True,
                        layer=f"{layer_prefix}_{color_val}",
                        color=color_map.get(color_val, "#808080"),
                    )
                )

    return paths


def build_wave_grid(
    cols: int = 52,
    rows: int = 18,
    amplitude: float = 6.0,
    seg_len: float = 18.0,
    gap: float = 2.0,
    skew: float = 0.72,
    chase: float = 13.0,
    d: float = 4.0,
    strand_w: float = 1.8,
    num_strands: int = 7,
) -> List[List[int]]:
    """
    Build crashing wave grid using asymmetric arch formula.

    Swell side (x < peakX):  A · sin(π/2 · x / peakX)
    Crash side (x ≥ peakX):  A · cos(π/2 · (x − peakX) / (segLen − peakX))
    """
    pitch = seg_len + gap

    def arch_y(local_x: float) -> float:
        peak_x = skew * seg_len
        if peak_x <= 0 or seg_len <= 0:
            return 0.0
        if local_x <= peak_x:
            return amplitude * math.sin((math.pi / 2) * (local_x / peak_x))
        return amplitude * math.cos(
            (math.pi / 2) * ((local_x - peak_x) / (seg_len - peak_x))
        )

    grid: List[List[int]] = []
    for r in range(rows):
        row: List[int] = []
        for c in range(cols):
            hit = False
            hit_n = 0
            for n in range(-2, num_strands + 3):
                offset = ((n * chase) % pitch + pitch * 100) % pitch
                x_shifted = ((c - offset) % pitch + pitch * 100) % pitch
                if x_shifted >= seg_len:
                    continue
                cy = n * d + arch_y(x_shifted)
                if abs(r - cy) < strand_w / 2:
                    hit = True
                    hit_n = n
                    break
            if hit:
                idx = ((hit_n % 3) + 3) % 3
                row.append(1 if idx == 0 else (2 if idx == 1 else 3))
            else:
                row.append(0)
        grid.append(row)
    return grid


# Default 23×15 Spanish grid (0=black, 1=white, 2=blue)
SPANISH_GRID: List[List[int]] = [
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

# Built-in celtic tile library (from rosette-grid-designer v4 mothership)
CELTIC_TILES: Dict[str, List[List[int]]] = {
    "square8": [
        [0,0,1,1,1,1,0,0],[0,1,1,0,0,1,1,0],
        [1,1,0,0,0,0,1,1],[1,0,0,1,1,0,0,1],
        [1,0,0,1,1,0,0,1],[1,1,0,0,0,0,1,1],
        [0,1,1,0,0,1,1,0],[0,0,1,1,1,1,0,0],
    ],
    "braid8": [
        [1,1,0,1,1,0,1,1],[1,0,0,1,0,0,1,0],
        [0,0,1,0,0,1,0,0],[0,1,1,0,1,1,0,1],
        [1,1,0,1,1,0,1,1],[1,0,0,1,0,0,1,0],
        [0,0,1,0,0,1,0,0],[0,1,1,0,1,1,0,1],
    ],
    "step12": [
        [0,0,0,0,0,0,0,0,0,0,0,0],
        [0,1,1,1,1,1,1,1,1,1,1,0],
        [0,1,0,0,0,0,0,0,0,0,1,0],
        [0,1,0,1,1,1,1,1,1,0,1,0],
        [0,1,0,1,0,0,0,0,1,0,1,0],
        [0,1,0,1,0,1,1,0,1,0,1,0],
        [0,1,0,1,0,1,1,0,1,0,1,0],
        [0,1,0,1,0,0,0,0,1,0,1,0],
        [0,1,0,1,1,1,1,1,1,0,1,0],
        [0,1,0,0,0,0,0,0,0,0,1,0],
        [0,1,1,1,1,1,1,1,1,1,1,0],
        [0,0,0,0,0,0,0,0,0,0,0,0],
    ],
    "rosette16": [
        [0,0,0,0,1,1,1,1,1,1,1,1,0,0,0,0],
        [0,0,0,1,1,0,0,0,0,0,0,1,1,0,0,0],
        [0,0,1,1,0,0,1,1,1,1,0,0,1,1,0,0],
        [0,1,1,0,0,1,1,0,0,1,1,0,0,1,1,0],
        [1,1,0,0,1,1,0,0,0,0,1,1,0,0,1,1],
        [1,0,0,1,1,0,0,1,1,0,0,1,1,0,0,1],
        [1,0,1,1,0,0,1,1,1,1,0,0,1,1,0,1],
        [1,1,1,0,0,1,1,0,0,1,1,0,0,1,1,1],
        [1,1,1,0,0,1,1,0,0,1,1,0,0,1,1,1],
        [1,0,1,1,0,0,1,1,1,1,0,0,1,1,0,1],
        [1,0,0,1,1,0,0,1,1,0,0,1,1,0,0,1],
        [1,1,0,0,1,1,0,0,0,0,1,1,0,0,1,1],
        [0,1,1,0,0,1,1,0,0,1,1,0,0,1,1,0],
        [0,0,1,1,0,0,1,1,1,1,0,0,1,1,0,0],
        [0,0,0,1,1,0,0,0,0,0,0,1,1,0,0,0],
        [0,0,0,0,1,1,1,1,1,1,1,1,0,0,0,0],
    ],
}


def generate_herringbone_ring_paths(ring: RingSpec) -> List[PathSegment]:
    """Generate herringbone pattern for a ring."""
    paths = []
    inner_r = ring.inner_diameter_mm / 2
    outer_r = ring.outer_diameter_mm / 2
    avg_r = (inner_r + outer_r) / 2
    circumference = 2 * math.pi * avg_r
    tile_count = max(1, int(circumference / ring.tile_width_mm))
    angle_step = 2 * math.pi / tile_count
    tile_angle = math.radians(ring.tile_angle_deg)

    for i in range(tile_count):
        base_angle = i * angle_step
        if i % 2 == 0:
            p1 = Point2D(
                inner_r * math.cos(base_angle - tile_angle / 2),
                inner_r * math.sin(base_angle - tile_angle / 2),
            )
            p2 = Point2D(
                outer_r * math.cos(base_angle + tile_angle / 2),
                outer_r * math.sin(base_angle + tile_angle / 2),
            )
        else:
            p1 = Point2D(
                inner_r * math.cos(base_angle + tile_angle / 2),
                inner_r * math.sin(base_angle + tile_angle / 2),
            )
            p2 = Point2D(
                outer_r * math.cos(base_angle - tile_angle / 2),
                outer_r * math.sin(base_angle - tile_angle / 2),
            )
        paths.append(
            PathSegment(
                points=[p1, p2],
                is_closed=False,
                layer=f"ring_{ring.ring_index}",
                color=ring.primary_color if i % 2 == 0 else ring.secondary_color,
            )
        )
    return paths


def generate_checkerboard_ring_paths(ring: RingSpec) -> List[PathSegment]:
    """Generate checkerboard pattern for a ring."""
    paths = []
    inner_r = ring.inner_diameter_mm / 2
    outer_r = ring.outer_diameter_mm / 2
    avg_r = (inner_r + outer_r) / 2
    circumference = 2 * math.pi * avg_r
    tile_count = max(4, int(circumference / ring.tile_width_mm))
    tile_count = tile_count + (tile_count % 2)
    angle_step = 2 * math.pi / tile_count

    for i in range(tile_count):
        start_angle = i * angle_step
        end_angle = (i + 1) * angle_step
        points = [
            Point2D(inner_r * math.cos(start_angle), inner_r * math.sin(start_angle)),
            Point2D(outer_r * math.cos(start_angle), outer_r * math.sin(start_angle)),
            Point2D(outer_r * math.cos(end_angle), outer_r * math.sin(end_angle)),
            Point2D(inner_r * math.cos(end_angle), inner_r * math.sin(end_angle)),
        ]
        paths.append(
            PathSegment(
                points=points,
                is_closed=True,
                layer=f"ring_{ring.ring_index}",
                color=ring.primary_color if i % 2 == 0 else ring.secondary_color,
            )
        )
    return paths


def generate_solid_ring_paths(ring: RingSpec) -> List[PathSegment]:
    """Generate solid ring (inner and outer circles)."""
    inner_r = ring.inner_diameter_mm / 2
    outer_r = ring.outer_diameter_mm / 2
    return [
        PathSegment(
            points=generate_circle(0, 0, inner_r),
            is_closed=True,
            layer=f"ring_{ring.ring_index}_inner",
            color=ring.primary_color,
        ),
        PathSegment(
            points=generate_circle(0, 0, outer_r),
            is_closed=True,
            layer=f"ring_{ring.ring_index}_outer",
            color=ring.primary_color,
        ),
    ]


def generate_rope_ring_paths(ring: RingSpec) -> List[PathSegment]:
    """Generate rope pattern for a ring using spiral curves."""
    paths = []
    inner_r = ring.inner_diameter_mm / 2
    outer_r = ring.outer_diameter_mm / 2
    ring_width = outer_r - inner_r
    strand_count = max(2, int(ring_width / ring.tile_width_mm))
    twist_count = 8
    segments_per_twist = 12

    for strand in range(strand_count):
        points = []
        strand_offset = strand / strand_count
        for i in range(twist_count * segments_per_twist + 1):
            t = i / (twist_count * segments_per_twist)
            theta = 2 * math.pi * t
            rope_phase = (
                2 * math.pi * twist_count * t + strand_offset * 2 * math.pi
            )
            r = inner_r + ring_width * (0.5 + 0.3 * math.sin(rope_phase))
            points.append(Point2D(r * math.cos(theta), r * math.sin(theta)))
        paths.append(
            PathSegment(
                points=points,
                is_closed=False,
                layer=f"ring_{ring.ring_index}_strand_{strand}",
                color=ring.primary_color if strand % 2 == 0 else ring.secondary_color,
            )
        )
    return paths


def generate_wave_ring_paths(
    ring: RingSpec, grid: List[List[int]] | None = None
) -> List[PathSegment]:
    """Generate wave pattern for a ring using grid-to-annulus mapping."""
    inner_r = ring.inner_diameter_mm / 2
    outer_r = ring.outer_diameter_mm / 2
    if grid is None:
        grid = build_wave_grid()
    avg_circ = math.pi * (inner_r + outer_r)
    cols = len(grid[0]) if grid else 52
    repeats = ring.grid_repeats or max(1, round(avg_circ / (cols * 0.5)))
    color_map = {
        0: "#1a1008",
        1: "#f0e8d0",
        2: "#8b2020",
        3: "#2d6a4f",
    }
    return grid_to_annulus_paths(
        grid, inner_r, outer_r, repeats, color_map,
        f"ring_{ring.ring_index}_wave",
    )


def generate_spanish_ring_paths(
    ring: RingSpec, grid: List[List[int]] | None = None
) -> List[PathSegment]:
    """Generate Spanish right-angle pattern using grid-to-annulus mapping."""
    inner_r = ring.inner_diameter_mm / 2
    outer_r = ring.outer_diameter_mm / 2
    if grid is None:
        grid = SPANISH_GRID
    avg_circ = math.pi * (inner_r + outer_r)
    cols = len(grid[0]) if grid else 23
    repeats = ring.grid_repeats or max(1, round(avg_circ / (cols * 0.5)))
    color_map = {0: "#1a1008", 1: "#f5efe0", 2: "#2e6da4"}
    return grid_to_annulus_paths(
        grid, inner_r, outer_r, repeats, color_map,
        f"ring_{ring.ring_index}_spanish",
    )


def generate_celtic_ring_paths(
    ring: RingSpec, grid: List[List[int]] | None = None
) -> List[PathSegment]:
    """Generate celtic knot pattern using grid-to-annulus mapping."""
    inner_r = ring.inner_diameter_mm / 2
    outer_r = ring.outer_diameter_mm / 2
    if grid is None:
        grid = CELTIC_TILES["square8"]
    avg_circ = math.pi * (inner_r + outer_r)
    cols = len(grid[0]) if grid else 8
    repeats = ring.grid_repeats or max(1, round(avg_circ / (cols * 0.5)))
    color_map = {0: "#1a1008", 1: "#f5efe0"}
    return grid_to_annulus_paths(
        grid, inner_r, outer_r, repeats, color_map,
        f"ring_{ring.ring_index}_celtic",
    )


__all__ = [
    "generate_circle",
    "grid_to_annulus_paths",
    "build_wave_grid",
    "SPANISH_GRID",
    "CELTIC_TILES",
    "generate_herringbone_ring_paths",
    "generate_checkerboard_ring_paths",
    "generate_solid_ring_paths",
    "generate_rope_ring_paths",
    "generate_wave_ring_paths",
    "generate_spanish_ring_paths",
    "generate_celtic_ring_paths",
]
