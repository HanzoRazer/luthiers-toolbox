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
