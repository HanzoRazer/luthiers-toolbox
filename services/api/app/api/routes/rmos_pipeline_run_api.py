"""
RMOS Pipeline Run API Router (N10.2.1)

Job execution with safety mode evaluation for experimental/high-risk lanes.
"""

from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.api.deps.rmos_stores import get_pattern_store, get_joblog_store
from app.schemas.rmos_safety import SafetyActionContext
from app.core import rmos_safety_policy as safety_policy


router = APIRouter()


class RunPipelineRequest(BaseModel):
    """Request body for pipeline run."""
    pattern_id: str
    lane: str
    job_params: Optional[dict] = None
    override_token: Optional[str] = None


class RunPipelineResponse(BaseModel):
    """Response for successful pipeline start."""
    job_id: str
    pattern_id: str
    lane: str
    safety_decision: dict


@router.post("/run", response_model=RunPipelineResponse)
def run_pipeline(body: RunPipelineRequest):
    """
    Start a job run on specified lane with safety mode evaluation.
    
    Safety rules apply to high-risk lanes (experimental, tuned_v2) and fragile materials:
    - Unrestricted: High-risk requires override
    - Apprentice: High-risk denied, medium-risk requires override
    - Mentor review: High-risk requires override
    
    Returns 403 Forbidden if safety policy blocks (deny or invalid override).
    Returns 409 Conflict if requires override.
    
    Body:
    - pattern_id: Pattern/preset ID to run
    - lane: Target lane (safe, tuned_v1, tuned_v2, experimental)
    - job_params: Optional job parameters (feeds, speeds, etc.)
    - override_token: Optional mentor override token for safety policy
    
    Example:
        POST /api/rmos/pipeline/run
        {
          "pattern_id": "preset_abc123",
          "lane": "experimental",
          "job_params": {"feed_xy": 1200},
          "override_token": "OVR-1701345678123456"
        }
    
    Success response:
        {
          "job_id": "JOB-20251130-103045",
          "pattern_id": "preset_abc123",
          "lane": "experimental",
          "safety_decision": {
            "decision": "allow",
            "mode": "unrestricted",
            "risk_level": "high",
            "reason": "Override accepted: Override accepted."
          }
        }
    
    Blocked by safety (403):
        {
          "detail": "Job start denied by safety policy: High-risk action denied in apprentice mode; mentor must run this."
        }
    
    Requires override (409):
        {
          "detail": {
            "message": "High-risk action in unrestricted mode; override recommended for fragile / experimental work.",
            "safety_decision": {...},
            "policy": "safety_mode"
          }
        }
    """
    # 1. Get pattern and extract metadata
    pattern_store = get_pattern_store()
    try:
        pat = pattern_store.get(body.pattern_id)
    except Exception:
        raise HTTPException(status_code=404, detail=f"Pattern '{body.pattern_id}' not found.")

    if not pat:
        raise HTTPException(status_code=404, detail=f"Pattern '{body.pattern_id}' not found.")

    # Extract fragility/risk data
    meta = pat.get("metadata") or {}
    analytics = meta.get("analytics") or {}
    frag = analytics.get("worst_fragility_score") or meta.get("worst_fragility_score")
    grade = analytics.get("risk_grade") or meta.get("risk_grade")

    # 2. SAFETY MODE EVALUATION
    # Use different action for experimental/tuned_v2 lanes
    action_name = "run_experimental_lane" if body.lane.lower() in ("experimental", "tuned_v2") else "start_job"
    
    ctx = SafetyActionContext(
        action=action_name,
        lane=body.lane,
        fragility_score=frag,
        risk_grade=grade,
        preset_id=body.pattern_id,
    )

    decision = safety_policy.evaluate_action(ctx)

    # If override token provided, try to consume it
    if body.override_token:
        ok, msg = safety_policy.consume_override_token(body.override_token, ctx.action)
        if not ok:
            raise HTTPException(status_code=403, detail=msg)
        # Override accepted - treat as allow
        decision.decision = "allow"
        decision.requires_override = False
        decision.reason = f"Override accepted: {msg}"

    # Enforce safety decision
    if decision.decision == "deny":
        raise HTTPException(
            status_code=403,
            detail=f"Job start denied by safety policy: {decision.reason}",
        )
    if decision.decision == "require_override":
        raise HTTPException(
            status_code=409,
            detail={
                "message": decision.reason,
                "safety_decision": decision.dict(),
                "policy": "safety_mode",
            },
        )

    # 3. START PIPELINE JOB (safety passed)
    # Generate job ID (in real system, this would kick off actual job execution)
    import datetime
    job_id = f"JOB-{datetime.datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"

    # Log job start
    joblog_store = get_joblog_store()
    try:
        joblog_store.create({
            "job_id": job_id,
            "preset_id": body.pattern_id,
            "job_type": "pipeline_run",
            "lane": body.lane,
            "promotion_lane": body.lane,
            "risk_grade": grade or "UNKNOWN",
            "metadata": {
                "job_params": body.job_params or {},
                "safety_decision": decision.dict(),
                "fragility_score": frag,
            },
        })
    except Exception as e:
        print(f"Warning: Failed to log job start: {e}")

    return RunPipelineResponse(
        job_id=job_id,
        pattern_id=body.pattern_id,
        lane=body.lane,
        safety_decision=decision.dict(),
    )
