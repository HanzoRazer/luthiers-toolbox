"""
RMOS Pipeline Schemas - Base Types for Multi-Stage Execution

LANE: OPERATION (infrastructure)
Reference: docs/OPERATION_EXECUTION_GOVERNANCE_v1.md, ADR-003 Phase 4

This module defines the base Pydantic models for the 4-stage pipeline:
SPEC → PLAN → DECISION → EXECUTE

Each stage creates an immutable artifact that links to its parent,
forming an auditable chain for deterministic replay.

ARTIFACT NAMING CONVENTION:
    {tool_type}_{stage}

    Examples:
    - roughing_spec, roughing_plan, roughing_decision, roughing_execution
    - drilling_spec, drilling_plan, drilling_decision, drilling_execution
    - helical_spec, helical_plan, helical_decision, helical_execution
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class PipelineStage(str, Enum):
    """Pipeline stage enumeration."""
    SPEC = "spec"           # Design intent captured
    PLAN = "plan"           # Feasibility scored
    DECISION = "decision"   # Operator approved
    EXECUTE = "execute"     # Toolpaths generated


class PipelineStatus(str, Enum):
    """Artifact status enumeration."""
    CREATED = "CREATED"     # Artifact created
    OK = "OK"               # Stage completed successfully
    BLOCKED = "BLOCKED"     # Safety policy blocked
    ERROR = "ERROR"         # Error during processing
    APPROVED = "APPROVED"   # Decision approved
    REJECTED = "REJECTED"   # Decision rejected


class RiskBucket(str, Enum):
    """Risk classification for feasibility."""
    GREEN = "GREEN"         # Safe to proceed
    YELLOW = "YELLOW"       # Proceed with caution
    RED = "RED"             # Do not proceed
    UNKNOWN = "UNKNOWN"     # Cannot determine


class ArtifactKind(str, Enum):
    """Standard artifact kinds following naming convention."""
    # Generic pipeline
    SPEC = "spec"
    PLAN = "plan"
    DECISION = "decision"
    EXECUTION = "execution"
    OP_TOOLPATHS = "op_toolpaths"


# =============================================================================
# Base Artifact Types
# =============================================================================

class IndexMeta(BaseModel):
    """
    Index metadata for artifact queries.

    Stores parent references and searchable fields for efficient lookups.
    """
    # Parent lineage (for ancestry queries)
    parent_spec_artifact_id: Optional[str] = None
    parent_plan_artifact_id: Optional[str] = None
    parent_decision_artifact_id: Optional[str] = None
    parent_execution_artifact_id: Optional[str] = None

    # Searchable fields
    tool_type: Optional[str] = None         # e.g., "roughing", "drilling", "helical"
    batch_label: Optional[str] = None       # User-provided label
    session_id: Optional[str] = None        # Session correlation
    workflow_mode: Optional[str] = None     # Workflow context

    # Approval metadata (for decision stage)
    approved_by: Optional[str] = None

    # Summary counts (for execution stage)
    op_count: Optional[int] = None
    ok_count: Optional[int] = None
    blocked_count: Optional[int] = None
    error_count: Optional[int] = None


class PipelineArtifactBase(BaseModel):
    """
    Base class for all pipeline artifacts.

    Every artifact in the pipeline has:
    - Unique ID (generated on creation)
    - Kind (tool_type + stage, e.g., "roughing_spec")
    - Status (CREATED, OK, BLOCKED, ERROR, APPROVED, REJECTED)
    - Timestamps
    - Index metadata for queries
    - Hashes for integrity verification
    """
    artifact_id: str = Field(..., description="Unique artifact identifier")
    kind: str = Field(..., description="Artifact kind (e.g., 'roughing_spec')")
    stage: PipelineStage = Field(..., description="Pipeline stage")
    status: PipelineStatus = Field(..., description="Artifact status")

    created_at_utc: str = Field(..., description="ISO 8601 timestamp")

    index_meta: IndexMeta = Field(default_factory=IndexMeta, description="Query metadata")

    # Integrity hashes
    request_hash: Optional[str] = Field(None, description="SHA256 of request payload")
    output_hash: Optional[str] = Field(None, description="SHA256 of output (G-code, etc.)")

    # Error tracking
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


# =============================================================================
# Stage-Specific Artifact Types
# =============================================================================

class SpecArtifact(PipelineArtifactBase):
    """
    SPEC stage artifact - Captures design intent.

    The spec artifact stores the original request parameters that define
    what the user wants to machine. It's the root of the artifact chain.
    """
    stage: PipelineStage = Field(default=PipelineStage.SPEC)

    # Design parameters (tool-specific, stored as dict)
    design: Dict[str, Any] = Field(default_factory=dict, description="Design parameters")

    # Context parameters (tool, material, machine)
    context: Dict[str, Any] = Field(default_factory=dict, description="Machining context")

    # Batch information
    batch_label: Optional[str] = None
    session_id: Optional[str] = None
    item_count: int = Field(default=1, description="Number of items in batch")


class PlanOperation(BaseModel):
    """
    Single operation within a plan.

    Each operation represents one machining step with its own
    feasibility score and risk classification.
    """
    op_id: str = Field(..., description="Operation identifier")
    setup_key: Optional[str] = Field(None, description="Setup grouping key")

    # Design/context snapshot for this op
    design: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)

    # Feasibility result
    feasibility_score: float = Field(default=0.0, ge=0.0, le=100.0)
    risk_bucket: RiskBucket = Field(default=RiskBucket.UNKNOWN)
    warnings: List[str] = Field(default_factory=list)

    # Feasibility details (calculator results, etc.)
    feasibility_details: Dict[str, Any] = Field(default_factory=dict)


class PlanArtifact(PipelineArtifactBase):
    """
    PLAN stage artifact - Feasibility-scored execution plan.

    The plan artifact contains all operations organized by setup,
    each with feasibility scores and risk classifications.
    """
    stage: PipelineStage = Field(default=PipelineStage.PLAN)

    # Parent reference
    spec_artifact_id: str = Field(..., description="Parent spec artifact ID")

    # Operations grouped by setup
    operations: List[PlanOperation] = Field(default_factory=list)

    # Aggregate feasibility
    aggregate_score: float = Field(default=0.0, ge=0.0, le=100.0)
    aggregate_risk: RiskBucket = Field(default=RiskBucket.UNKNOWN)

    # Summary counts
    op_count: int = Field(default=0)
    green_count: int = Field(default=0)
    yellow_count: int = Field(default=0)
    red_count: int = Field(default=0)


class ChosenOrder(BaseModel):
    """Operator-chosen execution order (locked at approval)."""
    setup_order: List[str] = Field(default_factory=list, description="Order of setups")
    op_order: List[str] = Field(default_factory=list, description="Order of operations")


class DecisionArtifact(PipelineArtifactBase):
    """
    DECISION stage artifact - Operator approval checkpoint.

    The decision artifact locks in the execution order and records
    who approved the plan and why. This is the governance checkpoint.
    """
    stage: PipelineStage = Field(default=PipelineStage.DECISION)

    # Parent references
    plan_artifact_id: str = Field(..., description="Parent plan artifact ID")
    spec_artifact_id: str = Field(..., description="Root spec artifact ID")

    # Approval metadata
    approved_by: str = Field(..., description="Operator who approved")
    reason: Optional[str] = Field(None, description="Approval reason/notes")

    # Locked execution order
    chosen_order: ChosenOrder = Field(default_factory=ChosenOrder)

    # Decision status
    decision_status: str = Field(default="APPROVED", description="APPROVED or REJECTED")


class ExecutionResult(BaseModel):
    """Result for a single operation execution."""
    op_id: str = Field(..., description="Operation identifier")
    setup_key: Optional[str] = None

    status: PipelineStatus = Field(..., description="OK, BLOCKED, or ERROR")
    risk_bucket: RiskBucket = Field(default=RiskBucket.UNKNOWN)
    feasibility_score: float = Field(default=0.0)

    # Child artifact reference
    toolpaths_artifact_id: Optional[str] = None

    # Errors/warnings for this op
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class ExecutionArtifact(PipelineArtifactBase):
    """
    EXECUTE stage artifact - Toolpaths generated.

    The execution artifact is the parent container for all
    op_toolpaths artifacts. It tracks the overall execution summary.
    """
    stage: PipelineStage = Field(default=PipelineStage.EXECUTE)

    # Parent references (full lineage)
    decision_artifact_id: str = Field(..., description="Parent decision artifact ID")
    plan_artifact_id: str = Field(..., description="Parent plan artifact ID")
    spec_artifact_id: str = Field(..., description="Root spec artifact ID")

    # Execution summary
    op_count: int = Field(default=0)
    ok_count: int = Field(default=0)
    blocked_count: int = Field(default=0)
    error_count: int = Field(default=0)

    # Child artifact references
    results: List[ExecutionResult] = Field(default_factory=list)
    children: List[Dict[str, str]] = Field(
        default_factory=list,
        description="List of {artifact_id, kind} for child op_toolpaths"
    )

    # Retry tracking
    is_retry: bool = Field(default=False)
    retry_of_execution_id: Optional[str] = None
    retry_reason: Optional[str] = None


class OpToolpathsArtifact(PipelineArtifactBase):
    """
    OP_TOOLPATHS artifact - Individual operation result.

    Child artifact containing the actual toolpaths/G-code for one operation.
    """
    stage: PipelineStage = Field(default=PipelineStage.EXECUTE)

    # Parent references
    execution_artifact_id: str = Field(..., description="Parent execution artifact ID")
    decision_artifact_id: str = Field(..., description="Parent decision artifact ID")

    # Operation identification
    op_id: str = Field(..., description="Operation identifier")
    setup_key: Optional[str] = None

    # Input snapshot (for deterministic replay)
    design: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)

    # Feasibility (recomputed server-side)
    feasibility_recomputed: Dict[str, Any] = Field(default_factory=dict)

    # Output
    toolpaths: Dict[str, Any] = Field(
        default_factory=dict,
        description="Toolpath data (moves, gcode, stats)"
    )
    gcode: Optional[str] = Field(None, description="Generated G-code")
    gcode_hash: Optional[str] = Field(None, description="SHA256 of G-code")


# =============================================================================
# Request/Response Types
# =============================================================================

class SpecRequest(BaseModel):
    """Base request for creating a spec artifact."""
    batch_label: Optional[str] = Field(None, description="User-provided batch label")
    session_id: Optional[str] = Field(None, description="Session correlation ID")

    # Design parameters (tool-specific)
    design: Dict[str, Any] = Field(..., description="Design parameters")

    # Context parameters (tool, material, machine)
    context: Dict[str, Any] = Field(default_factory=dict, description="Machining context")


class SpecResponse(BaseModel):
    """Response after creating a spec artifact."""
    spec_artifact_id: str
    batch_label: Optional[str] = None
    session_id: Optional[str] = None
    status: str
    item_count: int = 1


class PlanRequest(BaseModel):
    """Request for creating a plan from a spec."""
    spec_artifact_id: str = Field(..., description="Parent spec artifact ID")


class PlanResponse(BaseModel):
    """Response after creating a plan artifact."""
    plan_artifact_id: str
    spec_artifact_id: str
    batch_label: Optional[str] = None
    status: str
    op_count: int
    aggregate_score: float
    aggregate_risk: str
    operations: List[PlanOperation] = Field(default_factory=list)


class ApproveRequest(BaseModel):
    """Request for approving a plan (creating decision artifact)."""
    plan_artifact_id: str = Field(..., description="Plan to approve")
    approved_by: str = Field(..., description="Operator name/ID")
    reason: Optional[str] = Field(None, description="Approval reason")
    setup_order: List[str] = Field(default_factory=list, description="Chosen setup order")
    op_order: List[str] = Field(default_factory=list, description="Chosen op order")


class ApproveResponse(BaseModel):
    """Response after creating a decision artifact."""
    decision_artifact_id: str
    plan_artifact_id: str
    spec_artifact_id: str
    batch_label: Optional[str] = None
    status: str
    approved_by: str


class ExecuteRequest(BaseModel):
    """Request for executing a decision (generating toolpaths)."""
    decision_artifact_id: str = Field(..., description="Approved decision to execute")

    # Optional: subset of ops to execute
    op_ids: Optional[List[str]] = Field(None, description="Specific ops to execute (None = all)")


class ExecuteResponse(BaseModel):
    """Response after creating an execution artifact."""
    execution_artifact_id: str
    decision_artifact_id: str
    plan_artifact_id: Optional[str] = None
    spec_artifact_id: Optional[str] = None
    batch_label: Optional[str] = None
    status: str
    op_count: int
    ok_count: int
    blocked_count: int
    error_count: int
    results: List[ExecutionResult] = Field(default_factory=list)


# =============================================================================
# Query Types
# =============================================================================

class ArtifactQuery(BaseModel):
    """Query parameters for artifact lookup."""
    kind: Optional[str] = None
    tool_type: Optional[str] = None
    batch_label: Optional[str] = None
    session_id: Optional[str] = None

    # Parent filters
    parent_spec_artifact_id: Optional[str] = None
    parent_plan_artifact_id: Optional[str] = None
    parent_decision_artifact_id: Optional[str] = None

    # Status filter
    status: Optional[str] = None

    # Pagination
    limit: int = Field(default=25, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class ArtifactQueryResult(BaseModel):
    """Result of an artifact query."""
    items: List[Dict[str, Any]] = Field(default_factory=list)
    total: int = 0
    limit: int = 25
    offset: int = 0
