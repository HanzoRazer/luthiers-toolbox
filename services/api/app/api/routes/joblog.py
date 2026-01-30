# server/app/api/routes/joblog.py
"""
Job Log API Router.

Provides REST endpoints for production run tracking.
Wired to SQLite store for persistent storage.
"""
from __future__ import annotations

from typing import List, Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Query

from app.api.deps.rmos_stores import get_joblog_store
from app.schemas.job_log import JobLogEntry

router = APIRouter(prefix="/joblog", tags=["joblog"])


def _entry_to_store_dict(entry: JobLogEntry) -> Dict[str, Any]:
    """Convert Pydantic JobLogEntry to store dictionary format."""
    data = entry.model_dump()
    # Map schema fields to store fields
    return {
        "id": data["id"],
        "job_type": data["job_type"],
        "pattern_id": data.get("pipeline_id"),
        "status": "completed",  # Default status
        "parameters": {
            "pipeline_id": data.get("pipeline_id"),
            "node_id": data.get("node_id"),
            **data.get("extra", {}),
        },
        "results": data,  # Store full entry as results
    }


def _store_dict_to_entry(data: Dict[str, Any]) -> Dict[str, Any]:
    """Convert store dictionary to response format."""
    results = data.get("results", {})
    return {
        "id": data["id"],
        "job_type": data.get("job_type", "unknown"),
        "created_at": data.get("created_at"),
        "pipeline_id": data.get("pattern_id"),
        "status": data.get("status"),
        "parameters": data.get("parameters"),
        "results": results,
        "duration_seconds": data.get("duration_seconds"),
    }


@router.get("/", response_model=List[Dict[str, Any]])
def list_joblogs(
    limit: int = Query(50, ge=1, le=500),
    status: Optional[str] = Query(None, description="Filter by status"),
    job_type: Optional[str] = Query(None, description="Filter by job type"),
) -> List[Dict[str, Any]]:
    """
    Return all job log entries, newest first.

    Supports filtering by status and job_type.
    """
    store = get_joblog_store()

    if status:
        jobs = store.get_by_status(status, limit=limit)
    elif job_type:
        jobs = store.get_by_job_type(job_type, limit=limit)
    else:
        jobs = store.get_recent(limit=limit)

    return [_store_dict_to_entry(j) for j in jobs]


@router.get("/statistics", response_model=Dict[str, Any])
def get_statistics() -> Dict[str, Any]:
    """
    Get job log statistics.

    Returns counts, success rate, and averages.
    """
    store = get_joblog_store()
    return store.get_statistics()


@router.get("/{job_id}", response_model=Dict[str, Any])
def get_joblog(job_id: str) -> Dict[str, Any]:
    """
    Fetch a single job log entry by id.
    """
    store = get_joblog_store()
    job = store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="JobLog entry not found")
    return _store_dict_to_entry(job)


@router.post("/", response_model=Dict[str, Any], status_code=201)
def create_joblog(entry: JobLogEntry) -> Dict[str, Any]:
    """
    Create a new job log entry.
    """
    store = get_joblog_store()

    # Check if exists
    existing = store.get_job(entry.id)
    if existing:
        raise HTTPException(status_code=400, detail="JobLog id already exists")

    # Convert and create
    store_data = _entry_to_store_dict(entry)
    created = store.create(store_data)
    return _store_dict_to_entry(created)


@router.patch("/{job_id}/status", response_model=Dict[str, Any])
def update_joblog_status(
    job_id: str,
    status: str = Query(..., description="New status"),
    results: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Update job status and optionally add results.
    """
    store = get_joblog_store()

    updated = store.update_status(job_id, status, results=results)
    if not updated:
        raise HTTPException(status_code=404, detail="JobLog entry not found")

    return _store_dict_to_entry(updated)


@router.delete("/{job_id}")
def delete_joblog(job_id: str) -> Dict[str, str]:
    """
    Delete a job log entry.
    """
    store = get_joblog_store()

    if not store.delete(job_id):
        raise HTTPException(status_code=404, detail="JobLog entry not found")

    return {"status": "deleted", "job_id": job_id}
