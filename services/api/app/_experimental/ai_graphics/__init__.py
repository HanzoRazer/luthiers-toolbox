"""
AI Graphics Package

Provides AI-powered parameter suggestion for rosette designs.
Lives in sandbox mode only - does NOT touch geometry or CAM.

Components:
    - schemas/: AI request/response models
    - services/: LLM client, parameter suggester
    - sessions.py: Session memory for deduplication
    - api/: FastAPI routers

Integration:
    - RMOS provides feasibility scoring
    - Art Studio provides RosetteParamSpec
    - AI Graphics suggests parameters, RMOS validates them
"""

from .sessions import (
    AiSessionState,
    AiSuggestionRecord,
    fingerprint_spec,
    get_session,
    get_or_create_session,
    mark_explored,
    is_explored,
    reset_session,
)

__all__ = [
    "AiSessionState",
    "AiSuggestionRecord",
    "fingerprint_spec",
    "get_session",
    "get_or_create_session",
    "mark_explored",
    "is_explored",
    "reset_session",
]
