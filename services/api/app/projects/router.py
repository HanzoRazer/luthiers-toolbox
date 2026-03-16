# services/api/app/projects/router.py
"""
Project State Router (PROJ-003) — DB session wired

Endpoints:
    POST /api/projects                             — create project
    GET  /api/projects                             — list user projects
    GET  /api/projects/{project_id}/design-state   — read typed project data
    PUT  /api/projects/{project_id}/design-state   — write typed project data
    GET  /api/projects/{project_id}                — project metadata

See docs/PLATFORM_ARCHITECTURE.md — Layer 0.
"""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..auth.principal import Principal
from ..auth.deps import get_current_principal
from ..db.session import get_db
from ..db.models.project import Project
from ..schemas.instrument_project import (
    DesignStateResponse,
    DesignStatePutRequest,
    InstrumentProjectData,
)
from .service import (
    apply_design_state_to_project,
    build_design_state_response,
    create_default_design_state,
    parse_design_state,
    serialize_design_state,
)

router = APIRouter(prefix="/api/projects", tags=["Projects", "Layer0"])


def _get_project_or_404(project_id: str, principal: Principal, db: Session) -> Project:
    try:
        pid = uuid.UUID(project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid project_id: '{project_id}'.")

    project: Optional[Project] = db.get(Project, pid)

    if project is None or project.archived_at is not None:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")

    if str(project.owner_id) != str(principal.user_id):
        raise HTTPException(status_code=403, detail="Access denied.")

    return project


class CreateProjectRequest(BaseModel):
    name: str
    instrument_type: str = "acoustic_guitar"
    scale_length_mm: Optional[float] = None
    description: Optional[str] = None
    initial_state: Optional[InstrumentProjectData] = None


class ProjectSummaryResponse(BaseModel):
    project_id: str
    name: str
    instrument_type: Optional[str]
    has_design_state: bool
    is_cam_ready: bool
    created_at: str
    updated_at: str


@router.post("", response_model=ProjectSummaryResponse, status_code=201,
             summary="Create a new instrument project")
def create_project(
    body: CreateProjectRequest,
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
) -> ProjectSummaryResponse:
    """Create project, seed default InstrumentProjectData, persist."""
    design_state = body.initial_state or create_default_design_state(
        instrument_type=body.instrument_type,
        scale_length_mm=body.scale_length_mm,
    )
    project = Project(
        owner_id=uuid.UUID(str(principal.user_id)),
        name=body.name,
        description=body.description,
        instrument_type=design_state.instrument_type.value,
        data=serialize_design_state(design_state),
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return ProjectSummaryResponse(
        project_id=str(project.id),
        name=project.name,
        instrument_type=project.instrument_type,
        has_design_state=True,
        is_cam_ready=design_state.is_ready_for_cam(),
        created_at=project.created_at.isoformat(),
        updated_at=project.updated_at.isoformat(),
    )


@router.get("", response_model=list[ProjectSummaryResponse],
            summary="List all projects for current user")
def list_projects(
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
) -> list[ProjectSummaryResponse]:
    """Return non-archived projects sorted by most recently edited."""
    projects = (
        db.query(Project)
        .filter(
            Project.owner_id == uuid.UUID(str(principal.user_id)),
            Project.archived_at.is_(None),
        )
        .order_by(Project.updated_at.desc())
        .all()
    )
    results = []
    for p in projects:
        ds = parse_design_state(p.data)
        results.append(ProjectSummaryResponse(
            project_id=str(p.id),
            name=p.name,
            instrument_type=p.instrument_type,
            has_design_state=ds is not None,
            is_cam_ready=ds.is_ready_for_cam() if ds else False,
            created_at=p.created_at.isoformat(),
            updated_at=p.updated_at.isoformat(),
        ))
    return results


@router.get("/{project_id}/design-state", response_model=DesignStateResponse,
            summary="Get typed instrument project design state")
def get_design_state(
    project_id: str,
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
) -> DesignStateResponse:
    """Layer 0 read endpoint — all workspaces load project state here."""
    project = _get_project_or_404(project_id, principal, db)
    design_state = parse_design_state(project.data)
    return build_design_state_response(project, design_state)


@router.put("/{project_id}/design-state", response_model=DesignStateResponse,
            summary="Update instrument project design state")
def put_design_state(
    project_id: str,
    body: DesignStatePutRequest,
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
) -> DesignStateResponse:
    """
    Layer 0 write endpoint. Called on explicit user confirmation only.
    analyzer_observations are append-only by run_id to prevent data loss.
    """
    project = _get_project_or_404(project_id, principal, db)
    new_state = body.design_state

    existing_state = parse_design_state(project.data)
    if existing_state and existing_state.analyzer_observations:
        existing_ids = {obs.run_id for obs in existing_state.analyzer_observations}
        merged = existing_state.analyzer_observations + [
            obs for obs in new_state.analyzer_observations
            if obs.run_id not in existing_ids
        ]
        new_state = new_state.model_copy(update={"analyzer_observations": merged})

    apply_design_state_to_project(project, new_state)
    db.commit()
    db.refresh(project)
    return build_design_state_response(project, new_state)


@router.get("/{project_id}", response_model=ProjectSummaryResponse,
            summary="Get project metadata without full design state")
def get_project_summary(
    project_id: str,
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
) -> ProjectSummaryResponse:
    """Lightweight metadata — faster than /design-state for list views."""
    project = _get_project_or_404(project_id, principal, db)
    design_state = parse_design_state(project.data)
    return ProjectSummaryResponse(
        project_id=str(project.id),
        name=project.name,
        instrument_type=project.instrument_type,
        has_design_state=design_state is not None,
        is_cam_ready=design_state.is_ready_for_cam() if design_state else False,
        created_at=project.created_at.isoformat(),
        updated_at=project.updated_at.isoformat(),
    )
