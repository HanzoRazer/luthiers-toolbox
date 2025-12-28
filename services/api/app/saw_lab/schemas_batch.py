"""
Saw Lab Batch Schemas

Pydantic models for batch operations: spec, plan, approve, and toolpaths execution.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# =============================================================================
# Batch Spec Schemas
# =============================================================================

class SawBatchSpecItem(BaseModel):
    """Individual item in a batch specification."""
    part_id: str
    qty: int = 1
    material_id: str
    thickness_mm: float
    length_mm: float
    width_mm: float = 0.0
    notes: Optional[str] = None


class SawBatchSpecRequest(BaseModel):
    """Request to create a batch specification."""
    batch_label: str = Field(..., min_length=1)
    session_id: Optional[str] = None
    tool_id: str = "saw:thin_140"
    items: List[SawBatchSpecItem] = Field(..., min_length=1)


class SawBatchSpecResponse(BaseModel):
    """Response from batch spec creation."""
    batch_spec_artifact_id: str
    batch_label: str
    session_id: Optional[str] = None
    status: str
    item_count: int


# =============================================================================
# Batch Plan Schemas
# =============================================================================

class SawBatchPlanOp(BaseModel):
    """Individual operation within a setup."""
    op_id: str
    setup_key: str
    part_id: Optional[str] = None
    material_id: str
    thickness_mm: float
    length_mm: float
    qty: int = 1
    feasibility_score: float = 0.0
    risk_bucket: str = "UNKNOWN"
    warnings: List[str] = Field(default_factory=list)


class SawBatchPlanSetup(BaseModel):
    """A setup grouping related operations."""
    setup_key: str
    tool_id: str
    material_id: Optional[str] = None
    ops: List[SawBatchPlanOp] = Field(default_factory=list)


class SawBatchPlanRequest(BaseModel):
    """Request to generate a batch plan from a spec."""
    batch_spec_artifact_id: str = Field(..., min_length=8)


class SawBatchPlanResponse(BaseModel):
    """Response from batch plan generation."""
    batch_plan_artifact_id: str
    batch_spec_artifact_id: str
    batch_label: Optional[str] = None
    session_id: Optional[str] = None
    status: str
    setups: List[SawBatchPlanSetup] = Field(default_factory=list)


# =============================================================================
# Batch Approve (Choose) Schemas
# =============================================================================

class SawBatchPlanChooseRequest(BaseModel):
    """Request to approve/choose a plan with operator-defined order."""
    batch_plan_artifact_id: str = Field(..., min_length=8)
    approved_by: str = Field(..., min_length=1)
    reason: Optional[str] = None
    setup_order: List[str] = Field(default_factory=list)
    op_order: List[str] = Field(default_factory=list)


class SawBatchPlanChooseResponse(BaseModel):
    """Response from plan approval."""
    batch_decision_artifact_id: str
    batch_plan_artifact_id: str
    batch_spec_artifact_id: Optional[str] = None
    batch_label: Optional[str] = None
    session_id: Optional[str] = None
    status: str


# =============================================================================
# Batch Toolpaths Execution Schemas (NEW)
# =============================================================================

class SawBatchToolpathsRequest(BaseModel):
    """Request to generate toolpaths from an approved decision."""
    batch_decision_artifact_id: str = Field(..., min_length=8)


class SawBatchOpToolpathsResult(BaseModel):
    """Result for a single operation's toolpath generation."""
    op_id: str
    setup_key: str
    status: str  # "OK" | "BLOCKED" | "ERROR"
    risk_bucket: str
    score: float
    toolpaths_artifact_id: str
    warnings: List[str] = Field(default_factory=list)


class SawBatchToolpathsResponse(BaseModel):
    """Response from batch toolpaths generation."""
    batch_execution_artifact_id: str
    batch_decision_artifact_id: str
    batch_plan_artifact_id: Optional[str] = None
    batch_spec_artifact_id: Optional[str] = None
    batch_label: Optional[str] = None
    session_id: Optional[str] = None
    status: str  # "OK" | "ERROR"

    op_count: int
    ok_count: int
    blocked_count: int
    error_count: int

    results: List[SawBatchOpToolpathsResult]


class SawBatchOpToolpathsLookupResponse(BaseModel):
    """
    Optional typed response if you later want strict models on the alias endpoints.
    (Router currently returns raw artifacts for maximum compatibility.)
    """
    artifacts: List[dict]
