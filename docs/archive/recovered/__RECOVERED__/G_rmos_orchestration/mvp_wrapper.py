"""RMOS MVP Wrapper - DXF to GRBL Golden Path with Governance"""
from __future__ import annotations
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, Request

from .mvp_wrapper_schemas import (
    RMOSWrapDecision, RMOSWrapAttachmentRef, RMOSWrapHashes,
    RMOSWrapGCodeRef, RMOSWrapMvpResponse, MVPManifest,
)
from .runs_v2.schemas import RunArtifact, RunDecision, RunOutputs, Hashes, RunAttachment
from .runs_v2.store import create_run_id, persist_run
from .runs_v2.hashing import sha256_of_bytes, sha256_of_obj, sha256_of_text
from .runs_v2.attachments import put_bytes_attachment, put_json_attachment, put_text_attachment
from .feasibility import FeasibilityInput, compute_feasibility

router = APIRouter(prefix="/api/rmos/wrap/mvp", tags=["RMOS MVP Wrapper"])

GCODE_INLINE_LIMIT = 200_000  # Inline size limit for gcode (200KB)

# --- Internal Helpers ---

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
    except OSError:  # WP-1: narrowed from except Exception
        pass
    return os.getenv("GIT_SHA", None)

def _compute_risk_level(warnings: List[str]) -> str:
    """Compute risk level from warnings."""
    if not warnings:
        return "GREEN"
    return "YELLOW"

def _call_plan_from_dxf(
    dxf_bytes: bytes,
    filename: str,
    params: Dict[str, Any],
) -> Dict[str, Any]:
    """Call plan_from_dxf internally."""
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
    """Generate G-code from plan result."""
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

# --- Main Wrapper Endpoint ---

@router.post("/dxf-to-grbl", response_model=RMOSWrapMvpResponse)
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
) -> RMOSWrapMvpResponse:
    """MVP Golden Path with RMOS Wrapping."""
    run_id = create_run_id()
    warnings: List[str] = []
    rmos_status = "ok"
    rmos_error: Optional[str] = None

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

    dxf_bytes = await file.read()
    dxf_filename = file.filename or "input.dxf"
    dxf_sha256 = sha256_of_bytes(dxf_bytes)

    fi = FeasibilityInput(
        tool_d=tool_d,
        stepover=stepover,
        stepdown=stepdown,
        z_rough=z_rough,
        feed_xy=feed_xy,
        feed_z=feed_z,
        rapid=rapid,
        safe_z=safe_z,
        strategy=strategy,
        layer_name=layer_name,
        climb=climb,
        smoothing=smoothing,
        margin=margin,
        has_closed_paths=None,
        loop_count_hint=None,
        entity_count=None,
        bbox=None,
        smallest_feature_mm=None,
        post_id="GRBL",
        units="mm",
    )

    feasibility_result = compute_feasibility(fi)

    feasibility_for_hash = feasibility_result.model_dump()
    feasibility_for_hash.pop("computed_at_utc", None)
    feasibility_sha256 = sha256_of_obj(feasibility_for_hash)

    risk_level = feasibility_result.risk_level.value
    block_reason: Optional[str] = None
    if feasibility_result.blocking:
        block_reason = "; ".join(feasibility_result.blocking_reasons[:3])
        warnings.extend(feasibility_result.blocking_reasons)
    warnings.extend(feasibility_result.warnings)

    plan_result: Optional[Dict[str, Any]] = None
    gcode_text: Optional[str] = None
    cam_error: Optional[str] = None
    cam_ok = True

    try:
        plan_result = _call_plan_from_dxf(dxf_bytes, dxf_filename, params)

        # Extract request payload for gcode generation
        request_payload = plan_result.get("request", {})
        if not request_payload.get("loops"):
            cam_error = "No geometry found in DXF"
            cam_ok = False
        else:
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
            except HTTPException as e:  # WP-1: catch internal validation HTTPExceptions
                cam_error = f"G-code generation failed: {e.detail}"
                cam_ok = False
            except (ValueError, TypeError, KeyError, OSError) as e:  # WP-1: narrowed from except Exception
                cam_error = f"G-code generation failed: {e}"
                cam_ok = False

    except HTTPException as e:  # WP-1: catch internal validation HTTPExceptions (e.g., tool_d <= 0)
        cam_error = f"DXF processing failed: {e.detail}"
        cam_ok = False
    except (ValueError, TypeError, KeyError, OSError) as e:  # WP-1: narrowed from except Exception
        cam_error = f"DXF processing failed: {e}"
        cam_ok = False

    if not cam_ok:
        # Store feasibility attachment even if CAM failed
        try:
            feasibility_att, _, _ = put_json_attachment(
                feasibility_result.model_dump(),
                kind="feasibility",
                filename="feasibility.json",
            )
            attachments: List[RunAttachment] = [feasibility_att]
        except OSError:  # WP-1: narrowed from except Exception
            attachments = []

        # Build error response with feasibility info
        return RMOSWrapMvpResponse(
            ok=False,
            run_id=run_id,
            decision=RMOSWrapDecision(
                risk_level=risk_level,
                warnings=warnings,
                block_reason=block_reason or cam_error,
            ),
            hashes=RMOSWrapHashes(
                feasibility_sha256=feasibility_sha256,
                opplan_sha256=None,
                gcode_sha256=None,
                toolpaths_sha256=None,
            ),
            attachments=[
                RMOSWrapAttachmentRef(
                    kind=att.kind,
                    sha256=att.sha256,
                    filename=att.filename,
                    mime=att.mime,
                    size_bytes=att.size_bytes,
                    created_at_utc=att.created_at_utc,
                )
                for att in attachments
            ],
            gcode=RMOSWrapGCodeRef(inline=True, text=None, path=None),
            warnings=warnings,
            rmos_persisted=False,
            rmos_error=cam_error,
        )

    plan_sha256 = sha256_of_obj(plan_result)
    gcode_sha256 = sha256_of_text(gcode_text)

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

        # Feasibility (from pre-CAM check)
        feasibility_att, _, _ = put_json_attachment(
            feasibility_result.model_dump(),
            kind="feasibility",
            filename="feasibility.json",
        )
        attachments.append(feasibility_att)

    except OSError as e:  # WP-1: narrowed from except Exception
        rmos_status = "partial"
        rmos_error = f"Attachment storage failed: {e}"
        warnings.append(f"RMOS attachment storage failed: {e}")

    if risk_level == "GREEN":
        score = 100.0
    elif risk_level == "YELLOW":
        score = 75.0
    else:  # RED
        score = 25.0

    try:
        artifact = RunArtifact(
            run_id=run_id,
            mode="mvp_dxf_to_grbl",
            tool_id=f"endmill_{tool_d}mm",
            status="BLOCKED" if feasibility_result.blocking else "OK",
            request_summary={
                "pipeline_id": "mvp_dxf_to_grbl_v1",
                "dxf_filename": dxf_filename,
                "job_name": job_name,
                "params": params,
            },
            feasibility=feasibility_result.model_dump(),
            decision=RunDecision(
                risk_level=risk_level,
                score=score,
                block_reason=block_reason,
                warnings=warnings,
                details={
                    "policy": "best_effort",
                    "controller": "GRBL",
                    "engine_version": feasibility_result.engine_version,
                    "blocking": feasibility_result.blocking,
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

    except (OSError, ValueError, TypeError) as e:  # WP-1: narrowed from except Exception
        if rmos_status == "ok":
            rmos_status = "failed"
        else:
            rmos_status = "failed"
        rmos_error = f"Run persistence failed: {e}"
        warnings.append(f"RMOS run persistence failed: {e}")

    # ==========================================================================
    # Return response (always includes gcode per best-effort policy)
    # ==========================================================================

    attachment_refs = [
        RMOSWrapAttachmentRef(
            kind=att.kind,
            sha256=att.sha256,
            filename=att.filename,
            mime=att.mime,
            size_bytes=att.size_bytes,
            created_at_utc=att.created_at_utc,
        )
        for att in attachments
    ]

    gcode_inline = len(gcode_text) <= GCODE_INLINE_LIMIT
    gcode_ref = RMOSWrapGCodeRef(
        inline=gcode_inline,
        text=gcode_text if gcode_inline else None,
        path=f"attachments/{gcode_sha256}.nc" if not gcode_inline else None,
    )

    return RMOSWrapMvpResponse(
        ok=True,
        run_id=run_id,
        decision=RMOSWrapDecision(
            risk_level=risk_level,
            warnings=warnings,
            block_reason=block_reason,
        ),
        hashes=RMOSWrapHashes(
            feasibility_sha256=feasibility_sha256,
            opplan_sha256=plan_sha256,
            gcode_sha256=gcode_sha256,
            toolpaths_sha256=None,
        ),
        attachments=attachment_refs,
        gcode=gcode_ref,
        warnings=warnings,
        rmos_persisted=(rmos_status == "ok"),
        rmos_error=rmos_error,
    )
