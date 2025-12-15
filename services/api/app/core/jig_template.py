from __future__ import annotations

import math
from typing import Dict

from app.schemas.jig_template import JigRingSpec, JigTemplate
from app.schemas.rosette_pattern import RosettePatternInDB, RosetteRingBand


def _ring_specs(
    rings: list[RosetteRingBand],
    guitars: int,
    tile_length_mm: float,
    scrap_factor: float,
) -> tuple[list[JigRingSpec], int]:
    specs: list[JigRingSpec] = []
    total_tiles = 0

    for ring in sorted(rings, key=lambda r: r.index):
        ring_tile_len = ring.tile_length_override_mm or tile_length_mm
        circumference = 2.0 * math.pi * float(ring.radius_mm)
        tiles_per_guitar = max(1, math.ceil(circumference / ring_tile_len))
        tiles_all = math.ceil(tiles_per_guitar * guitars * (1.0 + scrap_factor))
        total_tiles += tiles_all

        specs.append(
            JigRingSpec(
                ring_index=ring.index,
                strip_family_id=ring.strip_family_id,
                radius_mm=ring.radius_mm,
                width_mm=ring.width_mm,
                circumference_mm=circumference,
                tiles_per_guitar=tiles_per_guitar,
                tile_length_mm=ring_tile_len,
                slice_angle_deg=ring.slice_angle_deg,
                color_hint=ring.color_hint,
            )
        )

    return specs, total_tiles


def build_jig_template(
    pattern: RosettePatternInDB,
    guitars: int = 1,
    tile_length_mm: float = 8.0,
    scrap_factor: float = 0.12,
) -> Dict[str, object]:
    """Build a jig template payload from a rosette pattern."""

    specs, total_tiles = _ring_specs(
        rings=pattern.ring_bands,
        guitars=guitars,
        tile_length_mm=tile_length_mm,
        scrap_factor=scrap_factor,
    )

    jig = JigTemplate(
        pattern_id=pattern.id,
        pattern_name=pattern.name,
        guitars=guitars,
        tile_length_mm=tile_length_mm,
        scrap_factor=scrap_factor,
        base_center_x_mm=pattern.center_x_mm,
        base_center_y_mm=pattern.center_y_mm,
        rings=specs,
        total_tiles_all_rings=total_tiles,
        notes="Jig template derived from current pattern parameters.",
    )
    return jig.model_dump()
