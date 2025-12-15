# Patch N12.0 - Ring-level engine skeleton
#
# This orchestrates segmentation + slice generation + kerf + twist +
# herringbone for a SINGLE ring. Multi-ring stitching is handled by
# MultiRingAssembly in a later patch.

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

    N12 final behavior:
      - full segmentation based on ring geometry
      - slices with kerf, twist, and herringbone applied correctly

    N12.0 skeleton behavior:
      - uses segmentation_engine's fixed tile count segmentation
      - builds slices at tile centers
      - runs "no-op" kerf & twist/herringbone modifications
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
