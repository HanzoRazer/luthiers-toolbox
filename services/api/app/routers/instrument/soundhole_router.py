"""
Soundhole Router (DECOMP-001)
=============================

Endpoints for soundhole calculations:
- Soundhole diameter and position
- Position validation
- Body style options

Split from instrument_geometry_router.py per BACKLOG.md DECOMP-001.
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.calculators.soundhole_calc import (
    SoundholeSpec,
    compute_soundhole_spec,
    check_soundhole_position,
    list_body_styles,
)

router = APIRouter(
    prefix="",  # Manifest adds /api/instrument prefix
    tags=["soundhole"],
)


# ─── Request/Response Models ──────────────────────────────────────────────────

class SoundholeRequest(BaseModel):
    """Request for soundhole specification."""
    body_style: str = Field(..., description="Body style (dreadnought, om_000, parlor, classical, etc.)")
    body_length_mm: float = Field(..., gt=0, description="Body length from neck block to tail block in mm")
    custom_diameter_mm: Optional[float] = Field(None, gt=0, description="Custom diameter override in mm")


class SoundholeResponse(BaseModel):
    """Response with soundhole specification."""
    diameter_mm: float
    position_from_neck_block_mm: float
    body_style: str
    gate: str
    notes: List[str]


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


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.post(
    "/soundhole",
    response_model=SoundholeResponse,
    summary="Calculate soundhole specification",
    description="""
    Calculate soundhole diameter and position for a given body style.

    **Input:**
    - Body style (dreadnought, om_000, parlor, classical, etc.)
    - Body length (mm)
    - Optional custom diameter override

    **Output:**
    - Diameter (mm)
    - Position from neck block (mm)
    - Gate status (GREEN/YELLOW/RED)
    - Notes and warnings

    **Standard diameters:**
    - Dreadnought: 100mm
    - OM/000: 98mm
    - Parlor: 85mm
    - Classical: 85mm
    """,
)
def calculate_soundhole(req: SoundholeRequest) -> SoundholeResponse:
    """Calculate soundhole specification for body style."""
    spec: SoundholeSpec = compute_soundhole_spec(
        body_style=req.body_style,
        body_length_mm=req.body_length_mm,
        custom_diameter_mm=req.custom_diameter_mm,
    )
    return SoundholeResponse(**spec.to_dict())


@router.post(
    "/soundhole/check-position",
    response_model=SoundholePositionCheckResponse,
    summary="Check soundhole position validity",
    description="""
    Validate a soundhole position against body proportions.

    **Position rules:**
    - Should be 45-55% of body length from neck block
    - Front edge must clear neck block by at least 20mm
    - Rear edge must leave room for bracing (40mm from tail)
    """,
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
