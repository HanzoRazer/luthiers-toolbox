"""Retract G-code Router - G-code generation (draft and governed lanes).

Provides:
- POST /gcode - Simple retract G-code (draft lane)
- POST /gcode_governed - Simple retract G-code (governed lane with RMOS artifacts)
- POST /gcode/download - Download optimized G-code (draft lane)
- POST /gcode/download_governed - Download optimized G-code (governed lane)

Total: 4 routes for G-code generation.

LANE: OPERATION (draft and governed variants)
"""
from datetime import datetime, timezone

from fastapi import APIRouter
from fastapi.responses import Response

from app.safety import safety_critical

from ...rmos.runs_v2 import (
    RunArtifact,
    RunDecision,
    Hashes,
    persist_run,
    create_run_id,
    sha256_of_obj,
    sha256_of_text,
)
from .retract_apply_router import RetractStrategyIn, apply_retract_strategy

router = APIRouter(tags=["Retract", "G-code"])


# ---------------------------------------------------------------------------
# Draft Lane Endpoints
# ---------------------------------------------------------------------------

@router.post("/gcode", response_class=Response)
@safety_critical
def generate_simple_retract_gcode(
    strategy: str = "direct",
    current_z: float = -10.0,
    safe_z: float = 5.0,
    ramp_feed: float = 600.0,
    helix_radius: float = 5.0,
    helix_pitch: float = 1.0
) -> Response:
    """Generate simple retract G-code (for CAM Essentials Lab UI)."""
    gcode_lines = [
        "G21 G90",
        f"(Retract Strategy: {strategy})",
        f"(Current Z: {current_z}mm → Safe Z: {safe_z}mm)",
        ""
    ]

    z_travel = safe_z - current_z

    if strategy == "direct":
        # Instant rapid to safe Z
        gcode_lines.append(f"G0 Z{safe_z:.4f}")
        gcode_lines.append("(Direct rapid retract)")

    elif strategy == "ramped":
        # Linear ramp at controlled feed
        gcode_lines.append(f"G1 Z{safe_z:.4f} F{ramp_feed:.0f}")
        gcode_lines.append("(Ramped retract for delicate parts)")

    elif strategy == "helical":
        # Spiral up with Z lift (simplified for demonstration)
        revolutions = int(z_travel / helix_pitch) + 1
        for i in range(revolutions):
            z_step = current_z + (i + 1) * helix_pitch
            if z_step > safe_z:
                z_step = safe_z
            # Circular interpolation (simplified - full circle per step)
            gcode_lines.append(f"G2 X0 Y0 I{helix_radius:.4f} J0 Z{z_step:.4f} F{ramp_feed:.0f}")
            if z_step >= safe_z:
                break
        gcode_lines.append("(Helical retract - safest for finished surfaces)")

    gcode_lines.append("")
    gcode_lines.append("M30")
    gcode_lines.append("(End of retract sequence)")

    gcode_text = "\n".join(gcode_lines)

    resp = Response(
        content=gcode_text,
        media_type="text/plain",
        headers={"Content-Type": "text/plain"}
    )
    resp.headers["X-ToolBox-Lane"] = "draft"
    return resp


@router.post("/gcode/download", response_class=Response)
@safety_critical
def download_retract_gcode(body: RetractStrategyIn) -> Response:
    """
    Generate and download G-code with retract optimization.

    Returns .nc file ready for CNC controller.
    """
    # Apply strategy (reuse apply endpoint logic)
    result = apply_retract_strategy(body)

    # Build complete G-code
    gcode_lines = [
        "G21 G90",
        f"(Strategy: {body.strategy})",
        f"(Features: {len(body.features)})",
        ""
    ]
    gcode_lines.extend(result["gcode"])
    gcode_lines.append("")
    gcode_lines.append("M30")
    gcode_lines.append("(End of program)")

    gcode_text = "\n".join(gcode_lines)

    # Return as downloadable file
    resp = Response(
        content=gcode_text,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename=retract_{body.strategy}.nc"
        }
    )
    resp.headers["X-ToolBox-Lane"] = "draft"
    return resp


# ---------------------------------------------------------------------------
# Governed Lane Endpoints (with RMOS artifact persistence)
# ---------------------------------------------------------------------------

@router.post("/gcode_governed", response_class=Response)
@safety_critical
def generate_simple_retract_gcode_governed(
    strategy: str = "direct",
    current_z: float = -10.0,
    safe_z: float = 5.0,
    ramp_feed: float = 600.0,
    helix_radius: float = 5.0,
    helix_pitch: float = 1.0
) -> Response:
    """Generate simple retract G-code (GOVERNED lane)."""
    gcode_lines = [
        "G21 G90",
        f"(Retract Strategy: {strategy})",
        f"(Current Z: {current_z}mm -> Safe Z: {safe_z}mm)",
        ""
    ]

    z_travel = safe_z - current_z

    if strategy == "direct":
        gcode_lines.append(f"G0 Z{safe_z:.4f}")
        gcode_lines.append("(Direct rapid retract)")

    elif strategy == "ramped":
        gcode_lines.append(f"G1 Z{safe_z:.4f} F{ramp_feed:.0f}")
        gcode_lines.append("(Ramped retract for delicate parts)")

    elif strategy == "helical":
        revolutions = int(z_travel / helix_pitch) + 1
        for i in range(revolutions):
            z_step = current_z + (i + 1) * helix_pitch
            if z_step > safe_z:
                z_step = safe_z
            gcode_lines.append(f"G2 X0 Y0 I{helix_radius:.4f} J0 Z{z_step:.4f} F{ramp_feed:.0f}")
            if z_step >= safe_z:
                break
        gcode_lines.append("(Helical retract - safest for finished surfaces)")

    gcode_lines.append("")
    gcode_lines.append("M30")
    gcode_lines.append("(End of retract sequence)")

    gcode_text = "\n".join(gcode_lines)

    # Create RMOS artifact
    now = datetime.now(timezone.utc).isoformat()
    request_hash = sha256_of_obj({
        "strategy": strategy,
        "current_z": current_z,
        "safe_z": safe_z,
        "ramp_feed": ramp_feed,
        "helix_radius": helix_radius,
        "helix_pitch": helix_pitch
    })
    gcode_hash = sha256_of_text(gcode_text)

    run_id = create_run_id()
    artifact = RunArtifact(
        run_id=run_id,
        created_at_utc=now,
        tool_id="retract_gcode",
        mode="retract",
        event_type="retract_gcode_execution",
        status="OK",
        decision=RunDecision(risk_level="GREEN"),
        hashes=Hashes(
            feasibility_sha256=request_hash,
            gcode_sha256=gcode_hash,
        ),
    )
    persist_run(artifact)

    resp = Response(
        content=gcode_text,
        media_type="text/plain",
        headers={"Content-Type": "text/plain"}
    )
    resp.headers["X-Run-ID"] = run_id
    resp.headers["X-GCode-SHA256"] = gcode_hash
    resp.headers["X-ToolBox-Lane"] = "governed"
    return resp


@router.post("/gcode/download_governed", response_class=Response)
@safety_critical
def download_retract_gcode_governed(body: RetractStrategyIn) -> Response:
    """Generate and download G-code with retract optimization (GOVERNED lane)."""
    # Apply strategy (reuse apply endpoint logic)
    result = apply_retract_strategy(body)

    # Build complete G-code
    gcode_lines = [
        "G21 G90",
        f"(Strategy: {body.strategy})",
        f"(Features: {len(body.features)})",
        ""
    ]
    gcode_lines.extend(result["gcode"])
    gcode_lines.append("")
    gcode_lines.append("M30")
    gcode_lines.append("(End of program)")

    gcode_text = "\n".join(gcode_lines)

    # Create RMOS artifact
    now = datetime.now(timezone.utc).isoformat()
    request_hash = sha256_of_obj(body.model_dump(mode="json"))
    gcode_hash = sha256_of_text(gcode_text)

    run_id = create_run_id()
    artifact = RunArtifact(
        run_id=run_id,
        created_at_utc=now,
        tool_id="retract_download_gcode",
        mode="retract",
        event_type="retract_download_gcode_execution",
        status="OK",
        decision=RunDecision(risk_level="GREEN"),
        hashes=Hashes(
            feasibility_sha256=request_hash,
            gcode_sha256=gcode_hash,
        ),
    )
    persist_run(artifact)

    # Return as downloadable file
    resp = Response(
        content=gcode_text,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename=retract_{body.strategy}.nc"
        }
    )
    resp.headers["X-Run-ID"] = run_id
    resp.headers["X-GCode-SHA256"] = gcode_hash
    resp.headers["X-ToolBox-Lane"] = "governed"
    return resp


__all__ = ["router"]
