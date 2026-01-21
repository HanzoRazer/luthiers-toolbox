"""
Ingest Audit Router - Browse and retrieve ingest events.

Endpoints:
    GET /api/rmos/acoustics/ingest/events       - Browse ingest events
    GET /api/rmos/acoustics/ingest/events/{id}  - Get event detail
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from .store import RunStoreV2
from .ingest_audit import (
    IngestEventSummary,
    list_events_recent,
    get_event,
)


router = APIRouter(tags=["rmos", "acoustics", "ingest-audit"])


# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------


def require_auth() -> None:
    """Placeholder for auth gating."""
    return None


def get_store() -> RunStoreV2:
    """Store accessor for runs_root."""
    return RunStoreV2()


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class IngestEventSummaryOut(BaseModel):
    """Ingest event summary for browse response."""
    event_id: str
    created_at_utc: str
    outcome: str
    session_id: Optional[str] = None
    batch_label: Optional[str] = None
    uploader_filename: Optional[str] = None
    zip_sha256: Optional[str] = None
    zip_size_bytes: Optional[int] = None
    http_status: Optional[int] = None
    run_id: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None


class IngestEventsBrowseOut(BaseModel):
    """Browse ingest events response."""
    schema_version: str = "acoustics_ingest_events_out_v1"
    count: int
    limit: int
    next_cursor: Optional[str] = None
    outcome_filter: Optional[str] = None
    entries: List[IngestEventSummaryOut] = Field(default_factory=list)


class IngestEventErrorOut(BaseModel):
    """Error payload in event detail."""
    code: Optional[str] = None
    message: Optional[str] = None
    detail: Optional[Any] = None


class IngestEventValidationOut(BaseModel):
    """Validation summary in event detail."""
    passed: Optional[bool] = None
    errors_count: Optional[int] = None
    warnings_count: Optional[int] = None
    reason: Optional[str] = None


class IngestEventDetailOut(BaseModel):
    """Full ingest event detail."""
    schema_id: str
    event_id: str
    created_at_utc: str
    outcome: str
    session_id: Optional[str] = None
    batch_label: Optional[str] = None
    uploader_filename: Optional[str] = None
    zip_sha256: Optional[str] = None
    zip_size_bytes: Optional[int] = None
    http_status: Optional[int] = None
    error: Optional[IngestEventErrorOut] = None
    validation: Optional[IngestEventValidationOut] = None
    run_id: Optional[str] = None
    bundle_id: Optional[str] = None
    bundle_sha256: Optional[str] = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/ingest/events", response_model=IngestEventsBrowseOut)
def browse_ingest_events(
    limit: int = Query(
        default=50,
        ge=1,
        le=200,
        description="Max events to return (1..200)"
    ),
    cursor: Optional[str] = Query(
        default=None,
        description="Pagination cursor (event_id from previous response)"
    ),
    outcome: Optional[str] = Query(
        default=None,
        pattern="^(accepted|rejected|quarantined)$",
        description="Filter by outcome (accepted|rejected|quarantined)"
    ),
    _auth: None = Depends(require_auth),
    store: RunStoreV2 = Depends(get_store),
) -> IngestEventsBrowseOut:
    """
    Browse ingest events with pagination.

    Returns newest events first (sorted by created_at_utc DESC).
    Use cursor for pagination (format: event_id).
    """
    result = list_events_recent(
        root=store.root,
        limit=limit,
        cursor=cursor,
        outcome=outcome,
    )

    entries = [
        IngestEventSummaryOut(**e)
        for e in result["entries"]
    ]

    return IngestEventsBrowseOut(
        count=result["count"],
        limit=limit,
        next_cursor=result["next_cursor"],
        outcome_filter=outcome,
        entries=entries,
    )


@router.get("/ingest/events/{event_id}", response_model=IngestEventDetailOut)
def get_ingest_event_detail(
    event_id: str,
    _auth: None = Depends(require_auth),
    store: RunStoreV2 = Depends(get_store),
) -> IngestEventDetailOut:
    """
    Get full ingest event detail by event_id.
    """
    event = get_event(store.root, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail=f"Event not found: {event_id}")

    # Convert nested dicts to Pydantic models
    error_out = None
    if event.get("error"):
        error_out = IngestEventErrorOut(**event["error"])

    validation_out = None
    if event.get("validation"):
        validation_out = IngestEventValidationOut(**event["validation"])

    return IngestEventDetailOut(
        schema_id=event.get("schema_id", "acoustics_ingest_event_v1"),
        event_id=event.get("event_id", event_id),
        created_at_utc=event.get("created_at_utc", ""),
        outcome=event.get("outcome", ""),
        session_id=event.get("session_id"),
        batch_label=event.get("batch_label"),
        uploader_filename=event.get("uploader_filename"),
        zip_sha256=event.get("zip_sha256"),
        zip_size_bytes=event.get("zip_size_bytes"),
        http_status=event.get("http_status"),
        error=error_out,
        validation=validation_out,
        run_id=event.get("run_id"),
        bundle_id=event.get("bundle_id"),
        bundle_sha256=event.get("bundle_sha256"),
    )
