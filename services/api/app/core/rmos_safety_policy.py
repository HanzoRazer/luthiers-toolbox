"""
RMOS N10.2: Safety policy engine for apprenticeship mode.

This module implements the core safety policy logic:
- Risk classification based on lane, fragility, and action type
- Mode-based decision making (unrestricted, apprentice, mentor_review)
- Override token generation and validation
- In-memory state management (replace with DB later)
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, Any, Tuple, List

from ..schemas.rmos_safety import (
    SafetyMode,
    SafetyModeState,
    SafetyActionContext,
    SafetyDecision,
    ActionRiskLevel,
    ActionDecision,
    OverrideToken,
)


# In-memory state management (replace with DB in production)
# For now we assume a simple file-backed state or singleton pattern
_safety_mode_state: SafetyModeState | None = None
_override_tokens: Dict[str, OverrideToken] = {}


def get_safety_mode() -> SafetyModeState:
    """Get current safety mode state, initializing if needed."""
    global _safety_mode_state
    if _safety_mode_state is None:
        _safety_mode_state = SafetyModeState(
            mode="unrestricted",
            set_by=None,
            set_at=datetime.utcnow().isoformat(),
        )
    return _safety_mode_state


def set_safety_mode(mode: SafetyMode, set_by: str | None = None) -> SafetyModeState:
    """
    Set safety mode with metadata.
    
    NOTE: In production, check that caller is a mentor/admin before allowing.
    """
    global _safety_mode_state
    _safety_mode_state = SafetyModeState(
        mode=mode,
        set_by=set_by,
        set_at=datetime.utcnow().isoformat(),
    )
    return _safety_mode_state


def _classify_risk(ctx: SafetyActionContext) -> ActionRiskLevel:
    """
    Classify action risk based on lane, fragility score, and risk grade.
    
    Rules:
    - Experimental lanes with high fragility (≥0.7) or RED grade → high risk
    - Experimental lanes otherwise → medium risk
    - Tuned_v1 with moderate fragility (≥0.6) or YELLOW grade → medium risk
    - Default → low risk
    
    You can tighten these rules over time based on operational data.
    """
    lane = (ctx.lane or "").lower()
    frag = ctx.fragility_score or 0.0
    grade = (ctx.risk_grade or "").upper()

    # High-risk: experimental lane or very fragile
    if lane in ("experimental", "tuned_v2"):
        if frag >= 0.7 or grade == "RED":
            return "high"
        return "medium"

    # Medium risk: tuned_v1 with moderate fragility
    if lane == "tuned_v1":
        if frag >= 0.6 or grade == "YELLOW":
            return "medium"

    # Default: low risk
    return "low"


def evaluate_action(ctx: SafetyActionContext) -> SafetyDecision:
    """
    Evaluate whether an action should be allowed, require override, or be denied.
    
    Mode-specific rules:
    
    Unrestricted:
    - High-risk actions (start_job, promote_preset) require override
    - Everything else allowed
    
    Mentor Review:
    - High-risk actions require override
    - Medium/low risk allowed but logged
    
    Apprentice:
    - High-risk actions denied (mentor must perform)
    - Medium-risk actions require override
    - Low-risk actions allowed
    """
    mode_state = get_safety_mode()
    mode = mode_state.mode
    risk = _classify_risk(ctx)

    # Default decision
    decision: ActionDecision = "allow"
    reason = "Default allow in unrestricted mode."
    requires_override = False

    # Mode-specific rules
    if mode == "unrestricted":
        # Only require override for extremely high risk cases
        if risk == "high" and ctx.action in ("start_job", "promote_preset"):
            decision = "require_override"
            requires_override = True
            reason = (
                "High-risk action in unrestricted mode; override recommended "
                "for fragile / experimental work."
            )

    elif mode == "mentor_review":
        if risk == "high" and ctx.action in ("start_job", "promote_preset", "run_experimental_lane"):
            decision = "require_override"
            requires_override = True
            reason = (
                "High-risk action under mentor_review mode; mentor override required."
            )
        else:
            decision = "allow"
            reason = "Allowed under mentor_review; action will be logged."

    elif mode == "apprentice":
        # Apprentices are constrained
        if risk == "high" and ctx.action in ("start_job", "promote_preset", "run_experimental_lane"):
            decision = "deny"
            requires_override = False
            reason = (
                "High-risk action denied in apprentice mode; mentor must run this."
            )
        elif risk == "medium" and ctx.action in ("start_job", "promote_preset"):
            decision = "require_override"
            requires_override = True
            reason = (
                "Medium-risk action in apprentice mode; mentor override required."
            )
        else:
            decision = "allow"
            reason = "Low-risk action allowed in apprentice mode."

    return SafetyDecision(
        decision=decision,
        reason=reason,
        mode=mode,
        risk_level=risk,
        requires_override=requires_override,
    )


def create_override_token(action: str, created_by: str | None = None, ttl_minutes: int = 15) -> OverrideToken:
    """
    Create a one-time override token for a specific action.
    
    Args:
        action: Action name the token authorizes (e.g. "start_job")
        created_by: Optional mentor identifier
        ttl_minutes: Token validity period (default 15 minutes)
    
    Returns:
        OverrideToken with unique token string and metadata
    """
    token = f"OVR-{datetime.utcnow().timestamp():.6f}".replace(".", "")
    now = datetime.utcnow()
    exp = now + timedelta(minutes=ttl_minutes)
    ov = OverrideToken(
        token=token,
        action=action,
        created_by=created_by,
        created_at=now.isoformat(),
        expires_at=exp.isoformat(),
        used=False,
    )
    _override_tokens[token] = ov
    return ov


def consume_override_token(token: str, action: str) -> Tuple[bool, str]:
    """
    Mark a token as used if valid; return (ok, reason).
    
    Validates:
    - Token exists
    - Token not already used
    - Token matches action
    - Token not expired
    
    Returns:
        (True, "Override accepted.") on success
        (False, reason) on failure
    """
    ov = _override_tokens.get(token)
    if not ov:
        return False, "Invalid override token."
    if ov.used:
        return False, "Override token already used."
    if ov.action != action:
        return False, f"Override token is not valid for action '{action}'."

    # Expiry check
    if ov.expires_at:
        try:
            exp = datetime.fromisoformat(ov.expires_at)
            if datetime.utcnow() > exp:
                return False, "Override token has expired."
        except Exception:
            pass

    ov.used = True
    _override_tokens[token] = ov
    return True, "Override accepted."
