from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.art_job_store import _load as load_art_jobs, get_job
from app.services.art_presets_store import (
    create_preset,
    delete_preset,
    list_presets,
)

# NOTE: Legacy rosette router removed - canonical routes now in:
# - app.art_studio.api.rosette_jobs_routes (mounted at /api/art/rosette)
# - app.art_studio.api.rosette_compare_routes (mounted at /api/art/rosette/compare)
# Removal date: 2026-02-05 (WP-2: API Surface Reduction)

try:  # pragma: no cover - optional adaptive lane
    from app.routers.art.adaptive_router import router as adaptive_router  # type: ignore
except (ImportError, ModuleNotFoundError):  # WP-1: optional module import
    adaptive_router = None

try:  # pragma: no cover - optional relief lane
    from app.routers.art.relief_router import router as relief_router  # type: ignore
except (ImportError, ModuleNotFoundError):  # WP-1: optional module import
    relief_router = None

router = APIRouter(prefix="/api/art", tags=["art"])

if adaptive_router is not None:
    router.include_router(adaptive_router, prefix="/adaptive")

if relief_router is not None:
    router.include_router(relief_router, prefix="/relief")


@router.get("/jobs", summary="List all Art Studio jobs")
async def list_art_jobs(lane: Optional[str] = None, limit: int = 200) -> list[dict[str, Any]]:
    jobs = load_art_jobs()
    jobs.sort(key=lambda j: j.get("created_at", 0), reverse=True)

    if lane:
        jobs = [j for j in jobs if j.get("lane") == lane]

    return jobs[: max(1, limit)]


@router.get("/jobs/{job_id}", summary="Get Art Studio job by ID")
async def get_art_job(job_id: str) -> Dict[str, Any]:
    row = get_job(job_id)
    if not row:
        return {"error": f"Job not found: {job_id}"}
    return row


class ArtPresetCreateIn(BaseModel):
    lane: str = Field(..., description="rosette / adaptive / relief / all")
    name: str = Field(..., description="Human readable preset name")
    params: Dict[str, Any] = Field(default_factory=dict)


@router.get("/presets", summary="List Art Studio presets")
async def list_art_presets(lane: Optional[str] = None):
    return list_presets(lane=lane)


@router.post("/presets", summary="Create Art Studio preset")
async def create_art_preset(req: ArtPresetCreateIn):
    preset = create_preset(req.lane, req.name, req.params)
    return {
        "id": preset.id,
        "lane": preset.lane,
        "name": preset.name,
        "params": preset.params,
        "created_at": preset.created_at,
    }


@router.delete("/presets/{preset_id}", summary="Delete Art Studio preset")
async def delete_art_preset(preset_id: str):
    ok = delete_preset(preset_id)
    return {"ok": ok, "preset_id": preset_id}
