# services/api/app/art_studio/vcarve_router.py

"""
Art Studio VCarve Router (PREVIEW ONLY)

LANE: UTILITY

Art Studio is ornament-authority only. It may parse/preview SVG geometry, but must NOT:
- generate machine outputs (toolpaths/G-code)
- create or persist run artifacts

G-code generation has been moved to CAM:
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


# --------------------------------------------------------------------- #
# Endpoints
# --------------------------------------------------------------------- #


@router.post("/preview", response_model=VCarvePreviewResponse)
async def preview_vcarve(req: VCarvePreviewRequest) -> VCarvePreviewResponse:
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

    return VCarvePreviewResponse(stats=stats, normalized=req.normalize)
