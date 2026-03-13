# services/api/app/routers/instruments/guitar/pickup_calculator_router.py

"""
Pickup Position Calculator Router

Provides API endpoints for calculating optimal pickup placements based on
scale length, fret count, and configuration.

Endpoints:
    POST /calculate      - Calculate pickup layout
    GET  /configurations - List available configurations
    GET  /scale-lengths  - List scale length presets

GAP-04: Pickup position calculator for 24-fret Strat and other configurations.
"""

from typing import Literal, Dict, Any, List
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from ....calculators.pickup_position_calc import (
    calculate_pickup_layout,
    CONFIGURATIONS,
    SCALE_LENGTHS_MM,
    PickupLayoutResult,
)

router = APIRouter(
    prefix="/instruments/guitar/pickup-calculator",
    tags=["Instruments", "Guitar", "Calculators"],
)


# --- Request/Response Models ---

class PickupLayoutRequest(BaseModel):
    """Request for pickup layout calculation."""

    scale_length_mm: float = Field(
        default=647.7,
        ge=500.0,
        le=800.0,
        description="Scale length in mm (default: 647.7mm / 25.5\" Fender)"
    )
    fret_count: int = Field(
        default=22,
        ge=19,
        le=27,
        description="Number of frets (typically 21, 22, or 24)"
    )
    configuration: Literal["SSS", "HH", "HSS"] = Field(
        default="SSS",
        description="Pickup configuration: SSS (Strat), HH (Les Paul), HSS (Super Strat)"
    )


class PickupLayoutResponse(BaseModel):
    """Response with calculated pickup positions."""

    scale_length_mm: float
    fret_count: int
    configuration: str
    pickups: List[Dict[str, Any]]
    fret_24_position_mm: float | None
    neck_body_junction_mm: float
    notes: List[str]


# --- Endpoints ---

@router.post("/calculate", response_model=PickupLayoutResponse)
def calculate_pickups(request: PickupLayoutRequest) -> PickupLayoutResponse:
    """
    Calculate optimal pickup positions for a guitar.

    Returns positions for each pickup based on scale length, fret count,
    and configuration. Automatically adjusts neck pickup position for
    extended-range (24-fret) guitars.

    Supported configurations:
    - **SSS**: Stratocaster-style (3 single coils)
    - **HH**: Les Paul-style (2 humbuckers)
    - **HSS**: Super Strat (bridge humbucker + 2 singles)
    """
    result = calculate_pickup_layout(
        scale_length_mm=request.scale_length_mm,
        fret_count=request.fret_count,
        configuration=request.configuration,
    )
    return PickupLayoutResponse(**result.to_dict())


@router.get("/configurations")
def list_configurations() -> Dict[str, Any]:
    """
    List available pickup configurations.

    Returns configuration names with descriptions.
    """
    return {
        "configurations": [
            {"id": "SSS", "name": "Stratocaster SSS", "pickups": 3, "description": "3 single coils (neck, middle, bridge)"},
            {"id": "HH", "name": "Les Paul HH", "pickups": 2, "description": "2 humbuckers (neck, bridge)"},
            {"id": "HSS", "name": "Super Strat HSS", "pickups": 3, "description": "Bridge humbucker + 2 single coils"},
        ]
    }


@router.get("/scale-lengths")
def list_scale_lengths() -> Dict[str, Any]:
    """
    List standard scale length presets.

    Returns common scale lengths in mm with their associated guitar models.
    """
    presets = []
    for preset_id, value in SCALE_LENGTHS_MM.items():
        if isinstance(value, tuple):
            length_mm = value[0]
            notes = f"Multiscale: {value[0]}mm - {value[1]}mm"
        else:
            length_mm = value
            notes = ""

        presets.append({
            "id": preset_id,
            "length_mm": length_mm,
            "length_inches": round(length_mm / 25.4, 2),
            "notes": notes,
        })

    return {"scale_lengths": presets}


@router.get("/presets/24fret-strat")
def get_24fret_strat_preset() -> PickupLayoutResponse:
    """
    Get preset pickup layout for 24-fret Stratocaster.

    This is a convenience endpoint that returns the most common
    24-fret Strat configuration (25.5" scale, 24 frets, SSS).
    """
    result = calculate_pickup_layout(
        scale_length_mm=647.7,  # 25.5"
        fret_count=24,
        configuration="SSS",
    )
    return PickupLayoutResponse(**result.to_dict())
