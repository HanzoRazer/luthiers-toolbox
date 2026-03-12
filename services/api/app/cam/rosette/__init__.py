"""
RMOS Rosette CAM package — tile segmentation, kerf, herringbone, CNC export.

Maturity tiers:

  PRODUCTION   N11 stubs + N14 CNC wiring — used by current API routes.
  SKELETON     N12 core math models — structured interfaces, placeholder logic.
               Enable full N12 behavior via ROSETTE_ENGINE_N12_ENABLED=true.
  PROTOTYPE    cam/rosette/prototypes/ — standalone reference scripts.
               Never import from prototypes/ in production code.

Phase 6 graduation: skeleton modules are safe to import (stable types), but
callers should treat computed values (tile counts, angles) as approximate
until the N12 feature flag is enabled and real geometry is implemented.
"""

import os

# ── Feature gate ────────────────────────────────────────────────────────────
ROSETTE_N12_ENABLED: bool = (
    os.getenv("ROSETTE_ENGINE_N12_ENABLED", "false").lower() == "true"
)

# ── N11 stubs (PRODUCTION — used by current API) ───────────────────────────
from .tile_segmentation import compute_tile_segmentation_stub
from .kerf_compensation import apply_kerf_compensation_stub
from .herringbone import apply_herringbone_stub
from .saw_batch_generator import generate_saw_batch_stub

# ── N12 core models (SKELETON — stable types, placeholder math) ────────────
from .models import (
    RosetteRingConfig,
    Tile,
    SegmentationResult,
    SliceBatch,
    MultiRingAssembly,
    PreviewSnapshot,
)
from .segmentation_engine import compute_tile_segmentation
from .slice_engine import generate_slices_for_ring
from .kerf_engine import apply_kerf_physics
from .twist_engine import apply_twist, apply_herringbone as apply_herringbone_engine
from .ring_engine import compute_ring_geometry
from .preview_engine import build_preview_snapshot

# ── N14 CNC wiring (PRODUCTION) ────────────────────────────────────────────
from .rosette_cnc_wiring import build_ring_cnc_export, build_ring_operator_report_md

__all__ = [
    # Feature gate
    "ROSETTE_N12_ENABLED",
    # N11 stubs (production)
    "compute_tile_segmentation_stub",
    "apply_kerf_compensation_stub",
    "apply_herringbone_stub",
    "generate_saw_batch_stub",
    # N12 core models + skeleton engines
    "RosetteRingConfig",
    "Tile",
    "SegmentationResult",
    "SliceBatch",
    "MultiRingAssembly",
    "PreviewSnapshot",
    "compute_tile_segmentation",
    "generate_slices_for_ring",
    "apply_kerf_physics",
    "apply_twist",
    "apply_herringbone_engine",
    "compute_ring_geometry",
    "build_preview_snapshot",
    # N14 CNC wiring (production)
    "build_ring_cnc_export",
    "build_ring_operator_report_md",
]
