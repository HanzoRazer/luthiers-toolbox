"""
Module M.2: What-If Optimizer
Grid search optimizer for feed/stepover/RPM with chipload targeting.
Honors machine profile limits and tool constraints.
"""

import math
from typing import Dict, Any, Tuple, List
from .time_estimator_v2 import estimate_cycle_time_v2


def _safe(val: float, lo: float, hi: float) -> float:
    """Clamp value to range [lo, hi]."""
    return max(lo, min(hi, val))


def _chipload_ok(
    feed_mm_min: float,
    rpm: float,
    flutes: int,
    target_mm: float,
    tol: float
) -> bool:
    """Check if chipload is within tolerance of target.
    
    Args:
        feed_mm_min: Feed rate in mm/min
        rpm: Spindle speed in RPM
        flutes: Number of cutting flutes
        target_mm: Target chipload in mm/tooth
        tol: Tolerance in mm/tooth
    
    Returns:
        True if chipload is within [target-tol, target+tol]
    """
    if rpm <= 1e-6 or flutes < 1:
        return True
    
    chip = feed_mm_min / (rpm * flutes)  # mm/tooth
    return (target_mm - tol) <= chip <= (target_mm + tol)


def _rpm_for_chipload(
    feed_mm_min: float,
    target_mm: float,
    flutes: int,
    rpm_lo: float,
    rpm_hi: float
) -> float:
    """Calculate RPM to achieve target chipload, clamped to bounds.
    
    Args:
        feed_mm_min: Feed rate in mm/min
        target_mm: Target chipload in mm/tooth
        flutes: Number of cutting flutes
        rpm_lo: Minimum RPM
        rpm_hi: Maximum RPM
    
    Returns:
        Clamped RPM value
    """
    if target_mm <= 0 or flutes < 1:
        return rpm_hi
    
    rpm = feed_mm_min / (target_mm * flutes)
    return _safe(rpm, rpm_lo, rpm_hi)


def optimize_feed_stepover(
    moves: List[Dict[str, Any]],
    profile: Dict[str, Any],
    z_total: float,
    stepdown: float,
    safe_z: float,
    bounds: Dict[str, Tuple[float, float]],
    tool: Dict[str, Any],
    objective: str = "time",  # reserved for future: time, energy, etc.
    grid: Tuple[int, int] = (6, 6),
    tolerance_chip_mm: float = 0.02,
) -> Dict[str, Any]:
    """
    Grid search optimization for feed/stepover with chipload-targeted RPM.
    
    Args:
        moves: List of G-code moves from /plan
        profile: Machine profile dict
        z_total: Total pocket depth (negative)
        stepdown: Depth per pass (positive)
        safe_z: Safe retract height (positive)
        bounds: Dict with keys 'feed', 'stepover', 'rpm' → (lo, hi) tuples
        tool: Dict with 'flutes' and 'chipload_target_mm'
        objective: Optimization objective (currently only 'time')
        grid: (feed_steps, stepover_steps) tuple
        tolerance_chip_mm: Chipload tolerance in mm/tooth
    
    Returns:
        Dict with:
            best: {feed_mm_min, stepover, rpm, time_s, score}
            neighbors: List of 6 nearest samples by param L2 distance
            grid: {feed, stepover, rpm} bounds and step counts
    """
    feed_lo, feed_hi = bounds.get("feed", (300, 8000))
    stp_lo, stp_hi = bounds.get("stepover", (0.2, 0.9))  # 0..1
    rpm_lo, rpm_hi = bounds.get("rpm", (6000, 24000))
    
    flutes = int(tool.get("flutes", 2))
    chip_t = float(tool.get("chipload_target_mm", 0.05))

    # Profile feed cap guard
    feed_cap = float(profile.get("limits", {}).get("feed_xy", feed_hi))
    feed_hi = min(feed_hi, feed_cap)

    gF, gS = grid
    best = None
    samples = []

    for i in range(gF):
        f = feed_lo + (feed_hi - feed_lo) * (i / max(1, gF - 1))
        
        for j in range(gS):
            s = stp_lo + (stp_hi - stp_lo) * (j / max(1, gS - 1))  # 0..1
            
            # Set candidate RPM to hit chipload target, within bounds
            rpm = _rpm_for_chipload(f, chip_t, flutes, rpm_lo, rpm_hi)

            # Clone moves with this feed applied
            # (Simple: set F on G1/2/3; slowdowns handled by estimator)
            mv = []
            for m in moves:
                mm = dict(m)
                if mm.get("code") in ("G1", "G2", "G3"):
                    mm["f"] = f
                mv.append(mm)

            # Estimate cycle time
            est = estimate_cycle_time_v2(
                mv, profile,
                z_total=z_total,
                stepdown=stepdown,
                safe_z=safe_z
            )
            t = est["time_s"]

            # Check chipload constraint
            ok_chip = _chipload_ok(f, rpm, flutes, chip_t, tolerance_chip_mm)
            penalty = 0.0 if ok_chip else 0.08 * t  # 8% penalty if outside tolerance

            score = t + penalty
            
            itm = {
                "feed_mm_min": round(f, 1),
                "stepover": round(s, 3),
                "rpm": int(rpm),
                "time_s": t,
                "score": score
            }
            samples.append(itm)
            
            if (best is None) or (score < best["score"]):
                best = dict(itm)

    # Sensitivity: pick 6 neighbors closest in param space to best
    def dist(a, b):
        return (a["feed_mm_min"] - b["feed_mm_min"]) ** 2 + \
               (a["stepover"] - b["stepover"]) ** 2
    
    nb = sorted(samples, key=lambda x: dist(x, best))[0:6]

    return {
        "best": best,
        "neighbors": nb,
        "grid": {
            "feed": [feed_lo, feed_hi, gF],
            "stepover": [stp_lo, stp_hi, gS],
            "rpm": [rpm_lo, rpm_hi]
        }
    }
