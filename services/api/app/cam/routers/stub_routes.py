"""
CAM Stub Routes

Provides stub endpoints for CAM frontend paths that don't have backend implementations yet.
These return empty/default responses to prevent 404 errors while features are being built.

Endpoints covered:
- /job-int/* - Job intelligence
- /job_log/insights/* - Job log insights
- /opt/* - Optimization
- /probe/* - Probe operations
- /posts/* - Post processors
- /bridge/* - Bridge export
- /logs/* - Log writing
- /risk/* - Risk reports index
- /fret_slots/* - Fret slot preview
- /adaptive2/* - Adaptive v2 operations

REMOVED (real implementations exist):
- /backup/* - See cam/routers/utility/backup_router.py
- /drilling/* - See cam/routers/drilling/drill_router.py
- /pocket/adaptive/* - See routers/adaptive/*.py
- /blueprint/preflight, to-adaptive, reconstruct-contours - See routers/blueprint_cam/*.py
"""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter


router = APIRouter(tags=["cam", "stubs"])


# =============================================================================
# Job Intelligence Stubs
# =============================================================================

@router.post("/job-int/log")
def log_job_intelligence(payload: Dict[str, Any] = None) -> Dict[str, Any]:
    """Log job intelligence event."""
    if payload is None:
        payload = {}
    return {"ok": True, "event_id": None}


@router.get("/job-int/log/{job_id}")
def get_job_intelligence_log(job_id: str) -> Dict[str, Any]:
    """Get job intelligence log."""
    return {"job_id": job_id, "events": []}


@router.get("/job-int/favorites/{category}")
def get_job_favorites(category: str) -> Dict[str, Any]:
    """Get job favorites by category."""
    return {"category": category, "favorites": []}


# =============================================================================
# Job Log Insights Stubs
# =============================================================================

@router.get("/job_log/insights")
def get_job_insights() -> Dict[str, Any]:
    """Get job log insights."""
    return {"insights": [], "total_jobs": 0}


@router.get("/job_log/insights/{insight_id}")
def get_job_insight(insight_id: str) -> Dict[str, Any]:
    """Get specific job insight."""
    return {"insight_id": insight_id, "data": None}


# =============================================================================
# Optimization Stubs
# =============================================================================

@router.post("/opt/what_if")
def run_what_if(payload: Dict[str, Any] = None) -> Dict[str, Any]:
    """Run what-if optimization scenario."""
    if payload is None:
        payload = {}
    return {"ok": True, "results": [], "message": "Stub: what-if not yet implemented"}


# =============================================================================
# Probe Stubs
# =============================================================================

@router.get("/probe/svg_setup_sheet")
def get_probe_setup_sheet() -> str:
    """Get probe setup sheet as SVG."""
    return "<svg></svg>"


# =============================================================================
# Posts Stubs
# =============================================================================

@router.get("/posts")
def list_posts() -> List[Dict[str, Any]]:
    """List available post processors."""
    return []


@router.get("/posts/{post_id}")
def get_post(post_id: str) -> Dict[str, Any]:
    """Get post processor details."""
    return {"post_id": post_id, "name": post_id, "config": {}}


# =============================================================================
# Bridge Stubs
# =============================================================================

@router.post("/bridge/export_dxf")
def export_bridge_dxf(payload: Dict[str, Any] = None) -> Dict[str, Any]:
    """Export bridge geometry to DXF."""
    if payload is None:
        payload = {}
    return {"ok": True, "dxf_data": None, "message": "Stub: bridge export not yet implemented"}


# =============================================================================
# Logs Stubs
# =============================================================================

@router.post("/logs/write")
def write_cam_log(payload: Dict[str, Any] = None) -> Dict[str, Any]:
    """Write CAM log entry."""
    if payload is None:
        payload = {}
    return {"ok": True, "log_id": None}


# =============================================================================
# Risk Stubs
# =============================================================================

@router.get("/risk/reports_index")
def get_risk_reports_index() -> Dict[str, Any]:
    """Get risk reports index."""
    return {"reports": [], "total": 0}


# =============================================================================
# Fret Slots Stubs
# =============================================================================

@router.post("/fret_slots/preview")
def preview_fret_slots(payload: Dict[str, Any] = None) -> Dict[str, Any]:
    """Preview fret slot positions."""
    if payload is None:
        payload = {}
    return {"ok": True, "slots": [], "preview_svg": None}


# =============================================================================
# Adaptive v2 Stubs
# =============================================================================

@router.post("/adaptive2/bench")
def run_adaptive_bench(payload: Dict[str, Any] = None) -> Dict[str, Any]:
    """Run adaptive v2 benchmark."""
    if payload is None:
        payload = {}
    return {"ok": True, "results": {}, "message": "Stub: benchmark not yet implemented"}


@router.get("/adaptive2/offset_spiral.svg")
def get_offset_spiral_svg() -> str:
    """Get offset spiral preview as SVG."""
    return "<svg></svg>"


@router.get("/adaptive2/trochoid_corners.svg")
def get_trochoid_corners_svg() -> str:
    """Get trochoid corners preview as SVG."""
    return "<svg></svg>"
