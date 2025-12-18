"""
RMOS Runs Package - Immutable Run Artifact Storage

This package provides:
- RunArtifact schema for audit-grade tracking
- Content-addressed attachment storage
- Run diffing for comparison
- Deterministic hashing
- FastAPI routes for run access
"""

from .schemas import (
    RunArtifact,
    RunAttachment,
    RunStatus,
    # NEW from Gap Analysis
    RunDecision,
    AdvisoryInputRef,
    ExplanationStatus,
)
from .store import (
    get_run,
    list_runs_filtered,
    persist_run,
    create_run_id,
    # NEW from Gap Analysis
    patch_run_meta,
)
from .hashing import (
    sha256_of_obj,
    sha256_of_text,
    sha256_of_bytes,
    stable_json_dumps,
    sha256_file,
    # NEW from Gap Analysis
    sha256_of_text_safe,
    summarize_request,
)
from .attachments import (
    put_text_attachment,
    put_json_attachment,
    get_attachment_path,
    load_json_attachment,
)
from .diff import diff_runs
from .api_runs import router

__all__ = [
    # Schemas
    "RunArtifact",
    "RunAttachment",
    "RunStatus",
    "RunDecision",
    "AdvisoryInputRef",
    "ExplanationStatus",
    # Store
    "get_run",
    "list_runs_filtered",
    "persist_run",
    "create_run_id",
    "patch_run_meta",
    # Hashing
    "sha256_of_obj",
    "sha256_of_text",
    "sha256_of_bytes",
    "sha256_file",
    "sha256_of_text_safe",
    "summarize_request",
    "stable_json_dumps",
    # Attachments
    "put_text_attachment",
    "put_json_attachment",
    "get_attachment_path",
    "load_json_attachment",
    # Diff
    "diff_runs",
    # Router
    "router",
]
