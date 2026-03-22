"""
Materials Physics Router (DECOMP-001)
======================================

Endpoints for wood physics calculations:
- Side bending parameters and risk assessment
- Wood movement from humidity changes
- Safe humidity ranges

Split from instrument_geometry_router.py per BACKLOG.md DECOMP-001.
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.calculators.side_bending_calc import (
    BendingPlan,
    SideThicknessSpec,
    compute_bending_parameters,
    check_side_thickness,
    list_supported_species,
    list_instrument_types,
    compare_species_for_body,
)
from app.calculators.wood_movement_calc import (
    WoodMovementSpec,
    SafeHumidityRange,
    compute_wood_movement,
    safe_humidity_range,
    list_species as list_wood_species,
)

router = APIRouter(
    prefix="",  # Manifest adds /api/instrument prefix
    tags=["materials-physics"],
)


# ─── Request/Response Models ──────────────────────────────────────────────────

class SideBendingRequest(BaseModel):
    """Request for side bending parameters calculation."""
    species: str = Field(..., description="Wood species (e.g., 'rosewood_indian', 'mahogany_honduras')")
    side_thickness_mm: float = Field(..., gt=0, description="Side thickness in mm")
    waist_radius_mm: float = Field(..., gt=0, description="Tightest bend radius (waist) in mm")
    instrument_type: str = Field(
        default="steel_string_acoustic",
        description="Instrument type (steel_string_acoustic, classical, archtop_jazz, parlor, etc.)"
    )
    bending_method: str = Field(
        default="bending_iron",
        description="Bending method: bending_iron | fox_bender | pipe_bender"
    )


class SideBendingResponse(BaseModel):
    """Response with bending parameters, physics, and risk assessment."""
    species: str
    side_thickness_mm: float
    waist_radius_mm: float
    instrument_type: str

    # Physics-derived
    r_min_elastic_mm: float
    r_min_hot_mm: float
    temp_c: float
    lignin_tg_c: float

    # Species properties
    moisture_pct: float
    spring_back_deg: float
    density_kg_m3: int

    # Assessment
    risk: str
    notes: List[str]
    failure_modes: List[str]

    # Preparation
    pre_soak_min: int
    pre_soak_max: int
    bending_method_notes: str


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


# ─── Side Bending Endpoints ──────────────────────────────────────────────────

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
    - Recommended bending temperature (C)
    - Target moisture content (%)
    - Risk assessment (GREEN/YELLOW/RED)
    - Spring-back estimate (degrees)
    - Notes and warnings

    **Risk Gate Logic:**
    - GREEN: waist_radius >= species minimum safe radius
    - YELLOW: waist_radius >= min_radius x 0.85 (borderline)
    - RED: waist_radius < min_radius x 0.85 (cracking risk)
    """,
)
def calculate_side_bending(req: SideBendingRequest) -> SideBendingResponse:
    """Calculate side bending parameters with physics and risk assessment."""
    plan: BendingPlan = compute_bending_parameters(
        species=req.species,
        side_thickness_mm=req.side_thickness_mm,
        waist_radius_mm=req.waist_radius_mm,
        instrument_type=req.instrument_type,
        bending_method=req.bending_method,
    )
    return SideBendingResponse(**plan.to_dict())


@router.post(
    "/side-bending/compare",
    summary="Compare species for a given body and thickness",
    description="""
    Rank multiple wood species by bendability for a specific waist radius
    and side thickness. Returns GREEN/YELLOW/RED risk with temperatures and
    spring-back for each species. Useful when selecting a side wood.
    """,
)
def compare_side_bending(
    waist_radius_mm: float,
    side_thickness_mm: float,
    instrument_type: str = "steel_string_acoustic",
    species_list: Optional[List[str]] = None,
) -> List[dict]:
    """Compare species for a given body and thickness, sorted by bendability."""
    return compare_species_for_body(
        instrument_type=instrument_type,
        waist_radius_mm=waist_radius_mm,
        thickness_mm=side_thickness_mm,
        species_list=species_list,
    )


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


# ─── Wood Movement Endpoints (CONSTRUCTION-006) ──────────────────────────────

@router.post(
    "/wood-movement",
    response_model=WoodMovementResponse,
    summary="Calculate wood movement from humidity change (CONSTRUCTION-006)",
    description="""
    Calculate dimensional change from relative humidity variation.

    **Physics:**
    dW = W0 x dMC x S_r
    where:
    - dW = dimensional change (mm)
    - W0 = initial dimension (mm)
    - dMC = moisture content change (%)
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
    can move 3-6mm - cracking territory for unprotected instruments.
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
