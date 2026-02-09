"""Pydantic schemas for RMOS Workflow Router."""

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from app.workflow.state_machine import ActorRole, WorkflowMode


class GeneratorInfo(BaseModel):
    """Workflow generator metadata."""
    key: str = Field(..., description="Unique generator identifier")
    name: str = Field(..., description="Human-readable name")
    description: str = Field(default="", description="Generator description")
    category: str = Field(default="general", description="Generator category")
    version: str = Field(default="1.0.0", description="Generator version")


class GeneratorsListResponse(BaseModel):
    """Response for listing available generators."""
    generators: list[GeneratorInfo]
    count: int


class SaveSnapshotRequest(BaseModel):
    """Request to save a session snapshot."""
    name: Optional[str] = Field(default=None, description="Optional snapshot name")
    tags: list[str] = Field(default_factory=list, description="Optional tags")


class SaveSnapshotResponse(BaseModel):
    """Response from saving a session snapshot."""
    session_id: str
    snapshot_id: str
    name: str
    created_at: str


class CreateSessionRequest(BaseModel):
    """Request to create a new workflow session."""
    mode: WorkflowMode = Field(default=WorkflowMode.DESIGN_FIRST)
    tool_id: Optional[str] = None
    material_id: Optional[str] = None
    machine_id: Optional[str] = None


class CreateSessionResponse(BaseModel):
    """Response from creating a session."""
    session_id: str
    mode: str
    state: str
    next_step: str


class SetContextRequest(BaseModel):
    """Request to set session context."""
    session_id: str
    context: Dict[str, Any]


class SetDesignRequest(BaseModel):
    """Request to set session design."""
    session_id: str
    design: Dict[str, Any]


class StoreFeasibilityRequest(BaseModel):
    """Request to store feasibility results."""
    session_id: str
    score: float = Field(..., ge=0.0, le=100.0)
    risk_bucket: str = Field(..., description="GREEN, YELLOW, RED, UNKNOWN")
    warnings: list[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)


class ApproveRequest(BaseModel):
    """Request to approve a session."""
    session_id: str
    actor: ActorRole = ActorRole.OPERATOR
    note: Optional[str] = None


class RejectRequest(BaseModel):
    """Request to reject a session."""
    session_id: str
    actor: ActorRole = ActorRole.OPERATOR
    reason: str


class StoreToolpathsRequest(BaseModel):
    """Request to store toolpath results."""
    session_id: str
    plan_id: str
    toolpaths_data: Optional[Dict[str, Any]] = None
    gcode_text: Optional[str] = None
    meta: Dict[str, Any] = Field(default_factory=dict)


class RevisionRequest(BaseModel):
    """Request for design revision."""
    session_id: str
    actor: ActorRole = ActorRole.SYSTEM
    reason: str


class ApproveResponse(BaseModel):
    """Response after approval."""
    session_id: str
    state: str
    approved: bool
    message: str
    run_artifact_id: Optional[str] = None


class SessionStateResponse(BaseModel):
    """Full session state."""
    session_id: str
    mode: str
    state: str
    next_step: str
    events_count: int
    last_feasibility_artifact_id: Optional[str] = None
    last_toolpaths_artifact_id: Optional[str] = None


class TransitionResponse(BaseModel):
    """Response after a state transition."""
    session_id: str
    state: str
    previous_state: str
    next_step: str
    run_artifact_id: Optional[str] = None
