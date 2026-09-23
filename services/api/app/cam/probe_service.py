"""Governed probe downloads. Authority is supplied by the caller."""

from __future__ import annotations

from collections.abc import Mapping

from fastapi.responses import Response

from ..rmos.manufacturing_output_authority import (
    ManufacturingAuthorityContext,
    persist_authorized_manufacturing_output,
    require_manufacturing_output_authority,
)


def require_probe_manufacturing_authority(
    *,
    tool_id: str,
    event_type: str,
    request_summary: Mapping[str, Any],
) -> ManufacturingAuthorityContext:
    """Probe-family entry to the shared authority service. Mode is probing."""
    return require_manufacturing_output_authority(
        tool_id=tool_id,
        mode="probing",
        event_type=event_type,
        request_summary=request_summary,
    )


def create_governed_probe_response(
    gcode: str,
    *,
    filename: str,
    authority_context: ManufacturingAuthorityContext,
) -> Response:
    """Persist and attach a program that authority already permitted.

    This helper cannot evaluate feasibility or choose a risk level. Calling it
    without an authority context is a type error, not a GREEN default.
    """
    gcode_hash = persist_authorized_manufacturing_output(
        context=authority_context,
        gcode_text=gcode,
    )
    response = Response(
        content=gcode,
        media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
    response.headers["X-Run-ID"] = authority_context.run_id
    response.headers["X-GCode-SHA256"] = gcode_hash
    response.headers["X-ToolBox-Lane"] = "governed"
    return response
