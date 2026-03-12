# services/api/app/routers/instruments/guitar/electric_body_router.py

"""
Electric Body Outline Router

Provides API endpoints for generating electric guitar body outlines.
Supports Stratocaster, Les Paul, Telecaster, and other styles.

GAP-07: Strat body outline generator and related electric body generation.
"""

from typing import Dict, Any, List, Literal
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from ....generators.electric_body_generator import (
    generate_body_outline,
    list_available_styles,
    get_stratocaster_outline,
    ElectricBodyStyle,
    BodyOutlineResult,
)


router = APIRouter(
    prefix="/instruments/guitar/electric-body",
    tags=["Instruments", "Guitar", "Generators"],
)


# --- Request/Response Models ---

class BodyOutlineRequest(BaseModel):
    """Request for body outline generation."""

    style: str = Field(
        default="stratocaster",
        description="Body style: stratocaster, les_paul, telecaster, gibson_explorer, flying_v, etc."
    )
    scale: float = Field(
        default=1.0,
        ge=0.1,
        le=2.0,
        description="Scale factor (default 1.0 = full size)"
    )
    detailed: bool = Field(
        default=True,
        description="If True, return detailed outline; if False, return simplified bounding box"
    )


class StratOutlineRequest(BaseModel):
    """Request for Stratocaster outline with fret-count awareness."""

    fret_count: int = Field(
        default=22,
        ge=19,
        le=27,
        description="Number of frets (affects neck pocket notes)"
    )
    scale: float = Field(
        default=1.0,
        ge=0.1,
        le=2.0,
        description="Scale factor"
    )


class BodyOutlineResponse(BaseModel):
    """Response with body outline data."""

    style: str
    width_mm: float
    length_mm: float
    point_count: int
    centroid: Dict[str, float]
    bounding_box: Dict[str, float]
    scale_factor: float
    notes: List[str]
    points: List[tuple]


class BodyStyleInfo(BaseModel):
    """Info about an available body style."""

    id: str
    width_mm: float
    height_mm: float
    has_detailed_outline: bool


# --- Endpoints ---

@router.post("/generate", response_model=BodyOutlineResponse)
def generate_outline(request: BodyOutlineRequest) -> BodyOutlineResponse:
    """
    Generate an electric guitar body outline.

    Returns a polygon outline with points in mm, suitable for CAD/CAM.

    Supported styles:
    - **stratocaster**: Fender Stratocaster
    - **les_paul**: Gibson Les Paul
    - **telecaster**: Fender Telecaster
    - **gibson_explorer**: Gibson Explorer
    - **flying_v**: Gibson Flying V
    - **js1000**: Ibanez JS1000
    - **harmony_h44**: Harmony H44

    The detailed outline contains hundreds of points extracted from DXF files.
    Set `detailed=false` for a simple bounding box (4 points).
    """
    result = generate_body_outline(
        style=request.style,
        scale=request.scale,
        detailed=request.detailed,
    )
    return BodyOutlineResponse(**result.to_dict())


@router.post("/generate/strat")
def generate_strat_outline(request: StratOutlineRequest) -> BodyOutlineResponse:
    """
    Generate Stratocaster body outline with fret-count awareness.

    For 24-fret configurations, includes notes about neck pocket
    adjustments and pickup clearance.

    This is a convenience endpoint for the most common Strat body
    generation use case.
    """
    result = get_stratocaster_outline(
        fret_count=request.fret_count,
        scale=request.scale,
    )
    return BodyOutlineResponse(**result.to_dict())


@router.get("/styles")
def list_styles() -> Dict[str, List[BodyStyleInfo]]:
    """
    List available electric body styles.

    Returns all supported body styles with their dimensions.
    """
    styles = list_available_styles()
    return {"styles": [BodyStyleInfo(**s) for s in styles]}


@router.get("/styles/{style_id}")
def get_style_info(style_id: str) -> BodyOutlineResponse:
    """
    Get info and outline for a specific body style.

    Returns the full detailed outline for the requested style.
    """
    result = generate_body_outline(style=style_id, detailed=True)
    return BodyOutlineResponse(**result.to_dict())


@router.get("/styles/{style_id}/svg")
def get_style_svg(
    style_id: str,
    scale: float = Query(default=1.0, ge=0.1, le=2.0),
    stroke_color: str = Query(default="#333333"),
    stroke_width: float = Query(default=0.5, ge=0.1, le=5.0),
    include_centerline: bool = Query(default=False),
) -> Dict[str, Any]:
    """
    Get SVG representation of a body outline.

    Returns an SVG string that can be embedded in HTML or saved to file.
    The SVG uses mm units and is scaled to actual size.
    """
    result = generate_body_outline(style=style_id, scale=scale, detailed=True)
    svg = result.to_svg(
        stroke_color=stroke_color,
        stroke_width=stroke_width,
        include_centerline=include_centerline,
    )
    return {
        "style": style_id,
        "svg": svg,
        "width_mm": result.width_mm,
        "height_mm": result.length_mm,
    }


@router.get("/presets/24fret-strat")
def get_24fret_strat_preset() -> BodyOutlineResponse:
    """
    Get preset body outline for 24-fret Stratocaster.

    Convenience endpoint returning a full Strat outline with
    24-fret-specific notes about neck pocket adjustments.
    """
    result = get_stratocaster_outline(fret_count=24, scale=1.0)
    return BodyOutlineResponse(**result.to_dict())
