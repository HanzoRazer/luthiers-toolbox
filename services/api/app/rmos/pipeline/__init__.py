"""
RMOS Pipeline Package - Multi-Stage Execution Pipeline

LANE: OPERATION (infrastructure)
Reference: docs/OPERATION_EXECUTION_GOVERNANCE_v1.md, ADR-003 Phase 4

This package provides the base infrastructure for implementing the
SPEC → PLAN → DECISION → EXECUTE pipeline pattern used by OPERATION lane endpoints.

Pipeline Stages:
1. SPEC: Capture design intent and parameters (immutable input)
2. PLAN: Generate feasibility-scored execution plan
3. DECISION: Operator approval checkpoint (locks execution order)
4. EXECUTE: Generate toolpaths/G-code with artifact persistence

Key Features:
- Immutable artifact chain (each stage creates new artifact)
- Parent-child linking for lineage tracking
- Approval checkpoint with operator attribution
- Deterministic replay via artifact queries
- Server-side feasibility recompute on every execution

Reference Implementation:
- Saw Lab Batch Pipeline (services/api/app/saw_lab/batch_router.py)
"""
from .schemas import (
    PipelineStage,
    PipelineStatus,
    ArtifactKind,
    # Base artifact types
    PipelineArtifactBase,
    SpecArtifact,
    PlanArtifact,
    DecisionArtifact,
    ExecutionArtifact,
    # Request/Response types
    SpecRequest,
    SpecResponse,
    PlanRequest,
    PlanResponse,
    ApproveRequest,
    ApproveResponse,
    ExecuteRequest,
    ExecuteResponse,
    # Operation types
    PlanOperation,
    ExecutionResult,
    # Lookup types
    ArtifactQuery,
    ArtifactQueryResult,
)

from .store import (
    PipelineStore,
    get_pipeline_store,
    write_artifact,
    read_artifact,
    query_artifacts,
    list_executions_for_decision,
    latest_execution_for_decision,
)

from .services import (
    PipelineService,
    create_spec_artifact,
    create_plan_artifact,
    create_decision_artifact,
    create_execution_artifact,
)

# Feedback Loop (Phase 5 - ADR-003)
from .feedback import (
    # Schemas
    JobLogStatus,
    JobLogMetrics,
    JobLog,
    JobLogRequest,
    JobLogResponse,
    QualitySignal,
    LearningMultipliers,
    LearningSuggestion,
    LearningEvent,
    LearningEventResponse,
    LearningDecisionPolicy,
    LearningDecision,
    LearningDecisionRequest,
    LearningDecisionResponse,
    TimeMetrics,
    YieldMetrics,
    EventCounts,
    MetricsRollup,
    MetricsRollupResponse,
    # Config
    FeedbackConfig,
    get_feedback_config,
    is_learning_hook_enabled,
    is_metrics_rollup_hook_enabled,
    is_apply_overrides_enabled,
    get_learned_overrides_path,
    # Job Log Service
    JobLogService,
    write_job_log,
    list_job_logs_for_execution,
    # Learning Service
    LearningService,
    detect_signals,
    generate_suggestions,
    emit_learning_event,
    create_learning_decision,
    resolve_learned_multipliers,
    apply_multipliers_to_context,
    # Rollup Service
    RollupService,
    compute_execution_rollup,
    persist_execution_rollup,
    get_latest_rollup,
    list_rollup_history,
)

__all__ = [
    # Enums
    "PipelineStage",
    "PipelineStatus",
    "ArtifactKind",
    # Base artifact types
    "PipelineArtifactBase",
    "SpecArtifact",
    "PlanArtifact",
    "DecisionArtifact",
    "ExecutionArtifact",
    # Request/Response types
    "SpecRequest",
    "SpecResponse",
    "PlanRequest",
    "PlanResponse",
    "ApproveRequest",
    "ApproveResponse",
    "ExecuteRequest",
    "ExecuteResponse",
    # Operation types
    "PlanOperation",
    "ExecutionResult",
    # Lookup types
    "ArtifactQuery",
    "ArtifactQueryResult",
    # Store functions
    "PipelineStore",
    "get_pipeline_store",
    "write_artifact",
    "read_artifact",
    "query_artifacts",
    "list_executions_for_decision",
    "latest_execution_for_decision",
    # Service functions
    "PipelineService",
    "create_spec_artifact",
    "create_plan_artifact",
    "create_decision_artifact",
    "create_execution_artifact",
    # Feedback Schemas (Phase 5)
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
    # Feedback Config (Phase 5)
    "FeedbackConfig",
    "get_feedback_config",
    "is_learning_hook_enabled",
    "is_metrics_rollup_hook_enabled",
    "is_apply_overrides_enabled",
    "get_learned_overrides_path",
    # Job Log Service (Phase 5)
    "JobLogService",
    "write_job_log",
    "list_job_logs_for_execution",
    # Learning Service (Phase 5)
    "LearningService",
    "detect_signals",
    "generate_suggestions",
    "emit_learning_event",
    "create_learning_decision",
    "resolve_learned_multipliers",
    "apply_multipliers_to_context",
    # Rollup Service (Phase 5)
    "RollupService",
    "compute_execution_rollup",
    "persist_execution_rollup",
    "get_latest_rollup",
    "list_rollup_history",
]
