"""
Instrument Geometry Router (GEOMETRY-010+)
===========================================

This is the parent router that includes domain-specific sub-routers.
Endpoints directly in this file:
- Bridge geometry (GEOMETRY-004)
- Cantilever armrest

Sub-routers (see app/routers/instrument/):
- materials_physics_router: Side bending, wood movement
- soundhole_router: Soundhole calculations
- fretwork_router: Nut slots, fret leveling, fret wire, nut compensation
- build_workflow_router: Setup cascade, blocks, build sequence, voicing
- electronics_router: Pickup cavities, control layouts

Split per BACKLOG.md DECOMP-001.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.calculators.bridge_calc import (
    BridgeSpec,
    PinPositions,
    compute_bridge_spec,
    compute_pin_positions,
    list_body_styles as list_bridge_body_styles,
)
from app.calculators.cantilever_armrest_calc import (
    ArmRestSpec,
    ArmRestSection,
    compute_armrest,
    preset_standard,
    preset_classical,
    preset_archtop,
)

# Import sub-routers
from app.routers.instrument import (
    materials_physics_router,
    soundhole_router,
    fretwork_router,
    build_workflow_router,
    electronics_router,
)

router = APIRouter(
    prefix="",  # Manifest adds /api/instrument prefix
    tags=["instrument-geometry"],
)

# Include sub-routers
router.include_router(materials_physics_router)
router.include_router(soundhole_router)
router.include_router(fretwork_router)
router.include_router(build_workflow_router)
router.include_router(electronics_router)


# ─── Bridge Geometry Models (GEOMETRY-004) ───────────────────────────────────

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


# ─── Bridge Geometry Endpoints (GEOMETRY-004) ────────────────────────────────

@router.post(
    "/bridge",
    response_model=BridgeResponse,
    summary="Calculate bridge geometry (GEOMETRY-004)",
    description="""
    Calculate bridge dimensions for a given body style.

    **Input:**
    - Body style (dreadnought, om_000, parlor, classical, archtop, jumbo)
    - Scale length (mm)
    - String count (default 6)
    - Optional custom string spacing

    **Output:**
    - String spacing at saddle (E to e)
    - Bridge dimensions (length x width)
    - Saddle slot dimensions
    - Pin spacing
    - Bridge plate dimensions
    - Material recommendation
    - Gate status (GREEN/YELLOW)

    **Standard dimensions:**
    - Dreadnought: spacing=54mm, length=170mm, width=32mm
    - OM/000: spacing=52mm, length=165mm, width=30mm
    - Parlor: spacing=50mm, length=155mm, width=28mm
    - Classical: spacing=58mm, length=180mm, width=28mm (tie block)
    - Archtop: spacing=52mm, length=95mm, width=18mm (tune-o-matic)
    """,
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
    description="""
    Calculate bridge pin X positions from centerline.

    **Input:**
    - String spacing (E to e, mm)
    - String count
    - Bridge center X position

    **Output:**
    - List of X positions (bass to treble)
    - Total span

    Pins are evenly distributed across the string spacing.
    Position[0] = low E (bass), Position[5] = high e (treble).
    """,
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


# ─── Cantilever Armrest Models ───────────────────────────────────────────────

class ArmRestSectionResponse(BaseModel):
    """A cross-section of the arm rest at a given span position."""
    t: float = Field(..., description="Normalized span position (0=heel, 1=toe)")
    h_total_mm: float = Field(..., description="Total height at this section")
    theta_deg: float = Field(..., description="Face angle in degrees")
    h_block_mm: float = Field(..., description="Block height (below veneer)")
    x_overhang_mm: float = Field(..., description="Overhang from side of guitar")
    w_glue_mm: float = Field(..., description="Glue contact width")
    face_length_mm: float = Field(..., description="Face panel length")
    total_width_mm: float = Field(..., description="Total width of arm rest")


class CantileverArmrestRequest(BaseModel):
    """Request for cantilever arm rest geometry calculation."""
    preset: Optional[str] = Field(
        None,
        description="Use preset: 'standard', 'classical', or 'archtop'. Overrides other params if set."
    )
    span_mm: float = Field(140.0, gt=0, description="Total span along the bout edge")
    t_apex: float = Field(0.38, ge=0, le=1, description="Normalized position of apex (0-1)")
    h_max_mm: float = Field(14.0, gt=0, description="Maximum height at apex")
    theta_max_deg: float = Field(43.0, ge=0, le=90, description="Maximum face angle in degrees")
    t_veneer_mm: float = Field(3.0, ge=0, description="Veneer thickness")
    w_glue_max_mm: float = Field(22.0, gt=0, description="Maximum glue contact width")
    r_edge_mm: float = Field(10.0, ge=0, description="Edge rounding radius")
    r_lower_bout_mm: float = Field(200.0, gt=0, description="Lower bout radius for curvature")
    n_stations: int = Field(11, ge=3, le=51, description="Number of cross-sections to compute")


class CantileverArmrestResponse(BaseModel):
    """Response with complete arm rest geometry and sections."""
    warnings: List[str]
    sections: List[ArmRestSectionResponse]
    apex_section: ArmRestSectionResponse
    max_overhang_mm: float
    max_total_width_mm: float
    face_length_apex_mm: float
    spec: Dict[str, Any] = Field(..., description="Input spec used for computation")


# ─── Cantilever Armrest Endpoints ────────────────────────────────────────────

@router.post(
    "/cantilever-armrest",
    response_model=CantileverArmrestResponse,
    summary="Compute cantilever arm rest geometry",
    description="Calculate ruled surface geometry for a cantilever-style acoustic guitar arm rest. "
                "Supports presets (standard, classical, archtop) or custom parameters.",
)
def compute_cantilever_armrest(req: CantileverArmrestRequest) -> CantileverArmrestResponse:
    """
    Compute parametric geometry for a cantilever arm rest.

    The arm rest is an additive piece that sits on top of the guitar's
    lower bout corner, providing ergonomic forearm support.
    """
    # Use preset if specified
    if req.preset:
        preset_map = {
            "standard": preset_standard,
            "classical": preset_classical,
            "archtop": preset_archtop,
        }
        preset_fn = preset_map.get(req.preset.lower())
        if not preset_fn:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=400,
                detail=f"Unknown preset: {req.preset}. Valid: standard, classical, archtop"
            )
        spec = preset_fn()
    else:
        spec = ArmRestSpec(
            span_mm=req.span_mm,
            t_apex=req.t_apex,
            h_max_mm=req.h_max_mm,
            theta_max_deg=req.theta_max_deg,
            t_veneer_mm=req.t_veneer_mm,
            w_glue_max_mm=req.w_glue_max_mm,
            r_edge_mm=req.r_edge_mm,
            r_lower_bout_mm=req.r_lower_bout_mm,
        )

    result = compute_armrest(spec, n_stations=req.n_stations)

    def section_to_response(s: ArmRestSection) -> ArmRestSectionResponse:
        return ArmRestSectionResponse(
            t=s.t,
            h_total_mm=round(s.h_total_mm, 3),
            theta_deg=round(s.theta_deg, 2),
            h_block_mm=round(s.h_block_mm, 3),
            x_overhang_mm=round(s.x_overhang_mm, 3),
            w_glue_mm=round(s.w_glue_mm, 3),
            face_length_mm=round(s.face_length_mm, 3),
            total_width_mm=round(s.total_width_mm, 3),
        )

    return CantileverArmrestResponse(
        warnings=result.warnings,
        sections=[section_to_response(s) for s in result.sections],
        apex_section=section_to_response(result.apex_section),
        max_overhang_mm=round(result.max_overhang_mm, 3),
        max_total_width_mm=round(result.max_total_width_mm, 3),
        face_length_apex_mm=round(result.face_length_apex_mm, 3),
        spec={
            "span_mm": spec.span_mm,
            "t_apex": spec.t_apex,
            "h_max_mm": spec.h_max_mm,
            "theta_max_deg": spec.theta_max_deg,
            "t_veneer_mm": spec.t_veneer_mm,
            "w_glue_max_mm": spec.w_glue_max_mm,
            "r_edge_mm": spec.r_edge_mm,
            "r_lower_bout_mm": spec.r_lower_bout_mm,
        },
    )


@router.get(
    "/cantilever-armrest/presets",
    response_model=Dict[str, Dict[str, Any]],
    summary="List arm rest presets",
)
def list_armrest_presets() -> Dict[str, Dict[str, Any]]:
    """Return available arm rest presets with their parameters."""
    presets = {
        "standard": preset_standard(),
        "classical": preset_classical(),
        "archtop": preset_archtop(),
    }
    return {
        name: {
            "span_mm": p.span_mm,
            "t_apex": p.t_apex,
            "h_max_mm": p.h_max_mm,
            "theta_max_deg": p.theta_max_deg,
            "t_veneer_mm": p.t_veneer_mm,
            "w_glue_max_mm": p.w_glue_max_mm,
            "r_edge_mm": p.r_edge_mm,
            "r_lower_bout_mm": p.r_lower_bout_mm,
        }
        for name, p in presets.items()
    }
