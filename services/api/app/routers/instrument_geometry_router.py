"""
Instrument Geometry Router (GEOMETRY-010+)
===========================================

Endpoints for instrument geometry calculations:
- Side bending parameters
- Side thickness recommendations
- Nut slot depth schedule
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.calculators.side_bending_calc import (
    BendingPlan,
    SideThicknessSpec,
    compute_bending_parameters,
    check_side_thickness,
    list_supported_species,
    list_instrument_types,
)
from app.calculators.nut_slot_calc import (
    NutSlotSpec,
    compute_nut_slot_schedule,
    list_fret_types,
    list_string_sets,
    get_string_set,
    STANDARD_STRING_SETS,
)
from app.calculators.soundhole_calc import (
    SoundholeSpec,
    compute_soundhole_spec,
    check_soundhole_position,
    list_body_styles,
)
from app.calculators.fret_leveling_calc import (
    FretProfile,
    LevelingPlan,
    analyze_fret_heights,
    compute_leveling_radius,
)
from app.calculators.nut_comp_calc import (
    NutCompSpec,
    compute_nut_compensation,
    compare_nut_types,
)
from app.calculators.voicing_history_calc import (
    TapToneMeasurement,
    VoicingSession,
    VoicingReport,
    analyze_voicing_progress,
    predict_final_frequency,
    get_target_frequencies,
    list_build_stages,
)
from app.calculators.setup_cascade import (
    SetupState,
    SetupCascadeResult,
    SetupIssue,
    evaluate_setup,
    suggest_adjustments,
)
from app.calculators.bridge_calc import (
    BridgeSpec,
    PinPositions,
    compute_bridge_spec,
    compute_pin_positions,
    list_body_styles as list_bridge_body_styles,
    get_bridge_defaults,
)
from app.calculators.neck_block_calc import (
    BlockSpec,
    compute_neck_block,
    compute_tail_block,
    compute_both_blocks,
    list_body_styles as list_block_body_styles,
    get_default_side_depths,
)
from app.calculators.fret_wire_calc import (
    FretWireSpec,
    recommend_fret_wire,
    list_fret_wire_catalog,
    list_fret_wire_names,
    list_playing_styles,
    list_fretboard_materials,
    list_neck_profiles,
    list_string_gauges,
    get_fret_wire,
)
from app.calculators.wood_movement_calc import (
    WoodMovementSpec,
    SafeHumidityRange,
    compute_wood_movement,
    safe_humidity_range,
    list_species as list_wood_species,
    get_shrinkage_coefficient,
)
from app.calculators.electronics_layout_calc import (
    CavitySpec,
    compute_pickup_cavity,
    compute_control_layout,
    check_cavity_clearance,
    compute_shielding_area,
    list_pickup_types,
    list_switch_types,
)
from app.calculators.build_sequence import (
    BuildSpec,
    BuildResult,
    BuildSequence,
    InstrumentType,
    BodyStyle,
    NeckJointType,
    create_dreadnought_spec,
    create_om_spec,
    create_classical_spec,
    run_build_sequence,
)
from app.calculators.electronics_layout_calc import (
    list_jack_types,
    list_body_styles as list_electronics_body_styles,
)

router = APIRouter(
    prefix="/api/instrument",
    tags=["instrument-geometry"],
)


# ─── Request/Response Models ──────────────────────────────────────────────────

class SideBendingRequest(BaseModel):
    """Request for side bending parameters calculation."""
    species: str = Field(..., description="Wood species (e.g., 'rosewood', 'mahogany')")
    side_thickness_mm: float = Field(..., gt=0, description="Side thickness in mm")
    waist_radius_mm: float = Field(..., gt=0, description="Tightest bend radius (waist) in mm")
    instrument_type: str = Field(
        default="steel_string_acoustic",
        description="Instrument type (steel_string_acoustic, classical, archtop_jazz, etc.)"
    )


class SideBendingResponse(BaseModel):
    """Response with bending parameters and risk assessment."""
    species: str
    side_thickness_mm: float
    waist_radius_mm: float
    temp_c: float
    moisture_pct: float
    risk: str
    spring_back_deg: float
    notes: List[str]


class SideThicknessRequest(BaseModel):
    """Request for side thickness recommendation."""
    instrument_type: str = Field(..., description="Instrument type")
    species: str = Field(..., description="Wood species")


class SideThicknessResponse(BaseModel):
    """Response with thickness recommendation."""
    instrument_type: str
    species: str
    target_mm: float
    min_mm: float
    max_mm: float
    note: str


class SupportedOptionsResponse(BaseModel):
    """Response with supported species and instrument types."""
    species: List[str]
    instrument_types: List[str]

class SoundholeRequest(BaseModel):
    """Request for soundhole specification."""
    body_style: str = Field(..., description="Body style (dreadnought, om_000, parlor, classical, etc.)")
    body_length_mm: float = Field(..., gt=0, description="Body length from neck block to tail block in mm")
    custom_diameter_mm: Optional[float] = Field(None, gt=0, description="Custom diameter override in mm")


class SoundholeResponse(BaseModel):
    """Response with soundhole specification."""
    diameter_mm: float
    position_from_neck_block_mm: float
    body_style: str
    gate: str
    notes: List[str]


class SoundholePositionCheckRequest(BaseModel):
    """Request to check soundhole position validity."""
    diameter_mm: float = Field(..., gt=0, description="Soundhole diameter in mm")
    position_mm: float = Field(..., gt=0, description="Position from neck block in mm")
    body_length_mm: float = Field(..., gt=0, description="Body length in mm")


class SoundholePositionCheckResponse(BaseModel):
    """Response with position check result."""
    gate: str
    diameter_mm: float
    position_mm: float
    body_length_mm: float


class SoundholeOptionsResponse(BaseModel):
    """Response with supported body styles."""
    body_styles: List[str]

class FretLevelingRequest(BaseModel):
    """Request for fret leveling analysis."""
    heights_mm: List[float] = Field(..., description="Measured fret heights from fret 1 onwards")
    scale_length_mm: float = Field(..., gt=0, description="Scale length in mm")
    relief_mm: float = Field(default=0.2, ge=0, description="Target neck relief in mm")
    tolerance_mm: float = Field(default=0.03, gt=0, description="High fret detection tolerance")


class FretProfileResponse(BaseModel):
    """Single fret profile in response."""
    fret_number: int
    height_mm: float
    deviation_mm: float
    status: str


class FretLevelingResponse(BaseModel):
    """Response with fret leveling analysis."""
    frets: List[FretProfileResponse]
    high_fret_count: int
    low_fret_count: int
    max_deviation_mm: float
    material_removal_mm: float
    replacement_needed: List[int]
    leveling_radius_mm: float
    gate: str
    notes: List[str]


class LevelingRadiusRequest(BaseModel):
    """Request for leveling beam radius calculation."""
    scale_length_mm: float = Field(..., gt=0, description="Scale length in mm")
    relief_mm: float = Field(..., gt=0, description="Target relief in mm")


class LevelingRadiusResponse(BaseModel):
    """Response with leveling beam radius."""
    scale_length_mm: float
    relief_mm: float
    radius_mm: float

class NutCompensationRequest(BaseModel):
    """Request for nut compensation calculation."""
    nut_type: str = Field(..., description="'traditional' or 'zero_fret'")
    nut_width_mm: float = Field(default=3.0, gt=0, description="Nut width in mm")
    break_angle_deg: float = Field(default=10.0, ge=0, description="Break angle at nut in degrees")
    scale_length_mm: float = Field(..., gt=0, description="Scale length in mm")


class NutCompensationResponse(BaseModel):
    """Response with nut compensation specification."""
    nut_type: str
    compensation_mm: float
    effective_scale_length_mm: float
    open_string_pitch_error_cents: float
    gate: str
    recommendation: str


class NutComparisonRequest(BaseModel):
    """Request for nut type comparison."""
    scale_length_mm: float = Field(..., gt=0, description="Scale length in mm")
    nut_width_mm: float = Field(default=3.0, gt=0, description="Nut width in mm")
    break_angle_deg: float = Field(default=10.0, ge=0, description="Break angle in degrees")


class NutComparisonResponse(BaseModel):
    """Response comparing traditional vs zero-fret."""
    traditional: Dict[str, Any]
    zero_fret: Dict[str, Any]
    comparison: Dict[str, Any]

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






# ─── Nut Slot Models ──────────────────────────────────────────────────────────

class StringSpec(BaseModel):
    """Single string specification."""
    name: str = Field(..., description="String name (e.g., 'e', 'B', 'G')")
    gauge_inch: float = Field(..., gt=0, description="String gauge in inches")


class NutSlotsRequest(BaseModel):
    """Request for nut slot schedule calculation."""
    string_set: Optional[List[StringSpec]] = Field(
        default=None,
        description="List of strings with name and gauge_inch. If not provided, use preset_name."
    )
    preset_name: Optional[str] = Field(
        default=None,
        description="Predefined string set name (light_electric_009, regular_electric_010, etc.)"
    )
    fret_type: str = Field(
        default="medium",
        description="Fret type (vintage_narrow, medium, medium_jumbo, jumbo, extra_jumbo, evo_gold)"
    )
    nut_width_mm: float = Field(default=43.0, gt=0, description="Nut width in mm")
    clearance_mm: float = Field(default=0.13, ge=0.05, le=0.3, description="Clearance above first fret")


class NutSlotResponse(BaseModel):
    """Single nut slot specification."""
    string_name: str
    gauge_inch: float
    gauge_mm: float
    fret_type: str
    slot_depth_mm: float
    slot_width_mm: float
    string_height_above_first_fret_mm: float
    gate: str


class NutSlotsResponse(BaseModel):
    """Response with complete nut slot schedule."""
    slots: List[NutSlotResponse]
    fret_type: str
    nut_width_mm: float
    clearance_mm: float


class NutSlotOptionsResponse(BaseModel):
    """Response with supported fret types and string sets."""
    fret_types: List[str]
    preset_string_sets: List[str]


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.post(
    "/side-bending",
    response_model=SideBendingResponse,
    summary="Calculate side bending parameters",
    description="""
    Calculate bending preparation parameters for guitar/instrument sides.

    **Input:**
    - Wood species
    - Side thickness (mm)
    - Waist radius (tightest bend, mm)
    - Instrument type

    **Output:**
    - Recommended bending temperature (°C)
    - Target moisture content (%)
    - Risk assessment (GREEN/YELLOW/RED)
    - Spring-back estimate (degrees)
    - Notes and warnings

    **Risk Gate Logic:**
    - GREEN: waist_radius >= species minimum safe radius
    - YELLOW: waist_radius >= min_radius × 0.85 (borderline)
    - RED: waist_radius < min_radius × 0.85 (cracking risk)
    """,
)
def calculate_side_bending(req: SideBendingRequest) -> SideBendingResponse:
    """Calculate side bending parameters with risk assessment."""
    plan: BendingPlan = compute_bending_parameters(
        species=req.species,
        side_thickness_mm=req.side_thickness_mm,
        waist_radius_mm=req.waist_radius_mm,
        instrument_type=req.instrument_type,
    )
    return SideBendingResponse(**plan.to_dict())


@router.post(
    "/side-thickness",
    response_model=SideThicknessResponse,
    summary="Get side thickness recommendation",
    description="""
    Get recommended side thickness for an instrument type and wood species.

    **Input:**
    - Instrument type (steel_string_acoustic, classical, archtop_jazz, etc.)
    - Wood species

    **Output:**
    - Target thickness (mm)
    - Minimum/maximum range (mm)
    - Species-specific notes
    """,
)
def get_side_thickness(req: SideThicknessRequest) -> SideThicknessResponse:
    """Get side thickness recommendation for instrument/species combo."""
    spec: SideThicknessSpec = check_side_thickness(
        instrument_type=req.instrument_type,
        species=req.species,
    )
    return SideThicknessResponse(**spec.to_dict())


@router.get(
    "/side-bending/options",
    response_model=SupportedOptionsResponse,
    summary="List supported species and instrument types",
)
def get_bending_options() -> SupportedOptionsResponse:
    """Return lists of supported wood species and instrument types."""
    return SupportedOptionsResponse(
        species=list_supported_species(),
        instrument_types=list_instrument_types(),
    )



# ─── Nut Slot Endpoints ───────────────────────────────────────────────────────

@router.post(
    "/nut-slots",
    response_model=NutSlotsResponse,
    summary="Calculate nut slot schedule",
    description="""
    Calculate nut slot depths for a complete string set.

    **Input:**
    - String set (custom list or preset name)
    - Fret type (affects crown height)
    - Nut width (mm)
    - Clearance above first fret (mm)

    **Output per string:**
    - Slot depth (mm)
    - Slot width (mm)
    - String height above first fret
    - Gate (GREEN/YELLOW/RED)

    **Formula:**
    slot_depth = string_diameter/2 + fret_crown_height/2 + clearance

    **Gate Logic:**
    - GREEN: 0.3-0.5mm string height (optimal)
    - YELLOW: 0.2-0.3mm (low, buzzing risk) or 0.5-0.8mm (high, intonation)
    - RED: < 0.2mm or > 0.8mm
    """,
)
def calculate_nut_slots(req: NutSlotsRequest) -> NutSlotsResponse:
    """Calculate nut slot schedule for string set."""
    # Get string set from preset or custom
    if req.string_set:
        string_set = [{"name": s.name, "gauge_inch": s.gauge_inch} for s in req.string_set]
    elif req.preset_name:
        string_set = get_string_set(req.preset_name)
    else:
        # Default to light acoustic
        string_set = get_string_set("light_acoustic_012")

    # Compute schedule
    schedule = compute_nut_slot_schedule(
        string_set=string_set,
        fret_type=req.fret_type,
        nut_width_mm=req.nut_width_mm,
        clearance_mm=req.clearance_mm,
    )

    return NutSlotsResponse(
        slots=[NutSlotResponse(**s.to_dict()) for s in schedule],
        fret_type=req.fret_type,
        nut_width_mm=req.nut_width_mm,
        clearance_mm=req.clearance_mm,
    )


@router.get(
    "/nut-slots/options",
    response_model=NutSlotOptionsResponse,
    summary="List supported fret types and string sets",
)
def get_nut_slot_options() -> NutSlotOptionsResponse:
    """Return lists of supported fret types and preset string sets."""
    return NutSlotOptionsResponse(
        fret_types=list_fret_types(),
        preset_string_sets=list_string_sets(),
    )


# ─── Setup cascade (CONSTRUCTION-002) ────────────────────────────────────────

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

# ─── Soundhole Endpoints ─────────────────────────────────────────────────────

@router.post(
    "/soundhole",
    response_model=SoundholeResponse,
    summary="Calculate soundhole specification",
    description="""
    Calculate soundhole diameter and position for a given body style.

    **Input:**
    - Body style (dreadnought, om_000, parlor, classical, etc.)
    - Body length (mm)
    - Optional custom diameter override

    **Output:**
    - Diameter (mm)
    - Position from neck block (mm)
    - Gate status (GREEN/YELLOW/RED)
    - Notes and warnings

    **Standard diameters:**
    - Dreadnought: 100mm
    - OM/000: 98mm
    - Parlor: 85mm
    - Classical: 85mm
    """,
)
def calculate_soundhole(req: SoundholeRequest) -> SoundholeResponse:
    """Calculate soundhole specification for body style."""
    spec: SoundholeSpec = compute_soundhole_spec(
        body_style=req.body_style,
        body_length_mm=req.body_length_mm,
        custom_diameter_mm=req.custom_diameter_mm,
    )
    return SoundholeResponse(**spec.to_dict())


@router.post(
    "/soundhole/check-position",
    response_model=SoundholePositionCheckResponse,
    summary="Check soundhole position validity",
    description="""
    Validate a soundhole position against body proportions.

    **Position rules:**
    - Should be 45-55% of body length from neck block
    - Front edge must clear neck block by at least 20mm
    - Rear edge must leave room for bracing (40mm from tail)
    """,
)
def check_soundhole_position_endpoint(req: SoundholePositionCheckRequest) -> SoundholePositionCheckResponse:
    """Check if soundhole position is valid."""
    gate = check_soundhole_position(
        diameter_mm=req.diameter_mm,
        position_mm=req.position_mm,
        body_length_mm=req.body_length_mm,
    )
    return SoundholePositionCheckResponse(
        gate=gate,
        diameter_mm=req.diameter_mm,
        position_mm=req.position_mm,
        body_length_mm=req.body_length_mm,
    )


@router.get(
    "/soundhole/options",
    response_model=SoundholeOptionsResponse,
    summary="List supported body styles for soundhole calculation",
)
def get_soundhole_options() -> SoundholeOptionsResponse:
    """Return list of supported body styles."""
    return SoundholeOptionsResponse(body_styles=list_body_styles())


# ─── Bridge Geometry Models (GEOMETRY-004) ───────────────────────────────────

class BridgeRequest(BaseModel):
    """Request for bridge geometry calculation."""
    body_style: str = Field(..., description="Body style (dreadnought, om_000, parlor, classical, archtop, jumbo)")
    scale_length_mm: float = Field(..., gt=0, description="Scale length in mm")
    string_count: int = Field(default=6, ge=1, le=12, description="Number of strings")
    custom_spacing_mm: Optional[float] = Field(None, gt=0, description="Custom string spacing override in mm")


class BridgeResponse(BaseModel):
    """Response with bridge geometry specification."""
    body_style: str
    string_spacing_mm: float
    bridge_length_mm: float
    bridge_width_mm: float
    saddle_slot_width_mm: float
    saddle_slot_depth_mm: float
    pin_spacing_mm: float
    bridge_plate_length_mm: float
    bridge_plate_width_mm: float
    material: str
    gate: str
    string_count: int
    notes: List[str]


class PinPositionsRequest(BaseModel):
    """Request for bridge pin positions calculation."""
    string_spacing_mm: float = Field(..., gt=0, description="E-to-e string spacing in mm")
    string_count: int = Field(default=6, ge=1, le=12, description="Number of strings")
    bridge_center_x: float = Field(default=0.0, description="X position of bridge center")


class PinPositionsResponse(BaseModel):
    """Response with bridge pin positions."""
    positions_mm: List[float]
    string_spacing_mm: float
    string_count: int
    total_span_mm: float


class BridgeOptionsResponse(BaseModel):
    """Response with supported body styles for bridge calculation."""
    body_styles: List[str]


# ─── Bridge Geometry Endpoints (GEOMETRY-004) ────────────────────────────────

@router.post(
    "/bridge",
    response_model=BridgeResponse,
    summary="Calculate bridge geometry (GEOMETRY-004)",
    description="""
    Calculate bridge dimensions for a given body style.

    **Input:**
    - Body style (dreadnought, om_000, parlor, classical, archtop, jumbo)
    - Scale length (mm)
    - String count (default 6)
    - Optional custom string spacing

    **Output:**
    - String spacing at saddle (E to e)
    - Bridge dimensions (length × width)
    - Saddle slot dimensions
    - Pin spacing
    - Bridge plate dimensions
    - Material recommendation
    - Gate status (GREEN/YELLOW)

    **Standard dimensions:**
    - Dreadnought: spacing=54mm, length=170mm, width=32mm
    - OM/000: spacing=52mm, length=165mm, width=30mm
    - Parlor: spacing=50mm, length=155mm, width=28mm
    - Classical: spacing=58mm, length=180mm, width=28mm (tie block)
    - Archtop: spacing=52mm, length=95mm, width=18mm (tune-o-matic)
    """,
)
def calculate_bridge(req: BridgeRequest) -> BridgeResponse:
    """Calculate bridge geometry for body style."""
    spec: BridgeSpec = compute_bridge_spec(
        body_style=req.body_style,
        scale_length_mm=req.scale_length_mm,
        string_count=req.string_count,
        custom_spacing_mm=req.custom_spacing_mm,
    )
    return BridgeResponse(**spec.to_dict())


@router.post(
    "/bridge/pin-positions",
    response_model=PinPositionsResponse,
    summary="Calculate bridge pin positions",
    description="""
    Calculate bridge pin X positions from centerline.

    **Input:**
    - String spacing (E to e, mm)
    - String count
    - Bridge center X position

    **Output:**
    - List of X positions (bass to treble)
    - Total span

    Pins are evenly distributed across the string spacing.
    Position[0] = low E (bass), Position[5] = high e (treble).
    """,
)
def calculate_pin_positions(req: PinPositionsRequest) -> PinPositionsResponse:
    """Calculate bridge pin positions."""
    result: PinPositions = compute_pin_positions(
        string_spacing_mm=req.string_spacing_mm,
        string_count=req.string_count,
        bridge_center_x=req.bridge_center_x,
    )
    return PinPositionsResponse(**result.to_dict())


@router.get(
    "/bridge/options",
    response_model=BridgeOptionsResponse,
    summary="List supported body styles for bridge calculation",
)
def get_bridge_options() -> BridgeOptionsResponse:
    """Return list of supported body styles."""
    return BridgeOptionsResponse(body_styles=list_bridge_body_styles())

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

# ─── Fret Leveling Endpoints ─────────────────────────────────────────────────

@router.post(
    "/fret-leveling",
    response_model=FretLevelingResponse,
    summary="Analyze fret heights for leveling",
    description="""
    Analyze measured fret heights to determine leveling requirements.

    **Input:**
    - List of fret heights (measured from fretboard surface)
    - Scale length (mm)
    - Target relief (mm, default 0.2)
    - Tolerance for high fret detection (mm, default 0.03)

    **Output:**
    - Per-fret analysis (height, deviation, status)
    - Count of high/low frets
    - Maximum deviation and material removal needed
    - Frets needing replacement (if any)
    - Leveling beam radius
    - Gate status (GREEN/YELLOW/RED)

    **Gate Logic:**
    - GREEN: No issues or minor leveling needed
    - YELLOW: Significant leveling or many high frets
    - RED: Frets need replacement (too low after leveling)
    """,
)
def analyze_fret_leveling(req: FretLevelingRequest) -> FretLevelingResponse:
    """Analyze fret heights and create leveling plan."""
    plan: LevelingPlan = analyze_fret_heights(
        heights_mm=req.heights_mm,
        scale_length_mm=req.scale_length_mm,
        relief_mm=req.relief_mm,
        tolerance_mm=req.tolerance_mm,
    )
    return FretLevelingResponse(**plan.to_dict())


@router.post(
    "/fret-leveling/radius",
    response_model=LevelingRadiusResponse,
    summary="Calculate leveling beam radius",
    description="""
    Calculate the radius of the leveling beam arc for a given relief.

    The leveling beam should follow the neck relief curve.
    For typical relief values (0.1-0.3mm), the radius is very large
    (essentially flat with slight concavity).
    """,
)
def calculate_leveling_radius(req: LevelingRadiusRequest) -> LevelingRadiusResponse:
    """Calculate leveling beam radius for target relief."""
    radius = compute_leveling_radius(
        scale_length_mm=req.scale_length_mm,
        relief_mm=req.relief_mm,
    )
    return LevelingRadiusResponse(
        scale_length_mm=req.scale_length_mm,
        relief_mm=req.relief_mm,
        radius_mm=radius,
    )

# ─── Fret Wire Models (GEOMETRY-006) ──────────────────────────────────────────

class FretWireRecommendRequest(BaseModel):
    """Request for fret wire recommendation."""
    playing_style: str = Field(
        default="flatpick",
        description="Playing style (fingerstyle, flatpick, shred, jazz)"
    )
    fretboard_material: str = Field(
        default="rosewood",
        description="Fretboard material (rosewood, ebony, maple, pau_ferro, richlite)"
    )
    neck_profile: str = Field(
        default="C",
        description="Neck profile shape (C, D, V, U)"
    )
    string_gauge: str = Field(
        default="medium",
        description="String gauge category (light, medium, heavy)"
    )


class FretWireResponse(BaseModel):
    """Response with fret wire specification."""
    name: str
    crown_width_mm: float
    crown_height_mm: float
    tang_depth_mm: float
    tang_width_mm: float
    material: str
    hardness_hv: int
    wear_factor: float
    recommended_for: List[str]
    gate: str
    notes: str


class FretWireRecommendResponse(BaseModel):
    """Response with ranked fret wire recommendations."""
    recommendations: List[FretWireResponse]
    playing_style: str
    fretboard_material: str
    neck_profile: str
    string_gauge: str


class FretWireCatalogResponse(BaseModel):
    """Response with full fret wire catalog."""
    catalog: List[FretWireResponse]


class FretWireOptionsResponse(BaseModel):
    """Response with available options for fret wire selection."""
    playing_styles: List[str]
    fretboard_materials: List[str]
    neck_profiles: List[str]
    string_gauges: List[str]
    fret_wire_names: List[str]


# ─── Fret Wire Endpoints (GEOMETRY-006) ───────────────────────────────────────

@router.post(
    "/fret-wire/recommend",
    response_model=FretWireRecommendResponse,
    summary="Get fret wire recommendations (GEOMETRY-006)",
    description="""
    Get ranked fret wire recommendations based on playing style, fretboard,
    neck profile, and string gauge.

    **Input:**
    - Playing style (fingerstyle, flatpick, shred, jazz)
    - Fretboard material (rosewood, ebony, maple, pau_ferro, richlite)
    - Neck profile (C, D, V, U)
    - String gauge (light, medium, heavy)

    **Output:**
    - Ranked list of fret wire recommendations (best first)
    - Each includes dimensions, material, hardness, gate status, notes

    **Fret wire profiles:**
    - vintage_narrow: 1.65×0.89mm (classic vintage)
    - medium: 2.06×1.19mm (versatile)
    - medium_jumbo: 2.54×1.40mm (modern)
    - jumbo: 2.79×1.52mm (easy bending)
    - extra_jumbo: 2.90×1.65mm (shred)
    - evo_6105: 2.29×1.14mm (gold, hypoallergenic)
    - stainless_6105: 2.29×1.14mm (hardest, most durable)
    """,
)
def recommend_fret_wire_endpoint(req: FretWireRecommendRequest) -> FretWireRecommendResponse:
    """Get ranked fret wire recommendations."""
    recommendations = recommend_fret_wire(
        playing_style=req.playing_style,
        fretboard_material=req.fretboard_material,
        neck_profile=req.neck_profile,
        string_gauge=req.string_gauge,
    )
    return FretWireRecommendResponse(
        recommendations=[FretWireResponse(**r.to_dict()) for r in recommendations],
        playing_style=req.playing_style,
        fretboard_material=req.fretboard_material,
        neck_profile=req.neck_profile,
        string_gauge=req.string_gauge,
    )


@router.get(
    "/fret-wire/catalog",
    response_model=FretWireCatalogResponse,
    summary="Get full fret wire catalog",
)
def get_fret_wire_catalog() -> FretWireCatalogResponse:
    """Return complete fret wire catalog."""
    catalog = list_fret_wire_catalog()
    return FretWireCatalogResponse(
        catalog=[FretWireResponse(**fw.to_dict()) for fw in catalog]
    )


@router.get(
    "/fret-wire/options",
    response_model=FretWireOptionsResponse,
    summary="List options for fret wire selection",
)
def get_fret_wire_options() -> FretWireOptionsResponse:
    """Return lists of available options for fret wire selection."""
    return FretWireOptionsResponse(
        playing_styles=list_playing_styles(),
        fretboard_materials=list_fretboard_materials(),
        neck_profiles=list_neck_profiles(),
        string_gauges=list_string_gauges(),
        fret_wire_names=list_fret_wire_names(),
    )


# ─── Wood Movement Models (CONSTRUCTION-006) ─────────────────────────────────

class WoodMovementRequest(BaseModel):
    """Request for wood movement calculation."""
    species: str = Field(..., description="Wood species (sitka_spruce, rosewood, mahogany, etc.)")
    dimension_mm: float = Field(..., gt=0, description="Current dimension in mm (across grain)")
    rh_from: float = Field(..., ge=0, le=100, description="Starting relative humidity %")
    rh_to: float = Field(..., ge=0, le=100, description="Ending relative humidity %")
    grain_direction: str = Field(
        default="tangential",
        description="Grain direction: tangential (wider movement) or radial"
    )


class WoodMovementResponse(BaseModel):
    """Response with wood movement calculation."""
    species: str
    dimension_mm: float
    rh_from: float
    rh_to: float
    mc_change_pct: float
    movement_mm: float
    direction: str
    grain_direction: str
    shrinkage_coefficient: float
    gate: str
    risk_note: str


class SafeHumidityRequest(BaseModel):
    """Request for safe humidity range calculation."""
    species: str = Field(..., description="Wood species")
    dimension_mm: float = Field(default=400.0, gt=0, description="Dimension to evaluate in mm")
    max_movement_mm: float = Field(default=1.0, gt=0, description="Maximum acceptable movement in mm")
    nominal_rh: float = Field(default=45.0, ge=0, le=100, description="Nominal relative humidity %")


class SafeHumidityResponse(BaseModel):
    """Response with safe humidity range."""
    species: str
    nominal_rh: float
    max_movement_mm: float
    dimension_mm: float
    min_rh: float
    max_rh: float
    notes: List[str]


class WoodSpeciesResponse(BaseModel):
    """Response with supported wood species."""
    species: List[str]


# ─── Wood Movement Endpoints (CONSTRUCTION-006) ──────────────────────────────

@router.post(
    "/wood-movement",
    response_model=WoodMovementResponse,
    summary="Calculate wood movement from humidity change (CONSTRUCTION-006)",
    description="""
    Calculate dimensional change from relative humidity variation.

    **Physics:**
    ΔW = W₀ × ΔMC × S_r
    where:
    - ΔW = dimensional change (mm)
    - W₀ = initial dimension (mm)
    - ΔMC = moisture content change (%)
    - S_r = shrinkage coefficient

    **Input:**
    - Wood species
    - Dimension (mm, across grain)
    - Starting RH (%)
    - Ending RH (%)
    - Grain direction (tangential or radial)

    **Output:**
    - Movement (mm)
    - Direction (expansion/contraction)
    - Gate status (GREEN/YELLOW/RED)
    - Risk assessment

    **Houston note:** RH swings 30-90% seasonally. A 400mm spruce top
    can move 3-6mm — cracking territory for unprotected instruments.
    """,
)
def calculate_wood_movement(req: WoodMovementRequest) -> WoodMovementResponse:
    """Calculate wood movement from humidity change."""
    result: WoodMovementSpec = compute_wood_movement(
        species=req.species,
        dimension_mm=req.dimension_mm,
        rh_from=req.rh_from,
        rh_to=req.rh_to,
        grain_direction=req.grain_direction,
    )
    return WoodMovementResponse(**result.to_dict())


@router.post(
    "/wood-movement/safe-range",
    response_model=SafeHumidityResponse,
    summary="Calculate safe humidity range for wood",
    description="""
    Calculate the humidity range that keeps wood movement within limits.

    **Input:**
    - Wood species
    - Dimension to evaluate (default 400mm for guitar top)
    - Maximum acceptable movement (default 1.0mm)
    - Nominal/target humidity (default 45%)

    **Output:**
    - Min/max safe RH (%)
    - Notes and warnings

    Use this to determine case humidification requirements.
    """,
)
def calculate_safe_humidity_range(req: SafeHumidityRequest) -> SafeHumidityResponse:
    """Calculate safe humidity range for wood species."""
    result: SafeHumidityRange = safe_humidity_range(
        species=req.species,
        dimension_mm=req.dimension_mm,
        max_movement_mm=req.max_movement_mm,
        nominal_rh=req.nominal_rh,
    )
    return SafeHumidityResponse(**result.to_dict())


@router.get(
    "/wood-movement/species",
    response_model=WoodSpeciesResponse,
    summary="List supported wood species for movement calculation",
)
def get_wood_species() -> WoodSpeciesResponse:
    """Return list of supported wood species."""
    return WoodSpeciesResponse(species=list_wood_species())

# ─── Nut Compensation Endpoints ──────────────────────────────────────────────

@router.post(
    "/nut-compensation",
    response_model=NutCompensationResponse,
    summary="Calculate nut compensation",
    description="""
    Calculate nut compensation for traditional or zero-fret system.

    **Traditional nut:**
    - The nut acts as the zero reference point
    - String contact point offset causes slight sharpness
    - Compensation moves effective zero toward saddle

    **Zero-fret:**
    - A fret at position zero sets string height
    - Nut becomes string guide only
    - Eliminates nut slot intonation issues

    **Compensation formula (traditional):**
    comp_mm = (nut_width / 2) × (1 - cos(break_angle)) + stretch_factor
    """,
)
def calculate_nut_compensation(req: NutCompensationRequest) -> NutCompensationResponse:
    """Calculate nut compensation for given nut type."""
    spec: NutCompSpec = compute_nut_compensation(
        nut_type=req.nut_type,
        nut_width_mm=req.nut_width_mm,
        break_angle_deg=req.break_angle_deg,
        scale_length_mm=req.scale_length_mm,
    )
    return NutCompensationResponse(**spec.to_dict())


@router.post(
    "/nut-compensation/compare",
    response_model=NutComparisonResponse,
    summary="Compare traditional vs zero-fret",
    description="""
    Compare traditional nut against zero-fret system for the same parameters.

    Returns specs for both types plus a comparison summary highlighting
    advantages and pitch error differences.
    """,
)
def compare_nut_compensation(req: NutComparisonRequest) -> NutComparisonResponse:
    """Compare traditional nut vs zero-fret."""
    comparison = compare_nut_types(
        scale_length_mm=req.scale_length_mm,
        nut_width_mm=req.nut_width_mm,
        break_angle_deg=req.break_angle_deg,
    )
    return NutComparisonResponse(**comparison)


# ─── Electronics Layout Models (CONSTRUCTION-008) ─────────────────────────────

class PickupCavityRequest(BaseModel):
    """Request for pickup cavity calculation."""
    pickup_type: str = Field(
        ...,
        description="Pickup type (humbucker, single_coil, p90, mini_humbucker, filtertron, lipstick, jazzmaster)"
    )
    position: str = Field(
        default="bridge",
        description="Position (neck, middle, bridge)"
    )
    body_thickness_mm: float = Field(
        default=45.0, gt=0,
        description="Body thickness at pickup location in mm"
    )
    body_style: str = Field(
        default="default",
        description="Body style for position reference (les_paul, stratocaster, telecaster, sg, default)"
    )


class CavityResponse(BaseModel):
    """Response with cavity specification."""
    component: str
    length_mm: float
    width_mm: float
    depth_mm: float
    position_x_mm: float
    position_y_mm: float
    clearance_mm: float
    gate: str
    notes: List[str]


class PickupCavityResponse(BaseModel):
    """Response with pickup cavity specification."""
    cavity: CavityResponse
    pickup_type: str
    position: str


class ControlLayoutRequest(BaseModel):
    """Request for control layout calculation."""
    pot_count: int = Field(
        default=4, ge=1, le=6,
        description="Number of potentiometers (1-6)"
    )
    switch_type: str = Field(
        default="3way_toggle",
        description="Switch type (3way_toggle, 5way_blade, rotary)"
    )
    jack_type: str = Field(
        default="side",
        description="Jack type (side, top, endpin)"
    )
    body_style: str = Field(
        default="les_paul",
        description="Body style (les_paul, stratocaster, telecaster, sg, default)"
    )
    body_thickness_mm: float = Field(
        default=45.0, gt=0,
        description="Body thickness in mm"
    )


class ControlLayoutResponse(BaseModel):
    """Response with complete control layout."""
    cavities: List[CavityResponse]
    overall_gate: str
    pot_count: int
    switch_type: str
    jack_type: str
    body_style: str
    shielding_area_mm2: float


class ElectronicsLayoutRequest(BaseModel):
    """Combined request for full electronics layout."""
    pickups: List[PickupCavityRequest] = Field(
        default_factory=list,
        description="List of pickups to include"
    )
    pot_count: int = Field(default=4, ge=1, le=6)
    switch_type: str = Field(default="3way_toggle")
    jack_type: str = Field(default="side")
    body_style: str = Field(default="les_paul")
    body_thickness_mm: float = Field(default=45.0, gt=0)


class ElectronicsLayoutResponse(BaseModel):
    """Response with complete electronics layout."""
    pickup_cavities: List[CavityResponse]
    control_cavities: List[CavityResponse]
    overall_gate: str
    total_shielding_area_mm2: float
    body_style: str


class ElectronicsOptionsResponse(BaseModel):
    """Response with available options for electronics layout."""
    pickup_types: List[str]
    switch_types: List[str]
    jack_types: List[str]
    body_styles: List[str]


# ─── Electronics Layout Endpoints (CONSTRUCTION-008) ──────────────────────────

@router.post(
    "/electronics-layout",
    response_model=ElectronicsLayoutResponse,
    summary="Calculate complete electronics layout (CONSTRUCTION-008)",
    description="""
    Calculate complete electronics physical layout for electric guitars.

    **Input:**
    - List of pickups (type and position)
    - Pot count (1-6)
    - Switch type (3way_toggle, 5way_blade, rotary)
    - Jack type (side, top, endpin)
    - Body style (les_paul, stratocaster, telecaster, sg, default)
    - Body thickness (mm)

    **Output:**
    - Pickup cavities with dimensions and positions
    - Control cavity with pot layout
    - Switch and jack cavities
    - Overall gate status
    - Total shielding area

    **Standard cavity depths:**
    - Humbucker: 50×40×45mm
    - Single coil: 90×15×45mm
    - P90: 90×50×45mm
    - Control: 120×80×40mm typical
    - Switch: 40×20×35mm
    - Jack: 35mm diameter × 40mm

    **Pot spacing:** Minimum 19mm center-to-center for standard knobs.
    """,
)
def calculate_electronics_layout(req: ElectronicsLayoutRequest) -> ElectronicsLayoutResponse:
    """Calculate complete electronics layout."""
    all_cavities: List[CavitySpec] = []

    # Compute pickup cavities
    pickup_cavities: List[CavitySpec] = []
    for pickup_req in req.pickups:
        cavity = compute_pickup_cavity(
            pickup_type=pickup_req.pickup_type,
            position=pickup_req.position,
            body_thickness_mm=req.body_thickness_mm,
            body_style=req.body_style,
        )
        pickup_cavities.append(cavity)
        all_cavities.append(cavity)

    # Compute control layout
    control_cavities = compute_control_layout(
        pot_count=req.pot_count,
        switch_type=req.switch_type,
        jack_type=req.jack_type,
        body_style=req.body_style,
        body_thickness_mm=req.body_thickness_mm,
    )
    all_cavities.extend(control_cavities)

    # Check overall clearance
    overall_gate = check_cavity_clearance(all_cavities, req.body_thickness_mm)

    # Calculate shielding area
    shielding_area = compute_shielding_area(all_cavities)

    return ElectronicsLayoutResponse(
        pickup_cavities=[CavityResponse(**c.to_dict()) for c in pickup_cavities],
        control_cavities=[CavityResponse(**c.to_dict()) for c in control_cavities],
        overall_gate=overall_gate,
        total_shielding_area_mm2=round(shielding_area, 1),
        body_style=req.body_style,
    )


@router.post(
    "/electronics-layout/pickup-cavity",
    response_model=PickupCavityResponse,
    summary="Calculate single pickup cavity",
    description="""
    Calculate cavity dimensions for a single pickup.

    **Pickup types:**
    - humbucker: 50×40×45mm
    - single_coil: 90×15×45mm
    - p90: 90×50×45mm
    - mini_humbucker: 67×34×40mm
    - filtertron: 70×38×42mm
    - lipstick: 85×20×35mm
    - jazzmaster: 95×45×40mm

    Position is measured from bridge (0 = at bridge).
    """,
)
def calculate_pickup_cavity(req: PickupCavityRequest) -> PickupCavityResponse:
    """Calculate single pickup cavity."""
    cavity = compute_pickup_cavity(
        pickup_type=req.pickup_type,
        position=req.position,
        body_thickness_mm=req.body_thickness_mm,
        body_style=req.body_style,
    )
    return PickupCavityResponse(
        cavity=CavityResponse(**cavity.to_dict()),
        pickup_type=req.pickup_type,
        position=req.position,
    )


@router.post(
    "/electronics-layout/control-layout",
    response_model=ControlLayoutResponse,
    summary="Calculate control cavity layout",
    description="""
    Calculate control cavity layout with pots, switch, and jack.

    **Pot spacing:** Minimum 19mm center-to-center required for standard knobs.
    Cavity size adjusts automatically for pot count.

    **Switch types:**
    - 3way_toggle: 40×20×35mm (Les Paul style)
    - 5way_blade: 45×25×25mm (Strat style, pickguard mounted)
    - rotary: 35×35×30mm

    **Jack types:**
    - side: 35mm diameter, body edge
    - top: 25mm diameter, in control cavity
    - endpin: 15mm diameter, body end
    """,
)
def calculate_control_layout(req: ControlLayoutRequest) -> ControlLayoutResponse:
    """Calculate control layout."""
    cavities = compute_control_layout(
        pot_count=req.pot_count,
        switch_type=req.switch_type,
        jack_type=req.jack_type,
        body_style=req.body_style,
        body_thickness_mm=req.body_thickness_mm,
    )

    overall_gate = check_cavity_clearance(cavities, req.body_thickness_mm)
    shielding_area = compute_shielding_area(cavities)

    return ControlLayoutResponse(
        cavities=[CavityResponse(**c.to_dict()) for c in cavities],
        overall_gate=overall_gate,
        pot_count=req.pot_count,
        switch_type=req.switch_type,
        jack_type=req.jack_type,
        body_style=req.body_style,
        shielding_area_mm2=round(shielding_area, 1),
    )


@router.get(
    "/electronics-layout/options",
    response_model=ElectronicsOptionsResponse,
    summary="List options for electronics layout",
)
def get_electronics_options() -> ElectronicsOptionsResponse:
    """Return lists of available options for electronics layout."""
    return ElectronicsOptionsResponse(
        pickup_types=list_pickup_types(),
        switch_types=list_switch_types(),
        jack_types=list_jack_types(),
        body_styles=list_electronics_body_styles(),
    )


# ─── Build Sequence Models (CONSTRUCTION-010) ──────────────────────────────────


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


# ─── Build Sequence Endpoints (CONSTRUCTION-010) ───────────────────────────────


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

# ─── Voicing History Endpoints ───────────────────────────────────────────────

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
    - f ∝ h (frequency proportional to thickness for thin plates)
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

    Uses linear relationship: f ∝ h (for thin plates)
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

