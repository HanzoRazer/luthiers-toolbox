"""
RMOS N10.2: Safety API router for apprenticeship mode.

Endpoints:
- GET /rmos/safety/mode - Get current safety mode
- POST /rmos/safety/mode - Set safety mode (mentor/admin only)
- POST /rmos/safety/evaluate - Evaluate action safety
- POST /rmos/safety/create-override - Create override token (mentor only)
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...schemas.rmos_safety import (
    SafetyMode,
    SafetyModeState,
    SafetyActionContext,
    SafetyDecision,
    EvaluateActionResponse,
    OverrideToken,
)
from ...core import rmos_safety_policy as policy

router = APIRouter(prefix="/rmos/safety", tags=["rmos-safety"])


class SetModeRequest(BaseModel):
    """Request to set safety mode."""
    mode: SafetyMode
    set_by: str | None = None


class EvaluateRequest(SafetyActionContext):
    """Request to evaluate action safety with optional override token."""
    # Optional override token the operator is presenting
    override_token: str | None = None


class CreateOverrideRequest(BaseModel):
    """Request to create override token."""
    action: str
    created_by: str | None = None
    ttl_minutes: int = 15


@router.get("/mode", response_model=SafetyModeState)
def get_mode():
    """
    Get current safety mode state.
    
    Returns:
        SafetyModeState with mode, set_by, and set_at fields
    
    Example response:
        {
          "mode": "apprentice",
          "set_by": "mentor_alice",
          "set_at": "2025-11-30T10:15:00"
        }
    """
    return policy.get_safety_mode()


@router.post("/mode", response_model=SafetyModeState)
def set_mode(body: SetModeRequest):
    """
    Set safety mode (requires mentor/admin privileges).
    
    NOTE: In production, verify caller has mentor/admin role before allowing.
    
    Args:
        body: SetModeRequest with mode and optional set_by
    
    Returns:
        Updated SafetyModeState
    
    Example request:
        {
          "mode": "apprentice",
          "set_by": "mentor_alice"
        }
    """
    # TODO: Add auth check here when auth system is ready
    return policy.set_safety_mode(body.mode, set_by=body.set_by)


@router.post("/evaluate", response_model=EvaluateActionResponse)
def evaluate_action(body: EvaluateRequest):
    """
    Evaluate whether an action should be allowed, require override, or be denied.
    
    If override_token is provided, attempts to consume it to allow the action.
    
    Args:
        body: EvaluateRequest with action context and optional override token
    
    Returns:
        EvaluateActionResponse with decision and valid override tokens
    
    Raises:
        HTTPException 403 if override token is invalid or expired
    
    Example request (no override):
        {
          "action": "start_job",
          "lane": "experimental",
          "fragility_score": 0.8,
          "risk_grade": "RED",
          "job_id": "job_12345"
        }
    
    Example request (with override):
        {
          "action": "start_job",
          "lane": "experimental",
          "fragility_score": 0.8,
          "risk_grade": "RED",
          "job_id": "job_12345",
          "override_token": "OVR-1701345678123456"
        }
    
    Example response (require override):
        {
          "decision": {
            "decision": "require_override",
            "reason": "High-risk action in unrestricted mode; override recommended for fragile / experimental work.",
            "mode": "unrestricted",
            "risk_level": "high",
            "requires_override": true
          },
          "valid_override_tokens": []
        }
    """
    ctx = SafetyActionContext(
        action=body.action,
        lane=body.lane,
        fragility_score=body.fragility_score,
        risk_grade=body.risk_grade,
        preset_id=body.preset_id,
        job_id=body.job_id,
    )

    decision = policy.evaluate_action(ctx)
    valid_tokens: list[OverrideToken] = []

    # If an override token is supplied, attempt to consume it
    if body.override_token:
        ok, msg = policy.consume_override_token(body.override_token, ctx.action)
        if not ok:
            # Override failed; decision stands, but tell caller
            raise HTTPException(status_code=403, detail=msg)
        else:
            # Override succeeded; treat as allow
            decision.decision = "allow"
            decision.requires_override = False
            decision.reason = f"Override accepted: {msg}"

    # You could also list non-used tokens for this action; for now, we skip
    return EvaluateActionResponse(
        decision=decision,
        valid_override_tokens=valid_tokens,
    )


@router.post("/create-override", response_model=OverrideToken)
def create_override(body: CreateOverrideRequest):
    """
    Create a one-time override token for a specific action (mentor only).
    
    NOTE: In production, verify caller has mentor role before allowing.
    
    Args:
        body: CreateOverrideRequest with action, creator, and TTL
    
    Returns:
        OverrideToken with unique token string and metadata
    
    Example request:
        {
          "action": "start_job",
          "created_by": "mentor_alice",
          "ttl_minutes": 15
        }
    
    Example response:
        {
          "token": "OVR-1701345678123456",
          "action": "start_job",
          "created_by": "mentor_alice",
          "created_at": "2025-11-30T10:15:00",
          "expires_at": "2025-11-30T10:30:00",
          "used": false
        }
    """
    # TODO: Add auth check here when auth system is ready
    return policy.create_override_token(
        action=body.action,
        created_by=body.created_by,
        ttl_minutes=body.ttl_minutes,
    )
