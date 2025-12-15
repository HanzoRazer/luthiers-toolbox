"""
Luthier's Tool Box - CNC Guitar Lutherie CAD/CAM Toolbox
CAM Pipeline Preset Run Router - Execute saved pipeline presets

Part of Phase 25.0: Pipeline Preset Integration
Repository: HanzoRazer/luthiers-toolbox
Created: January 2025

Features:
- Run saved pipeline presets by ID
- Forward preset spec to /cam/pipeline/run
- Unified pipeline execution via internal HTTP call
- Error handling with proper HTTP status codes
- Returns complete pipeline run result
"""

from __future__ import annotations

from typing import Any, Dict

import httpx
from fastapi import APIRouter, HTTPException, Request

from ..services.pipeline_preset_store import PipelinePresetStore

router = APIRouter(prefix="/cam/pipeline", tags=["cam", "pipeline", "presets"])

_preset_store = PipelinePresetStore()


@router.post("/presets/{preset_id}/run")
async def run_preset(
    preset_id: str,
    request: Request,
) -> Dict[str, Any]:
    """
    Load a pipeline preset by ID and forward its spec to /cam/pipeline/run.

    Expects the main pipeline router to expose:
        POST /cam/pipeline/run  with body: { spec: {...} }

    Returns the pipeline run result (same envelope as /cam/pipeline/run).
    
    Args:
        preset_id: Unique identifier for the saved preset
        request: FastAPI request object for base URL construction
        
    Returns:
        Pipeline execution result with run_id and step outputs
        
    Raises:
        HTTPException: 404 if preset not found, 500 if spec invalid, 502 if pipeline call fails
    """
    preset = _preset_store.get(preset_id)
    if not preset:
        raise HTTPException(status_code=404, detail=f"Preset {preset_id!r} not found")

    spec = preset.get("spec")
    if not isinstance(spec, dict):
        raise HTTPException(status_code=500, detail="Preset spec is missing or invalid")

    base_url = str(request.base_url).rstrip("/")
    pipeline_url = f"{base_url}/cam/pipeline/run"

    # Defer to existing pipeline router via internal HTTP call to keep behavior unified
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(pipeline_url, json={"spec": spec}, timeout=60.0)
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=502,
                detail=f"Failed to call pipeline runner: {exc}",
            ) from exc

    if resp.status_code != 200:
        try:
            detail = resp.json()
        except Exception:
            detail = resp.text
        raise HTTPException(status_code=resp.status_code, detail=detail)

    return resp.json()
