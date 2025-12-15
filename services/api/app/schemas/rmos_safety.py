"""
RMOS N10.2: Safety schemas for apprenticeship mode and safety overrides.

This module defines the core types and models for the safety policy system:
- Safety modes (unrestricted, apprentice, mentor_review)
- Risk levels (low, medium, high)
- Action decisions (allow, require_override, deny)
- Override tokens for mentor approval
"""

from __future__ import annotations

from typing import Literal, List, Dict, Any
from pydantic import BaseModel


SafetyMode = Literal[
    "unrestricted",   # normal production - full capabilities enabled
    "apprentice",     # restricted - risky actions blocked or require override
    "mentor_review",  # mentor supervising - apprentices allowed but logged
]

ActionRiskLevel = Literal[
    "low",    # safe operations (view, query, low-fragility work)
    "medium", # moderate risk (tuned lanes, moderate fragility)
    "high",   # dangerous (experimental lanes, high fragility, production changes)
]

ActionDecision = Literal[
    "allow",            # action permitted without override
    "require_override", # action needs mentor override token
    "deny",            # action blocked entirely (mentor must perform)
]


class SafetyModeState(BaseModel):
    """Current safety mode state with metadata."""
    mode: SafetyMode
    # who set it, optional (for auth integration later)
    set_by: str | None = None
    # ISO timestamp when mode was set
    set_at: str | None = None


class SafetyActionContext(BaseModel):
    """
    Minimal context needed to evaluate a safety decision.
    Extensible for future features (operator_id, router_id, etc.).
    """
    action: str  # e.g. "start_job", "promote_preset", "run_experimental_lane"
    lane: str | None = None
    fragility_score: float | None = None
    risk_grade: str | None = None  # "GREEN", "YELLOW", "RED"
    preset_id: str | None = None
    job_id: str | None = None


class SafetyDecision(BaseModel):
    """Result of evaluating an action against current safety policy."""
    decision: ActionDecision
    reason: str
    mode: SafetyMode
    risk_level: ActionRiskLevel
    requires_override: bool = False


class OverrideToken(BaseModel):
    """One-time token for mentor approval of risky actions."""
    token: str
    action: str
    created_by: str | None = None
    created_at: str
    expires_at: str | None = None
    used: bool = False


class EvaluateActionResponse(BaseModel):
    """Response from action evaluation endpoint."""
    decision: SafetyDecision
    valid_override_tokens: List[OverrideToken] = []
