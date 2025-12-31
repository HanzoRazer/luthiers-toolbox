# services/api/app/art_studio/vcarve_router.py

"""
Art Studio VCarve Router

LANE: OPERATION (for /gcode endpoint)
LANE: UTILITY (for /preview endpoint)
Reference: docs/OPERATION_EXECUTION_GOVERNANCE_v1.md
Execution Class: A (Planning) - generates G-code from SVG geometry

FastAPI endpoints for SVG → toolpath → G-code conversion.

GOVERNANCE INVARIANTS:
1. Client feasibility is ALWAYS ignored and recomputed server-side
2. RED/UNKNOWN risk levels result in HTTP 409 (blocked)
3. EVERY request creates a run artifact (OK, BLOCKED, or ERROR)
4. All outputs are SHA256 hashed for provenance

ARTIFACT KINDS:
- vcarve_gcode_execution (OK/ERROR) - from /gcode
- vcarve_gcode_blocked (BLOCKED) - from /gcode when safety policy blocks

Endpoints:
- POST /preview: Parse SVG and return stats (UTILITY - no artifacts)
- POST /gcode: Generate G-code from SVG (OPERATION - creates artifacts)
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

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

# Import run artifact persistence (OPERATION lane requirement)
from ..rmos.runs import (
    RunArtifact,
    persist_run,
    create_run_id,
    sha256_of_obj,
    sha256_of_text,
)

# Import feasibility functions (Phase 2: server-side enforcement)
from ..rmos.api.rmos_feasibility_router import compute_feasibility_internal
from ..rmos.policies import SafetyPolicy

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
    # Feasibility context (Phase 2)
    tool_id: Optional[str] = Field(
        default="vcarve:default",
        description="Tool identifier for feasibility lookup"
    )
    material_id: Optional[str] = Field(
        default=None,
        description="Material identifier for feasibility assessment"
    )


class VCarveGCodeResponse(BaseModel):
    """Response model for VCarve G-code generation."""

    gcode: str = Field(..., description="Generated G-code")
    _run_id: Optional[str] = Field(None, description="Run artifact ID for audit trail")
    _hashes: Optional[Dict[str, str]] = Field(None, description="SHA256 hashes for provenance")


# --------------------------------------------------------------------- #
# Endpoints
# --------------------------------------------------------------------- #


@router.post("/preview", response_model=VCarvePreviewResponse)
async def preview_vcarve(req: VCarvePreviewRequest) -> VCarvePreviewResponse:
    """
    Parse SVG and return geometry statistics.

    LANE: UTILITY - Preview only, no artifacts.

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
async def generate_vcarve_gcode(req: VCarveGCodeRequest) -> Dict[str, Any]:
    """
    Generate G-code from SVG for VCarve operations.

    LANE: OPERATION - Creates vcarve_gcode_execution or vcarve_gcode_blocked artifact.

    Flow:
    1. Validate SVG input
    2. Recompute feasibility server-side (NEVER trust client)
    3. Block if RED/UNKNOWN (HTTP 409)
    4. Generate G-code if safe
    5. Persist run artifact for audit trail
    """
    now = datetime.now(timezone.utc).isoformat()
    request_hash = sha256_of_obj(req.model_dump())
    tool_id = req.tool_id or "vcarve:default"

    if not req.svg.strip():
        # Create ERROR artifact for empty SVG
        run_id = create_run_id()
        artifact = RunArtifact(
            run_id=run_id,
            created_at_utc=now,
            tool_id=tool_id,
            workflow_mode="vcarve",
            event_type="vcarve_gcode_execution",
            status="ERROR",
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

    # Phase 2: Server-side feasibility enforcement
    feasibility = compute_feasibility_internal(
        tool_id=tool_id,
        req={
            "tool_id": tool_id,
            "material_id": req.material_id,
            "depth_mm": req.depth_mm,
            "bit_angle_deg": req.bit_angle_deg,
            "feed_rate_mm_min": req.feed_rate_mm_min,
        },
        context="vcarve_gcode",
    )
    decision = SafetyPolicy.extract_safety_decision(feasibility)
    risk_level = decision.risk_level_str()
    feas_hash = sha256_of_obj(feasibility)

    # Block if policy requires (BLOCKED artifact)
    if SafetyPolicy.should_block(decision.risk_level):
        run_id = create_run_id()
        artifact = RunArtifact(
            run_id=run_id,
            created_at_utc=now,
            tool_id=tool_id,
            workflow_mode="vcarve",
            event_type="vcarve_gcode_blocked",
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
                "message": "V-Carve G-code generation blocked by server-side safety policy.",
                "run_id": run_id,
                "decision": decision.to_dict(),
                "authoritative_feasibility": feasibility,
            },
        )

    try:
        params = VCarveToolpathParams(
            bit_angle_deg=req.bit_angle_deg,
            depth_mm=req.depth_mm,
            safe_z_mm=req.safe_z_mm,
            feed_rate_mm_min=req.feed_rate_mm_min,
            plunge_rate_mm_min=req.plunge_rate_mm_min,
        )

        gcode = svg_to_naive_gcode(req.svg, params)

        # Hash outputs for provenance
        gcode_hash = sha256_of_text(gcode)

        # Create OK artifact
        run_id = create_run_id()
        artifact = RunArtifact(
            run_id=run_id,
            created_at_utc=now,
            tool_id=tool_id,
            workflow_mode="vcarve",
            event_type="vcarve_gcode_execution",
            status="OK",
            feasibility=feasibility,
            request_hash=request_hash,
            gcode_hash=gcode_hash,
        )
        persist_run(artifact)

        return {
            "gcode": gcode,
            "_run_id": run_id,
            "_hashes": {
                "request_sha256": request_hash,
                "feasibility_sha256": feas_hash,
                "gcode_sha256": gcode_hash,
            },
        }

    except Exception as e:
        # Create ERROR artifact
        run_id = create_run_id()
        artifact = RunArtifact(
            run_id=run_id,
            created_at_utc=now,
            tool_id=tool_id,
            workflow_mode="vcarve",
            event_type="vcarve_gcode_execution",
            status="ERROR",
            feasibility=feasibility,
            request_hash=request_hash,
            errors=[f"{type(e).__name__}: {str(e)}"],
        )
        persist_run(artifact)

        raise HTTPException(
            status_code=400,
            detail={
                "error": "GCODE_GENERATION_ERROR",
                "run_id": run_id,
                "message": f"G-code generation failed: {str(e)}",
            },
        )
