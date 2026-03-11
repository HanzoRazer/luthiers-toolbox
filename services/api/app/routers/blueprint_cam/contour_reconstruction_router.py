"""
Contour Reconstruction API Router
==================================

API endpoints for reconstructing closed contours from LINE/ARC entities.

Resolves: VINE-09
"""

from typing import List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel

from .contour_reconstruction import (
    reconstruct_contours,
    reconstruct_bracing_dxf,
    ReconstructionResult,
    ContourLoop,
)


router = APIRouter(prefix="/contour-reconstruction", tags=["Contour Reconstruction"])


class ContourInfo(BaseModel):
    """Info about a single reconstructed contour."""
    point_count: int
    is_closed: bool
    perimeter_mm: float
    bounds_min_x: float
    bounds_min_y: float
    bounds_max_x: float
    bounds_max_y: float


class ReconstructionResponse(BaseModel):
    """Response from contour reconstruction."""
    success: bool
    # Stats
    total_entities: int
    entities_used: int
    entities_orphaned: int
    contours_found: int
    closed_contours: int
    open_chains: int
    # Contour details
    contours: List[ContourInfo]
    # Messages
    warnings: List[str]
    errors: List[str]


def _contour_to_info(contour: ContourLoop) -> ContourInfo:
    """Convert ContourLoop to ContourInfo response model."""
    return ContourInfo(
        point_count=len(contour.points),
        is_closed=contour.is_closed,
        perimeter_mm=contour.perimeter_mm,
        bounds_min_x=contour.bounds[0],
        bounds_min_y=contour.bounds[1],
        bounds_max_x=contour.bounds[2],
        bounds_max_y=contour.bounds[3],
    )


@router.get("/info")
def get_contour_reconstruction_info():
    """Get contour reconstruction module info."""
    return {
        "module": "Contour Reconstruction Pipeline",
        "version": "1.0.0",
        "resolves": ["VINE-09"],
        "capabilities": {
            "line_arc_chaining": "Chain LINE and ARC entities by endpoint proximity",
            "arc_to_polyline": "Convert ARC segments to polyline points",
            "layer_filtering": "Process specific layers only",
            "bracing_mode": "Specialized mode for bracing DXF files",
        },
        "supported_entity_types": ["LINE", "ARC"],
        "output_format": "LWPOLYLINE (closed)",
    }


@router.post("/reconstruct", response_model=ReconstructionResponse)
async def reconstruct(
    file: UploadFile = File(..., description="DXF file with LINE/ARC entities"),
    layer_name: Optional[str] = Form(None, description="Layer to process (None = all)"),
    tolerance_mm: float = Form(0.5, ge=0.01, le=10.0, description="Endpoint connection tolerance"),
    min_points: int = Form(3, ge=2, description="Minimum points for valid contour"),
    output_layer: str = Form("CONTOURS", description="Output layer name"),
    return_dxf: bool = Form(False, description="Return reconstructed DXF file"),
):
    """
    Reconstruct closed contours from LINE/ARC entities.

    Chains entities by endpoint proximity to form closed loops,
    then converts each loop to a closed LWPOLYLINE.
    """
    content = await file.read()

    if len(content) == 0:
        raise HTTPException(400, "Empty file")

    result = reconstruct_contours(
        dxf_bytes=content,
        layer_name=layer_name,
        tolerance_mm=tolerance_mm,
        min_points=min_points,
        output_layer=output_layer,
    )

    if not result.success:
        raise HTTPException(500, f"Reconstruction failed: {result.errors}")

    if return_dxf:
        filename = file.filename or "reconstructed.dxf"
        if not filename.endswith("_contours.dxf"):
            filename = filename.replace(".dxf", "_contours.dxf")
        return Response(
            content=result.dxf_bytes,
            media_type="application/dxf",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    return ReconstructionResponse(
        success=result.success,
        total_entities=result.total_entities,
        entities_used=result.entities_used,
        entities_orphaned=result.entities_orphaned,
        contours_found=result.contours_found,
        closed_contours=result.closed_contours,
        open_chains=result.open_chains,
        contours=[_contour_to_info(c) for c in result.contours],
        warnings=result.warnings,
        errors=result.errors,
    )


@router.post("/reconstruct-download")
async def reconstruct_and_download(
    file: UploadFile = File(..., description="DXF file with LINE/ARC entities"),
    layer_name: Optional[str] = Form(None),
    tolerance_mm: float = Form(0.5),
    min_points: int = Form(3),
    output_layer: str = Form("CONTOURS"),
):
    """
    Reconstruct contours and return the DXF file.

    Convenience endpoint that always returns the reconstructed DXF.
    """
    content = await file.read()

    if len(content) == 0:
        raise HTTPException(400, "Empty file")

    result = reconstruct_contours(
        dxf_bytes=content,
        layer_name=layer_name,
        tolerance_mm=tolerance_mm,
        min_points=min_points,
        output_layer=output_layer,
    )

    if not result.success:
        raise HTTPException(500, f"Reconstruction failed: {result.errors}")

    filename = file.filename or "reconstructed.dxf"
    if not filename.endswith("_contours.dxf"):
        filename = filename.replace(".dxf", "_contours.dxf")

    return Response(
        content=result.dxf_bytes,
        media_type="application/dxf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "X-Total-Entities": str(result.total_entities),
            "X-Entities-Used": str(result.entities_used),
            "X-Contours-Found": str(result.contours_found),
            "X-Closed-Contours": str(result.closed_contours),
        },
    )


@router.post("/reconstruct-bracing", response_model=ReconstructionResponse)
async def reconstruct_bracing(
    file: UploadFile = File(..., description="Bracing DXF file"),
    tolerance_mm: float = Form(1.0, ge=0.01, le=10.0, description="Endpoint connection tolerance"),
    return_dxf: bool = Form(False, description="Return reconstructed DXF file"),
):
    """
    Reconstruct contours from bracing DXF files.

    Specialized mode that:
    - Automatically finds layers containing 'BRAC' in name
    - Processes each bracing layer separately
    - Outputs contours to named layers (e.g., TOP_BRACING_CONTOURS)
    """
    content = await file.read()

    if len(content) == 0:
        raise HTTPException(400, "Empty file")

    result = reconstruct_bracing_dxf(
        dxf_bytes=content,
        tolerance_mm=tolerance_mm,
    )

    if not result.success:
        raise HTTPException(500, f"Bracing reconstruction failed: {result.errors}")

    if return_dxf:
        filename = file.filename or "bracing_contours.dxf"
        if not filename.endswith("_contours.dxf"):
            filename = filename.replace(".dxf", "_contours.dxf")
        return Response(
            content=result.dxf_bytes,
            media_type="application/dxf",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    return ReconstructionResponse(
        success=result.success,
        total_entities=result.total_entities,
        entities_used=result.entities_used,
        entities_orphaned=result.entities_orphaned,
        contours_found=result.contours_found,
        closed_contours=result.closed_contours,
        open_chains=result.open_chains,
        contours=[_contour_to_info(c) for c in result.contours],
        warnings=result.warnings,
        errors=result.errors,
    )
