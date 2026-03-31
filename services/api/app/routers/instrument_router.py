# 19 endpoints migrated to split routers 2026-03-29
# 4 retained as parallel implementations pending
# schema reconciliation. See INSTRUMENT_ROUTER_OVERLAP.md
"""
Instrument router — parallel implementations only.

Most instrument geometry endpoints moved to split routers (manifest 6ffb0bf9).
This module keeps nut compensation and soundhole POST handlers until schema
reconciliation with the canonical split routes is complete.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from ..calculators.nut_compensation_calc import (
    compare_nut_types,
    compute_nut_compensation,
)
from ..calculators.soundhole_facade import (
    compute_soundhole_spec,
    check_soundhole_position,
    SoundholeType,
    SpiralParams,
    list_soundhole_types,
)
from ..calculators.soundhole_presets import (
    list_spiral_presets,
    get_standard_diameter,
)
from .instrument_geometry.tuning_machine_router import router as tuning_machine_router

router = APIRouter(
    prefix="/api/instrument",
    tags=["instrument_geometry"],
)

# Include split routers
router.include_router(tuning_machine_router)


# ---------------------------------------------------------------------------
# Nut Compensation (GEOMETRY-007) — parallel
# ---------------------------------------------------------------------------


class NutCompensationRequest(BaseModel):
    """Request for nut compensation calculation."""
    action_at_nut_mm: float = Field(
        ...,
        gt=0,
        description="String height at nut (bottom of string to fretboard) in mm",
    )
    fret_height_mm: float = Field(
        ...,
        gt=0,
        description="Height of frets above fretboard in mm (typically 0.8-1.2mm)",
    )
    scale_length_mm: float = Field(
        ...,
        gt=0,
        description="Scale length in mm",
    )
    nut_type: Optional[str] = Field(
        default="traditional",
        description="Nut type: traditional, zero_fret, or compensated",
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


@router.post("/nut-compensation", response_model=NutCompensationResponse)
def get_nut_compensation(payload: NutCompensationRequest) -> NutCompensationResponse:
    """Calculate nut compensation for a given configuration."""
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
    """Compare all nut types for a given configuration."""
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


# ---------------------------------------------------------------------------
# Soundhole (GEOMETRY-002) — supports round, oval, spiral, fhole types
# ---------------------------------------------------------------------------


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
    """Request for soundhole placement and sizing."""
    body_style: str = Field(
        ...,
        description="Body style: dreadnought, om_000, parlor, classical, jumbo, concert, auditorium, carlos_jumbo",
    )
    body_length_mm: float = Field(
        ...,
        gt=0,
        description="Body length from neck block to tail block in mm",
    )
    custom_diameter_mm: Optional[float] = Field(
        default=None,
        gt=0,
        description="Override standard diameter (optional)",
    )
    soundhole_type: str = Field(
        "round",
        description="Soundhole type: round, oval, spiral, or fhole",
    )
    spiral_params: Optional[SpiralParamsRequest] = Field(
        None,
        description="Parameters for spiral soundhole (only used when soundhole_type='spiral')",
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

    Supports multiple soundhole types:
    - round: Traditional circular soundhole (default)
    - oval: Oval/elliptical (Selmer/Maccaferri style)
    - spiral: Logarithmic spiral slot (Williams 2019 acoustic research)
    - fhole: F-holes (redirects to f-hole calculator)
    """
    # Parse soundhole type
    try:
        sh_type = SoundholeType(payload.soundhole_type.lower())
    except ValueError:
        sh_type = SoundholeType.ROUND

    # Convert spiral params if provided
    spiral_params = None
    if payload.spiral_params and sh_type == SoundholeType.SPIRAL:
        spiral_params = SpiralParams(
            slot_width_mm=payload.spiral_params.slot_width_mm,
            start_radius_mm=payload.spiral_params.start_radius_mm,
            growth_rate_k=payload.spiral_params.growth_rate_k,
            turns=payload.spiral_params.turns,
            rotation_deg=payload.spiral_params.rotation_deg,
            center_x_mm=payload.spiral_params.center_x_mm,
            center_y_mm=payload.spiral_params.center_y_mm,
        )

    spec = compute_soundhole_spec(
        body_style=payload.body_style,
        body_length_mm=payload.body_length_mm,
        custom_diameter_mm=payload.custom_diameter_mm,
        soundhole_type=sh_type,
        spiral_params=spiral_params,
    )

    return SoundholeResponse(**spec.to_dict())


@router.post("/soundhole/check-position", response_model=SoundholePositionCheckResponse)
def check_soundhole_position_endpoint(
    payload: SoundholePositionCheckRequest,
) -> SoundholePositionCheckResponse:
    """Validate a specific soundhole position."""
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


@router.get("/soundhole/types", summary="List supported soundhole types")
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
