from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query
from starlette.responses import Response

from .audit_export import AuditExportPorts, build_batch_audit_zip


router = APIRouter(prefix="/runs", tags=["runs"])


def _ports() -> AuditExportPorts:
    """
    Real adapters to repo store + attachments.
    """
    from . import store as runs_store
    from . import attachments as runs_attachments

    # list_attachments already exists via api_runs; use underlying implementation if present.
    list_attachments = getattr(runs_store, "list_attachments", None) or getattr(runs_attachments, "list_attachments", None)
    if list_attachments is None:
        # Fallback: the API layer may expose it; keep strict to avoid silent export gaps.
        raise RuntimeError("No list_attachments() found in runs_v2 store/attachments")

    # Get bytes: prefer attachments.get_bytes-like function if present
    get_bytes = (
        getattr(runs_attachments, "get_bytes_attachment", None)
        or getattr(runs_attachments, "get_attachment_bytes", None)
        or getattr(runs_store, "get_attachment_bytes", None)
    )
    if get_bytes is None:
        raise RuntimeError("No get_attachment_bytes()/get_bytes_attachment() found for runs_v2 attachments")

    return AuditExportPorts(
        list_runs_filtered=runs_store.list_runs_filtered,
        get_run=runs_store.get_run,
        list_attachments=list_attachments,
        get_attachment_bytes=get_bytes,
    )


@router.get("/batch-audit-export")
def batch_audit_export(
    session_id: str = Query(...),
    batch_label: str = Query(...),
    tool_kind: Optional[str] = Query(None),
    include_attachments: bool = Query(True),
):
    """
    Option B micro-step: export a single batch as a ZIP (manifest + artifacts + attachments).

    Returns application/zip bytes (download).
    """
    ports = _ports()
    zip_bytes, manifest = build_batch_audit_zip(
        ports,
        session_id=session_id,
        batch_label=batch_label,
        tool_kind=tool_kind,
        include_attachments=include_attachments,
    )
    filename = f"audit_{session_id}__{batch_label}.zip"
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
