"""
CAM Stub Routes

Provides stub endpoints for CAM frontend paths that don't have backend implementations yet.
These return empty/default responses to prevent 404 errors while features are being built.

Endpoints covered:
- /job-int/* - Job intelligence (proxied to real job_int_log service)
- /job_log/insights/* - WIRED to real job_int_log analysis
- /probe/* - Probe operations (proxied to real setup_router)
- /posts/* - Post processors (proxied to real posts_consolidated_router)
- /bridge/* - Bridge export (proxied to real DXF generator)
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

from fastapi import APIRouter, Response


router = APIRouter(tags=["cam", "stubs"])


# =============================================================================
# Job Intelligence Proxies (using real job_int_log service)
# =============================================================================

from fastapi import Query, HTTPException
from pydantic import BaseModel

from app.services.job_int_log import (
    load_all_job_logs,
    find_job_log_by_run_id,
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
# Job Log Insights (wired to real job_int_log analysis)
# =============================================================================

from typing import Optional


def _compute_job_insights(job: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute job intelligence insights from job log data.

    Analyzes estimated vs actual times and provides recommendations.
    """
    job_id = job.get("run_id") or job.get("job_id") or "unknown"
    job_name = job.get("job_name") or f"Job {job_id[:8]}"
    wood_type = job.get("material") or "Unknown"

    # Get times - estimated from sim_time_s, actual from duration or estimate
    estimated_time_s = job.get("sim_time_s") or 0
    # Actual time: use stored actual_time_s if available, otherwise estimate
    actual_time_s = job.get("actual_time_s")
    if actual_time_s is None:
        # Fallback: estimate actual time from move count with typical timing
        move_count = job.get("sim_move_count") or 0
        # Rough estimate: ~0.1s per move average
        actual_time_s = move_count * 0.1 if move_count > 0 else estimated_time_s

    # Compute time difference percentage
    if estimated_time_s > 0:
        time_diff_pct = round(((actual_time_s - estimated_time_s) / estimated_time_s) * 100, 1)
    else:
        time_diff_pct = 0.0

    # Classification and severity based on time difference
    abs_diff = abs(time_diff_pct)
    if abs_diff <= 5:
        classification = "on_target"
        severity = "ok"
        recommendation = "Job performance is within expected parameters. No adjustments needed."
    elif abs_diff <= 15:
        if time_diff_pct > 0:
            classification = "slightly_slow"
            severity = "ok"
            recommendation = "Job ran slightly slower than estimated. Consider checking tool wear or feed rates."
        else:
            classification = "slightly_fast"
            severity = "ok"
            recommendation = "Job completed faster than estimated. Verify quality meets specifications."
    elif abs_diff <= 30:
        if time_diff_pct > 0:
            classification = "moderately_slow"
            severity = "warn"
            recommendation = "Significant slowdown detected. Review machining parameters, tool condition, and material properties."
        else:
            classification = "moderately_fast"
            severity = "warn"
            recommendation = "Job completed significantly faster. Verify cut quality and consider recalibrating time estimates."
    else:
        if time_diff_pct > 0:
            classification = "significantly_slow"
            severity = "error"
            recommendation = "Critical slowdown. Inspect for tool damage, material issues, or machine problems before next run."
        else:
            classification = "significantly_fast"
            severity = "error"
            recommendation = "Unusually fast completion. Verify all cuts were made correctly and quality is acceptable."

    # Compute review/gate percentages
    # Review threshold: flag for review at 80%+ of expected variance
    # Gate threshold: block at 100%+ deviation
    review_pct = min(100, round((abs_diff / 15) * 80))  # 15% diff = 80% review
    gate_pct = min(100, round((abs_diff / 30) * 100))   # 30% diff = 100% gate

    # Add issue-based adjustments
    issue_count = job.get("sim_issue_count") or 0
    if issue_count > 0:
        review_pct = min(100, review_pct + issue_count * 5)
        if issue_count > 3:
            severity = "error" if severity == "warn" else severity
            recommendation += f" Note: {issue_count} simulation issues detected."

    return {
        "job_id": job_id,
        "job_name": job_name,
        "wood_type": wood_type,
        "actual_time_s": round(actual_time_s, 1),
        "estimated_time_s": round(estimated_time_s, 1),
        "time_diff_pct": time_diff_pct,
        "classification": classification,
        "severity": severity,
        "review_pct": review_pct,
        "gate_pct": gate_pct,
        "recommendation": recommendation,
    }


@router.get("/job_log/insights")
def get_job_insights(
    limit: int = Query(default=50, le=200),
    wood: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
) -> Dict[str, Any]:
    """Get job log insights summary (wired to real job_int_log)."""
    all_logs = load_all_job_logs()

    # Compute insights for each job
    insights = []
    for job in all_logs:
        insight = _compute_job_insights(job)

        # Apply filters
        if wood and insight["wood_type"].lower() != wood.lower():
            continue
        if severity and insight["severity"] != severity:
            continue

        insights.append(insight)

    # Sort by most recent (assuming created_at exists)
    insights.sort(key=lambda x: x.get("job_id", ""), reverse=True)

    return {
        "insights": insights[:limit],
        "total_jobs": len(insights),
    }


@router.get("/job_log/insights/{insight_id}")
def get_job_insight(insight_id: str) -> Dict[str, Any]:
    """Get specific job insight by run_id (wired to real job_int_log)."""
    job = find_job_log_by_run_id(insight_id)

    if not job:
        # Return empty insight structure with error state
        return {
            "job_id": insight_id,
            "job_name": f"Job {insight_id[:8] if len(insight_id) >= 8 else insight_id}",
            "wood_type": "Unknown",
            "actual_time_s": 0,
            "estimated_time_s": 0,
            "time_diff_pct": 0,
            "classification": "unknown",
            "severity": "ok",
            "review_pct": 0,
            "gate_pct": 0,
            "recommendation": f"No job log found for ID: {insight_id}",
        }

    return _compute_job_insights(job)


# =============================================================================
# Probe Proxy (delegating to real setup_router implementation)
# =============================================================================

from pydantic import BaseModel

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
# Bridge DXF Export (real DXF generation from bridge geometry)
# =============================================================================


class BridgeGeometryIn(BaseModel):
    """Bridge geometry payload from frontend BridgeModel."""
    units: str = "mm"
    scaleLength: float
    stringSpread: float
    compTreble: float
    compBass: float
    slotWidth: float
    slotLength: float
    angleDeg: float
    endpoints: Dict[str, Dict[str, float]]
    slotPolygon: List[Dict[str, float]]


class BridgeDxfRequest(BaseModel):
    """Request payload for bridge DXF export."""
    geometry: BridgeGeometryIn
    filename: Optional[str] = None


def _build_bridge_dxf(geom: BridgeGeometryIn, meta: str = "") -> str:
    """
    Build DXF R12 content from bridge geometry.

    Layers:
    - SADDLE: Centerline from treble to bass endpoint
    - SLOT: 4 LINE entities forming closed slot rectangle
    - REFERENCE: Scale length reference line
    """
    out: List[str] = ["0", "SECTION", "2", "ENTITIES"]

    # Saddle centerline (LAYER: SADDLE)
    ep = geom.endpoints
    treble = ep.get("treble", {})
    bass = ep.get("bass", {})
    tx, ty = treble.get("x", 0), treble.get("y", 0)
    bx, by = bass.get("x", 0), bass.get("y", 0)
    out += [
        "0", "LINE", "8", "SADDLE",
        "10", str(tx), "20", str(ty), "30", "0",
        "11", str(bx), "21", str(by), "31", "0",
    ]

    # Slot polygon (LAYER: SLOT)
    poly = geom.slotPolygon
    if len(poly) >= 4:
        for i in range(len(poly)):
            p1, p2 = poly[i], poly[(i + 1) % len(poly)]
            x1, y1 = p1.get("x", 0), p1.get("y", 0)
            x2, y2 = p2.get("x", 0), p2.get("y", 0)
            out += [
                "0", "LINE", "8", "SLOT",
                "10", str(x1), "20", str(y1), "30", "0",
                "11", str(x2), "21", str(y2), "31", "0",
            ]

    # Reference line at scale length position (LAYER: REFERENCE)
    ref_y_min = -geom.stringSpread / 2 - 5
    ref_y_max = geom.stringSpread / 2 + 5
    out += [
        "0", "LINE", "8", "REFERENCE",
        "10", str(geom.scaleLength), "20", str(ref_y_min), "30", "0",
        "11", str(geom.scaleLength), "21", str(ref_y_max), "31", "0",
    ]

    out += ["0", "ENDSEC", "0", "EOF"]
    txt = chr(10).join(out)

    # Prepend metadata comment if provided
    if meta:
        return "999" + chr(10) + meta + chr(10) + txt
    return txt


@router.post("/bridge/export_dxf")
def export_bridge_dxf(body: BridgeDxfRequest) -> Response:
    """
    Export bridge saddle geometry to DXF R12 format.

    Returns a downloadable DXF file with layers:
    - SADDLE: Bridge saddle centerline
    - SLOT: Bridge slot outline (4-sided polygon)
    - REFERENCE: Scale length reference line
    """
    geom = body.geometry

    # Build metadata comment
    meta = f"(BRIDGE;SCALE={geom.scaleLength};SPREAD={geom.stringSpread};CT={geom.compTreble};CB={geom.compBass};UNITS={geom.units})"

    # Generate DXF content
    dxf_content = _build_bridge_dxf(geom, meta)

    # Build safe filename
    filename = body.filename or f"bridge_{geom.scaleLength}_{geom.units}"
    safe_filename = "".join(c for c in filename if c.isalnum() or c in "._-")[:64] or "bridge_export"

    return Response(
        content=dxf_content,
        media_type="application/dxf",
        headers={"Content-Disposition": f'attachment; filename="{safe_filename}.dxf"'},
    )


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
    except Exception as e:  # WP-2: API stub catch-all with structured error response
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
    except Exception as e:  # WP-2: API stub catch-all with structured error response
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
