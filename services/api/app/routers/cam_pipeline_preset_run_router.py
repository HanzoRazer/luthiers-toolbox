"""
Luthier's Tool Box - CNC Guitar Lutherie CAD/CAM Toolbox
CAM Pipeline Preset Router - CRUD + Execute saved pipeline presets

Part of Phase 25.0: Pipeline Preset Integration
Repository: HanzoRazer/luthiers-toolbox
Created: January 2025

Features:
- List, create, delete pipeline presets
- Run saved pipeline presets by ID
- Forward preset spec to /cam/pipeline/run
- Unified pipeline execution via internal HTTP call
- Error handling with proper HTTP status codes
- Returns complete pipeline run result

Endpoints:
    GET  /presets                - List all saved presets
    POST /presets                - Create a new preset
    DELETE /presets/{preset_id}  - Delete a preset
    POST /presets/{preset_id}/run - Run a preset
"""

from __future__ import annotations

from typing import Any, Dict, List

import httpx
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from ..services.pipeline_preset_store import PipelinePresetStore

router = APIRouter(prefix="/cam/pipeline", tags=["cam", "pipeline", "presets"])

_preset_store = PipelinePresetStore()


class PresetCreate(BaseModel):
    """Schema for creating a pipeline preset."""
    name: str
    description: str = ""
    spec: Dict[str, Any]


@router.get("/presets")
def list_presets() -> List[Dict[str, Any]]:
    """
    List all saved pipeline presets.

    Returns:
        List of preset objects with id, name, description, spec
    """
    return _preset_store.list()


@router.post("/presets")
def create_preset(payload: PresetCreate) -> Dict[str, Any]:
    """
    Create a new pipeline preset.

    Args:
        payload: Preset data with name, description, and spec

    Returns:
        Created preset with generated id
    """
    return _preset_store.save(payload.model_dump())


@router.delete("/presets/{preset_id}")
def delete_preset(preset_id: str) -> Dict[str, Any]:
    """
    Delete a pipeline preset by ID.

    Args:
        preset_id: The preset ID to delete

    Returns:
        Confirmation with deleted preset ID

    Raises:
        HTTPException: 404 if preset not found
    """
    preset = _preset_store.get(preset_id)
    if not preset:
        raise HTTPException(status_code=404, detail=f"Preset {preset_id!r} not found")
    _preset_store.delete(preset_id)
    return {"ok": True, "deleted": preset_id}


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
        except (ValueError, TypeError):  # WP-1: narrowed from except Exception
            detail = resp.text
        raise HTTPException(status_code=resp.status_code, detail=detail)

    return resp.json()
