"""
Blueprint CAM DXF export lifecycle orchestration (Phase 3B).

Centralizes governed save boundaries for blueprint_cam routers. Validation-only:
does not mutate DXF output or attach provenance.
"""

from __future__ import annotations

from typing import Literal

from app.util.dxf_lifecycle_guard import (
    DxfLifecycleContext,
    assert_dxf_lifecycle_context,
)

ExportType = Literal["dxf-create-save", "dxf-read-modify-save"]


def dxf_version_from_doc(doc) -> str:
    """Return DXF version string from an ezdxf document."""
    return getattr(doc, "dxfversion", "AC1015") or "AC1015"


def assert_governed_blueprint_dxf_export(
    *,
    source_module: str,
    export_type: ExportType,
    dxf_version: str,
) -> None:
    """Assert LIFECYCLE_GOVERNED export context for blueprint_cam router paths."""
    assert_dxf_lifecycle_context(
        DxfLifecycleContext(
            source_module=source_module,
            export_type=export_type,
            dxf_version=dxf_version,
            lifecycle_status="LIFECYCLE_GOVERNED",
            runtime_callable="router_endpoint",
            authority_context="user_request",
            provenance_status="NO",
        )
    )


def governed_doc_saveas(
    doc,
    path: str,
    *,
    source_module: str,
    export_type: ExportType,
    dxf_version: str | None = None,
) -> None:
    """Governed save boundary: validate context, then doc.saveas(path)."""
    version = dxf_version or dxf_version_from_doc(doc)
    assert_governed_blueprint_dxf_export(
        source_module=source_module,
        export_type=export_type,
        dxf_version=version,
    )
    doc.saveas(path)
