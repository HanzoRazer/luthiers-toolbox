"""
RMOS MVP Wrapper - DXF to GRBL Golden Path with Governance

Wraps the locked MVP manufacturing path (DXF -> plan_from_dxf -> GRBL gcode)
with RMOS audit + governance without modifying CAM output.

Policy: Best-effort RMOS (returns gcode even if RMOS storage fails)

Contract: MVP_DXF_TO_GRBL_WRAPPER_CONTRACT_v1
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, Request
from pydantic import BaseModel, Field

from .runs_v2.schemas import (
    RunArtifact,
    RunDecision,
    RunOutputs,
    Hashes,
    RunAttachment,
)
from .runs_v2.store import create_run_id, persist_run
from .runs_v2.hashing import sha256_of_bytes, sha256_of_obj, sha256_of_text
from .runs_v2.attachments import put_bytes_attachment, put_json_attachment, put_text_attachment


router = APIRouter(prefix="/api/rmos/wrap/mvp", tags=["RMOS MVP Wrapper"])


# =============================================================================
# Response Schemas
# =============================================================================

class MVPWrapperResponse(BaseModel):
    """Response from MVP DXF-to-GRBL wrapper."""
    run_id: str = Field(..., description="RMOS run artifact ID")
    status: str = Field(..., description="Overall status: GREEN, YELLOW, RED")
    gcode_text: str = Field(..., description="Generated GRBL G-code")
    warnings: List[str] = Field(default_factory=list, description="CAM warnings")

    # Artifact hashes for verification
    hashes: Dict[str, str] = Field(
        default_factory=dict,
        description="SHA256 hashes: dxf, plan, gcode, manifest"
    )

    # RMOS status
    rmos_status: str = Field(
        "ok",
        description="RMOS storage status: ok, failed, partial"
    )
    rmos_error: Optional[str] = Field(
        None,
        description="RMOS error message if storage failed"
    )


class MVPManifest(BaseModel):
    """Manifest documenting the MVP golden path execution."""
    pipeline_id: str = "mvp_dxf_to_grbl_v1"
    controller: str = "GRBL"
    created_at_utc: str

    # Input parameters
    params: Dict[str, Any] = Field(default_factory=dict)

    # Hashes
    dxf_sha256: str
    plan_sha256: str
    gcode_sha256: str

    # Metadata
    api_version: str = "1.0.0"
    git_sha: Optional[str] = None
    post_profile_id: str = "GRBL"

    # Warnings
    warnings: List[str] = Field(default_factory=list)


# =============================================================================
# Internal Helpers
# =============================================================================

def _get_git_sha() -> Optional[str]:
    """Get current git SHA if available."""
    try:
        git_sha_path = Path(__file__).parent.parent.parent.parent / ".git" / "HEAD"
        if git_sha_path.exists():
            ref = git_sha_path.read_text().strip()
            if ref.startswith("ref:"):
                ref_path = Path(__file__).parent.parent.parent.parent / ".git" / ref.split()[-1]
                if ref_path.exists():
                    return ref_path.read_text().strip()[:12]
            return ref[:12]
    except Exception:
        pass
    return os.getenv("GIT_SHA", None)


def _compute_risk_level(warnings: List[str]) -> str:
    """
    Compute risk level from warnings.

    MVP policy:
    - No warnings -> GREEN
    - Any warnings -> YELLOW
    - Errors handled separately -> RED
    """
    if not warnings:
        return "GREEN"
    return "YELLOW"


def _call_plan_from_dxf(
    dxf_bytes: bytes,
    filename: str,
    params: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Call the existing plan_from_dxf logic internally.

    This imports the router's internal functions to avoid HTTP overhead
    while maintaining the exact same CAM logic.
    """
    # Import adaptive router internals
    from ..routers.adaptive_router import (
        _dxf_to_loops_from_bytes,
        plan,
        PlanIn,
    )

    # Extract loops from DXF bytes
    layer_name = params.get("layer_name", "GEOMETRY")
    loops = _dxf_to_loops_from_bytes(dxf_bytes, layer_name=layer_name)

    # Build PlanIn request
    climb = params.get("climb", True)
    if isinstance(climb, str):
        climb = climb.lower() == "true"

    body = PlanIn(
        loops=loops,
        units=params.get("units", "mm"),
        tool_d=float(params.get("tool_d", 6.0)),
        stepover=float(params.get("stepover", 0.45)),
        stepdown=float(params.get("stepdown", 1.5)),
        margin=float(params.get("margin", 0.0)),
        strategy=params.get("strategy", "Spiral"),
        smoothing=float(params.get("smoothing", 0.1)),
        climb=climb,
        feed_xy=float(params.get("feed_xy", 1200)),
        feed_z=float(params.get("feed_z", 300)),
        safe_z=float(params.get("safe_z", 5.0)),
        z_rough=float(params.get("z_rough", -3.0)),
    )

    # Call plan() and get result
    plan_result = plan(body)

    # Convert to dict for return
    plan_dict = plan_result.dict() if hasattr(plan_result, 'dict') else plan_result

    return {
        "request": body.dict(),
        "plan": plan_dict,
    }


def _call_gcode(request_payload: Dict[str, Any], plan_result: Dict[str, Any]) -> str:
    """
    Generate G-code from plan result using post-processor.

    Uses the same logic as the /gcode endpoint but returns text directly.
    """
    from ..routers.adaptive_router import (
        _load_post_profiles,
        _apply_adaptive_feed,
    )
    from ..routers.geometry_router import export_gcode, GcodeExportIn
    from datetime import datetime, timezone

    post_id = request_payload.get("post_id", "GRBL")
    units = request_payload.get("units", "mm")

    # Load post profiles
    post_profiles = _load_post_profiles()
    post = post_profiles.get(post_id, {})

    # Get header and footer from profile
    hdr = post.get("header", ["G90", "G17"])
    ftr = post.get("footer", ["M30"])

    # Add units command if not in header
    units_cmd = "G20" if units.lower().startswith("in") else "G21"
    if units_cmd not in hdr:
        hdr = [units_cmd] + hdr

    # Apply adaptive feed translation
    moves = plan_result.get("plan", {}).get("moves", [])
    body_lines = _apply_adaptive_feed(
        moves=moves,
        post=post,
        base_units=units,
    )

    # Add metadata comment
    now = datetime.now(timezone.utc).isoformat()
    meta_comment = f"(POST={post_id};UNITS={units};DATE={now})"

    # Assemble full program
    full_lines = hdr + [meta_comment] + body_lines + ftr
    return "\n".join(full_lines)


# =============================================================================
# Main Wrapper Endpoint
# =============================================================================

@router.post("/dxf-to-grbl", response_model=MVPWrapperResponse)
async def wrap_mvp_dxf_to_grbl(
    request: Request,
    file: UploadFile = File(..., description="DXF file to process"),
    tool_d: float = Form(6.0, description="Tool diameter (mm)"),
    stepover: float = Form(0.45, description="Stepover ratio (0-1)"),
    stepdown: float = Form(1.5, description="Step down per pass (mm)"),
    strategy: str = Form("Spiral", description="Toolpath strategy"),
    feed_xy: float = Form(1200, description="XY feed rate (mm/min)"),
    feed_z: float = Form(300, description="Z feed rate (mm/min)"),
    rapid: float = Form(3000, description="Rapid rate (mm/min)"),
    safe_z: float = Form(5.0, description="Safe Z height (mm)"),
    z_rough: float = Form(-3.0, description="Target Z depth (mm)"),
    layer_name: str = Form("GEOMETRY", description="DXF layer to process"),
    climb: bool = Form(True, description="Use climb milling"),
    smoothing: float = Form(0.1, description="Smoothing tolerance"),
    margin: float = Form(0.0, description="Boundary margin"),
    job_name: Optional[str] = Form(None, description="Job name for tracking"),
    notes: Optional[str] = Form(None, description="Operator notes"),
) -> MVPWrapperResponse:
    """
    MVP Golden Path with RMOS Wrapping.

    Executes: DXF -> plan_from_dxf -> GRBL gcode

    Then wraps with RMOS governance:
    - Creates run artifact
    - Stores content-addressed attachments (DXF, plan, gcode, manifest)
    - Records decision status

    Policy: Best-effort RMOS - returns gcode even if RMOS storage fails.
    """
    run_id = create_run_id()
    warnings: List[str] = []
    rmos_status = "ok"
    rmos_error: Optional[str] = None

    # Collect parameters
    params = {
        "tool_d": tool_d,
        "stepover": stepover,
        "stepdown": stepdown,
        "strategy": strategy,
        "feed_xy": feed_xy,
        "feed_z": feed_z,
        "rapid": rapid,
        "safe_z": safe_z,
        "z_rough": z_rough,
        "layer_name": layer_name,
        "climb": climb,
        "smoothing": smoothing,
        "margin": margin,
    }

    # Read DXF bytes
    dxf_bytes = await file.read()
    dxf_filename = file.filename or "input.dxf"

    # ==========================================================================
    # Step 1: Generate plan (existing golden path logic)
    # ==========================================================================
    try:
        plan_result = _call_plan_from_dxf(dxf_bytes, dxf_filename, params)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"DXF processing failed: {e}")

    # Extract request payload for gcode generation
    request_payload = plan_result.get("request", {})
    if not request_payload.get("loops"):
        raise HTTPException(status_code=400, detail="No geometry found in DXF")

    # Collect any warnings from plan
    plan_warnings = plan_result.get("warnings", [])
    if plan_warnings:
        warnings.extend(plan_warnings)

    # ==========================================================================
    # Step 2: Generate G-code (existing golden path logic)
    # ==========================================================================
    request_payload["post_id"] = "GRBL"
    request_payload["units"] = "mm"

    try:
        gcode_text = _call_gcode(request_payload, plan_result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"G-code generation failed: {e}")

    # ==========================================================================
    # Step 3: Compute content hashes (RMOS wrapping begins here)
    # ==========================================================================
    dxf_sha256 = sha256_of_bytes(dxf_bytes)
    plan_sha256 = sha256_of_obj(plan_result)
    gcode_sha256 = sha256_of_text(gcode_text)

    # Build manifest
    manifest = MVPManifest(
        created_at_utc=datetime.now(timezone.utc).isoformat(),
        params=params,
        dxf_sha256=dxf_sha256,
        plan_sha256=plan_sha256,
        gcode_sha256=gcode_sha256,
        git_sha=_get_git_sha(),
        warnings=warnings,
    )
    manifest_sha256 = sha256_of_obj(manifest.model_dump())

    # ==========================================================================
    # Step 4: Store attachments (content-addressed, best-effort)
    # ==========================================================================
    attachments: List[RunAttachment] = []

    try:
        # DXF input
        dxf_att, _ = put_bytes_attachment(
            dxf_bytes,
            kind="dxf_input",
            mime="application/dxf",
            filename=dxf_filename,
            ext=".dxf",
        )
        attachments.append(dxf_att)

        # Plan JSON
        plan_att, _, _ = put_json_attachment(
            plan_result,
            kind="cam_plan",
            filename="plan.json",
        )
        attachments.append(plan_att)

        # G-code output
        gcode_att, _ = put_text_attachment(
            gcode_text,
            kind="gcode_output",
            mime="text/plain",
            filename="output.nc",
            ext=".nc",
        )
        attachments.append(gcode_att)

        # Manifest
        manifest_att, _, _ = put_json_attachment(
            manifest.model_dump(),
            kind="manifest",
            filename="manifest.json",
        )
        attachments.append(manifest_att)

    except Exception as e:
        rmos_status = "partial"
        rmos_error = f"Attachment storage failed: {e}"
        warnings.append(f"RMOS attachment storage failed: {e}")

    # ==========================================================================
    # Step 5: Create RMOS run artifact (best-effort)
    # ==========================================================================
    risk_level = _compute_risk_level(warnings)

    # Build feasibility record (simple for MVP)
    feasibility = {
        "status": "PASS" if risk_level == "GREEN" else "WARN",
        "risk_level": risk_level,
        "warnings": warnings,
        "params_valid": True,
        "geometry_valid": bool(request_payload.get("loops")),
    }
    feasibility_sha256 = sha256_of_obj(feasibility)

    try:
        artifact = RunArtifact(
            run_id=run_id,
            mode="mvp_dxf_to_grbl",
            tool_id=f"endmill_{tool_d}mm",
            status="OK",
            request_summary={
                "pipeline_id": "mvp_dxf_to_grbl_v1",
                "dxf_filename": dxf_filename,
                "job_name": job_name,
                "params": params,
            },
            feasibility=feasibility,
            decision=RunDecision(
                risk_level=risk_level,
                score=100.0 if risk_level == "GREEN" else 75.0,
                warnings=warnings,
                details={
                    "policy": "best_effort",
                    "controller": "GRBL",
                },
            ),
            hashes=Hashes(
                feasibility_sha256=feasibility_sha256,
                gcode_sha256=gcode_sha256,
            ),
            outputs=RunOutputs(
                gcode_text=gcode_text if len(gcode_text) <= 200_000 else None,
                gcode_path=f"attachments/{gcode_sha256}.nc" if len(gcode_text) > 200_000 else None,
            ),
            attachments=attachments,
            meta={
                "pipeline_id": "mvp_dxf_to_grbl_v1",
                "controller": "GRBL",
                "job_name": job_name,
                "notes": notes,
                "dxf_sha256": dxf_sha256,
                "plan_sha256": plan_sha256,
                "manifest_sha256": manifest_sha256,
                "git_sha": _get_git_sha(),
            },
        )

        persist_run(artifact)

    except Exception as e:
        if rmos_status == "ok":
            rmos_status = "failed"
        else:
            rmos_status = "failed"
        rmos_error = f"Run persistence failed: {e}"
        warnings.append(f"RMOS run persistence failed: {e}")

    # ==========================================================================
    # Return response (always includes gcode per best-effort policy)
    # ==========================================================================
    return MVPWrapperResponse(
        run_id=run_id,
        status=risk_level,
        gcode_text=gcode_text,
        warnings=warnings,
        hashes={
            "dxf": dxf_sha256,
            "plan": plan_sha256,
            "gcode": gcode_sha256,
            "manifest": manifest_sha256,
        },
        rmos_status=rmos_status,
        rmos_error=rmos_error,
    )
