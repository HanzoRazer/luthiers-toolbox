"""
Construction Calculator Router — Kerfing, top deflection, brace sizing.

Migrated from instrument_router.py (Phase A consolidation).

Endpoints:
- POST /kerfing — Calculate kerfing schedule for body style
- GET  /kerfing/types — List available kerfing types
- POST /top-deflection — Calculate top plate deflection (ACOUSTIC-003)
- POST /brace-sizing — Inverse brace sizing from deflection target (ACOUSTIC-004)

Total: 4 endpoints
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.calculators.kerfing_calc import (
    KerfingSpec,
    KerfingDimensions,
    compute_kerfing_schedule,
    compute_total_side_depth,
    list_kerfing_types,
    get_kerfing_type_info,
    KERFING_TYPES,
)
from app.calculators.top_deflection_calc import (
    compute_top_deflection,
    compute_plate_EI,
    compute_composite_EI,
    PlateProperties,
    BraceContribution,
    DeflectionResult,
)
from app.calculators.bracing_calc import (
    BraceSizingTarget,
    RequiredBraceSpec,
    compute_required_EI,
    compute_brace_dimensions_for_EI,
    solve_brace_sizing,
)

router = APIRouter(tags=["instrument-geometry", "construction"])


# ─── Kerfing Models ───────────────────────────────────────────────────────────

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


# ─── Top Deflection Models ────────────────────────────────────────────────────

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


# ─── Brace Sizing Models ──────────────────────────────────────────────────────

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


# ─── Kerfing Endpoints ────────────────────────────────────────────────────────

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


# ─── Top Deflection Endpoint ──────────────────────────────────────────────────

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


# ─── Brace Sizing Endpoint ────────────────────────────────────────────────────

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


__all__ = ["router"]
