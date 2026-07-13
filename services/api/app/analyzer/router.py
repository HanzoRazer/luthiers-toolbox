"""
Analyzer API Router — Endpoints for acoustic interpretation.

These endpoints consume viewer_pack data and return interpretations.
They do NOT perform measurements — that's tap_tone_pi's job.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session

from ..auth.principal import Principal
from ..auth.deps import get_current_principal
from ..db.session import get_db
from ..schemas.instrument_project import DesignStateResponse
from ..projects.router import _get_project_or_404
from ..projects.service import (
    append_analyzer_observation,
    build_design_state_response,
)
from .schemas import (
    ViewerPackV1,
    InterpretationResult,
    SpectrumDisplayData,
    AppendObservationRequest,
)
from .project_observation import build_analyzer_observation
from .viewer_pack_loader import load_viewer_pack
from .spectrum_service import SpectrumService
from .modal_visualizer import ModalVisualizerService
from .design_advisor import DesignAdvisorService


router = APIRouter(
    prefix="/api/analyzer",
    tags=["analyzer"],
)

# Services
spectrum_service = SpectrumService()
modal_service = ModalVisualizerService()
advisor_service = DesignAdvisorService()


@router.post("/interpret", response_model=InterpretationResult)
async def interpret_viewer_pack(
    pack: ViewerPackV1,
    reference_id: Optional[str] = Query(
        None,
        description="Reference instrument ID for comparison (e.g., 'martin_d28_1937')"
    ),
) -> InterpretationResult:
    """
    Interpret a viewer_pack and return design recommendations.

    This is the main entry point for acoustic analysis.

    - **pack**: viewer_pack_v1 data from tap_tone_pi
    - **reference_id**: Optional reference instrument for comparison

    Returns interpretation with recommendations for the luthier.
    """
    return advisor_service.analyze(pack, reference_id)


@router.post("/interpret/upload", response_model=InterpretationResult)
async def interpret_uploaded_pack(
    file: UploadFile = File(...),
    reference_id: Optional[str] = Query(None),
) -> InterpretationResult:
    """
    Upload and interpret a viewer_pack file (JSON or ZIP).

    Accepts:
    - `.json` file containing viewer_pack_v1
    - `.zip` archive containing viewer_pack.json
    """
    try:
        pack = load_viewer_pack(file.file)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except (ValueError, KeyError, OSError) as e:  # WP-1: viewer pack parse
        raise HTTPException(
            status_code=400,
            detail=f"Failed to parse viewer pack: {e}"
        )

    return advisor_service.analyze(pack, reference_id)


@router.post(
    "/projects/{project_id}/observations",
    response_model=DesignStateResponse,
    summary="Append an advisory analyzer observation to a project (ADR-002)",
)
async def append_project_observation(
    project_id: str,
    body: AppendObservationRequest,
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
) -> DesignStateResponse:
    """
    Persist a completed interpretation as an advisory ``AnalyzerObservation`` on the
    project's canonical Layer-0 state (ADR-002 Instrument Project Graph) — the first
    Analyzer → Project-Spine adoption edge (SPINE-002 / LAB-021 WP-PS-3).

    Append-only by the explicit ``run_id`` (re-posting the same run is idempotent).
    ADVISORY ONLY: the write touches only ``analyzer_observations`` and confers no
    geometry, material, CAM, or RMOS/manufacturing authority. The interpretation's
    ``specimen_id`` / ``interpreted_at`` and the supplied ``run_id`` are required —
    missing identity is a 400, never fabricated.
    """
    project = _get_project_or_404(project_id, principal, db)
    try:
        observation = build_analyzer_observation(
            body.interpretation,
            body.run_id,
            wsi=body.wsi,
            interpretation_confidence=body.interpretation_confidence,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    new_state = append_analyzer_observation(project, [observation])
    db.commit()
    db.refresh(project)
    return build_design_state_response(project, new_state)


@router.post("/spectrum/display", response_model=SpectrumDisplayData)
async def get_spectrum_display(
    pack: ViewerPackV1,
    min_hz: float = Query(20.0, ge=0),
    max_hz: float = Query(2000.0, le=20000),
    include_coherence: bool = Query(True),
) -> SpectrumDisplayData:
    """
    Get spectrum data formatted for UI visualization.

    Returns frequencies, magnitudes, and peak markers ready for chart.js.
    """
    return spectrum_service.prepare_display_data(
        pack,
        frequency_range=(min_hz, max_hz),
        include_coherence=include_coherence,
    )


@router.post("/modes/visualize")
async def visualize_mode_shapes(
    pack: ViewerPackV1,
    mode_index: int = Query(0, ge=0, description="Which mode to visualize"),
    grid_resolution: int = Query(50, ge=10, le=200),
):
    """
    Get mode shape visualization data for a specific mode.

    Returns grid data, nodal lines, and pattern interpretation.
    """
    if mode_index >= len(pack.mode_shapes):
        raise HTTPException(
            status_code=400,
            detail=f"Mode index {mode_index} not found. Pack has {len(pack.mode_shapes)} modes."
        )

    mode = pack.mode_shapes[mode_index]
    return modal_service.prepare_shape_visualization(mode, grid_resolution)


@router.get("/references")
async def list_reference_instruments():
    """
    List available reference instruments for comparison.
    """
    return {
        "references": [
            {
                "id": ref_id,
                "name": ref["name"],
                "character": ref["character"],
            }
            for ref_id, ref in advisor_service.REFERENCE_LIBRARY.items()
        ]
    }


@router.get("/health")
async def analyzer_health():
    """Health check for analyzer module."""
    return {
        "status": "healthy",
        "module": "analyzer",
        "boundary": "interpretation_only",
        "input_contract": "viewer_pack_v1",
    }
