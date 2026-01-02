"""
RMOS Pipeline Feedback Package - Learning Events & Metrics Rollups

LANE: OPERATION (infrastructure)
Reference: docs/OPERATION_EXECUTION_GOVERNANCE_v1.md, ADR-003 Phase 5

This package provides the feedback loop infrastructure for the pipeline:
1. Job Logging - Operator feedback on executed jobs
2. Learning Events - Auto-generated learning suggestions
3. Learning Decisions - Accept/reject learning suggestions
4. Metrics Rollups - Aggregated execution statistics

Feature Flags (all default to OFF for safety):
- {TOOL}_LEARNING_HOOK_ENABLED - Auto-emit learning events from job logs
- {TOOL}_METRICS_ROLLUP_HOOK_ENABLED - Auto-persist metrics rollups
- {TOOL}_APPLY_ACCEPTED_OVERRIDES - Apply learned multipliers to contexts

Reference Implementation:
- Saw Lab Feedback (services/api/app/services/saw_lab_*_service.py)
"""
from .schemas import (
    # Job Log
    JobLogStatus,
    JobLogMetrics,
    JobLog,
    JobLogRequest,
    JobLogResponse,
    # Learning Event
    QualitySignal,
    LearningMultipliers,
    LearningSuggestion,
    LearningEvent,
    LearningEventResponse,
    # Learning Decision
    LearningDecisionPolicy,
    LearningDecision,
    LearningDecisionRequest,
    LearningDecisionResponse,
    # Metrics Rollup
    TimeMetrics,
    YieldMetrics,
    EventCounts,
    MetricsRollup,
    MetricsRollupResponse,
)

from .config import (
    FeedbackConfig,
    get_feedback_config,
    is_learning_hook_enabled,
    is_metrics_rollup_hook_enabled,
    is_apply_overrides_enabled,
)

from .job_log import (
    JobLogService,
    write_job_log,
    list_job_logs_for_execution,
)

from .learning import (
    LearningService,
    emit_learning_event,
    create_learning_decision,
    resolve_learned_multipliers,
    apply_multipliers_to_context,
)

from .rollups import (
    RollupService,
    compute_execution_rollup,
    persist_execution_rollup,
    get_latest_rollup,
    list_rollup_history,
)

__all__ = [
    # Schemas
    "JobLogStatus",
    "JobLogMetrics",
    "JobLog",
    "JobLogRequest",
    "JobLogResponse",
    "QualitySignal",
    "LearningMultipliers",
    "LearningSuggestion",
    "LearningEvent",
    "LearningEventResponse",
    "LearningDecisionPolicy",
    "LearningDecision",
    "LearningDecisionRequest",
    "LearningDecisionResponse",
    "TimeMetrics",
    "YieldMetrics",
    "EventCounts",
    "MetricsRollup",
    "MetricsRollupResponse",
    # Config
    "FeedbackConfig",
    "get_feedback_config",
    "is_learning_hook_enabled",
    "is_metrics_rollup_hook_enabled",
    "is_apply_overrides_enabled",
    # Job Log
    "JobLogService",
    "write_job_log",
    "list_job_logs_for_execution",
    # Learning
    "LearningService",
    "emit_learning_event",
    "create_learning_decision",
    "resolve_learned_multipliers",
    "apply_multipliers_to_context",
    # Rollups
    "RollupService",
    "compute_execution_rollup",
    "persist_execution_rollup",
    "get_latest_rollup",
    "list_rollup_history",
]
