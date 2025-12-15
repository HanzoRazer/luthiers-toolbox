# Patch N11.2 - Tile segmentation scaffolding

from typing import Any, Dict


def compute_tile_segmentation_stub(ring: Dict[str, Any]) -> Dict[str, Any]:
    """
    Scaffolding only.

    Accepts a ring configuration dict and returns a minimal segmentation
    structure with dummy values. N12 will replace this with real math.

    Expected ring keys (for future use):
      - ring_id: int
      - radius_mm: float
      - width_mm: float
      - tile_length_mm: float
    """
    ring_id = ring.get("ring_id", 0)

    # Very simple placeholder segmentation:
    tile_count = 8
    tiles = []
    for i in range(tile_count):
        tiles.append(
            {
                "tile_index": i,
                "theta_start_deg": i * (360.0 / tile_count),
                "theta_end_deg": (i + 1) * (360.0 / tile_count),
            }
        )

    return {
        "segmentation_id": f"seg_stub_{ring_id}",
        "ring_id": ring_id,
        "tile_count": tile_count,
        "tile_length_mm": ring.get("tile_length_mm", 5.0),
        "tiles": tiles,
    }
