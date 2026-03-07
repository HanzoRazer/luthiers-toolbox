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


@router.get("/rosette/cnc-history")
def get_cnc_history(
    limit: int = Query(default=50, ge=1, le=200),
) -> Dict[str, Any]:
    """Get CNC job history for rosettes."""
    return {
        "jobs": [],
        "total": 0,
    }


@router.get("/rosette/cnc-job/{job_id}")
def get_cnc_job(job_id: str) -> Dict[str, Any]:
    """Get CNC job details."""
    return {
        "job_id": job_id,
        "status": "not_found",
        "message": "Stub: job lookup not yet implemented",
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

