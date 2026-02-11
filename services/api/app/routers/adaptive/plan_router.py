"""
Adaptive Pocketing Plan Router
==============================

Core planning endpoints for adaptive pocket toolpath generation.

LANE: OPERATION
Reference: docs/OPERATION_EXECUTION_GOVERNANCE_v1.md

Endpoints:
- POST /plan: Generate toolpath from boundary loops
- POST /sim: Simulate toolpath without G-code export
"""

import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from fastapi import APIRouter, HTTPException

# Import canonical geometry functions - NO inline math in routers (Fortran Rule)
from ...geometry.arc_utils import tessellate_arc_radians

from ..adaptive_schemas import (
    Loop,
    PlanIn,
    PlanOut,
)

from ...cam.adaptive_core_l1 import (
    polygon_area,
    to_toolpath,
)
from ...cam.adaptive_core_l2 import plan_adaptive_l2
from ...cam.feedtime import estimate_time
from ...cam.feedtime_l3 import (
    jerk_aware_time,
    jerk_aware_time_with_profile_and_tags,
)
from ...cam.stock_ops import rough_mrr_estimate
from ...cam.trochoid_l3 import insert_trochoids
from ...services.jobint_artifacts import build_jobint_payload
from ..machines_consolidated_router import get_profile

# Import run artifact persistence (OPERATION lane requirement)
from ...rmos.runs import (
    RunArtifact,
    persist_run,
    create_run_id,
    sha256_of_obj,
)

# Import feasibility functions (Phase 2: server-side enforcement)
from ...rmos.api.rmos_feasibility_router import compute_feasibility_internal
from ...rmos.policies import SafetyPolicy

router = APIRouter(tags=["cam-adaptive"])


@router.post("/plan", response_model=PlanOut)
def plan(body: PlanIn) -> PlanOut:
    """
    Generate adaptive pocket toolpath from boundary loops.

    Integrates L.1 (robust offsetting), L.2 (spiralizer + fillets + HUD),
    L.3 (trochoids + jerk-aware time), and M.4 (live learn feed overrides).

    Args:
        body: PlanIn request model with geometry and machining parameters

    Returns:
        PlanOut with moves array, statistics, and HUD overlays

    Raises:
        HTTPException 400: If loops empty or outer loop has < 3 points
        HTTPException 409: If safety policy blocks the operation
    """
    # Parameter validation
    if not body.loops:
        raise HTTPException(400, "Loops array cannot be empty")

    if len(body.loops[0].pts) < 3:
        raise HTTPException(400, "Outer loop must have at least 3 points")

    if body.tool_d <= 0:
        raise HTTPException(400, "Tool diameter must be positive")

    if not (0.1 <= body.stepover <= 0.95):
        raise HTTPException(400, "Stepover must be between 0.1 and 0.95 (10%-95% of tool diameter)")

    if body.strategy not in ["Spiral", "Lanes"]:
        raise HTTPException(400, f"Invalid strategy '{body.strategy}'. Must be 'Spiral' or 'Lanes'")

    plan_request_dict = body.model_dump(mode="json")
    request_hash = sha256_of_obj(plan_request_dict)

    # --- Server-side feasibility enforcement (ADR-003 / OPERATION lane) ---
    now = datetime.now(timezone.utc).isoformat()

    feasibility = compute_feasibility_internal(
        tool_id="adaptive:plan",
        req=plan_request_dict,
        context="adaptive_plan",
    )
    decision = SafetyPolicy.extract_safety_decision(feasibility)
    risk_level = decision.risk_level_str()
    feas_hash = sha256_of_obj(feasibility)

    if SafetyPolicy.should_block(decision.risk_level):
        run_id = create_run_id()
        artifact = RunArtifact(
            run_id=run_id,
            created_at_utc=now,
            tool_id="adaptive:plan",
            workflow_mode="adaptive",
            event_type="adaptive_plan_blocked",
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
                "message": "Adaptive pocket planning blocked due to unresolved feasibility concerns.",
                "run_id": run_id,
                "decision": decision.to_dict(),
                "authoritative_feasibility": feasibility,
            },
        )

    loops = [l.pts for l in body.loops]

    # Generate path using L.2: true spiral + adaptive stepover + fillets + HUD
    plan2 = plan_adaptive_l2(
        loops=loops,
        tool_d=body.tool_d,
        stepover=body.stepover,
        stepdown=body.stepdown,
        margin=body.margin,
        strategy=body.strategy,
        smoothing_radius=body.smoothing,
        corner_radius_min=body.corner_radius_min,
        target_stepover=body.target_stepover,
        feed_xy=body.feed_xy,
        slowdown_feed_pct=body.slowdown_feed_pct
    )

    path_pts_or_arcs = plan2["path"]

    overlays_normalized: List[Dict[str, Any]] = []
    for overlay in plan2.get("overlays", []):
        normalized = dict(overlay)
        coords = None
        if isinstance(normalized.get("pos"), (list, tuple)) and len(normalized["pos"]) >= 2:
            coords = normalized["pos"]
        elif isinstance(normalized.get("at"), (list, tuple)) and len(normalized["at"]) >= 2:
            coords = normalized["at"]

        if coords:
            normalized.setdefault("x", coords[0])
            normalized.setdefault("y", coords[1])

        overlays_normalized.append(normalized)

    # Convert mixed path (points + arcs) to linear moves for preview
    pts_only: List[Tuple[float, float]] = []
    for item in path_pts_or_arcs:
        if isinstance(item, dict) and item.get("type") == "arc":
            cx, cy, r = item["cx"], item["cy"], abs(item["r"])
            start_rad = math.radians(item["start"])
            end_rad = math.radians(item["end"])
            cw = item.get("cw", False)
            steps = max(6, int(r / 1.0))
            arc_pts = tessellate_arc_radians(cx, cy, r, start_rad, end_rad, cw, steps)
            pts_only.extend(arc_pts)
        else:
            pts_only.append(tuple(item))

    # Compute per-point slowdown factors (MERGED FEATURE)
    from ...cam.adaptive_spiralizer_utils import compute_slowdown_factors
    slowdown_factors = compute_slowdown_factors(
        pts_only,
        body.tool_d,
        k_threshold=1.0 / max(1.0, 3.0 * body.tool_d),
        slowdown_range=(body.slowdown_feed_pct / 100.0, 1.0)
    )

    # Convert to toolpath moves with slowdown metadata
    moves = to_toolpath(
        pts_only,
        body.feed_xy,
        body.z_rough,
        body.safe_z,
        lead_r=0.5
    )

    # Inject slowdown metadata into cutting moves (MERGED FEATURE)
    cutting_idx = 0
    for mv in moves:
        if mv.get("code") == "G1" and 'x' in mv and 'y' in mv:
            if cutting_idx < len(slowdown_factors):
                factor = slowdown_factors[cutting_idx]
                mv["meta"] = {"slowdown": round(factor, 3)}
                if "f" in mv:
                    mv["f"] = max(100.0, mv["f"] * factor)
                cutting_idx += 1

    # M.4 Live Learn: Apply session-only feed override
    if body.session_override_factor is not None:
        session_f = float(body.session_override_factor)
        if 0.5 <= session_f <= 1.5:
            for mv in moves:
                if mv.get("code") == "G1" and "f" in mv:
                    mv["f"] = max(100.0, mv["f"] * session_f)
                    if "meta" not in mv:
                        mv["meta"] = {}
                    mv["meta"]["session_override"] = round(session_f, 3)

    # L.3: Optional trochoids for overload segments
    base_moves = moves
    if body.use_trochoids:
        moves = insert_trochoids(
            base_moves,
            trochoid_radius=max(0.3, body.trochoid_radius),
            trochoid_pitch=max(0.6, body.trochoid_pitch),
            curvature_slowdown_threshold=1.0 / max(1.0, 3.0 * body.tool_d),
        )

    # Calculate statistics
    length = 0.0
    last = None
    tight_segments = 0
    trochoid_arcs = 0
    for mv in moves:
        if 'x' in mv and 'y' in mv:
            if last is not None:
                length += math.hypot(mv['x'] - last[0], mv['y'] - last[1])
            last = (mv['x'], mv['y'])
            if mv.get("meta", {}).get("slowdown", 1.0) < 0.85:
                tight_segments += 1
            if mv.get("meta", {}).get("trochoid"):
                trochoid_arcs += 1

    area = polygon_area(loops[0])

    # M.1: Load machine profile if specified
    profile = None
    if body.machine_profile_id:
        try:
            profile = get_profile(body.machine_profile_id)
        except (KeyError, FileNotFoundError, ValueError):
            profile = None

    # Classic time estimate
    t_classic = estimate_time(moves, body.feed_xy, plunge_f=300, rapid_f=body.machine_rapid)

    # L.3/M.1/M.1.1: Jerk-aware time estimate with bottleneck tagging
    t_jerk = None
    caps = {"feed_cap": 0, "accel": 0, "jerk": 0, "none": 0}

    if body.jerk_aware or profile:
        if profile:
            t_jerk, moves_tagged, caps = jerk_aware_time_with_profile_and_tags(moves, profile)
            moves = moves_tagged
        else:
            t_jerk = jerk_aware_time(
                moves,
                feed_xy=body.machine_feed_xy,
                rapid_f=body.machine_rapid,
                accel=body.machine_accel,
                jerk=body.machine_jerk,
                corner_tol_mm=body.corner_tol_mm,
            )

    volume_mm3 = rough_mrr_estimate(area, body.stepdown, length, body.tool_d)

    response: Dict[str, Any] = {
        "moves": moves,
        "stats": {
            "length_mm": round(length, 3),
            "area_mm2": round(area, 1),
            "time_s": round(t_jerk if t_jerk is not None else t_classic, 1),
            "time_s_classic": round(t_classic, 1),
            "time_s_jerk": round(t_jerk, 1) if t_jerk is not None else None,
            "volume_mm3": round(volume_mm3, 1),
            "move_count": len(moves),
            "tight_segments": tight_segments,
            "trochoid_arcs": trochoid_arcs,
            "caps": caps,
            "machine_profile_id": body.machine_profile_id or None,
            "session_override_factor": float(body.session_override_factor) if body.session_override_factor else None,
        },
        "overlays": overlays_normalized,
    }

    job_payload = build_jobint_payload(
        {
            "plan_request": plan_request_dict,
            "adaptive_plan_request": plan_request_dict,
            "moves": moves,
            "adaptive_moves": moves,
        }
    )
    if job_payload:
        response["job_int"] = job_payload

    # Create artifact for OPERATION lane compliance
    moves_hash = sha256_of_obj(moves)

    run_id = create_run_id()
    artifact = RunArtifact(
        run_id=run_id,
        created_at_utc=now,
        tool_id="adaptive:plan",
        workflow_mode="adaptive",
        event_type="adaptive_plan_execution",
        status="OK",
        feasibility=feasibility,
        request_hash=request_hash,
        toolpaths_hash=moves_hash,
    )
    persist_run(artifact)

    response["_run_id"] = run_id
    response["_hashes"] = {
        "request_sha256": request_hash,
        "moves_sha256": moves_hash,
    }

    return response


@router.post("/sim")
def simulate(body: PlanIn) -> Dict[str, Any]:
    """
    Simulate adaptive pocket toolpath without G-code export.

    Performs full toolpath planning and statistics calculation without
    generating post-processor-specific G-code. Used for:
    - Pre-flight validation (check tool collision, tight radii)
    - Time estimation (compare classic vs jerk-aware)
    - Parameter tuning (test stepover, feeds, L.2/L.3 options)

    Args:
        body: PlanIn request model with geometry and machining parameters

    Returns:
        Dictionary with success flag, stats, and first 10 moves for preview

    Notes:
        - Lightweight alternative to /gcode for validation
        - Returns truncated moves list (first 10) to reduce response size
    """
    plan_out = plan(body)

    return {
        "success": True,
        "stats": plan_out["stats"],
        "moves": plan_out["moves"][:10]
    }
