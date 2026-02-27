# services/api/app/art_studio/relief_router.py

"""
Art Studio Relief Router (PREVIEW ONLY)

LANE: UTILITY

Art Studio is ornament-authority only. It may parse/preview SVG geometry, but must NOT:
- generate machine outputs (DXF/toolpaths/G-code)
- create or persist run artifacts
- call Saw Lab / CAM execution APIs

DXF export has been moved to CAM:
    POST /api/cam/toolpath/relief/export-dxf
"""

from __future__ import annotations

from typing import Any, Dict, List

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


class ReliefPreviewRequest(BaseModel):
    """Request model for relief preview."""

    svg: str = Field(..., description="Source SVG for relief outlines")
    normalize: bool = Field(
        default=True,
        description="Whether to normalize coordinates to (0,0)"
    )


class ReliefPreviewResponse(BaseModel):
    """Response model for relief preview."""

    stats: Dict[str, Any] = Field(..., description="SVG/polyline statistics")
    normalized: bool = Field(
        ..., description="Whether coordinates were normalized"
    )


# --------------------------------------------------------------------- #
# Endpoints
# --------------------------------------------------------------------- #


@router.post("/preview", response_model=ReliefPreviewResponse)
async def preview_relief(req: ReliefPreviewRequest) -> ReliefPreviewResponse:
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

    return ReliefPreviewResponse(stats=stats, normalized=req.normalize)
