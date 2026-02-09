"""
Saw Lab Batch Router Schemas

All Pydantic schema classes used by the Saw Lab batch workflow router
(batch_router.py). Extracted for reuse and cleaner separation of
concerns.

Covers the full batch workflow:
    spec → plan → approve → toolpaths → job-log → learning → retry
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Spec Schemas
# ---------------------------------------------------------------------------


class BatchSpecItem(BaseModel):
    part_id: str
    qty: int = 1
    material_id: str = "maple"
    thickness_mm: float = 6.0
    length_mm: float = 300.0
    width_mm: float = 30.0


class BatchSpecRequest(BaseModel):
    batch_label: str
    session_id: str
    tool_id: str = "saw:thin_140"
    items: List[BatchSpecItem]


class BatchSpecResponse(BaseModel):
    batch_spec_artifact_id: str


# ---------------------------------------------------------------------------
# Plan Schemas
# ---------------------------------------------------------------------------


class BatchPlanRequest(BaseModel):
    batch_spec_artifact_id: str


class BatchPlanOp(BaseModel):
    op_id: str
    part_id: str
    cut_type: str = "crosscut"


class BatchPlanSetup(BaseModel):
    setup_key: str
    tool_id: str
    ops: List[BatchPlanOp]


class BatchPlanResponse(BaseModel):
    batch_plan_artifact_id: str
    setups: List[BatchPlanSetup]
    # Decision Intelligence (approved tuning decision, not learning suggestions)
    decision_intel_advisory: Optional[Dict[str, Any]] = None
    tuning_applied: bool = False
    # Auto-suggest block for UI: applied override (if any) + recommended latest approved (when override cleared)
    plan_auto_suggest: Optional[Dict[str, Any]] = None


# ---------------------------------------------------------------------------
# Approve Schemas
# ---------------------------------------------------------------------------


class BatchApproveRequest(BaseModel):
    batch_plan_artifact_id: str
    approved_by: str
    reason: str
    setup_order: List[str]
    op_order: List[str]


class BatchApproveResponse(BaseModel):
    batch_decision_artifact_id: str


class BatchPlanChooseRequest(BaseModel):
    """
    Operator approval: select ops from a plan, optionally apply recommended patch.
    """

    batch_plan_artifact_id: str
    selected_setup_key: str
    selected_op_ids: List[str]
    apply_recommended_patch: bool = False
    operator_note: str = ""


class BatchPlanChooseResponse(BaseModel):
    """
    Result of operator approval. If apply_recommended_patch=True,
    includes the advisory source decision artifact ID.
    """

    batch_decision_artifact_id: str
    selected_setup_key: str
    applied_context_patch: Optional[Dict[str, Any]] = None
    applied_multipliers: Optional[Dict[str, float]] = None
    advisory_source_decision_artifact_id: Optional[str] = None


# ---------------------------------------------------------------------------
# Toolpaths Schemas
# ---------------------------------------------------------------------------


class BatchToolpathsFromDecisionRequest(BaseModel):
    batch_decision_artifact_id: str
    include_gcode: bool = True


class BatchToolpathsFromDecisionResponse(BaseModel):
    batch_toolpaths_artifact_id: str
    status: str
    error: Optional[str] = None
    decision_apply_stamp: Optional[Dict[str, Any]] = None
    preview: Optional[Dict[str, Any]] = None


class BatchToolpathsRequest(BaseModel):
    batch_decision_artifact_id: str


class BatchOpResult(BaseModel):
    op_id: str
    setup_key: str = ""
    status: str = "OK"
    risk_bucket: str = "GREEN"
    score: float = 1.0
    toolpaths_artifact_id: str
    warnings: List[str] = []


class BatchToolpathsResponse(BaseModel):
    batch_execution_artifact_id: str
    batch_decision_artifact_id: Optional[str] = None
    batch_plan_artifact_id: Optional[str] = None
    batch_spec_artifact_id: Optional[str] = None
    batch_label: Optional[str] = None
    session_id: Optional[str] = None
    status: str = "OK"
    op_count: int = 0
    ok_count: int = 0
    blocked_count: int = 0
    error_count: int = 0
    results: List[BatchOpResult] = []
    gcode_lines: int = 0
    learning: Optional[LearningInfo] = None


class BatchToolpathsByDecisionResponse(BaseModel):
    batch_decision_artifact_id: str
    batch_toolpaths_artifact_id: Optional[str] = None
    status: Optional[str] = None
    created_utc: Optional[str] = None
    statistics: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None
    batch_label: Optional[str] = None


class BatchExecutionByDecisionResponse(BaseModel):
    batch_decision_artifact_id: str
    batch_execution_artifact_id: Optional[str] = None
    status: Optional[str] = None
    created_utc: Optional[str] = None
    statistics: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None
    batch_label: Optional[str] = None


class BatchExecutionsByDecisionResponse(BaseModel):
    batch_decision_artifact_id: str
    session_id: Optional[str] = None
    batch_label: Optional[str] = None
    tool_kind: Optional[str] = None
    total: int
    offset: int
    limit: int
    items: List[Dict[str, Any]]


# ---------------------------------------------------------------------------
# Job Log Schemas
# ---------------------------------------------------------------------------


class JobLogMetrics(BaseModel):
    parts_ok: int = 0
    parts_scrap: int = 0
    cut_time_s: float = 0.0
    setup_time_s: float = 0.0
    burn: bool = False
    tearout: bool = False
    kickback: bool = False


class JobLogRequest(BaseModel):
    metrics: JobLogMetrics = Field(default_factory=JobLogMetrics)


class LearningEvent(BaseModel):
    artifact_id: str
    id: str
    kind: str = "saw_batch_learning_event"
    suggestion_type: str = "parameter_override"


class RollupArtifacts(BaseModel):
    execution_rollup_artifact: Optional[Dict[str, Any]] = None
    decision_rollup_artifact: Optional[Dict[str, Any]] = None


class JobLogResponse(BaseModel):
    job_log_artifact_id: str
    metrics_rollup_artifact_id: Optional[str] = None
    learning_event: Optional[LearningEvent] = None
    learning_hook_enabled: Optional[bool] = None
    rollups: Optional[RollupArtifacts] = None


# ---------------------------------------------------------------------------
# Learning Schemas
# ---------------------------------------------------------------------------


class LearningTuningStamp(BaseModel):
    applied: bool = False
    event_ids: List[str] = []


class LearningResolved(BaseModel):
    source_count: int = 0


class LearningInfo(BaseModel):
    apply_enabled: bool = False
    resolved: LearningResolved = Field(default_factory=LearningResolved)
    tuning_stamp: Optional[LearningTuningStamp] = None


class LearningEventApprovalResponse(BaseModel):
    learning_event_artifact_id: str
    policy_decision: str
    approved_by: str


# ---------------------------------------------------------------------------
# Retry Schemas
# ---------------------------------------------------------------------------


class RetryResponse(BaseModel):
    source_execution_artifact_id: str
    new_execution_artifact_id: str
    retry_artifact_id: str
