# RMOS Rosette math models — canonical in-memory representation.
#
# Maturity: STABLE TYPES / SKELETON LOGIC
# These dataclasses define the ring, tile, slice, and batch shapes used
# across segmentation, slice, kerf, twist, and preview engines.
# The types are production-stable; computed values are approximate until
# ROSETTE_ENGINE_N12_ENABLED=true activates full geometry math.

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class RosetteRingConfig:
    """Configuration for a single rosette ring."""
    ring_id: int
    radius_mm: float
    width_mm: float
    tile_length_mm: float
    kerf_mm: float = 0.3
    herringbone_angle_deg: float = 0.0
    twist_angle_deg: float = 0.0


@dataclass
class Tile:
    """A single tile segment within a ring."""
    tile_index: int
    theta_start_deg: float
    theta_end_deg: float

    # Optional future fields
    # material_map: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SegmentationResult:
    """Result of segmenting a ring into tiles."""
    segmentation_id: str
    ring_id: int
    tile_count: int
    tile_length_mm: float
    tiles: List[Tile] = field(default_factory=list)


@dataclass
class Slice:
    """A single saw slice for cutting a tile."""
    slice_index: int
    tile_index: int
    angle_raw_deg: float
    angle_final_deg: float

    theta_start_deg: float
    theta_end_deg: float

    # Optional geometry fields (for future fill-in)
    # start_x_mm: float = 0.0
    # start_y_mm: float = 0.0
    # end_x_mm: float = 0.0
    # end_y_mm: float = 0.0

    kerf_mm: float = 0.0
    herringbone_flip: bool = False
    herringbone_angle_deg: float = 0.0
    twist_angle_deg: float = 0.0


@dataclass
class SliceBatch:
    """Collection of slices for a single ring."""
    batch_id: str
    ring_id: int
    slices: List[Slice] = field(default_factory=list)


@dataclass
class MultiRingAssembly:
    """
    Multi-ring rosette assembly geometry.

    Collects per-ring segmentation and slice results into a single
    assembly for cross-ring alignment and preview rendering.
    """

    pattern_id: Optional[str] = None
    rings: List[RosetteRingConfig] = field(default_factory=list)
    segmentations: Dict[int, SegmentationResult] = field(default_factory=dict)
    slice_batches: Dict[int, SliceBatch] = field(default_factory=dict)


@dataclass
class PreviewSnapshot:
    """
    Container for preview data — carries per-ring tile/slice summaries.

    When full geometry is enabled (ROSETTE_ENGINE_N12_ENABLED), the payload
    will include SVG path data and sampled points.  Currently returns a
    summary dict with tile and slice counts per ring.
    """

    pattern_id: Optional[str] = None
    rings: List[RosetteRingConfig] = field(default_factory=list)
    # 'payload' can be SVG strings, path commands, etc.
    payload: Dict[str, Any] = field(default_factory=dict)
