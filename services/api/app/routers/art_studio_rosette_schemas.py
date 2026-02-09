"""Pydantic models for art studio rosette router."""
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field, validator

class RosettePreviewIn(BaseModel):
    """Rosette preview input."""
    pattern_type: str = Field(..., description="e.g. 'herringbone', 'rope', 'simple_ring'")
    segments: int = Field(64, ge=8, le=720)
    inner_radius: float = Field(40.0, gt=0)
    outer_radius: float = Field(45.0, gt=0)
    units: str = Field("mm", pattern="^(mm|inch)$")
    preset: Optional[str] = Field(None, description="Optional preset name")
    name: Optional[str] = Field(None, description="Optional friendly job name for saving")

    @validator("outer_radius")
    def check_radii(cls, v, values):
        inner = values.get("inner_radius", None)
        if inner is not None and v <= inner:
            raise ValueError("outer_radius must be greater than inner_radius")
        return v

class RosettePath(BaseModel):
    """Rosette path segment."""
    points: List[Tuple[float, float]]

class RosettePreviewOut(BaseModel):
    """Rosette preview output."""
    job_id: str
    pattern_type: str
    segments: int
    inner_radius: float
    outer_radius: float
    units: str
    preset: Optional[str]
    name: Optional[str]
    paths: List[RosettePath]
    bbox: Tuple[float, float, float, float]

class RosetteSaveIn(BaseModel):
    """Save a rosette job with full preview data."""
    preview: RosettePreviewOut
    name: Optional[str] = None
    preset: Optional[str] = None

class RosetteJobOut(BaseModel):
    """Rosette job output."""
    job_id: str
    name: Optional[str]
    preset: Optional[str]
    created_at: str
    preview: RosettePreviewOut

class RosettePresetOut(BaseModel):
    """Rosette preset output."""
    name: str
    pattern_type: str
    segments: int
    inner_radius: float
    outer_radius: float
    metadata: Dict[str, Any]

class RosetteCompareIn(BaseModel):
    """Compare mode input."""
    job_id_a: str = Field(..., description="Baseline job id (A)")
    job_id_b: str = Field(..., description="Variant job id (B)")

class RosetteDiffSummary(BaseModel):
    """Rosette diff summary."""
    job_id_a: str
    job_id_b: str
    pattern_type_a: str
    pattern_type_b: str
    pattern_type_same: bool
    segments_a: int
    segments_b: int
    segments_delta: int
    inner_radius_a: float
    inner_radius_b: float
    inner_radius_delta: float
    outer_radius_a: float
    outer_radius_b: float
    outer_radius_delta: float
    units_a: str
    units_b: str
    units_same: bool
    bbox_union: Tuple[float, float, float, float]
    bbox_a: Tuple[float, float, float, float]
    bbox_b: Tuple[float, float, float, float]

class RosetteCompareOut(BaseModel):
    """Compare mode output."""
    job_a: RosettePreviewOut
    job_b: RosettePreviewOut
    diff_summary: RosetteDiffSummary

class CompareSnapshotIn(BaseModel):
    """Request to save a comparison snapshot to risk timeline."""
    job_id_a: str
    job_id_b: str
    risk_score: float = Field(..., ge=0, le=100, description="Risk score 0-100")
    diff_summary: Dict[str, Any]
    lane: Optional[str] = Field(None, description="Optional lane (e.g., 'production')")
    note: Optional[str] = Field(None, description="Optional note about this comparison")

class CompareSnapshotOut(BaseModel):
    """Snapshot record from risk timeline."""
    id: int
    job_id_a: str
    job_id_b: str
    lane: str
    risk_score: float
    diff_summary: Dict[str, Any]
    note: Optional[str]
    created_at: str
