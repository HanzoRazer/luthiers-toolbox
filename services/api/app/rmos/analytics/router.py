"""RMOS Analytics Router - API endpoints for analytics."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from .service import AnalyticsService


router = APIRouter(prefix="/analytics", tags=["rmos", "analytics"])

# Shared service instance
_service = AnalyticsService()


# =============================================================================
# Response Models
# =============================================================================

class LaneStats(BaseModel):
    """Statistics for a single operation lane."""
    lane: str
    total: int
    ok: int
    blocked: int
    error: int
    green: int
    yellow: int
    red: int


class LaneAnalyticsResponse(BaseModel):
    """Lane-level analytics response."""
    lanes: List[LaneStats]
    total_runs: int
    period_start: str
    period_end: str


class RiskEvent(BaseModel):
    """Single risk event in timeline."""
    run_id: str
    timestamp: Optional[str]
    risk_level: str
    status: str
    mode: Optional[str]
    block_reason: Optional[str]
    warnings_count: int


class RiskTimelineResponse(BaseModel):
    """Risk timeline response."""
    preset_id: str
    events: List[RiskEvent]
    total: int


class SummaryResponse(BaseModel):
    """Aggregate summary statistics."""
    total_runs: int
    by_status: Dict[str, int]
    by_risk_level: Dict[str, int]
    by_mode: Dict[str, int]
    period_start: Optional[str]
    period_end: Optional[str]
    generated_at: str


class TrendBucket(BaseModel):
    """Single trend bucket."""
    date: str
    total: int
    green: int
    yellow: int
    red: int


class TrendsResponse(BaseModel):
    """Trends over time response."""
    trends: List[TrendBucket]
    period_days: int
    bucket_size: str


class ExportResponse(BaseModel):
    """Export analytics response."""
    export_format: str
    generated_at: str
    summary: Dict[str, Any]
    lanes: Dict[str, Any]
    trends: Dict[str, Any]


# =============================================================================
# Endpoints
# =============================================================================

@router.get("/summary", response_model=SummaryResponse)
def get_summary(
    days: int = Query(default=30, ge=1, le=365, description="Number of days to include"),
) -> SummaryResponse:
    """Get aggregate summary statistics for RMOS runs."""
    date_to = datetime.now(timezone.utc)
    date_from = date_to - timedelta(days=days)

    result = _service.get_summary(date_from=date_from, date_to=date_to)
    return SummaryResponse(**result)


@router.get("/lane-analytics", response_model=LaneAnalyticsResponse)
def get_lane_analytics(
    limit_recent: int = Query(default=100, ge=1, le=1000, description="Max recent runs to analyze"),
    days: int = Query(default=30, ge=1, le=365, description="Number of days to include"),
) -> LaneAnalyticsResponse:
    """Get lane-level analytics for RMOS operations."""
    date_to = datetime.now(timezone.utc)
    date_from = date_to - timedelta(days=days)

    result = _service.get_lane_analytics(
        limit_recent=limit_recent,
        date_from=date_from,
        date_to=date_to,
    )
    return LaneAnalyticsResponse(**result)


@router.get("/risk-timeline", response_model=RiskTimelineResponse)
def get_risk_timeline_all(
    limit: int = Query(default=50, ge=1, le=500, description="Max events to return"),
    days: int = Query(default=30, ge=1, le=365, description="Number of days to include"),
) -> RiskTimelineResponse:
    """Get risk timeline events for all presets."""
    date_to = datetime.now(timezone.utc)
    date_from = date_to - timedelta(days=days)

    result = _service.get_risk_timeline(
        preset_id=None,
        limit=limit,
        date_from=date_from,
        date_to=date_to,
    )
    return RiskTimelineResponse(**result)


@router.get("/risk-timeline/{preset_id}", response_model=RiskTimelineResponse)
def get_risk_timeline(
    preset_id: str,
    limit: int = Query(default=50, ge=1, le=500, description="Max events to return"),
    days: int = Query(default=30, ge=1, le=365, description="Number of days to include"),
) -> RiskTimelineResponse:
    """Get risk timeline events for a specific preset."""
    date_to = datetime.now(timezone.utc)
    date_from = date_to - timedelta(days=days)

    result = _service.get_risk_timeline(
        preset_id=preset_id,
        limit=limit,
        date_from=date_from,
        date_to=date_to,
    )
    return RiskTimelineResponse(**result)


@router.get("/trends", response_model=TrendsResponse)
def get_trends(
    days: int = Query(default=30, ge=1, le=365, description="Number of days to trend"),
) -> TrendsResponse:
    """Get trends over time."""
    result = _service.get_trends(days=days)
    return TrendsResponse(**result)


@router.get("/export", response_model=ExportResponse)
def export_analytics(
    format: str = Query(default="json", description="Export format (json)"),
    days: int = Query(default=30, ge=1, le=365, description="Number of days to export"),
) -> ExportResponse:
    """Export analytics data for external tools."""
    date_to = datetime.now(timezone.utc)
    date_from = date_to - timedelta(days=days)

    result = _service.export_analytics(
        format=format,
        date_from=date_from,
        date_to=date_to,
    )
    return ExportResponse(**result)
