"""Shared plumbing for the project-driven guitar G-code routers.

These helpers are used by both the body and neck manufacturing routes. They live
here rather than in either router so that neither imports the other: a neck route
must not depend on a body router.
"""

from __future__ import annotations

import io
from datetime import datetime, timezone

from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ....cam.generator_readiness import (
    GeneratorReadinessBlocked,
    require_generator_readiness,
)
from ....auth.principal import Principal
from ....db.models.project import Project
from ....projects.service import parse_design_state
from ....schemas.instrument_project import InstrumentProjectData


def _readiness_gate(route_key: str) -> None:
    """Refuse unless generator readiness permits emission for this route.

    Passing is not an authorization: asset authority may still refuse downstream.
    """
    try:
        require_generator_readiness(route_key)
    except GeneratorReadinessBlocked as exc:
        raise HTTPException(status_code=422, detail=exc.as_detail())


def _get_project_or_404(project_id: str, principal: Principal, db: Session) -> Project:
    """Load project from DB, validate ownership."""
    try:
        pid = uuid.UUID(project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid project_id: '{project_id}'")

    project: Optional[Project] = db.get(Project, pid)

    if project is None or project.archived_at is not None:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")

    if str(project.owner_id) != str(principal.user_id):
        raise HTTPException(status_code=403, detail="Access denied.")

    return project


def _parse_design_state_or_422(project: Project) -> InstrumentProjectData:
    """Parse design state, return 422 if DRAFT or missing."""
    design_state = parse_design_state(project.data)

    if design_state is None:
        raise HTTPException(
            status_code=422,
            detail="Project has no design state. Use PUT /api/projects/{id}/design-state first."
        )

    # Check CAM-ready status
    if not design_state.manufacturing_state:
        raise HTTPException(
            status_code=422,
            detail=(
                "Project has no manufacturing_state. "
                "Set manufacturing_state.status to 'design_complete' before generating CAM output. "
                "Use PUT /api/projects/{id}/design-state to update."
            )
        )

    status_value = design_state.manufacturing_state.status.value
    if status_value == "draft":
        raise HTTPException(
            status_code=422,
            detail=(
                "Project is DRAFT. Cannot generate CAM output for draft projects. "
                "Advance to DESIGN_COMPLETE first. "
                "Use PUT /api/projects/{id}/design-state to set manufacturing_state.status='design_complete'."
            )
        )

    return design_state


def _make_nc_response(gcode: str, filename: str) -> StreamingResponse:
    """Create StreamingResponse with .nc file download."""
    buffer = io.BytesIO(gcode.encode("utf-8"))
    return StreamingResponse(
        buffer,
        media_type="text/plain",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Line-Count": str(len(gcode.splitlines())),
        }
    )


def _generate_timestamp() -> str:
    """Generate timestamp for filenames."""
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
