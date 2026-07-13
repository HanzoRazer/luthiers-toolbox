# services/api/app/cam/routers/project_execution.py
"""
Project Spine -> CAM execution router (SPINE-003).

One additive, owner-authenticated endpoint that drives the EXISTING governed adaptive-
clearing CAM operation from validated canonical project state (ADR-002), instead of
requiring the caller to hand-assemble the geometry payload:

    POST /api/cam/projects/{project_id}/adaptive-plan

This is the first Project Spine -> CAM adoption edge. It introduces NO new execution
model: geometry is translated once (``cam.project_adapter``) into the existing ``PlanIn``
and executed through the existing ``adaptive.plan`` router function, which owns feasibility
enforcement (HTTP 409 on block) and RMOS run persistence. CAM keeps computational
authority; RMOS keeps manufacturing authority.

The path is read-only against project state: it never mutates the project, its
manufacturing status, or any authority, and loading a project confers no execution
approval and bypasses no feasibility/safety policy.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ...auth.deps import get_current_principal
from ...auth.principal import Principal
from ...db.session import get_db
from ...projects.router import _get_project_or_404
from ...projects.service import load_project_for_cam
from ...routers.adaptive.plan_router import plan as adaptive_plan
from ...schemas.adaptive_schemas import PlanOut
from ..project_adapter import build_cam_request_from_project

router = APIRouter()


class ProjectAdaptivePlanRequest(BaseModel):
    """
    Machining parameters for a project-driven adaptive-clearing plan.

    Geometry is NOT accepted here — the outer boundary is derived from the project's
    canonical ``body_outline_mm``. These are the operation-level (non-design) parameters.
    ``tool_d`` is required; any omitted optional field keeps its ``PlanIn`` default (the
    single source of truth for defaults). Fields left unset are not forwarded.
    """
    tool_d: float = Field(..., gt=0, le=50, description="Tool diameter in mm (0.5-50).")
    units: Optional[str] = Field(default=None, description="Unit system ('mm' or 'inch').")
    stepover: Optional[float] = Field(default=None, gt=0, le=1, description="Radial stepover as fraction of tool_d.")
    stepdown: Optional[float] = Field(default=None, gt=0, description="Axial depth per pass (mm).")
    margin: Optional[float] = Field(default=None, ge=0, description="Clearance from boundary (mm).")
    strategy: Optional[str] = Field(default=None, description="Toolpath strategy ('Spiral' or 'Lanes').")
    smoothing: Optional[float] = Field(default=None, ge=0, description="Arc tolerance for rounded joins (mm).")
    climb: Optional[bool] = Field(default=None, description="Climb milling (True) vs conventional (False).")
    feed_xy: Optional[float] = Field(default=None, gt=0, description="Cutting feed rate (mm/min).")
    safe_z: Optional[float] = Field(default=None, description="Retract height above work (mm).")
    z_rough: Optional[float] = Field(default=None, description="Cutting depth (mm, typically negative).")


@router.post(
    "/{project_id}/adaptive-plan",
    response_model=PlanOut,
    tags=["CAM", "Project Spine"],
    summary="Run the governed adaptive-clearing plan from validated project state (ADR-002)",
)
def project_adaptive_plan(
    project_id: str,
    body: ProjectAdaptivePlanRequest,
    response: Response,
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
) -> PlanOut:
    """
    Derive the adaptive-clearing request from the project's canonical body outline and
    execute it through the existing governed CAM/RMOS path.

    Read-only against project state. Project identity/revision and the RMOS run id are
    returned as ``X-Project-Id`` / ``X-Project-Revision`` / ``X-Run-Id`` response headers
    (the response body remains the existing ``PlanOut`` shape). Missing/invalid project
    inputs are a 422; feasibility blocks surface as the existing 409 from ``adaptive.plan``.
    """
    project = _get_project_or_404(project_id, principal, db)

    try:
        project_data = load_project_for_cam(project)
        overrides = body.model_dump(exclude_unset=True, exclude={"tool_d"})
        plan_in = build_cam_request_from_project(
            project_data, tool_d=body.tool_d, overrides=overrides
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    # Existing governed execution: feasibility gate (409) + RMOS run persistence live here.
    result = adaptive_plan(plan_in)

    # Provenance (headers only — no CAM/RMOS/project schema change).
    response.headers["X-Project-Id"] = str(project.id)
    updated_at = getattr(project, "updated_at", None)
    if updated_at is not None:
        response.headers["X-Project-Revision"] = updated_at.isoformat()
    run_id = result.get("_run_id") if isinstance(result, dict) else None
    if run_id:
        response.headers["X-Run-Id"] = str(run_id)

    return result
