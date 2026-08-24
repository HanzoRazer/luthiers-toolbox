"""Retract G-code Router - G-code generation (all lanes governed).

Provides:
- POST /gcode - Simple retract G-code (governed; formerly draft)
- POST /gcode_governed - Alias of /gcode; same authority and headers
- POST /gcode/download - Download optimized G-code (governed; formerly draft)
- POST /gcode/download_governed - Alias of /gcode/download; same authority and headers

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
  decision and no hash, and advertised ``X-ToolBox-Lane: draft``.

Both are now routed through the single 001A authority boundary *before* any
G-code exists. There is no substantive retract feasibility evaluator, so the
capability currently resolves ``UNKNOWN`` and is **blocked by design** — see
``_PRODUCTION_FEASIBILITY_ENGINES``. No retract evaluator was invented to keep
the lane green.

**Contract change (explicit, not implicit):**
``POST /api/cam/retract/gcode`` and ``POST /api/cam/retract/gcode/download``
are no longer draft-lane endpoints. They keep the old paths for compatibility
but inherit governed semantics and governed headers:

* current behaviour: ``409 SAFETY_BLOCKED`` (no G-code body, no ``.nc``
  attachment, no ``X-GCode-SHA256``)
* headers on every response, including 409: ``X-ToolBox-Lane: governed``,
  ``X-Run-ID``
* when a retract evaluator is later registered, these paths stay governed;
  they will **not** revert to ``X-ToolBox-Lane: draft``

The ``_governed`` suffix is a retained alias, not a second lane.

The generation helpers below are pure builders: they are only reached after
``_authorize_retract`` returns, so blocking is structural rather than a matter
of statement order.

Both persistence paths go through ``validate_and_persist`` — the alternative
``FENCE_REGISTRY.json`` (profile ``artifact_authority``) prescribes — so this
router constructs no run-authority objects of its own at all. That is the same
principle as the rest of 001B applied one level down: the module that grants
authority is the module that shapes the record of it.
"""
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

from app.safety import safety_critical

from ...rmos.api.rmos_feasibility_router import compute_feasibility_internal
from ...rmos.policies import SafetyPolicy
from ...rmos.runs_v2 import (
    create_run_id,
    sha256_of_obj,
    sha256_of_text,
    validate_and_persist,
)
from .retract_apply_router import RetractStrategyIn, apply_retract_strategy

router = APIRouter(tags=["Retract", "G-code"])

# RMOS run `mode` values for this capability. Spelled out rather than assembled
# from a suffix so the audit label is greppable.
_MODE_SIMPLE = "retract"
_MODE_DOWNLOAD = "retract_download"

# All four retract G-code paths, including the former draft URLs, advertise
# the governed lane. This is a contract change: consumers that branched on
# X-ToolBox-Lane: draft must treat these paths as governed.
_GOVERNED_LANE = "governed"

# Shared Query() objects for /gcode and /gcode_governed.
#
# FastAPI already binds unannotated scalars as query params (a JSON body is
# ignored). Query() makes that contract visible in OpenAPI so callers do not
# confuse these routes with /gcode/download, which takes RetractStrategyIn as
# a JSON body. The objects are shared so the alias cannot drift from the
# plain route's defaults.
_Q_STRATEGY = Query(
    "direct",
    description=(
        "Retract strategy: direct, ramped, or helical. "
        "Bound from the query string; a JSON body is ignored."
    ),
)
_Q_CURRENT_Z = Query(-10.0, description="Current tool Z in mm")
_Q_SAFE_Z = Query(5.0, description="Safe retract Z in mm")
_Q_RAMP_FEED = Query(600.0, description="Feed for ramped/helical retract, mm/min")
_Q_HELIX_RADIUS = Query(5.0, description="Helical retract radius in mm")
_Q_HELIX_PITCH = Query(1.0, description="Helical retract pitch, mm/rev")


def _governed_headers(run_id: str, *, gcode_sha256: Optional[str] = None) -> Dict[str, str]:
    headers = {
        "X-Run-ID": run_id,
        "X-ToolBox-Lane": _GOVERNED_LANE,
    }
    if gcode_sha256 is not None:
        headers["X-GCode-SHA256"] = gcode_sha256
    return headers


# ---------------------------------------------------------------------------
# Authority boundary (RMOS-CONVERGE-001B)
# ---------------------------------------------------------------------------

def _authorize_retract(
    *,
    tool_id: str,
    event_type: str,
    mode: str,
    request_summary: Dict[str, Any],
) -> Tuple[str, Dict[str, Any], str, str]:
    """
    Obtain the server-authoritative decision for a retract request.

    Returns ``(run_id, feasibility, feasibility_sha256, risk_level)`` when the
    operation is authorized. Raises HTTP 409 — after persisting a BLOCKED run
    for audit — when it is not.

    ``risk_level`` is returned rather than re-derived downstream so exactly one
    call site interprets the feasibility result: the authorized artifact records
    the same decision that authorized it, by construction.

    This runs **before** any G-code is built. The caller cannot emit an
    artifact without first passing through here.
    """
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
        validate_and_persist(
            run_id=run_id,
            mode=mode,
            tool_id=tool_id,
            event_type=f"{event_type}_blocked",
            status="BLOCKED",
            request_summary=request_summary,
            feasibility=feasibility,
            feasibility_sha256=feas_hash,
            risk_level=risk_level,
            block_reason=f"Blocked by safety policy: {risk_level}",
            decision_warnings=list(decision.warnings),
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
            headers=_governed_headers(run_id),
        )

    return run_id, feasibility, feas_hash, risk_level


def _persist_authorized_run(
    *,
    run_id: str,
    tool_id: str,
    mode: str,
    event_type: str,
    request_summary: Dict[str, Any],
    feasibility: Dict[str, Any],
    feas_hash: str,
    risk_level: str,
    gcode_text: str,
) -> str:
    """Bind an authorized artifact to the run that authorized it. Returns the G-code hash.

    ``risk_level`` is the decision produced by ``_authorize_retract``; it is not
    re-derived here, so the recorded decision cannot drift from the one that
    actually granted authority.
    """
    gcode_hash = sha256_of_text(gcode_text)
    validate_and_persist(
        run_id=run_id,
        mode=mode,
        tool_id=tool_id,
        event_type=f"{event_type}_execution",
        status="OK",
        request_summary=request_summary,
        feasibility=feasibility,
        feasibility_sha256=feas_hash,
        risk_level=risk_level,
        gcode_sha256=gcode_hash,
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

    else:
        # No motion block matched. Emitting the header-only program would put a
        # file named retract_<strategy>.nc in front of an operator that retracts
        # nothing. Fail instead.
        raise ValueError(
            f"unsupported retract strategy {strategy!r}; "
            f"expected one of: direct, ramped, helical"
        )

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
    strategy: str = _Q_STRATEGY,
    current_z: float = _Q_CURRENT_Z,
    safe_z: float = _Q_SAFE_Z,
    ramp_feed: float = _Q_RAMP_FEED,
    helix_radius: float = _Q_HELIX_RADIUS,
    helix_pitch: float = _Q_HELIX_PITCH,
) -> Response:
    """Generate simple retract G-code.

    **Not a draft lane.** This path previously returned ``200`` with
    ``X-ToolBox-Lane: draft`` and no RMOS involvement. It now shares governed
    authority and governed headers with ``/gcode_governed``. Currently
    ``409 SAFETY_BLOCKED`` until a retract evaluator exists; if one is later
    registered this path remains governed and will not revert to draft.

    Parameters are **query-string bound**, not a JSON body. A JSON body is
    ignored (the pre-#315 Vue client POSTed JSON and silently received
    defaults). ``POST /gcode/download`` is the body-model route.
    """
    summary = _simple_request_summary(
        strategy, current_z, safe_z, ramp_feed, helix_radius, helix_pitch
    )
    run_id, feasibility, feas_hash, risk_level = _authorize_retract(
        tool_id=f"retract:{strategy}",
        event_type="retract_gcode",
        mode=_MODE_SIMPLE,
        request_summary=summary,
    )

    gcode_text = _build_simple_retract_gcode(
        strategy, current_z, safe_z, ramp_feed, helix_radius, helix_pitch
    )
    gcode_hash = _persist_authorized_run(
        run_id=run_id, tool_id=f"retract:{strategy}", mode=_MODE_SIMPLE,
        event_type="retract_gcode", request_summary=summary,
        feasibility=feasibility, feas_hash=feas_hash, risk_level=risk_level,
        gcode_text=gcode_text,
    )

    resp = Response(
        content=gcode_text,
        media_type="text/plain",
        headers={"Content-Type": "text/plain"},
    )
    resp.headers.update(_governed_headers(run_id, gcode_sha256=gcode_hash))
    return resp


@router.post("/gcode/download", response_class=Response)
@safety_critical
def download_retract_gcode(body: RetractStrategyIn) -> Response:
    """
    Generate and download G-code with retract optimization.

    **Not a draft lane.** This path previously returned a ``.nc`` attachment
    with ``X-ToolBox-Lane: draft`` and no RMOS involvement. It now shares
    governed authority and governed headers with ``/gcode/download_governed``.
    Currently ``409 SAFETY_BLOCKED`` until a retract evaluator exists; if one
    is later registered this path remains governed and will not revert to draft.
    """
    summary = body.model_dump(mode="json")
    run_id, feasibility, feas_hash, risk_level = _authorize_retract(
        tool_id=f"retract:{body.strategy}",
        event_type="retract_download_gcode",
        mode=_MODE_DOWNLOAD,
        request_summary=summary,
    )

    gcode_text = _build_download_retract_gcode(body)
    gcode_hash = _persist_authorized_run(
        run_id=run_id, tool_id=f"retract:{body.strategy}", mode=_MODE_DOWNLOAD,
        event_type="retract_download_gcode", request_summary=summary,
        feasibility=feasibility, feas_hash=feas_hash, risk_level=risk_level,
        gcode_text=gcode_text,
    )

    resp = Response(
        content=gcode_text,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename=retract_{body.strategy}.nc"
        },
    )
    resp.headers.update(_governed_headers(run_id, gcode_sha256=gcode_hash))
    return resp


@router.post("/gcode_governed", response_class=Response)
@safety_critical
def generate_simple_retract_gcode_governed(
    strategy: str = _Q_STRATEGY,
    current_z: float = _Q_CURRENT_Z,
    safe_z: float = _Q_SAFE_Z,
    ramp_feed: float = _Q_RAMP_FEED,
    helix_radius: float = _Q_HELIX_RADIUS,
    helix_pitch: float = _Q_HELIX_PITCH,
) -> Response:
    """
    Generate simple retract G-code.

    Retained alias of ``/gcode``. Same authority, same governed headers; the
    ``_governed`` suffix no longer denotes a different lane. Query-string
    bound, same as ``/gcode`` — a JSON body is ignored.
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

    Retained alias of ``/gcode/download``. Same authority, same governed
    headers; the ``_governed`` suffix no longer denotes a different lane.
    """
    return download_retract_gcode(body)


__all__ = ["router"]
