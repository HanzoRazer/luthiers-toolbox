"""Art Studio Workflow Integration — Request/Response Models.

Extracted from ``workflow_integration.py`` (WP-3 decomposition).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Conditional imports for state-machine enums / schemas
# ---------------------------------------------------------------------------
try:
    from app.workflow.state_machine import WorkflowMode
    from app.art_studio.schemas.design_snapshot import DesignContextRefs
    from app.art_studio.schemas.rosette_params import RosetteParamSpec
except ImportError:
    try:
        from workflow.state_machine import WorkflowMode
        from art_studio.schemas.design_snapshot import DesignContextRefs
        from art_studio.schemas.rosette_params import RosetteParamSpec
    except ImportError:
        from ...workflow.state_machine import WorkflowMode
        from ..schemas.design_snapshot import DesignContextRefs
        from ..schemas.rosette_params import RosetteParamSpec


# =========================================================================
# Creation Requests
# =========================================================================

class CreateFromPatternRequest(BaseModel):
    """Create workflow session from a pattern library item."""

    pattern_id: str
    mode: WorkflowMode = WorkflowMode.DESIGN_FIRST
    context_refs: Optional[DesignContextRefs] = None
    context_override: Optional[Dict[str, Any]] = None


class CreateFromGeneratorRequest(BaseModel):
    """Create workflow session directly from a generator."""

    generator_key: str
    outer_diameter_mm: float = Field(..., gt=0)
    inner_diameter_mm: float = Field(..., ge=0)
    params: Dict[str, Any] = Field(default_factory=dict)
    mode: WorkflowMode = WorkflowMode.DESIGN_FIRST
    context_refs: Optional[DesignContextRefs] = None
    context_override: Optional[Dict[str, Any]] = None


class CreateFromSnapshotRequest(BaseModel):
    """Create workflow session from a saved snapshot."""

    snapshot_id: str
    mode: Optional[WorkflowMode] = None  # None = use snapshot's mode
    context_override: Optional[Dict[str, Any]] = None


# =========================================================================
# Action Requests
# =========================================================================

class EvaluateFeasibilityRequest(BaseModel):
    """Request to evaluate feasibility for a session."""

    context_override: Optional[Dict[str, Any]] = None


class ApproveSessionRequest(BaseModel):
    """Request to approve a session."""

    note: Optional[str] = None


class RejectSessionRequest(BaseModel):
    """Request to reject a session."""

    reason: str


class RequestRevisionRequest(BaseModel):
    """Request design revision."""

    reason: str


class UpdateDesignRequest(BaseModel):
    """Update session design parameters."""

    rosette_params: RosetteParamSpec


class SaveSnapshotRequest(BaseModel):
    """Save current session state as a snapshot."""

    name: str = Field(..., min_length=1, max_length=200)
    notes: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


# =========================================================================
# Responses
# =========================================================================

class SessionStatusResponse(BaseModel):
    """Detailed session status for UI."""

    session_id: str
    mode: str
    state: str
    next_step: str
    events_count: int

    # Design info
    has_design: bool
    has_context: bool

    # Feasibility info
    feasibility_score: Optional[float] = None
    feasibility_risk: Optional[str] = None
    feasibility_warnings: List[str] = Field(default_factory=list)

    # Artifact refs
    last_feasibility_artifact_id: Optional[str] = None
    last_toolpaths_artifact_id: Optional[str] = None

    # Governance
    allow_red_override: bool = False
    require_explicit_approval: bool = True


class WorkflowCreatedResponse(BaseModel):
    """Response after creating a workflow session."""

    session_id: str
    mode: str
    state: str
    next_step: str
    warnings: List[str] = Field(default_factory=list)


class FeasibilityResponse(BaseModel):
    """Response after feasibility evaluation."""

    session_id: str
    state: str
    score: float
    risk_bucket: str
    warnings: List[str]
    run_artifact_id: Optional[str] = None
    next_step: str


class ApprovalResponse(BaseModel):
    """Response after approval/rejection."""

    session_id: str
    state: str
    approved: bool
    message: str
    run_artifact_id: Optional[str] = None


class SnapshotCreatedResponse(BaseModel):
    """Response after saving a snapshot."""

    snapshot_id: str
    name: str
    session_id: str


class GeneratorInfo(BaseModel):
    """Generator info for UI."""

    generator_key: str
    name: str
    description: str
    param_hints: Dict[str, Any]
