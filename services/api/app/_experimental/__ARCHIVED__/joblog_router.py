"""
CP-S59 — Saw JobLog API Router

FastAPI endpoints for saw operation job logging and telemetry collection.
Provides CRUD operations for job runs and telemetry data.

Endpoints:
- POST /joblog/saw_runs - Create job run entry
- GET /joblog/saw_runs - List recent runs (with filters)
- GET /joblog/saw_runs/{run_id} - Get specific run details
- PUT /joblog/saw_runs/{run_id}/status - Update run status
- POST /joblog/saw_runs/{run_id}/telemetry - Add telemetry sample
- GET /joblog/saw_runs/{run_id}/telemetry - Get run telemetry

Usage:
```python
# In main.py
from routers import joblog_router

app.include_router(joblog_router.router)
```

Example Requests:
```bash
# Create job run
curl -X POST http://localhost:8000/joblog/saw_runs \
  -H "Content-Type: application/json" \
  -d '{
    "run_id": "20251127T120000Z_a1b2",
    "meta": {...},
    "gcode": "G21\\nG90\\n..."
  }'

# List recent slice operations
curl "http://localhost:8000/joblog/saw_runs?op_type=slice&limit=10"

# Add telemetry sample
curl -X POST http://localhost:8000/joblog/saw_runs/20251127T120000Z_a1b2/telemetry \
  -H "Content-Type: application/json" \
  -d '{
    "x_mm": 10.0,
    "rpm_actual": 3600,
    "spindle_load_percent": 45.0,
    "in_cut": true
  }'
```
"""

from __future__ import annotations

from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

try:
    # FastAPI application import (normal deployment)
    from .cnc_production.joblog.models import (
        SawRunRecord,
        SawRunMeta,
        TelemetrySample,
        SawTelemetryRecord
    )
    from .cnc_production.joblog.storage import (
        save_run,
        get_run,
        list_runs,
        update_run_status,
        append_telemetry,
        get_telemetry,
        compute_telemetry_stats
    )
except ImportError:
    # Direct testing import
    from cnc_production.joblog.models import (
        SawRunRecord,
        SawRunMeta,
        TelemetrySample,
        SawTelemetryRecord
    )
    from cnc_production.joblog.storage import (
        save_run,
        get_run,
        list_runs,
        update_run_status,
        append_telemetry,
        get_telemetry,
        compute_telemetry_stats
    )


router = APIRouter(prefix="/joblog", tags=["joblog", "telemetry"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class CreateRunRequest(BaseModel):
    """Request to create new job run (includes G-code)."""
    run_id: str
    meta: SawRunMeta
    gcode: str


class UpdateStatusRequest(BaseModel):
    """Request to update run execution status."""
    status: str
    error_message: Optional[str] = None


# ============================================================================
# JOB RUN ENDPOINTS
# ============================================================================

@router.post("/saw_runs", response_model=SawRunRecord, status_code=201)
def create_saw_run(request: CreateRunRequest) -> SawRunRecord:
    """
    Create new saw operation job run entry.
    
    Stores metadata, G-code, and initializes execution tracking.
    Returns created run with timestamps.
    
    Args:
        request: Run metadata + G-code
    
    Returns:
        Created SawRunRecord
    
    Example:
        ```json
        {
          "run_id": "20251127T120000Z_a1b2c3d4",
          "meta": {
            "op_type": "slice",
            "blade_id": "TENRYU_GM-305100AB",
            "rpm": 3600,
            "feed_ipm": 60,
            "depth_passes": 3,
            "total_length_mm": 300.0,
            "risk_grade": "GREEN"
          },
          "gcode": "G21\\nG90\\nG17\\n..."
        }
        ```
    """
    # Check for duplicate run_id
    existing = get_run(request.run_id)
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Run ID {request.run_id} already exists"
        )
    
    # Create run record
    run = SawRunRecord(
        run_id=request.run_id,
        meta=request.meta,
        gcode=request.gcode,
        status="created"
    )
    
    return save_run(run)


@router.get("/saw_runs", response_model=List[SawRunRecord])
def list_saw_runs(
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum runs to return"),
    op_type: Optional[str] = Query(None, description="Filter by operation type"),
    machine_profile: Optional[str] = Query(None, description="Filter by machine")
) -> List[SawRunRecord]:
    """
    List recent saw operation runs with optional filtering.
    
    Returns runs in reverse chronological order (newest first).
    
    Query Parameters:
        - limit: Max results (1-1000, default 100)
        - op_type: Filter by "slice", "batch", or "contour"
        - machine_profile: Filter by machine identifier
    
    Returns:
        List of SawRunRecord objects
    
    Example:
        ```
        GET /joblog/saw_runs?limit=10&op_type=slice&machine_profile=AXIOM_AR8
        ```
    """
    return list_runs(
        limit=limit,
        op_type=op_type,
        machine_profile=machine_profile
    )


@router.get("/saw_runs/{run_id}", response_model=SawRunRecord)
def get_saw_run(run_id: str) -> SawRunRecord:
    """
    Get specific saw operation run by ID.
    
    Returns complete run record including metadata, G-code, and timestamps.
    
    Args:
        run_id: Unique run identifier
    
    Returns:
        SawRunRecord
    
    Raises:
        404: Run not found
    
    Example:
        ```
        GET /joblog/saw_runs/20251127T120000Z_a1b2c3d4
        ```
    """
    run = get_run(run_id)
    if not run:
        raise HTTPException(
            status_code=404,
            detail=f"Run {run_id} not found"
        )
    return run


@router.put("/saw_runs/{run_id}/status", response_model=SawRunRecord)
def update_saw_run_status(run_id: str, request: UpdateStatusRequest) -> SawRunRecord:
    """
    Update run execution status and timestamps.
    
    Used to track run lifecycle: created → running → completed/failed.
    
    Args:
        run_id: Run identifier
        request: New status and optional error message
    
    Returns:
        Updated SawRunRecord
    
    Raises:
        404: Run not found
    
    Status Values:
        - created: Job logged but not started
        - running: Execution in progress
        - completed: Successfully finished
        - failed: Execution error
    
    Example:
        ```json
        PUT /joblog/saw_runs/20251127T120000Z_a1b2c3d4/status
        {
          "status": "running"
        }
        ```
    """
    # Determine timestamps based on status
    started_at = None
    completed_at = None
    
    if request.status == "running":
        started_at = datetime.utcnow()
    elif request.status in ["completed", "failed"]:
        completed_at = datetime.utcnow()
    
    run = update_run_status(
        run_id,
        status=request.status,
        started_at=started_at,
        completed_at=completed_at,
        error_message=request.error_message
    )
    
    if not run:
        raise HTTPException(
            status_code=404,
            detail=f"Run {run_id} not found"
        )
    
    return run


# ============================================================================
# TELEMETRY ENDPOINTS
# ============================================================================

@router.post("/saw_runs/{run_id}/telemetry", response_model=SawTelemetryRecord)
def add_telemetry_sample(run_id: str, sample: TelemetrySample) -> SawTelemetryRecord:
    """
    Add real-time telemetry sample to run.
    
    Appends sample to run's telemetry record. Creates record if it doesn't exist.
    Used for continuous data collection during job execution.
    
    Args:
        run_id: Associated job run ID
        sample: Telemetry sample with position, feeds, loads, etc.
    
    Returns:
        Updated SawTelemetryRecord with all samples
    
    Example:
        ```json
        POST /joblog/saw_runs/20251127T120000Z_a1b2/telemetry
        {
          "x_mm": 10.5,
          "y_mm": 20.3,
          "z_mm": -1.5,
          "rpm_actual": 3600,
          "feed_actual_mm_min": 1524,
          "spindle_load_percent": 45.2,
          "in_cut": true
        }
        ```
    """
    # Verify run exists
    run = get_run(run_id)
    if not run:
        raise HTTPException(
            status_code=404,
            detail=f"Run {run_id} not found. Create run before adding telemetry."
        )
    
    return append_telemetry(run_id, sample)


@router.get("/saw_runs/{run_id}/telemetry", response_model=SawTelemetryRecord)
def get_run_telemetry(run_id: str, compute_stats: bool = Query(False)) -> SawTelemetryRecord:
    """
    Get telemetry data for run.
    
    Returns all telemetry samples collected during execution.
    Optionally computes summary statistics (avg load, cut time, anomalies).
    
    Args:
        run_id: Job run identifier
        compute_stats: Whether to compute/update summary statistics
    
    Returns:
        SawTelemetryRecord with samples and optional stats
    
    Raises:
        404: Telemetry not found (no samples collected)
    
    Example:
        ```
        GET /joblog/saw_runs/20251127T120000Z_a1b2/telemetry?compute_stats=true
        ```
    """
    if compute_stats:
        # Compute and save stats
        telem = compute_telemetry_stats(run_id)
    else:
        # Just retrieve
        telem = get_telemetry(run_id)
    
    if not telem:
        raise HTTPException(
            status_code=404,
            detail=f"No telemetry found for run {run_id}"
        )
    
    return telem


@router.delete("/saw_runs/{run_id}/telemetry", status_code=204)
def clear_run_telemetry(run_id: str):
    """
    Clear telemetry samples for run (debug/testing only).
    
    Removes all telemetry data but preserves job run record.
    Use cautiously - telemetry data is valuable for learning.
    
    Args:
        run_id: Job run identifier
    
    Returns:
        204 No Content on success
    
    Example:
        ```
        DELETE /joblog/saw_runs/20251127T120000Z_a1b2/telemetry
        ```
    """
    from .cnc_production.joblog.storage import TELEMETRY_PATH, _load_json, _save_json
    
    data = _load_json(TELEMETRY_PATH)
    telem: dict = data.get("telemetry", {})
    
    if run_id in telem:
        del telem[run_id]
        data["telemetry"] = telem
        _save_json(TELEMETRY_PATH, data)
    
    return None
