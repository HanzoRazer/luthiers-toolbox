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
from app.calculators.setup_cascade import (
    SetupState,
    SetupCascadeResult,
    SetupIssue,
    evaluate_setup,
    suggest_adjustments,
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

