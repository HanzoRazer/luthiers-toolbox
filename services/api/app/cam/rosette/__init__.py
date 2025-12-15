# Patch N11.2 + N12.0 + N14.1 + N14.x - RMOS Rosette cam package
#
# N11.2: stub-level functions for initial scaffolding.
# N12.0: core math skeleton for real geometry, not yet wired into
#        the existing APIs (wiring will come in a later bundle).
# N14.1: CNC wiring function for per-ring export.
# N14.x: Operator report generation for CNC exports.

from .tile_segmentation import compute_tile_segmentation_stub
from .kerf_compensation import apply_kerf_compensation_stub
from .herringbone import apply_herringbone_stub
from .saw_batch_generator import generate_saw_batch_stub

# N12.0 skeleton exports
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

# N14.1 CNC wiring
from .rosette_cnc_wiring import build_ring_cnc_export, build_ring_operator_report_md

__all__ = [
    # N11 stubs (still used by current API)
    "compute_tile_segmentation_stub",
    "apply_kerf_compensation_stub",
    "apply_herringbone_stub",
    "generate_saw_batch_stub",
    # N12.0 core skeleton
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
    # N14.1 + N14.x CNC wiring
    "build_ring_cnc_export",
    "build_ring_operator_report_md",
]
