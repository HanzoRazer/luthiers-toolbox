# Patch N11.2 - Saw batch generator scaffolding

from typing import Any, Dict, List


def generate_saw_batch_stub(
    ring_id: int,
    segmentation: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Scaffolding only.

    Builds a very simple 'SliceBatch' structure from segmentation tiles.
    Each slice is just a record with index and angle; geometry is not real yet.
    """
    slices: List[Dict[str, Any]] = []
    tiles = segmentation.get("tiles", [])
    for tile in tiles:
        idx = tile.get("tile_index", 0)
        theta_start = tile.get("theta_start_deg", 0.0)
        theta_end = tile.get("theta_end_deg", 0.0)
        center_angle = 0.5 * (theta_start + theta_end)

        slices.append(
            {
                "slice_index": idx,
                "tile_index": idx,
                "angle_deg": center_angle,
                "theta_start_deg": theta_start,
                "theta_end_deg": theta_end,
            }
        )

    return {
        "batch_id": f"saw_batch_stub_{ring_id}",
        "ring_id": ring_id,
        "slices": slices,
    }
