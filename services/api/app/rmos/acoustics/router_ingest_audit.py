"""
Router for Ingest Audit Events.

Provides API endpoints for the "Ingest Events" UI panel:
- List events with filtering
- Get single event details
- Get outcome counts/summary
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from .ingest_audit import (
    query_ingest_events,
    get_ingest_event,
    count_ingest_events,
    IngestOutcome,
)

router = APIRouter(tags=["acoustics", "ingest-audit"])


class IngestEventSummary(BaseModel):
    """Summary view of an ingest event for list display."""
    event_id: str
    timestamp: str
    outcome: str
    session_id: Optional[str] = None
    batch_label: Optional[str] = None
    filename: Optional[str] = None
    bundle_sha256: Optional[str] = None
    rejection_reason: Optional[str] = None
    run_id: Optional[str] = None


class IngestEventDetail(BaseModel):
    """Full details of an ingest event."""
    event_id: str
    timestamp: str
    outcome: str
    
    # Request context
    session_id: Optional[str] = None
    batch_label: Optional[str] = None
    filename: Optional[str] = None
    
    # Bundle identity
    bundle_sha256: Optional[str] = None
    bundle_id: Optional[str] = None
    manifest_event_type: Optional[str] = None
    manifest_tool_id: Optional[str] = None
    
    # Rejection/error details
    rejection_reason: Optional[str] = None
    rejection_message: Optional[str] = None
    errors_count: Optional[int] = None
    warnings_count: Optional[int] = None
    error_excerpt: List[str] = Field(default_factory=list)
    
    # Success details
    run_id: Optional[str] = None
    attachments_written: Optional[int] = None
    attachments_deduped: Optional[int] = None
    
    # Metadata
    request_id: Optional[str] = None
    client_ip: Optional[str] = None
    bundle_size_bytes: Optional[int] = None


class IngestEventsListResponse(BaseModel):
    """Response for listing ingest events."""
    events: List[IngestEventSummary]
    total_returned: int
    limit: int
    offset: int


class IngestEventCountsResponse(BaseModel):
    """Response for ingest event counts."""
    accepted: int
    rejected: int
    quarantined: int
    error: int
    total: int


@router.get("/ingest-events", response_model=IngestEventsListResponse)
def list_ingest_events(
    outcome: Optional[str] = Query(
        default=None,
        description="Filter by outcome: accepted, rejected, quarantined, error"
    ),
    session_id: Optional[str] = Query(default=None, description="Filter by session ID"),
    batch_label: Optional[str] = Query(default=None, description="Filter by batch label"),
    since: Optional[str] = Query(
        default=None,
        description="Filter events after this ISO 8601 timestamp"
    ),
    until: Optional[str] = Query(
        default=None,
        description="Filter events before this ISO 8601 timestamp"
    ),
    limit: int = Query(default=100, ge=1, le=1000, description="Max events to return"),
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
) -> IngestEventsListResponse:
    """
    List ingest audit events with optional filtering.
    
    Returns events in reverse chronological order (newest first).
    Use for the "Ingest Events" UI panel.
    """
    # Validate outcome if provided
    if outcome and outcome not in [e.value for e in IngestOutcome]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid outcome. Must be one of: {[e.value for e in IngestOutcome]}"
        )
    
    events = query_ingest_events(
        outcome=outcome,
        session_id=session_id,
        batch_label=batch_label,
        since=since,
        until=until,
        limit=limit,
        offset=offset,
    )
    
    summaries = [
        IngestEventSummary(
            event_id=e.get("event_id", ""),
            timestamp=e.get("timestamp", ""),
            outcome=e.get("outcome", "error"),
            session_id=e.get("session_id"),
            batch_label=e.get("batch_label"),
            filename=e.get("filename"),
            bundle_sha256=e.get("bundle_sha256"),
            rejection_reason=e.get("rejection_reason"),
            run_id=e.get("run_id"),
        )
        for e in events
    ]
    
    return IngestEventsListResponse(
        events=summaries,
        total_returned=len(summaries),
        limit=limit,
        offset=offset,
    )


@router.get("/ingest-events/counts", response_model=IngestEventCountsResponse)
def get_ingest_event_counts(
    since: Optional[str] = Query(
        default=None,
        description="Count events after this ISO 8601 timestamp"
    ),
) -> IngestEventCountsResponse:
    """
    Get counts of ingest events by outcome.
    
    Useful for dashboard summary widgets.
    """
    counts = count_ingest_events(since=since)
    return IngestEventCountsResponse(**counts)


@router.get("/ingest-events/{event_id}", response_model=IngestEventDetail)
def get_ingest_event_detail(event_id: str) -> IngestEventDetail:
    """
    Get full details of a single ingest event.
    
    Use for the detail view when clicking on an event in the list.
    """
    event = get_ingest_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail=f"Ingest event not found: {event_id}")
    
    return IngestEventDetail(
        event_id=event.get("event_id", ""),
        timestamp=event.get("timestamp", ""),
        outcome=event.get("outcome", "error"),
        session_id=event.get("session_id"),
        batch_label=event.get("batch_label"),
        filename=event.get("filename"),
        bundle_sha256=event.get("bundle_sha256"),
        bundle_id=event.get("bundle_id"),
        manifest_event_type=event.get("manifest_event_type"),
        manifest_tool_id=event.get("manifest_tool_id"),
        rejection_reason=event.get("rejection_reason"),
        rejection_message=event.get("rejection_message"),
        errors_count=event.get("errors_count"),
        warnings_count=event.get("warnings_count"),
        error_excerpt=event.get("error_excerpt", []),
        run_id=event.get("run_id"),
        attachments_written=event.get("attachments_written"),
        attachments_deduped=event.get("attachments_deduped"),
        request_id=event.get("request_id"),
        client_ip=event.get("client_ip"),
        bundle_size_bytes=event.get("bundle_size_bytes"),
    )
