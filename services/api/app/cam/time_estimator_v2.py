"""
Module M.2: Cycle Time Estimator v2
Enhanced predictive time estimation with multi-pass accounting and Z logistics.
Builds on M.1 jerk-aware dynamics.
"""

import math
from typing import List, Dict, Any, Tuple


def _length_xy(moves: List[Dict[str, Any]]) -> float:
    """Calculate total XY path length from moves."""
    L = 0.0
    last = None
    for m in moves:
        if 'x' in m and 'y' in m:
            p = (m['x'], m['y'])
            if last:
                L += math.hypot(p[0] - last[0], p[1] - last[1])
            last = p
    return L


def _passes_from_stepdown(total_depth: float, stepdown: float) -> int:
    """Calculate number of Z passes needed."""
    if stepdown <= 1e-6:
        return 1
    n = max(1, int(math.ceil(abs(total_depth) / stepdown)))
    return n


def _engagement_scale(m: Dict[str, Any]) -> float:
    """
    Lightweight proxy for cutter engagement: 1.0 normal; reduce for arcs/trochoids/tight corners.
    Uses m.meta.slowdown if present; otherwise small penalty for G2/G3.
    
    Returns:
        Scale factor 0.0-1.0 for feed rate adjustment
    """
    meta = m.get("meta", {})
    
    # Prefer existing slowdown annotation from adaptive feed override
    if "slowdown" in meta:
        return float(meta["slowdown"])
    
    # Trochoid arcs have higher engagement
    if meta.get("trochoid"):
        return 0.85
    
    # Regular arcs have slightly lower engagement
    if m.get("code") in ("G2", "G3"):
        return 0.92
    
    return 1.0


def estimate_cycle_time_v2(
    moves: List[Dict[str, Any]],
    profile: Dict[str, Any],
    z_total: float,
    stepdown: float,
    safe_z: float,
    plunge_f: float = 300.0,  # mm/min
) -> Dict[str, Any]:
    """
    Enhanced cycle time estimator v2.
    
    Improvements over v1:
    - Multi-pass stepdown accounting
    - Retract/plunge & safe-Z hop costs
    - Corner blending optimization
    - Per-segment engagement proxy → dynamic feed cap
    
    Args:
        moves: List of G-code moves (G0/G1/G2/G3 with x,y,z,f)
        profile: Machine profile dict with limits {accel, jerk, rapid, feed_xy, corner_tol_mm}
        z_total: Total depth of pocket (negative, e.g., -3.0 mm)
        stepdown: Depth per pass (positive, e.g., 1.5 mm)
        safe_z: Safe retract height above work (positive, e.g., 5.0 mm)
        plunge_f: Plunge feed rate in mm/min (default: 300)
    
    Returns:
        Dict with:
            time_s: Total estimated cycle time (seconds)
            xy_time_one_pass_s: XY cutting time for single pass
            passes: Number of Z passes
            hop_count: Total number of safe-Z hops
            caps: Bottleneck histogram {feed_cap, accel, jerk, none}
    """
    limits = profile.get("limits", {})
    accel = float(limits.get("accel", 800))
    jerk = float(limits.get("jerk", 2000))
    rapid = float(limits.get("rapid", 3000)) / 60.0  # mm/s
    feed_cap = float(limits.get("feed_xy", 1200))
    corner_tol = float(limits.get("corner_tol_mm", 0.2))

    # Per-segment time function (jerk-limited trapezoid; simplified from M.1)
    def seg_time(d: float, v_target: float) -> Tuple[float, str]:
        """Calculate segment time with jerk-aware acceleration.
        
        Returns:
            (time_s, limiter) where limiter ∈ {"accel", "jerk", "none"}
        """
        if d <= 1e-9 or v_target <= 1e-9:
            return 0.0, "none"
        
        a = max(1.0, accel)
        j = max(1.0, jerk)
        t_a = a / j  # jerk-limited acceleration time
        s_a = 0.5 * a * (t_a ** 2)  # distance during accel
        
        v_reach = math.sqrt(max(0.0, 2 * a * max(0.0, d - 2 * s_a)))
        
        if v_reach < v_target * 0.9:
            # Can't reach target speed → short move
            lim = "jerk" if j < a * 2 else "accel"
            return 2.0 * math.sqrt(d / max(1e-6, a)), lim
        
        s_cruise = max(0.0, d - 2 * s_a)
        return (2 * t_a) + (s_cruise / max(1e-6, v_target)), "none"

    # Walk moves, sum XY time with engagement scaling & feed caps
    t_xy = 0.0
    last = None
    caps = {"feed_cap": 0, "accel": 0, "jerk": 0, "none": 0}
    
    for m in moves:
        if m.get("code") in ("G0", "G1", "G2", "G3") and 'x' in m and 'y' in m:
            p = (m['x'], m['y'])
            d = 0.0 if last is None else math.hypot(p[0] - last[0], p[1] - last[1])
            last = p
            
            if m["code"] == "G0":
                # Rapid traverse
                dt, lim = seg_time(d, rapid)
                t_xy += dt
                caps[lim] += 1
                continue

            # Cutting motion at feed
            base_f = float(m.get("f", feed_cap))  # mm/min
            scale = _engagement_scale(m)  # 0..1
            v_req = min(feed_cap, base_f * scale) / 60.0  # mm/s
            
            dt, lim = seg_time(d, v_req)
            
            # If we're at feed cap limit due to scaling, record feed_cap
            if v_req * 60.0 >= feed_cap - 1e-6 and scale < 1.0:
                caps["feed_cap"] += 1
            else:
                caps[lim] += 1
            
            t_xy += dt

    # Corner blending bonus (controller path smoothing reduces time)
    t_xy *= (1.0 - min(0.1, corner_tol / 10.0))

    # Z pass accounting
    passes = _passes_from_stepdown(z_total, stepdown)
    
    # Retract/plunge heuristic cost per pass
    plunge_v = max(1e-6, plunge_f / 60.0)  # mm/s
    
    # Estimate safe hops: ~1 hop per 200mm of XY path
    L = _length_xy(moves)
    hops = max(1, int(L / 200.0))
    
    hop_h = abs(safe_z)  # mm of vertical per hop
    t_hops = passes * hops * ((hop_h / rapid) + (hop_h / plunge_v))

    total = t_xy * passes + t_hops
    
    return {
        "time_s": round(total, 2),
        "xy_time_one_pass_s": round(t_xy, 2),
        "passes": passes,
        "hop_count": hops * passes,
        "caps": caps
    }
