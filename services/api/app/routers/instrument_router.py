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

from typing import List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from ..calculators.nut_compensation_calc import (
    compare_nut_types,
    compute_nut_compensation,
)
from ..calculators.soundhole_calc import (
    compute_soundhole_spec,
    check_soundhole_position,
    get_standard_diameter,
)

router = APIRouter(
    prefix="/api/instrument",
    tags=["instrument_geometry"],
)


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
# Soundhole (GEOMETRY-002) — parallel
# ---------------------------------------------------------------------------


class SoundholeRequest(BaseModel):
    """Request for soundhole placement and sizing."""
    body_style: str = Field(
        ...,
        description="Body style: dreadnought, om_000, parlor, classical, jumbo, concert, auditorium",
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
    """Calculate soundhole placement and sizing for a given body style."""
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
