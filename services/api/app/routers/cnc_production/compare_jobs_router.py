# File: services/api/app/routers/cnc_production/compare_jobs_router.py
# B21 – CompareRunsPanel API endpoint

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ...services.job_int_log import load_all_job_logs, find_job_log_by_run_id, update_job_baseline

router = APIRouter(prefix="/cnc/jobs", tags=["cnc-production"])


@router.get("/compare")
async def compare_jobs(
    ids: str = Query(..., description="Comma-separated run_ids to compare (2-4 jobs)")
) -> Dict[str, Any]:
    """
    Compare multiple job runs side-by-side.
    
    Returns:
        - jobs: List of job entries with full artifacts
        - comparison: Computed metrics table for UI rendering
    """
    run_ids = [rid.strip() for rid in ids.split(",") if rid.strip()]
    
    if len(run_ids) < 2:
        raise HTTPException(status_code=400, detail="Minimum 2 jobs required for comparison")
    if len(run_ids) > 4:
        raise HTTPException(status_code=400, detail="Maximum 4 jobs supported")
    
    all_logs = load_all_job_logs()
    jobs: List[Dict[str, Any]] = []
    
    for run_id in run_ids:
        entry = find_job_log_by_run_id(run_id)
        if not entry:
            raise HTTPException(status_code=404, detail=f"Job {run_id} not found")
        jobs.append(entry)
    
    # Build comparison table
    comparison = _build_comparison_table(jobs)
    
    return {
        "jobs": jobs,
        "comparison": comparison,
        "job_count": len(jobs)
    }


def _build_comparison_table(jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate comparison metrics table with winner detection.
    
    Returns dict with metric rows and winner indicators.
    """
    if not jobs:
        return {}
    
    metrics = {}
    
    # Machine
    machines = [j.get("machine_id", "—") for j in jobs]
    metrics["machine"] = {"values": machines, "winner": None}
    
    # Material
    materials = [j.get("material", "—") for j in jobs]
    metrics["material"] = {"values": materials, "winner": None}
    
    # Post Processor
    posts = [j.get("post_id", "—") for j in jobs]
    metrics["post"] = {"values": posts, "winner": None}
    
    # Predicted Time
    times = [j.get("sim_time_s") for j in jobs]
    if any(t is not None for t in times):
        min_time = min((t for t in times if t is not None), default=None)
        winner_idx = times.index(min_time) if min_time is not None else None
        metrics["predicted_time_s"] = {
            "values": times,
            "winner": winner_idx,
            "direction": "lower"  # Lower is better
        }
    
    # Energy
    energies = [j.get("sim_energy_j") for j in jobs]
    if any(e is not None for e in energies):
        min_energy = min((e for e in energies if e is not None), default=None)
        winner_idx = energies.index(min_energy) if min_energy is not None else None
        metrics["energy_j"] = {
            "values": energies,
            "winner": winner_idx,
            "direction": "lower"
        }
    
    # Move Count
    moves = [j.get("sim_move_count") for j in jobs]
    if any(m is not None for m in moves):
        min_moves = min((m for m in moves if m is not None), default=None)
        winner_idx = moves.index(min_moves) if min_moves is not None else None
        metrics["move_count"] = {
            "values": moves,
            "winner": winner_idx,
            "direction": "lower"
        }
    
    # Issue Count
    issues = [j.get("sim_issue_count") for j in jobs]
    if any(i is not None for i in issues):
        min_issues = min((i for i in issues if i is not None), default=None)
        winner_idx = issues.index(min_issues) if min_issues is not None else None
        metrics["issue_count"] = {
            "values": issues,
            "winner": winner_idx,
            "direction": "lower"
        }
    
    # Max Deviation
    devs = [j.get("sim_max_dev_pct") for j in jobs]
    if any(d is not None for d in devs):
        min_dev = min((d for d in devs if d is not None), default=None)
        winner_idx = devs.index(min_dev) if min_dev is not None else None
        metrics["max_deviation_pct"] = {
            "values": devs,
            "winner": winner_idx,
            "direction": "lower"
        }
    
    # Notes
    notes = [j.get("notes", "") for j in jobs]
    metrics["notes"] = {"values": notes, "winner": None}
    
    # Tags
    tags = [j.get("tags", []) for j in jobs]
    metrics["tags"] = {"values": tags, "winner": None}
    
    return metrics


# B26 – Baseline marking endpoint
class SetBaselineRequest(BaseModel):
    baseline_id: str | None = None


@router.post("/{run_id}/set-baseline")
async def set_job_baseline(run_id: str, body: SetBaselineRequest) -> Dict[str, Any]:
    """
    Mark a job as a baseline or clear baseline status.
    
    Args:
        run_id: Job identifier
        baseline_id: Optional baseline identifier (None to clear)
    
    Returns:
        Updated job entry
    """
    # Verify job exists
    entry = find_job_log_by_run_id(run_id)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Job {run_id} not found")
    
    # Update baseline_id field
    success = update_job_baseline(run_id, body.baseline_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update job baseline")
    
    # Return updated entry
    updated = find_job_log_by_run_id(run_id)
    return {
        "success": True,
        "run_id": run_id,
        "baseline_id": body.baseline_id,
        "job": updated
    }

