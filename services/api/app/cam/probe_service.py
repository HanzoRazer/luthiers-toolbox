# services/api/app/cam/probe_service.py
"""Probe pattern service - extracts common governed workflow logic."""

from datetime import datetime, timezone
from typing import Any, Dict

from fastapi.responses import Response

from ..rmos.runs import (
    RunArtifact, persist_run, create_run_id, sha256_of_obj, sha256_of_text,
)


def create_governed_probe_response(
    gcode: str,
    body: Any,
    tool_id: str,
    event_type: str,
    filename: str,
) -> Response:
    """Create a governed probe G-code download response with RMOS persistence."""
    now = datetime.now(timezone.utc).isoformat()
    request_hash = sha256_of_obj(body.model_dump(mode="json"))
    gcode_hash = sha256_of_text(gcode)

    run_id = create_run_id()
    artifact = RunArtifact(
        run_id=run_id,
        created_at_utc=now,
        tool_id=tool_id,
        workflow_mode="probing",
        event_type=event_type,
        status="OK",
        request_hash=request_hash,
        gcode_hash=gcode_hash,
    )
    persist_run(artifact)

    resp = Response(
        content=gcode,
        media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
    resp.headers["X-Run-ID"] = run_id
    resp.headers["X-GCode-SHA256"] = gcode_hash
    resp.headers["X-ToolBox-Lane"] = "governed"
    return resp
