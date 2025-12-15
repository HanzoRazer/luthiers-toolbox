"""
Art Studio - Preset Aggregate Router
Provides /api/art/presets_aggregate endpoint for Tuning Tree and Compare Mode
"""
from fastapi import APIRouter
from typing import List, Dict, Any, Optional

router = APIRouter()

@router.get("/presets_aggregate")
async def get_presets_aggregate() -> List[Dict[str, Any]]:
    """
    Return aggregated preset data with health, trend, risk counts, and lineage.
    
    Used by:
    - ArtPresetTuningTree.vue
    - ArtPresetCompareAB.vue
    - ArtStudioRosetteCompare.vue
    """
    # Mock data for Phase 30.5 - replace with actual preset aggregation logic
    return [
        {
            "preset_id": "rosette_preset_001",
            "preset_name": "Rosette Base (12-petal)",
            "lane": "rosette",
            "parent_id": None,
            "parent_name": None,
            "diff_summary": None,
            "rationale": "Initial design",
            "source": "manual",
            "job_count": 45,
            "risk_count": 3,
            "critical_count": 0,
            "avg_total_length": 2450.5,
            "avg_total_lines": 1850,
            "health_color": "green",
            "trend_direction": "flat",
            "trend_delta": 0.0
        },
        {
            "preset_id": "rosette_preset_002",
            "preset_name": "Rosette Tuned (tighter spacing)",
            "lane": "rosette",
            "parent_id": "rosette_preset_001",
            "parent_name": "Rosette Base (12-petal)",
            "diff_summary": "Reduced petal_spacing by 15%",
            "rationale": "Reduce risk of overload in tight curves",
            "source": "auto_tune",
            "job_count": 12,
            "risk_count": 1,
            "critical_count": 0,
            "avg_total_length": 2320.8,
            "avg_total_lines": 1780,
            "health_color": "green",
            "trend_direction": "down",
            "trend_delta": -5.3
        },
        {
            "preset_id": "adaptive_preset_001",
            "preset_name": "Adaptive Standard",
            "lane": "adaptive",
            "parent_id": None,
            "parent_name": None,
            "diff_summary": None,
            "rationale": "Default adaptive pocketing",
            "source": "manual",
            "job_count": 28,
            "risk_count": 8,
            "critical_count": 2,
            "avg_total_length": 5800.2,
            "avg_total_lines": 3200,
            "health_color": "yellow",
            "trend_direction": "up",
            "trend_delta": 12.5
        }
    ]
