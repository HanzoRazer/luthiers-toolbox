# services/api/app/rmos/models/pattern.py

from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Literal, Dict, Any

from pydantic import BaseModel, Field


class RosettePoint(BaseModel):
    """Single point in rosette geometry (mm)."""
    x: float
    y: float


class RosetteRing(BaseModel):
    """One ring within a rosette pattern."""
    ring_id: str
    radius_mm: float
    points: List[RosettePoint] = Field(
        default_factory=list,
        description="Optional explicit polyline; may be empty for purely parametric rings.",
    )
    strip_width_mm: float
    strip_thickness_mm: float


class RosettePattern(BaseModel):
    """
    RMOS-level rosette pattern definition.

    NOTE: This is intentionally generic. Art Studio / Rosette Lab can
    store richer geometry in metadata if needed.
    """
    pattern_id: str
    pattern_name: str
    description: Optional[str] = None

    outer_radius_mm: float
    inner_radius_mm: float

    ring_count: int
    rings: List[RosetteRing] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    metadata: Dict[str, Any] = Field(default_factory=dict)


class SlicePreviewRequest(BaseModel):
    """Request for single-slice saw preview (RMOS → Saw Lab)."""
    geometry: Dict[str, Any]  # Simple geometry (circle/arc/polygon/etc.)
    tool_id: str
    material_id: Optional[str] = None
    cut_depth_mm: float
    feed_rate_mm_min: Optional[float] = None


class SlicePreviewResponse(BaseModel):
    """Response with slice preview data."""
    toolpath: List[Dict[str, Any]]
    statistics: Dict[str, Any]
    warnings: List[str] = Field(default_factory=list)
    visualization_svg: Optional[str] = None


class PipelineHandoffRequest(BaseModel):
    """Request to hand a rosette pattern to the CAM pipeline."""
    pattern_id: str
    tool_id: str
    material_id: str
    operation_type: Literal["channel", "inlay", "relief"]
    parameters: Dict[str, Any] = Field(default_factory=dict)


class PipelineHandoffResponse(BaseModel):
    """Response with pipeline job ID & status."""
    job_id: str
    pattern_id: str
    status: Literal["queued", "processing", "completed", "failed"]
    message: str
