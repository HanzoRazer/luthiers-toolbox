"""Pydantic models for MVP wrapper."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class RMOSWrapDecision(BaseModel):
    """RMOS wrapper schema."""
    risk_level: str = Field(..., description="GREEN|YELLOW|RED|UNKNOWN|ERROR")
    warnings: List[str] = Field(default_factory=list)
    block_reason: Optional[str] = None

class RMOSWrapAttachmentRef(BaseModel):
    """RMOS wrapper schema."""
    kind: str = Field(..., description="dxf_input|cam_plan|gcode_output|manifest")
    sha256: str = Field(..., min_length=64, max_length=64)
    filename: str
    mime: Optional[str] = None
    size_bytes: Optional[int] = None
    created_at_utc: Optional[str] = None

class RMOSWrapHashes(BaseModel):
    """RMOS wrapper schema."""
    feasibility_sha256: str = Field(..., min_length=64, max_length=64)
    opplan_sha256: Optional[str] = Field(None, min_length=64, max_length=64)
    gcode_sha256: Optional[str] = Field(None, min_length=64, max_length=64)
    toolpaths_sha256: Optional[str] = Field(None, min_length=64, max_length=64)

class RMOSWrapGCodeRef(BaseModel):
    """RMOS wrapper schema."""
    inline: bool = Field(..., description="True if gcode is included inline")
    text: Optional[str] = Field(None, description="Inline gcode text when inline=true")
    path: Optional[str] = Field(None, description="Attachment path when inline=false")

class RMOSWrapMvpResponse(BaseModel):
    """RMOS wrapper schema."""
    ok: bool = Field(True, description="True if CAM succeeded (regardless of RMOS)")
    run_id: str = Field(..., description="RMOS run artifact ID (empty string if not persisted)")
    decision: RMOSWrapDecision = Field(..., description="Risk assessment outcome")
    hashes: RMOSWrapHashes = Field(..., description="SHA256 hash chain")
    attachments: List[RMOSWrapAttachmentRef] = Field(default_factory=list, description="Content-addressed attachments")
    gcode: RMOSWrapGCodeRef = Field(..., description="G-code delivery reference")
    warnings: List[str] = Field(default_factory=list, description="All warnings (same as decision.warnings)")
    rmos_persisted: bool = Field(True, description="True if RMOS artifact was persisted")
    rmos_error: Optional[str] = Field(None, description="RMOS error message if persistence failed")

class MVPManifest(BaseModel):
    """MVP execution manifest."""
    pipeline_id: str = "mvp_dxf_to_grbl_v1"
    controller: str = "GRBL"
    created_at_utc: str
    params: Dict[str, Any] = Field(default_factory=dict)
    dxf_sha256: str
    plan_sha256: str
    gcode_sha256: str
    api_version: str = "1.0.0"
    git_sha: Optional[str] = None
    post_profile_id: str = "GRBL"
    warnings: List[str] = Field(default_factory=list)
