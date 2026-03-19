"""
Instrument Geometry Router (GEOMETRY-010+)
===========================================

Endpoints for instrument geometry calculations:
- Side bending parameters
- Side thickness recommendations
"""

from __future__ import annotations

from typing import List

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
