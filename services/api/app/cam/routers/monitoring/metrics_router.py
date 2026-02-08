"""CAM Metrics Router"""

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
from ....routers.machine_router import get_profile
from ....routers.material_router import get_material
from ....util.names import safe_stem

router = APIRouter()


class EnergyIn(BaseModel):
    """Request body for energy analysis."""
    moves: List[Dict[str, Any]] = Field(..., description="Toolpath moves from /plan endpoint")
    material_id: str = Field(default="maple_hard", description="Material ID from material database")
    tool_d: float = Field(..., description="Tool diameter in mm")
    stepover: float = Field(..., description="Stepover ratio (0..1)")
    stepdown: float = Field(..., description="Depth per pass in mm")
    job_name: Optional[str] = Field(default=None, description="Optional job identifier")


@router.post("/energy")
def energy(body: EnergyIn) -> Dict[str, Any]:
    """Calculate cutting energy and heat distribution for a toolpath."""
    # Get material properties
    mat = get_material(body.material_id)

    # Calculate energy breakdown
    out = energy_breakdown(
        moves=body.moves,
        sce_j_per_mm3=float(mat["sce_j_per_mm3"]),
        tool_d_mm=float(body.tool_d),
        stepover=float(body.stepover),
        stepdown=float(body.stepdown),
        heat_partition=mat.get("heat_partition", {"chip": 0.7, "tool": 0.2, "work": 0.1})
    )

    # Add metadata
    out["material"] = mat["id"]
    out["job_name"] = body.job_name

    return out


@router.post("/energy_csv")
def energy_csv(body: EnergyIn) -> StreamingResponse:
    """Export per-segment energy breakdown as CSV."""
    # Get material properties
    mat = get_material(body.material_id)

    # Calculate energy breakdown
    out = energy_breakdown(
        moves=body.moves,
        sce_j_per_mm3=float(mat["sce_j_per_mm3"]),
        tool_d_mm=float(body.tool_d),
        stepover=float(body.stepover),
        stepdown=float(body.stepdown),
        heat_partition=mat.get("heat_partition", {"chip": 0.7, "tool": 0.2, "work": 0.1})
    )

    # Generate safe filename stem
    stem = safe_stem(body.job_name, prefix="energy")

    # Build CSV in memory
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

    # Convert to bytes for streaming
    data = io.BytesIO(buf.getvalue().encode("utf-8"))

    return StreamingResponse(
        iter([data.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{stem}.csv"'}
    )


# ========== Heat Timeseries ==========

class HeatIn(BaseModel):
    """Input for heat timeseries: power (J/s) over time."""
    moves: List[Dict[str, Any]]
    machine_profile_id: str
    material_id: str = "maple_hard"
    tool_d: float
    stepover: float
    stepdown: float
    bins: int = Field(default=120, ge=10, le=2000)


@router.post("/heat_timeseries")
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


# ========== Bottleneck CSV Export ==========

class BottleneckCsvIn(BaseModel):
    """Input for bottleneck CSV export."""
    moves: List[Dict[str, Any]]
    machine_profile_id: str
    job_name: str = "pocket"


@router.post("/bottleneck_csv")
def bottleneck_csv_export(body: BottleneckCsvIn) -> StreamingResponse:
    """Export per-segment bottleneck data as CSV."""
    prof = get_profile(body.machine_profile_id)

    # Safe filename
    stem = f"bottleneck_{safe_stem(body.job_name)}"

    # Generate CSV
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["idx", "code", "x", "y", "len_mm", "limit"])

    for i, m in enumerate(body.moves):
        code = m.get("code", "")
        x = m.get("x", "")
        y = m.get("y", "")

        # Calculate length and determine limit
        len_mm = 0.0
        limit = "none"

        if code in ("G1", "G2", "G3"):
            # Get previous position
            prev_x = body.moves[i-1].get("x", 0.0) if i > 0 else 0.0
            prev_y = body.moves[i-1].get("y", 0.0) if i > 0 else 0.0

            if isinstance(x, (int, float)) and isinstance(y, (int, float)):
                dx = float(x) - float(prev_x)
                dy = float(y) - float(prev_y)
                len_mm = (dx*dx + dy*dy)**0.5

                # Determine bottleneck (simplified from M.1.1 logic)
                if len_mm > 0:
                    feed_f = m.get("f", 0.0)
                    feed_cap = prof.get("feed_xy", 1200.0)
                    accel = prof.get("accel", 500.0)
                    jerk = prof.get("jerk", 1000.0)

                    # Check feed cap
                    if feed_f >= feed_cap * 0.95:
                        limit = "feed_cap"
                    # Check if accel-limited (short move)
                    elif len_mm < (feed_f/60.0)**2 / (2*accel):
                        limit = "accel"
                    # Check if jerk-limited (very short move)
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

    # Convert to bytes for streaming
    data = io.BytesIO(buf.getvalue().encode("utf-8"))

    return StreamingResponse(
        iter([data.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{stem}.csv"'}
    )



# WP-3: Thermal report endpoints extracted to metrics_thermal.py
from .metrics_thermal import router as _thermal_router  # noqa: E402
from .metrics_thermal import (  # noqa: E402  # re-export for type consumers
    ThermalBudget as ThermalBudget,
    ThermalReportIn as ThermalReportIn,
)

router.include_router(_thermal_router)

