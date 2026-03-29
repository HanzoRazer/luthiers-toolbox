"""
Nut & Fret Router — Nut slots, compensation, fret leveling, fret wire selection.

Endpoints:
- POST /nut-slots — Calculate nut slot schedule
- GET  /nut-slots/options — List fret types and string sets
- POST /nut-compensation — Calculate nut compensation
- POST /nut-compensation/compare — Compare traditional vs zero-fret
- POST /nut-compensation/zero-fret-positions — Calculate zero-fret adjusted positions
- GET  /nut-compensation/types — List nut types and specifications
- POST /fret-leveling — Analyze fret heights
- POST /fret-leveling/radius — Calculate leveling radius
- POST /fret-wire/recommend — Get fret wire recommendations
- GET  /fret-wire/catalog — Full fret wire catalog
- GET  /fret-wire/options — List fret wire options

Total: 11 endpoints
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.calculators.nut_slot_calc import (
    NutSlotSpec,
    compute_nut_slot_schedule,
    list_fret_types,
    list_string_sets,
    get_string_set,
)
from app.calculators.nut_comp_calc import (
    NutCompSpec,
    compute_nut_compensation,
    compare_nut_types,
)
from app.calculators.nut_compensation_calc import (
    compute_zero_fret_positions,
    list_nut_types,
    get_nut_type_info,
    COMPENSATION_FACTORS,
)
from app.calculators.fret_leveling_calc import (
    LevelingPlan,
    analyze_fret_heights,
    compute_leveling_radius,
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
)

router = APIRouter(tags=["instrument-geometry", "nut-fret"])


# ─── Nut Slot Models ───────────────────────────────────────────────────────────

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


# ─── Nut Compensation Models ───────────────────────────────────────────────────

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


class ZeroFretPositionsRequest(BaseModel):
    """Request for zero-fret adjusted positions."""
    scale_length_mm: float = Field(..., gt=0, description="Scale length in mm")
    fret_count: int = Field(..., gt=0, le=36, description="Number of frets")
    zero_fret_crown_width_mm: float = Field(default=1.0, gt=0, description="Zero fret crown width in mm")


class ZeroFretPositionsResponse(BaseModel):
    """Response with zero-fret adjusted positions."""
    zero_fret_position_mm: float
    nut_guide_position_mm: float
    nut_guide_offset_mm: float
    crown_offset_mm: float
    fret_positions_mm: List[float]
    fret_count: int
    scale_length_mm: float
    notes: List[str]


# ─── Fret Leveling Models ──────────────────────────────────────────────────────

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


# ─── Fret Wire Models ──────────────────────────────────────────────────────────

class FretWireRecommendRequest(BaseModel):
    """Request for fret wire recommendation."""
    playing_style: str = Field(default="flatpick", description="Playing style")
    fretboard_material: str = Field(default="rosewood", description="Fretboard material")
    neck_profile: str = Field(default="C", description="Neck profile shape")
    string_gauge: str = Field(default="medium", description="String gauge category")


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


# ─── Nut Slot Endpoints ────────────────────────────────────────────────────────

@router.post(
    "/nut-slots",
    response_model=NutSlotsResponse,
    summary="Calculate nut slot schedule",
)
def calculate_nut_slots(req: NutSlotsRequest) -> NutSlotsResponse:
    """Calculate nut slot schedule for string set."""
    if req.string_set:
        string_set = [{"name": s.name, "gauge_inch": s.gauge_inch} for s in req.string_set]
    elif req.preset_name:
        string_set = get_string_set(req.preset_name)
    else:
        string_set = get_string_set("light_acoustic_012")

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


# ─── Nut Compensation Endpoints ────────────────────────────────────────────────

@router.post(
    "/nut-compensation",
    response_model=NutCompensationResponse,
    summary="Calculate nut compensation",
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
)
def compare_nut_compensation(req: NutComparisonRequest) -> NutComparisonResponse:
    """Compare traditional nut vs zero-fret."""
    comparison = compare_nut_types(
        scale_length_mm=req.scale_length_mm,
        nut_width_mm=req.nut_width_mm,
        break_angle_deg=req.break_angle_deg,
    )
    return NutComparisonResponse(**comparison)


@router.post(
    "/nut-compensation/zero-fret-positions",
    response_model=ZeroFretPositionsResponse,
    summary="Calculate zero-fret adjusted positions",
)
def get_zero_fret_positions(req: ZeroFretPositionsRequest) -> ZeroFretPositionsResponse:
    """
    Calculate fret positions adjusted for zero-fret reference.

    With a zero-fret:
    - Scale length is measured from zero-fret crown center to saddle
    - The nut becomes a string guide only (positioned behind zero-fret)
    - All fret positions are calculated from the zero-fret

    Migrated from instrument_router.py.
    """
    result = compute_zero_fret_positions(
        scale_length_mm=req.scale_length_mm,
        fret_count=req.fret_count,
        zero_fret_crown_width_mm=req.zero_fret_crown_width_mm,
    )
    return ZeroFretPositionsResponse(
        zero_fret_position_mm=result["zero_fret_position_mm"],
        nut_guide_position_mm=result["nut_guide_position_mm"],
        nut_guide_offset_mm=result["nut_guide_offset_mm"],
        crown_offset_mm=result["crown_offset_mm"],
        fret_positions_mm=result["fret_positions_mm"],
        fret_count=result["fret_count"],
        scale_length_mm=result["scale_length_mm"],
        notes=result["notes"],
    )


@router.get(
    "/nut-compensation/types",
    summary="List available nut types and specifications",
)
def list_nut_compensation_types():
    """
    List available nut types and their specifications.

    Returns nut types, compensation factors, and detailed info for each type.
    Migrated from instrument_router.py.
    """
    return {
        "nut_types": list_nut_types(),
        "compensation_factors": COMPENSATION_FACTORS,
        "details": {
            nut_type: get_nut_type_info(nut_type)
            for nut_type in list_nut_types()
        },
    }


# ─── Fret Leveling Endpoints ───────────────────────────────────────────────────

@router.post(
    "/fret-leveling",
    response_model=FretLevelingResponse,
    summary="Analyze fret heights for leveling",
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


# ─── Fret Wire Endpoints ───────────────────────────────────────────────────────

@router.post(
    "/fret-wire/recommend",
    response_model=FretWireRecommendResponse,
    summary="Get fret wire recommendations",
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


__all__ = ["router"]
