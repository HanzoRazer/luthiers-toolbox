"""
Heat Timeseries Calculator for M.3 Energy & Heat Model.

Calculates power (J/s) over time by combining:
- Per-segment energy from energy_model.py
- Per-segment time from jerk-aware dynamics
- Binned timeline for visualization

This enables heat-over-time strip charts showing chip/tool/work
heat generation throughout the cutting operation.
"""

import math
from typing import List, Dict, Any


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


def _seg_time_mm(m: Dict[str, Any], accel: float, jerk: float, rapid_mm_s: float, feed_cap_mm_min: float) -> float:
    """
    Calculate segment time with jerk-aware dynamics (light proxy).
    
    Args:
        m: Move dict with code, _len_mm, f, meta
        accel: Acceleration (mm/s²)
        jerk: Jerk (mm/s³)
        rapid_mm_s: Rapid feed rate (mm/s)
        feed_cap_mm_min: Feed cap (mm/min)
    
    Returns:
        Segment time in seconds
    """
    code = m.get("code", "")
    d = float(m.get("_len_mm", 0.0))
    if d <= 1e-9:
        return 0.0
    
    # Target velocity
    if code == "G0":
        v = rapid_mm_s
    else:
        base_f = float(m.get("f", feed_cap_mm_min))
        scale = float(m.get("meta", {}).get("slowdown", 1.0))
        if m.get("meta", {}).get("trochoid") or code in ("G2", "G3"):
            scale *= 0.9
        v = min(feed_cap_mm_min, base_f * scale) / 60.0
    
    # Light jerk-limited time (same shape as v2 estimator)
    a = max(1.0, accel)
    j = max(1.0, jerk)
    t_a = a / j
    s_a = 0.5 * a * (t_a ** 2)
    v_reach = math.sqrt(max(0.0, 2 * a * max(0.0, d - 2 * s_a)))
    
    if v_reach < v * 0.9:
        return 2.0 * math.sqrt(d / max(1e-6, a))
    
    s_cruise = max(0.0, d - 2 * s_a)
    return (2 * t_a) + (s_cruise / max(1e-6, v))


def _energy_per_segment(m: Dict[str, Any], tool_d_mm: float, stepover: float, stepdown: float, sce_j_per_mm3: float) -> float:
    """
    Calculate energy removed for a single segment.
    
    Args:
        m: Move dict with code, x, y, _len_mm, meta
        tool_d_mm: Tool diameter in mm
        stepover: Stepover ratio (0..1)
        stepdown: Depth per pass in mm
        sce_j_per_mm3: Specific cutting energy (J/mm³)
    
    Returns:
        Energy in joules
    """
    if not (m.get("code") in ("G1", "G2", "G3") and "x" in m and "y" in m):
        return 0.0
    
    w = stepover * tool_d_mm
    k = 0.9 if m.get("meta", {}).get("trochoid") else 1.0
    vol = float(m.get("_len_mm", 0.0)) * w * stepdown * k
    return vol * sce_j_per_mm3


def heat_timeseries(
    moves: List[Dict[str, Any]],
    profile: Dict[str, Any],
    tool_d_mm: float,
    stepover: float,
    stepdown: float,
    sce_j_per_mm3: float,
    heat_partition: Dict[str, float],
    bins: int = 120
) -> Dict[str, Any]:
    """
    Calculate heat generation over time as power (J/s) timeseries.
    
    Args:
        moves: Toolpath moves from /plan endpoint
        profile: Machine profile with limits (accel, jerk, rapid, feed_xy)
        tool_d_mm: Tool diameter in mm
        stepover: Stepover ratio (0..1)
        stepdown: Depth per pass in mm
        sce_j_per_mm3: Specific cutting energy (J/mm³)
        heat_partition: Heat distribution {"chip": 0.7, "tool": 0.2, "work": 0.1}
        bins: Number of time bins for visualization (10-2000)
    
    Returns:
        {
            "t": [time_0, time_1, ...],           # Time axis (seconds)
            "p_chip": [power_0, power_1, ...],    # Chip heat (J/s)
            "p_tool": [power_0, power_1, ...],    # Tool heat (J/s)
            "p_work": [power_0, power_1, ...],    # Work heat (J/s)
            "total_s": total_time                  # Total time (seconds)
        }
    """
    limits = profile.get("limits", {})
    accel = float(limits.get("accel", 800))
    jerk = float(limits.get("jerk", 2000))
    rapid = float(limits.get("rapid", 3000)) / 60.0
    feedc = float(limits.get("feed_xy", 1200))
    
    moves = _length_annotate(moves)
    
    # Calculate per-segment energy (J) and time (s)
    seg_e = []
    seg_t = []
    total_t = 0.0
    
    for m in moves:
        e = _energy_per_segment(m, tool_d_mm, stepover, stepdown, sce_j_per_mm3)
        t = _seg_time_mm(m, accel, jerk, rapid, feedc)
        seg_e.append(e)
        seg_t.append(t)
        total_t += t
    
    if total_t <= 1e-9:
        return {"t": [], "p_chip": [], "p_tool": [], "p_work": [], "total_s": 0.0}
    
    # Spread each segment's energy over its time window, then bin to uniform timeline
    T = total_t
    B = max(10, int(bins))
    p_raw = [0.0] * B
    
    # Map cumulative time to bin index
    c = 0.0
    for e, t in zip(seg_e, seg_t):
        if t <= 1e-9:
            continue
        
        p = e / t  # Power (W = J/s) over this segment
        
        # Distribute evenly across bins overlapped by [c, c+t]
        start = int((c / T) * B)
        end = int(((c + t) / T) * B)
        if end == start:
            end = min(B - 1, start + 1)
        
        for bi in range(max(0, start), min(B, end + 1)):
            p_raw[bi] += p
        
        c += t
    
    # Partition heat
    chip_k = float(heat_partition.get("chip", 0.7))
    tool_k = float(heat_partition.get("tool", 0.2))
    work_k = float(heat_partition.get("work", 0.1))
    
    p_chip = [v * chip_k for v in p_raw]
    p_tool = [v * tool_k for v in p_raw]
    p_work = [v * work_k for v in p_raw]
    t_axis = [(i / (B - 1)) * T for i in range(B)]
    
    return {
        "t": t_axis,
        "p_chip": p_chip,
        "p_tool": p_tool,
        "p_work": p_work,
        "total_s": T
    }
