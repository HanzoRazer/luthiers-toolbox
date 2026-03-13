"""
Art Studio Preview Routers (Consolidated)
==========================================

SVG preview endpoints for relief and vcarve operations.

LANE: UTILITY

Art Studio is ornament-authority only. It may parse/preview SVG geometry, but must NOT:
- generate machine outputs (DXF/toolpaths/G-code)
- create or persist run artifacts
- call Saw Lab / CAM execution APIs

Consolidated from:
    - relief_router.py (1 route)
    - vcarve_router.py (1 route)

Endpoints:
    POST /relief/preview  - Preview relief geometry (stats only)
    POST /vcarve/preview  - Preview vcarve geometry (stats only)

DXF/G-code generation moved to CAM:
    POST /api/cam/toolpath/relief/export-dxf
    POST /api/cam/toolpath/vcarve/gcode
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


# ===========================================================================
# Sub-routers with prefixes
# ===========================================================================

relief_router = APIRouter()
vcarve_router = APIRouter()


# ===========================================================================
# SHARED MODELS
# ===========================================================================

class SvgPreviewRequest(BaseModel):
    """Request model for SVG preview."""
    svg: str = Field(..., description="SVG document as text")
    normalize: bool = Field(
        default=True,
        description="Whether to normalize coordinates to (0,0)"
    )


class SvgPreviewResponse(BaseModel):
    """Response model for SVG preview."""
    stats: Dict[str, Any] = Field(
        ..., description="Statistics about the parsed geometry"
    )
    normalized: bool = Field(
        ..., description="Whether coordinates were normalized"
    )


# ===========================================================================
# RELIEF ENDPOINTS
# ===========================================================================

@relief_router.post("/preview", response_model=SvgPreviewResponse)
async def preview_relief(req: SvgPreviewRequest) -> SvgPreviewResponse:
    """
    Parse SVG and return relief geometry statistics.

    LANE: UTILITY - Preview only, no artifacts.

    Use this endpoint to preview relief geometry before DXF export.
    DXF export is available at: POST /api/cam/toolpath/relief/export-dxf
    """
    if not req.svg.strip():
        raise HTTPException(status_code=400, detail="SVG text is empty.")

    polys = parse_svg_to_polylines(req.svg)

    if req.normalize:
        polys = normalize_polylines(polys)

    stats = {"svg": polyline_stats(polys)}

    return SvgPreviewResponse(stats=stats, normalized=req.normalize)


# ===========================================================================
# VCARVE ENDPOINTS
# ===========================================================================

@vcarve_router.post("/preview", response_model=SvgPreviewResponse)
async def preview_vcarve(req: SvgPreviewRequest) -> SvgPreviewResponse:
    """
    Parse SVG and return geometry statistics.

    LANE: UTILITY - Preview only, no artifacts.

    Use this endpoint to preview SVG geometry before generating G-code.
    G-code generation is available at: POST /api/cam/toolpath/vcarve/gcode
    """
    if not req.svg.strip():
        raise HTTPException(status_code=400, detail="SVG text is empty.")

    polylines = parse_svg_to_polylines(req.svg)

    if req.normalize:
        polylines = normalize_polylines(polylines)

    stats = polyline_stats(polylines)

    return SvgPreviewResponse(stats=stats, normalized=req.normalize)


# ===========================================================================
# Aggregate Router
# ===========================================================================

router = APIRouter()
router.include_router(relief_router, prefix="/relief", tags=["Art Studio", "Relief"])
router.include_router(vcarve_router, prefix="/vcarve", tags=["Art Studio", "VCarve"])

__all__ = ["router", "relief_router", "vcarve_router"]
