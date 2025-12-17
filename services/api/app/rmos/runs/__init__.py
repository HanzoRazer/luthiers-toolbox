"""
RMOS Runs Package - Immutable Run Artifact Storage

This package provides:
- RunArtifact schema for audit-grade tracking
- Content-addressed attachment storage
- Run diffing for comparison
- Deterministic hashing
- FastAPI routes for run access
"""

from .schemas import RunArtifact, RunAttachment, RunStatus
from .store import (
    get_run,
    list_runs_filtered,
    persist_run,
    get_store_path,
)
from .hashing import (
    compute_request_hash,
    compute_canonical_hash,
)
from .attachments import (
    store_attachment,
    get_attachment_path,
    verify_attachment,
    list_attachments,
)
from .diff import diff_runs
from .api_runs import router

__all__ = [
    # Schemas
    "RunArtifact",
    "RunAttachment",
    "RunStatus",
    # Store
    "get_run",
    "list_runs_filtered",
    "persist_run",
    "get_store_path",
    # Hashing
    "compute_request_hash",
    "compute_canonical_hash",
    # Attachments
    "store_attachment",
    "get_attachment_path",
    "verify_attachment",
    "list_attachments",
    # Diff
    "diff_runs",
    # Router
    "router",
]
