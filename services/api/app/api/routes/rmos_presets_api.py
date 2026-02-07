"""
RMOS Presets API Router (MM-5 + N10.2.1)

Preset/pattern lane promotion with:
- Ultra-fragility policy enforcement (MM-5)
- Safety mode evaluation (N10.2.1)
"""

from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.schemas.rmos_analytics import Lane
from app.core.rmos_promotion_policy import evaluate_promotion_policy
from app.api.deps.rmos_stores import get_pattern_store, get_joblog_store
from app.schemas.rmos_safety import SafetyActionContext
from app.core import rmos_safety_policy as safety_policy


router = APIRouter()


class PromoteRequest(BaseModel):
    """Request body for preset promotion."""
    target_lane: Lane
    reason: Optional[str] = None
    # N10.2.1: Optional override token from mentor
    override_token: Optional[str] = None


class PromoteResponse(BaseModel):
    """Response for successful promotion."""
    preset_id: str
    from_lane: str
    target_lane: Lane
    policy_reason: str
    policy_stats: dict


@router.post("/{preset_id}/promote", response_model=PromoteResponse)
def promote_preset(preset_id: str, body: PromoteRequest):
    """
    Promote preset to target lane with ultra-fragility policy enforcement.
    
    Policy checks (in order):
    1. Safety mode evaluation (N10.2.1) - apprentice/mentor rules
    2. Ultra-fragility policy (MM-5) - fragility limits + clean job requirements
    
    Safety mode rules:
    - Unrestricted: High-risk promotions require override
    - Apprentice: High-risk denied, medium-risk requires override
    - Mentor review: High-risk requires override
    
    Ultra-fragility policy checks:
    - Ultra-fragile materials (≥0.90) blocked from all lanes
    - Fragile materials (>0.60) blocked from 'safe' lane
    - Minimum clean job requirements per lane (safe: 5, tuned_v1: 3, tuned_v2: 4)
    
    Returns 403 Forbidden if safety policy blocks (deny or invalid override).
    Returns 409 Conflict if requires override or fragility policy blocks.
    
    Path params:
    - preset_id: Preset/pattern ID to promote
    
    Body:
    - target_lane: Destination lane (safe, tuned_v1, tuned_v2, experimental, archived)
    - reason: Optional human explanation for promotion
    - override_token: Optional mentor override token for safety policy
    
    Example:
        POST /api/rmos/presets/preset_abc123/promote
        {
          "target_lane": "safe",
          "reason": "Passed 6 validation runs with wood+resin",
          "override_token": "OVR-1701345678123456"
        }
    
    Success response:
        {
          "preset_id": "preset_abc123",
          "from_lane": "tuned_v1",
          "target_lane": "safe",
          "policy_reason": "Allowed: 6/8 jobs are clean; worst fragility 0.28 within policy limits...",
          "policy_stats": {
            "total_runs": 8,
            "clean_runs": 6,
            "worst_fragility_overall": 0.28,
            "worst_fragility_clean": 0.28,
            "safety_decision": {
              "decision": "allow",
              "mode": "unrestricted",
              "risk_level": "low"
            }
          }
        }
    
    Blocked by safety (403):
        {
          "detail": "Promotion denied by safety policy: High-risk action denied in apprentice mode; mentor must run this."
        }
    
    Requires override (409):
        {
          "detail": {
            "message": "High-risk action in unrestricted mode; override recommended for fragile / experimental work.",
            "safety_decision": {...},
            "policy": "safety_mode"
          }
        }
    
    Blocked by fragility (409):
        {
          "detail": {
            "message": "Blocked: worst fragility 0.94 exceeds ultra-fragile threshold 0.90...",
            "stats": {
              "total_runs": 3,
              "clean_runs": 0,
              "worst_fragility_overall": 0.94,
              "worst_fragility_clean": 0.0
            },
            "policy": "ultra_fragility_guard"
          }
        }
    """
    # Get preset first to extract metadata for safety evaluation
    pattern_store = get_pattern_store()
    try:
        pat = pattern_store.get(preset_id)
    except HTTPException:
        raise
    except Exception:  # WP-1: governance catch-all — HTTP endpoint
        raise HTTPException(status_code=404, detail=f"Preset '{preset_id}' not found.")

    if not pat:
        raise HTTPException(status_code=404, detail=f"Preset '{preset_id}' not found.")

    # Extract fragility/risk data from metadata
    meta = pat.get("metadata") or {}
    analytics = meta.get("analytics") or {}
    frag = analytics.get("worst_fragility_score") or meta.get("worst_fragility_score")
    grade = analytics.get("risk_grade") or meta.get("risk_grade")

    # 1. SAFETY MODE EVALUATION (N10.2.1)
    ctx = SafetyActionContext(
        action="promote_preset",
        lane=body.target_lane,
        fragility_score=frag,
        risk_grade=grade,
        preset_id=preset_id,
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
            detail=f"Promotion denied by safety policy: {decision.reason}",
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

    # 2. ULTRA-FRAGILITY POLICY CHECK (MM-5)
    allowed, policy_reason, stats = evaluate_promotion_policy(preset_id, body.target_lane)

    if not allowed:
        # Block promotion with clear message and stats
        raise HTTPException(
            status_code=409,
            detail={
                "message": policy_reason,
                "stats": stats,
                "policy": "ultra_fragility_guard",
            },
        )

    # 3. APPLY PROMOTION (both policies passed)
    from_lane = pat.get("promotion_lane") or pat.get("lane") or "unknown"
    
    # Update lane
    pat["promotion_lane"] = body.target_lane
    pattern_store.update(preset_id, pat)

    # 3. Log promotion to job log
    joblog_store = get_joblog_store()
    try:
        joblog_store.create({
            "preset_id": preset_id,
            "job_type": "preset_promote_manual",
            "from_lane": from_lane,
            "to_lane": body.target_lane,
            "lane": body.target_lane,
            "promotion_lane": body.target_lane,
            "risk_grade": "GREEN",  # Promotion itself is not risky
            "metadata": {
                "promotion_reason": body.reason or "Manual promotion",
                "policy_reason": policy_reason,
                "policy_stats": stats,
                "safety_decision": decision.dict(),  # N10.2.1: Include safety decision
            },
        })
    except Exception as e:  # WP-1: keep broad — non-critical joblog write
        print(f"Warning: Failed to log promotion to joblog: {e}")

    # Include safety decision in stats for response
    stats["safety_decision"] = decision.dict()

    return PromoteResponse(
        preset_id=preset_id,
        from_lane=from_lane,
        target_lane=body.target_lane,
        policy_reason=policy_reason,
        policy_stats=stats,
    )


@router.get("/{preset_id}/promotion-check")
def check_promotion_eligibility(preset_id: str, target_lane: Lane):
    """
    Check if preset is eligible for promotion without actually promoting.
    
    Useful for UI to show preview or disable promotion buttons.
    
    Query params:
    - target_lane: Lane to check eligibility for
    
    Returns:
        {
          "eligible": bool,
          "reason": str,
          "stats": {...}
        }
    
    Example:
        GET /api/rmos/presets/preset_abc123/promotion-check?target_lane=safe
        
        {
          "eligible": false,
          "reason": "Blocked: only 2 clean jobs found; 5 required for 'safe'.",
          "stats": {
            "total_runs": 4,
            "clean_runs": 2,
            "worst_fragility_overall": 0.45,
            "worst_fragility_clean": 0.42
          }
        }
    """
    allowed, reason, stats = evaluate_promotion_policy(preset_id, target_lane)
    
    return {
        "eligible": allowed,
        "reason": reason,
        "stats": stats,
    }
