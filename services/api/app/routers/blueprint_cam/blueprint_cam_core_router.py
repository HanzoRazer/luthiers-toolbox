"""
Blueprint CAM Core Router (Consolidated)
=========================================

Core endpoints for DXF-to-Toolpath integration.

Consolidated from:
    - contour_router.py (1 route)
    - preflight_router.py (1 route)
    - pipeline_adapter_router.py (3 routes)
    - adaptive_router.py (1 route)

Endpoints:
    POST /reconstruct-contours     - Chain LINE + SPLINE into closed loops
    POST /preflight                - DXF validation before CAM processing
    GET  /pipeline-adapter/info    - Adapter info
    POST /pipeline-adapter/from-pipeline      - Convert PipelineResult to CAM spec
    POST /pipeline-adapter/from-pipeline-raw  - Convert raw dict to CAM spec
    POST /to-adaptive              - Convert DXF to adaptive pocket toolpath
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from ..blueprint_cam_bridge_schemas import BlueprintToAdaptiveResponse
from ...cam.adaptive_core_l1 import plan_adaptive_l1, to_toolpath
from ...cam.contour_reconstructor import reconstruct_contours_from_dxf
from ...cam.dxf_preflight import DXFPreflight, generate_html_report
from ...services.pipeline_cam_adapter import adapt_dict_to_cam, CamReadySpec

from .extraction import extract_loops_from_dxf

logger = logging.getLogger(__name__)


# ===========================================================================
# CONTOUR RECONSTRUCTION
# ===========================================================================

contour_router = APIRouter(tags=["blueprint-cam-bridge"])


@contour_router.post("/reconstruct-contours")
async def reconstruct_contours(
    file: UploadFile = File(..., description="DXF file with primitive geometry (LINE + SPLINE)"),
    layer_name: str = "Contours",
    tolerance: float = 0.1,
    min_loop_points: int = 3
) -> Dict[str, Any]:
    """
    Chain primitive DXF geometry (LINE + SPLINE) into closed LWPOLYLINE loops.
    """
    from app.cam.dxf_upload_guard import read_dxf_with_validation
    from app.cam.async_timeout import run_with_timeout, GeometryTimeout

    dxf_bytes = await read_dxf_with_validation(file)

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
    except (ValueError, KeyError, TypeError, OSError) as e:
        raise HTTPException(status_code=500, detail=f"Contour reconstruction failed: {str(e)}")

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
        "message": f"Reconstructed {len(result.loops)} closed contours"
    }


# ===========================================================================
# PREFLIGHT VALIDATION
# ===========================================================================

preflight_router = APIRouter(tags=["blueprint-cam-bridge"])


@preflight_router.post("/preflight")
async def dxf_preflight(
    file: UploadFile = File(..., description="DXF file to validate"),
    format: str = Form(default="json")
) -> Dict[str, Any]:
    """
    Validate DXF files before CAM processing to catch issues early.
    """
    from app.cam.dxf_upload_guard import read_dxf_with_validation

    dxf_bytes = await read_dxf_with_validation(file)

    try:
        preflight = DXFPreflight(dxf_bytes, filename=file.filename)
        report = preflight.run_all_checks()
    except HTTPException:
        raise
    except (ValueError, KeyError, TypeError, OSError) as e:
        raise HTTPException(status_code=500, detail=f"Preflight validation failed: {str(e)}")

    if format.lower() == "html":
        html = generate_html_report(report)
        return HTMLResponse(content=html, status_code=200)
    else:
        return {
            "filename": report.filename,
            "dxf_version": report.dxf_version,
            "passed": report.passed,
            "total_entities": report.total_entities,
            "layers": report.layers,
            "issues": [
                {
                    "severity": issue.severity,
                    "message": issue.message,
                    "category": issue.category,
                    "layer": issue.layer,
                    "entity_handle": issue.entity_handle,
                    "entity_type": issue.entity_type,
                    "suggestion": issue.suggestion
                }
                for issue in report.issues
            ],
            "stats": report.stats,
            "summary": {
                "errors": report.error_count(),
                "warnings": report.warning_count(),
                "info": report.info_count()
            },
            "timestamp": report.timestamp
        }


# ===========================================================================
# PIPELINE ADAPTER
# ===========================================================================

pipeline_adapter_router = APIRouter(prefix="/pipeline-adapter", tags=["Pipeline CAM Adapter"])


class PipelineResultInput(BaseModel):
    """Input: Phase 4 PipelineResult as JSON dict."""
    source_file: str = ""
    extraction: Dict[str, Any] = {}
    linking: Dict[str, Any] = {}
    linked_dimensions: Dict[str, Any] = {}


class CamSpecResponse(BaseModel):
    """Response: CAM-ready specification."""
    success: bool
    geometry: Dict[str, Any] = {}
    dimensions: Dict[str, Any] = {}
    suggested_params: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}
    warnings: list = []


@pipeline_adapter_router.get("/info")
def get_adapter_info() -> Dict[str, Any]:
    """Get pipeline adapter information."""
    return {
        "module": "pipeline_cam_adapter",
        "description": "Converts Phase 4 PipelineResult to CAM-ready specification",
        "resolves": ["VEC-GAP-03"],
    }


@pipeline_adapter_router.post("/from-pipeline", response_model=CamSpecResponse)
def convert_pipeline_to_cam(data: PipelineResultInput) -> CamSpecResponse:
    """Convert Phase 4 PipelineResult to CAM-ready specification."""
    try:
        result_dict = data.model_dump()
        spec = adapt_dict_to_cam(result_dict)
        return CamSpecResponse(success=True, **spec.to_dict())
    except Exception as e:  # audited: http-500 — ValueError,KeyError
        logger.exception("Pipeline to CAM conversion failed")
        raise HTTPException(500, f"Conversion failed: {e}")


@pipeline_adapter_router.post("/from-pipeline-raw")
def convert_pipeline_raw(data: Dict[str, Any]) -> JSONResponse:
    """Convert raw PipelineResult dict to CAM spec."""
    try:
        spec = adapt_dict_to_cam(data)
        return JSONResponse(content=spec.to_dict())
    except Exception as e:  # audited: http-500 — ValueError,KeyError
        logger.exception("Pipeline to CAM conversion failed")
        raise HTTPException(500, f"Conversion failed: {e}")


# ===========================================================================
# ADAPTIVE POCKET BRIDGE
# ===========================================================================

adaptive_router = APIRouter(tags=["blueprint-cam-bridge"])


@adaptive_router.post("/to-adaptive", response_model=BlueprintToAdaptiveResponse)
async def blueprint_to_adaptive(
    file: UploadFile = File(..., description="DXF file from Phase 2 vectorization"),
    layer_name: str = "GEOMETRY",
    tool_d: float = 6.0,
    stepover: float = 0.45,
    stepdown: float = 2.0,
    margin: float = 0.5,
    strategy: str = "Spiral",
    smoothing: float = 0.3,
    climb: bool = True,
    feed_xy: float = 1200,
    feed_z: float = 600,
    rapid: float = 3000,
    safe_z: float = 5.0,
    z_rough: float = -1.5,
    units: str = "mm"
):
    """Convert Phase 2 DXF vectorization output to adaptive pocket toolpath."""
    from app.cam.dxf_upload_guard import read_dxf_with_validation

    dxf_bytes = await read_dxf_with_validation(file)
    loops, warnings = extract_loops_from_dxf(dxf_bytes, layer_name)

    if not loops:
        raise HTTPException(
            status_code=422,
            detail=f"No valid closed loops found in DXF. Warnings: {'; '.join(warnings)}"
        )

    loops_data = [loop.pts for loop in loops]

    try:
        path_pts = plan_adaptive_l1(
            loops=loops_data,
            tool_d=tool_d,
            stepover=stepover,
            stepdown=stepdown,
            margin=margin,
            strategy=strategy,
            smoothing_radius=smoothing
        )
    except HTTPException:
        raise
    except (ValueError, KeyError, TypeError, ZeroDivisionError) as e:
        raise HTTPException(status_code=500, detail=f"Adaptive planner error: {str(e)}")

    moves = to_toolpath(path_pts=path_pts, z_rough=z_rough, safe_z=safe_z, feed_xy=feed_xy, lead_r=0.0)

    # Calculate statistics
    total_length = 0.0
    cutting_moves = 0
    for i in range(1, len(moves)):
        move = moves[i]
        prev = moves[i - 1]
        if move.get('code') == 'G1':
            dx = move.get('x', prev.get('x', 0)) - prev.get('x', 0)
            dy = move.get('y', prev.get('y', 0)) - prev.get('y', 0)
            dz = move.get('z', prev.get('z', 0)) - prev.get('z', 0)
            total_length += (dx ** 2 + dy ** 2 + dz ** 2) ** 0.5
            cutting_moves += 1

    time_s = (total_length / feed_xy) * 60 * 1.1
    volume_mm3 = total_length * tool_d * abs(z_rough)

    stats = {
        "length_mm": round(total_length, 2),
        "time_s": round(time_s, 1),
        "time_min": round(time_s / 60, 2),
        "move_count": len(moves),
        "cutting_moves": cutting_moves,
        "volume_mm3": round(volume_mm3, 0)
    }

    return BlueprintToAdaptiveResponse(
        loops_extracted=len(loops),
        loops=loops,
        moves=moves,
        stats=stats,
        warnings=warnings
    )


# ===========================================================================
# Aggregate Router
# ===========================================================================

router = APIRouter(tags=["blueprint-cam-bridge"])
router.include_router(contour_router)
router.include_router(preflight_router)
router.include_router(pipeline_adapter_router)
router.include_router(adaptive_router)

__all__ = ["router", "contour_router", "preflight_router", "pipeline_adapter_router", "adaptive_router"]
