"""
Agentic API Router - REST endpoints for agentic features.

Endpoints:
- POST /api/agentic/events - Submit events for processing
- POST /api/agentic/replay - Replay events from JSONL
- GET /api/agentic/status - Check agentic system status
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .spine import (
    detect_moments,
    decide,
    group_by_session,
    DetectedMoment,
    PolicyDecision,
    UWSMSnapshot,
    DEFAULT_UWSM,
    IMPLEMENTED,
)

router = APIRouter(prefix="/api/agentic", tags=["Agentic"])


class EventsRequest(BaseModel):
    """Request body for event processing."""
    events: List[Dict[str, Any]]
    uwsm: Optional[UWSMSnapshot] = None
    mode: str = "M1"


class EventsResponse(BaseModel):
    """Response from event processing."""
    ok: bool
    moments: List[DetectedMoment]
    decision: Optional[PolicyDecision] = None
    error: Optional[str] = None


class StatusResponse(BaseModel):
    """Agentic system status."""
    ok: bool
    implemented: bool
    version: str
    mode: str


@router.get("/status", response_model=StatusResponse)
async def get_status():
    """
    Get agentic system status.

    Returns implementation status and version info.
    """
    return StatusResponse(
        ok=True,
        implemented=IMPLEMENTED,
        version="1.0.0",
        mode="M1",
    )


@router.post("/events", response_model=EventsResponse)
async def process_events(request: EventsRequest):
    """
    Process events and generate directives.

    Accepts a list of AgentEventV1 events and returns:
    - Detected moments
    - Policy decision (if any directive should be shown)
    """
    try:
        moments = detect_moments(request.events)

        decision = None
        if moments:
            uwsm = request.uwsm or DEFAULT_UWSM
            decision = decide(moments[0], uwsm=uwsm, mode=request.mode)  # type: ignore

        return EventsResponse(
            ok=True,
            moments=moments,
            decision=decision,
        )
    except Exception as e:  # audited: agent-pipeline
        return EventsResponse(
            ok=False,
            moments=[],
            error=str(e),
        )


class ReplayRequest(BaseModel):
    """Request body for replay."""
    events: List[Dict[str, Any]]


class SessionResult(BaseModel):
    """Result for a single session."""
    session_id: str
    event_count: int
    moments: List[DetectedMoment]


class ReplayResponse(BaseModel):
    """Response from replay."""
    ok: bool
    sessions: List[SessionResult]
    total_events: int
    total_sessions: int
    error: Optional[str] = None


@router.post("/replay", response_model=ReplayResponse)
async def replay_events(request: ReplayRequest):
    """
    Replay events and analyze sessions.

    Groups events by session and runs moment detection on each.
    Useful for testing and analyzing user workflows.
    """
    try:
        sessions = group_by_session(request.events)
        results: List[SessionResult] = []

        for session_id, session_events in sessions.items():
            moments = detect_moments(session_events)
            results.append(
                SessionResult(
                    session_id=session_id,
                    event_count=len(session_events),
                    moments=moments,
                )
            )

        return ReplayResponse(
            ok=True,
            sessions=results,
            total_events=len(request.events),
            total_sessions=len(sessions),
        )
    except Exception as e:  # audited: agent-pipeline
        return ReplayResponse(
            ok=False,
            sessions=[],
            total_events=0,
            total_sessions=0,
            error=str(e),
        )
