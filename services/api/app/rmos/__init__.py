"""
RMOS Package - Rosette Manufacturing Optimization System

This package provides:
- Feasibility scoring for rosette designs
- AI-assisted constraint-first search
- Constraint profile management with history
- Logging and analytics for AI operations
- API routes for manufacturing optimization

Existing Modules (already in repo):
- api_contracts: Core type definitions
- feasibility_scorer: Design scoring engine
- logging_ai: AI attempt/run logging (integrates with logging_core)
- schemas_logs_ai: Read-only log view schemas
- ai_policy: Global constraint clamping

Phase B Additions:
- schemas_ai: Request/response models for AI search API
- ai_search: Constraint-first search loop
- api_ai_routes: FastAPI router for AI endpoints

Phase C Additions:
- constraint_profiles: YAML-based profile management
- profile_history: JSONL change journal
- api_constraint_profiles: Profile CRUD endpoints
- api_profile_history: History/rollback endpoints
"""

# Core API contracts
from .api_contracts import (
    RiskBucket,
    RmosContext,
    RmosFeasibilityResult,
    RmosBomResult,
    RmosToolpathPlan,
    RmosServices,
    compute_feasibility_for_design,
)

# AI Search Schemas (Phase B)
from .schemas_ai import (
    SearchStatus,
    WorkflowMode,
    SearchContext,
    SearchBudget,
    AiSearchRequest,
    AiSearchResponse,
    AiSearchSummary,
    SearchAttemptSummary,
)

# AI Search Engine (Phase B)
from .ai_search import (
    run_constraint_first_search,
    get_search_status_description,
)

# Constraint Profiles (Phase C)
from .constraint_profiles import (
    RosetteGeneratorConstraints,
    ProfileMetadata,
    ConstraintProfile,
    ProfileStore,
    get_profile_store,
    get_constraints_by_profile_id,
    list_available_profiles,
    default_constraints,
    constraints_for_beginner,
    constraints_for_advanced,
)

# Profile History (Phase C)
from .profile_history import (
    ChangeType,
    ProfileHistoryEntry,
    ProfileHistoryStore,
    get_profile_history_store,
    record_profile_change,
    get_profile_history,
)

# Routers
from .api_ai_routes import router as ai_router
from .api_constraint_profiles import router as profiles_router
from .api_profile_history import router as history_router
from .api_routes import router as rmos_router  # Existing core RMOS router

# Runs Module (Phase D - Audit Trail)
# Feature flag: RMOS_RUNS_V2_ENABLED controls v1/v2 implementation
# DEFAULT: true (v2 governance-compliant implementation)
# Set to "false" to use legacy v1 if needed for rollback
import os
_RMOS_RUNS_V2_ENABLED = os.getenv("RMOS_RUNS_V2_ENABLED", "true").lower() == "true"

if _RMOS_RUNS_V2_ENABLED:
    # v2: Pydantic schemas, date-partitioned storage, immutable artifacts
    try:
        from .runs_v2 import (
            RunArtifact,
            RunAttachment,
            RunDecision,
            Hashes,
            RunOutputs,
            AdvisoryInputRef,
            RunStatus,
            get_run,
            list_runs_filtered,
            persist_run,
            diff_runs,
            attach_advisory,
            create_run_id,
            # Hashing
            sha256_of_obj,
            compute_feasibility_hash,
            # Migration
            migrate_v1_to_v2,
            migration_status,
        )
        from .runs_v2.api_runs import router as runs_router
    except ImportError:
        runs_router = None
else:
    # v1: Dataclass schemas, single-file storage (legacy)
    try:
        from .runs import (
            RunArtifact,
            RunAttachment,
            RunStatus,
            get_run,
            list_runs_filtered,
            persist_run,
            diff_runs,
        )
        from .runs.api_runs import router as runs_router
    except ImportError:
        runs_router = None

# Engines Registry
try:
    from .engines.registry import (
        EngineVersion,
        get_engine_version,
        register_engine,
    )
except ImportError:
    pass

# Gates Policy
try:
    from .gates.policy import (
        GatePolicy,
        ReplayGateResult,
        check_replay_gate,
    )
except ImportError:
    pass

# Re-export from existing modules for convenience
try:
    from .logging_ai import (
        new_run_id,
        log_ai_constraint_attempt,
        log_ai_constraint_run_summary,
    )
except ImportError:
    pass

try:
    from .schemas_logs_ai import (
        AiAttemptLogView,
        AiRunSummaryLogView,
        AiLogQueryParams,
    )
except ImportError:
    pass

try:
    from .ai_policy import (
        apply_global_policy_to_constraints,
        validate_request_against_policy,
        clamp_budget_to_policy,
    )
except ImportError:
    pass

__all__ = [
    # API Contracts
    "RiskBucket",
    "RmosContext",
    "RmosFeasibilityResult",
    "RmosBomResult",
    "RmosToolpathPlan",
    "RmosServices",
    "compute_feasibility_for_design",
    # AI Search Schemas (Phase B)
    "SearchStatus",
    "WorkflowMode",
    "SearchContext",
    "SearchBudget",
    "AiSearchRequest",
    "AiSearchResponse",
    "AiSearchSummary",
    "SearchAttemptSummary",
    # AI Search Engine (Phase B)
    "run_constraint_first_search",
    "get_search_status_description",
    # Constraint Profiles (Phase C)
    "RosetteGeneratorConstraints",
    "ProfileMetadata",
    "ConstraintProfile",
    "ProfileStore",
    "get_profile_store",
    "get_constraints_by_profile_id",
    "list_available_profiles",
    "default_constraints",
    "constraints_for_beginner",
    "constraints_for_advanced",
    # Profile History (Phase C)
    "ChangeType",
    "ProfileHistoryEntry",
    "ProfileHistoryStore",
    "get_profile_history_store",
    "record_profile_change",
    "get_profile_history",
    # Routers
    "ai_router",
    "profiles_router",
    "history_router",
    "rmos_router",
    "runs_router",
    # Runs Module (Phase D - v1/v2 conditional)
    "RunArtifact",
    "RunAttachment",
    "RunStatus",
    "get_run",
    "list_runs_filtered",
    "persist_run",
    "diff_runs",
    # v2-only exports (available when RMOS_RUNS_V2_ENABLED=true)
    "RunDecision",
    "Hashes",
    "RunOutputs",
    "AdvisoryInputRef",
    "attach_advisory",
    "create_run_id",
    "sha256_of_obj",
    "compute_feasibility_hash",
    "migrate_v1_to_v2",
    "migration_status",
    # Engines Registry
    "EngineVersion",
    "get_engine_version",
    "register_engine",
    # Gates Policy
    "GatePolicy",
    "ReplayGateResult",
    "check_replay_gate",
    # Logging (from existing)
    "new_run_id",
    "log_ai_constraint_attempt",
    "log_ai_constraint_run_summary",
    # Log View Schemas (from existing)
    "AiAttemptLogView",
    "AiRunSummaryLogView",
    "AiLogQueryParams",
    # Policy (from existing)
    "apply_global_policy_to_constraints",
    "validate_request_against_policy",
    "clamp_budget_to_policy",
]
