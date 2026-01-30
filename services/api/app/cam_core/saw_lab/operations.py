"""Saw Lab operation planners.

Provides functions for planning and executing saw operations,
with integration to the joblog storage system.
"""
from __future__ import annotations

from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid

from .models import SawRunMeta, SawRunRecord, TelemetrySample

# Import storage functions from experimental
from app._experimental.cnc_production.joblog.storage import (
    save_run,
    get_run,
    list_runs,
    update_run_status,
    append_telemetry,
    get_telemetry,
)


def generate_run_id() -> str:
    """Generate a unique run ID with timestamp prefix."""
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    unique = uuid.uuid4().hex[:8]
    return f"{timestamp}_{unique}"


def plan_cut_operation(job: Dict[str, Any]) -> Dict[str, Any]:
    """
    Plan a saw cut operation and create a run record.

    Args:
        job: Job specification with keys:
            - op_type: "slice", "batch", or "contour"
            - blade_id: Blade identifier from registry
            - material: Material being cut
            - rpm: Spindle speed
            - feed_ipm: Feed rate
            - gcode: G-code program (optional)

    Returns:
        Plan result with run_id and any warnings
    """
    # Extract parameters
    op_type = job.get("op_type", "slice")
    blade_id = job.get("blade_id")
    material = job.get("material", "unknown")
    rpm = job.get("rpm")
    feed_ipm = job.get("feed_ipm")
    gcode = job.get("gcode", "")

    # Create metadata
    meta = SawRunMeta(
        op_type=op_type,
        blade_id=blade_id,
        material_family=material,
        rpm=rpm,
        feed_ipm=feed_ipm,
        program_comment=job.get("comment", "Saw Lab operation"),
        # Required fields with sensible defaults
        depth_passes=job.get("depth_passes", 1),
        total_length_mm=job.get("total_length_mm", 0.0),
        doc_per_pass_mm=job.get("doc_per_pass_mm"),
        total_depth_mm=job.get("total_depth_mm"),
    )

    # Generate run ID and create record
    run_id = generate_run_id()
    run = SawRunRecord(
        run_id=run_id,
        meta=meta,
        gcode=gcode,
        status="created",
    )

    # Save to storage
    saved_run = save_run(run)

    # Build warnings
    warnings = []
    if not blade_id:
        warnings.append("No blade specified - using default parameters")
    if not rpm:
        warnings.append("No RPM specified - machine will use default")
    if not gcode:
        warnings.append("No G-code provided - run created for planning only")

    return {
        "run_id": saved_run.run_id,
        "status": saved_run.status,
        "meta": meta.model_dump(),
        "gcode": gcode,
        "warnings": warnings,
    }


def start_run(run_id: str) -> Dict[str, Any]:
    """
    Mark a run as started.

    Args:
        run_id: Run identifier

    Returns:
        Updated run status
    """
    run = update_run_status(run_id, "running")
    if run is None:
        return {"error": f"Run {run_id} not found"}
    return {
        "run_id": run.run_id,
        "status": run.status,
        "started_at": run.started_at,
    }


def complete_run(run_id: str, success: bool = True) -> Dict[str, Any]:
    """
    Mark a run as completed.

    Args:
        run_id: Run identifier
        success: Whether the run completed successfully

    Returns:
        Updated run status
    """
    status = "completed" if success else "failed"
    run = update_run_status(run_id, status)
    if run is None:
        return {"error": f"Run {run_id} not found"}
    return {
        "run_id": run.run_id,
        "status": run.status,
        "completed_at": run.completed_at,
    }


def add_telemetry(run_id: str, sample: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add a telemetry sample to a run.

    Args:
        run_id: Run identifier
        sample: Telemetry data with keys like x_mm, y_mm, rpm_actual, etc.

    Returns:
        Telemetry record summary
    """
    telemetry_sample = TelemetrySample(**sample)
    record = append_telemetry(run_id, telemetry_sample)
    return {
        "run_id": run_id,
        "sample_count": len(record.samples),
        "latest_sample": telemetry_sample.model_dump(),
    }


def get_run_details(run_id: str) -> Optional[Dict[str, Any]]:
    """
    Get full details for a run including telemetry.

    Args:
        run_id: Run identifier

    Returns:
        Run details or None if not found
    """
    run = get_run(run_id)
    if run is None:
        return None

    telemetry = get_telemetry(run_id)

    return {
        "run": run.model_dump(),
        "telemetry": telemetry.model_dump() if telemetry else None,
    }


def list_recent_runs(
    limit: int = 20,
    status: Optional[str] = None,
    op_type: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    List recent runs with optional filtering.

    Args:
        limit: Maximum number of runs to return
        status: Filter by status (created, running, completed, failed)
        op_type: Filter by operation type (slice, batch, contour)

    Returns:
        List of run summaries
    """
    # Storage only supports op_type filtering, so we filter status in Python
    runs = list_runs(limit=limit, op_type=op_type)

    # Apply status filter if provided
    if status:
        runs = [r for r in runs if r.status == status]

    return [
        {
            "run_id": r.run_id,
            "status": r.status,
            "op_type": r.meta.op_type if r.meta else None,
            "blade_id": r.meta.blade_id if r.meta else None,
            "created_at": r.created_at,
        }
        for r in runs
    ]
