# server/app/api/routes/joblog.py
from __future__ import annotations

from typing import List, Dict

from fastapi import APIRouter, HTTPException

from app.schemas.job_log import JobLogEntry

router = APIRouter(prefix="/joblog", tags=["joblog"])

# Simple in-memory store for now; you can later back this with SQLite/PG.
JOBLOG_DB: Dict[str, JobLogEntry] = {}


@router.get("/", response_model=List[JobLogEntry])
def list_joblogs() -> List[JobLogEntry]:
    """
    Return all job log entries, newest first.
    """
    return sorted(JOBLOG_DB.values(), key=lambda j: j.created_at, reverse=True)


@router.get("/{job_id}", response_model=JobLogEntry)
def get_joblog(job_id: str) -> JobLogEntry:
    """
    Fetch a single job log entry by id.
    """
    job = JOBLOG_DB.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="JobLog entry not found")
    return job


@router.post("/", response_model=JobLogEntry, status_code=201)
def create_joblog(entry: JobLogEntry) -> JobLogEntry:
    """
    Explicit creation endpoint (rare; most logs will be written by internal code).
    """
    if entry.id in JOBLOG_DB:
        raise HTTPException(status_code=400, detail="JobLog id already exists")
    JOBLOG_DB[entry.id] = entry
    return entry
