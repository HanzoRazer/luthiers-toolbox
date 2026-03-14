"""
RMOS Rosette CAM package — tile segmentation, kerf, herringbone, CNC export.

Rosette Consolidation: skeleton engines absorbed into tile_segmentation.py.
Remaining maturity tiers:

  PRODUCTION   Real geometry + N14 CNC wiring — used by current API routes.
  PROTOTYPE    cam/rosette/prototypes/ — standalone reference scripts.
               Never import from prototypes/ in production code.
"""

import os

# ── Feature gate ────────────────────────────────────────────────────────────
ROSETTE_N12_ENABLED: bool = (
    os.getenv("ROSETTE_ENGINE_N12_ENABLED", "false").lower() == "true"
)

# ── Core models ─────────────────────────────────────────────────────────────
from .models import (
    RosetteRingConfig,
    Tile,
    Slice,
    SegmentationResult,
    SliceBatch,
    MultiRingAssembly,
    PreviewSnapshot,
)

# ── Tile Segmentation (real geometry + absorbed functions) ──────────────────
from .tile_segmentation import (
    # Real geometry
    TilePattern,
    Point2D,
    TileGeometry,
    RingSegmentation,
    compute_tile_count,
    compute_tile_geometry,
    compute_ring_segmentation,
    compute_tile_segmentation,
    compute_tile_segmentation_stub,
    # Absorbed from slice_engine.py
    generate_slices_for_ring,
    # Absorbed from twist_engine.py
    apply_twist,
    apply_herringbone,
    # Absorbed from preview_engine.py
    build_preview_snapshot,
)

# Backward compatibility alias
apply_herringbone_engine = apply_herringbone

# ── N14 CNC wiring (PRODUCTION) ────────────────────────────────────────────
from .rosette_cnc_wiring import build_ring_cnc_export, build_ring_operator_report_md

__all__ = [
    # Feature gate
    "ROSETTE_N12_ENABLED",
    # Core models
    "RosetteRingConfig",
    "Tile",
    "Slice",
    "SegmentationResult",
    "SliceBatch",
    "MultiRingAssembly",
    "PreviewSnapshot",
    # Tile geometry (real implementation)
    "TilePattern",
    "Point2D",
    "TileGeometry",
    "RingSegmentation",
    "compute_tile_count",
    "compute_tile_geometry",
    "compute_ring_segmentation",
    "compute_tile_segmentation",
    "compute_tile_segmentation_stub",
    # Absorbed functions
    "generate_slices_for_ring",
    "apply_twist",
    "apply_herringbone",
    "apply_herringbone_engine",  # backward compat alias
    "build_preview_snapshot",
    # N14 CNC wiring (production)
    "build_ring_cnc_export",
    "build_ring_operator_report_md",
]
