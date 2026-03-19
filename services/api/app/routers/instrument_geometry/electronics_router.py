"""
Electronics Layout Router — Pickup cavities, control layouts.

Endpoints:
- POST /electronics-layout — Calculate complete electronics layout
- POST /electronics-layout/pickup-cavity — Calculate single pickup cavity
- POST /electronics-layout/control-layout — Calculate control layout
- GET  /electronics-layout/options — List options

Total: 4 endpoints
"""

from __future__ import annotations

from typing import List

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.calculators.electronics_layout_calc import (
    CavitySpec,
    compute_pickup_cavity,
    compute_control_layout,
    check_cavity_clearance,
    compute_shielding_area,
    list_pickup_types,
    list_switch_types,
    list_jack_types,
    list_body_styles as list_electronics_body_styles,
)

router = APIRouter(tags=["instrument-geometry", "electronics"])


# ─── Models ────────────────────────────────────────────────────────────────────

class PickupCavityRequest(BaseModel):
    """Request for pickup cavity calculation."""
    pickup_type: str = Field(
        ...,
        description="Pickup type (humbucker, single_coil, p90, mini_humbucker, filtertron, lipstick, jazzmaster)"
    )
    position: str = Field(default="bridge", description="Position (neck, middle, bridge)")
    body_thickness_mm: float = Field(default=45.0, gt=0, description="Body thickness at pickup location in mm")
    body_style: str = Field(default="default", description="Body style for position reference")


class CavityResponse(BaseModel):
    """Response with cavity specification."""
    component: str
    length_mm: float
    width_mm: float
    depth_mm: float
    position_x_mm: float
    position_y_mm: float
    clearance_mm: float
    gate: str
    notes: List[str]


class PickupCavityResponse(BaseModel):
    """Response with pickup cavity specification."""
    cavity: CavityResponse
    pickup_type: str
    position: str


class ControlLayoutRequest(BaseModel):
    """Request for control layout calculation."""
    pot_count: int = Field(default=4, ge=1, le=6, description="Number of potentiometers (1-6)")
    switch_type: str = Field(default="3way_toggle", description="Switch type (3way_toggle, 5way_blade, rotary)")
    jack_type: str = Field(default="side", description="Jack type (side, top, endpin)")
    body_style: str = Field(default="les_paul", description="Body style")
    body_thickness_mm: float = Field(default=45.0, gt=0, description="Body thickness in mm")


class ControlLayoutResponse(BaseModel):
    """Response with complete control layout."""
    cavities: List[CavityResponse]
    overall_gate: str
    pot_count: int
    switch_type: str
    jack_type: str
    body_style: str
    shielding_area_mm2: float


class ElectronicsLayoutRequest(BaseModel):
    """Combined request for full electronics layout."""
    pickups: List[PickupCavityRequest] = Field(default_factory=list, description="List of pickups to include")
    pot_count: int = Field(default=4, ge=1, le=6)
    switch_type: str = Field(default="3way_toggle")
    jack_type: str = Field(default="side")
    body_style: str = Field(default="les_paul")
    body_thickness_mm: float = Field(default=45.0, gt=0)


class ElectronicsLayoutResponse(BaseModel):
    """Response with complete electronics layout."""
    pickup_cavities: List[CavityResponse]
    control_cavities: List[CavityResponse]
    overall_gate: str
    total_shielding_area_mm2: float
    body_style: str


class ElectronicsOptionsResponse(BaseModel):
    """Response with available options for electronics layout."""
    pickup_types: List[str]
    switch_types: List[str]
    jack_types: List[str]
    body_styles: List[str]


# ─── Endpoints ─────────────────────────────────────────────────────────────────

@router.post(
    "/electronics-layout",
    response_model=ElectronicsLayoutResponse,
    summary="Calculate complete electronics layout (CONSTRUCTION-008)",
)
def calculate_electronics_layout(req: ElectronicsLayoutRequest) -> ElectronicsLayoutResponse:
    """Calculate complete electronics layout."""
    all_cavities: List[CavitySpec] = []

    # Compute pickup cavities
    pickup_cavities: List[CavitySpec] = []
    for pickup_req in req.pickups:
        cavity = compute_pickup_cavity(
            pickup_type=pickup_req.pickup_type,
            position=pickup_req.position,
            body_thickness_mm=req.body_thickness_mm,
            body_style=req.body_style,
        )
        pickup_cavities.append(cavity)
        all_cavities.append(cavity)

    # Compute control layout
    control_cavities = compute_control_layout(
        pot_count=req.pot_count,
        switch_type=req.switch_type,
        jack_type=req.jack_type,
        body_style=req.body_style,
        body_thickness_mm=req.body_thickness_mm,
    )
    all_cavities.extend(control_cavities)

    # Check overall clearance
    overall_gate = check_cavity_clearance(all_cavities, req.body_thickness_mm)

    # Calculate shielding area
    shielding_area = compute_shielding_area(all_cavities)

    return ElectronicsLayoutResponse(
        pickup_cavities=[CavityResponse(**c.to_dict()) for c in pickup_cavities],
        control_cavities=[CavityResponse(**c.to_dict()) for c in control_cavities],
        overall_gate=overall_gate,
        total_shielding_area_mm2=round(shielding_area, 1),
        body_style=req.body_style,
    )


@router.post(
    "/electronics-layout/pickup-cavity",
    response_model=PickupCavityResponse,
    summary="Calculate single pickup cavity",
)
def calculate_pickup_cavity(req: PickupCavityRequest) -> PickupCavityResponse:
    """Calculate single pickup cavity."""
    cavity = compute_pickup_cavity(
        pickup_type=req.pickup_type,
        position=req.position,
        body_thickness_mm=req.body_thickness_mm,
        body_style=req.body_style,
    )
    return PickupCavityResponse(
        cavity=CavityResponse(**cavity.to_dict()),
        pickup_type=req.pickup_type,
        position=req.position,
    )


@router.post(
    "/electronics-layout/control-layout",
    response_model=ControlLayoutResponse,
    summary="Calculate control cavity layout",
)
def calculate_control_layout(req: ControlLayoutRequest) -> ControlLayoutResponse:
    """Calculate control layout."""
    cavities = compute_control_layout(
        pot_count=req.pot_count,
        switch_type=req.switch_type,
        jack_type=req.jack_type,
        body_style=req.body_style,
        body_thickness_mm=req.body_thickness_mm,
    )

    overall_gate = check_cavity_clearance(cavities, req.body_thickness_mm)
    shielding_area = compute_shielding_area(cavities)

    return ControlLayoutResponse(
        cavities=[CavityResponse(**c.to_dict()) for c in cavities],
        overall_gate=overall_gate,
        pot_count=req.pot_count,
        switch_type=req.switch_type,
        jack_type=req.jack_type,
        body_style=req.body_style,
        shielding_area_mm2=round(shielding_area, 1),
    )


@router.get(
    "/electronics-layout/options",
    response_model=ElectronicsOptionsResponse,
    summary="List options for electronics layout",
)
def get_electronics_options() -> ElectronicsOptionsResponse:
    """Return lists of available options for electronics layout."""
    return ElectronicsOptionsResponse(
        pickup_types=list_pickup_types(),
        switch_types=list_switch_types(),
        jack_types=list_jack_types(),
        body_styles=list_electronics_body_styles(),
    )


__all__ = ["router"]
