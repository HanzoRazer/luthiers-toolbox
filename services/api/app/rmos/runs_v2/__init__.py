"""
RMOS Runs v2 - Governance-Compliant Implementation

This module provides date-partitioned, immutable run artifact storage
compliant with RUN_ARTIFACT_PERSISTENCE_CONTRACT_v1.md.

Key Features:
- Pydantic-based schemas with required field validation
- Date-partitioned storage: {YYYY-MM-DD}/{run_id}.json
- Immutable artifacts (write-once, never modified)
- Append-only advisory links
- Content-addressed attachments

Usage:
    # Import schemas
    from rmos.runs_v2 import RunArtifact, RunDecision, Hashes

    # Import store functions
    from rmos.runs_v2 import persist_run, get_run, list_runs_filtered

    # Import hashing utilities
    from rmos.runs_v2 import sha256_of_obj, compute_feasibility_hash

Feature Flag:
    Set RMOS_RUNS_V2_ENABLED=true to use this implementation.
    Default storage: services/api/data/runs/rmos
"""

from __future__ import annotations

# =============================================================================
# Schemas
# =============================================================================

from .schemas import (
    # Core models
    RunArtifact,
    RunDecision,
    Hashes,
    RunOutputs,
    RunAttachment,
    AdvisoryInputRef,
    # Type aliases
    RunStatus,
    ExplanationStatus,
    RiskLevel,
    # Utilities
    utc_now,
)

# Advisory variant rejection schemas
from .schemas_advisory_reject import (
    RejectReasonCode,
    RejectVariantRequest,
    AdvisoryVariantRejectionRecord,
)

# =============================================================================
# Store Operations
# =============================================================================

from .store import (
    # Class
    RunStoreV2,
    # Completeness guard (meta validation)
    CompletenessViolation,
    check_completeness,
    create_blocked_artifact_for_violations,
    validate_and_persist,
    # Module-level functions
    create_run_id,
    persist_run,
    get_run,
    list_runs_filtered,
    attach_advisory,
)

# =============================================================================
# Hashing Utilities
# =============================================================================

from .hashing import (
    stable_json_dumps,
    sha256_of_obj,
    sha256_of_text,
    sha256_of_text_safe,
    sha256_of_bytes,
    sha256_file,
    summarize_request,
    compute_feasibility_hash,
)

# =============================================================================
# Attachment Storage
# =============================================================================

from .attachments import (
    put_bytes_attachment,
    put_text_attachment,
    put_json_attachment,
    get_attachment_path,
    load_json_attachment,
    verify_attachment,
)

# =============================================================================
# Diff Engine
# =============================================================================

from .diff import (
    diff_runs,
    diff_summary,
    build_diff,
)

from .diff_attachments import (
    DIFF_PREVIEW_MAX_CHARS_DEFAULT,
    DiffAttachmentResult,
    persist_diff_as_attachment_if_needed,
)

# =============================================================================
# Compatibility Layer
# =============================================================================

from .compat import (
    convert_v1_to_v2,
    convert_v2_to_v1_dict,
    validate_v2_artifact,
)

# =============================================================================
# Migration Utilities
# =============================================================================

from .migration_utils import (
    MigrationReport,
    backup_v1_store,
    load_v1_store,
    migrate_v1_to_v2,
    verify_migration,
    rollback_migration,
    migration_status,
)

# =============================================================================
# Batch Tree Helpers (Option B foundation)
# =============================================================================

from .batch_tree import resolve_batch_root, list_batch_tree  # noqa: F401
from .batch_dashboard import build_batch_summary_dashboard_card  # noqa: F401

# =============================================================================
# Override Primitive (YELLOW unlock)
# =============================================================================

from .schemas_override import (
    OverrideRequest,
    OverrideRecord,
    OverrideMetaUpdate,
    OverrideResponse,
    OverrideScope,
)

from .override_service import (
    apply_override,
    get_override_info,
    is_overridden,
    validate_override_preconditions,
    # Errors
    OverrideError,
    RunNotFoundError,
    NotBlockedError,
    AlreadyOverriddenError,
    RedOverrideNotAllowedError,
    RiskMismatchError,
    AcknowledgmentRequiredError,
)

# =============================================================================
# API Router
# =============================================================================

from .api_runs import router


# =============================================================================
# CLI (for direct execution)
# =============================================================================

# Migration CLI available via:
#   python -m rmos.runs_v2.cli_migrate status
#   python -m rmos.runs_v2.cli_migrate migrate
#   python -m rmos.runs_v2.cli_migrate verify


# =============================================================================
# Public API
# =============================================================================

__all__ = [
    # Schemas
    "RunArtifact",
    # Advisory Rejection
    "RejectReasonCode",
    "RejectVariantRequest",
    "AdvisoryVariantRejectionRecord",
    "RunDecision",
    "Hashes",
    "RunOutputs",
    "RunAttachment",
    "AdvisoryInputRef",
    "RunStatus",
    "ExplanationStatus",
    "RiskLevel",
    "utc_now",
    # Store
    "RunStoreV2",
    "CompletenessViolation",
    "check_completeness",
    "create_blocked_artifact_for_violations",
    "validate_and_persist",
    "create_run_id",
    "persist_run",
    "get_run",
    "list_runs_filtered",
    "attach_advisory",
    # Hashing
    "stable_json_dumps",
    "sha256_of_obj",
    "sha256_of_text",
    "sha256_of_text_safe",
    "sha256_of_bytes",
    "sha256_file",
    "summarize_request",
    "compute_feasibility_hash",
    # Attachments
    "put_bytes_attachment",
    "put_text_attachment",
    "put_json_attachment",
    "get_attachment_path",
    "load_json_attachment",
    "verify_attachment",
    # Diff
    "diff_runs",
    "diff_summary",
    "build_diff",
    # Compat
    "convert_v1_to_v2",
    "convert_v2_to_v1_dict",
    "validate_v2_artifact",
    # Migration
    "MigrationReport",
    "backup_v1_store",
    "load_v1_store",
    "migrate_v1_to_v2",
    "verify_migration",
    "rollback_migration",
    "migration_status",
    # Override
    "OverrideRequest",
    "OverrideRecord",
    "OverrideMetaUpdate",
    "OverrideResponse",
    "OverrideScope",
    "apply_override",
    "get_override_info",
    "is_overridden",
    "validate_override_preconditions",
    "OverrideError",
    "RunNotFoundError",
    "NotBlockedError",
    "AlreadyOverriddenError",
    "RedOverrideNotAllowedError",
    "RiskMismatchError",
    "AcknowledgmentRequiredError",
    # Router
    "router",
]
