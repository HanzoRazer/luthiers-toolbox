"""WP-3: Modern (parametric) rosette pattern generator.

Extracted from pattern_generator.py to reduce god-object size.
Generates CAD-based parametric patterns with DXF R12 and SVG export.
"""
from __future__ import annotations

import math
from typing import Dict, List, Optional

from .pattern_schemas import (
    PatternType,
    RingSpec,
    RosetteSpec,
    Point2D,
    PathSegment,
    ModernPatternResult,
)


class ModernPatternGenerator:
    """Generator for modern CAD-based parametric patterns."""

    def __init__(self, spec: RosetteSpec):
        self.spec = spec
        errors = spec.validate()
        if errors:
            raise ValueError(f"Invalid spec: {'; '.join(errors)}")

    def _generate_circle(
        self, cx: float, cy: float, radius: float, segments: int = 72
    ) -> List[Point2D]:
        """Generate circle as list of points."""
        points = []
        for i in range(segments + 1):
            angle = 2 * math.pi * i / segments
            points.append(
                Point2D(cx + radius * math.cos(angle), cy + radius * math.sin(angle))
            )
        return points

    def _generate_herringbone_ring(self, ring: RingSpec) -> List[PathSegment]:
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

    def _generate_checkerboard_ring(self, ring: RingSpec) -> List[PathSegment]:
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
                Point2D(
                    inner_r * math.cos(start_angle),
                    inner_r * math.sin(start_angle),
                ),
                Point2D(
                    outer_r * math.cos(start_angle),
                    outer_r * math.sin(start_angle),
                ),
                Point2D(
                    outer_r * math.cos(end_angle), outer_r * math.sin(end_angle)
                ),
                Point2D(
                    inner_r * math.cos(end_angle), inner_r * math.sin(end_angle)
                ),
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

    def _generate_solid_ring(self, ring: RingSpec) -> List[PathSegment]:
        """Generate solid ring (inner and outer circles)."""
        inner_r = ring.inner_diameter_mm / 2
        outer_r = ring.outer_diameter_mm / 2

        return [
            PathSegment(
                points=self._generate_circle(0, 0, inner_r),
                is_closed=True,
                layer=f"ring_{ring.ring_index}_inner",
                color=ring.primary_color,
            ),
            PathSegment(
                points=self._generate_circle(0, 0, outer_r),
                is_closed=True,
                layer=f"ring_{ring.ring_index}_outer",
                color=ring.primary_color,
            ),
        ]

    def _generate_rope_ring(self, ring: RingSpec) -> List[PathSegment]:
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
                    color=ring.primary_color
                    if strand % 2 == 0
                    else ring.secondary_color,
                )
            )

        return paths

    # ================================================================
    # Grid-to-annulus mapping (shared by wave, spanish, celtic, rope)
    # ================================================================

    @staticmethod
    def _grid_to_annulus_paths(
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
        Ported from prototype _build_cells() functions.

        Args:
            grid: 2D integer grid (rows × cols), values are color keys.
            inner_r: Inner radius of the pattern ring (mm).
            outer_r: Outer radius of the pattern ring (mm).
            repeats: How many times the tile repeats around the annulus.
            color_map: Maps grid integer values to color strings.
            layer_prefix: DXF layer prefix for these tiles.
            mirror_alternation: If True, alternate repeats flip grid cols
                                (rope twist effect).
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

    # ================================================================
    # Wave pattern — asymmetric crashing arch formula
    # ================================================================

    @staticmethod
    def _build_wave_grid(
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

        Ported from prototype generate_wave_rosette.py.
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

    def _generate_wave_ring(self, ring: RingSpec) -> List[PathSegment]:
        """Generate wave pattern for a ring using grid-to-annulus mapping."""
        inner_r = ring.inner_diameter_mm / 2
        outer_r = ring.outer_diameter_mm / 2

        if ring.grid is not None:
            grid = ring.grid
        else:
            grid = self._build_wave_grid()

        avg_circ = math.pi * (inner_r + outer_r)
        cols = len(grid[0]) if grid else 52
        repeats = ring.grid_repeats or max(1, round(avg_circ / (cols * 0.5)))

        color_map = {
            0: "#1a1008",  # background (black)
            1: "#f0e8d0",  # strand A (cream)
            2: "#8b2020",  # strand B (red)
            3: "#2d6a4f",  # strand C (green)
        }

        return self._grid_to_annulus_paths(
            grid, inner_r, outer_r, repeats, color_map,
            f"ring_{ring.ring_index}_wave",
        )

    # ================================================================
    # Spanish right-angle pattern — grid-based mosaic
    # ================================================================

    # Default 23×15 Spanish grid (0=black, 1=white, 2=blue)
    SPANISH_GRID = [
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

    def _generate_spanish_ring(self, ring: RingSpec) -> List[PathSegment]:
        """Generate Spanish right-angle pattern using grid-to-annulus mapping."""
        inner_r = ring.inner_diameter_mm / 2
        outer_r = ring.outer_diameter_mm / 2

        grid = ring.grid if ring.grid is not None else self.SPANISH_GRID

        avg_circ = math.pi * (inner_r + outer_r)
        cols = len(grid[0]) if grid else 23
        repeats = ring.grid_repeats or max(1, round(avg_circ / (cols * 0.5)))

        color_map = {
            0: "#1a1008",  # black
            1: "#f5efe0",  # white
            2: "#2e6da4",  # blue
        }

        return self._grid_to_annulus_paths(
            grid, inner_r, outer_r, repeats, color_map,
            f"ring_{ring.ring_index}_spanish",
        )

    # ================================================================
    # Celtic knot — tile library with interlace grids
    # ================================================================

    # Built-in celtic tile library (from rosette-grid-designer v4 mothership)
    CELTIC_TILES = {
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

    def _generate_celtic_ring(self, ring: RingSpec) -> List[PathSegment]:
        """Generate celtic knot pattern using grid-to-annulus mapping."""
        inner_r = ring.inner_diameter_mm / 2
        outer_r = ring.outer_diameter_mm / 2

        if ring.grid is not None:
            grid = ring.grid
        else:
            grid = self.CELTIC_TILES["square8"]

        avg_circ = math.pi * (inner_r + outer_r)
        cols = len(grid[0]) if grid else 8
        repeats = ring.grid_repeats or max(1, round(avg_circ / (cols * 0.5)))

        color_map = {
            0: "#1a1008",  # background
            1: "#f5efe0",  # knot strand
        }

        return self._grid_to_annulus_paths(
            grid, inner_r, outer_r, repeats, color_map,
            f"ring_{ring.ring_index}_celtic",
        )

    # ================================================================
    # Dispatch
    # ================================================================

    def generate_ring_paths(self, ring: RingSpec) -> List[PathSegment]:
        """Generate paths for a single ring based on pattern type."""
        if ring.pattern_type == PatternType.HERRINGBONE:
            return self._generate_herringbone_ring(ring)
        elif ring.pattern_type == PatternType.CHECKERBOARD:
            return self._generate_checkerboard_ring(ring)
        elif ring.pattern_type == PatternType.SOLID:
            return self._generate_solid_ring(ring)
        elif ring.pattern_type == PatternType.ROPE:
            return self._generate_rope_ring(ring)
        elif ring.pattern_type == PatternType.WAVE:
            return self._generate_wave_ring(ring)
        elif ring.pattern_type == PatternType.SPANISH:
            return self._generate_spanish_ring(ring)
        elif ring.pattern_type == PatternType.CELTIC_KNOT:
            return self._generate_celtic_ring(ring)
        else:
            return self._generate_solid_ring(ring)

    def _export_dxf(self, paths: List[PathSegment]) -> str:
        """Export paths to DXF R12 format."""
        lines = []

        # Header
        lines.extend(
            [
                "0", "SECTION",
                "2", "HEADER",
                "9", "$ACADVER",
                "1", "AC1009",  # R12
                "9", "$INSUNITS",
                "70", "4",  # mm
                "0", "ENDSEC",
            ]
        )

        # Tables section (layers)
        lines.extend(
            ["0", "SECTION", "2", "TABLES", "0", "TABLE", "2", "LAYER"]
        )

        layers = set(p.layer for p in paths)
        for layer in layers:
            lines.extend(
                ["0", "LAYER", "2", layer, "70", "0", "62", "7", "6", "CONTINUOUS"]
            )

        lines.extend(["0", "ENDTAB", "0", "ENDSEC"])

        # Entities section
        lines.extend(["0", "SECTION", "2", "ENTITIES"])

        for path in paths:
            if len(path.points) < 2:
                continue

            if path.is_closed and len(path.points) >= 3:
                lines.extend(
                    ["0", "POLYLINE", "8", path.layer, "66", "1", "70", "1"]
                )
                for pt in path.points:
                    lines.extend(
                        [
                            "0", "VERTEX",
                            "8", path.layer,
                            "10", f"{pt.x:.6f}",
                            "20", f"{pt.y:.6f}",
                        ]
                    )
                lines.extend(["0", "SEQEND"])
            else:
                for i in range(len(path.points) - 1):
                    p1, p2 = path.points[i], path.points[i + 1]
                    lines.extend(
                        [
                            "0", "LINE",
                            "8", path.layer,
                            "10", f"{p1.x:.6f}",
                            "20", f"{p1.y:.6f}",
                            "11", f"{p2.x:.6f}",
                            "21", f"{p2.y:.6f}",
                        ]
                    )

        lines.extend(["0", "ENDSEC", "0", "EOF"])

        return "\n".join(lines)

    def _export_svg(self, paths: List[PathSegment]) -> str:
        """Export paths to SVG format."""
        all_x = [p.x for path in paths for p in path.points]
        all_y = [p.y for path in paths for p in path.points]

        if not all_x:
            min_x, max_x, min_y, max_y = -50, 50, -50, 50
        else:
            min_x, max_x = min(all_x), max(all_x)
            min_y, max_y = min(all_y), max(all_y)

        padding = 5
        width = max_x - min_x + 2 * padding
        height = max_y - min_y + 2 * padding

        svg_lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<svg xmlns="http://www.w3.org/2000/svg" ',
            f'     viewBox="{min_x - padding} {min_y - padding} {width} {height}"',
            f'     width="{width}mm" height="{height}mm">',
            f"  <title>Rosette Pattern - {self.spec.name}</title>",
            "  <desc>Generated by The Production Shop</desc>",
        ]

        for i, path in enumerate(paths):
            if len(path.points) < 2:
                continue

            points_str = " ".join(f"{p.x:.3f},{p.y:.3f}" for p in path.points)

            if path.is_closed:
                svg_lines.append(
                    f'  <polygon points="{points_str}" '
                    f'fill="none" stroke="{path.color}" stroke-width="0.2"/>'
                )
            else:
                svg_lines.append(
                    f'  <polyline points="{points_str}" '
                    f'fill="none" stroke="{path.color}" stroke-width="0.2"/>'
                )

        svg_lines.append("</svg>")
        return "\n".join(svg_lines)

    def _calculate_bom(self, paths: List[PathSegment]) -> Dict[str, float]:
        """Calculate bill of materials (area per color/material).

        For grid-based patterns (wave, spanish, celtic), counts tile areas
        by color from the actual generated paths. For other patterns, uses
        the ring-area split heuristic.
        """
        bom: Dict[str, float] = {}
        grid_types = {PatternType.WAVE, PatternType.SPANISH, PatternType.CELTIC_KNOT}

        for ring in self.spec.rings:
            inner_r = ring.inner_diameter_mm / 2
            outer_r = ring.outer_diameter_mm / 2
            ring_area = math.pi * (outer_r**2 - inner_r**2)

            if ring.pattern_type == PatternType.SOLID:
                bom[ring.primary_color] = bom.get(ring.primary_color, 0) + ring_area
            elif ring.pattern_type in grid_types and ring.grid is not None:
                # Count actual grid cell ratios for grid-based patterns
                grid = ring.grid
                total_cells = sum(len(row) for row in grid)
                if total_cells > 0:
                    counts: Dict[int, int] = {}
                    for row in grid:
                        for val in row:
                            counts[val] = counts.get(val, 0) + 1
                    for val, count in counts.items():
                        color_label = f"grid_color_{val}"
                        bom[color_label] = bom.get(color_label, 0) + ring_area * count / total_cells
            else:
                half_area = ring_area / 2
                bom[ring.primary_color] = bom.get(ring.primary_color, 0) + half_area
                bom[ring.secondary_color] = (
                    bom.get(ring.secondary_color, 0) + half_area
                )

        return bom

    def generate(
        self, include_dxf: bool = True, include_svg: bool = True
    ) -> ModernPatternResult:
        """Generate complete modern pattern result."""
        all_paths = []

        for ring in self.spec.rings:
            ring_paths = self.generate_ring_paths(ring)
            all_paths.extend(ring_paths)

        bom = self._calculate_bom(all_paths)

        total_segments = sum(
            len(p.points) - 1 for p in all_paths if len(p.points) > 1
        )
        cut_time = total_segments / 100

        result = ModernPatternResult(
            spec=self.spec,
            paths=all_paths,
            bom=bom,
            estimated_cut_time_min=round(cut_time, 1),
            notes=[
                f"Generated {len(all_paths)} path segments",
                f"Total rings: {len(self.spec.rings)}",
            ],
        )

        if include_dxf:
            result.dxf_content = self._export_dxf(all_paths)

        if include_svg:
            result.svg_content = self._export_svg(all_paths)

        return result
