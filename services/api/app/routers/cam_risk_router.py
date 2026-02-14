"""
CAM Risk Reports Router

Provides endpoints for risk report storage and timeline browsing.
Stub implementation for Phase 18.0.

Endpoints:
    POST /jobs/risk_report - Submit a new risk report
    GET  /jobs/recent      - Get recent risk report summaries
    GET  /jobs/{job_id}/risk_timeline - Get risk timeline for a job
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, Query
from pydantic import BaseModel


router = APIRouter(prefix="/cam", tags=["cam", "risk"])


# In-memory store for stub
_risk_reports: List[Dict[str, Any]] = []


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
    Submit a new CAM risk report.
    Stub implementation stores in memory.
    """
    report_id = uuid4().hex[:12]
    created_at = datetime.utcnow().isoformat() + "Z"
    
    stored = {
        "id": report_id,
        "created_at": created_at,
        **report.model_dump()
    }
    _risk_reports.append(stored)
    
    # Keep only last 100 reports in memory
    if len(_risk_reports) > 100:
        _risk_reports.pop(0)
    
    return stored


@router.get("/jobs/recent")
def get_recent_risk_reports(
    limit: int = Query(default=100, le=500)
) -> List[Dict[str, Any]]:
    """
    Get recent risk report summaries.
    """
    # Return summaries of recent reports
    summaries = []
    for r in _risk_reports[-limit:]:
        analytics = r.get("analytics", {})
        severity_counts = analytics.get("severity_counts", {})
        summaries.append({
            "id": r.get("id"),
            "created_at": r.get("created_at"),
            "job_id": r.get("job_id"),
            "pipeline_id": r.get("pipeline_id"),
            "op_id": r.get("op_id"),
            "machine_profile_id": r.get("machine_profile_id"),
            "post_preset": r.get("post_preset"),
            "total_issues": analytics.get("total_issues", 0),
            "critical_count": severity_counts.get("critical", 0),
            "high_count": severity_counts.get("high", 0),
            "medium_count": severity_counts.get("medium", 0),
            "low_count": severity_counts.get("low", 0),
            "info_count": severity_counts.get("info", 0),
            "risk_score": analytics.get("risk_score", 0),
            "total_extra_time_s": analytics.get("total_extra_time_s", 0),
        })
    return list(reversed(summaries))


@router.get("/jobs/{job_id}/risk_timeline")
def get_job_risk_timeline(
    job_id: str,
    limit: int = Query(default=50, le=200)
) -> List[Dict[str, Any]]:
    """
    Get risk timeline for a specific job.
    """
    # Filter reports by job_id
    job_reports = [r for r in _risk_reports if r.get("job_id") == job_id]
    return list(reversed(job_reports[-limit:]))


@router.get("/risk/reports")
def get_risk_reports(
    lane: Optional[str] = None,
    preset: Optional[str] = None,
    limit: int = Query(default=100, le=500),
    start_ts: Optional[float] = None,
    end_ts: Optional[float] = None,
) -> List[Dict[str, Any]]:
    """
    Browse risk reports with optional filters.
    """
    results = []
    for r in _risk_reports:
        # Apply filters
        if preset and r.get("post_preset") != preset:
            continue
        # Convert to timeline format
        try:
            created_ts = datetime.fromisoformat(r.get("created_at", "").replace("Z", "+00:00")).timestamp()
        except (ValueError, AttributeError):
            created_ts = 0
        
        if start_ts and created_ts < start_ts:
            continue
        if end_ts and created_ts > end_ts:
            continue
            
        results.append({
            "id": r.get("id"),
            "created_at": created_ts,
            "lane": lane or "default",
            "job_id": r.get("job_id"),
            "preset": r.get("post_preset"),
            "source": r.get("design_source"),
            "summary": r.get("analytics", {}),
        })
    
    return list(reversed(results[-limit:]))
