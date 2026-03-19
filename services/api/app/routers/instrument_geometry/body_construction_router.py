"""
Body Construction Router — Side bending, thickness, neck/tail blocks.

Endpoints:
- POST /side-bending — Calculate bending parameters
- POST /side-thickness — Check side thickness
- GET  /side-bending/options — List species and instrument types
- POST /blocks — Compute neck/tail blocks
- GET  /blocks/options — List body styles

Total: 5 endpoints
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
)
from app.calculators.neck_block_calc import (
    compute_both_blocks,
    list_body_styles as list_block_body_styles,
)

router = APIRouter(tags=["instrument-geometry", "body-construction"])


# ─── Side Bending Models ───────────────────────────────────────────────────────

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


# ─── Block Models ──────────────────────────────────────────────────────────────

class BlocksRequest(BaseModel):
    """Request for neck and tail block calculation."""
    body_style: str = Field(
        default="dreadnought",
        description="Body style (dreadnought, om_000, parlor, classical, archtop, jumbo, concert)"
    )
    neck_heel_width_mm: Optional[float] = Field(None, gt=0, description="Neck heel width in mm")
    side_depth_at_neck_mm: Optional[float] = Field(None, gt=0, description="Side depth at neck in mm")
    side_depth_at_tail_mm: Optional[float] = Field(None, gt=0, description="Side depth at tail in mm")
    material: str = Field(default="mahogany", description="Block material")


class BlockResponse(BaseModel):
    """Response with single block specification."""
    block_type: str
    height_mm: float
    width_mm: float
    depth_mm: float
    material: str
    grain_orientation: str
    gate: str
    notes: List[str]


class BlocksResponse(BaseModel):
    """Response with both neck and tail block specifications."""
    neck: BlockResponse
    tail: BlockResponse
    body_style: str


class BlockOptionsResponse(BaseModel):
    """Response with supported body styles for block calculation."""
    body_styles: List[str]


# ─── Side Bending Endpoints ────────────────────────────────────────────────────

@router.post(
    "/side-bending",
    response_model=SideBendingResponse,
    summary="Calculate side bending parameters",
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


# ─── Block Endpoints ───────────────────────────────────────────────────────────

@router.post(
    "/blocks",
    response_model=BlocksResponse,
    summary="Calculate neck and tail block dimensions (GEOMETRY-005)",
)
def calculate_blocks(req: BlocksRequest) -> BlocksResponse:
    """Calculate neck and tail block dimensions."""
    blocks = compute_both_blocks(
        body_style=req.body_style,
        neck_heel_width_mm=req.neck_heel_width_mm,
        side_depth_at_neck_mm=req.side_depth_at_neck_mm,
        side_depth_at_tail_mm=req.side_depth_at_tail_mm,
        material=req.material,
    )
    return BlocksResponse(
        neck=BlockResponse(**blocks["neck"].to_dict()),
        tail=BlockResponse(**blocks["tail"].to_dict()),
        body_style=req.body_style,
    )


@router.get(
    "/blocks/options",
    response_model=BlockOptionsResponse,
    summary="List supported body styles for block calculation",
)
def get_block_options() -> BlockOptionsResponse:
    """Return list of supported body styles."""
    return BlockOptionsResponse(body_styles=list_block_body_styles())


__all__ = ["router"]
