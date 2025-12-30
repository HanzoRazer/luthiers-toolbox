# services/api/app/art_studio/relief_router.py

"""
Art Studio Relief Router

LANE: OPERATION (for /export-dxf endpoint)
LANE: UTILITY (for /preview, /preview-feasibility endpoints)
Reference: docs/OPERATION_EXECUTION_GOVERNANCE_v1.md
Execution Class: A (Planning) - generates DXF from SVG geometry

FastAPI endpoints for relief SVG → DXF export.

GOVERNANCE INVARIANTS:
1. /export-dxf creates a run artifact (OK or ERROR)
2. All outputs are SHA256 hashed for provenance

ARTIFACT KINDS:
- relief_dxf_export (OK/ERROR) - from /export-dxf

Endpoints:
- POST /preview: Parse SVG and return relief stats (UTILITY)
- POST /preview-feasibility: Preview with RMOS feasibility calculation (UTILITY)
- POST /export-dxf: Export relief geometry to DXF (OPERATION)

For Wave 3, relief is: SVG → polylines → MLPaths → DXF.
Z/height mapping will be added later when we bring in full relief CAM.
"""

from __future__ import annotations

import io
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .svg_ingest_service import (
    parse_svg_to_polylines,
    normalize_polylines,
    polyline_stats,
)
from ..toolpath.relief_geometry import (
    ReliefPolylineSpec,
    ReliefDesignSpec,
    relief_design_to_mlpaths,
    relief_stats,
)
from ..toolpath.dxf_exporter import (
    DXFExportOptions,
    DXFVersion,
    export_mlpaths_to_dxf,
)

# Import run artifact persistence (OPERATION lane requirement)
from datetime import datetime, timezone
from ..rmos.runs import (
    RunArtifact,
    persist_run,
    create_run_id,
    sha256_of_obj,
    sha256_of_text,
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

    stats: Dict[str, Any] = Field(
        ..., description="Combined relief and SVG statistics"
    )
    normalized: bool = Field(
        ..., description="Whether coordinates were normalized"
    )


class ReliefFeasibilityRequest(ReliefPreviewRequest):
    """Request model for relief preview with feasibility."""

    material_id: str = Field(..., description="e.g. spruce, maple, etc.")
    tool_id: str = Field(..., description="e.g. ballnose_3mm")
    spindle_rpm: float = Field(..., gt=0, description="Spindle RPM")
    feed_mm_min: float = Field(..., gt=0, description="Feed rate in mm/min")


class ReliefFeasibilityResponse(BaseModel):
    """Response model for relief preview with feasibility."""

    stats: Dict[str, Any] = Field(
        ..., description="Combined relief and SVG statistics"
    )
    feasibility: Dict[str, Any] = Field(
        ..., description="RMOS feasibility result"
    )


class ReliefDXFExportRequest(BaseModel):
    """Request model for relief DXF export."""

    svg: str = Field(..., description="Source SVG for relief outlines")
    normalize: bool = Field(default=True)
    dxf_version: DXFVersion = Field(default=DXFVersion.R12)
    prefer_lwpolyline: bool | None = Field(default=None)
    filename: str = Field(default="relief.dxf")

    # Optional feasibility parameters
    compute_feasibility: bool = Field(
        default=False,
        description="Whether to include feasibility calculation"
    )
    material_id: str | None = Field(default=None)
    tool_id: str | None = Field(default=None)
    spindle_rpm: float | None = Field(default=None)
    feed_mm_min: float | None = Field(default=None)


# --------------------------------------------------------------------- #
# Endpoints
# --------------------------------------------------------------------- #


@router.post("/preview", response_model=ReliefPreviewResponse)
async def preview_relief(req: ReliefPreviewRequest) -> ReliefPreviewResponse:
    """
    Parse SVG and return relief geometry statistics.

    Use this endpoint to preview relief geometry before DXF export.
    """
    if not req.svg.strip():
        raise HTTPException(status_code=400, detail="SVG text is empty.")

    polys = parse_svg_to_polylines(req.svg)

    if req.normalize:
        polys = normalize_polylines(polys)

    specs: List[ReliefPolylineSpec] = [
        ReliefPolylineSpec(points=list(poly)) for poly in polys
    ]
    design = ReliefDesignSpec(polylines=specs)
    mlpaths = relief_design_to_mlpaths(design)
    stats = relief_stats(mlpaths)

    # Also include raw polyline stats for UI
    svg_stats = polyline_stats(polys)
    combined = {
        "relief": stats,
        "svg": svg_stats,
    }

    return ReliefPreviewResponse(stats=combined, normalized=req.normalize)


@router.post("/preview-feasibility", response_model=ReliefFeasibilityResponse)
async def preview_relief_feasibility(
    req: ReliefFeasibilityRequest,
) -> ReliefFeasibilityResponse:
    """
    Parse SVG and return relief stats with RMOS feasibility calculation.
    """
    if not req.svg.strip():
        raise HTTPException(status_code=400, detail="SVG text is empty.")

    polys = parse_svg_to_polylines(req.svg)

    if req.normalize:
        polys = normalize_polylines(polys)

    specs: List[ReliefPolylineSpec] = [
        ReliefPolylineSpec(points=list(poly)) for poly in polys
    ]
    design = ReliefDesignSpec(polylines=specs)
    mlpaths = relief_design_to_mlpaths(design)
    r_stats = relief_stats(mlpaths)
    svg_stats = polyline_stats(polys)
    stats = {
        "relief": r_stats,
        "svg": svg_stats,
    }

    # Try to use the Saw Lab bridge for feasibility
    try:
        from ..calculators.saw_bridge import evaluate_operation_feasibility

        feasibility = evaluate_operation_feasibility(
            operation="relief_outline",
            material_id=req.material_id,
            tool_id=req.tool_id,
            spindle_rpm=req.spindle_rpm,
            feed_mm_min=req.feed_mm_min,
            path_length_mm=r_stats.get("total_length", 0.0),
        )
        if feasibility is None:
            feasibility = {"error": "Saw bridge returned None"}
    except ImportError:
        # Fallback if saw_bridge not available
        feasibility = {
            "error": "Saw bridge not available",
            "path_length_mm": r_stats.get("total_length", 0.0),
        }

    return ReliefFeasibilityResponse(stats=stats, feasibility=feasibility)


@router.post("/export-dxf")
async def export_relief_dxf(req: ReliefDXFExportRequest) -> Response:
    """
    Export relief geometry to DXF format.

    LANE: OPERATION - Creates relief_dxf_export artifact.

    Optionally includes feasibility calculation if compute_feasibility=True.
    """
    now = datetime.now(timezone.utc).isoformat()
    request_hash = sha256_of_obj(req.model_dump())

    if not req.svg.strip():
        run_id = create_run_id()
        artifact = RunArtifact(
            run_id=run_id,
            created_at_utc=now,
            tool_id="relief_dxf",
            workflow_mode="relief",
            event_type="relief_dxf_export",
            status="ERROR",
            request_hash=request_hash,
            errors=["SVG text is empty"],
        )
        persist_run(artifact)
        raise HTTPException(status_code=400, detail={"error": "EMPTY_SVG", "run_id": run_id, "message": "SVG text is empty."})

    polys = parse_svg_to_polylines(req.svg)

    if req.normalize:
        polys = normalize_polylines(polys)

    specs: List[ReliefPolylineSpec] = [
        ReliefPolylineSpec(points=list(poly)) for poly in polys
    ]
    design = ReliefDesignSpec(polylines=specs)
    mlpaths = relief_design_to_mlpaths(design)

    buf = io.StringIO()
    options = DXFExportOptions(
        dxf_version=req.dxf_version,
        prefer_lwpolyline=req.prefer_lwpolyline,
    )
    export_mlpaths_to_dxf(mlpaths, buf, options=options)
    dxf_text = buf.getvalue()

    headers = {
        "Content-Disposition": f'attachment; filename="{req.filename}"'
    }

    if not req.compute_feasibility:
        # Create OK artifact
        dxf_hash = sha256_of_text(dxf_text)
        run_id = create_run_id()
        artifact = RunArtifact(
            run_id=run_id,
            created_at_utc=now,
            tool_id="relief_dxf",
            workflow_mode="relief",
            event_type="relief_dxf_export",
            status="OK",
            request_hash=request_hash,
            gcode_hash=dxf_hash,  # Using gcode_hash for DXF output
        )
        persist_run(artifact)
        headers["X-Run-ID"] = run_id
        headers["X-DXF-SHA256"] = dxf_hash
        return Response(
            content=dxf_text,
            media_type="application/dxf",
            headers=headers,
        )

    # Validate required fields for feasibility
    missing = [
        name
        for name, value in [
            ("material_id", req.material_id),
            ("tool_id", req.tool_id),
            ("spindle_rpm", req.spindle_rpm),
            ("feed_mm_min", req.feed_mm_min),
        ]
        if value is None
    ]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Missing fields for feasibility: {', '.join(missing)}",
        )

    # Calculate feasibility
    r_stats = relief_stats(mlpaths)
    try:
        from ..calculators.saw_bridge import evaluate_operation_feasibility

        feasibility = evaluate_operation_feasibility(
            operation="relief_outline",
            material_id=req.material_id or "",
            tool_id=req.tool_id or "",
            spindle_rpm=req.spindle_rpm or 0.0,
            feed_mm_min=req.feed_mm_min or 0.0,
            path_length_mm=r_stats.get("total_length", 0.0),
        )
        if feasibility is None:
            feasibility = {"error": "Saw bridge returned None"}
    except ImportError:
        feasibility = {"error": "Saw bridge not available"}

    # Create OK artifact with feasibility
    dxf_hash = sha256_of_text(dxf_text)
    run_id = create_run_id()
    artifact = RunArtifact(
        run_id=run_id,
        created_at_utc=now,
        tool_id="relief_dxf",
        workflow_mode="relief",
        event_type="relief_dxf_export",
        status="OK",
        request_hash=request_hash,
        gcode_hash=dxf_hash,
        feasibility=feasibility,
    )
    persist_run(artifact)
    headers["X-Run-ID"] = run_id
    headers["X-DXF-SHA256"] = dxf_hash

    # Return JSON with DXF + feasibility
    return JSONResponse(
        content={
            "dxf": dxf_text,
            "feasibility": feasibility,
            "_run_id": run_id,
            "_hashes": {"dxf_sha256": dxf_hash},
        },
        headers=headers,
    )
