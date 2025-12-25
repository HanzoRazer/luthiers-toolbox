"""
Rosette Design Snapshot Schema - Bundle 31.0.27

Defines the structure for persisted rosette design snapshots with feasibility data.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from .rosette_params import RosetteParamSpec
from .rosette_feasibility import RosetteFeasibilitySummary


class SnapshotMetadata(BaseModel):
    """Metadata for a design snapshot."""
    name: Optional[str] = None
    description: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=4096)  # Free-form notes (32.1.0)
    tags: List[str] = Field(default_factory=list)
    created_by: Optional[str] = None
    source: Optional[str] = None  # "manual", "ai_suggestion", "import"


class RosetteDesignSnapshot(BaseModel):
    """
    A complete snapshot of a rosette design with feasibility data.

    Used for export/import operations and design persistence.
    """
    snapshot_id: str
    design_fingerprint: str  # Hash of the design for deduplication
    created_at_utc: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # The actual design
    design: RosetteParamSpec

    # Feasibility at snapshot time (may be None for imports)
    feasibility: Optional[RosetteFeasibilitySummary] = None

    # Metadata
    metadata: SnapshotMetadata = Field(default_factory=SnapshotMetadata)

    # Run artifact reference (if created via API)
    run_id: Optional[str] = None

    # Baseline flag (32.1.0) - only one snapshot can be baseline at a time
    baseline: bool = False


class ExportSnapshotRequest(BaseModel):
    """Request to export/save a design snapshot."""
    design: RosetteParamSpec
    name: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    include_feasibility: bool = True


class ExportSnapshotResponse(BaseModel):
    """Response after exporting a snapshot."""
    snapshot_id: str
    design_fingerprint: str
    run_id: Optional[str] = None
    feasibility: Optional[RosetteFeasibilitySummary] = None


class ImportSnapshotRequest(BaseModel):
    """Request to import a design snapshot."""
    snapshot: RosetteDesignSnapshot


class ImportSnapshotResponse(BaseModel):
    """Response after importing a snapshot."""
    snapshot_id: str
    design_fingerprint: str
    run_id: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)


class ListSnapshotsResponse(BaseModel):
    """Response for listing snapshots."""
    snapshots: List[RosetteDesignSnapshot]
    total: int
