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
]
