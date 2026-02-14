"""
CAM Stub Routes

Provides stub endpoints for CAM frontend paths that don't have backend implementations yet.
These return empty/default responses to prevent 404 errors while features are being built.

Endpoints covered:
- /backup/* - Backup management
- /pocket/adaptive/* - Adaptive pocket operations
- /drilling/* - Drilling operations
- /metrics/* - CAM metrics and thermal reports
- /job-int/* - Job intelligence
- /job_log/insights/* - Job log insights
- /blueprint/* - Blueprint operations
- /opt/* - Optimization
- /probe/* - Probe operations
- /relief/* - Relief carving
- /posts/* - Post processors
- /machines - Machine list
- /compare/* - CAM diff comparison
- /bridge/* - Bridge export
- /logs/* - Log writing
- /risk/* - Risk reports index
- /fret_slots/* - Fret slot preview
- /adaptive2/* - Adaptive v2 operations
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query, UploadFile, File
from pydantic import BaseModel


router = APIRouter(tags=["cam", "stubs"])


# =============================================================================
# Backup Stubs
# =============================================================================

@router.get("/backup/list")
def list_backups() -> Dict[str, Any]:
    """List available CAM backups."""
    return {"backups": [], "total": 0}


@router.post("/backup/snapshot")
def create_backup_snapshot() -> Dict[str, Any]:
    """Create a new backup snapshot."""
    return {"ok": True, "snapshot_id": None, "message": "Stub: backup not yet implemented"}


# =============================================================================
# Pocket Adaptive Stubs
# =============================================================================

@router.post("/pocket/adaptive/plan")
def plan_adaptive_pocket(payload: Dict[str, Any] = None) -> Dict[str, Any]:
    """Plan an adaptive pocket operation."""
    if payload is None:
        payload = {}
    return {"ok": True, "plan": None, "message": "Stub: use /api/cam/adaptive/* endpoints"}


@router.post("/pocket/adaptive/plan_from_dxf")
def plan_adaptive_from_dxf(payload: Dict[str, Any] = None) -> Dict[str, Any]:
    """Plan adaptive pocket from DXF file."""
    if payload is None:
        payload = {}
    return {"ok": True, "plan": None, "message": "Stub: use /api/cam/adaptive/* endpoints"}


@router.post("/pocket/adaptive/gcode")
def generate_pocket_gcode(payload: Dict[str, Any] = None) -> Dict[str, Any]:
    """Generate G-code for adaptive pocket."""
    if payload is None:
        payload = {}
    return {"ok": True, "gcode": None, "message": "Stub: use /api/cam/adaptive/* endpoints"}


@router.post("/pocket/adaptive/batch_export")
def batch_export_pockets(payload: Dict[str, Any] = None) -> Dict[str, Any]:
    """Batch export adaptive pockets."""
    if payload is None:
        payload = {}
    return {"ok": True, "files": [], "message": "Stub: batch export not yet implemented"}


# =============================================================================
# Drilling Stubs
# =============================================================================

@router.post("/drilling/gcode")
def generate_drilling_gcode(payload: Dict[str, Any] = None) -> Dict[str, Any]:
    """Generate drilling G-code."""
    if payload is None:
        payload = {}
    return {"ok": True, "gcode": None, "message": "Stub: drilling not yet implemented"}


@router.get("/drilling/gcode/download")
def download_drilling_gcode() -> Dict[str, Any]:
    """Download drilling G-code file."""
    return {"ok": False, "message": "Stub: drilling download not yet implemented"}


# =============================================================================
# Metrics Stubs
# =============================================================================

@router.get("/metrics/energy")
def get_energy_metrics() -> Dict[str, Any]:
    """Get energy consumption metrics."""
    return {"total_kwh": 0, "by_operation": {}, "timestamp": None}


@router.get("/metrics/energy_csv")
def get_energy_csv() -> str:
    """Get energy metrics as CSV."""
    return "operation,kwh\n"


@router.get("/metrics/bottleneck_csv")
def get_bottleneck_csv() -> str:
    """Get bottleneck analysis as CSV."""
    return "step,duration_sec,bottleneck\n"


@router.get("/metrics/heat_timeseries")
def get_heat_timeseries() -> Dict[str, Any]:
    """Get thermal timeseries data."""
    return {"series": [], "max_temp": 0, "avg_temp": 0}


@router.get("/metrics/thermal_report_md")
def get_thermal_report_md() -> str:
    """Get thermal report as Markdown."""
    return "# Thermal Report\n\nNo data available."


@router.get("/metrics/thermal_report_bundle")
def get_thermal_report_bundle() -> Dict[str, Any]:
    """Get thermal report bundle."""
    return {"report_md": "", "charts": [], "data": {}}


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
# Blueprint Stubs
# =============================================================================

@router.post("/blueprint/preflight")
def blueprint_preflight(payload: Dict[str, Any] = None) -> Dict[str, Any]:
    """Run blueprint preflight checks."""
    if payload is None:
        payload = {}
    return {"ok": True, "warnings": [], "errors": []}


@router.post("/blueprint/reconstruct-contours")
def reconstruct_contours(payload: Dict[str, Any] = None) -> Dict[str, Any]:
    """Reconstruct contours from blueprint."""
    if payload is None:
        payload = {}
    return {"ok": True, "contours": [], "message": "Stub: contour reconstruction not yet implemented"}


@router.post("/blueprint/to-adaptive")
def blueprint_to_adaptive(payload: Dict[str, Any] = None) -> Dict[str, Any]:
    """Convert blueprint to adaptive toolpath."""
    if payload is None:
        payload = {}
    return {"ok": True, "adaptive_plan": None, "message": "Stub: blueprint-to-adaptive not yet implemented"}


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
# Relief Stubs
# =============================================================================

@router.post("/relief/heightfield_plan")
def plan_heightfield_relief(payload: Dict[str, Any] = None) -> Dict[str, Any]:
    """Plan heightfield relief carving."""
    if payload is None:
        payload = {}
    return {"ok": True, "plan": None, "message": "Stub: relief planning not yet implemented"}


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
# Machines Stubs
# =============================================================================

@router.get("/machines")
def list_machines() -> List[Dict[str, Any]]:
    """List available CNC machines."""
    return []


# =============================================================================
# Compare Stubs
# =============================================================================

@router.post("/compare/diff")
def compare_diff(payload: Dict[str, Any] = None) -> Dict[str, Any]:
    """Compare two CAM operations."""
    if payload is None:
        payload = {}
    return {"diffs": [], "summary": "No differences (stub)"}


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
