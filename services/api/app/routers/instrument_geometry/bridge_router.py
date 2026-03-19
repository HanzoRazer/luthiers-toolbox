"""
Bridge Router — Bridge geometry and pin positions.

Endpoints:
- POST /bridge — Calculate bridge spec
- POST /bridge/pin-positions — Calculate bridge pin positions
- GET  /bridge/options — List body styles

Total: 3 endpoints
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.calculators.bridge_calc import (
    BridgeSpec,
    PinPositions,
    compute_bridge_spec,
    compute_pin_positions,
    list_body_styles as list_bridge_body_styles,
)

router = APIRouter(tags=["instrument-geometry", "bridge"])


# ─── Models ────────────────────────────────────────────────────────────────────

class BridgeRequest(BaseModel):
    """Request for bridge geometry calculation."""
    body_style: str = Field(..., description="Body style (dreadnought, om_000, parlor, classical, archtop, jumbo)")
    scale_length_mm: float = Field(..., gt=0, description="Scale length in mm")
    string_count: int = Field(default=6, ge=1, le=12, description="Number of strings")
    custom_spacing_mm: Optional[float] = Field(None, gt=0, description="Custom string spacing override in mm")


class BridgeResponse(BaseModel):
    """Response with bridge geometry specification."""
    body_style: str
    string_spacing_mm: float
    bridge_length_mm: float
    bridge_width_mm: float
    saddle_slot_width_mm: float
    saddle_slot_depth_mm: float
    pin_spacing_mm: float
    bridge_plate_length_mm: float
    bridge_plate_width_mm: float
    material: str
    gate: str
    string_count: int
    notes: List[str]


class PinPositionsRequest(BaseModel):
    """Request for bridge pin positions calculation."""
    string_spacing_mm: float = Field(..., gt=0, description="E-to-e string spacing in mm")
    string_count: int = Field(default=6, ge=1, le=12, description="Number of strings")
    bridge_center_x: float = Field(default=0.0, description="X position of bridge center")


class PinPositionsResponse(BaseModel):
    """Response with bridge pin positions."""
    positions_mm: List[float]
    string_spacing_mm: float
    string_count: int
    total_span_mm: float


class BridgeOptionsResponse(BaseModel):
    """Response with supported body styles for bridge calculation."""
    body_styles: List[str]


# ─── Endpoints ─────────────────────────────────────────────────────────────────

@router.post(
    "/bridge",
    response_model=BridgeResponse,
    summary="Calculate bridge geometry (GEOMETRY-004)",
)
def calculate_bridge(req: BridgeRequest) -> BridgeResponse:
    """Calculate bridge geometry for body style."""
    spec: BridgeSpec = compute_bridge_spec(
        body_style=req.body_style,
        scale_length_mm=req.scale_length_mm,
        string_count=req.string_count,
        custom_spacing_mm=req.custom_spacing_mm,
    )
    return BridgeResponse(**spec.to_dict())


@router.post(
    "/bridge/pin-positions",
    response_model=PinPositionsResponse,
    summary="Calculate bridge pin positions",
)
def calculate_pin_positions(req: PinPositionsRequest) -> PinPositionsResponse:
    """Calculate bridge pin positions."""
    result: PinPositions = compute_pin_positions(
        string_spacing_mm=req.string_spacing_mm,
        string_count=req.string_count,
        bridge_center_x=req.bridge_center_x,
    )
    return PinPositionsResponse(**result.to_dict())


@router.get(
    "/bridge/options",
    response_model=BridgeOptionsResponse,
    summary="List supported body styles for bridge calculation",
)
def get_bridge_options() -> BridgeOptionsResponse:
    """Return list of supported body styles."""
    return BridgeOptionsResponse(body_styles=list_bridge_body_styles())


__all__ = ["router"]
