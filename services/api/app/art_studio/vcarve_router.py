# services/api/app/art_studio/vcarve_router.py

"""
Art Studio VCarve Router

FastAPI endpoints for SVG → toolpath → G-code conversion.

Endpoints:
- POST /preview: Parse SVG and return stats
- POST /gcode: Generate G-code from SVG
"""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .svg_ingest_service import (
    parse_svg_to_polylines,
    normalize_polylines,
    polyline_stats,
)
from ..toolpath.vcarve_toolpath import (
    VCarveToolpathParams,
    build_vcarve_mlpaths_from_svg,
    svg_to_naive_gcode,
)

router = APIRouter()


# --------------------------------------------------------------------- #
# Request/Response Models
# --------------------------------------------------------------------- #


class VCarvePreviewRequest(BaseModel):
    """Request model for VCarve preview."""

    svg: str = Field(..., description="SVG document as text")
    normalize: bool = Field(
        default=True,
        description="Whether to normalize coordinates to (0,0)"
    )


class VCarvePreviewResponse(BaseModel):
    """Response model for VCarve preview."""

    stats: Dict[str, Any] = Field(
        ..., description="Statistics about the parsed geometry"
    )
    normalized: bool = Field(
        ..., description="Whether coordinates were normalized"
    )


class VCarveGCodeRequest(BaseModel):
    """Request model for VCarve G-code generation."""

    svg: str = Field(..., description="SVG document as text")
    bit_angle_deg: float = Field(
        default=60.0, ge=10.0, le=180.0,
        description="V-bit angle in degrees"
    )
    depth_mm: float = Field(
        default=1.5, ge=0.1, le=10.0,
        description="Cutting depth in mm"
    )
    safe_z_mm: float = Field(
        default=5.0, ge=1.0, le=50.0,
        description="Safe Z height for rapids"
    )
    feed_rate_mm_min: float = Field(
        default=800.0, ge=100.0, le=5000.0,
        description="Cutting feed rate in mm/min"
    )
    plunge_rate_mm_min: float = Field(
        default=300.0, ge=50.0, le=2000.0,
        description="Plunge feed rate in mm/min"
    )


class VCarveGCodeResponse(BaseModel):
    """Response model for VCarve G-code generation."""

    gcode: str = Field(..., description="Generated G-code")


# --------------------------------------------------------------------- #
# Endpoints
# --------------------------------------------------------------------- #


@router.post("/preview", response_model=VCarvePreviewResponse)
async def preview_vcarve(req: VCarvePreviewRequest) -> VCarvePreviewResponse:
    """
    Parse SVG and return geometry statistics.

    Use this endpoint to preview SVG geometry before generating G-code.
    """
    if not req.svg.strip():
        raise HTTPException(status_code=400, detail="SVG text is empty.")

    polylines = parse_svg_to_polylines(req.svg)

    if req.normalize:
        polylines = normalize_polylines(polylines)

    stats = polyline_stats(polylines)

    return VCarvePreviewResponse(stats=stats, normalized=req.normalize)


@router.post("/gcode", response_model=VCarveGCodeResponse)
async def generate_vcarve_gcode(req: VCarveGCodeRequest) -> VCarveGCodeResponse:
    """
    Generate G-code from SVG for VCarve operations.

    Note: This is a naive G-code emitter for smoke testing and preview.
    It does not handle advanced CAM features like chipload, stepdown, etc.
    """
    if not req.svg.strip():
        raise HTTPException(status_code=400, detail="SVG text is empty.")

    params = VCarveToolpathParams(
        bit_angle_deg=req.bit_angle_deg,
        depth_mm=req.depth_mm,
        safe_z_mm=req.safe_z_mm,
        feed_rate_mm_min=req.feed_rate_mm_min,
        plunge_rate_mm_min=req.plunge_rate_mm_min,
    )

    gcode = svg_to_naive_gcode(req.svg, params)

    return VCarveGCodeResponse(gcode=gcode)
