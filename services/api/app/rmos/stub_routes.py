"""
RMOS Stub Routes

Provides stub endpoints for frontend paths that don't have backend implementations yet.
These return empty/default responses to prevent 404 errors while features are being built.

Endpoints covered:
- /analytics/* - Lane analytics and risk timeline
- /rosette/* - Rosette designer operations
- /live-monitor/* - Live monitoring drilldown
- /wrap/mvp/* - DXF to G-code MVP wrapper
- /safety/* - Safety evaluation endpoints
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel


router = APIRouter(tags=["rmos", "stubs"])


# =============================================================================
# Analytics Stubs
# =============================================================================

class LaneAnalyticsResponse(BaseModel):
    lanes: List[Dict[str, Any]] = []
    total_runs: int = 0
    period_start: Optional[str] = None
    period_end: Optional[str] = None


class RiskTimelineResponse(BaseModel):
    preset_id: str
    events: List[Dict[str, Any]] = []
    total: int = 0


@router.get("/analytics/lane-analytics", response_model=LaneAnalyticsResponse)
def get_lane_analytics(
    limit_recent: int = Query(default=100, ge=1, le=1000),
) -> LaneAnalyticsResponse:
    """Get lane-level analytics for RMOS operations."""
    return LaneAnalyticsResponse(
        lanes=[],
        total_runs=0,
        period_start=datetime.utcnow().isoformat() + "Z",
        period_end=datetime.utcnow().isoformat() + "Z",
    )


@router.get("/analytics/risk-timeline/{preset_id}", response_model=RiskTimelineResponse)
def get_risk_timeline(
    preset_id: str,
    limit: int = Query(default=50, ge=1, le=500),
) -> RiskTimelineResponse:
    """Get risk timeline events for a preset."""
    return RiskTimelineResponse(
        preset_id=preset_id,
        events=[],
        total=0,
    )


# =============================================================================
# Rosette Designer Stubs
# =============================================================================

@router.post("/rosette/segment-ring")
def generate_segment_ring(payload: Dict[str, Any] = {}) -> Dict[str, Any]:
    """Generate rosette segment ring geometry."""
    return {
        "ok": True,
        "segments": [],
        "message": "Stub: segment-ring generation not yet implemented",
    }


@router.post("/rosette/generate-slices")
def generate_slices(payload: Dict[str, Any] = {}) -> Dict[str, Any]:
    """Generate rosette slices for manufacturing."""
    return {
        "ok": True,
        "slices": [],
        "message": "Stub: slice generation not yet implemented",
    }


@router.post("/rosette/preview")
def preview_rosette(payload: Dict[str, Any] = {}) -> Dict[str, Any]:
    """Generate rosette preview image."""
    return {
        "ok": True,
        "preview_url": None,
        "message": "Stub: preview generation not yet implemented",
    }


@router.post("/rosette/export-cnc")
def export_rosette_cnc(payload: Dict[str, Any] = {}) -> Dict[str, Any]:
    """Export rosette to CNC-ready format."""
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
def dxf_to_grbl(payload: Dict[str, Any] = {}) -> Dict[str, Any]:
    """Convert DXF to GRBL G-code (MVP workflow)."""
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
def evaluate_safety(payload: Dict[str, Any] = {}) -> Dict[str, Any]:
    """Evaluate safety constraints for an operation."""
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
def create_safety_override(payload: Dict[str, Any] = {}) -> Dict[str, Any]:
    """Create a safety override for a blocked operation."""
    return {
        "ok": True,
        "override_id": None,
        "message": "Stub: override creation not yet implemented",
    }


# =============================================================================
# Presets Stubs
# =============================================================================

@router.post("/presets/{preset_id}/promote")
def promote_preset(preset_id: str) -> Dict[str, Any]:
    """Promote a preset to production."""
    return {
        "ok": True,
        "preset_id": preset_id,
        "message": "Stub: preset promotion not yet implemented",
    }
