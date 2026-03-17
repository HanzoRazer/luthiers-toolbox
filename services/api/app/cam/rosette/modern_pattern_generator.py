"""WP-3: Modern (parametric) rosette pattern generator.

Orchestrator: delegates geometry to pattern_geometry and rendering to pattern_renderer.
Generates CAD-based parametric patterns with DXF R12 and SVG export.
"""
from __future__ import annotations

import math
from typing import Dict, List

from .pattern_schemas import (
    ModernPatternResult,
    PathSegment,
    PatternType,
    RingSpec,
    RosetteSpec,
)
from .pattern_geometry import (
    generate_celtic_ring_paths,
    generate_checkerboard_ring_paths,
    generate_herringbone_ring_paths,
    generate_rope_ring_paths,
    generate_solid_ring_paths,
    generate_spanish_ring_paths,
    generate_wave_ring_paths,
)
from .pattern_renderer import export_paths_to_dxf, export_paths_to_svg


class ModernPatternGenerator:
    """Generator for modern CAD-based parametric patterns."""

    def __init__(self, spec: RosetteSpec):
        self.spec = spec
        errors = spec.validate()
        if errors:
            raise ValueError(f"Invalid spec: {'; '.join(errors)}")

    def generate_ring_paths(self, ring: RingSpec) -> List[PathSegment]:
        """Generate paths for a single ring based on pattern type."""
        if ring.pattern_type == PatternType.HERRINGBONE:
            return generate_herringbone_ring_paths(ring)
        if ring.pattern_type == PatternType.CHECKERBOARD:
            return generate_checkerboard_ring_paths(ring)
        if ring.pattern_type == PatternType.SOLID:
            return generate_solid_ring_paths(ring)
        if ring.pattern_type == PatternType.ROPE:
            return generate_rope_ring_paths(ring)
        if ring.pattern_type == PatternType.WAVE:
            return generate_wave_ring_paths(ring, ring.grid)
        if ring.pattern_type == PatternType.SPANISH:
            return generate_spanish_ring_paths(ring, ring.grid)
        if ring.pattern_type == PatternType.CELTIC_KNOT:
            return generate_celtic_ring_paths(ring, ring.grid)
        return generate_solid_ring_paths(ring)

    def _calculate_bom(self, paths: List[PathSegment]) -> Dict[str, float]:
        """Calculate bill of materials (area per color/material)."""
        bom: Dict[str, float] = {}
        grid_types = {PatternType.WAVE, PatternType.SPANISH, PatternType.CELTIC_KNOT}

        for ring in self.spec.rings:
            inner_r = ring.inner_diameter_mm / 2
            outer_r = ring.outer_diameter_mm / 2
            ring_area = math.pi * (outer_r**2 - inner_r**2)

            if ring.pattern_type == PatternType.SOLID:
                bom[ring.primary_color] = bom.get(ring.primary_color, 0) + ring_area
            elif ring.pattern_type in grid_types and ring.grid is not None:
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
                bom[ring.secondary_color] = bom.get(ring.secondary_color, 0) + half_area
        return bom

    def generate(
        self, include_dxf: bool = True, include_svg: bool = True
    ) -> ModernPatternResult:
        """Generate complete modern pattern result."""
        all_paths: List[PathSegment] = []
        for ring in self.spec.rings:
            all_paths.extend(self.generate_ring_paths(ring))

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
            result.dxf_content = export_paths_to_dxf(all_paths)
        if include_svg:
            result.svg_content = export_paths_to_svg(
                all_paths, title=f"Rosette Pattern - {self.spec.name}"
            )
        return result
