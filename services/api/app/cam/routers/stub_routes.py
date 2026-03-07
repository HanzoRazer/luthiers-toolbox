"""
CAM Stub Routes

Provides stub endpoints for CAM frontend paths that don't have backend implementations yet.
These return empty/default responses to prevent 404 errors while features are being built.

Endpoints covered:
- /job-int/* - Job intelligence (proxied to real job_int_log service)
- /job_log/insights/* - Job log insights
- /probe/* - Probe operations (proxied to real setup_router)
- /posts/* - Post processors (proxied to real posts_consolidated_router)
- /bridge/* - Bridge export
- /logs/* - Log writing (proxied to real logs_router)
- /risk/* - Risk reports index
- /fret_slots/* - Fret slot preview
- /adaptive2/* - Adaptive v2 operations (proxied to real benchmark_router)

REMOVED (real implementations exist):
- /backup/* - See cam/routers/utility/backup_router.py
- /drilling/* - See cam/routers/drilling/drill_router.py
- /pocket/adaptive/* - See routers/adaptive/*.py
- /blueprint/preflight, to-adaptive, reconstruct-contours - See routers/blueprint_cam/*.py
- /opt/what_if, /opt/feeds-speeds - See cam/routers/utility/optimization_router.py
"""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter


router = APIRouter(tags=["cam", "stubs"])


# =============================================================================
# Job Intelligence Proxies (using real job_int_log service)
# =============================================================================

from fastapi import Query, HTTPException
from pydantic import BaseModel

from app.services.job_int_log import (
    load_all_job_logs,
    find_job_log_by_run_id,
    append_job_log_entry,
)


class FavoriteUpdateIn(BaseModel):
    """Request body for favorite toggle."""
    favorite: bool


@router.get("/job-int/log")
def list_job_intelligence_logs(
    machine_id: Optional[str] = Query(None),
    post_id: Optional[str] = Query(None),
    helical_only: Optional[bool] = Query(None),
    favorites_only: Optional[bool] = Query(None),
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0),
) -> Dict[str, Any]:
    """List job intelligence logs with filtering (proxy to real service)."""
    all_logs = load_all_job_logs()
    
    # Apply filters
    filtered = all_logs
    if machine_id:
        filtered = [e for e in filtered if e.get("machine_id") == machine_id]
    if post_id:
        filtered = [e for e in filtered if e.get("post_id") == post_id]
    if helical_only:
        filtered = [e for e in filtered if e.get("use_helical")]
    if favorites_only:
        filtered = [e for e in filtered if e.get("favorite")]
    
    # Sort by created_at descending (most recent first)
    filtered.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    
    total = len(filtered)
    items = filtered[offset:offset + limit]
    
    return {"total": total, "items": items}


@router.get("/job-int/log/{run_id}")
def get_job_intelligence_log(run_id: str) -> Dict[str, Any]:
    """Get job intelligence log by run_id (proxy to real service)."""
    entry = find_job_log_by_run_id(run_id)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Job log '{run_id}' not found")
    return entry


@router.post("/job-int/favorites/{run_id}")
def update_job_favorite(run_id: str, body: FavoriteUpdateIn) -> Dict[str, Any]:
    """Update favorite status for a job log (proxy to real service)."""
    import json
    import os
    from app.services.job_int_log import DEFAULT_LOG_PATH
    
    # Find and update the entry
    all_logs = load_all_job_logs()
    found_idx = None
    for i, entry in enumerate(all_logs):
        if entry.get("run_id") == run_id:
            found_idx = i
            break
    
    if found_idx is None:
        raise HTTPException(status_code=404, detail=f"Job log '{run_id}' not found")
    
    # Update the favorite status
    all_logs[found_idx]["favorite"] = body.favorite
    
    # Rewrite the file
    path = DEFAULT_LOG_PATH
    if os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            for entry in all_logs:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    
    return all_logs[found_idx]


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
# Probe Proxy (delegating to real setup_router implementation)
# =============================================================================

from pydantic import BaseModel
from typing import Optional

from ...routers.probe.setup_router import generate_setup_sheet as real_generate_setup_sheet
from ...schemas.probe_schemas import SetupSheetIn


class ProbeSetupSheetRequest(BaseModel):
    """Frontend request format for probe setup sheet."""
    pattern: str
    estimated_diameter: Optional[float] = 50.0


@router.post("/probe/svg_setup_sheet")
async def get_probe_setup_sheet(req: ProbeSetupSheetRequest):
    """Get probe setup sheet as SVG (proxy to real implementation)."""
    from fastapi import HTTPException
    from pydantic import ValidationError
    
    try:
        # Map frontend format to real implementation format
        setup_req = SetupSheetIn(
            pattern=req.pattern,
            feature_diameter=req.estimated_diameter,
            part_width=100.0,
            part_height=60.0,
        )
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    
    return await real_generate_setup_sheet(setup_req)


# =============================================================================
# Posts Proxies (delegating to real posts_consolidated_router implementation)
# =============================================================================

from ...routers.posts_consolidated_router import (
    list_posts as real_list_posts,
    get_post as real_get_post,
    PostConfig,
    PostListItem,
)


@router.get("/posts")
def list_posts() -> Dict[str, List[PostListItem]]:
    """List available post processors (proxy to real implementation)."""
    return real_list_posts()


@router.get("/posts/{post_id}")
def get_post(post_id: str) -> PostConfig:
    """Get post processor details (proxy to real implementation)."""
    return real_get_post(post_id)


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
# Logs Proxies (delegating to real logs_router implementation)
# =============================================================================

from .monitoring.logs_router import (
    write_log as real_write_log,
    RunWithSegmentsIn,
)


@router.post("/logs/write")
def write_cam_log(body: RunWithSegmentsIn) -> Dict[str, Any]:
    """Write CAM log entry (proxy to real implementation)."""
    return real_write_log(body)


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
# Adaptive v2 Proxies (delegating to real benchmark_router implementations)
# =============================================================================

from .utility.benchmark_router import (
    BenchReq,
    SpiralReq,
    TrochReq,
    bench as real_bench,
    offset_spiral as real_offset_spiral,
    trochoid_corners as real_trochoid_corners,
)


@router.post("/adaptive2/bench")
def run_adaptive_bench(req: BenchReq) -> Dict[str, Any]:
    """Run adaptive v2 benchmark (proxy to real implementation)."""
    return real_bench(req)


@router.post("/adaptive2/offset_spiral.svg")
def get_offset_spiral_svg(req: SpiralReq):
    """Get offset spiral preview as SVG (proxy to real implementation)."""
    return real_offset_spiral(req)


@router.post("/adaptive2/trochoid_corners.svg")
def get_trochoid_corners_svg(req: TrochReq):
    """Get trochoid corners preview as SVG (proxy to real implementation)."""
    return real_trochoid_corners(req)
