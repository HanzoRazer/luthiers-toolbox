"""
Phase 27.0: Rosette Compare Mode MVP
Models for baseline storage and geometry diffing
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Literal

from pydantic import BaseModel, Field


class CompareBaselineIn(BaseModel):
    """Request model when saving a new baseline."""
    name: str = Field(..., description="Human-readable baseline name (manual).")
    lane: str = Field("rosette", description="Art Studio lane, e.g. 'rosette', 'headstock', 'relief'.")
    geometry: Dict[str, Any] = Field(..., description="Arbitrary geometry payload (usually JSON from Rosette).")


class CompareBaselineOut(BaseModel):
    """Response model for saved baseline and listing."""
    id: str
    name: str
    lane: str
    created_at: datetime
    geometry: Dict[str, Any]


class CompareBaselineSummary(BaseModel):
    """Lightweight version for lists."""
    id: str
    name: str
    lane: str
    created_at: datetime


class CompareDiffRequest(BaseModel):
    """Request for diff between a baseline and current geometry."""
    baseline_id: str
    lane: str = "rosette"
    current_geometry: Dict[str, Any]
    # Phase 27.1: optional job_id for logging into risk/job snapshots
    job_id: str | None = None
    # Phase 27.4: optional preset name/label (e.g. "Safe", "Aggressive")
    preset: str | None = None


class CompareDiffStats(BaseModel):
    """Simple numeric diff stats for MVP."""
    baseline_path_count: int
    current_path_count: int
    added_paths: int
    removed_paths: int
    unchanged_paths: int


class CompareDiffOut(BaseModel):
    """Diff result. You can extend later with per-path annotations."""
    baseline_id: str
    lane: str
    stats: CompareDiffStats
    # Optionally echo geometry back if desired:
    baseline_geometry: Dict[str, Any] | None = None
    current_geometry: Dict[str, Any] | None = None


# ----------------------------------------------------------------------------
# B22 Compare Lab Baseline Models (Geometry + Toolpath snapshots)
# ----------------------------------------------------------------------------


class BaselineGeometry(BaseModel):
    """Geometry payload persisted for Compare Lab baselines."""

    units: Literal["mm", "inch"] = "mm"
    paths: List[Dict[str, Any]] = Field(default_factory=list)
    source: Optional[str] = None  # optional filename/path metadata


class BaselineToolpath(BaseModel):
    """Optional toolpath snapshot stored with a baseline."""

    units: Literal["mm", "inch"] = "mm"
    moves: List[Dict[str, Any]] = Field(default_factory=list)
    stats: Optional[Dict[str, Any]] = None


class Baseline(BaseModel):
    """Complete baseline record used by Compare Lab APIs."""

    id: str
    name: str
    type: Literal["geometry", "toolpath"] = "geometry"
    created_at: str
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    preset_id: Optional[str] = None
    preset_name: Optional[str] = None
    machine_id: Optional[str] = None
    post_id: Optional[str] = None

    geometry: Optional[BaselineGeometry] = None
    toolpath: Optional[BaselineToolpath] = None
