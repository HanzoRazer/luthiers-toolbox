"""
Instrument Geometry Router (GEOMETRY-010+)
===========================================

Endpoints for instrument geometry calculations:
- Side bending parameters
- Side thickness recommendations
- Nut slot depth schedule
"""

from __future__ import annotations

from typing import List, Any, Dict, Optional

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
