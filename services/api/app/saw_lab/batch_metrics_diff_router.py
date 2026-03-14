"""Batch Metrics Diff Router - Compare rollup artifacts.

Provides:
- GET /rollups/diff - Compute diff between two rollup artifacts

Total: 1 route for rollup comparison.

LANE: UTILITY
"""

from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Query

from app.saw_lab.store import get_artifact

router = APIRouter(tags=["saw", "batch", "diff"])


@router.get("/rollups/diff")
def compute_rollup_diff(
    left_rollup_artifact_id: str = Query(..., description="Left rollup artifact ID"),
    right_rollup_artifact_id: str = Query(..., description="Right rollup artifact ID"),
) -> Dict[str, Any]:
    """Compute diff between two rollup artifacts."""
    left = get_artifact(left_rollup_artifact_id)
    right = get_artifact(right_rollup_artifact_id)

    if not left:
        raise HTTPException(
            status_code=404, detail=f"Left rollup not found: {left_rollup_artifact_id}"
        )
    if not right:
        raise HTTPException(
            status_code=404,
            detail=f"Right rollup not found: {right_rollup_artifact_id}",
        )

    left_metrics = left.get("payload", {}).get("metrics", {})
    right_metrics = right.get("payload", {}).get("metrics", {})

    # Compute diffs
    metrics_diff = {}
    all_keys = set(left_metrics.keys()) | set(right_metrics.keys())
    for key in all_keys:
        left_val = left_metrics.get(key, 0)
        right_val = right_metrics.get(key, 0)
        if isinstance(left_val, (int, float)) and isinstance(right_val, (int, float)):
            metrics_diff[key] = {
                "left": left_val,
                "right": right_val,
                "delta": right_val - left_val,
            }

    return {
        "left_artifact_id": left_rollup_artifact_id,
        "right_artifact_id": right_rollup_artifact_id,
        "metrics": metrics_diff,
    }


__all__ = ["router"]
