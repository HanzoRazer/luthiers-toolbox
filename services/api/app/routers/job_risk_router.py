# services/api/app/routers/job_risk_router.py
"""
Job Risk Router - Phase 18.0 + Phase 26.29

Endpoints for CAM risk reporting, timeline browsing, and pipeline job linking.
"""
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional
import json

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..schemas.cam_risk import RiskReportIn, RiskReportOut, RiskReportSummary
from ..services.job_risk_store import get_risk_store

router = APIRouter(prefix="/cam/jobs", tags=["cam", "jobs", "risk"])

# Phase 26.29: Job attachment storage
JOB_RECORDS_DIR = Path("data/job_records")
JOB_RECORDS_FILE = JOB_RECORDS_DIR / "jobs.json"


def _ensure_job_records_dir() -> None:
    """Create job records directory on first write (Docker compatibility)."""
    JOB_RECORDS_DIR.mkdir(parents=True, exist_ok=True)


class PipelineJobAttachIn(BaseModel):
    """Phase 26.29: Attach pipeline run to job record"""
    job_id: str
    preset_key: Optional[str] = None
    adaptive_stats: Optional[dict] = None
    post_stats: Optional[dict] = None
    sim_stats: Optional[dict] = None
    pipeline_spec: Optional[dict] = None


class JobRecordOut(BaseModel):
    """Phase 26.29: Job record with linked pipeline runs"""
    job_id: str
    created_at: str
    notes: List[Any] = []
    risk_snapshots: List[Any] = []
    linked_pipeline_runs: List[Any] = []
    last_pipeline_spec: Optional[dict] = None


def _load_job_records() -> dict:
    """Load job records from JSON file"""
    if not JOB_RECORDS_FILE.exists():
        return {}
    try:
        with open(JOB_RECORDS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def _save_job_records(jobs: dict) -> None:
    """Save job records to JSON file"""
    _ensure_job_records_dir()  # Create directory on first write
    with open(JOB_RECORDS_FILE, 'w', encoding='utf-8') as f:
        json.dump(jobs, f, indent=2)


def _now_ts() -> str:
    """Current timestamp as ISO string"""
    return datetime.now().isoformat()


@router.post("/risk_report", response_model=RiskReportOut)
def post_risk_report(report: RiskReportIn) -> RiskReportOut:
    """
    Submit a new CAM risk report.
    
    Called after simulation to log risk analytics:
    - Issue counts by severity
    - Risk score calculation
    - Extra time estimates
    - Machine/post/pipeline context
    
    Returns the saved report with ID and timestamp.
    """
    store = get_risk_store()
    return store.save(report)


@router.get("/{job_id}/risk_timeline", response_model=List[RiskReportOut])
def get_job_risk_timeline(
    job_id: str,
    limit: int = Query(50, ge=1, le=500, description="Max reports to return")
) -> List[RiskReportOut]:
    """
    Get risk timeline for a specific job.
    
    Returns all risk reports for the given job_id,
    sorted by created_at (newest first).
    
    Use this to see how risk metrics evolved across
    multiple simulation runs of the same job.
    """
    store = get_risk_store()
    return store.get_timeline(job_id, limit=limit)


@router.get("/recent", response_model=List[RiskReportSummary])
def get_recent_risk_reports(
    limit: int = Query(100, ge=1, le=500, description="Max reports to return")
) -> List[RiskReportSummary]:
    """
    Get recent risk reports across all jobs.
    
    Returns lightweight summaries sorted by created_at (newest first).
    
    Use this for the Risk Timeline Lab dashboard to browse
    all recent simulation runs and their risk analytics.
    """
    store = get_risk_store()
    return store.get_recent(limit=limit)


@router.post("/attach", response_model=JobRecordOut)
def attach_pipeline_job(payload: PipelineJobAttachIn) -> JobRecordOut:
    """
    Phase 26.29: Attach a pipeline run to a job record.
    
    Creates the job if it doesn't exist.
    Stores adaptive/post/sim stats and optional pipeline spec.
    Enables manufacturing history tracking and job iteration.
    """
    job_id = payload.job_id
    jobs = _load_job_records()
    
    # Create job record if it doesn't exist
    if job_id not in jobs:
        jobs[job_id] = {
            "job_id": job_id,
            "created_at": _now_ts(),
            "notes": [],
            "risk_snapshots": [],
            "linked_pipeline_runs": [],
            "last_pipeline_spec": None,
        }
    
    # Append pipeline run data
    jobs[job_id]["linked_pipeline_runs"].append({
        "ts": _now_ts(),
        "adaptive": payload.adaptive_stats,
        "post": payload.post_stats,
        "simulate": payload.sim_stats,
        "preset": payload.preset_key,
    })
    
    # Update last pipeline spec if provided
    if payload.pipeline_spec:
        jobs[job_id]["last_pipeline_spec"] = payload.pipeline_spec
    
    _save_job_records(jobs)
    return JobRecordOut(**jobs[job_id])


@router.get("/records/{job_id}", response_model=JobRecordOut)
def get_job_record(job_id: str) -> JobRecordOut:
    """
    Phase 26.29: Get full job record including linked pipeline runs.
    """
    jobs = _load_job_records()
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return JobRecordOut(**jobs[job_id])
