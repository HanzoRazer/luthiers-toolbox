# Preview engine — builds preview payloads from ring geometry.
#
# Maturity: SKELETON (returns tile/slice count summary per ring).
# Full implementation will generate SVG paths and drawing instructions.

from __future__ import annotations

from typing import Dict, Any, List

from .models import (
    RosetteRingConfig,
    SegmentationResult,
    SliceBatch,
    PreviewSnapshot,
)


def build_preview_snapshot(
    pattern_id: str | None,
    rings: List[RosetteRingConfig],
    segmentations: Dict[int, SegmentationResult],
    slice_batches: Dict[int, SliceBatch],
) -> PreviewSnapshot:
    """
    Build a preview snapshot.

    Full implementation:
      - generate SVG paths / drawing instructions
      - optionally produce a downsampled raster

    Current behavior:
      - return a minimal summary of tile and slice counts per ring
    """
    payload: Dict[str, Any] = {
        "rings": [],
    }

    for ring in rings:
        seg = segmentations.get(ring.ring_id)
        batch = slice_batches.get(ring.ring_id)

        payload["rings"].append(
            {
                "ring_id": ring.ring_id,
                "radius_mm": ring.radius_mm,
                "width_mm": ring.width_mm,
                "tile_count": seg.tile_count if seg else 0,
                "slice_count": len(batch.slices) if batch else 0,
            }
        )

    return PreviewSnapshot(
        pattern_id=pattern_id,
        rings=list(rings),
        payload=payload,
    )
