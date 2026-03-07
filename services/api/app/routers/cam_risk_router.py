"""
CAM Risk Reports Router

Provides endpoints for risk report storage and timeline browsing.
WIRED to persistent JSONL storage (risk_reports_store).

Endpoints:
    POST /jobs/risk_report - Submit a new risk report (persisted to JSONL)
    GET  /jobs/recent      - Get recent risk report summaries
    GET  /jobs/{job_id}/risk_timeline - Get risk timeline for a job
    GET  /risk/reports     - Browse reports with filters
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel


router = APIRouter(prefix="/cam", tags=["cam", "risk"])

from app.services.risk_reports_store import (
    append_risk_report,
    get_recent_reports,
    get_reports_by_job_id,
    browse_reports,
)


class RiskIssue(BaseModel):
    index: int
    type: str
    severity: str
    x: float
    y: float
    z: Optional[float] = None
    extra_time_s: Optional[float] = None
    note: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None


class RiskAnalytics(BaseModel):
    total_issues: int
    severity_counts: Dict[str, int]
    risk_score: float
    total_extra_time_s: float
    total_extra_time_human: str


class RiskReportIn(BaseModel):
    job_id: str
    pipeline_id: Optional[str] = None
    op_id: Optional[str] = None
    machine_profile_id: Optional[str] = None
    post_preset: Optional[str] = None
    design_source: Optional[str] = None
    design_path: Optional[str] = None
    issues: List[RiskIssue] = []
    analytics: RiskAnalytics


@router.post("/jobs/risk_report")
def submit_risk_report(report: RiskReportIn) -> Dict[str, Any]:
    """
    Submit a new CAM risk report (wired to persistent JSONL storage).
    """
    stored = append_risk_report(
        job_id=report.job_id,
        pipeline_id=report.pipeline_id,
        op_id=report.op_id,
        machine_profile_id=report.machine_profile_id,
        post_preset=report.post_preset,
        design_source=report.design_source,
        design_path=report.design_path,
        issues=[i.model_dump() for i in report.issues],
        analytics=report.analytics.model_dump(),
    )
    return stored


@router.get("/jobs/recent")
def get_recent_risk_reports(
    limit: int = Query(default=100, le=500)
) -> List[Dict[str, Any]]:
    """
    Get recent risk report summaries (from persistent JSONL storage).
    """
    return get_recent_reports(limit=limit)


@router.get("/jobs/{job_id}/risk_timeline")
def get_job_risk_timeline(
    job_id: str,
    limit: int = Query(default=50, le=200)
) -> List[Dict[str, Any]]:
    """
    Get risk timeline for a specific job (from persistent JSONL storage).
    """
    return get_reports_by_job_id(job_id=job_id, limit=limit)


@router.get("/risk/reports")
def get_risk_reports(
    lane: Optional[str] = None,
    preset: Optional[str] = None,
    limit: int = Query(default=100, le=500),
    start_ts: Optional[float] = None,
    end_ts: Optional[float] = None,
) -> List[Dict[str, Any]]:
    """
    Browse risk reports with optional filters (from persistent JSONL storage).
    """
    return browse_reports(
        lane=lane,
        preset=preset,
        start_ts=start_ts,
        end_ts=end_ts,
        limit=limit,
    )
