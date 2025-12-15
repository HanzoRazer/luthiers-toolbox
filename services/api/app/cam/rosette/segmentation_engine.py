# Patch N12.0 - Tile segmentation engine (skeleton implementation)
#
# This replaces the ad-hoc stub with a structured interface that N12
# can later fill with the full math described in N12_ROSETTE_ENGINE_PLAN.md.
#
# For now, it uses the same "8 tiles equally spaced" behavior as the
# N11 stub, but returns proper dataclasses.

from __future__ import annotations

from typing import Optional
from math import fmod

from .models import RosetteRingConfig, SegmentationResult, Tile


def compute_tile_segmentation(
    ring: RosetteRingConfig,
    tile_count_override: Optional[int] = None,
) -> SegmentationResult:
    """
    Compute a ring segmentation into tiles.

    N12 final behavior:
      - derive tile_count from circumference and tile_length_mm
      - compute effective tile length, etc.

    N12.0 skeleton behavior:
      - keep a fixed tile count (8) or tile_count_override
      - equally spaced tiles around 360 degrees
    """
    tile_count = tile_count_override or 8
    if tile_count <= 0:
        tile_count = 8

    theta_per_tile = 360.0 / tile_count

    tiles: list[Tile] = []
    for i in range(tile_count):
        theta_start = i * theta_per_tile
        theta_end = (i + 1) * theta_per_tile
        # Normalize angles into [0, 360) just to keep consistency
        tiles.append(
            Tile(
                tile_index=i,
                theta_start_deg=fmod(theta_start, 360.0),
                theta_end_deg=fmod(theta_end, 360.0),
            )
        )

    segmentation_id = f"seg_ring_{ring.ring_id}_tc_{tile_count}"

    return SegmentationResult(
        segmentation_id=segmentation_id,
        ring_id=ring.ring_id,
        tile_count=tile_count,
        tile_length_mm=ring.tile_length_mm,
        tiles=tiles,
    )
