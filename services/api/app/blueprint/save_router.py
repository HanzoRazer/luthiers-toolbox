# services/api/app/blueprint/save_router.py
"""
Blueprint → Project State Router (BLUE-002/003) — DB session wired

POST /api/blueprint/save-to-project/{project_id}

Maps Blueprint Lab pipeline outputs to BlueprintDerivedGeometry
and writes into InstrumentProjectData.blueprint_geometry.

See docs/PLATFORM_ARCHITECTURE.md — Layer 2 / Blueprint.
"""
from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..auth.principal import Principal
from ..auth.deps import get_current_principal
from ..db.session import get_db
from ..db.models.project import Project
from ..schemas.instrument_project import (
    BlueprintDerivedGeometry,
    BlueprintSource,
    InstrumentCategory,
    InstrumentProjectData,
)
from ..projects.service import (
    apply_design_state_to_project,
    build_design_state_response,
    parse_design_state,
)
from .project_writer import (
    apply_manual_override,
    build_blueprint_derived_geometry,
)

router = APIRouter(prefix="/api/blueprint", tags=["Blueprint", "Layer2"])


class SaveBlueprintToProjectRequest(BaseModel):
    analysis_result: Optional[Dict[str, Any]] = None
    calibration_result: Optional[Dict[str, Any]] = None
    dimension_result: Optional[Dict[str, Any]] = None
    phase3_body_size_mm: Optional[Dict[str, float]] = None
    phase4_linked_dimensions: Optional[List[Dict[str, Any]]] = None
    body_outline_mm: Optional[List[Tuple[float, float]]] = None
    source: str = Field(default="photo", description="'photo' | 'dxf' | 'manual'")
    instrument_type_override: Optional[str] = None
    commit_message: Optional[str] = None


class SaveBlueprintResponse(BaseModel):
    success: bool
    project_id: str
    blueprint_geometry_saved: bool
    instrument_classification: Optional[str]
    centerline_detected: bool
    scale_detected: bool
    confidence: float
    notes: List[str]
    message: str


@router.post(
    "/save-to-project/{project_id}",
    response_model=SaveBlueprintResponse,
    status_code=status.HTTP_200_OK,
    summary="Save Blueprint pipeline results into Instrument Project Graph",
)
def save_blueprint_to_project(
    project_id: str,
    body: SaveBlueprintToProjectRequest,
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
) -> SaveBlueprintResponse:
    """
    Save Blueprint Reader pipeline outputs into InstrumentProjectData.

    Called by Blueprint Lab after all available pipeline phases complete.
    Writes BlueprintDerivedGeometry into project.blueprint_geometry.
    If instrument_type_override or AI classification is present, updates
    InstrumentProjectData.instrument_type as well.

    Exit criteria (BLUE-002/003):
    ✅ Import blueprint → save → reload → blueprint geometry persists
    ✅ source, confidence, provenance retained
    ✅ instrument_type updated when classification detected or override given
    """
    # Fetch and authorise
    try:
        pid = uuid.UUID(project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid project_id '{project_id}'.")

    project: Optional[Project] = db.get(Project, pid)
    if project is None or project.archived_at is not None:
        raise HTTPException(status_code=404, detail="Project not found.")
    if str(project.owner_id) != str(principal.user_id):
        raise HTTPException(status_code=403, detail="Access denied.")

    # Parse source
    source_map = {
        "photo": BlueprintSource.PHOTO,
        "dxf": BlueprintSource.DXF,
        "manual": BlueprintSource.MANUAL,
    }
    source = source_map.get(body.source, BlueprintSource.PHOTO)

    # Build BlueprintDerivedGeometry from pipeline outputs
    geometry = build_blueprint_derived_geometry(
        analysis_result=body.analysis_result,
        calibration_result=body.calibration_result,
        dimension_result=body.dimension_result,
        phase3_body_size_mm=body.phase3_body_size_mm,
        phase4_linked_dimensions=body.phase4_linked_dimensions,
        body_outline_mm=body.body_outline_mm,
        source=source,
    )

    # Load existing project state (or start fresh)
    existing_state = parse_design_state(project.data) or InstrumentProjectData(
        instrument_type=InstrumentCategory(project.instrument_type or "custom")
    )

    # Resolve instrument type: explicit override > AI classification > existing
    instrument_type = existing_state.instrument_type
    if body.instrument_type_override:
        try:
            instrument_type = InstrumentCategory(body.instrument_type_override)
        except ValueError:
            pass  # ignore unknown values, keep existing
    elif geometry.instrument_classification:
        try:
            instrument_type = InstrumentCategory(geometry.instrument_classification)
        except ValueError:
            pass

    updated_state = existing_state.model_copy(update={
        "instrument_type": instrument_type,
        "blueprint_geometry": geometry,
    })

    apply_design_state_to_project(project, updated_state)
    db.commit()

    return SaveBlueprintResponse(
        success=True,
        project_id=project_id,
        blueprint_geometry_saved=True,
        instrument_classification=geometry.instrument_classification,
        centerline_detected=geometry.centerline_x_mm is not None,
        scale_detected=geometry.scale_length_detected_mm is not None,
        confidence=geometry.confidence,
        notes=geometry.notes,
        message="Blueprint geometry saved to project.",
    )
