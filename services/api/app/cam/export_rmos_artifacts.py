"""
Export RMOS Artifact Adapter

CAM Dev Order 6F: RMOS-compatible artifact persistence for Export Objects.

This module persists export objects and lifecycle reports to content-addressed
storage without creating full RMOS run lifecycle entries.

Core rule:
  - Artifact persistence only, not run orchestration
  - No RunStoreV2 lifecycle coupling
  - No job lifecycle
  - No machine execution state
  - No DXF/G-code persistence

The run_id returned is a lightweight export provenance ID (RUN-EXPORT-{uuid}),
not a full RMOS run lifecycle record.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.rmos.runs_v2.attachments import put_json_attachment


# -----------------------------------------------------------------------------
# Models
# -----------------------------------------------------------------------------

class RMOSArtifactRef(BaseModel):
    """Reference to a persisted RMOS artifact."""
    kind: str = Field(..., description="Artifact kind")
    sha256: str = Field(..., description="Content hash")
    bytes: int = Field(..., description="Size in bytes")


class RMOSPersistenceResult(BaseModel):
    """Result of RMOS artifact persistence."""
    persisted: bool = Field(..., description="Whether artifacts were persisted")
    run_id: Optional[str] = Field(
        None,
        description="Lightweight export provenance ID (RUN-EXPORT-{uuid})"
    )
    artifacts: List[RMOSArtifactRef] = Field(
        default_factory=list,
        description="List of persisted artifact references"
    )


# -----------------------------------------------------------------------------
# Artifact Kind Constants
# -----------------------------------------------------------------------------

EXPORT_OBJECT_KIND = "export_object_json"
LIFECYCLE_REPORT_KIND = "export_lifecycle_report_json"


# -----------------------------------------------------------------------------
# Run ID Generation
# -----------------------------------------------------------------------------

def generate_export_run_id() -> str:
    """
    Generate a lightweight export provenance ID.

    Format: RUN-EXPORT-{uuid4}

    This is NOT a full RMOS run lifecycle record.
    It is a provenance identifier for export artifact tracking.
    """
    return f"RUN-EXPORT-{uuid.uuid4().hex}"


# -----------------------------------------------------------------------------
# Artifact Persistence
# -----------------------------------------------------------------------------

def persist_export_object_artifact(
    export_object: Dict[str, Any],
    run_id: str,
) -> RMOSArtifactRef:
    """
    Persist an export object as a content-addressed JSON artifact.

    Args:
        export_object: The export object dict (serialized from ExportObject)
        run_id: The export provenance ID

    Returns:
        Artifact reference with kind, sha256, and bytes
    """
    filename = f"export_object_{run_id}.json"

    attachment, _path, sha256 = put_json_attachment(
        obj=export_object,
        kind=EXPORT_OBJECT_KIND,
        filename=filename,
    )

    return RMOSArtifactRef(
        kind=EXPORT_OBJECT_KIND,
        sha256=sha256,
        bytes=attachment.size_bytes,
    )


def persist_lifecycle_report_artifact(
    lifecycle_report: Dict[str, Any],
    run_id: str,
) -> RMOSArtifactRef:
    """
    Persist a lifecycle report as a content-addressed JSON artifact.

    Args:
        lifecycle_report: The lifecycle report dict (serialized from report)
        run_id: The export provenance ID

    Returns:
        Artifact reference with kind, sha256, and bytes
    """
    filename = f"lifecycle_report_{run_id}.json"

    attachment, _path, sha256 = put_json_attachment(
        obj=lifecycle_report,
        kind=LIFECYCLE_REPORT_KIND,
        filename=filename,
    )

    return RMOSArtifactRef(
        kind=LIFECYCLE_REPORT_KIND,
        sha256=sha256,
        bytes=attachment.size_bytes,
    )


def persist_export_lifecycle_artifacts(
    export_object: Optional[Dict[str, Any]],
    lifecycle_report: Dict[str, Any],
) -> RMOSPersistenceResult:
    """
    Persist export lifecycle artifacts to RMOS content-addressed storage.

    Behavior:
      - Always persists lifecycle report
      - Only persists export object if provided (not None)
      - RED lifecycle with no export object: lifecycle report only

    Args:
        export_object: Export object dict, or None if not created
        lifecycle_report: Lifecycle report dict (always required)

    Returns:
        Persistence result with run_id and artifact references
    """
    run_id = generate_export_run_id()
    artifacts: List[RMOSArtifactRef] = []

    # Always persist lifecycle report
    report_ref = persist_lifecycle_report_artifact(lifecycle_report, run_id)
    artifacts.append(report_ref)

    # Persist export object only if created
    if export_object is not None:
        obj_ref = persist_export_object_artifact(export_object, run_id)
        artifacts.append(obj_ref)

    return RMOSPersistenceResult(
        persisted=True,
        run_id=run_id,
        artifacts=artifacts,
    )


def create_empty_persistence_result() -> RMOSPersistenceResult:
    """Create a result indicating no persistence occurred."""
    return RMOSPersistenceResult(
        persisted=False,
        run_id=None,
        artifacts=[],
    )


# -----------------------------------------------------------------------------
# Audit Ledger Persistence (6K)
# -----------------------------------------------------------------------------

AUDIT_LEDGER_KIND = "lifecycle_audit_ledger_json"


# -----------------------------------------------------------------------------
# Promotion Evidence Persistence (6M)
# -----------------------------------------------------------------------------

PROMOTION_EVIDENCE_KIND = "promotion_evidence_json"


def persist_promotion_evidence_artifact(
    evidence_bundle: Dict[str, Any],
    operation: str,
) -> RMOSArtifactRef:
    """
    Persist a promotion evidence bundle as a content-addressed JSON artifact.

    Args:
        evidence_bundle: The evidence bundle dict
        operation: Operation name (for filename)

    Returns:
        Artifact reference with kind, sha256, and bytes
    """
    evidence_id = evidence_bundle.get("evidence_id", "unknown")
    filename = f"promotion_evidence_{operation}_{evidence_id}.json"

    attachment, _path, sha256 = put_json_attachment(
        obj=evidence_bundle,
        kind=PROMOTION_EVIDENCE_KIND,
        filename=filename,
    )

    return RMOSArtifactRef(
        kind=PROMOTION_EVIDENCE_KIND,
        sha256=sha256,
        bytes=attachment.size_bytes,
    )


def persist_audit_ledger_artifact(
    audit_ledger: Dict[str, Any],
    run_id: str,
) -> RMOSArtifactRef:
    """
    Persist an audit ledger as a content-addressed JSON artifact.

    Args:
        audit_ledger: The audit ledger dict
        run_id: The export provenance ID

    Returns:
        Artifact reference with kind, sha256, and bytes
    """
    filename = f"audit_ledger_{run_id}.json"

    attachment, _path, sha256 = put_json_attachment(
        obj=audit_ledger,
        kind=AUDIT_LEDGER_KIND,
        filename=filename,
    )

    return RMOSArtifactRef(
        kind=AUDIT_LEDGER_KIND,
        sha256=sha256,
        bytes=attachment.size_bytes,
    )


# -----------------------------------------------------------------------------
# Audit Index (6K) — In-memory index of operation → [audit_ids]
# -----------------------------------------------------------------------------

import threading
from typing import Dict, List

# Thread-safe in-memory audit index
# Note: This is in-memory only for 6K. Persistent indexing is future work.
# For 6L promotion queries, this provides recent audit history.
_audit_index_lock = threading.Lock()
_audit_index: Dict[str, List[Dict[str, str]]] = {}


def register_audit_in_index(
    operation: str,
    audit_id: str,
    deterministic_hash: str,
    run_id: Optional[str] = None,
) -> None:
    """
    Register an audit entry in the in-memory operation index.

    Thread-safe index update.

    Note: This is in-memory only. Audit artifacts are persisted to RMOS
    when persist_to_rmos=True. The index provides fast lookup for 6L
    promotion queries during the current process lifetime.

    Args:
        operation: Operation type (e.g., 'nut_slot')
        audit_id: Audit identifier
        deterministic_hash: Governance state hash
        run_id: RMOS run ID (if persisted)
    """
    with _audit_index_lock:
        if operation not in _audit_index:
            _audit_index[operation] = []

        entry = {
            "audit_id": audit_id,
            "deterministic_hash": deterministic_hash,
        }
        if run_id:
            entry["run_id"] = run_id

        # Prepend (most recent first), limit to 100 entries per operation
        _audit_index[operation].insert(0, entry)
        _audit_index[operation] = _audit_index[operation][:100]


def get_audit_history(operation: str, limit: int = 10) -> List[Dict[str, str]]:
    """
    Get audit history for an operation from in-memory index.

    Args:
        operation: Operation type
        limit: Maximum number of entries to return

    Returns:
        List of audit references (most recent first)
    """
    with _audit_index_lock:
        entries = _audit_index.get(operation, [])
        return entries[:limit]


def get_all_audit_history() -> Dict[str, List[Dict[str, str]]]:
    """Get full in-memory audit index."""
    with _audit_index_lock:
        return dict(_audit_index)


def clear_audit_index() -> None:
    """Clear in-memory audit index (for testing)."""
    with _audit_index_lock:
        _audit_index.clear()
