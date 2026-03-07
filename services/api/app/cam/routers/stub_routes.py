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
- /fret_slots/* - Fret slot preview (proxied to real fret_slots_cam calculator)
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
# Risk Proxies (delegating to real cam_risk_router implementation)
# =============================================================================

from ...routers.cam_risk_router import get_risk_reports as real_get_risk_reports


@router.get("/risk/reports_index")
def get_risk_reports_index(
    lane: Optional[str] = Query(None),
    preset: Optional[str] = Query(None),
    limit: int = Query(default=100, le=500),
) -> Dict[str, Any]:
    """Get risk reports index (proxy to real implementation)."""
    reports = real_get_risk_reports(
        lane=lane,
        preset=preset,
        limit=limit,
    )
    return {"reports": reports, "total": len(reports)}


# =============================================================================
# Fret Slots Preview (proxied to real fret_slots_cam calculator)
# =============================================================================

from pydantic import BaseModel, Field

from app.instrument_geometry import load_model_spec
from app.instrument_geometry.neck.neck_profiles import FretboardSpec
from app.calculators.fret_slots_cam import generate_fret_slot_toolpaths, compute_cam_statistics
from app.rmos.context import RmosContext


class FretSlotsPreviewRequest(BaseModel):
    """Request for fret slot preview."""
    model_id: str
    fret_count: int = Field(22, ge=1, le=36)
    slot_width_mm: float = Field(0.58, gt=0, le=2.0)
    slot_depth_mm: float = Field(3.0, gt=0, le=10.0)
    bit_diameter_mm: float = Field(0.58, gt=0, le=10.0)
    mode: Optional[str] = Field("standard", pattern="^(standard|fan_fret)$")
    perpendicular_fret: Optional[int] = None
    bass_scale_mm: Optional[float] = None
    treble_scale_mm: Optional[float] = None


class FretSlotOut(BaseModel):
    """Single fret slot data."""
    fret: int
    stringIndex: int = 0  # For now, single slot per fret
    positionMm: float
    widthMm: float
    depthMm: float
    angleRad: Optional[float] = None
    isPerpendicular: bool = False


class RmosMessageOut(BaseModel):
    """RMOS validation message."""
    code: str
    severity: str  # info, warning, error, fatal
    message: str
    context: Dict[str, Any] = Field(default_factory=dict)
    hint: Optional[str] = None


class FretSlotsPreviewResponse(BaseModel):
    """Response for fret slot preview."""
    model_id: str
    fret_count: int
    slots: List[FretSlotOut]
    messages: List[RmosMessageOut]
    statistics: Optional[Dict[str, Any]] = None


@router.post("/fret_slots/preview")
def preview_fret_slots(req: FretSlotsPreviewRequest) -> FretSlotsPreviewResponse:
    """Preview fret slot positions using real calculator."""
    messages: List[RmosMessageOut] = []
    
    # Try to load model spec to get fretboard dimensions
    try:
        model_spec = load_model_spec(req.model_id)
        scale_length_mm = model_spec.scale.scale_length_mm
        # Default fretboard widths if not in spec
        nut_width_mm = 42.0
        heel_width_mm = 56.0
    except Exception as e:
        # Fall back to common defaults
        messages.append(RmosMessageOut(
            code="MODEL_NOT_FOUND",
            severity="warning",
            message=f"Model '{req.model_id}' not found, using defaults",
            context={"model_id": req.model_id},
            hint="Check model registry for available model IDs",
        ))
        scale_length_mm = 648.0  # Fender scale
        nut_width_mm = 42.0
        heel_width_mm = 56.0
    
    # Create fretboard spec
    spec = FretboardSpec(
        nut_width_mm=nut_width_mm,
        heel_width_mm=heel_width_mm,
        scale_length_mm=scale_length_mm,
        fret_count=req.fret_count,
    )
    
    # Create minimal RMOS context (calculator only uses context.materials optionally)
    context = RmosContext(model_id=req.model_id, model_spec={})
    
    # Generate toolpaths
    try:
        toolpaths = generate_fret_slot_toolpaths(
            spec=spec,
            context=context,
            slot_depth_mm=req.slot_depth_mm,
            slot_width_mm=req.slot_width_mm,
        )
        statistics = compute_cam_statistics(toolpaths)
    except Exception as e:
        messages.append(RmosMessageOut(
            code="CALCULATION_ERROR",
            severity="error",
            message=f"Fret slot calculation failed: {str(e)}",
            context={},
        ))
        toolpaths = []
        statistics = None
    
    # Convert toolpaths to response format
    slots = [
        FretSlotOut(
            fret=tp.fret_number,
            positionMm=tp.position_mm,
            widthMm=tp.width_mm,
            depthMm=tp.slot_depth_mm,
            angleRad=tp.angle_rad if hasattr(tp, 'angle_rad') else None,
            isPerpendicular=tp.is_perpendicular if hasattr(tp, 'is_perpendicular') else False,
        )
        for tp in toolpaths
    ]
    
    # Add validation messages for potential issues
    if req.bit_diameter_mm > req.slot_width_mm * 1.5:
        messages.append(RmosMessageOut(
            code="BIT_TOO_LARGE",
            severity="warning",
            message=f"Bit diameter ({req.bit_diameter_mm}mm) exceeds slot width ({req.slot_width_mm}mm)",
            context={"bit_diameter_mm": req.bit_diameter_mm, "slot_width_mm": req.slot_width_mm},
            hint="Use a smaller bit or increase slot width",
        ))
    
    if req.slot_depth_mm > 5.0:
        messages.append(RmosMessageOut(
            code="SLOT_DEPTH_HIGH",
            severity="info",
            message=f"Slot depth ({req.slot_depth_mm}mm) is deeper than typical (2.5-3.5mm)",
            context={"slot_depth_mm": req.slot_depth_mm},
        ))
    
    return FretSlotsPreviewResponse(
        model_id=req.model_id,
        fret_count=req.fret_count,
        slots=slots,
        messages=messages,
        statistics=statistics,
    )


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
