# services/api/app/routers/pipeline_router.py
"""CAM Pipeline Router - DXF upload through toolpath generation."""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Literal, Optional, Tuple

import httpx
from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from pydantic import ValidationError

from .pipeline_schemas import (
    DEFAULT_TOOL_DIAMETER_MM, PipelineOp, PipelineOpKind, PipelineOpResult, PipelineRequest, PipelineResponse,
)

from ..services.jobint_artifacts import build_jobint_payload
logger = logging.getLogger(__name__)

try:
    from ..util.dxf_preflight import (
        PreflightEngineMissingError,
        PreflightGeometryError,
        PreflightParseError,
        preflight_dxf_bytes,
    )
except ImportError:
    def preflight_dxf_bytes(*a, **k): raise NotImplementedError("DXF preflight not implemented")
    class PreflightEngineMissingError(Exception): pass
    class PreflightParseError(Exception): pass
    class PreflightGeometryError(Exception): pass

try:
    from ..routers.blueprint_cam import extract_loops_from_dxf
except ImportError:
    def extract_loops_from_dxf(*a, **k): raise NotImplementedError("DXF loop extraction not implemented")

router = APIRouter(prefix="/cam", tags=["cam", "pipeline"])

MAX_DXF_SIZE_BYTES = 50 * 1024 * 1024
HTTP_TIMEOUT_SECONDS = 60.0
MAX_PIPELINE_OPS = 20
SUPPORTED_DXF_EXTENSIONS = (".dxf",)

def _validate_ops(ops: List[PipelineOp]) -> None:
    """Validate pipeline ops."""
    if not ops:
        raise HTTPException(
            status_code=400, 
            detail="Pipeline must contain at least one operation."
        )

    ids = [op.id for op in ops if op.id]
    if len(ids) != len(set(ids)):
        raise HTTPException(
            status_code=400, 
            detail="Pipeline operation IDs must be unique. Found duplicate IDs."
        )

    kinds = [op.kind for op in ops]

    if "export_post" in kinds:
        idx_export = kinds.index("export_post")
        if idx_export > 0 and "adaptive_plan_run" not in kinds[:idx_export]:
            raise HTTPException(
                status_code=400,
                detail="export_post requires a prior adaptive_plan_run operation to generate G-code."
            )

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
    # --- Parse pipeline spec -------------------------------------------------
    try:
        req = PipelineRequest.model_validate_json(pipeline)
    except ValidationError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid pipeline spec: {exc}",
        ) from exc

    _validate_ops(req.ops)

    if not file.filename or not file.filename.lower().endswith(".dxf"):
        raise HTTPException(status_code=400, detail="Only .dxf files are supported.")

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file.")

    # --- DXF caching + context ----------------------------------------------
    ctx: Dict[str, Any] = {
        "dxf_bytes": data,
        "dxf_filename": file.filename,
        "loops": None,
        "plan": None,
        "plan_result": None,
        "gcode": None,
        "post_result": None,
        "sim_result": None,
        "machine_profile": None,
        "post_profile": None,
    }

    results: List[PipelineOpResult] = []
    summary: Dict[str, Any] = {}

    shared_tool_d = req.tool_d
    shared_units = req.units
    shared_geometry_layer = req.geometry_layer
    shared_auto_scale = req.auto_scale
    shared_cam_prefix = req.cam_layer_prefix
    shared_machine_id = req.machine_id
    shared_post_id = req.post_id

    
    async def _ensure_machine_profile(
        client: httpx.AsyncClient, 
        machine_id: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """Load machine profile."""
        if not machine_id:
            return None
        
        mp = ctx.get("machine_profile")
        if mp and mp.get("id") == machine_id:
            return mp
        
        try:
            # Fetch machine profile from endpoint
            resp = await client.get(f"{machine_path}/{machine_id}", timeout=HTTP_TIMEOUT_SECONDS)
            if resp.status_code != 200:
                logger.warning(
                    f"Machine profile '{machine_id}' not found (status {resp.status_code})"
                )
                raise HTTPException(
                    status_code=resp.status_code,
                    detail=f"Failed to load machine profile '{machine_id}': {resp.text}",
                )
            
            mp = resp.json()
            ctx["machine_profile"] = mp
            return mp
            
        except httpx.RequestError as e:
            # Machine endpoint might not exist yet - continue without it
            logger.warning(f"Machine endpoint unavailable: {e}")
            return None

    async def _ensure_post_profile(
        client: httpx.AsyncClient, 
        post_id: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """Load post preset."""
        if not post_id:
            return None
        
        pp = ctx.get("post_profile")
        if pp and pp.get("id") == post_id:
            return pp
        
        try:
            # Fetch post preset from endpoint
            resp = await client.get(f"{post_path}/{post_id}", timeout=HTTP_TIMEOUT_SECONDS)
            if resp.status_code != 200:
                logger.warning(
                    f"Post preset '{post_id}' not found (status {resp.status_code})"
                )
                raise HTTPException(
                    status_code=resp.status_code,
                    detail=f"Failed to load post preset '{post_id}': {resp.text}",
                )
            
            pp = resp.json()
            ctx["post_profile"] = pp
            return pp
            
        except httpx.RequestError as e:
            # Post endpoint might not exist yet - continue with base post
            logger.warning(f"Post endpoint unavailable: {e}")
            return None

    
    def _merge_params(op: PipelineOp) -> Dict[str, Any]:
        """Merge params."""
        merged: Dict[str, Any] = {
            "tool_d": shared_tool_d,
            "units": shared_units,
            "geometry_layer": shared_geometry_layer,
            "auto_scale": shared_auto_scale,
            "cam_layer_prefix": shared_cam_prefix,
            "machine_id": shared_machine_id,
            "post_id": shared_post_id,
        }
        merged.update(op.params)
        return merged

    
    def _wrap_preflight(params: Dict[str, Any]) -> Dict[str, Any]:
        """Run preflight."""
        profile = params.get("profile")
        cam_prefix = params.get("cam_layer_prefix", shared_cam_prefix)
        debug_flag = bool(params.get("debug", False))
        
        rep = preflight_dxf_bytes(
            ctx["dxf_bytes"],
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

    def _wrap_adaptive_plan(params: Dict[str, Any]) -> Dict[str, Any]:
        """Extract loops."""
        import os
        import tempfile
        
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.dxf', delete=False) as tmp:
            tmp.write(ctx["dxf_bytes"])
            tmp_path = tmp.name
        
        try:
            # Extract loops from DXF bytes
            layer_name = params.get("geometry_layer") or shared_geometry_layer or "GEOMETRY"
            loops, warnings = extract_loops_from_dxf(ctx["dxf_bytes"], layer_name=layer_name)
            ctx["loops"] = loops
            return {
                "loops": [{"pts": loop.pts} for loop in loops],
                "count": len(loops),
                "warnings": warnings
            }
        finally:
            os.unlink(tmp_path)

    async def _wrap_adaptive_plan_run(params: Dict[str, Any], client: httpx.AsyncClient) -> Dict[str, Any]:
        """Run planning."""
        if ctx["loops"] is None:
            raise HTTPException(
                status_code=400,
                detail="adaptive_plan_run requires prior adaptive_plan operation to extract loops"
            )
        
        machine_id = params.get("machine_id", shared_machine_id)
        mp = await _ensure_machine_profile(client, machine_id)
        
        plan_req = {
            "loops": [{"pts": loop.pts} for loop in ctx["loops"]],
            "units": params.get("units", shared_units),
            "tool_d": float(params.get("tool_d", shared_tool_d)),
            "stepover": float(params.get("stepover", 0.45)),
            "stepdown": float(params.get("stepdown", 2.0)),
            "margin": float(params.get("margin", 0.5)),
            "strategy": params.get("strategy", "Spiral"),
            "smoothing": float(params.get("smoothing", 0.5)),
            "climb": bool(params.get("climb", True)),
            "feed_xy": float(params.get("feed_xy", mp.get("max_feed_xy") if mp else 1200)),
            "safe_z": float(params.get("safe_z", mp.get("safe_z_default") if mp and "safe_z_default" in mp else 5.0)),
            "z_rough": float(params.get("z_rough", -1.5)),
        }
        
        if mp:
            for k, v in [("machine_profile_id", "id"), ("machine_feed_xy", "max_feed_xy"), ("machine_rapid", "rapid"), ("machine_accel", "accel"), ("machine_jerk", "jerk")]:
                plan_req.setdefault(k, mp.get(v))
        
        for k in ("corner_radius_min", "target_stepover", "slowdown_feed_pct"):
            if k in params: plan_req[k] = float(params[k])
        
        if "use_trochoids" in params: plan_req["use_trochoids"] = bool(params["use_trochoids"])
        for k in ("trochoid_radius", "trochoid_pitch"):
            if k in params: plan_req[k] = float(params[k])
        
        ctx["plan"] = plan_req
        
        resp = await client.post(adaptive_plan_path, json=plan_req)
        
        if resp.status_code != 200:
            raise HTTPException(
                status_code=resp.status_code,
                detail=f"Adaptive planner error: {resp.text}",
            )
        
        result = resp.json()
        ctx["plan_result"] = result
        
        if "gcode" not in result and "moves" in result:
            gcode_lines = []
            for move in result["moves"]:
                parts = [move.get("code", "G0")]
                if "x" in move:
                    parts.append(f"X{move['x']:.4f}")
                if "y" in move:
                    parts.append(f"Y{move['y']:.4f}")
                if "z" in move:
                    parts.append(f"Z{move['z']:.4f}")
                if "f" in move:
                    parts.append(f"F{move['f']:.1f}")
                gcode_lines.append(" ".join(parts))
            ctx["gcode"] = "\n".join(gcode_lines)
        
        return result

    async def _wrap_export_post(params: Dict[str, Any], client: httpx.AsyncClient) -> Dict[str, Any]:
        """Apply post."""
        if ctx["gcode"] is None:
            raise HTTPException(
                status_code=400,
                detail="export_post requires gcode from prior adaptive_plan_run"
            )
        
        post_id = params.get("post_id", shared_post_id) or "GRBL"
        pp = await _ensure_post_profile(client, post_id)
        
        units = params.get("units", shared_units)
        
        import os
        post_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "data", "posts", f"{post_id.lower()}.json"
        )
        
        if not os.path.exists(post_file):
            raise HTTPException(
                status_code=404,
                detail=f"Post-processor '{post_id}' not found"
            )
        
        with open(post_file, 'r') as f:
            post_config = json.load(f)
        
        if pp:
            if "post" in pp: post_config["dialect"] = pp["post"]
            if "header" in pp: post_config["header"] = pp["header"]
            if "footer" in pp: post_config["footer"] = pp["footer"]
        
        gcode_lines = []
        
        gcode_lines.append("G21" if units == "mm" else "G20")
        
        if "header" in post_config:
            gcode_lines.extend(post_config["header"])
        
        from datetime import datetime
        gcode_lines.append(
            f"(POST={post_id};UNITS={units};DATE={datetime.utcnow().isoformat()})"
        )
        
        gcode_lines.append(ctx["gcode"])
        
        if "footer" in post_config:
            gcode_lines.extend(post_config["footer"])
        
        final_gcode = "\n".join(gcode_lines)
        ctx["gcode"] = final_gcode
        ctx["post_result"] = {
            "post_id": post_id,
            "units": units,
            "lines": len(gcode_lines),
        }
        
        return {
            "post_id": post_id,
            "gcode_preview": "\n".join(gcode_lines[:20]),  # First 20 lines
            "total_lines": len(gcode_lines),
        }

    async def _wrap_simulate_gcode(params: Dict[str, Any], client: httpx.AsyncClient) -> Dict[str, Any]:
        """Simulate."""
        gcode = params.get("gcode") or ctx.get("gcode")
        
        if not gcode:
            raise HTTPException(
                status_code=400,
                detail=(
                    "simulate_gcode requires 'gcode' in params or a prior op "
                    "that provides gcode (e.g. adaptive_plan_run or export_post)."
                ),
            )
        
        machine_id = params.get("machine_id", shared_machine_id)
        mp = await _ensure_machine_profile(client, machine_id)
        
        body = {
            "gcode": gcode,
            "accel": float(params.get("accel", mp.get("accel") if mp else 800)),
            "clearance_z": float(params.get("safe_z", mp.get("safe_z_default") if mp and "safe_z_default" in mp else 5.0)),
            "as_csv": False,
        }
        
        if mp:
            if "feed_xy" not in params and "max_feed_xy" in mp:
                body["feed_xy"] = mp["max_feed_xy"]
            if "feed_z" not in params and "max_feed_z" in mp:
                body["feed_z"] = mp["max_feed_z"]
            if "rapid" not in params and "rapid" in mp:
                body["rapid"] = mp["rapid"]
        
        resp = await client.post(sim_path, json=body)
        
        if resp.status_code != 200:
            raise HTTPException(
                status_code=resp.status_code,
                detail=f"Simulation error: {resp.text}",
            )
        
        result = resp.json()
        ctx["sim_result"] = result
        return result

    # --- Main loop with per-op error wrapping -------------------------------
    async with httpx.AsyncClient(base_url=base_url, timeout=60.0) as client:
        for op in req.ops:
            merged = _merge_params(op)
            kind = op.kind

            try:
                if kind == "dxf_preflight":
                    payload = _wrap_preflight(merged)
                    ok = bool(payload.get("ok", True))
                elif kind == "adaptive_plan":
                    payload = _wrap_adaptive_plan(merged)
                    ok = True
                elif kind == "adaptive_plan_run":
                    payload = await _wrap_adaptive_plan_run(merged, client)
                    ok = True
                elif kind == "export_post":
                    payload = await _wrap_export_post(merged, client)
                    ok = True
                elif kind == "simulate_gcode":
                    payload = await _wrap_simulate_gcode(merged, client)
                    ok = True
                else:
                    results.append(PipelineOpResult(id=op.id, kind=kind, ok=False, error=f"Unsupported pipeline op kind: {kind}", payload=None))
                    break

                results.append(
                    PipelineOpResult(id=op.id, kind=kind, ok=ok, payload=payload)
                )

            except (PreflightEngineMissingError,) as exc:
                results.append(PipelineOpResult(id=op.id, kind=kind, ok=False, error=f"Engine missing: {exc}", payload=None))
                break
            except (PreflightParseError,) as exc:
                results.append(PipelineOpResult(id=op.id, kind=kind, ok=False, error=f"DXF parse error: {exc}", payload=None))
                break
            except (PreflightGeometryError,) as exc:
                results.append(PipelineOpResult(id=op.id, kind=kind, ok=False, error=f"DXF geometry error: {exc}", payload=None))
                break
            except HTTPException as exc:  # WP-1: catch HTTPException separately
                results.append(PipelineOpResult(id=op.id, kind=kind, ok=False, error=str(exc.detail), payload=None))
                break
            except Exception as exc:  # WP-1: governance catch-all — HTTP endpoint
                results.append(PipelineOpResult(id=op.id, kind=kind, ok=False, error=f"Unexpected error: {exc}", payload=None))
                break

    if ctx.get("sim_result") and isinstance(ctx["sim_result"], dict):
        summary = ctx["sim_result"].get("summary", {})
    elif ctx.get("plan_result"):
        summary = ctx["plan_result"].get("stats", {})

    job_payload = build_jobint_payload(
        {
            "plan_request": ctx.get("plan"),
            "adaptive_plan_request": ctx.get("plan"),
            "moves": (ctx.get("plan_result") or {}).get("moves"),
            "adaptive_moves": (ctx.get("plan_result") or {}).get("moves"),
            "moves_path": ctx.get("moves_path"),
        }
    )

    return PipelineResponse(ops=results, summary=summary, job_int=job_payload)
