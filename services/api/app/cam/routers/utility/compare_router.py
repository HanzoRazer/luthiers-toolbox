"""Compare Router — Job comparison endpoints.

Provides:
- GET /compare/diff - Compare two job runs by ID
"""
from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Query

from ....services.job_int_log import find_job_log_by_run_id
from ....services.jobint_artifacts import extract_jobint_artifacts

router = APIRouter(prefix="/compare")


@router.get("/diff")
def compare_job_diff(baseline: str = Query(...), compare: str = Query(...)) -> Dict[str, Any]:
    """Compare two job runs by ID and return toolpath/geometry diffs."""
    job_base = find_job_log_by_run_id(baseline)
    job_comp = find_job_log_by_run_id(compare)
    if not job_base or not job_comp:
        raise HTTPException(status_code=404, detail="One or both job IDs not found")

    base_geom, base_plan, base_moves, base_path = extract_jobint_artifacts(job_base)
    comp_geom, comp_plan, comp_moves, comp_path = extract_jobint_artifacts(job_comp)

    def get_stats(job_dict: Dict[str, Any]) -> Dict[str, Any]:
        stats = job_dict.get("stats", {})
        return {
            "length": stats.get("length_mm"),
            "time": stats.get("time_s"),
            "retracts": stats.get("retract_count"),
        }

    base_stats = get_stats(job_base)
    comp_stats = get_stats(job_comp)
    delta = {
        "length": (comp_stats["length"] or 0) - (base_stats["length"] or 0),
        "time": (comp_stats["time"] or 0) - (base_stats["time"] or 0),
        "retracts": (comp_stats["retracts"] or 0) - (base_stats["retracts"] or 0),
    }

    return {
        "baseline": {
            "id": baseline,
            "toolpath": base_moves,
            "geometry": base_geom,
            "stats": base_stats,
            "meta": job_base.get("meta", {}),
        },
        "compare": {
            "id": compare,
            "toolpath": comp_moves,
            "geometry": comp_geom,
            "stats": comp_stats,
            "meta": job_comp.get("meta", {}),
        },
        "delta": delta,
    }


__all__ = ["router"]
