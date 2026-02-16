# services/api/app/routers/pipeline_router.py
"""CAM Pipeline Router - DXF upload through toolpath generation.

Refactored for reduced complexity:
- PipelineContext dataclass for state management
- Module-level operation handlers
- Operation dispatch table pattern
"""
from __future__ import annotations

import json
import logging
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Awaitable, Callable, Dict, List, Optional

import httpx
from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from pydantic import ValidationError

from .pipeline_schemas import (
    DEFAULT_TOOL_DIAMETER_MM,
    PipelineOp,
    PipelineOpResult,
    PipelineRequest,
    PipelineResponse,
)
from ..services.jobint_artifacts import build_jobint_payload

logger = logging.getLogger(__name__)

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
# Constants
# -----------------------------------------------------------------------------
router = APIRouter(prefix="/cam", tags=["cam", "pipeline"])

MAX_DXF_SIZE_BYTES = 50 * 1024 * 1024
HTTP_TIMEOUT_SECONDS = 60.0
MAX_PIPELINE_OPS = 20
SUPPORTED_DXF_EXTENSIONS = (".dxf",)


# -----------------------------------------------------------------------------
# Context dataclass
# -----------------------------------------------------------------------------
@dataclass
class PipelineContext:
    """Pipeline execution state passed between operations."""

    dxf_bytes: bytes
    dxf_filename: str
    client: httpx.AsyncClient

    # Shared parameters from request
    tool_d: float = DEFAULT_TOOL_DIAMETER_MM
    units: str = "mm"
    geometry_layer: Optional[str] = None
    auto_scale: bool = False
    cam_layer_prefix: str = "CAM_"
    machine_id: Optional[str] = None
    post_id: Optional[str] = None

    # Endpoint paths
    adaptive_plan_path: str = "/api/cam/pocket/adaptive/plan"
    sim_path: str = "/cam/simulate_gcode"
    machine_path: str = "/cam/machines"
    post_path: str = "/cam/posts"

    # Cached state
    loops: Optional[List] = None
    plan: Optional[Dict[str, Any]] = None
    plan_result: Optional[Dict[str, Any]] = None
    gcode: Optional[str] = None
    post_result: Optional[Dict[str, Any]] = None
    sim_result: Optional[Dict[str, Any]] = None
    machine_profile: Optional[Dict[str, Any]] = None
    post_profile: Optional[Dict[str, Any]] = None

    def merge_params(self, op: PipelineOp) -> Dict[str, Any]:
        """Merge operation params with shared defaults."""
        merged: Dict[str, Any] = {
            "tool_d": self.tool_d,
            "units": self.units,
            "geometry_layer": self.geometry_layer,
            "auto_scale": self.auto_scale,
            "cam_layer_prefix": self.cam_layer_prefix,
            "machine_id": self.machine_id,
            "post_id": self.post_id,
        }
        merged.update(op.params)
        return merged


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
    except httpx.RequestError as e:
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
    except httpx.RequestError as e:
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

    plan_req = _build_plan_request(ctx, params, mp)
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
        ctx.gcode = _moves_to_gcode(result["moves"])

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

    post_config = _load_post_config(post_id)
    _apply_post_profile(post_config, pp)

    final_gcode, line_count = _build_posted_gcode(ctx.gcode, post_config, post_id, units)
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

    body = _build_sim_request(params, mp, gcode)

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
# Helper functions
# -----------------------------------------------------------------------------
def _build_plan_request(
    ctx: PipelineContext, params: Dict[str, Any], mp: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """Build adaptive plan request payload."""
    plan_req = {
        "loops": [{"pts": loop.pts} for loop in ctx.loops],
        "units": params.get("units", ctx.units),
        "tool_d": float(params.get("tool_d", ctx.tool_d)),
        "stepover": float(params.get("stepover", 0.45)),
        "stepdown": float(params.get("stepdown", 2.0)),
        "margin": float(params.get("margin", 0.5)),
        "strategy": params.get("strategy", "Spiral"),
        "smoothing": float(params.get("smoothing", 0.5)),
        "climb": bool(params.get("climb", True)),
        "feed_xy": float(params.get("feed_xy", mp.get("max_feed_xy") if mp else 1200)),
        "safe_z": float(
            params.get("safe_z", mp.get("safe_z_default") if mp and "safe_z_default" in mp else 5.0)
        ),
        "z_rough": float(params.get("z_rough", -1.5)),
    }

    # Apply machine profile defaults
    if mp:
        for key, mp_key in [
            ("machine_profile_id", "id"),
            ("machine_feed_xy", "max_feed_xy"),
            ("machine_rapid", "rapid"),
            ("machine_accel", "accel"),
            ("machine_jerk", "jerk"),
        ]:
            plan_req.setdefault(key, mp.get(mp_key))

    # Optional numeric params
    for key in ("corner_radius_min", "target_stepover", "slowdown_feed_pct"):
        if key in params:
            plan_req[key] = float(params[key])

    # Trochoid params
    if "use_trochoids" in params:
        plan_req["use_trochoids"] = bool(params["use_trochoids"])
    for key in ("trochoid_radius", "trochoid_pitch"):
        if key in params:
            plan_req[key] = float(params[key])

    return plan_req


def _moves_to_gcode(moves: List[Dict[str, Any]]) -> str:
    """Convert move list to G-code string."""
    lines = []
    for move in moves:
        parts = [move.get("code", "G0")]
        if "x" in move:
            parts.append(f"X{move['x']:.4f}")
        if "y" in move:
            parts.append(f"Y{move['y']:.4f}")
        if "z" in move:
            parts.append(f"Z{move['z']:.4f}")
        if "f" in move:
            parts.append(f"F{move['f']:.1f}")
        lines.append(" ".join(parts))
    return "\n".join(lines)


def _load_post_config(post_id: str) -> Dict[str, Any]:
    """Load post-processor configuration file."""
    post_file = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "data",
        "posts",
        f"{post_id.lower()}.json",
    )
    if not os.path.exists(post_file):
        raise HTTPException(status_code=404, detail=f"Post-processor '{post_id}' not found")

    with open(post_file, "r") as f:
        return json.load(f)


def _apply_post_profile(post_config: Dict[str, Any], pp: Optional[Dict[str, Any]]) -> None:
    """Apply post profile overrides to config."""
    if not pp:
        return
    if "post" in pp:
        post_config["dialect"] = pp["post"]
    if "header" in pp:
        post_config["header"] = pp["header"]
    if "footer" in pp:
        post_config["footer"] = pp["footer"]


def _build_posted_gcode(
    raw_gcode: str, post_config: Dict[str, Any], post_id: str, units: str
) -> tuple:
    """Build final posted G-code with header/footer."""
    lines = []
    lines.append("G21" if units == "mm" else "G20")

    if "header" in post_config:
        lines.extend(post_config["header"])

    lines.append(f"(POST={post_id};UNITS={units};DATE={datetime.utcnow().isoformat()})")
    lines.append(raw_gcode)

    if "footer" in post_config:
        lines.extend(post_config["footer"])

    return "\n".join(lines), len(lines)


def _build_sim_request(
    params: Dict[str, Any], mp: Optional[Dict[str, Any]], gcode: str
) -> Dict[str, Any]:
    """Build simulation request payload."""
    body = {
        "gcode": gcode,
        "accel": float(params.get("accel", mp.get("accel") if mp else 800)),
        "clearance_z": float(
            params.get("safe_z", mp.get("safe_z_default") if mp and "safe_z_default" in mp else 5.0)
        ),
        "as_csv": False,
    }

    if mp:
        if "feed_xy" not in params and "max_feed_xy" in mp:
            body["feed_xy"] = mp["max_feed_xy"]
        if "feed_z" not in params and "max_feed_z" in mp:
            body["feed_z"] = mp["max_feed_z"]
        if "rapid" not in params and "rapid" in mp:
            body["rapid"] = mp["rapid"]

    return body


# -----------------------------------------------------------------------------
# Validation
# -----------------------------------------------------------------------------
def _validate_ops(ops: List[PipelineOp]) -> None:
    """Validate pipeline operations."""
    if not ops:
        raise HTTPException(status_code=400, detail="Pipeline must contain at least one operation.")

    ids = [op.id for op in ops if op.id]
    if len(ids) != len(set(ids)):
        raise HTTPException(status_code=400, detail="Pipeline operation IDs must be unique.")

    kinds = [op.kind for op in ops]
    if "export_post" in kinds:
        idx_export = kinds.index("export_post")
        if idx_export > 0 and "adaptive_plan_run" not in kinds[:idx_export]:
            raise HTTPException(
                status_code=400,
                detail="export_post requires a prior adaptive_plan_run operation.",
            )


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


def build_response(ctx: PipelineContext, results: List[PipelineOpResult]) -> PipelineResponse:
    """Build final pipeline response."""
    summary: Dict[str, Any] = {}
    if ctx.sim_result and isinstance(ctx.sim_result, dict):
        summary = ctx.sim_result.get("summary", {})
    elif ctx.plan_result:
        summary = ctx.plan_result.get("stats", {})

    job_payload = build_jobint_payload(
        {
            "plan_request": ctx.plan,
            "adaptive_plan_request": ctx.plan,
            "moves": (ctx.plan_result or {}).get("moves"),
            "adaptive_moves": (ctx.plan_result or {}).get("moves"),
            "moves_path": None,
        }
    )

    return PipelineResponse(ops=results, summary=summary, job_int=job_payload)


# -----------------------------------------------------------------------------
# Main endpoint
# -----------------------------------------------------------------------------
@router.post("/pipeline/run", response_model=PipelineResponse)
async def run_pipeline(
    file: UploadFile = File(...),
    pipeline: str = Form(..., description="PipelineRequest JSON string."),
    base_url: str = Query("http://127.0.0.1:8000"),
    adaptive_plan_path: str = Query("/api/cam/pocket/adaptive/plan"),
    sim_path: str = Query("/cam/simulate_gcode"),
    machine_path: str = Query("/cam/machines"),
    post_path: str = Query("/cam/posts"),
):
    """Execute CAM pipeline: DXF → preflight → plan → post → simulate."""
    # Parse and validate request
    try:
        req = PipelineRequest.model_validate_json(pipeline)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid pipeline spec: {exc}") from exc

    _validate_ops(req.ops)

    # Validate file
    if not file.filename or not file.filename.lower().endswith(".dxf"):
        raise HTTPException(status_code=400, detail="Only .dxf files are supported.")

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file.")

    # Execute pipeline
    async with httpx.AsyncClient(base_url=base_url, timeout=60.0) as client:
        ctx = PipelineContext(
            dxf_bytes=data,
            dxf_filename=file.filename,
            client=client,
            tool_d=req.tool_d,
            units=req.units,
            geometry_layer=req.geometry_layer,
            auto_scale=req.auto_scale,
            cam_layer_prefix=req.cam_layer_prefix,
            machine_id=req.machine_id,
            post_id=req.post_id,
            adaptive_plan_path=adaptive_plan_path,
            sim_path=sim_path,
            machine_path=machine_path,
            post_path=post_path,
        )
        results = await execute_pipeline(ctx, req.ops)

    return build_response(ctx, results)
