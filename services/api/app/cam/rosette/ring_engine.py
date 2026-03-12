# Ring-level engine — orchestrates segmentation + slice + kerf + twist
# for a single ring.
#
# Maturity: SKELETON (calls through to skeleton sub-engines).
# Multi-ring stitching is handled by MultiRingAssembly separately.

from __future__ import annotations

from .models import RosetteRingConfig, SegmentationResult, SliceBatch
from .segmentation_engine import compute_tile_segmentation
from .slice_engine import generate_slices_for_ring
from .kerf_engine import apply_kerf_physics
from .twist_engine import apply_twist, apply_herringbone


def compute_ring_geometry(
    ring: RosetteRingConfig,
) -> tuple[SegmentationResult, SliceBatch]:
    """
    Compute the full geometry for a single ring.

    Full implementation:
      - segmentation based on ring geometry (circumference ÷ tile_length)
      - slices with kerf, twist, and herringbone applied correctly

    Current behavior:
      - uses segmentation_engine's fixed tile count segmentation
      - builds slices at tile centers
      - runs pass-through kerf & twist/herringbone modifications
    """
    seg = compute_tile_segmentation(ring)
    batch = generate_slices_for_ring(ring, seg)

    # Apply kerf physics skeleton
    kerfed = apply_kerf_physics(ring, batch.slices)
    # Apply twist & herringbone skeleton
    twisted = apply_twist(ring, kerfed)
    final_slices = apply_herringbone(ring, twisted)

    batch.slices = final_slices
    return seg, batch
