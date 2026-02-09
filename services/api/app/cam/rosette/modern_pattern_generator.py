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
            "  <desc>Generated by Luthier's ToolBox</desc>",
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
        """Calculate bill of materials (area per color/material)."""
        bom: Dict[str, float] = {}

        for ring in self.spec.rings:
            inner_r = ring.inner_diameter_mm / 2
            outer_r = ring.outer_diameter_mm / 2
            ring_area = math.pi * (outer_r**2 - inner_r**2)

            if ring.pattern_type == PatternType.SOLID:
                bom[ring.primary_color] = bom.get(ring.primary_color, 0) + ring_area
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
