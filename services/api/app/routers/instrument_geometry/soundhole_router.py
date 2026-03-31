"""
Soundhole Router — Soundhole specification and position validation.

Endpoints:
- POST /soundhole — Calculate soundhole spec (supports round, oval, spiral, fhole types)
- POST /soundhole/check-position — Check soundhole position validity
- GET  /soundhole/options — List body styles
- GET  /soundhole/body-styles — List body styles with standard diameters
- GET  /soundhole/types — List supported soundhole types

Total: 5 endpoints
"""

from __future__ import annotations

from typing import Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.calculators.soundhole_calc import (
    SoundholeSpec,
    compute_soundhole_spec,
    check_soundhole_position,
    list_body_styles,
    STANDARD_DIAMETERS_MM,
)
from app.calculators.soundhole_facade import (
    SoundholeType,
    SpiralParams,
    list_soundhole_types,
)
from app.calculators.soundhole_presets import (
    list_spiral_presets,
    SPIRAL_PRESETS,
)

router = APIRouter(tags=["instrument-geometry", "soundhole"])


# ─── Models ────────────────────────────────────────────────────────────────────

class SpiralParamsRequest(BaseModel):
    """Parameters for spiral soundhole geometry."""
    slot_width_mm: float = Field(14.0, ge=8.0, le=30.0, description="Slot width in mm (14-20mm optimal)")
    start_radius_mm: float = Field(10.0, ge=5.0, le=25.0, description="Starting radius r0 in mm")
    growth_rate_k: float = Field(0.18, ge=0.05, le=0.40, description="Growth rate k per radian")
    turns: float = Field(1.1, ge=0.5, le=2.5, description="Number of full turns")
    rotation_deg: float = Field(0.0, ge=0.0, le=360.0, description="Rotation offset in degrees")
    center_x_mm: float = Field(0.0, description="Center X position (mm from centerline)")
    center_y_mm: float = Field(0.0, description="Center Y position (mm from bridge)")


class SoundholeRequest(BaseModel):
    """Request for soundhole specification."""
    body_style: str = Field(..., description="Body style (dreadnought, om_000, parlor, classical, etc.)")
    body_length_mm: float = Field(..., gt=0, description="Body length from neck block to tail block in mm")
    custom_diameter_mm: Optional[float] = Field(None, gt=0, description="Custom diameter override in mm")
    soundhole_type: str = Field(
        "round",
        description="Soundhole type: round, oval, spiral, or fhole"
    )
    spiral_params: Optional[SpiralParamsRequest] = Field(
        None,
        description="Parameters for spiral soundhole (only used when soundhole_type='spiral')"
    )


class SoundholeResponse(BaseModel):
    """Response with soundhole specification."""
    diameter_mm: float
    position_from_neck_block_mm: float
    body_style: str
    gate: str
    notes: List[str]
    soundhole_type: str = "round"
    spiral_params: Optional[Dict] = None
    area_mm2: Optional[float] = None
    perimeter_mm: Optional[float] = None
    pa_ratio_mm_inv: Optional[float] = None


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


# ─── Endpoints ─────────────────────────────────────────────────────────────────

@router.post(
    "/soundhole",
    response_model=SoundholeResponse,
    summary="Calculate soundhole specification",
)
def calculate_soundhole(req: SoundholeRequest) -> SoundholeResponse:
    """
    Calculate soundhole specification for body style.

    Supports multiple soundhole types:
    - round: Traditional circular soundhole (default)
    - oval: Oval/elliptical (Selmer/Maccaferri style)
    - spiral: Logarithmic spiral slot (Williams 2019 acoustic research)
    - fhole: F-holes (redirects to f-hole calculator)
    """
    # Parse soundhole type
    try:
        sh_type = SoundholeType(req.soundhole_type.lower())
    except ValueError:
        sh_type = SoundholeType.ROUND

    # Convert spiral params if provided
    spiral_params = None
    if req.spiral_params and sh_type == SoundholeType.SPIRAL:
        spiral_params = SpiralParams(
            slot_width_mm=req.spiral_params.slot_width_mm,
            start_radius_mm=req.spiral_params.start_radius_mm,
            growth_rate_k=req.spiral_params.growth_rate_k,
            turns=req.spiral_params.turns,
            rotation_deg=req.spiral_params.rotation_deg,
            center_x_mm=req.spiral_params.center_x_mm,
            center_y_mm=req.spiral_params.center_y_mm,
        )

    spec: SoundholeSpec = compute_soundhole_spec(
        body_style=req.body_style,
        body_length_mm=req.body_length_mm,
        custom_diameter_mm=req.custom_diameter_mm,
        soundhole_type=sh_type,
        spiral_params=spiral_params,
    )
    return SoundholeResponse(**spec.to_dict())


@router.post(
    "/soundhole/check-position",
    response_model=SoundholePositionCheckResponse,
    summary="Check soundhole position validity",
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


@router.get(
    "/soundhole/body-styles",
    summary="List body styles with standard soundhole diameters",
)
def list_soundhole_body_styles():
    """
    List supported body styles and their standard soundhole diameters.

    Migrated from instrument_router.py — provides extended response
    with standard_diameters_mm lookup table.
    """
    return {
        "body_styles": list_body_styles(),
        "standard_diameters_mm": STANDARD_DIAMETERS_MM,
    }


@router.get(
    "/soundhole/types",
    summary="List supported soundhole types",
)
def get_soundhole_types():
    """
    List supported soundhole types for the generator dropdown.

    Returns available types: round, oval, spiral, fhole
    with descriptions and any type-specific notes.
    """
    return {
        "types": list_soundhole_types(),
        "spiral_presets": list_spiral_presets(),
    }


__all__ = ["router"]
