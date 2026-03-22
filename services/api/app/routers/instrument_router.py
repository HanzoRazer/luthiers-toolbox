"""
Wave 7: Instrument Geometry Router

Exposes endpoints for guitar instrument geometry calculations:
- Bridge location with compensation
- Compound radius profiles
- Standard guitar presets (convenience endpoints)

NOTE: Fret-specific endpoints (positions, outline, slots) moved to fret_router.py (December 2025)
See: /api/fret/table, /api/fret/board/outline, /api/fret/slots

All calculations use the instrument_geometry package.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional

# Canonical imports (updated from shims - December 2025)
from ..instrument_geometry.neck.fret_math import compute_fret_positions_mm
from ..instrument_geometry.bridge.geometry import (
    compute_bridge_location_mm,
    compute_compensation_estimate,
)
from ..instrument_geometry.neck.radius_profiles import (
    compute_compound_radius_at_fret,
)
from ..calculators.saddle_force_calc import (
    compute_saddle_force,
    SaddleForceResult,
    StringForce,
)
from ..calculators.top_deflection_calc import (
    compute_top_deflection,
    compute_plate_EI,
    compute_composite_EI,
    PlateProperties,
    BraceContribution,
    DeflectionResult,
)
from ..calculators.bracing_calc import (
    BraceSizingTarget,
    RequiredBraceSpec,
    compute_required_EI,
    compute_brace_dimensions_for_EI,
    solve_brace_sizing,
)

router = APIRouter(
    prefix="/api/instrument",
    tags=["instrument_geometry"],
)


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------
# NOTE: Fret-related models moved to fret_router.py (December 2025)
# See: /api/fret/table, /api/fret/board/outline, /api/fret/slots
# ---------------------------------------------------------------------------

class BridgeLocationRequest(BaseModel):
    """Request for bridge saddle location."""
    scale_length_mm: float = Field(..., gt=0)
    saddle_compensation_mm: Optional[float] = Field(
        default=None, 
        description="Manual compensation offset (positive = further from nut)"
    )
    string_gauge_mm: Optional[float] = Field(
        default=None,
        description="String gauge for automatic compensation calculation"
    )
    action_height_mm: Optional[float] = Field(
        default=None,
        description="Action height at 12th fret for compensation"
    )


class BridgeLocationResponse(BaseModel):
    """Response with bridge location details."""
    scale_length_mm: float
    bridge_location_mm: float
    compensation_mm: float
    notes: str


class RadiusProfileRequest(BaseModel):
    """Request for compound radius profile."""
    fret_count: int = Field(..., gt=0, le=36)
    base_radius_mm: float = Field(..., gt=0, description="Radius at nut (e.g., 184mm = 7.25 inch)")
    end_radius_mm: float = Field(..., gt=0, description="Radius at last fret (e.g., 305mm = 12 inch)")


class RadiusProfileResponse(BaseModel):
    """Response with radius at each fret position."""
    radii_mm: List[float]
    base_radius_mm: float
    end_radius_mm: float
    is_compound: bool


class RadiusAtPositionRequest(BaseModel):
    """Request for radius at arbitrary position."""
    position_mm: float = Field(..., ge=0, description="Distance from nut in mm")
    fretboard_length_mm: float = Field(..., gt=0)
    base_radius_mm: float = Field(..., gt=0)
    end_radius_mm: float = Field(..., gt=0)


class RadiusAtPositionResponse(BaseModel):
    """Response with interpolated radius."""
    position_mm: float
    radius_mm: float


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
# NOTE: Fret endpoints moved to fret_router.py (December 2025)
# - /geometry/frets → /api/fret/table
# - /geometry/fretboard → /api/fret/board/outline
# - /geometry/fret-slots → /api/fret/slots
# ---------------------------------------------------------------------------

@router.post("/geometry/bridge", response_model=BridgeLocationResponse)
def get_bridge_location(payload: BridgeLocationRequest) -> BridgeLocationResponse:
    """
    Calculate bridge saddle location with compensation.
    
    Compensation can be:
    - Manual: provided via saddle_compensation_mm
    - Automatic: calculated from string_gauge_mm and action_height_mm
    - Default: uses basic scale length (no compensation)
    """
    base_location = compute_bridge_location_mm(scale_length_mm=payload.scale_length_mm)
    
    compensation = 0.0
    notes = "No compensation applied"
    
    if payload.saddle_compensation_mm is not None:
        compensation = payload.saddle_compensation_mm
        notes = f"Manual compensation: {compensation:.2f}mm"
    elif payload.string_gauge_mm is not None and payload.action_height_mm is not None:
        # Use compute_compensation_estimate for automatic calculation
        # Heuristic: strings >= 0.4mm are typically wound
        is_wound = payload.string_gauge_mm >= 0.4
        compensation = compute_compensation_estimate(
            string_gauge_mm=payload.string_gauge_mm,
            is_wound=is_wound,
            action_mm=payload.action_height_mm,
        )
        notes = f"Calculated compensation for {payload.string_gauge_mm}mm {'wound' if is_wound else 'plain'} string, {payload.action_height_mm}mm action"
    
    return BridgeLocationResponse(
        scale_length_mm=payload.scale_length_mm,
        bridge_location_mm=base_location + compensation,
        compensation_mm=compensation,
        notes=notes,
    )


@router.post("/geometry/radius-profile", response_model=RadiusProfileResponse)
def get_radius_profile(payload: RadiusProfileRequest) -> RadiusProfileResponse:
    """
    Calculate compound radius profile for all fret positions.
    
    Returns the fretboard radius at each fret, interpolated linearly
    from base_radius (at nut) to end_radius (at last fret).
    """
    radii: List[float] = []
    for fret_index in range(payload.fret_count):
        r = compute_compound_radius_at_fret(
            fret_index=fret_index,
            total_frets=payload.fret_count,
            start_radius_mm=payload.base_radius_mm,
            end_radius_mm=payload.end_radius_mm,
        )
        radii.append(r)

    is_compound = abs(payload.base_radius_mm - payload.end_radius_mm) > 0.1

    return RadiusProfileResponse(
        radii_mm=radii,
        base_radius_mm=payload.base_radius_mm,
        end_radius_mm=payload.end_radius_mm,
        is_compound=is_compound,
    )


@router.post("/geometry/radius-at-position", response_model=RadiusAtPositionResponse)
def get_radius_at_position(payload: RadiusAtPositionRequest) -> RadiusAtPositionResponse:
    """
    Calculate fretboard radius at any arbitrary position.
    
    Useful for CNC operations that need radius at specific X coordinates
    rather than at fret positions.
    """
    # Linear interpolation of radius based on position
    ratio = payload.position_mm / payload.fretboard_length_mm
    ratio = max(0.0, min(1.0, ratio))  # Clamp to [0, 1]
    
    radius = payload.base_radius_mm + (payload.end_radius_mm - payload.base_radius_mm) * ratio
    
    return RadiusAtPositionResponse(
        position_mm=payload.position_mm,
        radius_mm=radius,
    )


# ---------------------------------------------------------------------------
# Convenience endpoints for common use cases
# ---------------------------------------------------------------------------

class StandardGuitarRequest(BaseModel):
    """Request using standard guitar presets."""
    preset: str = Field(
        ..., 
        description="Preset name: 'fender_25.5', 'gibson_24.75', 'prs_25', 'classical'"
    )
    fret_count: int = Field(default=22, gt=0, le=36)


class StandardGuitarResponse(BaseModel):
    """Complete geometry for a standard guitar configuration."""
    preset: str
    scale_length_mm: float
    fret_count: int
    nut_width_mm: float
    frets_mm: List[float]
    bridge_location_mm: float


# Standard guitar presets
GUITAR_PRESETS = {
    "fender_25.5": {
        "scale_length_mm": 647.7,  # 25.5 inches
        "nut_width_mm": 42.86,     # 1 11/16 inches
        "heel_width_mm": 56.0,
    },
    "gibson_24.75": {
        "scale_length_mm": 628.65,  # 24.75 inches
        "nut_width_mm": 43.05,      # 1.695 inches
        "heel_width_mm": 55.0,
    },
    "prs_25": {
        "scale_length_mm": 635.0,   # 25 inches
        "nut_width_mm": 42.5,
        "heel_width_mm": 55.5,
    },
    "classical": {
        "scale_length_mm": 650.0,
        "nut_width_mm": 52.0,
        "heel_width_mm": 62.0,
    },
}


@router.post("/geometry/standard-guitar", response_model=StandardGuitarResponse)
def get_standard_guitar_geometry(payload: StandardGuitarRequest) -> StandardGuitarResponse:
    """
    Get complete geometry for a standard guitar preset.
    
    Available presets:
    - fender_25.5: Fender-style 25.5" scale
    - gibson_24.75: Gibson-style 24.75" scale  
    - prs_25: PRS-style 25" scale
    - classical: Classical guitar 650mm scale
    """
    preset_key = payload.preset.lower().replace(" ", "_")
    
    if preset_key not in GUITAR_PRESETS:
        raise HTTPException(
            status_code=400, 
            detail=f"Unknown preset: {payload.preset}. Available: {list(GUITAR_PRESETS.keys())}"
        )
    
    preset = GUITAR_PRESETS[preset_key]
    
    frets = compute_fret_positions_mm(
        scale_length_mm=preset["scale_length_mm"],
        fret_count=payload.fret_count,
    )
    
    bridge = compute_bridge_location_mm(scale_length_mm=preset["scale_length_mm"])
    
    return StandardGuitarResponse(
        preset=payload.preset,
        scale_length_mm=preset["scale_length_mm"],
        fret_count=payload.fret_count,
        nut_width_mm=preset["nut_width_mm"],
        frets_mm=frets,
        bridge_location_mm=bridge,
    )


@router.get("/geometry/presets")
def list_presets():
    """List available guitar presets."""
    return {
        "presets": list(GUITAR_PRESETS.keys()),
        "details": GUITAR_PRESETS,
    }


# ---------------------------------------------------------------------------
# String Tension Calculator (CONSTRUCTION-004)
# ---------------------------------------------------------------------------

from ..calculators.string_tension import (
    StringSpec as StringSpecCalc,
    TensionResult,
    SetTensionResult,
    compute_string_tension_from_spec,
    compute_set_tension,
    get_preset_set,
    list_preset_sets,
    STRING_SETS,
    SCALE_LENGTHS_MM,
)


class StringSpecRequest(BaseModel):
    """Specification for a single string."""
    name: str = Field(..., description="String name (e.g., '1' or 'e')")
    gauge_inch: float = Field(..., gt=0, description="String diameter in inches")
    is_wound: bool = Field(..., description="True if wound string")
    note: str = Field(..., description="Note name (e.g., 'E4', 'B3')")
    frequency_hz: float = Field(..., gt=0, description="Target frequency in Hz")


class StringTensionRequest(BaseModel):
    """Request for string tension calculation."""
    scale_length_mm: float = Field(..., gt=0, description="Scale length in mm")
    string_set: Optional[str] = Field(
        default=None,
        description="Preset string set name (e.g., 'light_012', 'medium_013')"
    )
    custom_strings: Optional[List[StringSpecRequest]] = Field(
        default=None,
        description="Custom string specifications (overrides string_set)"
    )


class StringTensionResponse(BaseModel):
    """Response with tension calculations."""
    scale_length_mm: float
    set_name: str
    strings: List[dict]
    total_tension_lb: float
    total_tension_n: float


@router.post("/string-tension", response_model=StringTensionResponse)
def calculate_string_tension(payload: StringTensionRequest) -> StringTensionResponse:
    """
    Calculate string tension for a guitar string set.

    Uses the physics formula: T = (2 × f × L)² × μ

    Can use either:
    - A preset string set (light_012, medium_013, etc.)
    - Custom string specifications

    Returns tension for each string and total tension.
    Useful for bracing calculations and bridge plate sizing.
    """
    if payload.custom_strings:
        # Use custom strings
        strings = [
            StringSpecCalc(
                name=s.name,
                gauge_inch=s.gauge_inch,
                is_wound=s.is_wound,
                note=s.note,
                frequency_hz=s.frequency_hz,
            )
            for s in payload.custom_strings
        ]
        set_name = "custom"
    elif payload.string_set:
        # Use preset
        try:
            strings = get_preset_set(payload.string_set)
            set_name = payload.string_set
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    else:
        # Default to light gauge
        strings = get_preset_set("light_012")
        set_name = "light_012"

    result = compute_set_tension(strings, payload.scale_length_mm, set_name=set_name)

    return StringTensionResponse(
        scale_length_mm=result.scale_length_mm,
        set_name=result.set_name,
        strings=[
            {
                "name": s.name,
                "gauge_inch": s.gauge_inch,
                "gauge_mm": s.gauge_mm,
                "note": s.note,
                "is_wound": s.is_wound,
                "tension_lb": s.tension_lb,
                "tension_n": s.tension_n,
            }
            for s in result.strings
        ],
        total_tension_lb=result.total_tension_lb,
        total_tension_n=result.total_tension_n,
    )


@router.get("/string-tension/presets")
def list_string_presets():
    """List available string set presets and scale lengths."""
    return {
        "string_sets": list_preset_sets(),
        "scale_lengths_mm": SCALE_LENGTHS_MM,
    }


# ---------------------------------------------------------------------------
# Soundhole Calculator (GEOMETRY-002)
# ---------------------------------------------------------------------------

from ..calculators.soundhole_calc import (
    SoundholeSpec,
    compute_soundhole_spec,
    check_soundhole_position,
    list_body_styles,
    get_standard_diameter,
    STANDARD_DIAMETERS_MM,
)


class SoundholeRequest(BaseModel):
    """Request for soundhole placement and sizing."""
    body_style: str = Field(
        ...,
        description="Body style: dreadnought, om_000, parlor, classical, jumbo, concert, auditorium"
    )
    body_length_mm: float = Field(..., gt=0, description="Body length from neck block to tail block in mm")
    custom_diameter_mm: Optional[float] = Field(
        default=None,
        gt=0,
        description="Override standard diameter (optional)"
    )


class SoundholeResponse(BaseModel):
    """Response with soundhole specification."""
    diameter_mm: float
    position_from_neck_block_mm: float
    body_style: str
    gate: str
    notes: List[str]
    standard_diameter_mm: Optional[float] = None


class SoundholePositionCheckRequest(BaseModel):
    """Request for validating a specific soundhole position."""
    diameter_mm: float = Field(..., gt=0, description="Soundhole diameter in mm")
    position_mm: float = Field(..., gt=0, description="Center position from neck block in mm")
    body_length_mm: float = Field(..., gt=0, description="Total body length in mm")


class SoundholePositionCheckResponse(BaseModel):
    """Response with position validation result."""
    gate: str
    position_mm: float
    body_length_mm: float
    position_ratio: float


@router.post("/soundhole", response_model=SoundholeResponse)
def get_soundhole_spec(payload: SoundholeRequest) -> SoundholeResponse:
    """
    Calculate soundhole placement and sizing for a given body style.

    Standard placement: approximately 1/2 body length from neck block.
    Standard diameters:
    - Dreadnought: 100mm
    - OM/000: 98mm
    - Parlor: 85mm
    - Classical: 85mm
    - Jumbo: 102mm

    Returns gate status (GREEN/YELLOW/RED) with notes.
    """
    spec = compute_soundhole_spec(
        body_style=payload.body_style,
        body_length_mm=payload.body_length_mm,
        custom_diameter_mm=payload.custom_diameter_mm,
    )

    return SoundholeResponse(
        diameter_mm=spec.diameter_mm,
        position_from_neck_block_mm=spec.position_from_neck_block_mm,
        body_style=spec.body_style,
        gate=spec.gate,
        notes=spec.notes,
        standard_diameter_mm=get_standard_diameter(payload.body_style),
    )


@router.post("/soundhole/check-position", response_model=SoundholePositionCheckResponse)
def check_soundhole_position_endpoint(payload: SoundholePositionCheckRequest) -> SoundholePositionCheckResponse:
    """
    Validate a specific soundhole position.

    Checks if position is within acceptable range (45-55% of body length)
    and ensures adequate clearance from neck block and bridge area.

    Returns gate status:
    - GREEN: Position within standard range
    - YELLOW: Position acceptable but non-standard
    - RED: Position problematic (structural concerns)
    """
    gate = check_soundhole_position(
        diameter_mm=payload.diameter_mm,
        position_mm=payload.position_mm,
        body_length_mm=payload.body_length_mm,
    )

    return SoundholePositionCheckResponse(
        gate=gate,
        position_mm=payload.position_mm,
        body_length_mm=payload.body_length_mm,
        position_ratio=payload.position_mm / payload.body_length_mm,
    )


@router.get("/soundhole/body-styles")
def list_soundhole_body_styles():
    """List supported body styles and their standard soundhole diameters."""
    return {
        "body_styles": list_body_styles(),
        "standard_diameters_mm": STANDARD_DIAMETERS_MM,
    }


# ---------------------------------------------------------------------------
# Kerfing Calculator (GEOMETRY-003)
# ---------------------------------------------------------------------------

from ..calculators.kerfing_calc import (
    KerfingSpec,
    KerfingDimensions,
    compute_kerfing_schedule,
    compute_total_side_depth,
    list_kerfing_types,
    get_kerfing_type_info,
    KERFING_TYPES,
)


class KerfingDimensionsResponse(BaseModel):
    """Kerfing dimensions for a single strip."""
    width_mm: float
    height_mm: float
    kerf_spacing_mm: float
    kerf_depth_mm: float
    material: str


class KerfingRequest(BaseModel):
    """Request for kerfing schedule calculation."""
    side_depth_mm: float = Field(..., gt=0, description="Side depth from SIDE_PROFILE (without kerfing) in mm")
    body_style: str = Field(
        ...,
        description="Body style: dreadnought, om_000, parlor, classical, jumbo, archtop"
    )
    kerfing_type: Optional[str] = Field(
        default="standard_lining",
        description="Kerfing type: standard_lining, reverse_kerfing, laminate_lining, carbon_fiber, solid_lining"
    )


class KerfingResponse(BaseModel):
    """Response with complete kerfing specification."""
    kerfing_type: str
    side_depth_mm: float
    top_kerfing: KerfingDimensionsResponse
    back_kerfing: KerfingDimensionsResponse
    total_side_depth_mm: float
    flexibility_note: str


@router.post("/kerfing", response_model=KerfingResponse)
def get_kerfing_schedule(payload: KerfingRequest) -> KerfingResponse:
    """
    Calculate kerfing schedule for a guitar body.

    Kerfing adds depth to the sides at the top and back.
    It provides the gluing surface for top and back plates.

    Standard kerfing dimensions:
    - width: 6.35mm (1/4")
    - height: 7.94mm (5/16") for standard
    - kerf_spacing: 3.0mm
    - kerf_depth_ratio: 0.66 (2/3 of height)

    Available kerfing types:
    - standard_lining: height=7.94mm, flexible
    - reverse_kerfing: height=9.53mm, stiffer
    - laminate_lining: height=6.35mm, very flexible
    - carbon_fiber: height=6.35mm, rigid (no kerfs)
    - solid_lining: height=9.53mm, rigid (no kerfs)
    """
    spec = compute_kerfing_schedule(
        side_depth_mm=payload.side_depth_mm,
        body_style=payload.body_style,
        kerfing_type=payload.kerfing_type or "standard_lining",
    )

    return KerfingResponse(
        kerfing_type=spec.kerfing_type,
        side_depth_mm=spec.side_depth_mm,
        top_kerfing=KerfingDimensionsResponse(
            width_mm=spec.top_kerfing.width_mm,
            height_mm=spec.top_kerfing.height_mm,
            kerf_spacing_mm=spec.top_kerfing.kerf_spacing_mm,
            kerf_depth_mm=spec.top_kerfing.kerf_depth_mm,
            material=spec.top_kerfing.material,
        ),
        back_kerfing=KerfingDimensionsResponse(
            width_mm=spec.back_kerfing.width_mm,
            height_mm=spec.back_kerfing.height_mm,
            kerf_spacing_mm=spec.back_kerfing.kerf_spacing_mm,
            kerf_depth_mm=spec.back_kerfing.kerf_depth_mm,
            material=spec.back_kerfing.material,
        ),
        total_side_depth_mm=spec.total_side_depth_mm,
        flexibility_note=spec.flexibility_note,
    )


@router.get("/kerfing/types")
def list_kerfing_types_endpoint():
    """List available kerfing types and their specifications."""
    return {
        "kerfing_types": list_kerfing_types(),
        "specifications": KERFING_TYPES,
    }


# ---------------------------------------------------------------------------
# Tuning Machine Calculator (GEOMETRY-008)
# ---------------------------------------------------------------------------

from ..calculators.tuning_machine_calc import (
    TuningMachineSpec,
    compute_tuning_machine_spec,
    compute_required_post_height,
    check_string_tree_needed,
    compute_wrap_count,
    list_standard_post_heights,
    get_string_tree_spec,
    STRING_TREE_SPECS,
    STANDARD_POST_HEIGHTS,
)


class TuningMachineRequest(BaseModel):
    """Request for tuning machine specification."""
    headstock_angle_deg: float = Field(
        ...,
        ge=0,
        le=20,
        description="Headstock pitch angle in degrees (0 for flat/Fender, 14-17 for Gibson)"
    )
    nut_to_post_mm: float = Field(
        ...,
        gt=0,
        description="Distance from nut to tuner post center in mm"
    )
    post_height_mm: float = Field(
        ...,
        gt=0,
        description="Height of tuner post above headstock face in mm"
    )
    string_name: str = Field(
        ...,
        description="String identifier: E, A, D, G, B, e (or 6, 5, 4, 3, 2, 1)"
    )
    string_gauge_inch: Optional[float] = Field(
        default=0.010,
        gt=0,
        description="String diameter in inches (default: 0.010)"
    )


class TuningMachineResponse(BaseModel):
    """Response with tuning machine specification."""
    post_height_mm: float
    break_angle_deg: float
    string_tree_needed: bool
    string_tree_type: str
    wrap_count: float
    gate: str
    notes: List[str]


class PostHeightRequest(BaseModel):
    """Request for required post height calculation."""
    headstock_angle_deg: float = Field(..., ge=0, le=20)
    nut_to_post_mm: float = Field(..., gt=0)
    target_break_angle_deg: float = Field(default=9.0, ge=5, le=15)


class PostHeightResponse(BaseModel):
    """Response with required post height."""
    required_post_height_mm: float
    target_break_angle_deg: float
    headstock_angle_deg: float


@router.post("/tuning-machine", response_model=TuningMachineResponse)
def get_tuning_machine_spec(payload: TuningMachineRequest) -> TuningMachineResponse:
    """
    Calculate tuning machine specification for a string.

    Computes break angle, string tree recommendation, and wrap count.

    Break angle formula (angled headstock):
    break_angle = arctan(
        (nut_to_tuner × sin(headstock_angle) - post_height)
        / (nut_to_tuner × cos(headstock_angle))
    )

    String tree needed if:
    - break_angle < 7° AND string is G or B

    Minimum recommended break angle: 7-10°
    Maximum before string breakage risk: 20°
    """
    spec = compute_tuning_machine_spec(
        headstock_angle_deg=payload.headstock_angle_deg,
        nut_to_post_mm=payload.nut_to_post_mm,
        post_height_mm=payload.post_height_mm,
        string_name=payload.string_name,
        string_gauge_inch=payload.string_gauge_inch or 0.010,
    )

    return TuningMachineResponse(
        post_height_mm=spec.post_height_mm,
        break_angle_deg=spec.break_angle_deg,
        string_tree_needed=spec.string_tree_needed,
        string_tree_type=spec.string_tree_type,
        wrap_count=spec.wrap_count,
        gate=spec.gate,
        notes=spec.notes,
    )


@router.post("/tuning-machine/required-height", response_model=PostHeightResponse)
def get_required_post_height(payload: PostHeightRequest) -> PostHeightResponse:
    """
    Calculate required tuner post height to achieve target break angle.

    Useful for selecting tuning machines when designing a headstock.
    """
    required_height = compute_required_post_height(
        headstock_angle_deg=payload.headstock_angle_deg,
        nut_to_post_mm=payload.nut_to_post_mm,
        target_break_angle_deg=payload.target_break_angle_deg,
    )

    return PostHeightResponse(
        required_post_height_mm=required_height,
        target_break_angle_deg=payload.target_break_angle_deg,
        headstock_angle_deg=payload.headstock_angle_deg,
    )


@router.get("/tuning-machine/post-heights")
def list_post_heights():
    """List standard tuner post heights by brand."""
    return {
        "post_heights_mm": list_standard_post_heights(),
    }


@router.get("/tuning-machine/string-trees")
def list_string_trees():
    """List available string tree types and specifications."""
    return {
        "string_tree_types": list(STRING_TREE_SPECS.keys()),
        "specifications": STRING_TREE_SPECS,
    }


# ---------------------------------------------------------------------------
# Nut Compensation Calculator (GEOMETRY-007)
# ---------------------------------------------------------------------------

from ..calculators.nut_compensation_calc import (
    NutCompensationSpec,
    compute_nut_compensation,
    compare_nut_types,
    compute_zero_fret_positions,
    list_nut_types,
    get_nut_type_info,
    COMPENSATION_FACTORS,
)


class NutCompensationRequest(BaseModel):
    """Request for nut compensation calculation."""
    action_at_nut_mm: float = Field(
        ...,
        gt=0,
        description="String height at nut (bottom of string to fretboard) in mm"
    )
    fret_height_mm: float = Field(
        ...,
        gt=0,
        description="Height of frets above fretboard in mm (typically 0.8-1.2mm)"
    )
    scale_length_mm: float = Field(
        ...,
        gt=0,
        description="Scale length in mm"
    )
    nut_type: Optional[str] = Field(
        default="traditional",
        description="Nut type: traditional, zero_fret, or compensated"
    )


class NutCompensationResponse(BaseModel):
    """Response with nut compensation specification."""
    nut_type: str
    setback_mm: float
    intonation_error_cents: float
    gate: str
    recommendation: str


class NutCompareResponse(BaseModel):
    """Response comparing all nut types."""
    action_at_nut_mm: float
    fret_height_mm: float
    scale_length_mm: float
    comparisons: List[NutCompensationResponse]
    best_option: str


class ZeroFretPositionsRequest(BaseModel):
    """Request for zero-fret adjusted positions."""
    scale_length_mm: float = Field(..., gt=0)
    fret_count: int = Field(..., gt=0, le=36)
    zero_fret_crown_width_mm: float = Field(default=1.0, gt=0)


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


@router.post("/nut-compensation", response_model=NutCompensationResponse)
def get_nut_compensation(payload: NutCompensationRequest) -> NutCompensationResponse:
    """
    Calculate nut compensation for a given configuration.

    Traditional nut compensation formula:
      setback_mm = (action_at_nut_mm - fret_height_mm)
                   × scale_length_mm / 1000
                   × compensation_factor (0.5-0.8)

    Zero-fret: No compensation needed (open string height = fretted height)
    Compensated nut: Per-string setback (most accurate)

    Returns setback distance and estimated intonation error in cents.
    """
    spec = compute_nut_compensation(
        action_at_nut_mm=payload.action_at_nut_mm,
        fret_height_mm=payload.fret_height_mm,
        scale_length_mm=payload.scale_length_mm,
        nut_type=payload.nut_type or "traditional",
    )

    return NutCompensationResponse(
        nut_type=spec.nut_type,
        setback_mm=spec.setback_mm,
        intonation_error_cents=spec.intonation_error_cents,
        gate=spec.gate,
        recommendation=spec.recommendation,
    )


@router.post("/nut-compensation/compare", response_model=NutCompareResponse)
def compare_nut_compensation_types(payload: NutCompensationRequest) -> NutCompareResponse:
    """
    Compare all nut types for a given configuration.

    Returns compensation specs for traditional, zero_fret, and compensated nuts,
    sorted by intonation error (best first).

    Useful for deciding which nut approach to use in a build.
    """
    results = compare_nut_types(
        action_at_nut_mm=payload.action_at_nut_mm,
        fret_height_mm=payload.fret_height_mm,
        scale_length_mm=payload.scale_length_mm,
    )

    comparisons = [
        NutCompensationResponse(
            nut_type=r.nut_type,
            setback_mm=r.setback_mm,
            intonation_error_cents=r.intonation_error_cents,
            gate=r.gate,
            recommendation=r.recommendation,
        )
        for r in results
    ]

    return NutCompareResponse(
        action_at_nut_mm=payload.action_at_nut_mm,
        fret_height_mm=payload.fret_height_mm,
        scale_length_mm=payload.scale_length_mm,
        comparisons=comparisons,
        best_option=results[0].nut_type if results else "traditional",
    )


@router.post("/nut-compensation/zero-fret-positions", response_model=ZeroFretPositionsResponse)
def get_zero_fret_positions(payload: ZeroFretPositionsRequest) -> ZeroFretPositionsResponse:
    """
    Calculate fret positions adjusted for zero-fret reference.

    With a zero-fret:
    - Scale length is measured from zero-fret crown center to saddle
    - The nut becomes a string guide only (positioned behind zero-fret)
    - All fret positions are calculated from the zero-fret

    Returns positions and notes about the zero-fret system.
    """
    result = compute_zero_fret_positions(
        scale_length_mm=payload.scale_length_mm,
        fret_count=payload.fret_count,
        zero_fret_crown_width_mm=payload.zero_fret_crown_width_mm,
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


@router.get("/nut-compensation/types")
def list_nut_compensation_types():
    """List available nut types and their specifications."""
    return {
        "nut_types": list_nut_types(),
        "compensation_factors": COMPENSATION_FACTORS,
        "details": {
            nut_type: get_nut_type_info(nut_type)
            for nut_type in list_nut_types()
        },
    }


# ---------------------------------------------------------------------------
# ACOUSTIC-002: Saddle Force Decomposition
# ---------------------------------------------------------------------------


class SaddleForceRequest(BaseModel):
    """Request for saddle force calculation."""
    string_tensions_n: List[float] = Field(
        ...,
        description="Tension for each string in Newtons",
        min_length=1,
        max_length=12,
    )
    break_angles_deg: List[float] = Field(
        ...,
        description="Break angle over saddle for each string (degrees)",
        min_length=1,
        max_length=12,
    )
    body_depth_at_bridge_mm: float = Field(
        default=100.0,
        gt=0,
        description="Depth of body at bridge location (mm)",
    )
    pin_to_tailblock_mm: float = Field(
        default=250.0,
        gt=0,
        description="Distance from bridge pins to tailblock (mm)",
    )
    string_names: Optional[List[str]] = Field(
        default=None,
        description="Optional names for each string (e.g., ['E2', 'A2', ...])",
    )


class StringForceResponse(BaseModel):
    """Force contribution from a single string."""
    string_name: str
    tension_n: float
    break_angle_deg: float
    behind_angle_deg: float
    vertical_force_n: float


class SaddleForceResponse(BaseModel):
    """Response with saddle force decomposition."""
    string_forces: List[StringForceResponse]
    total_vertical_force_n: float
    total_vertical_force_lbs: float
    gate: str
    notes: List[str]


@router.post("/saddle-force", response_model=SaddleForceResponse)
def calculate_saddle_force(payload: SaddleForceRequest) -> SaddleForceResponse:
    """
    Calculate saddle force from string tensions and break angles.

    ACOUSTIC-002: Decomposes saddle break angle into vertical downbearing
    force component (bridge plate load).

    Formula: F_saddle_i = T_i × (sin(θ_front_i) + sin(θ_behind_i))

    Gate thresholds:
    - GREEN: total < 500 N (normal range)
    - YELLOW: 500 <= total < 700 N (heavy strings, monitor)
    - RED: total >= 700 N (excessive, risk of failure)
    """
    if len(payload.string_tensions_n) != len(payload.break_angles_deg):
        raise HTTPException(
            status_code=422,
            detail=f"Mismatched lengths: {len(payload.string_tensions_n)} tensions vs {len(payload.break_angles_deg)} break angles",
        )

    result = compute_saddle_force(
        string_tensions_n=payload.string_tensions_n,
        break_angles_deg=payload.break_angles_deg,
        body_depth_at_bridge_mm=payload.body_depth_at_bridge_mm,
        pin_to_tailblock_mm=payload.pin_to_tailblock_mm,
        string_names=payload.string_names,
    )

    return SaddleForceResponse(
        string_forces=[
            StringForceResponse(
                string_name=sf.string_name,
                tension_n=sf.tension_n,
                break_angle_deg=sf.break_angle_deg,
                behind_angle_deg=sf.behind_angle_deg,
                vertical_force_n=sf.vertical_force_n,
            )
            for sf in result.string_forces
        ],
        total_vertical_force_n=result.total_vertical_force_n,
        total_vertical_force_lbs=result.total_vertical_force_lbs,
        gate=result.gate,
        notes=result.notes,
    )


# ---------------------------------------------------------------------------
# ACOUSTIC-003: Top Deflection Calculator
# ---------------------------------------------------------------------------


class PlatePropertiesRequest(BaseModel):
    """Plate material and geometric properties."""
    E_L_GPa: float = Field(..., gt=0, description="Longitudinal Young's modulus (GPa)")
    E_C_GPa: float = Field(default=0.8, gt=0, description="Cross-grain Young's modulus (GPa)")
    thickness_mm: float = Field(..., gt=0, description="Plate thickness (mm)")
    length_mm: float = Field(..., gt=0, description="Body length (mm)")
    width_mm: float = Field(..., gt=0, description="Lower bout width (mm)")
    density_kg_m3: float = Field(default=400.0, gt=0, description="Wood density (kg/m³)")


class BraceContributionRequest(BaseModel):
    """Brace stiffness contribution."""
    brace_EI_Nm2: float = Field(..., ge=0, description="Brace EI from bracing_calc.py (N·m²)")
    brace_count: int = Field(default=1, ge=0, description="Number of braces")


class TopDeflectionRequest(BaseModel):
    """Request for top deflection calculation."""
    load_n: float = Field(..., gt=0, description="Vertical load at bridge (N)")
    plate: PlatePropertiesRequest
    braces: Optional[BraceContributionRequest] = Field(
        default=None,
        description="Optional brace stiffness contribution"
    )
    bridge_position_fraction: float = Field(
        default=0.63,
        ge=0.0,
        le=1.0,
        description="Bridge position as fraction of length (0=tail, 1=neck)"
    )


class TopDeflectionResponse(BaseModel):
    """Response with top deflection analysis."""
    static_deflection_mm: float
    creep_projection_mm: float
    total_projected_mm: float
    gate: str
    composite_EI_Nm2: float
    notes: List[str]


@router.post("/top-deflection", response_model=TopDeflectionResponse)
def calculate_top_deflection(payload: TopDeflectionRequest) -> TopDeflectionResponse:
    """
    Calculate top plate deflection under saddle load.

    ACOUSTIC-003: Orthotropic plate deflection using simply-supported
    beam approximation with creep projection.

    Formula:
        δ = F × a² × b² / (3 × EI × L)
        where a, b are distances from bridge to supports

    Creep adds ~35% over instrument lifetime.

    Gate thresholds:
    - GREEN: total < 1.5 mm (acceptable)
    - YELLOW: 1.5 <= total < 3.0 mm (monitor)
    - RED: total >= 3.0 mm (excessive)
    """
    # Convert request to dataclasses
    plate = PlateProperties(
        E_L_GPa=payload.plate.E_L_GPa,
        E_C_GPa=payload.plate.E_C_GPa,
        thickness_mm=payload.plate.thickness_mm,
        length_mm=payload.plate.length_mm,
        width_mm=payload.plate.width_mm,
        density_kg_m3=payload.plate.density_kg_m3,
    )

    braces = None
    if payload.braces is not None:
        braces = BraceContribution(
            brace_EI_Nm2=payload.braces.brace_EI_Nm2,
            brace_count=payload.braces.brace_count,
        )

    result = compute_top_deflection(
        load_n=payload.load_n,
        plate=plate,
        braces=braces,
        bridge_position_fraction=payload.bridge_position_fraction,
    )

    return TopDeflectionResponse(
        static_deflection_mm=result.static_deflection_mm,
        creep_projection_mm=result.creep_projection_mm,
        total_projected_mm=result.total_projected_mm,
        gate=result.gate,
        composite_EI_Nm2=result.composite_EI_Nm2,
        notes=result.notes,
    )

# ---------------------------------------------------------------------------
# ACOUSTIC-004: Inverse Brace Sizing
# ---------------------------------------------------------------------------


class BraceSizingTargetRequest(BaseModel):
    """Target deflection parameters for inverse brace sizing."""
    max_deflection_mm: float = Field(
        ...,
        gt=0,
        description="Maximum allowable total deflection with creep (mm)"
    )
    applied_load_n: float = Field(
        ...,
        gt=0,
        description="String tension load at bridge (N)"
    )
    plate_length_mm: float = Field(
        ...,
        gt=0,
        description="Body length - bridge to tail direction (mm)"
    )
    bridge_position_fraction: float = Field(
        default=0.63,
        ge=0.0,
        le=1.0,
        description="Bridge position as fraction of length"
    )
    existing_plate_EI_Nm2: float = Field(
        default=0.0,
        ge=0,
        description="Existing plate EI from top_deflection_calc (N*m^2)"
    )
    wood_species: str = Field(
        default="sitka_spruce",
        description="Wood species: sitka_spruce, engelmann_spruce, red_spruce, mahogany, maple, cedar"
    )
    brace_width_mm: float = Field(
        default=5.5,
        gt=0,
        description="Brace width (mm)"
    )
    profile_type: str = Field(
        default="parabolic",
        description="Brace profile: rectangular, parabolic, triangular"
    )
    brace_count: int = Field(
        default=2,
        ge=1,
        description="Number of braces to distribute EI across"
    )


class BraceSizingResponse(BaseModel):
    """Response with required brace dimensions."""
    required_EI_Nm2: float
    required_brace_EI_Nm2: float
    suggested_width_mm: float
    suggested_height_mm: float
    wood_species: str
    profile_type: str
    gate: str
    notes: List[str]


@router.post("/brace-sizing", response_model=BraceSizingResponse)
def calculate_brace_sizing(payload: BraceSizingTargetRequest) -> BraceSizingResponse:
    """
    Inverse brace sizing: from deflection target to required brace dimensions.

    ACOUSTIC-004: Given a maximum allowable deflection, compute the brace
    dimensions (height) needed to achieve that target.

    This is the inverse of top_deflection_calc: instead of computing
    deflection from brace dimensions, compute brace dimensions from
    deflection limit.

    Formula (inverse of simply-supported beam):
        EI = F * a^2 * b^2 / (3 * delta_max * L)
        height = cbrt(12 * EI / (E * width))  for rectangular
        height = cbrt(175 * EI / (8 * E * width))  for parabolic

    Gate thresholds (based on achievable brace height):
    - ACHIEVABLE: height <= 10mm (typical range)
    - MARGINAL: 10mm < height <= 14mm (tall but achievable)
    - NOT_ACHIEVABLE: height > 14mm (impractical, need more braces)
    """
    target = BraceSizingTarget(
        max_deflection_mm=payload.max_deflection_mm,
        applied_load_n=payload.applied_load_n,
        plate_length_mm=payload.plate_length_mm,
        bridge_position_fraction=payload.bridge_position_fraction,
        existing_plate_EI_Nm2=payload.existing_plate_EI_Nm2,
    )

    result = solve_brace_sizing(
        target=target,
        wood_species=payload.wood_species,
        brace_width_mm=payload.brace_width_mm,
        profile_type=payload.profile_type,
        brace_count=payload.brace_count,
    )

    return BraceSizingResponse(
        required_EI_Nm2=result.required_EI_Nm2,
        required_brace_EI_Nm2=result.required_brace_EI_Nm2,
        suggested_width_mm=result.suggested_width_mm,
        suggested_height_mm=result.suggested_height_mm,
        wood_species=result.wood_species,
        profile_type=result.profile_type,
        gate=result.gate,
        notes=result.notes,
    )
