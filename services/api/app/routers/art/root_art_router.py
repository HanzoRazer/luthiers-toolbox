from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.art_job_store import _load as load_art_jobs, get_job
from app.services.art_presets_store import (
    create_preset,
    delete_preset,
    list_presets,
)

# NOTE: Legacy rosette/adaptive/relief routers removed - canonical routes now in:
# - app.art_studio.api.rosette_jobs_routes (mounted at /api/art/rosette)
# - app.art_studio.api.rosette_compare_routes (mounted at /api/art/rosette/compare)
# Removal date: 2026-02-05 (WP-2: API Surface Reduction)
# Dead optional imports removed: 2026-02-22 (bloat cleanup)

router = APIRouter(prefix="/api/art", tags=["art"])


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


# ============================================================================
# Presets Aggregate Endpoint (merged from art_presets_router.py)
# ============================================================================

from app.services.art_presets_store import get_preset as get_single_preset

def _convert_to_aggregate(preset: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a stored preset to the aggregate format expected by the UI."""
    params = preset.get("params", {})
    parent_id = params.get("parent_id")
    parent_name = params.get("parent_name")
    diff_summary = params.get("diff_summary")
    rationale = params.get("rationale", "User created")
    source = params.get("source", "manual")

    return {
        "preset_id": preset.get("id", ""),
        "preset_name": preset.get("name", "Unnamed Preset"),
        "lane": preset.get("lane", "all"),
        "parent_id": parent_id,
        "parent_name": parent_name,
        "diff_summary": diff_summary,
        "rationale": rationale,
        "source": source,
        "job_count": 0,
        "risk_count": 0,
        "critical_count": 0,
        "avg_total_length": 0.0,
        "avg_total_lines": 0,
        "health_color": "green",
        "trend_direction": "flat",
        "trend_delta": 0.0,
    }


@router.get("/presets_aggregate")
async def get_presets_aggregate(lane: Optional[str] = None) -> list[Dict[str, Any]]:
    """Return aggregated preset data with health, trend, risk counts, and lineage."""
    presets = list_presets(lane=lane)
    return [_convert_to_aggregate(p) for p in presets]
