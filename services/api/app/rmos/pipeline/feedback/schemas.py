"""
RMOS Pipeline Feedback Schemas

LANE: OPERATION (infrastructure)
Reference: docs/OPERATION_EXECUTION_GOVERNANCE_v1.md, ADR-003 Phase 5

Pydantic models for the feedback loop:
1. Job Logs - Operator feedback on executed jobs
2. Learning Events - Auto-generated learning suggestions
3. Learning Decisions - Accept/reject learning suggestions
4. Metrics Rollups - Aggregated execution statistics
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# =============================================================================
# Job Log Models
# =============================================================================

class JobLogStatus(str, Enum):
    """Status of a logged job."""
    OK = "OK"                   # Job completed successfully
    PARTIAL = "PARTIAL"         # Some issues but usable
    SCRAP = "SCRAP"             # Job failed, parts scrapped
    ABORTED = "ABORTED"         # Job stopped before completion


class JobLogMetrics(BaseModel):
    """
    Metrics captured from a job execution.

    These metrics are used for:
    - Quality signal detection (burn, tearout, kickback)
    - Learning event generation
    - Metrics rollup aggregation
    """
    # Time metrics
    setup_time_s: Optional[float] = Field(None, ge=0, description="Setup time in seconds")
    cut_time_s: Optional[float] = Field(None, ge=0, description="Cut time in seconds")
    total_time_s: Optional[float] = Field(None, ge=0, description="Total job time in seconds")

    # Yield metrics
    parts_ok: int = Field(default=0, ge=0, description="Number of good parts")
    parts_scrap: int = Field(default=0, ge=0, description="Number of scrapped parts")

    # Quality signals (detected or reported)
    burn: bool = Field(default=False, description="Burn marks detected")
    tearout: bool = Field(default=False, description="Tearout detected")
    kickback: bool = Field(default=False, description="Kickback event occurred")
    chatter: bool = Field(default=False, description="Chatter detected")
    tool_wear: bool = Field(default=False, description="Excessive tool wear")

    # Machine metrics
    spindle_load_pct: Optional[float] = Field(None, ge=0, le=100)
    feed_override_pct: Optional[float] = Field(None, ge=0, le=200)
    spindle_override_pct: Optional[float] = Field(None, ge=0, le=200)

    # Custom metrics
    custom: Dict[str, Any] = Field(default_factory=dict)


class JobLog(BaseModel):
    """
    Job log artifact - Operator feedback on an executed job.

    Created by POST /job-log endpoint after job completion.
    Auto-triggers learning event and metrics rollup hooks if enabled.
    """
    artifact_id: str = Field(..., description="Unique artifact ID")
    kind: str = Field(..., description="e.g., 'roughing_job_log'")
    created_at_utc: str = Field(..., description="ISO 8601 timestamp")

    # Parent reference
    execution_artifact_id: str = Field(..., description="Parent execution artifact")
    op_id: Optional[str] = Field(None, description="Specific operation (if applicable)")

    # Operator info
    operator: str = Field(..., description="Operator name/ID")
    station: Optional[str] = Field(None, description="Workstation ID")

    # Job status
    status: JobLogStatus = Field(..., description="Job completion status")
    notes: Optional[str] = Field(None, description="Operator notes")

    # Metrics
    metrics: JobLogMetrics = Field(default_factory=JobLogMetrics)

    # Index metadata
    tool_type: str = Field(..., description="Tool type (e.g., 'roughing')")
    batch_label: Optional[str] = None
    session_id: Optional[str] = None


class JobLogRequest(BaseModel):
    """Request to create a job log."""
    execution_artifact_id: str = Field(..., description="Execution to log")
    op_id: Optional[str] = Field(None, description="Specific operation")
    operator: str = Field(..., description="Operator name/ID")
    station: Optional[str] = Field(None, description="Workstation ID")
    status: JobLogStatus = Field(..., description="Job status")
    notes: Optional[str] = Field(None, description="Operator notes")
    metrics: JobLogMetrics = Field(default_factory=JobLogMetrics)


class JobLogResponse(BaseModel):
    """Response after creating a job log."""
    job_log_artifact_id: str
    execution_artifact_id: str
    status: str
    learning_event_emitted: bool = False
    metrics_rollup_updated: bool = False


# =============================================================================
# Learning Event Models
# =============================================================================

class QualitySignal(str, Enum):
    """Quality signals detected from job execution."""
    BURN = "burn"               # Burn marks - reduce feed or increase RPM
    TEAROUT = "tearout"         # Tearout - adjust feed direction or reduce DOC
    KICKBACK = "kickback"       # Kickback - reduce feed rate
    CHATTER = "chatter"         # Chatter - adjust RPM or reduce DOC
    TOOL_WEAR = "tool_wear"     # Tool wear - schedule tool change
    EXCELLENT = "excellent"     # Excellent finish - current params are good


class LearningMultipliers(BaseModel):
    """
    Suggested parameter multipliers for learning.

    Values > 1.0 increase the parameter, < 1.0 decrease it.
    """
    spindle_rpm_mult: float = Field(default=1.0, ge=0.5, le=2.0)
    feed_rate_mult: float = Field(default=1.0, ge=0.5, le=2.0)
    doc_mult: float = Field(default=1.0, ge=0.5, le=2.0)  # Depth of cut
    woc_mult: float = Field(default=1.0, ge=0.5, le=2.0)  # Width of cut


class LearningSuggestion(BaseModel):
    """A learning suggestion based on quality signals."""
    signal: QualitySignal
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    multipliers: LearningMultipliers = Field(default_factory=LearningMultipliers)
    rationale: str = Field(default="", description="Human-readable explanation")


class LearningEvent(BaseModel):
    """
    Learning event artifact - Auto-generated from job log analysis.

    Contains suggested parameter adjustments based on quality signals.
    Requires explicit ACCEPT decision before being applied.
    """
    artifact_id: str = Field(..., description="Unique artifact ID")
    kind: str = Field(..., description="e.g., 'roughing_learning_event'")
    created_at_utc: str = Field(..., description="ISO 8601 timestamp")

    # Parent references
    job_log_artifact_id: str = Field(..., description="Source job log")
    execution_artifact_id: str = Field(..., description="Related execution")

    # Context snapshot (for matching future jobs)
    tool_id: Optional[str] = None
    material_id: Optional[str] = None
    operation_type: Optional[str] = None

    # Detected signals
    signals: List[QualitySignal] = Field(default_factory=list)

    # Suggestions
    suggestions: List[LearningSuggestion] = Field(default_factory=list)

    # Aggregate multipliers (average of suggestions)
    aggregate_multipliers: LearningMultipliers = Field(default_factory=LearningMultipliers)

    # Index metadata
    tool_type: str = Field(...)
    batch_label: Optional[str] = None


class LearningEventResponse(BaseModel):
    """Response after creating a learning event."""
    learning_event_artifact_id: str
    job_log_artifact_id: str
    signals_detected: List[str]
    suggestions_count: int


# =============================================================================
# Learning Decision Models
# =============================================================================

class LearningDecisionPolicy(str, Enum):
    """Policy for a learning decision."""
    PROPOSE = "PROPOSE"     # Suggested, awaiting review
    ACCEPT = "ACCEPT"       # Accepted, will be applied
    REJECT = "REJECT"       # Rejected, will not be applied


class LearningDecision(BaseModel):
    """
    Learning decision artifact - Accept/reject a learning event.

    Only ACCEPTED learning events are applied to future executions.
    """
    artifact_id: str = Field(..., description="Unique artifact ID")
    kind: str = Field(..., description="e.g., 'roughing_learning_decision'")
    created_at_utc: str = Field(..., description="ISO 8601 timestamp")

    # Parent reference
    learning_event_artifact_id: str = Field(..., description="Learning event")

    # Decision
    policy: LearningDecisionPolicy = Field(...)
    decided_by: str = Field(..., description="Who made the decision")
    reason: Optional[str] = Field(None, description="Decision rationale")

    # Accepted multipliers (if policy == ACCEPT)
    accepted_multipliers: Optional[LearningMultipliers] = None


class LearningDecisionRequest(BaseModel):
    """Request to create a learning decision."""
    learning_event_artifact_id: str = Field(...)
    policy: LearningDecisionPolicy = Field(...)
    decided_by: str = Field(...)
    reason: Optional[str] = None
    # Override multipliers (optional, uses event's aggregate if not provided)
    multipliers: Optional[LearningMultipliers] = None


class LearningDecisionResponse(BaseModel):
    """Response after creating a learning decision."""
    learning_decision_artifact_id: str
    learning_event_artifact_id: str
    policy: str
    will_be_applied: bool


# =============================================================================
# Metrics Rollup Models
# =============================================================================

class TimeMetrics(BaseModel):
    """Aggregated time metrics."""
    setup_time_s_total: float = 0.0
    setup_time_s_avg: float = 0.0
    cut_time_s_total: float = 0.0
    cut_time_s_avg: float = 0.0
    total_time_s_total: float = 0.0
    total_time_s_avg: float = 0.0


class YieldMetrics(BaseModel):
    """Aggregated yield metrics."""
    parts_ok_total: int = 0
    parts_scrap_total: int = 0
    parts_total: int = 0
    yield_rate: float = Field(default=0.0, ge=0.0, le=1.0)


class EventCounts(BaseModel):
    """Counts of quality events."""
    burn_events: int = 0
    tearout_events: int = 0
    kickback_events: int = 0
    chatter_events: int = 0
    tool_wear_events: int = 0
    excellent_events: int = 0


class MetricsRollup(BaseModel):
    """
    Metrics rollup artifact - Aggregated execution statistics.

    Provides summary metrics for an execution or decision level.
    """
    artifact_id: str = Field(..., description="Unique artifact ID")
    kind: str = Field(..., description="e.g., 'roughing_execution_metrics_rollup'")
    created_at_utc: str = Field(..., description="ISO 8601 timestamp")
    rollup_level: str = Field(..., description="'execution' or 'decision'")

    # Parent reference
    parent_artifact_id: str = Field(..., description="Execution or decision artifact")

    # Counts
    job_log_count: int = 0
    learning_event_count: int = 0
    learning_accepted_count: int = 0

    # Operators
    operators: Dict[str, int] = Field(default_factory=dict)

    # Statuses
    statuses: Dict[str, int] = Field(default_factory=dict)

    # Time metrics
    time_metrics: TimeMetrics = Field(default_factory=TimeMetrics)

    # Yield metrics
    yield_metrics: YieldMetrics = Field(default_factory=YieldMetrics)

    # Event counts
    event_counts: EventCounts = Field(default_factory=EventCounts)

    # Learning application tracking
    learning_applied_count: int = 0
    learning_applied_rate: float = 0.0


class MetricsRollupResponse(BaseModel):
    """Response after creating a metrics rollup."""
    rollup_artifact_id: str
    parent_artifact_id: str
    rollup_level: str
    job_log_count: int
    yield_rate: float
