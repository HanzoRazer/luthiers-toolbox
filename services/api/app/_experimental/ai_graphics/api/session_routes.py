"""
AI Graphics Session Routes - Session Management Endpoints

Provides:
- GET /api/ai/graphics/session/summary: Get session exploration summary
- POST /api/ai/graphics/session/reset: Reset/clear a session
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional

from ..sessions import get_session, reset_session
from ..schemas.ai_schemas import RiskBucket


router = APIRouter(
    prefix="/api/ai/graphics/session",
    tags=["ai_graphics_session"],
)


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class AiSuggestionSummaryModel(BaseModel):
    """Summary of a single suggestion in session history."""
    suggestion_id: str
    overall_score: float
    risk_bucket: Optional[RiskBucket] = None
    worst_ring_risk: Optional[RiskBucket] = None
    created_at: str


class AiSessionSummaryResponse(BaseModel):
    """Session summary response."""
    session_id: str
    explored_count: int = Field(..., description="Number of unique designs explored")
    suggestion_history: List[AiSuggestionSummaryModel] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/summary", response_model=AiSessionSummaryResponse)
async def get_session_summary(
    session_id: str = Query(..., description="Logical AI exploration session ID"),
) -> AiSessionSummaryResponse:
    """
    Get summary of an AI exploration session.
    
    Returns:
    - Number of unique designs explored
    - History of suggestions with scores and risk levels
    """
    state = get_session(session_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return AiSessionSummaryResponse(
        session_id=session_id,
        explored_count=len(state.explored_fingerprints),
        suggestion_history=[
            AiSuggestionSummaryModel(
                suggestion_id=s.suggestion_id,
                overall_score=s.overall_score,
                risk_bucket=s.risk_bucket,
                worst_ring_risk=s.worst_ring_risk,
                created_at=s.created_at.isoformat(),
            )
            for s in state.history
        ],
    )


@router.post("/reset")
async def reset_ai_session(
    session_id: str = Query(..., description="Session ID to reset/clear"),
) -> dict:
    """
    Reset/clear an AI exploration session.
    
    Removes all explored fingerprints and history for the session.
    The next AI request with this session_id will start fresh.
    """
    reset_session(session_id)
    return {"ok": True, "session_id": session_id}
