"""
Design Snapshot Schemas - Bundle 31.0.4

Defines the data models for saving, loading, and exporting design snapshots.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict

from .rosette_params import RosetteParamSpec


class DesignContextRefs(BaseModel):
    """
    Lightweight references to user's selected presets/context.
    These are refs/IDs only (not full objects).
    """
    model_config = ConfigDict(extra="forbid")

    material_preset_id: Optional[str] = None
    tool_preset_id: Optional[str] = None
    machine_id: Optional[str] = None
    mode: Optional[str] = Field(
        default="MODE_A",
        description="Directional workflow mode (Design-First default)"
    )


class DesignSnapshot(BaseModel):
    """
    Persisted snapshot of an Art Studio design state.

    - rosette_params is canonical
    - feasibility is stored as JSON-safe dict (RMOS result or summary)
    """
    model_config = ConfigDict(extra="forbid")

    snapshot_id: str
    name: str = Field(..., min_length=1, max_length=200)
    notes: Optional[str] = Field(default=None, max_length=4000)
    pattern_id: Optional[str] = Field(
        default=None,
        description="Optional link to a PatternRecord"
    )
    tags: List[str] = Field(default_factory=list)
    context_refs: DesignContextRefs = Field(default_factory=DesignContextRefs)
    rosette_params: RosetteParamSpec
    feasibility: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Serialized feasibility payload (RMOS FeasibilityResult-like)"
    )
    created_at: datetime
    updated_at: datetime


class SnapshotCreateRequest(BaseModel):
    """Request to create a new snapshot."""
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, max_length=200)
    notes: Optional[str] = Field(default=None, max_length=4000)
    pattern_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    context_refs: Optional[DesignContextRefs] = None
    rosette_params: RosetteParamSpec
    feasibility: Optional[Dict[str, Any]] = None


class SnapshotUpdateRequest(BaseModel):
    """
    Partial update for a snapshot.
    Omitted fields remain unchanged.
    """
    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    notes: Optional[str] = Field(default=None, max_length=4000)
    pattern_id: Optional[str] = None
    tags: Optional[List[str]] = None
    context_refs: Optional[DesignContextRefs] = None
    rosette_params: Optional[RosetteParamSpec] = None
    feasibility: Optional[Dict[str, Any]] = None


class SnapshotSummary(BaseModel):
    """Lightweight snapshot summary for list views."""
    model_config = ConfigDict(extra="forbid")

    snapshot_id: str
    name: str
    pattern_id: Optional[str]
    tags: List[str]
    updated_at: datetime


class SnapshotListResponse(BaseModel):
    """Response for snapshot list endpoint."""
    model_config = ConfigDict(extra="forbid")

    items: List[SnapshotSummary]


class SnapshotImportRequest(BaseModel):
    """
    Import a snapshot JSON blob previously exported.
    If snapshot_id collides, a new one is created.
    """
    model_config = ConfigDict(extra="forbid")

    snapshot: Dict[str, Any] = Field(
        ...,
        description="Raw exported snapshot JSON"
    )


class SnapshotExportResponse(BaseModel):
    """Response containing exported snapshot data."""
    model_config = ConfigDict(extra="forbid")

    snapshot: Dict[str, Any]
