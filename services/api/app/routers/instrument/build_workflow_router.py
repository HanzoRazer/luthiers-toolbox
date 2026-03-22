"""
Build Workflow Router (DECOMP-001)
==================================

Endpoints for build process calculations:
- Setup cascade evaluation
- Neck and tail block dimensions
- Build sequence orchestration
- Voicing history and tap tone analysis

Split from instrument_geometry_router.py per BACKLOG.md DECOMP-001.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.calculators.setup_cascade import (
    SetupState,
    evaluate_setup,
    suggest_adjustments,
)
from app.calculators.neck_block_calc import (
    compute_both_blocks,
    list_body_styles as list_block_body_styles,
)
from app.calculators.voicing_history_calc import (
    TapToneMeasurement,
    VoicingSession,
    analyze_voicing_progress,
    predict_final_frequency,
    get_target_frequencies,
    list_build_stages,
)
from app.calculators.build_sequence import (
    InstrumentType,
    BodyStyle,
    NeckJointType,
    create_dreadnought_spec,
    create_om_spec,
    create_classical_spec,
    run_build_sequence,
)

router = APIRouter(
    prefix="",  # Manifest adds /api/instrument prefix
    tags=["build-workflow"],
)


# ─── Setup Cascade Models (CONSTRUCTION-002) ──────────────────────────────────

class SetupStateRequest(BaseModel):
    """Request body for setup cascade evaluation."""
    neck_angle_deg: float = Field(default=1.5, description="Neck angle (degrees)")
    truss_rod_relief_mm: float = Field(default=0.25, description="Relief at 7th fret (mm)")
    nut_slot_depths_mm: Optional[Dict[str, float]] = Field(default_factory=dict)
    action_at_nut_mm: float = Field(default=0.5, description="High E at nut (mm)")
    action_at_12th_treble_mm: float = Field(default=1.9, description="Treble 12th (mm)")
    action_at_12th_bass_mm: float = Field(default=2.4, description="Bass 12th (mm)")
    saddle_height_mm: float = Field(default=3.0)
    saddle_projection_mm: float = Field(default=2.5)
    scale_length_mm: float = Field(default=628.65)
    fretboard_height_at_joint_mm: float = Field(default=5.0)
    neck_joint_fret: int = Field(default=14)


class SetupIssueResponse(BaseModel):
    """Single setup issue for API response."""
    parameter: str
    current_value: float
    recommended_range: List[float]  # [min, max]
    gate: str
    fix: str


class SetupCascadeResponse(BaseModel):
    """Response from setup cascade evaluation."""
    state: Dict[str, Any]  # serialized SetupState fields
    issues: List[SetupIssueResponse]
    overall_gate: str
    summary: str
    suggestions: List[str] = Field(default_factory=list)


# ─── Neck/Tail Block Models (GEOMETRY-005) ────────────────────────────────────

class BlocksRequest(BaseModel):
    """Request for neck and tail block calculation."""
    body_style: str = Field(
        default="dreadnought",
        description="Body style (dreadnought, om_000, parlor, classical, archtop, jumbo, concert)"
    )
    neck_heel_width_mm: Optional[float] = Field(
        None, gt=0,
        description="Neck heel width in mm (uses default for body style if not provided)"
    )
    side_depth_at_neck_mm: Optional[float] = Field(
        None, gt=0,
        description="Side depth at neck in mm (uses default for body style if not provided)"
    )
    side_depth_at_tail_mm: Optional[float] = Field(
        None, gt=0,
        description="Side depth at tail in mm (uses default for body style if not provided)"
    )
    material: str = Field(default="mahogany", description="Block material")


class BlockResponse(BaseModel):
    """Response with single block specification."""
    block_type: str
    height_mm: float
    width_mm: float
    depth_mm: float
    material: str
    grain_orientation: str
    gate: str
    notes: List[str]


class BlocksResponse(BaseModel):
    """Response with both neck and tail block specifications."""
    neck: BlockResponse
    tail: BlockResponse
    body_style: str


class BlockOptionsResponse(BaseModel):
    """Response with supported body styles for block calculation."""
    body_styles: List[str]


# ─── Voicing Models ───────────────────────────────────────────────────────────

class TapToneMeasurementModel(BaseModel):
    """Single tap tone measurement."""
    stage: str = Field(..., description="Build stage")
    thickness_mm: float = Field(..., gt=0, description="Plate thickness in mm")
    tap_frequency_hz: float = Field(..., gt=0, description="Measured frequency in Hz")
    timestamp: str = Field(..., description="ISO format timestamp")
    notes: str = Field(default="", description="Optional notes (include 'top' or 'back')")


class VoicingSessionRequest(BaseModel):
    """Request for voicing analysis."""
    instrument_id: str = Field(..., description="Unique instrument identifier")
    top_species: str = Field(..., description="Top wood species")
    back_species: str = Field(..., description="Back wood species")
    body_style: str = Field(..., description="Body style (dreadnought, om_000, etc.)")
    measurements: List[TapToneMeasurementModel] = Field(..., description="List of tap tone measurements")
    target_top_hz: float = Field(..., gt=0, description="Target top frequency in Hz")
    target_back_hz: float = Field(..., gt=0, description="Target back frequency in Hz")


class VoicingReportResponse(BaseModel):
    """Response with voicing analysis."""
    instrument_id: str
    current_stage: str
    top_status: str
    back_status: str
    top_frequency_hz: Optional[float]
    back_frequency_hz: Optional[float]
    top_delta_hz: float
    back_delta_hz: float
    predicted_top_hz: Optional[float]
    predicted_back_hz: Optional[float]
    trend_slope: float
    gate: str
    notes: List[str]


class FrequencyPredictionRequest(BaseModel):
    """Request for frequency prediction."""
    current_thickness_mm: float = Field(..., gt=0, description="Current thickness in mm")
    current_frequency_hz: float = Field(..., gt=0, description="Current frequency in Hz")
    target_thickness_mm: float = Field(..., gt=0, description="Target thickness in mm")


class FrequencyPredictionResponse(BaseModel):
    """Response with predicted frequency."""
    current_thickness_mm: float
    current_frequency_hz: float
    target_thickness_mm: float
    predicted_frequency_hz: float


class TargetFrequenciesResponse(BaseModel):
    """Response with target frequencies for body style."""
    body_style: str
    top_hz: float
    back_hz: float


class BuildStagesResponse(BaseModel):
    """Response with list of build stages."""
    stages: List[str]


# ─── Build Sequence Models (CONSTRUCTION-010) ─────────────────────────────────

class BuildSequenceRequest(BaseModel):
    """Request for running a complete build sequence."""
    build_id: Optional[str] = Field(default=None, description="Unique build identifier")
    preset: str = Field(
        default="dreadnought",
        description="Preset type: dreadnought, om, classical"
    )
    scale_length_mm: Optional[float] = Field(default=None, gt=0)
    string_count: Optional[int] = Field(default=None, ge=4, le=12)
    fret_count: Optional[int] = Field(default=None, ge=12, le=36)
    top_species: Optional[str] = Field(default=None)
    back_species: Optional[str] = Field(default=None)
    finish_type: Optional[str] = Field(default=None)
    build_rh_pct: Optional[float] = Field(default=None, ge=0, le=100)
    target_rh_pct: Optional[float] = Field(default=None, ge=0, le=100)


class StageResultResponse(BaseModel):
    """Result of a single build stage."""
    stage_name: str
    status: str
    gate: str
    warnings: List[str] = []
    errors: List[str] = []
    duration_ms: Optional[float] = None


class BuildSequenceResponse(BaseModel):
    """Response from build sequence execution."""
    build_id: str
    overall_gate: str
    stages: Dict[str, StageResultResponse]
    warnings: List[str]
    errors: List[str]
    spec: Dict[str, Any]
    string_tension: Optional[Dict[str, Any]] = None
    bridge_geometry: Optional[Dict[str, Any]] = None
    wood_movement: Optional[Dict[str, Any]] = None
    finish_schedule: Optional[Dict[str, Any]] = None


class BuildSequenceOptionsResponse(BaseModel):
    """Available options for build sequence configuration."""
    presets: List[str]
    instrument_types: List[str]
    body_styles: List[str]
    neck_joint_types: List[str]


# ─── Setup Cascade Endpoints (CONSTRUCTION-002) ───────────────────────────────

@router.post(
    "/setup/evaluate",
    response_model=SetupCascadeResponse,
    summary="Evaluate instrument setup (CONSTRUCTION-002)",
    description="""
    Run setup cascade: check neck angle, relief, nut action, 12th fret action,
    saddle projection. Returns GREEN/YELLOW/RED per parameter and overall,
    plus plain-language fix suggestions.
    """,
)
def evaluate_instrument_setup(req: SetupStateRequest) -> SetupCascadeResponse:
    """Evaluate setup state and return cascade result with issues and suggestions."""
    state = SetupState(
        neck_angle_deg=req.neck_angle_deg,
        truss_rod_relief_mm=req.truss_rod_relief_mm,
        nut_slot_depths_mm=req.nut_slot_depths_mm or {},
        action_at_nut_mm=req.action_at_nut_mm,
        action_at_12th_treble_mm=req.action_at_12th_treble_mm,
        action_at_12th_bass_mm=req.action_at_12th_bass_mm,
        saddle_height_mm=req.saddle_height_mm,
        saddle_projection_mm=req.saddle_projection_mm,
        scale_length_mm=req.scale_length_mm,
        fretboard_height_at_joint_mm=req.fretboard_height_at_joint_mm,
        neck_joint_fret=req.neck_joint_fret,
    )
    result = evaluate_setup(state)
    # Serialize state as dict (simple fields only)
    state_dict = {
        "neck_angle_deg": state.neck_angle_deg,
        "truss_rod_relief_mm": state.truss_rod_relief_mm,
        "action_at_nut_mm": state.action_at_nut_mm,
        "action_at_12th_treble_mm": state.action_at_12th_treble_mm,
        "action_at_12th_bass_mm": state.action_at_12th_bass_mm,
        "saddle_height_mm": state.saddle_height_mm,
        "saddle_projection_mm": state.saddle_projection_mm,
        "scale_length_mm": state.scale_length_mm,
    }
    issues_resp = [
        SetupIssueResponse(
            parameter=i.parameter,
            current_value=i.current_value,
            recommended_range=list(i.recommended_range),
            gate=i.gate,
            fix=i.fix,
        )
        for i in result.issues
    ]
    suggestions = suggest_adjustments(result)
    return SetupCascadeResponse(
        state=state_dict,
        issues=issues_resp,
        overall_gate=result.overall_gate,
        summary=result.summary,
        suggestions=suggestions,
    )


# ─── Neck/Tail Block Endpoints (GEOMETRY-005) ─────────────────────────────────

@router.post(
    "/blocks",
    response_model=BlocksResponse,
    summary="Calculate neck and tail block dimensions (GEOMETRY-005)",
    description="""
    Calculate neck and tail block dimensions for a given body style.

    **Input:**
    - Body style (dreadnought, om_000, parlor, classical, archtop, jumbo, concert)
    - Optional neck heel width override
    - Optional side depth overrides
    - Material (mahogany, maple, spanish_cedar)

    **Output for each block:**
    - Height (= side depth at location)
    - Width
    - Depth (front to back)
    - Grain orientation
    - Gate status (GREEN/YELLOW/RED)
    - Notes

    **Standard dimensions:**
    - Neck block: height=side depth, width=heel+12mm, depth=50-65mm
    - Tail block: height=side depth, width=65-90mm, depth=30-40mm

    **Gate Logic:**
    - GREEN: All dimensions within typical ranges
    - YELLOW: Borderline dimensions
    - RED: Structural concern (too small)
    """,
)
def calculate_blocks(req: BlocksRequest) -> BlocksResponse:
    """Calculate neck and tail block dimensions."""
    blocks = compute_both_blocks(
        body_style=req.body_style,
        neck_heel_width_mm=req.neck_heel_width_mm,
        side_depth_at_neck_mm=req.side_depth_at_neck_mm,
        side_depth_at_tail_mm=req.side_depth_at_tail_mm,
        material=req.material,
    )
    return BlocksResponse(
        neck=BlockResponse(**blocks["neck"].to_dict()),
        tail=BlockResponse(**blocks["tail"].to_dict()),
        body_style=req.body_style,
    )


@router.get(
    "/blocks/options",
    response_model=BlockOptionsResponse,
    summary="List supported body styles for block calculation",
)
def get_block_options() -> BlockOptionsResponse:
    """Return list of supported body styles."""
    return BlockOptionsResponse(body_styles=list_block_body_styles())


# ─── Build Sequence Endpoints (CONSTRUCTION-010) ──────────────────────────────

@router.post(
    "/build-sequence",
    response_model=BuildSequenceResponse,
    summary="Run complete build calculation sequence (CONSTRUCTION-010)",
)
def run_build_sequence_endpoint(req: BuildSequenceRequest) -> BuildSequenceResponse:
    """
    Execute the complete build calculation sequence.

    Runs all calculation stages in order:
    - String tension
    - Bridge geometry
    - Wood movement
    - Finish schedule

    Each stage reads from and writes to the shared BuildSpec state.
    """
    # Create spec from preset
    if req.preset.lower() == "om":
        spec = create_om_spec(req.build_id)
    elif req.preset.lower() == "classical":
        spec = create_classical_spec(req.build_id)
    else:
        spec = create_dreadnought_spec(req.build_id)

    # Apply overrides from request
    if req.scale_length_mm is not None:
        spec.scale_length_mm = req.scale_length_mm
    if req.string_count is not None:
        spec.string_count = req.string_count
    if req.fret_count is not None:
        spec.fret_count = req.fret_count
    if req.top_species is not None:
        spec.top_species = req.top_species
    if req.back_species is not None:
        spec.back_species = req.back_species
    if req.finish_type is not None:
        spec.finish_type = req.finish_type
    if req.build_rh_pct is not None:
        spec.build_rh_pct = req.build_rh_pct
    if req.target_rh_pct is not None:
        spec.target_rh_pct = req.target_rh_pct

    # Run the sequence
    result = run_build_sequence(spec)

    # Build stage responses
    stage_responses = {}
    for name, stage_result in result.stages.items():
        stage_responses[name] = StageResultResponse(
            stage_name=stage_result.stage_name,
            status=stage_result.status.value,
            gate=stage_result.gate,
            warnings=stage_result.warnings,
            errors=stage_result.errors,
            duration_ms=stage_result.duration_ms,
        )

    return BuildSequenceResponse(
        build_id=result.spec.build_id,
        overall_gate=result.overall_gate,
        stages=stage_responses,
        warnings=result.warnings,
        errors=result.errors,
        spec=result.spec.to_dict(),
        string_tension=result.string_tension.to_dict() if result.string_tension else None,
        bridge_geometry=result.bridge_geometry.to_dict() if result.bridge_geometry else None,
        wood_movement=result.wood_movement.to_dict() if result.wood_movement else None,
        finish_schedule=result.finish_schedule.to_dict() if result.finish_schedule else None,
    )


@router.get(
    "/build-sequence/options",
    response_model=BuildSequenceOptionsResponse,
    summary="List options for build sequence configuration",
)
def get_build_sequence_options() -> BuildSequenceOptionsResponse:
    """Return available presets and options for build sequence."""
    return BuildSequenceOptionsResponse(
        presets=["dreadnought", "om", "classical"],
        instrument_types=[t.value for t in InstrumentType],
        body_styles=[s.value for s in BodyStyle],
        neck_joint_types=[j.value for j in NeckJointType],
    )


# ─── Voicing History Endpoints ────────────────────────────────────────────────

@router.post(
    "/voicing/analyze",
    response_model=VoicingReportResponse,
    summary="Analyze voicing progress",
    description="""
    Analyze tap tone measurements to track voicing progress.

    **Build stages:**
    - rough_thicknessed: First tap tone reading
    - braced_free_plate: After bracing, before assembly
    - assembled_in_box: After gluing top/back
    - strung_up: Final instrument

    **Physics:**
    - f is proportional to h (frequency proportional to thickness for thin plates)
    - Thinning lowers frequency
    - Target: specific frequency for optimal tone

    **Gate Logic:**
    - GREEN: On target or minor adjustment needed
    - YELLOW: Significant work remaining
    - RED: Over-thinned (frequency too low)
    """,
)
def analyze_voicing(req: VoicingSessionRequest) -> VoicingReportResponse:
    """Analyze voicing progress for an instrument."""
    # Convert request to VoicingSession
    measurements = [
        TapToneMeasurement(
            stage=m.stage,
            thickness_mm=m.thickness_mm,
            tap_frequency_hz=m.tap_frequency_hz,
            timestamp=m.timestamp,
            notes=m.notes,
        )
        for m in req.measurements
    ]
    session = VoicingSession(
        instrument_id=req.instrument_id,
        top_species=req.top_species,
        back_species=req.back_species,
        body_style=req.body_style,
        measurements=measurements,
        target_top_hz=req.target_top_hz,
        target_back_hz=req.target_back_hz,
    )
    report = analyze_voicing_progress(session)
    return VoicingReportResponse(**report.to_dict())


@router.post(
    "/voicing/predict",
    response_model=FrequencyPredictionResponse,
    summary="Predict frequency at target thickness",
    description="""
    Predict the frequency after thinning to a target thickness.

    Uses linear relationship: f is proportional to h (for thin plates)
    """,
)
def predict_voicing_frequency(req: FrequencyPredictionRequest) -> FrequencyPredictionResponse:
    """Predict frequency at target thickness."""
    predicted = predict_final_frequency(
        current_thickness_mm=req.current_thickness_mm,
        current_frequency_hz=req.current_frequency_hz,
        target_thickness_mm=req.target_thickness_mm,
    )
    return FrequencyPredictionResponse(
        current_thickness_mm=req.current_thickness_mm,
        current_frequency_hz=req.current_frequency_hz,
        target_thickness_mm=req.target_thickness_mm,
        predicted_frequency_hz=round(predicted, 1),
    )


@router.get(
    "/voicing/targets/{body_style}",
    response_model=TargetFrequenciesResponse,
    summary="Get target frequencies for body style",
)
def get_voicing_targets(body_style: str) -> TargetFrequenciesResponse:
    """Get typical target frequencies for a body style."""
    targets = get_target_frequencies(body_style)
    return TargetFrequenciesResponse(
        body_style=body_style,
        top_hz=targets["top"],
        back_hz=targets["back"],
    )


@router.get(
    "/voicing/stages",
    response_model=BuildStagesResponse,
    summary="List build stages for voicing",
)
def get_voicing_stages() -> BuildStagesResponse:
    """Return list of build stages in order."""
    return BuildStagesResponse(stages=list_build_stages())
