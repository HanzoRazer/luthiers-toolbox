"""
Preview Routes - Bundle 31.0.3

SVG preview rendering API.
"""
from __future__ import annotations

from fastapi import APIRouter

from ..schemas.preview import RosettePreviewSvgRequest, RosettePreviewSvgResponse
from ..services.rosette_preview_renderer import render_rosette_preview_svg


router = APIRouter(
    prefix="/api/art/rosette/preview",
    tags=["art_studio_preview"],
)


@router.post("/svg", response_model=RosettePreviewSvgResponse)
async def preview_rosette_svg(req: RosettePreviewSvgRequest) -> RosettePreviewSvgResponse:
    """
    Render a lightweight SVG preview of a RosetteParamSpec.

    This is a UI preview only - not production geometry.
    No CAM, no toolpaths, no heavy geometry calculations.
    """
    result = render_rosette_preview_svg(
        spec=req.spec,
        size_px=req.size_px,
        padding_px=req.padding_px,
    )

    return RosettePreviewSvgResponse(
        svg=result.svg,
        size_px=req.size_px,
        view_box=result.view_box,
        warnings=result.warnings,
        debug=result.debug,
    )
