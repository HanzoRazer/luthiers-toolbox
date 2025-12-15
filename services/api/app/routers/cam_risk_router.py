# services/api/app/routers/cam_risk_router.py

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.services.risk_reports_store import (
    create_risk_report,
    latest_risk_by_job_ids,
    list_risk_reports,
)


router = APIRouter(prefix="/api/cam/risk", tags=["cam_risk"])


class RiskReportCreateRequest(BaseModel):
    """Request body for storing a CAM risk report."""

    lane: str = Field(..., description="Lane identifier (e.g. 'rosette')")
    job_id: Optional[str] = Field(
        default=None,
        description="Optional associated job id",
    )
    preset: Optional[str] = Field(
        default=None,
        description="Optional preset id/name (e.g. 'grbl_safe')",
    )
    source: str = Field(
        ..., description="Report source identifier (e.g. 'pipeline_rosette')"
    )
    steps: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Pipeline steps/results to persist",
    )
    summary: Dict[str, Any] = Field(
        default_factory=dict,
        description="Summary metrics (counts, totals, etc.)",
    )
    meta: Dict[str, Any] = Field(
        default_factory=dict,
        description="Optional metadata blob",
    )


class RiskReportCreateResponse(BaseModel):
    """Response returned after creating a risk report."""

    id: str
    lane: str
    job_id: Optional[str]
    preset: Optional[str]
    created_at: float


class RiskReportSummary(BaseModel):
    """Summary of a risk report for listing."""
    id: str
    created_at: float
    lane: str
    job_id: Optional[str] = None
    preset: Optional[str] = None
    source: Optional[str] = None
    summary: Dict[str, Any] = Field(default_factory=dict)


@router.post(
    "/reports",
    response_model=RiskReportCreateResponse,
    description="Create a new CAM risk report"
)
async def create_cam_risk_report(
    req: RiskReportCreateRequest,
) -> RiskReportCreateResponse:
    """Persist a new CAM risk report entry."""

    report = create_risk_report(
        lane=req.lane,
        job_id=req.job_id,
        preset=req.preset,
        source=req.source,
        steps=req.steps,
        summary=req.summary,
        meta=req.meta,
    )

    return RiskReportCreateResponse(
        id=report.id,
        lane=report.lane,
        job_id=report.job_id,
        preset=report.preset,
        created_at=report.created_at,
    )


@router.get(
    "/reports",
    response_model=List[RiskReportSummary],
    description="List CAM risk reports with optional filters"
)
async def list_cam_risk_reports(
    lane: Optional[str] = Query(None, description="Filter by lane"),
    preset: Optional[str] = Query(None, description="Filter by preset"),
    source: Optional[str] = Query(None, description="Filter by source"),
    job_id: Optional[str] = Query(None, description="Filter by job ID"),
    limit: int = Query(200, description="Maximum number of reports to return"),
    start_ts: Optional[float] = Query(
        None,
        description="Return reports created on/after this UNIX timestamp",
    ),
    end_ts: Optional[float] = Query(
        None,
        description="Return reports created on/before this UNIX timestamp",
    ),
) -> List[RiskReportSummary]:
    """List risk reports with optional filters."""
    reports = list_risk_reports(
        lane=lane,
        preset=preset,
        source=source,
        job_id=job_id,
        created_after=start_ts,
        created_before=end_ts,
        limit=limit,
    )
    
    return [
        RiskReportSummary(
            id=r["id"],
            created_at=r["created_at"],
            lane=r["lane"],
            job_id=r.get("job_id"),
            preset=r.get("preset"),
            source=r.get("source"),
            summary=r.get("summary", {})
        )
        for r in reports
    ]


@router.get(
    "/reports_index",
    summary="Batch index: latest risk report per job_id",
)
async def get_latest_risk_index(
    job_ids: List[str] = Query(
        ...,
        description="Repeated query param: job_ids=job1&job_ids=job2",
    ),
):
    latest_map = latest_risk_by_job_ids(job_ids)
    slim: Dict[str, Dict[str, Any]] = {}
    for jid, report in latest_map.items():
        slim[jid] = {
            "id": report.get("id"),
            "created_at": report.get("created_at"),
            "lane": report.get("lane"),
            "preset": report.get("preset"),
            "source": report.get("source"),
            "summary": report.get("summary") or {},
        }
    return slim
