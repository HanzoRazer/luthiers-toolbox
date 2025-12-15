"""
Luthier's Tool Box - CNC Guitar Lutherie CAD/CAM Toolbox
Relief carving schemas for heightmap-based 3D toolpath generation

Part of Phase 24.0-24.3: Relief Carving System
Repository: HanzoRazer/luthiers-toolbox
Updated: January 2025

This module defines Pydantic models for:
- Heightmap → Z grid conversion (ReliefMapFromHeightfield)
- Roughing toolpaths (multi-pass raster)
- Finishing toolpaths (scallop-based ball nose)
- Z-aware overlays (slope hotspots)
- Sim bridge for material removal estimation (Phase 24.3)
"""

from __future__ import annotations

from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field


class ReliefMapFromHeightfieldIn(BaseModel):
    """Input schema for converting grayscale heightmap to Z grid."""
    
    heightmap_path: str = Field(
        ...,
        description="Path to grayscale heightmap image (e.g. PNG).",
    )
    units: Literal["mm", "inch"] = Field(
        "mm", description="Units for generated toolpaths."
    )
    z_min: float = Field(
        0.0,
        description="Z value at brightest pixels (typically stock surface or top).",
    )
    z_max: float = Field(
        -3.0,
        description="Z value at darkest pixels (max relief depth).",
    )
    sample_pitch_xy: float = Field(
        0.3,
        description="Sampling pitch in XY in units (distance between samples).",
    )
    smooth_sigma: float = Field(
        0.0,
        description="Optional Gaussian smoothing radius in samples (0 = disabled).",
    )


class ReliefCellStats(BaseModel):
    """Statistics for Z grid cells."""
    
    width: int
    height: int
    z_min: float
    z_max: float
    z_mean: float
    z_std: float


class ReliefMapFromHeightfieldOut(BaseModel):
    """Output schema with Z grid and metadata."""
    
    width: int
    height: int
    origin_x: float
    origin_y: float
    cell_size_xy: float
    z_min: float
    z_max: float
    z_grid: List[List[float]] = Field(
        ..., description="2D grid of Z values, indexed as z_grid[row][col]."
    )
    stats: ReliefCellStats
    units: Literal["mm", "inch"]


class ReliefRasterToolpathIn(BaseModel):
    """Base input schema for relief raster toolpaths."""
    
    # Map can be passed inline (from previous op) or reloaded from disk later.
    z_grid: List[List[float]] = Field(
        ..., description="2D Z grid from ReliefMapFromHeightfield."
    )
    origin_x: float = 0.0
    origin_y: float = 0.0
    cell_size_xy: float = 0.3
    units: Literal["mm", "inch"] = "mm"

    # Tool parameters
    tool_d: float = Field(..., description="Tool diameter.")
    stepdown: float = Field(..., description="Depth per pass.")
    safe_z: float = Field(4.0, description="Clearance plane Z for rapids.")
    feed_xy: float = Field(800.0, description="Cutting feed rate in XY.")
    feed_z: float = Field(300.0, description="Plunge feed rate.")

    # Region of interest (optional cropping)
    roi_min_x: Optional[float] = None
    roi_max_x: Optional[float] = None
    roi_min_y: Optional[float] = None
    roi_max_y: Optional[float] = None


class ReliefFinishingIn(ReliefRasterToolpathIn):
    """Input schema for finishing toolpaths with scallop control."""
    
    scallop_height: float = Field(
        0.05,
        description=(
            "Target scallop height (for ball nose). Used to approximate stepover."
        ),
    )
    pattern: Literal["RasterX", "RasterY"] = "RasterX"
    
    # Phase 24.6: Dynamic scallop (slope-aware spacing)
    use_dynamic_scallop: bool = Field(
        False,
        description="If true, scallop height (and thus stepover) is varied by local slope to keep load more uniform across steep vs flat regions."
    )
    slope_low_deg: float = Field(
        10.0,
        description="Below this slope angle (deg) we treat the surface as 'flat' for dynamic scallop."
    )
    slope_high_deg: float = Field(
        50.0,
        description="Above this slope angle (deg) we treat the surface as 'steep' for dynamic scallop."
    )
    scallop_min: float = Field(
        0.03,
        description="Minimum scallop height (in current units) used in steep regions when dynamic scallop is enabled."
    )
    scallop_max: float = Field(
        0.08,
        description="Maximum scallop height (in current units) used in flat regions when dynamic scallop is enabled."
    )


class ReliefMove(BaseModel):
    """Single G-code move in relief toolpath."""
    
    code: str = Field(..., description="G-code style: G0 or G1")
    x: Optional[float] = None
    y: Optional[float] = None
    z: Optional[float] = None
    f: Optional[float] = None


class ReliefOverlay(BaseModel):
    """Z-aware overlay marker for backplot visualization."""
    
    type: str = Field(
        ..., description="Overlay category, e.g. 'slope_hotspot' or 'depth_limit'."
    )
    x: float
    y: float
    z: Optional[float] = None
    slope_deg: Optional[float] = None
    severity: Optional[Literal["info", "low", "medium", "high", "critical"]] = None
    meta: Dict[str, Any] = Field(default_factory=dict)


class ReliefToolpathStats(BaseModel):
    """Statistics for generated relief toolpath."""
    
    move_count: int
    length_xy: float
    min_z: float
    max_z: float
    est_time_s: float


class ReliefToolpathOut(BaseModel):
    """Output schema with moves, overlays, and statistics."""
    
    moves: List[ReliefMove]
    overlays: List[ReliefOverlay] = Field(default_factory=list)
    stats: ReliefToolpathStats
    units: Literal["mm", "inch"]


# ============================================================================
# Relief Sim Bridge - Mesh-ish material removal simulation
# ============================================================================


class ReliefSimIssue(BaseModel):
    """Simulation issue detected during relief material removal analysis."""
    
    type: str = Field(
        ...,
        description="Issue category, e.g. 'thin_floor', 'over_depth', 'high_load'",
    )
    severity: Literal["info", "low", "medium", "high", "critical"] = "medium"
    x: float
    y: float
    z: Optional[float] = None
    extra_time_s: Optional[float] = Field(
        default=None,
        description="Optional extra time associated with this issue (if any).",
    )
    note: Optional[str] = None
    meta: Dict[str, Any] = Field(default_factory=dict)


class ReliefSimOverlayOut(BaseModel):
    """Z-aware overlay for simulation visualization (load hotspots, thin floor zones)."""
    
    type: str = Field(
        ...,
        description="Overlay type, e.g. 'load_hotspot', 'thin_floor_zone'",
    )
    x: float
    y: float
    z: Optional[float] = None
    intensity: Optional[float] = Field(
        default=None,
        description="Normalized intensity (0..1) for heatmap-like display.",
    )
    severity: Optional[Literal["info", "low", "medium", "high", "critical"]] = None
    meta: Dict[str, Any] = Field(default_factory=dict)


class ReliefSimStats(BaseModel):
    """Statistics from relief simulation bridge."""
    
    cell_count: int
    avg_floor_thickness: float
    min_floor_thickness: float
    max_load_index: float
    avg_load_index: float
    total_removed_volume: float


class ReliefSimIn(BaseModel):
    """Input schema for relief simulation bridge."""
    
    moves: List[ReliefMove] = Field(
        ..., description="Finishing (or roughing) toolpath moves in machine space."
    )
    stock_thickness: float = Field(
        ...,
        description="Stock thickness above the relief reference (typically positive).",
    )
    origin_x: float = 0.0
    origin_y: float = 0.0
    cell_size_xy: float = 0.5
    units: Literal["mm", "inch"] = "mm"

    # thresholds
    min_floor_thickness: float = Field(
        0.6,
        description="Below this, we consider the floor too thin.",
    )
    high_load_index: float = Field(
        2.0,
        description="Above this normalized load index, mark as high-load hotspot.",
    )
    med_load_index: float = Field(
        1.0,
        description="Above this normalized load index, mark as medium-load hotspot.",
    )


class ReliefSimOut(BaseModel):
    """Output schema from relief simulation bridge."""
    
    issues: List[ReliefSimIssue]
    overlays: List[ReliefSimOverlayOut]
    stats: ReliefSimStats
