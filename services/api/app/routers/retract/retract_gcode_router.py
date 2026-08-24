"""Retract G-code Router - G-code generation (all lanes governed).

Provides:
- POST /gcode - Simple retract G-code
- POST /gcode_governed - Simple retract G-code (retained path; same authority)
- POST /gcode/download - Download optimized G-code
- POST /gcode/download_governed - Download optimized G-code (retained path; same authority)

Total: 4 routes for G-code generation.

LANE: OPERATION

RMOS-CONVERGE-001B — retract capability convergence
---------------------------------------------------
Owner ruling, 2026-08-23: **all four mounted retract G-code routes are subject
to the same RMOS production authority.** The governing unit is the production
capability, not the ``_governed`` suffix. An ungoverned convenience endpoint is
not an accepted alternate production path.

Before this change the capability carried two different defects:

* the ``_governed`` pair **manufactured its own authority** — it built the
  G-code first, then minted ``RunDecision(risk_level="GREEN")`` and persisted a
  governed-looking run around output that no evaluator had ever assessed;
* the plain pair **bypassed RMOS entirely** — it emitted the same
  machine-consumable G-code (including a ``.nc`` download) with no run, no
  decision and no hash.

Both are now routed through the single 001A authority boundary *before* any
G-code exists. There is no substantive retract feasibility evaluator, so the
capability currently resolves ``UNKNOWN`` and is **blocked by design** — see
``_PRODUCTION_FEASIBILITY_ENGINES``. No retract evaluator was invented to keep
the lane green.

The generation helpers below are pure builders: they are only reached after
``_authorize_retract`` returns, so blocking is structural rather than a matter
of statement order.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from app.safety import safety_critical

from ...rmos.api.rmos_feasibility_router import compute_feasibility_internal
from ...rmos.policies import SafetyPolicy
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
# Authority boundary (RMOS-CONVERGE-001B)
# ---------------------------------------------------------------------------

def _authorize_retract(
    *,
    tool_id: str,
    event_type: str,
    mode_suffix: str,
    request_summary: Dict[str, Any],
) -> Tuple[str, Dict[str, Any], str]:
    """
    Obtain the server-authoritative decision for a retract request.

    Returns ``(run_id, feasibility, feasibility_sha256)`` when the operation is
    authorized. Raises HTTP 409 — after persisting a BLOCKED run for audit —
    when it is not.

    This runs **before** any G-code is built. The caller cannot emit an
    artifact without first passing through here.
    """
    now = datetime.now(timezone.utc).isoformat()

    feasibility = compute_feasibility_internal(
        tool_id=tool_id,
        req={"tool_id": tool_id, **request_summary},
        context=event_type,
    )
    decision = SafetyPolicy.extract_safety_decision(feasibility)
    risk_level = decision.risk_level_str()
    feas_hash = sha256_of_obj(feasibility)
    run_id = create_run_id()

    if SafetyPolicy.should_block(decision.risk_level):
        # Blocked attempts stay auditable, but carry no executable artifact:
        # no gcode_sha256, no output, no attachment.
        persist_run(
            RunArtifact(
                run_id=run_id,
                created_at_utc=now,
                tool_id=tool_id,
                mode=f"retract{mode_suffix}",
                event_type=f"{event_type}_blocked",
                status="BLOCKED",
                request_summary=request_summary,
                feasibility=feasibility,
                decision=RunDecision(
                    risk_level=risk_level,
                    block_reason=f"Blocked by safety policy: {risk_level}",
                    warnings=list(decision.warnings),
                ),
                hashes=Hashes(feasibility_sha256=feas_hash),
                notes=f"Blocked by safety policy: {risk_level}",
            )
        )
        raise HTTPException(
            status_code=409,
            detail={
                "error": "SAFETY_BLOCKED",
                "message": "Retract G-code generation blocked by server-side safety policy.",
                "run_id": run_id,
                "decision": decision.to_dict(),
                "authoritative_feasibility": feasibility,
            },
        )

    return run_id, feasibility, feas_hash


def _persist_authorized_run(
    *,
    run_id: str,
    tool_id: str,
    mode_suffix: str,
    event_type: str,
    request_summary: Dict[str, Any],
    feasibility: Dict[str, Any],
    feas_hash: str,
    gcode_text: str,
) -> str:
    """Bind an authorized artifact to the run that authorized it. Returns the G-code hash."""
    gcode_hash = sha256_of_text(gcode_text)
    persist_run(
        RunArtifact(
            run_id=run_id,
            created_at_utc=datetime.now(timezone.utc).isoformat(),
            tool_id=tool_id,
            mode=f"retract{mode_suffix}",
            event_type=f"{event_type}_execution",
            status="OK",
            request_summary=request_summary,
            feasibility=feasibility,
            decision=RunDecision(
                risk_level=SafetyPolicy.extract_safety_decision(feasibility).risk_level_str(),
            ),
            hashes=Hashes(feasibility_sha256=feas_hash, gcode_sha256=gcode_hash),
        )
    )
    return gcode_hash


# ---------------------------------------------------------------------------
# Pure G-code builders (reached only after authorization)
# ---------------------------------------------------------------------------

def _build_simple_retract_gcode(
    strategy: str,
    current_z: float,
    safe_z: float,
    ramp_feed: float,
    helix_radius: float,
    helix_pitch: float,
) -> str:
    """Build simple retract G-code. Pure builder — performs no authority check."""
    gcode_lines: List[str] = [
        "G21 G90",
        f"(Retract Strategy: {strategy})",
        f"(Current Z: {current_z}mm -> Safe Z: {safe_z}mm)",
        "",
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
            gcode_lines.append(
                f"G2 X0 Y0 I{helix_radius:.4f} J0 Z{z_step:.4f} F{ramp_feed:.0f}"
            )
            if z_step >= safe_z:
                break
        gcode_lines.append("(Helical retract - safest for finished surfaces)")

    gcode_lines.append("")
    gcode_lines.append("M30")
    gcode_lines.append("(End of retract sequence)")

    return "\n".join(gcode_lines)


def _build_download_retract_gcode(body: RetractStrategyIn) -> str:
    """Build optimized retract G-code for download. Pure builder — no authority check."""
    result = apply_retract_strategy(body)

    gcode_lines: List[str] = [
        "G21 G90",
        f"(Strategy: {body.strategy})",
        f"(Features: {len(body.features)})",
        "",
    ]
    gcode_lines.extend(result["gcode"])
    gcode_lines.append("")
    gcode_lines.append("M30")
    gcode_lines.append("(End of program)")

    return "\n".join(gcode_lines)


# ---------------------------------------------------------------------------
# Endpoints — all four share one authority outcome
# ---------------------------------------------------------------------------

def _simple_request_summary(
    strategy: str, current_z: float, safe_z: float,
    ramp_feed: float, helix_radius: float, helix_pitch: float,
) -> Dict[str, Any]:
    return {
        "strategy": strategy,
        "current_z": current_z,
        "safe_z": safe_z,
        "ramp_feed": ramp_feed,
        "helix_radius": helix_radius,
        "helix_pitch": helix_pitch,
    }


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
    """Generate simple retract G-code (governed)."""
    summary = _simple_request_summary(
        strategy, current_z, safe_z, ramp_feed, helix_radius, helix_pitch
    )
    run_id, feasibility, feas_hash = _authorize_retract(
        tool_id=f"retract:{strategy}",
        event_type="retract_gcode",
        mode_suffix="",
        request_summary=summary,
    )

    gcode_text = _build_simple_retract_gcode(
        strategy, current_z, safe_z, ramp_feed, helix_radius, helix_pitch
    )
    gcode_hash = _persist_authorized_run(
        run_id=run_id, tool_id=f"retract:{strategy}", mode_suffix="",
        event_type="retract_gcode", request_summary=summary,
        feasibility=feasibility, feas_hash=feas_hash, gcode_text=gcode_text,
    )

    resp = Response(
        content=gcode_text,
        media_type="text/plain",
        headers={"Content-Type": "text/plain"},
    )
    resp.headers["X-Run-ID"] = run_id
    resp.headers["X-GCode-SHA256"] = gcode_hash
    resp.headers["X-ToolBox-Lane"] = "governed"
    return resp


@router.post("/gcode/download", response_class=Response)
@safety_critical
def download_retract_gcode(body: RetractStrategyIn) -> Response:
    """
    Generate and download G-code with retract optimization (governed).

    Returns .nc file ready for CNC controller.
    """
    summary = body.model_dump(mode="json")
    run_id, feasibility, feas_hash = _authorize_retract(
        tool_id=f"retract:{body.strategy}",
        event_type="retract_download_gcode",
        mode_suffix="_download",
        request_summary=summary,
    )

    gcode_text = _build_download_retract_gcode(body)
    gcode_hash = _persist_authorized_run(
        run_id=run_id, tool_id=f"retract:{body.strategy}", mode_suffix="_download",
        event_type="retract_download_gcode", request_summary=summary,
        feasibility=feasibility, feas_hash=feas_hash, gcode_text=gcode_text,
    )

    resp = Response(
        content=gcode_text,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename=retract_{body.strategy}.nc"
        },
    )
    resp.headers["X-Run-ID"] = run_id
    resp.headers["X-GCode-SHA256"] = gcode_hash
    resp.headers["X-ToolBox-Lane"] = "governed"
    return resp


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
    """
    Generate simple retract G-code.

    Retained for compatibility. Carries the same authority as ``/gcode``; the
    ``_governed`` suffix no longer denotes a different lane.
    """
    return generate_simple_retract_gcode(
        strategy=strategy,
        current_z=current_z,
        safe_z=safe_z,
        ramp_feed=ramp_feed,
        helix_radius=helix_radius,
        helix_pitch=helix_pitch,
    )


@router.post("/gcode/download_governed", response_class=Response)
@safety_critical
def download_retract_gcode_governed(body: RetractStrategyIn) -> Response:
    """
    Generate and download G-code with retract optimization.

    Retained for compatibility. Carries the same authority as
    ``/gcode/download``; the ``_governed`` suffix no longer denotes a different lane.
    """
    return download_retract_gcode(body)


__all__ = ["router"]
