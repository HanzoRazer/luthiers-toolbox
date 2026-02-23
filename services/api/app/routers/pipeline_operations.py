# services/api/app/routers/pipeline_operations.py
"""Pipeline operation handlers and execution logic."""
from __future__ import annotations

import logging
import os
import tempfile
from typing import Any, Awaitable, Callable, Dict, List, Optional

from fastapi import HTTPException

from .pipeline_context import PipelineContext
from .pipeline_helpers import (
    apply_post_profile,
    build_plan_request,
    build_posted_gcode,
    build_sim_request,
    load_post_config,
    moves_to_gcode,
)
from .pipeline_schemas import PipelineOp, PipelineOpResult

logger = logging.getLogger(__name__)

# HTTP timeout for external requests
HTTP_TIMEOUT_SECONDS = 60.0


# -----------------------------------------------------------------------------
# Optional imports with fallbacks
# -----------------------------------------------------------------------------
try:
    from ..util.dxf_preflight import (
        PreflightEngineMissingError,
        PreflightGeometryError,
        PreflightParseError,
        preflight_dxf_bytes,
    )
except ImportError:
    def preflight_dxf_bytes(*a, **k):
        raise NotImplementedError("DXF preflight not implemented")

    class PreflightEngineMissingError(Exception):
        pass

    class PreflightParseError(Exception):
        pass

    class PreflightGeometryError(Exception):
        pass

try:
    from ..routers.blueprint_cam import extract_loops_from_dxf
except ImportError:
    def extract_loops_from_dxf(*a, **k):
        raise NotImplementedError("DXF loop extraction not implemented")


# -----------------------------------------------------------------------------
# Profile loaders
# -----------------------------------------------------------------------------
async def load_machine_profile(
    ctx: PipelineContext, machine_id: Optional[str]
) -> Optional[Dict[str, Any]]:
    """Load and cache machine profile."""
    if not machine_id:
        return None

    # Return cached if same ID
    if ctx.machine_profile and ctx.machine_profile.get("id") == machine_id:
        return ctx.machine_profile

    try:
        resp = await ctx.client.get(
            f"{ctx.machine_path}/{machine_id}", timeout=HTTP_TIMEOUT_SECONDS
        )
        if resp.status_code != 200:
            logger.warning(f"Machine profile '{machine_id}' not found: {resp.status_code}")
            raise HTTPException(
                status_code=resp.status_code,
                detail=f"Failed to load machine profile '{machine_id}': {resp.text}",
            )
        ctx.machine_profile = resp.json()
        return ctx.machine_profile
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        logger.warning(f"Machine endpoint unavailable: {e}")
        return None


async def load_post_profile(
    ctx: PipelineContext, post_id: Optional[str]
) -> Optional[Dict[str, Any]]:
    """Load and cache post preset."""
    if not post_id:
        return None

    if ctx.post_profile and ctx.post_profile.get("id") == post_id:
        return ctx.post_profile

    try:
        resp = await ctx.client.get(
            f"{ctx.post_path}/{post_id}", timeout=HTTP_TIMEOUT_SECONDS
        )
        if resp.status_code != 200:
            logger.warning(f"Post preset '{post_id}' not found: {resp.status_code}")
            raise HTTPException(
                status_code=resp.status_code,
                detail=f"Failed to load post preset '{post_id}': {resp.text}",
            )
        ctx.post_profile = resp.json()
        return ctx.post_profile
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        logger.warning(f"Post endpoint unavailable: {e}")
        return None


# -----------------------------------------------------------------------------
# Operation handlers
# -----------------------------------------------------------------------------
async def op_dxf_preflight(ctx: PipelineContext, params: Dict[str, Any]) -> Dict[str, Any]:
    """Run DXF preflight validation."""
    profile = params.get("profile")
    cam_prefix = params.get("cam_layer_prefix", ctx.cam_layer_prefix)
    debug_flag = bool(params.get("debug", False))

    rep = preflight_dxf_bytes(
        ctx.dxf_bytes,
        cam_layer_prefix=cam_prefix,
        profile=profile,
        debug=debug_flag,
    )
    return {
        "ok": rep.ok,
        "report": {
            "ok": rep.ok,
            "units": rep.units,
            "layers": rep.layers,
            "candidate_layers": rep.candidate_layers,
            "issues": [
                {
                    "level": i.level,
                    "code": i.code,
                    "message": i.message,
                    "entity_id": i.entity_id,
                    "layer": i.layer,
                }
                for i in rep.issues
            ],
            "debug": rep.debug,
        },
    }


async def op_adaptive_plan(ctx: PipelineContext, params: Dict[str, Any]) -> Dict[str, Any]:
    """Extract loops from DXF for adaptive planning."""
    with tempfile.NamedTemporaryFile(mode="wb", suffix=".dxf", delete=False) as tmp:
        tmp.write(ctx.dxf_bytes)
        tmp_path = tmp.name

    try:
        layer_name = params.get("geometry_layer") or ctx.geometry_layer or "GEOMETRY"
        loops, warnings = extract_loops_from_dxf(ctx.dxf_bytes, layer_name=layer_name)
        ctx.loops = loops
        return {
            "loops": [{"pts": loop.pts} for loop in loops],
            "count": len(loops),
            "warnings": warnings,
        }
    finally:
        os.unlink(tmp_path)


async def op_adaptive_plan_run(ctx: PipelineContext, params: Dict[str, Any]) -> Dict[str, Any]:
    """Execute adaptive planning algorithm."""
    if ctx.loops is None:
        raise HTTPException(
            status_code=400,
            detail="adaptive_plan_run requires prior adaptive_plan operation",
        )

    machine_id = params.get("machine_id", ctx.machine_id)
    mp = await load_machine_profile(ctx, machine_id)

    plan_req = build_plan_request(ctx, params, mp)
    ctx.plan = plan_req

    resp = await ctx.client.post(ctx.adaptive_plan_path, json=plan_req)
    if resp.status_code != 200:
        raise HTTPException(
            status_code=resp.status_code,
            detail=f"Adaptive planner error: {resp.text}",
        )

    result = resp.json()
    ctx.plan_result = result

    # Generate G-code from moves if not provided
    if "gcode" not in result and "moves" in result:
        ctx.gcode = moves_to_gcode(result["moves"])

    return result


async def op_export_post(ctx: PipelineContext, params: Dict[str, Any]) -> Dict[str, Any]:
    """Apply post-processor to G-code."""
    if ctx.gcode is None:
        raise HTTPException(
            status_code=400,
            detail="export_post requires gcode from prior adaptive_plan_run",
        )

    post_id = params.get("post_id", ctx.post_id) or "GRBL"
    pp = await load_post_profile(ctx, post_id)
    units = params.get("units", ctx.units)

    post_config = load_post_config(post_id)
    apply_post_profile(post_config, pp)

    final_gcode, line_count = build_posted_gcode(ctx.gcode, post_config, post_id, units)
    ctx.gcode = final_gcode
    ctx.post_result = {"post_id": post_id, "units": units, "lines": line_count}

    return {
        "post_id": post_id,
        "gcode_preview": "\n".join(final_gcode.split("\n")[:20]),
        "total_lines": line_count,
    }


async def op_simulate_gcode(ctx: PipelineContext, params: Dict[str, Any]) -> Dict[str, Any]:
    """Simulate G-code execution."""
    gcode = params.get("gcode") or ctx.gcode
    if not gcode:
        raise HTTPException(
            status_code=400,
            detail="simulate_gcode requires 'gcode' param or prior op providing gcode",
        )

    machine_id = params.get("machine_id", ctx.machine_id)
    mp = await load_machine_profile(ctx, machine_id)

    body = build_sim_request(params, mp, gcode)

    resp = await ctx.client.post(ctx.sim_path, json=body)
    if resp.status_code != 200:
        raise HTTPException(
            status_code=resp.status_code,
            detail=f"Simulation error: {resp.text}",
        )

    result = resp.json()
    ctx.sim_result = result
    return result


# -----------------------------------------------------------------------------
# Operation dispatch table
# -----------------------------------------------------------------------------
OperationHandler = Callable[[PipelineContext, Dict[str, Any]], Awaitable[Dict[str, Any]]]

OPERATION_HANDLERS: Dict[str, OperationHandler] = {
    "dxf_preflight": op_dxf_preflight,
    "adaptive_plan": op_adaptive_plan,
    "adaptive_plan_run": op_adaptive_plan_run,
    "export_post": op_export_post,
    "simulate_gcode": op_simulate_gcode,
}


# -----------------------------------------------------------------------------
# Exception handling
# -----------------------------------------------------------------------------
def handle_pipeline_exception(
    exc: Exception, op_id: Optional[str], kind: str
) -> PipelineOpResult:
    """Convert exception to PipelineOpResult."""
    if isinstance(exc, PreflightEngineMissingError):
        error_msg = f"Engine missing: {exc}"
    elif isinstance(exc, PreflightParseError):
        error_msg = f"DXF parse error: {exc}"
    elif isinstance(exc, PreflightGeometryError):
        error_msg = f"DXF geometry error: {exc}"
    elif isinstance(exc, HTTPException):
        error_msg = str(exc.detail)
    else:
        error_msg = f"Unexpected error: {exc}"

    return PipelineOpResult(id=op_id, kind=kind, ok=False, error=error_msg, payload=None)


# -----------------------------------------------------------------------------
# Pipeline execution
# -----------------------------------------------------------------------------
async def execute_pipeline(
    ctx: PipelineContext, ops: List[PipelineOp]
) -> List[PipelineOpResult]:
    """Execute pipeline operations in sequence."""
    results: List[PipelineOpResult] = []

    for op in ops:
        params = ctx.merge_params(op)
        handler = OPERATION_HANDLERS.get(op.kind)

        if handler is None:
            results.append(
                PipelineOpResult(
                    id=op.id,
                    kind=op.kind,
                    ok=False,
                    error=f"Unsupported pipeline op kind: {op.kind}",
                    payload=None,
                )
            )
            break

        try:
            payload = await handler(ctx, params)
            ok = payload.get("ok", True) if isinstance(payload, dict) else True
            results.append(PipelineOpResult(id=op.id, kind=op.kind, ok=ok, payload=payload))
        except (
            PreflightEngineMissingError,
            PreflightParseError,
            PreflightGeometryError,
            HTTPException,
            Exception,
        ) as exc:
            results.append(handle_pipeline_exception(exc, op.id, op.kind))
            break

    return results
