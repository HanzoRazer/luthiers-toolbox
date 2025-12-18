"""
RMOS Runs v2

Governance-compliant Pydantic/date-partitioned implementation.
Per: docs/governance/RUN_ARTIFACT_PERSISTENCE_CONTRACT_v1.md

GOVERNANCE:
- Required fields enforced (feasibility_sha256, risk_level)
- Immutable artifacts (no patch_meta)
- Date-partitioned storage
- Separate advisory link files
"""
from .schemas import (
    RunArtifact,
    RunDecision,
    RunOutputs,
    Hashes,
    AdvisoryInputRef,
    RunAttachment,
)
from .store import (
    RunStoreV2,
    ImmutabilityViolation,
    get_store,
    reset_store,
)
from .hashing import (
    sha256_text,
    sha256_json,
    sha256_bytes,
    sha256_file,
    verify_hash,
    summarize_request,
)
from .diff import diff_runs, summarize_diff
from .compat import convert_v1_to_v2, convert_v2_to_v1, validate_v1_record
from .api_runs import router

__all__ = [
    # Schemas
    "RunArtifact",
    "RunDecision",
    "RunOutputs",
    "Hashes",
    "AdvisoryInputRef",
    "RunAttachment",
    # Store
    "RunStoreV2",
    "ImmutabilityViolation",
    "get_store",
    "reset_store",
    # Hashing
    "sha256_text",
    "sha256_json",
    "sha256_bytes",
    "sha256_file",
    "verify_hash",
    "summarize_request",
    # Diff
    "diff_runs",
    "summarize_diff",
    # Compat
    "convert_v1_to_v2",
    "convert_v2_to_v1",
    "validate_v1_record",
    # Router
    "router",
]
