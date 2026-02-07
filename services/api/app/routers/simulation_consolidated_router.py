"""
Consolidated Simulation Router - G-code simulation and metrics.

Consolidates:
- cam_sim_router.py (JSON-based simulation)
- cam_simulate_router.py (file upload simulation)
- sim_metrics_router.py (energy/time metrics)
- cam/routers/simulation/gcode_sim_router.py (duplicate of cam_sim_router)

Endpoints:
- POST /sim/gcode - Simulate G-code from JSON body
- POST /sim/upload - Simulate G-code from file upload
- POST /sim/metrics - Calculate energy/time metrics
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, Form, HTTPException, Response, UploadFile
from pydantic import BaseModel, Field

from .sim_validate import (
    DEFAULT_ACCEL,
    DEFAULT_CLEAR_Z,
    DEFAULT_ENVELOPE,
    csv_export,
    simulate,
)
from ..models.sim_metrics import SegTS, SimMetricsIn, SimMetricsOut
from ..services.sim_energy import simulate_energy, simulate_with_timeseries


router = APIRouter(tags=["CAM Simulation"])


# ============================================================================
# Models
# ============================================================================

class SimGcodeInput(BaseModel):
    """Input for JSON-based G-code simulation."""
    gcode: str = Field(..., description="Raw G-code to simulate")
    as_csv: Optional[bool] = Field(False, description="Return CSV format")
    accel: Optional[float] = Field(DEFAULT_ACCEL, description="Acceleration mm/s²")
    clearance_z: Optional[float] = Field(DEFAULT_CLEAR_Z, description="Clearance Z height")
    envelope: Optional[Dict[str, tuple]] = Field(DEFAULT_ENVELOPE, description="Machine envelope")


class SimUploadResponse(BaseModel):
    """Response for file upload simulation."""
    ok: bool
    units: str
    move_count: int
    length_mm: float
    time_s: float
    moves: List[Dict[str, Any]]
    issues: List[str]


# ============================================================================
# G-code Parsing Utilities
# ============================================================================

def _parse_gcode_basic(text: str) -> List[Dict[str, Any]]:
    """
    Basic G-code parser for backplot preview.
    Detects G0/G1 motion codes and XYZ coordinates.
    """
    lines = text.splitlines()
    moves: List[Dict[str, Any]] = []
    x = y = z = f = None
    pattern = re.compile(r"([XYZF])([-+]?\d*\.?\d+)")

    for line in lines:
        code = line.strip().split(" ")[0].upper()
        if not code or code.startswith("("):
            continue

        if code in {"G0", "G00", "G1", "G01"}:
            params = {m[0]: float(m[1]) for m in pattern.findall(line)}
            x = params.get("X", x)
            y = params.get("Y", y)
            z = params.get("Z", z)
            f = params.get("F", f)
            moves.append({"code": code[:2], "x": x, "y": y, "z": z, "f": f})

    return moves


def _parse_gcode_for_metrics(gcode_text: str) -> List[dict]:
    """
    Parse G-code for metrics calculation.
    Extracts G0/G1/G2/G3 commands with X, Y, Z, F parameters.
    """
    moves = []
    current_x = current_y = current_z = 0.0
    current_f = None

    for line in gcode_text.splitlines():
        line = line.strip()
        if not line or line.startswith("(") or line.startswith(";"):
            continue

        match_code = re.match(r"(G0|G1|G2|G3)", line)
        if not match_code:
            continue

        code = match_code.group(1)

        x_match = re.search(r"X([-\d.]+)", line)
        y_match = re.search(r"Y([-\d.]+)", line)
        z_match = re.search(r"Z([-\d.]+)", line)
        f_match = re.search(r"F([-\d.]+)", line)

        if x_match:
            current_x = float(x_match.group(1))
        if y_match:
            current_y = float(y_match.group(1))
        if z_match:
            current_z = float(z_match.group(1))
        if f_match:
            current_f = float(f_match.group(1))

        moves.append({
            "code": code,
            "x": current_x,
            "y": current_y,
            "z": current_z,
            "f": current_f
        })

    return moves


# ============================================================================
# Simulation Endpoints
# ============================================================================

@router.post("/gcode")
def simulate_gcode_json(body: SimGcodeInput) -> Response:
    """
    Simulate G-code from JSON body.

    Returns simulation results with moves, issues, and optional CSV export.
    Summary and modal state are included in response headers.
    """
    sim = simulate(
        body.gcode,
        accel=body.accel or DEFAULT_ACCEL,
        clearance_z=body.clearance_z or DEFAULT_CLEAR_Z,
        env=body.envelope or DEFAULT_ENVELOPE
    )

    if body.as_csv:
        data = csv_export(sim)
        return Response(
            content=data,
            media_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="simulation.csv"'}
        )

    headers = {
        "X-CAM-Summary": json.dumps(sim['summary']),
        "X-CAM-Modal": json.dumps(sim['modal'])
    }
    return Response(
        content=json.dumps({'issues': sim['issues'], 'moves': sim['moves']}),
        media_type="application/json",
        headers=headers
    )


@router.post("/upload", response_model=SimUploadResponse)
async def simulate_gcode_upload(
    file: UploadFile = File(...),
    units: str = Form("mm")
) -> SimUploadResponse:
    """
    Simulate G-code from file upload.

    Parses basic motion commands and calculates path statistics.
    """
    try:
        text = (await file.read()).decode("utf-8", errors="ignore")
    except HTTPException:  # WP-1: pass through HTTPException
        raise
    except Exception as exc:  # WP-1: governance catch-all — HTTP endpoint
        raise HTTPException(status_code=400, detail=f"Failed to read file: {exc}") from exc

    moves = _parse_gcode_basic(text)
    if not moves:
        raise HTTPException(status_code=400, detail="No motion commands found in file")

    # Calculate path length
    length_mm = 0.0
    last = None
    for m in moves:
        if last and None not in (last.get("x"), last.get("y"), m.get("x"), m.get("y")):
            dx = m["x"] - last["x"]
            dy = m["y"] - last["y"]
            length_mm += (dx ** 2 + dy ** 2) ** 0.5
        last = m

    return SimUploadResponse(
        ok=True,
        units=units,
        move_count=len(moves),
        length_mm=length_mm,
        time_s=round(length_mm / 100.0, 2),  # Naive 100 mm/s estimate
        moves=moves,
        issues=[]
    )


@router.post("/metrics", response_model=SimMetricsOut)
def calculate_metrics(body: SimMetricsIn) -> SimMetricsOut:
    """
    Calculate realistic time/energy metrics from G-code or moves list.

    Supports:
    - Material-specific energy modeling (SCE + splits)
    - Machine-specific feed/accel limits
    - Engagement-based MRR calculations
    - Optional per-segment timeseries
    """
    # Parse input
    if body.gcode_text:
        moves = _parse_gcode_for_metrics(body.gcode_text)
    elif body.moves:
        moves = [mv.dict() for mv in body.moves]
    else:
        moves = []

    if not moves:
        return SimMetricsOut(
            length_cutting_mm=0.0,
            length_rapid_mm=0.0,
            time_s=0.0,
            volume_mm3=0.0,
            mrr_mm3_min=0.0,
            power_avg_w=0.0,
            energy_total_j=0.0,
            energy_chip_j=0.0,
            energy_tool_j=0.0,
            energy_workpiece_j=0.0,
            timeseries=[]
        )

    mat = body.material
    caps = body.machine_caps
    eng = body.engagement

    if body.include_timeseries:
        summary, ts_list = simulate_with_timeseries(
            moves,
            sce_j_per_mm3=mat.sce_j_per_mm3,
            feed_xy_max=caps.feed_xy_max,
            rapid_xy=caps.rapid_xy,
            accel_xy=caps.accel_xy,
            stepover_frac=eng.stepover_frac,
            stepdown_mm=eng.stepdown_mm,
            engagement_pct=eng.engagement_pct,
            tool_d_mm=body.tool_d_mm
        )
        timeseries = [SegTS(**ts) for ts in ts_list]

        return SimMetricsOut(
            length_cutting_mm=summary["length_cutting_mm"],
            length_rapid_mm=summary["length_rapid_mm"],
            time_s=summary["time_s"],
            volume_mm3=summary["volume_mm3"],
            mrr_mm3_min=summary["mrr_mm3_min"],
            power_avg_w=summary["power_avg_w"],
            energy_total_j=summary["energy_total_j"],
            energy_chip_j=summary.get("energy_chip_j", 0.0),
            energy_tool_j=summary.get("energy_tool_j", 0.0),
            energy_workpiece_j=summary.get("energy_workpiece_j", 0.0),
            timeseries=timeseries
        )
    else:
        summary = simulate_energy(
            moves,
            sce_j_per_mm3=mat.sce_j_per_mm3,
            energy_split_chip=mat.energy_split_chip,
            energy_split_tool=mat.energy_split_tool,
            energy_split_workpiece=mat.energy_split_workpiece,
            feed_xy_max=caps.feed_xy_max,
            rapid_xy=caps.rapid_xy,
            accel_xy=caps.accel_xy,
            stepover_frac=eng.stepover_frac,
            stepdown_mm=eng.stepdown_mm,
            engagement_pct=eng.engagement_pct,
            tool_d_mm=body.tool_d_mm
        )

        return SimMetricsOut(
            length_cutting_mm=summary["length_cutting_mm"],
            length_rapid_mm=summary["length_rapid_mm"],
            time_s=summary["time_s"],
            volume_mm3=summary["volume_mm3"],
            mrr_mm3_min=summary["mrr_mm3_min"],
            power_avg_w=summary["power_avg_w"],
            energy_total_j=summary["energy_total_j"],
            energy_chip_j=summary["energy_chip_j"],
            energy_tool_j=summary["energy_tool_j"],
            energy_workpiece_j=summary["energy_workpiece_j"],
            timeseries=[]
        )


# ============================================================================
# Legacy Compatibility Endpoints
# ============================================================================

@router.post("/simulate_gcode")
def simulate_gcode_legacy(body: SimGcodeInput) -> Response:
    """
    Legacy endpoint - redirects to /gcode.

    Maintained for backward compatibility with existing clients.
    """
    return simulate_gcode_json(body)
