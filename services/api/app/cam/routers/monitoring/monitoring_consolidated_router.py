"""
CAM Monitoring Routers (Consolidated)
======================================

CAM metrics and logging.

Consolidated from:
    - logs_router.py (2 routes)
    - metrics_router.py (4 routes + includes thermal_router)

Total: 6 routes under /api/cam/monitoring

LANE: UTILITY (metrics/logging operations)
Reference: docs/OPERATION_EXECUTION_GOVERNANCE_v1.md

Endpoints:
    Logs (/logs):
        POST /write            - Log a CAM run with per-segment details
        GET  /caps/{machine_id} - Get bottleneck distribution

    Metrics (/metrics):
        POST /energy           - Calculate cutting energy
        POST /energy_csv       - Export energy as CSV
        POST /heat_timeseries  - Calculate heat over time
        POST /bottleneck_csv   - Export bottlenecks as CSV
        POST /thermal_report_md    - Generate thermal report (from thermal)
        POST /thermal_report_bundle - Export report bundle (from thermal)
"""

from __future__ import annotations

import csv
import io
import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from zipfile import ZipFile

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ...energy_model import energy_breakdown
from ...heat_timeseries import heat_timeseries
from ....routers.machines_consolidated_router import get_profile
from ....business.router import get_material
from ....util.names import safe_stem
from ....telemetry.cam_logs import fetch_caps_by_machine, insert_run, insert_segments


# ===========================================================================
# Sub-routers with prefixes
# ===========================================================================

logs_router = APIRouter()
metrics_router = APIRouter()


# ===========================================================================
# LOGS MODELS
# ===========================================================================

class RunIn(BaseModel):
    """Metadata for a single CAM run (plan or execution)."""
    job_name: Optional[str] = None
    machine_id: str
    material_id: str
    tool_d: float
    stepover: float  # 0..1
    stepdown: float
    post_id: Optional[str] = None
    feed_xy: Optional[float] = None
    rpm: Optional[int] = None
    est_time_s: Optional[float] = None  # Predicted time (jerk-aware)
    act_time_s: Optional[float] = None  # Actual time if known
    notes: Optional[str] = None


class SegmentIn(BaseModel):
    """Per-segment telemetry (G-code line details)."""
    idx: int
    code: str  # G0, G1, G2, G3
    x: Optional[float] = None
    y: Optional[float] = None
    len_mm: Optional[float] = None
    limit: Optional[str] = None  # feed_cap|accel|jerk|none
    slowdown: Optional[float] = None  # meta.slowdown (engagement penalty)
    trochoid: Optional[bool] = None  # Trochoidal arc flag
    radius_mm: Optional[float] = None  # Arc radius for G2/G3
    feed_f: Optional[float] = None  # Stamped feed on line


class RunWithSegmentsIn(BaseModel):
    """Complete run log (run metadata + all segments)."""
    run: RunIn
    segments: List[SegmentIn]


# ===========================================================================
# LOGS ENDPOINTS
# ===========================================================================

@logs_router.post("/write")
def write_log(body: RunWithSegmentsIn) -> Dict[str, Any]:
    """Log a CAM run with per-segment details."""
    rid = insert_run(body.run.model_dump())
    insert_segments(rid, [s.model_dump() for s in body.segments])
    return {"status": "ok", "run_id": rid}


@logs_router.get("/caps/{machine_id}")
def caps(machine_id: str) -> Dict[str, Any]:
    """Get bottleneck distribution (feed_cap/accel/jerk/none counts) for a machine."""
    rows = fetch_caps_by_machine(machine_id)
    return {r["limit"]: r["c"] for r in rows}


# ===========================================================================
# METRICS MODELS
# ===========================================================================

class EnergyIn(BaseModel):
    """Request body for energy analysis."""
    moves: List[Dict[str, Any]] = Field(..., description="Toolpath moves from /plan endpoint")
    material_id: str = Field(default="maple_hard", description="Material ID from material database")
    tool_d: float = Field(..., description="Tool diameter in mm")
    stepover: float = Field(..., description="Stepover ratio (0..1)")
    stepdown: float = Field(..., description="Depth per pass in mm")
    job_name: Optional[str] = Field(default=None, description="Optional job identifier")


class HeatIn(BaseModel):
    """Input for heat timeseries: power (J/s) over time."""
    moves: List[Dict[str, Any]]
    machine_profile_id: str
    material_id: str = "maple_hard"
    tool_d: float
    stepover: float
    stepdown: float
    bins: int = Field(default=120, ge=10, le=2000)


class BottleneckCsvIn(BaseModel):
    """Input for bottleneck CSV export."""
    moves: List[Dict[str, Any]]
    machine_profile_id: str
    job_name: str = "pocket"


# ===========================================================================
# METRICS ENDPOINTS
# ===========================================================================

@metrics_router.post("/energy")
def energy(body: EnergyIn) -> Dict[str, Any]:
    """Calculate cutting energy and heat distribution for a toolpath."""
    mat = get_material(body.material_id)
    out = energy_breakdown(
        moves=body.moves,
        sce_j_per_mm3=float(mat["sce_j_per_mm3"]),
        tool_d_mm=float(body.tool_d),
        stepover=float(body.stepover),
        stepdown=float(body.stepdown),
        heat_partition=mat.get("heat_partition", {"chip": 0.7, "tool": 0.2, "work": 0.1})
    )
    out["material"] = mat["id"]
    out["job_name"] = body.job_name
    return out


@metrics_router.post("/energy_csv")
def energy_csv(body: EnergyIn) -> StreamingResponse:
    """Export per-segment energy breakdown as CSV."""
    mat = get_material(body.material_id)
    out = energy_breakdown(
        moves=body.moves,
        sce_j_per_mm3=float(mat["sce_j_per_mm3"]),
        tool_d_mm=float(body.tool_d),
        stepover=float(body.stepover),
        stepdown=float(body.stepdown),
        heat_partition=mat.get("heat_partition", {"chip": 0.7, "tool": 0.2, "work": 0.1})
    )

    stem = safe_stem(body.job_name, prefix="energy")
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["idx", "code", "len_mm", "vol_mm3", "energy_j", "cum_energy_j"])

    cumulative = 0.0
    for seg in out["segments"]:
        cumulative += float(seg["energy_j"])
        w.writerow([
            seg["idx"],
            seg.get("code", ""),
            f'{seg.get("len_mm", 0):.4f}',
            f'{seg["vol_mm3"]:.4f}',
            f'{seg["energy_j"]:.4f}',
            f'{cumulative:.4f}'
        ])

    data = io.BytesIO(buf.getvalue().encode("utf-8"))
    return StreamingResponse(
        iter([data.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{stem}.csv"'}
    )


@metrics_router.post("/heat_timeseries")
def heat_ts(body: HeatIn) -> Dict[str, Any]:
    """Calculate heat generation over time: power (J/s) in chip, tool, work."""
    mat = get_material(body.material_id)
    prof = get_profile(body.machine_profile_id)

    out = heat_timeseries(
        body.moves, prof,
        tool_d_mm=float(body.tool_d),
        stepover=float(body.stepover),
        stepdown=float(body.stepdown),
        sce_j_per_mm3=float(mat["sce_j_per_mm3"]),
        heat_partition=mat.get("heat_partition", {"chip": 0.7, "tool": 0.2, "work": 0.1}),
        bins=int(body.bins)
    )

    out["material"] = mat["id"]
    out["machine_profile_id"] = body.machine_profile_id
    return out


@metrics_router.post("/bottleneck_csv")
def bottleneck_csv_export(body: BottleneckCsvIn) -> StreamingResponse:
    """Export per-segment bottleneck data as CSV."""
    prof = get_profile(body.machine_profile_id)
    stem = f"bottleneck_{safe_stem(body.job_name)}"

    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["idx", "code", "x", "y", "len_mm", "limit"])

    for i, m in enumerate(body.moves):
        code = m.get("code", "")
        x = m.get("x", "")
        y = m.get("y", "")
        len_mm = 0.0
        limit = "none"

        if code in ("G1", "G2", "G3"):
            prev_x = body.moves[i-1].get("x", 0.0) if i > 0 else 0.0
            prev_y = body.moves[i-1].get("y", 0.0) if i > 0 else 0.0

            if isinstance(x, (int, float)) and isinstance(y, (int, float)):
                dx = float(x) - float(prev_x)
                dy = float(y) - float(prev_y)
                len_mm = (dx*dx + dy*dy)**0.5

                if len_mm > 0:
                    feed_f = m.get("f", 0.0)
                    feed_cap = prof.get("feed_xy", 1200.0)
                    accel = prof.get("accel", 500.0)
                    jerk = prof.get("jerk", 1000.0)

                    if feed_f >= feed_cap * 0.95:
                        limit = "feed_cap"
                    elif len_mm < (feed_f/60.0)**2 / (2*accel):
                        limit = "accel"
                    elif len_mm < (feed_f/60.0)**3 / (jerk * accel):
                        limit = "jerk"

        w.writerow([
            str(i),
            code,
            f'{x:.4f}' if isinstance(x, (int, float)) else "",
            f'{y:.4f}' if isinstance(y, (int, float)) else "",
            f'{len_mm:.4f}',
            limit
        ])

    data = io.BytesIO(buf.getvalue().encode("utf-8"))
    return StreamingResponse(
        iter([data.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{stem}.csv"'}
    )


# ===========================================================================
# Include thermal router (from metrics_thermal.py)
# ===========================================================================

from .metrics_thermal import router as _thermal_router
from .metrics_thermal import ThermalBudget, ThermalReportIn

metrics_router.include_router(_thermal_router)


# ===========================================================================
# Aggregate Router
# ===========================================================================

router = APIRouter()
router.include_router(metrics_router, prefix="/metrics")
router.include_router(logs_router, prefix="/logs")

__all__ = ["router", "metrics_router", "logs_router", "ThermalBudget", "ThermalReportIn"]
