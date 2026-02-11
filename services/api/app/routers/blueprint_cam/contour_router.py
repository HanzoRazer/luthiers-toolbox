"""
Blueprint CAM Contour Router
============================

Contour reconstruction from primitive DXF geometry.

Endpoints:
- POST /reconstruct-contours: Chain LINE + SPLINE into closed loops
"""

from typing import Any, Dict

from fastapi import APIRouter, File, HTTPException, UploadFile

from ...cam.contour_reconstructor import reconstruct_contours_from_dxf

router = APIRouter(tags=["blueprint-cam-bridge"])


@router.post("/reconstruct-contours")
async def reconstruct_contours(
    file: UploadFile = File(..., description="DXF file with primitive geometry (LINE + SPLINE)"),
    layer_name: str = "Contours",
    tolerance: float = 0.1,
    min_loop_points: int = 3
) -> Dict[str, Any]:
    """
    Phase 3.1: Contour Reconstruction

    Chains primitive DXF geometry (LINE + SPLINE) into closed LWPOLYLINE loops.

    Problem:
        CAD drawings often use disconnected LINE and SPLINE primitives instead of
        closed paths. This endpoint reconstructs closed contours by:
        1. Building connectivity graph from endpoints
        2. Finding cycles using depth-first search
        3. Sampling splines to polyline segments
        4. Classifying loops (outer boundary vs islands)

    Args:
        file: DXF file with LINE + SPLINE entities
        layer_name: Layer to extract from (default: Contours)
        tolerance: Endpoint matching tolerance in mm (default: 0.1)
        min_loop_points: Minimum points per loop (default: 3)

    Returns:
        loops: List of closed contours (first = outer, rest = islands)
        stats: Geometry analysis (lines, splines, cycles found)
        warnings: Non-fatal issues during reconstruction

    Raises:
        HTTPException 422: No closed contours found
        HTTPException 500: Reconstruction failed
        HTTPException 504: Processing timeout
    """
    # Security patch: Validate file size and extension before reading
    from app.cam.dxf_upload_guard import read_dxf_with_validation
    from app.cam.async_timeout import run_with_timeout, GeometryTimeout

    dxf_bytes = await read_dxf_with_validation(file)

    # Reconstruct contours with timeout protection
    try:
        result = await run_with_timeout(
            reconstruct_contours_from_dxf,
            dxf_bytes=dxf_bytes,
            layer_name=layer_name,
            tolerance=tolerance,
            min_loop_points=min_loop_points,
            timeout=30.0
        )
    except GeometryTimeout as e:
        raise HTTPException(status_code=504, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Contour reconstruction failed: {str(e)}"
        )

    if not result.loops:
        raise HTTPException(
            status_code=422,
            detail=f"No closed contours found. Warnings: {'; '.join(result.warnings)}"
        )

    return {
        "success": True,
        "loops": [loop.dict() for loop in result.loops],
        "outer_loop_idx": result.outer_loop_idx,
        "stats": result.stats,
        "warnings": result.warnings,
        "message": f"Reconstructed {len(result.loops)} closed contours from {result.stats.get('lines_found', 0)} lines and {result.stats.get('splines_found', 0)} splines"
    }
