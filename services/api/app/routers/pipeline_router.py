# services/api/app/routers/pipeline_router.py
"""CAM Pipeline Router - DXF upload through toolpath generation.

Decomposed into focused modules:
- pipeline_context.py: PipelineContext dataclass for state management
- pipeline_operations.py: Operation handlers and execution logic
- pipeline_helpers.py: Request/response building functions
- pipeline_validators.py: Input validation
"""
from __future__ import annotations

from typing import Any, Dict

import httpx
from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from pydantic import ValidationError

from .pipeline_context import PipelineContext
from .pipeline_operations import execute_pipeline
from .pipeline_schemas import PipelineRequest, PipelineResponse
from .pipeline_validators import validate_ops
from ..services.jobint_artifacts import build_jobint_payload


# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------
router = APIRouter(prefix="/cam", tags=["cam", "pipeline"])

MAX_DXF_SIZE_BYTES = 50 * 1024 * 1024
SUPPORTED_DXF_EXTENSIONS = (".dxf",)


# -----------------------------------------------------------------------------
# Response builder
# -----------------------------------------------------------------------------
def build_response(ctx: PipelineContext, results: list) -> PipelineResponse:
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
    """Execute CAM pipeline: DXF -> preflight -> plan -> post -> simulate."""
    # Parse and validate request
    try:
        req = PipelineRequest.model_validate_json(pipeline)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid pipeline spec: {exc}") from exc

    validate_ops(req.ops)

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
