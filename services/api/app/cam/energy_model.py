"""
Energy & Heat Model for M.3.

Calculates cutting energy and heat generation based on:
- Material removal volume (proxy: length × stepover × stepdown)
- Specific cutting energy (sce_j_per_mm3) from material database
- Heat partition ratios (chip/tool/work)
"""

import math
from typing import List, Dict, Any


def _vol_removed_for_move(m: Dict[str, Any], tool_d_mm: float, stepover: float, stepdown: float) -> float:
    """
    Calculate volume removed for a single move (light proxy).
    
    Volume = length × effective_width × stepdown
    where effective_width = stepover × tool_diameter
    
    Trochoids have reduced engagement (~90% of normal).
    
    Args:
        m: Move dict with x, y, code, optional _len_mm and meta.trochoid
        tool_d_mm: Tool diameter in mm
        stepover: Stepover ratio (0..1)
        stepdown: Depth per pass in mm
    
    Returns:
        Volume removed in mm³
    """
    if not ("x" in m and "y" in m and m.get("code") in ("G1", "G2", "G3")):
        return 0.0
    
    length = float(m.get("_len_mm", 0.0))
    width = stepover * tool_d_mm
    
    # Trochoids have reduced engagement
    k = 0.9 if m.get("meta", {}).get("trochoid") else 1.0
    
    return max(0.0, length * width * stepdown * k)


def _length_annotate(moves: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Annotate moves with _len_mm field (XY distance from previous point).
    
    Args:
        moves: List of move dicts
    
    Returns:
        Annotated moves with _len_mm field added
    """
    out = []
    last = None
    
    for m in moves:
        mm = dict(m)
        if "x" in mm and "y" in mm:
            p = (mm["x"], mm["y"])
            if last is None:
                mm["_len_mm"] = 0.0
            else:
                mm["_len_mm"] = math.hypot(p[0] - last[0], p[1] - last[1])
            last = p
        out.append(mm)
    
    return out


def energy_breakdown(
    moves: List[Dict[str, Any]],
    sce_j_per_mm3: float,
    tool_d_mm: float,
    stepover: float,
    stepdown: float,
    heat_partition: Dict[str, float]
) -> Dict[str, Any]:
    """
    Calculate energy breakdown for a toolpath.
    
    Args:
        moves: List of G-code moves (dicts with x, y, code, meta)
        sce_j_per_mm3: Specific cutting energy in J/mm³ (from material)
        tool_d_mm: Tool diameter in mm
        stepover: Stepover ratio (0..1)
        stepdown: Depth per pass in mm
        heat_partition: Heat distribution {"chip": 0.7, "tool": 0.2, "work": 0.1}
    
    Returns:
        {
            "totals": {
                "volume_mm3": float,
                "energy_j": float,
                "heat": {"chip_j": float, "tool_j": float, "work_j": float}
            },
            "segments": [
                {"idx": int, "code": str, "len_mm": float, "vol_mm3": float, "energy_j": float}
            ]
        }
    """
    moves = _length_annotate(moves)
    
    total_vol = 0.0
    total_e = 0.0
    per = []
    
    for m in moves:
        v = _vol_removed_for_move(m, tool_d_mm, stepover, stepdown)
        e = v * sce_j_per_mm3
        total_vol += v
        total_e += e
        
        if e > 0:
            per.append({
                "idx": len(per),
                "code": m.get("code", ""),
                "len_mm": m.get("_len_mm", 0.0),
                "vol_mm3": v,
                "energy_j": e
            })
    
    # Calculate heat distribution
    chip = total_e * heat_partition.get("chip", 0.7)
    tool = total_e * heat_partition.get("tool", 0.2)
    work = total_e * heat_partition.get("work", 0.1)
    
    return {
        "totals": {
            "volume_mm3": total_vol,
            "energy_j": total_e,
            "heat": {
                "chip_j": chip,
                "tool_j": tool,
                "work_j": work
            }
        },
        "segments": per
    }
