"""
Fretwork Router (DECOMP-001)
============================

Endpoints for fret-related calculations:
- Nut slot schedule
- Fret leveling analysis
- Fret wire recommendations
- Nut compensation

Split from instrument_geometry_router.py per BACKLOG.md DECOMP-001.
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
from app.calculators.nut_comp_calc import (
    NutCompSpec,
    compute_nut_compensation,
    compare_nut_types,
)

router = APIRouter(
    prefix="",  # Manifest adds /api/instrument prefix
    tags=["fretwork"],
)


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


# ─── Fret Leveling Models ─────────────────────────────────────────────────────

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


# ─── Nut Compensation Models ──────────────────────────────────────────────────

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
    comp_mm = (nut_width / 2) x (1 - cos(break_angle)) + stretch_factor
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
    - vintage_narrow: 1.65x0.89mm (classic vintage)
    - medium: 2.06x1.19mm (versatile)
    - medium_jumbo: 2.54x1.40mm (modern)
    - jumbo: 2.79x1.52mm (easy bending)
    - extra_jumbo: 2.90x1.65mm (shred)
    - evo_6105: 2.29x1.14mm (gold, hypoallergenic)
    - stainless_6105: 2.29x1.14mm (hardest, most durable)
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
