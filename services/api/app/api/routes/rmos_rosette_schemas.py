"""Pydantic schemas for RMOS Rosette API."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from ...cam.rosette.cnc import MaterialType


class RingConfig(BaseModel):
    """Configuration for a single rosette ring."""
    ring_id: Optional[int] = Field(None, description="Ring identifier")
    radius_mm: float = Field(45.0, description="Ring radius in millimeters")
    width_mm: float = Field(3.0, description="Ring width in millimeters")
    tile_length_mm: float = Field(5.0, description="Target tile length in millimeters")
    kerf_mm: float = Field(0.3, description="Saw kerf width in millimeters")
    herringbone_angle_deg: float = Field(0.0, description="Herringbone alternation angle")
    twist_angle_deg: float = Field(0.0, description="Ring twist angle for spiral patterns")


class SegmentRingRequest(BaseModel):
    """Request to segment a ring into tiles."""
    ring: RingConfig


class GenerateSlicesRequest(BaseModel):
    """Request to generate saw slices from segmentation."""
    ring_id: int = Field(..., description="Ring identifier")
    segmentation: Dict[str, Any] = Field(..., description="Segmentation result from /segment-ring")
    kerf_mm: float = Field(0.3, description="Saw kerf width")
    herringbone_angle_deg: float = Field(0.0, description="Herringbone angle")
    twist_angle_deg: float = Field(0.0, description="Ring twist angle")


class RosettePatternsListResponse(BaseModel):
    """Response containing list of rosette patterns."""
    patterns: List[Dict[str, Any]]


class PreviewRequest(BaseModel):
    """Request body for RMOS Rosette preview."""
    pattern_id: Optional[str] = Field(None, description="Optional pattern identifier")
    rings: List[RingConfig] = Field(..., description="Array of ring configurations")


class PreviewRingSummary(BaseModel):
    """Summary of a single ring in preview."""
    ring_id: int = Field(..., description="Ring identifier")
    radius_mm: float = Field(..., description="Ring radius in millimeters")
    width_mm: float = Field(..., description="Ring width in millimeters")
    tile_count: int = Field(..., description="Number of tiles in ring")
    slice_count: int = Field(..., description="Number of slices in ring")


class PreviewResponse(BaseModel):
    """Response for multi-ring preview."""
    pattern_id: Optional[str] = Field(None, description="Pattern identifier if provided")
    rings: List[PreviewRingSummary] = Field(..., description="Array of ring summaries")


class JigAlignmentModel(BaseModel):
    """Jig alignment parameters for CNC setup."""
    origin_x_mm: float = Field(0.0, description="X origin of jig in machine coordinates")
    origin_y_mm: float = Field(0.0, description="Y origin of jig in machine coordinates")
    rotation_deg: float = Field(0.0, description="Rotation of jig relative to machine axes")


class EnvelopeModel(BaseModel):
    """Machine envelope (working volume) bounds."""
    x_min_mm: float = Field(0.0, description="Minimum X coordinate")
    y_min_mm: float = Field(0.0, description="Minimum Y coordinate")
    z_min_mm: float = Field(-50.0, description="Minimum Z coordinate (negative is below work surface)")
    x_max_mm: float = Field(1000.0, description="Maximum X coordinate")
    y_max_mm: float = Field(1000.0, description="Maximum Y coordinate")
    z_max_mm: float = Field(0.0, description="Maximum Z coordinate (0 is work surface)")


class CNCExportRequest(BaseModel):
    """Request body for per-ring CNC export."""
    ring: RingConfig
    slice_batch: Dict[str, Any]
    material: MaterialType
    jig_alignment: JigAlignmentModel = Field(default_factory=JigAlignmentModel)
    envelope: Optional[EnvelopeModel] = None


class CNCSegmentModel(BaseModel):
    """A single CNC toolpath segment."""
    x_start_mm: float
    y_start_mm: float
    z_start_mm: float
    x_end_mm: float
    y_end_mm: float
    z_end_mm: float
    feed_mm_per_min: float


class CNCSafetyModel(BaseModel):
    """Safety decision for CNC operation."""
    decision: str
    risk_level: str
    requires_override: bool
    reasons: List[str]


class CNCSimulationModel(BaseModel):
    """CNC simulation results."""
    passes: int
    estimated_runtime_sec: float
    max_feed_mm_per_min: float
    envelope_ok: bool


class CNCExportResponse(BaseModel):
    """Response for per-ring CNC export."""
    job_id: str = Field(..., description="JobLog identifier for traceability and report retrieval")
    ring_id: int
    toolpaths: List[CNCSegmentModel]
    jig_alignment: JigAlignmentModel
    safety: CNCSafetyModel
    simulation: CNCSimulationModel
    metadata: Dict[str, Any]
    operator_report_md: Optional[str] = Field(None, description="Markdown operator checklist")


class CNCHistoryItem(BaseModel):
    """Single CNC export job history item."""
    job_id: str
    created_at: Optional[datetime] = None
    status: str
    ring_id: Optional[int] = None
    material: Optional[str] = None
    safety_decision: Optional[str] = None
    safety_risk_level: Optional[str] = None
    runtime_sec: Optional[float] = None
    pattern_id: Optional[str] = None


class CNCHistoryResponse(BaseModel):
    """Response containing list of CNC export history items."""
    items: List[CNCHistoryItem]


class CNCToolpathStatsModel(BaseModel):
    """Toolpath statistics for CNC job detail."""
    segment_count: int
    origin_x_mm: float | None = None
    origin_y_mm: float | None = None
    rotation_deg: float | None = None


class CNCJobDetailResponse(BaseModel):
    """Complete details for a single CNC export job."""
    job_id: str
    pattern_id: str | None
    status: str
    ring_id: int | None
    material: str | None
    created_at: datetime | None = None

    safety: CNCSafetyModel | None = None
    simulation: CNCSimulationModel | None = None
    toolpath_stats: CNCToolpathStatsModel | None = None

    operator_report_md: str | None = None
    metadata: Dict[str, Any] = {}
    parameters: Dict[str, Any] = {}
