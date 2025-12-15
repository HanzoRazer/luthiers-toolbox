# Patch N12.0 - Slice geometry engine (skeleton)
#
# Responsible for turning tiles into slices with raw angles. The full
# N12 engine will compute actual geometry and incorporate twist,
# herringbone, and kerf. Here we just provide a structured placeholder.

from __future__ import annotations

from typing import List

from .models import SegmentationResult, Slice, SliceBatch, RosetteRingConfig


def generate_slices_for_ring(
    ring: RosetteRingConfig,
    segmentation: SegmentationResult,
) -> SliceBatch:
    """
    Generate slice records for each tile in the segmentation.

    N12 final behavior:
      - compute raw angles based on tangent + 90°
      - incorporate radius, width, etc.

    N12.0 skeleton behavior:
      - sets angle_raw_deg to tile center
      - angle_final_deg initially equals angle_raw_deg
    """
    slices: List[Slice] = []

    for tile in segmentation.tiles:
        center_angle = 0.5 * (tile.theta_start_deg + tile.theta_end_deg)

        s = Slice(
            slice_index=tile.tile_index,
            tile_index=tile.tile_index,
            angle_raw_deg=center_angle,
            angle_final_deg=center_angle,
            theta_start_deg=tile.theta_start_deg,
            theta_end_deg=tile.theta_end_deg,
            kerf_mm=ring.kerf_mm,
            herringbone_flip=False,
            herringbone_angle_deg=ring.herringbone_angle_deg,
            twist_angle_deg=ring.twist_angle_deg,
        )
        slices.append(s)

    batch_id = f"slice_batch_ring_{ring.ring_id}"
    return SliceBatch(batch_id=batch_id, ring_id=ring.ring_id, slices=slices)
