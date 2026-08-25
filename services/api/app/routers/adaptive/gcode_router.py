"""
Adaptive Pocketing G-code Router
================================

G-code export endpoint for adaptive pocket toolpath.

LANE: OPERATION (GOVERNED)
Reference: docs/OPERATION_EXECUTION_GOVERNANCE_v1.md

Endpoints:
- POST /gcode: Export G-code with post-processor headers/footers
"""

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from app.middleware.rate_limit import limiter, rate_limit_tier

from app.schemas.adaptive_schemas import GcodeIn
from ..geometry_schemas import GcodeExportIn
from ..geometry.export_router import export_gcode

from .helpers import (
    _load_post_profiles,
    _merge_adaptive_override,
    _apply_adaptive_feed,
)
from .plan_router import _enforce_safety_policy, plan

# Import run artifact persistence (OPERATION lane requirement)
from ...rmos.runs_v2 import (
    RunArtifact,
    RunDecision,
    Hashes,
    persist_run,
    create_run_id,
    sha256_of_text,
)

router = APIRouter(tags=["cam-adaptive"])


@router.post("/gcode", response_class=StreamingResponse)
@limiter.limit(rate_limit_tier("cam"))
def gcode(request: Request, body: GcodeIn) -> StreamingResponse:
    """
    Generate post-processor aware G-code for adaptive pocket (GOVERNED lane).

    This endpoint has full RMOS artifact persistence with SHA256 hashes.

    Transforms toolpath moves into machine-specific G-code with headers,
    footers, unit commands, metadata comments, and adaptive feed translation.

    Args:
        body: GcodeIn request model with geometry, machining params, and post config

    Returns:
        StreamingResponse with G-code file (.nc extension)
        Content-Type: application/octet-stream
        Content-Disposition: attachment; filename="<job_name>_<post>.nc"

    Raises:
        HTTPException 400: If loops invalid or post_id not found
        HTTPException 409: If safety policy blocks the operation
    """
    # Validate post_id if provided
    post_profiles = _load_post_profiles()
    if body.post_id:
        valid_post_ids = list(post_profiles.keys())
        if body.post_id not in valid_post_ids:
            raise HTTPException(400, f"Invalid post_id '{body.post_id}'. Available: {', '.join(valid_post_ids)}")

    # --- Server-side feasibility enforcement (RMOS-CONVERGE-001B-B2) ---
    #
    # This route used to inherit authority implicitly: it called plan(), which
    # gates internally, and then recorded RunDecision(risk_level="GREEN") with
    # feasibility_sha256 set to a hash of the *request*. Authority was really
    # being consumed, but the artifact did not say what the evaluator said — a
    # YELLOW plan was persisted as GREEN, against a hash that was not a
    # feasibility hash. The decision is now obtained explicitly, from the same
    # helper plan() uses, so the recorded decision is the one that authorised
    # the operation.
    #
    # This gate runs before any G-code exists. plan() re-evaluates internally;
    # compute_feasibility_internal is deterministic, so both agree.
    plan_request_dict = body.model_dump(mode="json")
    feasibility, risk_level, feas_hash = _enforce_safety_policy(plan_request_dict)

    # Generate toolpath using /plan logic
    plan_out = plan(body)

    # Load post profiles for adaptive feed configuration
    post = post_profiles.get(body.post_id or "GRBL")

    # Apply user override if provided (merge with post profile defaults)
    post = _merge_adaptive_override(
        post,
        body.adaptive_feed_override.dict() if body.adaptive_feed_override else None
    )

    # Get header and footer from profile (with fallback)
    hdr = post.get("header", ["G90", "G17"]) if post else ["G90", "G17"]
    ftr = post.get("footer", ["M30"]) if post else ["M30"]

    # Add units command if not already in header
    units_cmd = "G20" if body.units.lower().startswith("in") else "G21"
    if units_cmd not in hdr:
        hdr = [units_cmd] + hdr

    # Apply adaptive feed translation (comment/inline_f/mcode)
    body_lines = _apply_adaptive_feed(
        moves=plan_out["moves"],
        post=post,
        base_units=body.units
    )

    # Add metadata comment
    meta = f"(POST={body.post_id or 'GRBL'};UNITS={body.units};DATE={datetime.utcnow().isoformat()}Z)"

    # Assemble full program
    program = "\n".join(hdr + [meta] + body_lines + ftr) + "\n"

    # Create artifact for OPERATION lane compliance.
    #
    # The decision and the feasibility hash both come from the gate above, so
    # the record cannot drift from the authority that granted it.
    now = datetime.now(timezone.utc).isoformat()
    gcode_hash = sha256_of_text(program)

    run_id = create_run_id()
    artifact = RunArtifact(
        run_id=run_id,
        created_at_utc=now,
        tool_id="adaptive:gcode",
        mode="adaptive",
        event_type="adaptive_gcode_execution",
        status="OK",
        feasibility=feasibility,
        decision=RunDecision(risk_level=risk_level),
        hashes=Hashes(
            feasibility_sha256=feas_hash,
            gcode_sha256=gcode_hash,
        ),
    )
    persist_run(artifact)

    response = export_gcode(GcodeExportIn(gcode=program, units=body.units, post_id=body.post_id))
    response.headers["X-Run-ID"] = run_id
    response.headers["X-GCode-SHA256"] = gcode_hash
    response.headers["X-ToolBox-Lane"] = "governed"
    return response
