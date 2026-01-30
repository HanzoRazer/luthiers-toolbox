"""Saw Lab API endpoints.

Provides REST API for saw operation planning, execution tracking,
telemetry collection, and learning-based optimization.
"""
from __future__ import annotations

from datetime import datetime
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ..saw_lab.models import (
    SawLabRun,
    SawRunRecord,
    SawRunMeta,
    TelemetrySample,
    TelemetryIngestRequest,
)
from ..saw_lab.operations import (
    plan_cut_operation,
    start_run,
    complete_run,
    add_telemetry,
    get_run_details,
    list_recent_runs,
)
from ..saw_lab.learning import (
    compute_learning_lanes,
    analyze_run_telemetry,
    get_run_metrics,
)

# Import storage directly for simple lookups
from app._experimental.cnc_production.joblog.storage import get_run, list_runs

router = APIRouter(prefix="/saw-lab", tags=["cam-core", "saw-lab"])


# ============================================================================
# Request/Response Models
# ============================================================================

class CreateRunRequest(BaseModel):
    """Request to create a new saw run."""
    op_type: str = Field(default="slice", description="Operation type: slice, batch, contour")
    blade_id: Optional[str] = Field(None, description="Blade identifier from registry")
    material: Optional[str] = Field(None, description="Material being cut")
    rpm: Optional[int] = Field(None, description="Spindle speed")
    feed_ipm: Optional[float] = Field(None, description="Feed rate in inches per minute")
    gcode: Optional[str] = Field(None, description="G-code program")
    comment: Optional[str] = Field(None, description="Job description")


class UpdateStatusRequest(BaseModel):
    """Request to update run status."""
    status: str = Field(..., description="New status: running, completed, failed")


class TelemetrySampleRequest(BaseModel):
    """Request to add telemetry sample."""
    x_mm: Optional[float] = None
    y_mm: Optional[float] = None
    z_mm: Optional[float] = None
    rpm_actual: Optional[int] = None
    feed_actual_mm_min: Optional[float] = None
    spindle_load_pct: Optional[float] = None
    motor_current_amps: Optional[float] = None
    temp_c: Optional[float] = None
    vibration_rms: Optional[float] = None


class LearningRequest(BaseModel):
    """Request to analyze telemetry for learning."""
    tool_id: str
    material: str
    machine_profile: str = "default"
    current_scale: float = 1.0
    apply: bool = False


# ============================================================================
# Run Management Endpoints
# ============================================================================

@router.post("/runs", response_model=Dict[str, Any])
def create_run(request: CreateRunRequest) -> Dict[str, Any]:
    """
    Create a new saw run.

    Plans a cut operation and saves it to storage.
    Returns run_id and any warnings about missing parameters.
    """
    job = request.model_dump()
    return plan_cut_operation(job)


@router.get("/runs", response_model=List[Dict[str, Any]])
def list_runs_endpoint(
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    op_type: Optional[str] = Query(None),
) -> List[Dict[str, Any]]:
    """
    List recent runs with optional filtering.
    """
    return list_recent_runs(limit=limit, status=status, op_type=op_type)


@router.get("/runs/{run_id}", response_model=Dict[str, Any])
def get_run_endpoint(run_id: str) -> Dict[str, Any]:
    """
    Get details for a specific run including telemetry.
    """
    details = get_run_details(run_id)
    if details is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    return details


@router.post("/runs/{run_id}/start", response_model=Dict[str, Any])
def start_run_endpoint(run_id: str) -> Dict[str, Any]:
    """
    Mark a run as started.
    """
    result = start_run(run_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post("/runs/{run_id}/complete", response_model=Dict[str, Any])
def complete_run_endpoint(run_id: str, success: bool = Query(True)) -> Dict[str, Any]:
    """
    Mark a run as completed.
    """
    result = complete_run(run_id, success=success)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.patch("/runs/{run_id}/status", response_model=Dict[str, Any])
def update_run_status_endpoint(run_id: str, request: UpdateStatusRequest) -> Dict[str, Any]:
    """
    Update run status directly.
    """
    if request.status == "running":
        return start_run(run_id)
    elif request.status in ("completed", "failed"):
        return complete_run(run_id, success=(request.status == "completed"))
    else:
        raise HTTPException(status_code=400, detail=f"Invalid status: {request.status}")


# ============================================================================
# Telemetry Endpoints
# ============================================================================

@router.post("/runs/{run_id}/telemetry", response_model=Dict[str, Any])
def add_telemetry_endpoint(run_id: str, request: TelemetrySampleRequest) -> Dict[str, Any]:
    """
    Add a telemetry sample to a run.
    """
    sample = request.model_dump(exclude_none=True)
    return add_telemetry(run_id, sample)


@router.get("/runs/{run_id}/metrics", response_model=Dict[str, Any])
def get_run_metrics_endpoint(run_id: str) -> Dict[str, Any]:
    """
    Get computed metrics for a run's telemetry.
    """
    metrics = get_run_metrics(run_id)
    if metrics is None:
        raise HTTPException(status_code=404, detail=f"No telemetry found for run {run_id}")
    return metrics


# ============================================================================
# Learning Endpoints
# ============================================================================

@router.post("/runs/{run_id}/analyze", response_model=Dict[str, Any])
def analyze_run_endpoint(run_id: str, request: LearningRequest) -> Dict[str, Any]:
    """
    Analyze telemetry for a run and compute learning adjustments.

    Returns risk assessment and recommended feed/speed scale adjustments.
    Set apply=true to persist the adjustment to the learned overrides.
    """
    return analyze_run_telemetry(
        run_id=run_id,
        tool_id=request.tool_id,
        material=request.material,
        machine_profile=request.machine_profile,
        current_scale=request.current_scale,
        apply_adjustment=request.apply,
    )


@router.post("/learn", response_model=Dict[str, Any])
def compute_learning_endpoint(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compute learning insights from raw telemetry events.

    Legacy endpoint for batch processing telemetry.
    For new code, use POST /runs/{run_id}/analyze.
    """
    return compute_learning_lanes(events)


# ============================================================================
# Health Check
# ============================================================================

@router.get("/health")
def health_check() -> Dict[str, str]:
    """Check Saw Lab service health."""
    return {
        "status": "healthy",
        "service": "saw-lab",
        "version": "1.0.0",
    }
