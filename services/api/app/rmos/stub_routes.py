"""
RMOS Stub Routes

Provides stub endpoints for frontend paths that don't have backend implementations yet.
These return empty/default responses to prevent 404 errors while features are being built.

Endpoints covered:
- /rosette/* - Rosette designer operations
- /live-monitor/* - Live monitoring drilldown
- /wrap/mvp/* - DXF to G-code MVP wrapper
- /safety/* - Safety evaluation endpoints

REMOVED (real implementations exist):
- /analytics/* - See app.rmos.analytics.router
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query


router = APIRouter(tags=["rmos", "stubs"])


# =============================================================================
# Analytics - REMOVED: Real implementations exist in app.rmos.analytics.router
# See: /api/rmos/analytics/lane-analytics, /api/rmos/analytics/risk-timeline/*
# =============================================================================


# =============================================================================
# Rosette Designer Stubs
# =============================================================================

@router.post("/rosette/segment-ring")
def generate_segment_ring(payload: Dict[str, Any] = None) -> Dict[str, Any]:
    """Generate rosette segment ring geometry."""
    if payload is None:
        payload = {}
    return {
        "ok": True,
        "segments": [],
        "message": "Stub: segment-ring generation not yet implemented",
    }


@router.post("/rosette/generate-slices")
def generate_slices(payload: Dict[str, Any] = None) -> Dict[str, Any]:
    """Generate rosette slices for manufacturing."""
    if payload is None:
        payload = {}
    return {
        "ok": True,
        "slices": [],
        "message": "Stub: slice generation not yet implemented",
    }


@router.post("/rosette/preview")
def preview_rosette(payload: Dict[str, Any] = None) -> Dict[str, Any]:
    """Generate rosette preview image."""
    if payload is None:
        payload = {}
    return {
        "ok": True,
        "preview_url": None,
        "message": "Stub: preview generation not yet implemented",
    }


@router.post("/rosette/export-cnc")
def export_rosette_cnc(payload: Dict[str, Any] = None) -> Dict[str, Any]:
    """Export rosette to CNC-ready format."""
    if payload is None:
        payload = {}
    return {
        "ok": True,
        "gcode": None,
        "job_id": None,
        "message": "Stub: CNC export not yet implemented",
    }


# =============================================================================
# Rosette CNC Proxies (delegating to real art_jobs_store)
# =============================================================================

from ..services.art_jobs_store import get_art_job, _load_jobs
from datetime import datetime


@router.get("/rosette/cnc-history")
def get_cnc_history(
    limit: int = Query(default=50, ge=1, le=200),
    job_type: Optional[str] = Query(None, description="Filter by job type"),
) -> Dict[str, Any]:
    """Get CNC job history for rosettes (proxy to real art_jobs_store)."""
    all_jobs = _load_jobs()

    # Filter by job_type if specified (default: rosette_cam)
    if job_type:
        filtered = [j for j in all_jobs if j.get("job_type") == job_type]
    else:
        # Default to rosette jobs
        filtered = [j for j in all_jobs if j.get("job_type", "").startswith("rosette")]

    # Sort by created_at descending (most recent first)
    filtered.sort(key=lambda x: x.get("created_at", 0), reverse=True)

    # Apply limit
    jobs = filtered[:limit]

    # Format timestamps for frontend
    for job in jobs:
        if "created_at" in job and isinstance(job["created_at"], (int, float)):
            job["created_at"] = datetime.fromtimestamp(job["created_at"]).isoformat() + "Z"

    return {
        "jobs": jobs,
        "total": len(filtered),
    }


@router.get("/rosette/cnc-job/{job_id}")
def get_cnc_job(job_id: str) -> Dict[str, Any]:
    """Get CNC job details (proxy to real art_jobs_store)."""
    from fastapi import HTTPException

    job = get_art_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job ''{job_id}'' not found")

    # Format timestamp for frontend
    created_at = job.created_at
    if isinstance(created_at, (int, float)):
        created_at = datetime.fromtimestamp(created_at).isoformat() + "Z"

    return {
        "job_id": job.id,
        "job_type": job.job_type,
        "created_at": created_at,
        "post_preset": job.post_preset,
        "rings": job.rings,
        "z_passes": job.z_passes,
        "length_mm": job.length_mm,
        "gcode_lines": job.gcode_lines,
        "meta": job.meta,
        "status": "complete",
    }


# =============================================================================
# Live Monitor Stubs
# =============================================================================

@router.get("/live-monitor/{job_id}/drilldown")
def get_live_monitor_drilldown(job_id: str) -> Dict[str, Any]:
    """Get live monitor drilldown data for a job."""
    return {
        "job_id": job_id,
        "metrics": [],
        "events": [],
        "status": "unknown",
        "message": "Stub: live monitor not yet implemented",
    }


# =============================================================================
# MVP Wrapper Stubs
# =============================================================================

@router.post("/wrap/mvp/dxf-to-grbl")
def dxf_to_grbl(payload: Dict[str, Any] = None) -> Dict[str, Any]:
    """Convert DXF to GRBL G-code (MVP workflow)."""
    if payload is None:
        payload = {}
    return {
        "ok": False,
        "gcode": None,
        "run_id": None,
        "message": "Stub: DXF-to-GRBL conversion not yet implemented. Use /api/cam/adaptive/* endpoints.",
    }


# =============================================================================
# Safety Evaluation Stubs
# =============================================================================

@router.post("/safety/evaluate")
def evaluate_safety(payload: Dict[str, Any] = None) -> Dict[str, Any]:
    """Evaluate safety constraints for an operation."""
    if payload is None:
        payload = {}
    return {
        "ok": True,
        "decision": "ALLOW",
        "risk_level": "GREEN",
        "warnings": [],
        "blocks": [],
    }


@router.get("/safety/mode")
def get_safety_mode() -> Dict[str, Any]:
    """Get current safety mode settings."""
    return {
        "mode": "standard",
        "strict_mode": False,
        "allow_overrides": True,
    }


@router.post("/safety/create-override")
def create_safety_override(payload: Dict[str, Any] = None) -> Dict[str, Any]:
    """Create a safety override for a blocked operation."""
    if payload is None:
        payload = {}
    return {
        "ok": True,
        "override_id": None,
        "message": "Stub: override creation not yet implemented",
    }

