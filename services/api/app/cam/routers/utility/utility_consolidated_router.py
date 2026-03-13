"""Consolidated CAM Utility Router.

Merged from:
- backup_router.py (3 routes)
- benchmark_router.py (3 routes)
- compare_router.py (1 route)
- optimization_router.py (2 routes)
- polygon_router.py (1 route)
- settings_router.py (3 routes)

Total: 13 routes for CAM utilities.
"""
from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel, Field

from ...polygon_offset_n17 import toolpath_offsets
from ...time_estimator_v2 import estimate_cycle_time_v2
from ...whatif_opt import optimize_feed_stepover
from ....routers.machines_consolidated_router import get_profile
from ....cam_core.feeds_speeds import calculate_feed_plan
from ....services.cam_backup_service import BACKUP_DIR, ensure_dir, write_snapshot
from ....services.job_int_log import find_job_log_by_run_id
from ....services.jobint_artifacts import extract_jobint_artifacts
from ....services.pipeline_preset_store import PipelinePresetStore
from ....util.adaptive_geom import (
    inward_offset_spiral_rect,
    rect_offset_path,
    svg_polyline,
    trochoid_corner_loops,
)
from ....util.gcode_emit_advanced import emit_xy_with_arcs
from ....util.gcode_emit_basic import emit_xy_polyline_nc

logger = logging.getLogger(__name__)

# Sub-routers with prefixes
backup_router = APIRouter(prefix="/backup")
benchmark_router = APIRouter()  # No prefix
compare_router = APIRouter(prefix="/compare")
optimization_router = APIRouter(prefix="/opt")
polygon_router = APIRouter()  # No prefix
settings_router = APIRouter(prefix="/settings")


# =============================================================================
# BACKUP ROUTES (/backup/*)
# =============================================================================


@backup_router.post("/snapshot")
async def snapshot_now() -> Dict[str, Any]:
    """Force an immediate backup snapshot."""
    p = write_snapshot()
    return {"status": "ok", "path": str(p)}


@backup_router.get("/list")
async def list_backups() -> List[Dict[str, Any]]:
    """List all available backup files."""
    ensure_dir()
    items: List[Dict[str, Any]] = []
    for p in sorted(BACKUP_DIR.glob("*.json")):
        items.append({"name": p.name, "bytes": p.stat().st_size})
    return items


@backup_router.get("/download/{name}")
async def download_backup(name: str) -> Response:
    """Download a specific backup file."""
    ensure_dir()
    safe = Path(name).name
    path = BACKUP_DIR / safe
    if not path.exists():
        raise HTTPException(status_code=404, detail="not found")
    data = path.read_bytes()
    return Response(
        content=data,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{safe}"'},
    )


# =============================================================================
# BENCHMARK ROUTES
# =============================================================================


class SpiralReq(BaseModel):
    width: float = 100.0
    height: float = 60.0
    tool_dia: float = 6.0
    stepover: float = 2.4
    corner_fillet: float = 0.0


@benchmark_router.post("/offset_spiral.svg", response_class=Response)
def offset_spiral(req: SpiralReq) -> Response:
    """Generate inward offset spiral toolpath for rectangular pocket (SVG)."""
    if req.tool_dia <= 0:
        raise HTTPException(status_code=422, detail="Tool diameter must be positive")
    if req.width <= 0 or req.height <= 0:
        raise HTTPException(status_code=422, detail="Width and height must be positive")
    if req.stepover < 0:
        raise HTTPException(status_code=422, detail="Stepover cannot be negative")
    pts = inward_offset_spiral_rect(
        req.width, req.height, req.tool_dia, req.stepover, req.corner_fillet
    )
    return Response(content=svg_polyline(pts, stroke="purple"), media_type="image/svg+xml")


class TrochReq(BaseModel):
    width: float = 100.0
    height: float = 60.0
    tool_dia: float = 6.0
    loop_pitch: float = 2.5
    amp: float = 0.4


@benchmark_router.post("/trochoid_corners.svg", response_class=Response)
def trochoid_corners(req: TrochReq) -> Response:
    """Generate trochoidal loops around rectangle corners (SVG)."""
    if req.tool_dia <= 0:
        raise HTTPException(status_code=422, detail="Tool diameter must be positive")
    if req.width <= 0 or req.height <= 0:
        raise HTTPException(status_code=422, detail="Width and height must be positive")
    if req.loop_pitch <= 0:
        raise HTTPException(status_code=422, detail="Loop pitch must be positive")
    outer = rect_offset_path(req.width, req.height, 0.0)
    pts = trochoid_corner_loops(outer, req.tool_dia, req.loop_pitch, req.amp)
    return Response(content=svg_polyline(pts, stroke="teal"), media_type="image/svg+xml")


class BenchReq(BaseModel):
    width: float = 100.0
    height: float = 60.0
    tool_dia: float = 6.0
    stepover: float = 2.4
    runs: int = 20


@benchmark_router.post("/bench")
def bench(req: BenchReq) -> Dict[str, Any]:
    """Run performance benchmark on inward offset spiral algorithm."""
    if req.tool_dia <= 0:
        raise HTTPException(status_code=422, detail="Tool diameter must be positive")
    if req.width <= 0 or req.height <= 0:
        raise HTTPException(status_code=422, detail="Width and height must be positive")
    if req.stepover < 0:
        raise HTTPException(status_code=422, detail="Stepover cannot be negative")
    if req.runs <= 0:
        raise HTTPException(status_code=422, detail="Runs must be positive")

    run_times = []
    for _ in range(req.runs):
        t0 = time.perf_counter()
        _ = inward_offset_spiral_rect(req.width, req.height, req.tool_dia, req.stepover, 0.6)
        t1 = time.perf_counter()
        run_times.append((t1 - t0) * 1000.0)

    total_ms = sum(run_times)
    avg_ms = total_ms / req.runs
    return {
        "runs": req.runs,
        "total_ms": round(total_ms, 3),
        "avg_ms": round(avg_ms, 3),
        "width": req.width,
        "height": req.height,
        "tool_dia": req.tool_dia,
        "stepover": req.stepover,
    }


# =============================================================================
# COMPARE ROUTE
# =============================================================================


@compare_router.get("/diff")
def compare_job_diff(baseline: str = Query(...), compare: str = Query(...)) -> Dict[str, Any]:
    """Compare two job runs by ID and return toolpath/geometry diffs."""
    job_base = find_job_log_by_run_id(baseline)
    job_comp = find_job_log_by_run_id(compare)
    if not job_base or not job_comp:
        raise HTTPException(status_code=404, detail="One or both job IDs not found")

    base_geom, base_plan, base_moves, base_path = extract_jobint_artifacts(job_base)
    comp_geom, comp_plan, comp_moves, comp_path = extract_jobint_artifacts(job_comp)

    def get_stats(job_dict: Dict[str, Any]) -> Dict[str, Any]:
        stats = job_dict.get("stats", {})
        return {
            "length": stats.get("length_mm"),
            "time": stats.get("time_s"),
            "retracts": stats.get("retract_count"),
        }

    base_stats = get_stats(job_base)
    comp_stats = get_stats(job_comp)
    delta = {
        "length": (comp_stats["length"] or 0) - (base_stats["length"] or 0),
        "time": (comp_stats["time"] or 0) - (base_stats["time"] or 0),
        "retracts": (comp_stats["retracts"] or 0) - (base_stats["retracts"] or 0),
    }

    return {
        "baseline": {
            "id": baseline,
            "toolpath": base_moves,
            "geometry": base_geom,
            "stats": base_stats,
            "meta": job_base.get("meta", {}),
        },
        "compare": {
            "id": compare,
            "toolpath": comp_moves,
            "geometry": comp_geom,
            "stats": comp_stats,
            "meta": job_comp.get("meta", {}),
        },
        "delta": delta,
    }


# =============================================================================
# OPTIMIZATION ROUTES
# =============================================================================


class LoopIn(BaseModel):
    pts: List[List[float]]


class OptIn(BaseModel):
    moves: Optional[List[Dict[str, Any]]] = None
    loops: Optional[List[LoopIn]] = None
    machine_profile_id: str
    z_total: float = -3.0
    stepdown: float = 1.0
    safe_z: float = 5.0
    bounds: Dict[str, List[float]] = Field(
        default={"feed": [600, 9000], "stepover": [0.25, 0.85], "rpm": [8000, 24000]}
    )
    tool: Dict[str, Any] = Field(default={"flutes": 2, "chipload_target_mm": 0.05})
    grid: List[int] = Field(default=[6, 6])


@optimization_router.post("/what_if")
def what_if_opt(body: OptIn) -> Dict[str, Any]:
    """What-if optimizer for feed/stepover/RPM parameters."""
    profile = get_profile(body.machine_profile_id)
    if body.moves is None:
        raise HTTPException(400, "M.2 expects prebuilt moves; call /plan first.")

    res = optimize_feed_stepover(
        body.moves,
        profile,
        z_total=body.z_total,
        stepdown=body.stepdown,
        safe_z=body.safe_z,
        bounds={k: tuple(v) for k, v in body.bounds.items()},
        tool=body.tool,
        grid=tuple(body.grid),
    )
    baseline = estimate_cycle_time_v2(
        body.moves, profile, z_total=body.z_total, stepdown=body.stepdown, safe_z=body.safe_z
    )
    return {"baseline": baseline, "opt": res}


class FeedsSpeedsRequest(BaseModel):
    tool_id: str
    material: str
    strategy: str = "roughing"
    flutes: Optional[int] = None
    diameter_mm: Optional[float] = None
    stickout_mm: Optional[float] = None


class FeedsSpeedsResponse(BaseModel):
    tool_id: str
    material: str
    strategy: str
    feed_xy: float
    feed_z: float
    rpm: int
    stepdown_mm: float
    stepover_mm: float
    chipload_mm: float
    heat_rating: str
    deflection_mm: float
    notes: str


@optimization_router.post("/feeds-speeds", response_model=FeedsSpeedsResponse)
def calculate_feeds_speeds(body: FeedsSpeedsRequest) -> FeedsSpeedsResponse:
    """Calculate optimal feeds and speeds for tool/material/strategy."""
    tool: Dict[str, Any] = {"id": body.tool_id}
    if body.flutes is not None:
        tool["flutes"] = body.flutes
    if body.diameter_mm is not None:
        tool["diameter_mm"] = body.diameter_mm
    if body.stickout_mm is not None:
        tool["stickout_mm"] = body.stickout_mm
    result = calculate_feed_plan(tool, body.material, body.strategy)
    return FeedsSpeedsResponse(**result)


# =============================================================================
# POLYGON OFFSET ROUTE
# =============================================================================

Pt = Tuple[float, float]


class PolyOffsetReq(BaseModel):
    polygon: List[Tuple[float, float]]
    tool_dia: float = 6.0
    stepover: float = 2.0
    inward: bool = True
    z: float = -1.5
    safe_z: float = 5.0
    units: str = "mm"
    feed: float = 600.0
    feed_arc: Optional[float] = None
    feed_floor: Optional[float] = None
    join_type: str = "round"
    arc_tolerance: float = 0.25
    link_mode: str = "arc"
    link_radius: float = 1.0
    spindle: int = 12000
    post: Optional[str] = None


@polygon_router.post("/polygon_offset.nc", response_class=Response)
def polygon_offset(req: PolyOffsetReq) -> Response:
    """Generate G-code for polygon offsetting with multiple passes."""
    paths = toolpath_offsets(
        req.polygon, req.tool_dia, req.stepover, req.inward, req.join_type, req.arc_tolerance
    )
    if not paths:
        return Response(
            content="(Error: No valid offset paths generated)\nM30\n", media_type="text/plain"
        )

    if req.link_mode == "arc":
        nc = emit_xy_with_arcs(
            paths,
            z=req.z,
            safe_z=req.safe_z,
            units=req.units,
            feed=req.feed,
            feed_arc=req.feed_arc,
            feed_floor=req.feed_floor,
            link_radius=req.link_radius,
        )
    else:
        nc = emit_xy_polyline_nc(
            paths, z=req.z, safe_z=req.safe_z, units=req.units, feed=req.feed, spindle=req.spindle
        )
    return Response(content=nc, media_type="text/plain")


# =============================================================================
# SETTINGS ROUTES
# =============================================================================


class MachineLimits(BaseModel):
    min_x: Optional[float] = None
    max_x: Optional[float] = None
    min_y: Optional[float] = None
    max_y: Optional[float] = None
    min_z: Optional[float] = None
    max_z: Optional[float] = None


class MachineCamDefaults(BaseModel):
    tool_d: Optional[float] = None
    stepover: Optional[float] = None
    stepdown: Optional[float] = None
    feed_xy: Optional[float] = None
    safe_z: Optional[float] = None
    z_rough: Optional[float] = None


class MachineIn(BaseModel):
    id: str
    name: str
    controller: Optional[str] = None
    description: Optional[str] = None
    units: Optional[str] = Field(default="mm", pattern="^(mm|inch|in)$")
    limits: Optional[MachineLimits] = None
    feed_xy: Optional[float] = None
    rapid: Optional[float] = None
    accel: Optional[float] = None
    camDefaults: Optional[MachineCamDefaults] = None


class LineNumberCfg(BaseModel):
    enabled: Optional[bool] = None
    start: Optional[int] = None
    step: Optional[int] = None
    prefix: Optional[str] = None


class PostOptions(BaseModel):
    use_percent: Optional[bool] = None
    use_o_word: Optional[bool] = None
    supports_arcs: Optional[bool] = None


class PostIn(BaseModel):
    id: str
    name: str
    dialect: Optional[str] = None
    description: Optional[str] = None
    line_numbers: Optional[LineNumberCfg] = None
    options: Optional[PostOptions] = None
    header_template: Optional[str] = None
    footer_template: Optional[str] = None
    canned_cycles: Optional[dict] = None


class PresetIn(BaseModel):
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    spec: dict


class CamBackupIn(BaseModel):
    version: Optional[str] = None
    machines: List[MachineIn] = Field(default_factory=list)
    posts: List[PostIn] = Field(default_factory=list)
    pipeline_presets: List[PresetIn] = Field(default_factory=list)


@settings_router.get("/summary")
def get_settings_summary() -> Dict[str, Any]:
    """Return counts of machines, posts, and pipeline presets."""
    machines_count = 0
    posts_count = 0
    pipeline_presets_count = 0

    try:
        from ....services.machine_store import MachineStore
        ms = MachineStore()
        machines_count = len(ms.list_all())
    except (ImportError, OSError):
        pass

    try:
        from ....services.post_store import PostStore
        ps = PostStore()
        posts_count = len(ps.list_all())
    except (ImportError, OSError):
        pass

    try:
        pps = PipelinePresetStore()
        pipeline_presets_count = len(pps.list())
    except (ImportError, OSError, AttributeError):
        pass

    return {
        "machines_count": machines_count,
        "posts_count": posts_count,
        "pipeline_presets_count": pipeline_presets_count,
    }


@settings_router.get("/export")
async def cam_settings_export() -> Dict[str, Any]:
    """Export full CAM configuration for backup/sharing."""
    machines: List[Dict[str, Any]] = []
    posts: List[Dict[str, Any]] = []
    presets: List[Dict[str, Any]] = []

    try:
        from ....services.machine_store import MachineStore
        m_store = MachineStore()
        machines = list(m_store.list_all() or [])
    except (ImportError, OSError):
        machines = []

    try:
        from ....services.post_store import PostStore
        p_store = PostStore()
        posts = list(p_store.list_all() or [])
    except (ImportError, OSError):
        posts = []

    try:
        pps = PipelinePresetStore()
        presets = list(pps.list() or [])
    except (ImportError, OSError, AttributeError):
        presets = []

    return {
        "version": "A_N",
        "machines": machines,
        "posts": posts,
        "pipeline_presets": presets,
    }


@settings_router.post("/import")
async def cam_settings_import(
    payload: CamBackupIn, overwrite: bool = Query(False)
) -> Dict[str, Any]:
    """Import full CAM configuration (backup restore)."""
    report: Dict[str, Any] = {
        "imported": {"machines": 0, "posts": 0, "pipeline_presets": 0},
        "skipped": {"machines": 0, "posts": 0, "pipeline_presets": 0},
        "errors": [],
    }

    def add_error(kind: str, item_id: str, exc: Exception) -> None:
        report["errors"].append({"kind": kind, "id": item_id, "error": str(exc)})

    try:
        from ....services.machine_store import MachineStore
        mstore = MachineStore()
        existing_ids = {m.get("id") for m in (mstore.list_all() or [])}
        for m in payload.machines:
            try:
                if (m.id in existing_ids) and not overwrite:
                    report["skipped"]["machines"] += 1
                    continue
                mstore.upsert(m.model_dump(exclude_none=True))
                report["imported"]["machines"] += 1
            except (ValueError, TypeError, KeyError, OSError) as exc:
                logger.warning("Machine import failed for '%s': %s", m.id, exc)
                add_error("machine", m.id, exc)
    except (ImportError, OSError) as exc:
        add_error("machine_store", "_", exc)

    try:
        from ....services.post_store import PostStore
        pstore = PostStore()
        existing_ids = {p.get("id") for p in (pstore.list_all() or [])}
        for p in payload.posts:
            try:
                if (p.id in existing_ids) and not overwrite:
                    report["skipped"]["posts"] += 1
                    continue
                pstore.upsert(p.model_dump(exclude_none=True))
                report["imported"]["posts"] += 1
            except (ValueError, TypeError, KeyError, OSError) as exc:
                logger.warning("Post import failed for '%s': %s", p.id, exc)
                add_error("post", p.id, exc)
    except (ImportError, OSError) as exc:
        add_error("post_store", "_", exc)

    try:
        pps = PipelinePresetStore()
        existing = {pr.get("id") for pr in (pps.list() or [])}
        for pr in payload.pipeline_presets:
            try:
                pid = pr.id or pps.new_id(pr.name)
                if (pid in existing) and not overwrite:
                    report["skipped"]["pipeline_presets"] += 1
                    continue
                pps.upsert({**pr.model_dump(exclude_none=True), "id": pid})
                report["imported"]["pipeline_presets"] += 1
            except (ValueError, TypeError, KeyError, OSError) as exc:
                logger.warning("Pipeline preset import failed for '%s': %s", pr.id or pr.name, exc)
                add_error("pipeline_preset", pr.id or pr.name, exc)
    except (ImportError, OSError) as exc:
        add_error("preset_store", "_", exc)

    return report


# =============================================================================
# AGGREGATE ROUTER
# =============================================================================

router = APIRouter()
router.include_router(backup_router)
router.include_router(benchmark_router)
router.include_router(compare_router)
router.include_router(optimization_router)
router.include_router(polygon_router)
router.include_router(settings_router)

__all__ = [
    "router",
    "backup_router",
    "benchmark_router",
    "compare_router",
    "optimization_router",
    "polygon_router",
    "settings_router",
]
