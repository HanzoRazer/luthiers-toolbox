"""
Art Studio - Preset Aggregate Router

Provides /api/art/presets_aggregate endpoint for Tuning Tree and Compare Mode.
WIRED to art_presets_store.py for persistent preset storage.

Endpoints:
    GET /art/presets_aggregate - List presets with aggregate stats
"""
from fastapi import APIRouter, Query
from typing import List, Dict, Any, Optional

from app.services.art_presets_store import list_presets, get_preset

router = APIRouter()


def _convert_to_aggregate(preset: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a stored preset to the aggregate format expected by the UI.

    Stats fields (job_count, risk_count, etc.) default to 0/neutral since
    job-to-preset associations are not yet tracked. These will be enriched
    when job history linking is implemented.
    """
    params = preset.get("params", {})

    # Extract lineage info from params if present
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
        # Stats default to 0/neutral - will be enriched when job tracking is wired
        "job_count": 0,
        "risk_count": 0,
        "critical_count": 0,
        "avg_total_length": 0.0,
        "avg_total_lines": 0,
        "health_color": "green",
        "trend_direction": "flat",
        "trend_delta": 0.0,
    }


@router.get("/art/presets_aggregate")
async def get_presets_aggregate(
    lane: Optional[str] = Query(default=None, description="Filter by lane (rosette/adaptive/relief)")
) -> List[Dict[str, Any]]:
    """
    Return aggregated preset data with health, trend, risk counts, and lineage.

    Reads from persistent art_presets_store. Stats fields (job_count, risk_count, etc.)
    are placeholder values until job-to-preset tracking is implemented.

    Used by:
    - ArtPresetTuningTree.vue
    - ArtPresetCompareAB.vue
    - ArtStudioRosetteCompare.vue
    """
    presets = list_presets(lane=lane)
    return [_convert_to_aggregate(p) for p in presets]
