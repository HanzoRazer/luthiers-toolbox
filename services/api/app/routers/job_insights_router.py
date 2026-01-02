"""
Job Intelligence System — AI-assisted job analysis with gate/review classification.

Routes:
- GET /api/cam/job_log/insights/{job_id} — Single job analysis
- GET /api/cam/job_log/insights — List with machine/wood filters

Classification:
- below_gate: Job well under review threshold (ok)
- near_gate: Job approaching review threshold (warn)
- over_gate: Job exceeds review threshold but under critical (warn)
- blocked: Job exceeds critical gate (error)

Wood Inference:
- Regex-based heuristic from job name/note (ebony, maple, rosewood, etc.)
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/api/cam/job_log", tags=["CAM Job Intelligence"])


# Mock job log storage (replace with real DB in production)
JOB_LOG_DIR = Path("data/cam_jobs")


def _ensure_job_log_dir() -> None:
    """Create job log directory on first write (Docker compatibility)."""
    JOB_LOG_DIR.mkdir(parents=True, exist_ok=True)


def infer_wood_type(job_name: str, job_note: str) -> Optional[str]:
    """
    Infer wood type from job name or note using regex patterns.
    
    Args:
        job_name: Job name string
        job_note: Job note string
    
    Returns:
        Wood type string (lowercase) or None if not detected
    """
    combined = (job_name + " " + job_note).lower()
    
    # Common wood patterns
    patterns = {
        "ebony": r"\bebony\b",
        "maple": r"\bmaple\b",
        "rosewood": r"\brosewood\b",
        "mahogany": r"\bmahogany\b",
        "walnut": r"\bwalnut\b",
        "cherry": r"\bcherry\b",
        "oak": r"\boak\b",
        "ash": r"\bash\b",
        "alder": r"\balder\b",
        "basswood": r"\bbasswood\b"
    }
    
    for wood, pattern in patterns.items():
        if re.search(pattern, combined):
            return wood
    
    return None


def classify_job(
    actual_time_s: float,
    review_threshold_s: float = 300.0,  # 5 minutes
    critical_gate_s: float = 600.0      # 10 minutes
) -> dict:
    """
    Classify job based on actual time vs thresholds.
    
    Args:
        actual_time_s: Actual job runtime in seconds
        review_threshold_s: Review threshold (warn if near or over)
        critical_gate_s: Critical gate (error if over)
    
    Returns:
        dict with classification, severity, recommendation
    """
    
    # Calculate percentages
    review_pct = (actual_time_s / review_threshold_s) * 100.0
    gate_pct = (actual_time_s / critical_gate_s) * 100.0
    
    if actual_time_s < review_threshold_s * 0.8:
        # Below 80% of review threshold → ok
        classification = "below_gate"
        severity = "ok"
        recommendation = "Job well within normal parameters. No action needed."
    
    elif actual_time_s < review_threshold_s:
        # 80-100% of review threshold → warn
        classification = "near_gate"
        severity = "warn"
        recommendation = f"Job approaching review threshold ({review_pct:.0f}%). Consider optimizing feeds."
    
    elif actual_time_s < critical_gate_s:
        # Between review and critical → warn
        classification = "over_gate"
        severity = "warn"
        recommendation = f"Job exceeded review threshold ({review_pct:.0f}%). Review toolpath and parameters."
    
    else:
        # Over critical gate → error
        classification = "blocked"
        severity = "error"
        recommendation = f"Job exceeded critical gate ({gate_pct:.0f}%). Immediate review required. Check for errors."
    
    return {
        "classification": classification,
        "severity": severity,
        "review_pct": round(review_pct, 1),
        "gate_pct": round(gate_pct, 1),
        "recommendation": recommendation
    }


@router.get("/insights/{job_id}")
def get_job_insights(job_id: str) -> Dict[str, Any]:
    """
    Get intelligence analysis for a single job.
    
    Args:
        job_id: Job identifier
    
    Returns:
        dict with classification, wood_type, analysis, recommendations
    """
    
    # Load job data (mock implementation)
    job_file = JOB_LOG_DIR / f"{job_id}.json"
    if not job_file.exists():
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    with open(job_file) as f:
        job_data = json.load(f)
    
    # Extract job info
    job_name = job_data.get("name", "")
    job_note = job_data.get("note", "")
    actual_time_s = job_data.get("actual_time_s", 0.0)
    estimated_time_s = job_data.get("estimated_time_s", 0.0)
    
    # Infer wood type
    wood_type = infer_wood_type(job_name, job_note)
    
    # Classify job
    classification = classify_job(actual_time_s)
    
    # Build analysis
    time_diff_pct = ((actual_time_s - estimated_time_s) / estimated_time_s * 100.0) if estimated_time_s > 0 else 0.0
    
    analysis = {
        "job_id": job_id,
        "job_name": job_name,
        "wood_type": wood_type or "unknown",
        "actual_time_s": actual_time_s,
        "estimated_time_s": estimated_time_s,
        "time_diff_pct": round(time_diff_pct, 1),
        "classification": classification["classification"],
        "severity": classification["severity"],
        "review_pct": classification["review_pct"],
        "gate_pct": classification["gate_pct"],
        "recommendation": classification["recommendation"]
    }
    
    return analysis


@router.get("/insights")
def list_job_insights(
    machine_id: Optional[str] = Query(None, description="Filter by machine ID"),
    wood_type: Optional[str] = Query(None, description="Filter by wood type"),
    severity: Optional[str] = Query(None, description="Filter by severity (ok/warn/error)"),
    limit: int = Query(50, ge=1, le=500, description="Maximum results")
) -> List[Dict[str, Any]]:
    """
    List job insights with optional filters.
    
    Args:
        machine_id: Filter by machine ID
        wood_type: Filter by wood type
        severity: Filter by severity
        limit: Maximum results
    
    Returns:
        List of job insight summaries
    """
    
    # Load all jobs (mock implementation)
    job_files = list(JOB_LOG_DIR.glob("*.json"))
    
    insights = []
    
    for job_file in job_files[:limit]:
        try:
            with open(job_file) as f:
                job_data = json.load(f)
            
            # Extract job info
            job_id = job_file.stem
            job_name = job_data.get("name", "")
            job_note = job_data.get("note", "")
            actual_time_s = job_data.get("actual_time_s", 0.0)
            job_machine_id = job_data.get("machine_id", "")
            
            # Apply filters
            if machine_id and job_machine_id != machine_id:
                continue
            
            # Infer wood type
            inferred_wood = infer_wood_type(job_name, job_note)
            if wood_type and inferred_wood != wood_type.lower():
                continue
            
            # Classify job
            classification = classify_job(actual_time_s)
            
            # Apply severity filter
            if severity and classification["severity"] != severity:
                continue
            
            insights.append({
                "job_id": job_id,
                "job_name": job_name,
                "wood_type": inferred_wood or "unknown",
                "actual_time_s": actual_time_s,
                "classification": classification["classification"],
                "severity": classification["severity"],
                "review_pct": classification["review_pct"]
            })
        
        except Exception as e:
            # Skip invalid job files
            continue
    
    return {
        "total": len(insights),
        "insights": insights
    }
