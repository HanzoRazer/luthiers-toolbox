"""
IBG DXF export lifecycle (DO 79 / R2).

Fail-closed save boundary for IBG DxfWriter paths. Validation-only — does not
mutate DXF output or attach provenance to file bytes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from app.governance.provenance_attachment import (
    NON_EXPORTABLE_STATUSES,
    ProvenanceAttachmentDraft,
    ProvenanceAttachmentStatus,
    create_ibg_provenance_draft,
)
from app.util.dxf_lifecycle_guard import (
    DxfLifecycleContext,
    assert_dxf_lifecycle_context,
)

if TYPE_CHECKING:
    from app.cam.dxf_writer import DxfWriter

IBG_DXF_VERSION = "R12"


class IbgDxfExportBlockedError(Exception):
    """Raised when IBG DXF export is not authorized at the save boundary."""


def default_ibg_attachment_for_save(
    output_path: str,
    *,
    transformation_method: str,
    source_artifact_id: Optional[str] = None,
) -> ProvenanceAttachmentDraft:
    """Create a blocked IBG provenance draft for an export attempt."""
    artifact = source_artifact_id or output_path
    return create_ibg_provenance_draft(
        attachment_id=f"ibg-export:{artifact}",
        source_artifact_id=artifact,
        transformation_method=transformation_method,
    )


def _attachment_allows_export(attachment: ProvenanceAttachmentDraft) -> bool:
    if attachment.status in NON_EXPORTABLE_STATUSES:
        return False
    return attachment.is_exportable()


def assert_ibg_dxf_export_allowed(
    attachment: Optional[ProvenanceAttachmentDraft],
    *,
    source_module: str,
) -> DxfLifecycleContext:
    """
    Validate provenance and build lifecycle context for an IBG save.

    Raises:
        IbgDxfExportBlockedError: Missing attachment or non-exportable status.
    """
    if attachment is None:
        raise IbgDxfExportBlockedError(
            "IBG DXF export requires a provenance attachment at the save boundary"
        )

    if not _attachment_allows_export(attachment):
        reason = attachment.blocking_reason or (
            f"IBG export blocked: provenance status={attachment.status.value}"
        )
        raise IbgDxfExportBlockedError(reason)

    if attachment.status == ProvenanceAttachmentStatus.RATIFIED:
        return DxfLifecycleContext(
            source_module=source_module,
            export_type="dxf-create-save",
            dxf_version=IBG_DXF_VERSION,
            lifecycle_status="COMPAT_ONLY",
            runtime_callable="runtime_service",
            authority_context="pipeline_stage",
            provenance_status="YES",
        )

    return DxfLifecycleContext(
        source_module=source_module,
        export_type="dxf-create-save",
        dxf_version=IBG_DXF_VERSION,
        lifecycle_status="BLOCKED_PROVENANCE",
        runtime_callable="runtime_service",
        authority_context="pipeline_stage",
        provenance_status="BLOCKED",
    )


def governed_ibg_writer_saveas(
    writer: "DxfWriter",
    path: str,
    *,
    attachment: Optional[ProvenanceAttachmentDraft],
    source_module: str,
    transformation_method: Optional[str] = None,
) -> None:
    """Governed IBG save: provenance check, lifecycle assert, then writer.saveas."""
    if attachment is None and transformation_method:
        attachment = default_ibg_attachment_for_save(
            path,
            transformation_method=transformation_method,
            source_artifact_id=None,
        )

    context = assert_ibg_dxf_export_allowed(attachment, source_module=source_module)
    assert_dxf_lifecycle_context(context)
    writer.saveas(path)
