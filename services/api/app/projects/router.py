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
from pydantic import BaseModel, Field
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
from .model_seeding import create_design_state_from_model_id
from .service import (
    ProjectStateUninitializedError,
    apply_design_state_to_project,
    build_design_state_response,
    create_default_design_state,
    lock_project_row_for_update,
    merge_analyzer_observations,
    parse_design_state,
    serialize_design_state,
)
from .project_artifact_service import (
    ArtifactAssociationConflictError,
    ArtifactNotFoundError,
    ArtifactProvenanceMismatchError,
    associate_artifact_with_project,
    merge_artifact_refs,
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
    model_id: Optional[str] = None  # GEN-1: e.g., "stratocaster", "les_paul", "dreadnought"
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
    """Create project, seed default InstrumentProjectData, persist.
    
    GEN-1: If model_id is provided (e.g., "stratocaster"), seed from model spec.
    """
    design_state = body.initial_state
    
    # GEN-1: Try model_id first for model-accurate defaults
    if design_state is None and body.model_id:
        design_state = create_design_state_from_model_id(body.model_id)
    
    # Fall back to generic defaults
    if design_state is None:
        design_state = create_default_design_state(
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

    # Serialize the read-modify-write of Project.data against concurrent writers
    # (this endpoint and the analyzer observation edge both rewrite the whole blob).
    lock_project_row_for_update(db, project)
    existing_state = parse_design_state(project.data)
    if existing_state and existing_state.analyzer_observations:
        # Append-only by run_id — canonical single implementation in the service, so
        # this writer and the Analyzer enrichment edge (SPINE-002) behave identically.
        merged = merge_analyzer_observations(existing_state, new_state.analyzer_observations)
        new_state = new_state.model_copy(update={"analyzer_observations": merged})
    if existing_state and existing_state.manufacturing_artifacts:
        # Append-only by run_id — same canonical merge as the artifact association edge
        # (SPINE-004), so a full-state PUT cannot drop existing artifact associations.
        merged_artifacts = merge_artifact_refs(existing_state, new_state.manufacturing_artifacts)
        new_state = new_state.model_copy(update={"manufacturing_artifacts": merged_artifacts})

    apply_design_state_to_project(project, new_state)
    db.commit()
    db.refresh(project)
    return build_design_state_response(project, new_state)


class AssociateArtifactRequest(BaseModel):
    """Associate an existing RMOS manufacturing run artifact with this project.

    Only ``run_id`` is required — every provenance field of the recorded reference is read
    from the actual persisted artifact, never from the caller. The optional ``expected_*``
    fields let a caller assert which artifact it means; a mismatch is rejected (422)."""
    run_id: str = Field(..., description="RMOS run id of the artifact to associate.")
    expected_tool_id: Optional[str] = Field(
        default=None, description="If set, must match the artifact's tool_id or the request is rejected."
    )
    expected_feasibility_sha256: Optional[str] = Field(
        default=None, description="If set, must match the artifact's feasibility hash or the request is rejected."
    )


@router.post("/{project_id}/artifacts", response_model=DesignStateResponse,
             summary="Associate an RMOS manufacturing artifact with a project (ADR-002)")
def associate_project_artifact(
    project_id: str,
    body: AssociateArtifactRequest,
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
) -> DesignStateResponse:
    """
    Record a reference to an existing RMOS manufacturing run artifact on the project's
    canonical engineering record — the first Project ↔ Manufacturing-artifact edge
    (SPINE-004). Append-only + idempotent by ``run_id``.

    Association only: RMOS keeps sole ownership of the artifact payload and CAM keeps sole
    ownership of planning; the project stores a reference (built from the real artifact),
    never a copy. Read-only against the artifact; no authority promoted. A missing artifact
    is 404; a provenance mismatch or an uninitialized project (no state, no instrument_type)
    is 422; a genuine provenance conflict on an existing run_id is 409.
    """
    project = _get_project_or_404(project_id, principal, db)

    # Serialize the read-modify-write of Project.data against concurrent writers.
    lock_project_row_for_update(db, project)
    try:
        new_state = associate_artifact_with_project(
            project,
            body.run_id,
            expected_tool_id=body.expected_tool_id,
            expected_feasibility_sha256=body.expected_feasibility_sha256,
        )
    except ArtifactNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ArtifactAssociationConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except (ArtifactProvenanceMismatchError, ProjectStateUninitializedError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc))

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
