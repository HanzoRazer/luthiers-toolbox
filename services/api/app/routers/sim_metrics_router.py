"""
Simulation metrics endpoint for realistic time/energy estimation.

POST /cam/sim/metrics — Calculate metrics from G-code or moves list
"""

import re
from typing import Any, Dict, List

from fastapi import APIRouter

from ..models.sim_metrics import SegTS, SimMetricsIn, SimMetricsOut
from ..services.sim_energy import simulate_energy, simulate_with_timeseries

router = APIRouter(prefix="/cam/sim", tags=["CAM Simulation"])


def parse_gcode_to_moves(gcode_text: str) -> List[dict]:
    """
    Parse G-code text into moves list.
    
    Extracts G0/G1/G2/G3 commands with X, Y, Z, F parameters.
    
    Args:
        gcode_text: Raw G-code string
    
    Returns:
        List of move dicts with code, x, y, z, f
    """
    moves = []
    current_x = current_y = current_z = 0.0
    current_f = None
    
    for line in gcode_text.splitlines():
        line = line.strip()
        if not line or line.startswith("(") or line.startswith(";"):
            continue
        
        # Extract command (G0, G1, G2, G3)
        match_code = re.match(r"(G0|G1|G2|G3)", line)
        if not match_code:
            continue
        
        code = match_code.group(1)
        
        # Extract coordinates
        x_match = re.search(r"X([-\d.]+)", line)
        y_match = re.search(r"Y([-\d.]+)", line)
        z_match = re.search(r"Z([-\d.]+)", line)
        f_match = re.search(r"F([-\d.]+)", line)
        
        # Update modal values
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


@router.post("/metrics", response_model=SimMetricsOut)
def calculate_metrics(body: SimMetricsIn) -> Dict[str, Any]:
    """
    Calculate realistic time/energy metrics from G-code or moves list.
    
    Supports:
    - Material-specific energy modeling (SCE + splits)
    - Machine-specific feed/accel limits
    - Engagement-based MRR calculations
    - Optional per-segment timeseries
    
    Args:
        body: SimMetricsIn with either gcode_text or moves
    
    Returns:
        SimMetricsOut with energy breakdown and optional timeseries
    """
    
    # Parse input
    if body.gcode_text:
        moves = parse_gcode_to_moves(body.gcode_text)
    elif body.moves:
        moves = [mv.dict() for mv in body.moves]
    else:
        moves = []
    
    if not moves:
        # Empty input → zero metrics
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
    
    # Unpack parameters
    mat = body.material
    caps = body.machine_caps
    eng = body.engagement
    
    # Simulate
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
        
        # Convert timeseries to Pydantic models
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
