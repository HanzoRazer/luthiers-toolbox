"""
RunLogEntry schema - flattened audit surface for RMOS runs.

Design principles:
- Append-only: Never mutates history
- Deterministic: Derived entirely from RunArtifact + attachments
- Schema-stable: New fields append; old ones never change meaning
- Lossy by design: This is a log, not a source of truth
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class InputSummary(BaseModel):
    """Summary of run input."""
    source_type: str = Field(..., description="DXF, Art Studio, Saw Lab, etc.")
    filename: Optional[str] = Field(None, description="Original input filename")
    loop_count: Optional[int] = Field(None, description="Number of closed loops in geometry")
    bbox_mm: Optional[list[float]] = Field(None, description="Bounding box [x_min, y_min, x_max, y_max]")


class CAMSummary(BaseModel):
    """Summary of CAM parameters."""
    tool_d_mm: Optional[float] = Field(None, description="Tool diameter in mm")
    stepover: Optional[float] = Field(None, description="Stepover as fraction (0-1)")
    stepdown_mm: Optional[float] = Field(None, description="Depth of cut in mm")
    z_rough_mm: Optional[float] = Field(None, description="Roughing depth in mm")
    strategy: Optional[str] = Field(None, description="Toolpath strategy (Spiral, Zigzag, etc.)")


class OutputsSummary(BaseModel):
    """Summary of run outputs."""
    gcode_lines: Optional[int] = Field(None, description="Number of G-code lines")
    gcode_sha256: Optional[str] = Field(None, description="SHA256 of G-code content")
    inline: bool = Field(False, description="Whether G-code was returned inline")


class AttachmentsSummary(BaseModel):
    """Summary of run attachments."""
    count: int = Field(0, description="Total attachment count")
    has_dxf: bool = Field(False, description="DXF attachment present")
    has_gcode: bool = Field(False, description="G-code attachment present")
    has_feasibility: bool = Field(False, description="Feasibility attachment present")


class HashesSummary(BaseModel):
    """Content-addressed hashes for verification."""
    feasibility_sha256: Optional[str] = Field(None, description="Feasibility artifact hash")
    toolpaths_sha256: Optional[str] = Field(None, description="Toolpaths artifact hash")
    gcode_sha256: Optional[str] = Field(None, description="G-code content hash")


class LineageSummary(BaseModel):
    """Run lineage information."""
    parent_run_id: Optional[str] = Field(None, description="Parent run ID if this is a re-run")


class RunLogEntry(BaseModel):
    """
    Flattened, human- and machine-readable audit entry for a single RMOS run.

    This answers: "What happened, and can I trust it?"

    Designed for:
    - Operators
    - Manufacturing engineers
    - Auditors
    - Business / ops analysis
    - Future AI consumers (not authorities)
    """
    # Core identifiers
    run_id: str = Field(..., description="Unique run identifier")
    created_at_utc: datetime = Field(..., description="UTC timestamp of run creation")
    mode: str = Field(..., description="Run mode (mvp_dxf_to_grbl, etc.)")
    tool_id: Optional[str] = Field(None, description="Tool identifier used")

    # Status
    status: str = Field(..., description="Run status (OK, ERROR, BLOCKED)")

    # Feasibility decision
    risk_level: str = Field(..., description="GREEN, YELLOW, or RED")
    rules_triggered: list[str] = Field(default_factory=list, description="Rule IDs that fired")
    warning_count: int = Field(0, description="Number of warnings")
    block_reason: Optional[str] = Field(None, description="Reason for block if status=BLOCKED")
    override_applied: bool = Field(False, description="Whether an override was used")

    # Summaries
    input_summary: InputSummary = Field(..., description="Input summary")
    cam_summary: Optional[CAMSummary] = Field(None, description="CAM parameters summary")
    outputs: Optional[OutputsSummary] = Field(None, description="Outputs summary")
    attachments: AttachmentsSummary = Field(default_factory=AttachmentsSummary, description="Attachments summary")
    hashes: HashesSummary = Field(default_factory=HashesSummary, description="Content hashes")
    lineage: LineageSummary = Field(default_factory=LineageSummary, description="Lineage info")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


# CSV column order (flattened)
CSV_COLUMNS = [
    "run_id",
    "created_at_utc",
    "mode",
    "tool_id",
    "status",
    "risk_level",
    "warning_count",
    "override_applied",
    "block_reason",
    "rules_triggered",
    "input_filename",
    "loop_count",
    "bbox_width_mm",
    "bbox_height_mm",
    "tool_d_mm",
    "stepover",
    "stepdown_mm",
    "z_rough_mm",
    "strategy",
    "gcode_lines",
    "gcode_inline",
    "feasibility_sha256",
    "gcode_sha256",
    "parent_run_id",
]
