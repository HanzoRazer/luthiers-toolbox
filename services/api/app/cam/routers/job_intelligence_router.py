"""
Job Intelligence Router

Job intelligence and insights endpoints for CAM operations.
Extracted from stub_routes.py during decomposition.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.services.job_int_log import (
    load_all_job_logs,
    find_job_log_by_run_id,
    DEFAULT_LOG_PATH,
)


router = APIRouter(tags=["cam", "job-intelligence"])


class FavoriteUpdateIn(BaseModel):
    """Request body for favorite toggle."""
    favorite: bool


@router.get("/job-int/log")
def list_job_intelligence_logs(
    machine_id: Optional[str] = Query(None),
    post_id: Optional[str] = Query(None),
    helical_only: Optional[bool] = Query(None),
    favorites_only: Optional[bool] = Query(None),
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0),
) -> Dict[str, Any]:
    """List job intelligence logs with filtering."""
    all_logs = load_all_job_logs()

    filtered = all_logs
    if machine_id:
        filtered = [e for e in filtered if e.get("machine_id") == machine_id]
    if post_id:
        filtered = [e for e in filtered if e.get("post_id") == post_id]
    if helical_only:
        filtered = [e for e in filtered if e.get("use_helical")]
    if favorites_only:
        filtered = [e for e in filtered if e.get("favorite")]

    filtered.sort(key=lambda x: x.get("created_at", ""), reverse=True)

    total = len(filtered)
    items = filtered[offset:offset + limit]

    return {"total": total, "items": items}


@router.get("/job-int/log/{run_id}")
def get_job_intelligence_log(run_id: str) -> Dict[str, Any]:
    """Get job intelligence log by run_id."""
    entry = find_job_log_by_run_id(run_id)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Job log '{run_id}' not found")
    return entry


@router.post("/job-int/favorites/{run_id}")
def update_job_favorite(run_id: str, body: FavoriteUpdateIn) -> Dict[str, Any]:
    """Update favorite status for a job log."""
    all_logs = load_all_job_logs()
    found_idx = None
    for i, entry in enumerate(all_logs):
        if entry.get("run_id") == run_id:
            found_idx = i
            break

    if found_idx is None:
        raise HTTPException(status_code=404, detail=f"Job log '{run_id}' not found")

    all_logs[found_idx]["favorite"] = body.favorite

    path = DEFAULT_LOG_PATH
    if os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            for entry in all_logs:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    return all_logs[found_idx]


# =============================================================================
# Job Log Insights
# =============================================================================


def _compute_job_insights(job: Dict[str, Any]) -> Dict[str, Any]:
    """Compute job intelligence insights from job log data."""
    job_id = job.get("run_id") or job.get("job_id") or "unknown"
    job_name = job.get("job_name") or f"Job {job_id[:8]}"
    wood_type = job.get("material") or "Unknown"

    estimated_time_s = job.get("sim_time_s") or 0
    actual_time_s = job.get("actual_time_s")
    if actual_time_s is None:
        move_count = job.get("sim_move_count") or 0
        actual_time_s = move_count * 0.1 if move_count > 0 else estimated_time_s

    if estimated_time_s > 0:
        time_diff_pct = round(((actual_time_s - estimated_time_s) / estimated_time_s) * 100, 1)
    else:
        time_diff_pct = 0.0

    abs_diff = abs(time_diff_pct)
    if abs_diff <= 5:
        classification = "on_target"
        severity = "ok"
        recommendation = "Job performance is within expected parameters. No adjustments needed."
    elif abs_diff <= 15:
        if time_diff_pct > 0:
            classification = "slightly_slow"
            severity = "ok"
            recommendation = "Job ran slightly slower than estimated. Consider checking tool wear or feed rates."
        else:
            classification = "slightly_fast"
            severity = "ok"
            recommendation = "Job completed faster than estimated. Verify quality meets specifications."
    elif abs_diff <= 30:
        if time_diff_pct > 0:
            classification = "moderately_slow"
            severity = "warn"
            recommendation = "Significant slowdown detected. Review machining parameters, tool condition, and material properties."
        else:
            classification = "moderately_fast"
            severity = "warn"
            recommendation = "Job completed significantly faster. Verify cut quality and consider recalibrating time estimates."
    else:
        if time_diff_pct > 0:
            classification = "significantly_slow"
            severity = "error"
            recommendation = "Critical slowdown. Inspect for tool damage, material issues, or machine problems before next run."
        else:
            classification = "significantly_fast"
            severity = "error"
            recommendation = "Unusually fast completion. Verify all cuts were made correctly and quality is acceptable."

    review_pct = min(100, round((abs_diff / 15) * 80))
    gate_pct = min(100, round((abs_diff / 30) * 100))

    issue_count = job.get("sim_issue_count") or 0
    if issue_count > 0:
        review_pct = min(100, review_pct + issue_count * 5)
        if issue_count > 3:
            severity = "error" if severity == "warn" else severity
            recommendation += f" Note: {issue_count} simulation issues detected."

    return {
        "job_id": job_id,
        "job_name": job_name,
        "wood_type": wood_type,
        "actual_time_s": round(actual_time_s, 1),
        "estimated_time_s": round(estimated_time_s, 1),
        "time_diff_pct": time_diff_pct,
        "classification": classification,
        "severity": severity,
        "review_pct": review_pct,
        "gate_pct": gate_pct,
        "recommendation": recommendation,
    }


@router.get("/job_log/insights")
def get_job_insights(
    limit: int = Query(default=50, le=200),
    wood: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
) -> Dict[str, Any]:
    """Get job log insights summary."""
    all_logs = load_all_job_logs()

    insights = []
    for job in all_logs:
        insight = _compute_job_insights(job)

        if wood and insight["wood_type"].lower() != wood.lower():
            continue
        if severity and insight["severity"] != severity:
            continue

        insights.append(insight)

    insights.sort(key=lambda x: x.get("job_id", ""), reverse=True)

    return {
        "insights": insights[:limit],
        "total_jobs": len(insights),
    }


@router.get("/job_log/insights/{insight_id}")
def get_job_insight(insight_id: str) -> Dict[str, Any]:
    """Get specific job insight by run_id."""
    job = find_job_log_by_run_id(insight_id)

    if not job:
        return {
            "job_id": insight_id,
            "job_name": f"Job {insight_id[:8] if len(insight_id) >= 8 else insight_id}",
            "wood_type": "Unknown",
            "actual_time_s": 0,
            "estimated_time_s": 0,
            "time_diff_pct": 0,
            "classification": "unknown",
            "severity": "ok",
            "review_pct": 0,
            "gate_pct": 0,
            "recommendation": f"No job log found for ID: {insight_id}",
        }

    return _compute_job_insights(job)
