"""
AI Graphics Sessions - Session Memory with Fingerprint Deduplication

Provides:
- Session state management for AI exploration
- Fingerprint-based deduplication to avoid repeating designs
- History tracking for session summary/inspection

Usage:
    session = get_or_create_session("user-session-123")
    
    # Check if design already explored
    fp = fingerprint_spec(spec)
    if is_explored(session.session_id, fp):
        skip_this_design()
    
    # Mark as explored
    mark_explored(session.session_id, [fp])
"""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple

from pydantic import BaseModel, Field

from .schemas.ai_schemas import RiskBucket


# ---------------------------------------------------------------------------
# Session state models
# ---------------------------------------------------------------------------

class AiSuggestionRecord(BaseModel):
    """
    Record of a single AI suggestion within a session.
    Used for history tracking and session summary.
    """
    suggestion_id: str
    overall_score: float
    risk_bucket: Optional[RiskBucket] = None
    worst_ring_risk: Optional[RiskBucket] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AiSessionState(BaseModel):
    """
    In-memory state for an AI exploration session.
    
    Tracks:
    - explored_fingerprints: Set of design fingerprints already seen
    - history: List of suggestion records for inspection
    """
    session_id: str
    explored_fingerprints: Set[Tuple[float, float, Tuple[float, ...]]] = Field(default_factory=set)
    history: List[AiSuggestionRecord] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        arbitrary_types_allowed = True


# ---------------------------------------------------------------------------
# In-memory session store
# ---------------------------------------------------------------------------

_sessions: Dict[str, AiSessionState] = {}


def get_session(session_id: str) -> Optional[AiSessionState]:
    """Get existing session by ID, or None if not found."""
    return _sessions.get(session_id)


def get_or_create_session(session_id: str) -> AiSessionState:
    """Get existing session or create a new one."""
    if session_id not in _sessions:
        _sessions[session_id] = AiSessionState(session_id=session_id)
    return _sessions[session_id]


def reset_session(session_id: str) -> None:
    """Reset/clear a session, removing all explored fingerprints and history."""
    if session_id in _sessions:
        del _sessions[session_id]


# ---------------------------------------------------------------------------
# Fingerprinting
# ---------------------------------------------------------------------------

def fingerprint_spec(spec) -> Tuple[float, float, Tuple[float, ...]]:
    """
    Create a compact fingerprint for a RosetteParamSpec.
    
    Fingerprint: (outer_diameter, inner_diameter, tuple_of_ring_widths)
    
    This allows deduplication of "essentially same" designs even if
    other metadata differs.
    """
    outer = float(getattr(spec, "outer_diameter_mm", 0.0) or 0.0)
    inner = float(getattr(spec, "inner_diameter_mm", 0.0) or 0.0)
    
    ring_params = getattr(spec, "ring_params", []) or []
    ring_widths = tuple(
        float(getattr(rp, "width_mm", 0.0) or 0.0)
        for rp in ring_params
    )
    
    return (outer, inner, ring_widths)


# ---------------------------------------------------------------------------
# Exploration tracking
# ---------------------------------------------------------------------------

def mark_explored(
    session_id: str,
    fingerprints: List[Tuple[float, float, Tuple[float, ...]]],
) -> None:
    """Mark a list of design fingerprints as explored in the session."""
    session = get_or_create_session(session_id)
    session.explored_fingerprints.update(fingerprints)


def is_explored(
    session_id: str,
    fingerprint: Tuple[float, float, Tuple[float, ...]],
) -> bool:
    """Check if a fingerprint has already been explored in the session."""
    session = get_session(session_id)
    if session is None:
        return False
    return fingerprint in session.explored_fingerprints


def add_suggestion_to_history(
    session_id: str,
    suggestion_id: str,
    overall_score: float,
    risk_bucket: Optional[RiskBucket] = None,
    worst_ring_risk: Optional[RiskBucket] = None,
) -> None:
    """Add a suggestion record to session history."""
    session = get_or_create_session(session_id)
    session.history.append(
        AiSuggestionRecord(
            suggestion_id=suggestion_id,
            overall_score=overall_score,
            risk_bucket=risk_bucket,
            worst_ring_risk=worst_ring_risk,
        )
    )
