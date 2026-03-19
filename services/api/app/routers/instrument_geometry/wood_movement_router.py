"""
Wood Movement Router — Wood movement from humidity changes.

Endpoints:
- POST /wood-movement — Calculate wood movement
- POST /wood-movement/safe-range — Calculate safe humidity range
- GET  /wood-movement/species — List wood species

Total: 3 endpoints
"""

from __future__ import annotations

from typing import List

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.calculators.wood_movement_calc import (
    WoodMovementSpec,
    SafeHumidityRange,
    compute_wood_movement,
    safe_humidity_range,
    list_species as list_wood_species,
)

router = APIRouter(tags=["instrument-geometry", "wood-movement"])


# ─── Models ────────────────────────────────────────────────────────────────────

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


# ─── Endpoints ─────────────────────────────────────────────────────────────────

@router.post(
    "/wood-movement",
    response_model=WoodMovementResponse,
    summary="Calculate wood movement from humidity change (CONSTRUCTION-006)",
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


__all__ = ["router"]
