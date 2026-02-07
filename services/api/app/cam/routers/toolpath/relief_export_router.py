# services/api/app/cam/routers/toolpath/relief_export_router.py

"""
CAM Relief DXF Export Router

LANE: OPERATION
Reference: docs/OPERATION_EXECUTION_GOVERNANCE_v1.md

This endpoint was moved out of Art Studio to satisfy the Art Studio Scope Gate.
Art Studio is ornament-authority only and cannot generate machine outputs.

Path:
    POST /api/cam/toolpath/relief/export-dxf

GOVERNANCE INVARIANTS:
1. Client feasibility is ALWAYS ignored and recomputed server-side
2. RED/UNKNOWN risk levels result in HTTP 409 (blocked)
3. EVERY request creates a run artifact (OK, BLOCKED, or ERROR)
4. All outputs are SHA256 hashed for provenance

ARTIFACT KINDS:
- relief_dxf_export (OK/ERROR) - from /export-dxf
- relief_dxf_blocked (BLOCKED) - from /export-dxf when safety policy blocks
"""

from __future__ import annotations

import io
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# SVG parsing from Art Studio (allowed: utility functions)
from ....art_studio.svg_ingest_service import (
    parse_svg_to_polylines,
    normalize_polylines,
    polyline_stats,
)

# Toolpath geometry (CAM domain)
from ....toolpath.relief_geometry import (
    ReliefPolylineSpec,
    ReliefDesignSpec,
    relief_design_to_mlpaths,
    relief_stats,
)
from ....toolpath.dxf_exporter import (
    DXFExportOptions,
    DXFVersion,
    export_mlpaths_to_dxf,
)

# RMOS artifact persistence (OPERATION lane requirement)
from ....rmos.runs import (
    RunArtifact,
    persist_run,
    create_run_id,
    sha256_of_obj,
    sha256_of_text,
)

# Feasibility enforcement
from ....rmos.api.rmos_feasibility_router import compute_feasibility_internal
from ....rmos.policies import SafetyPolicy

router = APIRouter()


# --------------------------------------------------------------------- #
# Request/Response Models
# --------------------------------------------------------------------- #


class ReliefDXFExportRequest(BaseModel):
    """Request model for relief DXF export."""

    svg: str = Field(..., description="Source SVG for relief outlines")
    normalize: bool = Field(default=True)
    dxf_version: DXFVersion = Field(default=DXFVersion.R12)
    prefer_lwpolyline: Optional[bool] = Field(default=None)
    filename: str = Field(default="relief.dxf")

    # Optional feasibility parameters
    compute_feasibility: bool = Field(
        default=False, description="Whether to include feasibility calculation"
    )
    material_id: Optional[str] = Field(default=None)
    tool_id: Optional[str] = Field(default=None)
    spindle_rpm: Optional[float] = Field(default=None)
    feed_mm_min: Optional[float] = Field(default=None)


# --------------------------------------------------------------------- #
# Endpoints
# --------------------------------------------------------------------- #


@router.post("/export-dxf")
async def export_relief_dxf(req: ReliefDXFExportRequest) -> Response:
    """
    Export relief geometry to DXF format.

    LANE: OPERATION - Creates relief_dxf_export artifact.

    Optionally includes feasibility calculation if compute_feasibility=True.
    """
    now = datetime.now(timezone.utc).isoformat()
    request_hash = sha256_of_obj(req.model_dump())
    tool_id = req.tool_id or "relief_dxf"

    # --- Server-side feasibility enforcement (ADR-003 / OPERATION lane) ---
    feasibility = compute_feasibility_internal(
        tool_id=tool_id,
        req=req,
        context="relief_dxf",
    )
    decision = SafetyPolicy.extract_safety_decision(feasibility)
    risk_level = decision.risk_level_str()
    feas_hash = sha256_of_obj(feasibility)

    if SafetyPolicy.should_block(decision.risk_level):
        run_id = create_run_id()
        artifact = RunArtifact(
            run_id=run_id,
            created_at_utc=now,
            tool_id=tool_id,
            workflow_mode="relief",
            event_type="relief_dxf_blocked",
            status="BLOCKED",
            feasibility=feasibility,
            request_hash=feas_hash,
            notes=f"Blocked by safety policy: {risk_level}",
        )
        persist_run(artifact)
        raise HTTPException(
            status_code=409,
            detail={
                "error": "SAFETY_BLOCKED",
                "message": "Relief DXF export blocked due to unresolved feasibility concerns.",
                "run_id": run_id,
                "decision": decision.to_dict(),
                "authoritative_feasibility": feasibility,
            },
        )

    if not req.svg.strip():
        run_id = create_run_id()
        artifact = RunArtifact(
            run_id=run_id,
            created_at_utc=now,
            tool_id=tool_id,
            workflow_mode="relief",
            event_type="relief_dxf_export",
            status="ERROR",
            feasibility=feasibility,
            request_hash=request_hash,
            errors=["SVG text is empty"],
        )
        persist_run(artifact)
        raise HTTPException(
            status_code=400,
            detail={
                "error": "EMPTY_SVG",
                "run_id": run_id,
                "message": "SVG text is empty.",
            },
        )

    try:
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

        headers = {"Content-Disposition": f'attachment; filename="{req.filename}"'}

        # Create OK artifact
        dxf_hash = sha256_of_text(dxf_text)
        run_id = create_run_id()
        artifact = RunArtifact(
            run_id=run_id,
            created_at_utc=now,
            tool_id=tool_id,
            workflow_mode="relief",
            event_type="relief_dxf_export",
            status="OK",
            feasibility=feasibility,
            request_hash=request_hash,
            gcode_hash=dxf_hash,  # Using gcode_hash for DXF output
        )
        persist_run(artifact)
        headers["X-Run-ID"] = run_id
        headers["X-DXF-SHA256"] = dxf_hash

        if not req.compute_feasibility:
            return Response(
                content=dxf_text,
                media_type="application/dxf",
                headers=headers,
            )

        # Return JSON with DXF + feasibility if requested
        r_stats = relief_stats(mlpaths)
        return JSONResponse(
            content={
                "dxf": dxf_text,
                "feasibility": feasibility,
                "stats": r_stats,
                "_run_id": run_id,
                "_hashes": {"dxf_sha256": dxf_hash},
            },
            headers=headers,
        )

    except HTTPException:
        raise  # WP-1: pass through
    except Exception as e:  # WP-1: governance catch-all — HTTP endpoint
        run_id = create_run_id()
        artifact = RunArtifact(
            run_id=run_id,
            created_at_utc=now,
            tool_id=tool_id,
            workflow_mode="relief",
            event_type="relief_dxf_export",
            status="ERROR",
            feasibility=feasibility,
            request_hash=request_hash,
            errors=[f"{type(e).__name__}: {str(e)}"],
        )
        persist_run(artifact)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "DXF_EXPORT_ERROR",
                "run_id": run_id,
                "message": f"DXF export failed: {e}",
            },
        )
