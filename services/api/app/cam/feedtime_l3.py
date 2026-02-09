"""Jerk-Aware Time Estimator (L.3 Physics-Based Motion Planning)"""
import math
from typing import List, Dict, Any, Tuple

# =============================================================================
# VALIDATION CONSTANTS
# =============================================================================

# Acceleration bounds (mm/s²)
MIN_ACCEL_MM_S2: float = 50.0      # Minimum acceleration (conservative hobby machines)
MAX_ACCEL_MM_S2: float = 5000.0    # Maximum acceleration (high-speed machining centers)

# Jerk bounds (mm/s³) - controls acceleration ramp smoothness
MIN_JERK_MM_S3: float = 100.0      # Minimum jerk (gentle s-curves)
MAX_JERK_MM_S3: float = 50000.0    # Maximum jerk (aggressive ramps)

# Feed rate bounds (mm/min)
MIN_FEED_RATE_MM_MIN: float = 1.0       # Minimum feed rate (prevent division by zero)
MAX_FEED_RATE_MM_MIN: float = 10000.0   # Maximum feed rate (sanity check)

# =============================================================================
# JERK-AWARE TIME ESTIMATION
# =============================================================================


def jerk_aware_time(
    moves: List[Dict[str, Any]],
    feed_xy: float,        # mm/min nominal cutting feed
    rapid_f: float,        # mm/min rapid traverse
    accel: float,          # mm/s² acceleration limit
    jerk: float,           # mm/s³ s-curve jerk limit
    corner_tol_mm: float,  # allowed corner rounding (blending tolerance)
) -> float:
    """Conservative time estimator using jerk-limited motion profile."""
    # Validate parameters
    if feed_xy <= 0 or feed_xy > MAX_FEED_RATE_MM_MIN:
        raise ValueError(
            f"feed_xy must be between {MIN_FEED_RATE_MM_MIN} and {MAX_FEED_RATE_MM_MIN} mm/min, "
            f"got {feed_xy}"
        )
    if rapid_f <= 0 or rapid_f > MAX_FEED_RATE_MM_MIN:
        raise ValueError(
            f"rapid_f must be between {MIN_FEED_RATE_MM_MIN} and {MAX_FEED_RATE_MM_MIN} mm/min, "
            f"got {rapid_f}"
        )
    if not (MIN_ACCEL_MM_S2 <= accel <= MAX_ACCEL_MM_S2):
        raise ValueError(
            f"accel must be between {MIN_ACCEL_MM_S2} and {MAX_ACCEL_MM_S2} mm/s², "
            f"got {accel}"
        )
    if not (MIN_JERK_MM_S3 <= jerk <= MAX_JERK_MM_S3):
        raise ValueError(
            f"jerk must be between {MIN_JERK_MM_S3} and {MAX_JERK_MM_S3} mm/s³, "
            f"got {jerk}"
        )
    if corner_tol_mm < 0 or corner_tol_mm > 10.0:
        raise ValueError(f"corner_tol_mm must be between 0 and 10 mm, got {corner_tol_mm}")
    
    # Convert feed rates to mm/s
    v_nom = max(1e-6, feed_xy / 60.0)
    v_rapid = max(1e-6, rapid_f / 60.0)

    total_time = 0.0
    last_xy = None

    def seg_time(distance: float, v_target: float) -> float:
        """
        Calculate time for a single segment using jerk-limited trapezoid profile.
        
        Args:
            distance: Segment length in mm
            v_target: Target velocity in mm/s
        
        Returns:
            Time in seconds
        """
        if distance <= 1e-6 or v_target <= 1e-6:
            return 0.0

        # Ensure sane limits (clamp to valid range)
        a = max(MIN_ACCEL_MM_S2, min(MAX_ACCEL_MM_S2, accel))
        j = max(MIN_JERK_MM_S3, min(MAX_JERK_MM_S3, jerk))

        # Time to reach full acceleration with jerk limit (s-curve ramp)
        t_a = a / j
        
        # Distance covered during acceleration ramp
        s_a = 0.5 * a * (t_a ** 2)

        # Maximum reachable velocity given distance constraint
        # (assumes symmetric accel/decel ramps)
        v_reach = min(v_target, math.sqrt(2 * a * max(0.0, distance - 2 * s_a)))

        # Short segment: triangular velocity profile (can't reach full speed)
        if v_reach < v_target * 0.9:
            # Triangular profile with jerk ramps (simplified approximation)
            return 2.0 * math.sqrt(distance / max(1e-6, a))

        # Long segment: trapezoid profile (accel → cruise → decel)
        s_cruise = max(0.0, distance - 2 * s_a)
        t_cruise = s_cruise / max(1e-6, v_target)
        return (2 * t_a) + t_cruise

    # Process each move
    for m in moves:
        code = m.get("code")

        # Rapid moves (G0)
        if code == "G0":
            nx = m.get("x", None)
            ny = m.get("y", None)
            nz = m.get("z", None)
            
            if last_xy and (nx is not None and ny is not None):
                d = math.hypot(nx - last_xy[0], ny - last_xy[1])
            else:
                d = 0.0
            
            total_time += seg_time(d, v_rapid)
            
            if nx is not None and ny is not None:
                last_xy = (nx, ny)
            continue

        # Cutting moves (G1/G2/G3)
        if code in ("G1", "G2", "G3"):
            nx = m.get("x", None)
            ny = m.get("y", None)
            nz = m.get("z", None)

            if last_xy and (nx is not None and ny is not None):
                d = math.hypot(nx - last_xy[0], ny - last_xy[1])
            else:
                d = 0.0

            # Use move's feed rate if specified, else default
            v = (m.get("f") or feed_xy) / 60.0

            # Penalize arcs & trochoids: reduce steady-state by 10%
            # (higher cutting forces due to radial engagement)
            if code in ("G2", "G3") or m.get("meta", {}).get("trochoid"):
                v *= 0.9

            total_time += seg_time(d, v)

            if nx is not None and ny is not None:
                last_xy = (nx, ny)
            continue

    # Corner blending benefit (crude approximation):
    # Larger corner tolerance allows more path smoothing, reducing stop-and-go
    # Reduce total time by up to 10% based on tolerance
    blending_factor = 1.0 - min(0.1, corner_tol_mm / 10.0)
    total_time *= blending_factor

    return total_time


# =============================================================================
# FEED RATE CALCULATION (PENALTIES AND LIMITS)
# =============================================================================

def effective_feed_for_segment(
    code: str,
    base_f_mm_min: float,
    profile: Dict[str, Any],
    is_trochoid: bool,
    curvature_slowdown: float,
) -> float:
    """Compute effective segment feed rate with machine limits and slowdown factors."""
    limits = profile.get("limits", {})
    feed_xy_cap = float(limits.get("feed_xy", base_f_mm_min))
    
    # Start with machine cap (hard limit)
    v = min(base_f_mm_min, feed_xy_cap)

    # Apply curvature/slowdown scaling (from L.2/L.3)
    v *= max(0.1, curvature_slowdown)  # Clamp to 10% minimum

    # Trochoids and arcs: additional 10% safety reduction
    if is_trochoid or code in ("G2", "G3"):
        v *= 0.9

    return v


# =============================================================================
# PROFILE-BASED TIME ESTIMATION (MACHINE-AWARE)
# =============================================================================

def jerk_aware_time_with_profile(
    moves: List[Dict[str, Any]],
    profile: Dict[str, Any],
    plunge_f: float = 300.0,
) -> float:
    """Machine profile-aware time estimator with jerk-limited motion."""
    limits = profile.get("limits", {})
    accel = float(limits.get("accel", 800))
    jerk = float(limits.get("jerk", 2000))
    rapid = float(limits.get("rapid", 3000)) / 60.0  # mm/s
    corner_tol_mm = float(limits.get("corner_tol_mm", 0.2))

    def seg_time(distance: float, v_target: float) -> float:
        """
        Calculate time for segment with jerk-limited trapezoid profile.
        
        Args:
            distance: Segment length in mm
            v_target: Target velocity in mm/s
        
        Returns:
            Time in seconds
        """
        if distance <= 1e-6 or v_target <= 1e-6:
            return 0.0

        a = max(1.0, accel)
        j = max(1.0, jerk)

        # Jerk-limited ramp time
        t_a = a / j
        s_a = 0.5 * a * (t_a ** 2)

        # Reachable velocity
        v_reach = min(v_target, math.sqrt(2 * a * max(0.0, distance - 2 * s_a)))

        # Short segment: triangular profile
        if v_reach < v_target * 0.9:
            return 2.0 * math.sqrt(distance / max(1e-6, a))

        # Long segment: trapezoid profile
        s_cruise = max(0.0, distance - 2 * s_a)
        t_cruise = s_cruise / max(1e-6, v_target)
        return (2 * t_a) + t_cruise

    total_time = 0.0
    last_xy = None

    for m in moves:
        code = m.get("code")

        # Rapid moves
        if code == "G0":
            nx = m.get("x", None)
            ny = m.get("y", None)
            
            if last_xy and (nx is not None and ny is not None):
                d = math.hypot(nx - last_xy[0], ny - last_xy[1])
                total_time += seg_time(d, rapid)
            
            if nx is not None and ny is not None:
                last_xy = (nx, ny)
            continue

        # Cutting moves
        if code in ("G1", "G2", "G3"):
            nx = m.get("x", None)
            ny = m.get("y", None)

            if last_xy and (nx is not None and ny is not None):
                d = math.hypot(nx - last_xy[0], ny - last_xy[1])
            else:
                d = 0.0

            # Get base feed and metadata
            base_f = float(m.get("f", limits.get("feed_xy", 1200)))
            meta = m.get("meta", {})
            slowdown = float(meta.get("slowdown", 1.0))
            is_troch = bool(meta.get("trochoid"))

            # Compute effective feed with all factors
            f_eff = effective_feed_for_segment(code, base_f, profile, is_troch, slowdown)
            v_eff = f_eff / 60.0  # mm/s

            total_time += seg_time(d, v_eff)

            if nx is not None and ny is not None:
                last_xy = (nx, ny)
            continue

    # Corner blending benefit
    blending_factor = 1.0 - min(0.1, corner_tol_mm / 10.0)
    total_time *= blending_factor

    return total_time


def _tri_time_and_limit(
    d: float, 
    v_target: float, 
    accel: float, 
    jerk: float
) -> Tuple[float, str]:
    """Jerk-limited trapezoid time calculation with limiter identification."""
    if d <= 1e-9 or v_target <= 1e-9:
        return 0.0, "none"
    
    a = max(1.0, accel)
    j = max(1.0, jerk)
    
    # Jerk-limited ramp
    t_a = a / j
    s_a = 0.5 * a * (t_a ** 2)
    
    # Reachable velocity
    v_reach = math.sqrt(max(0.0, 2 * a * max(0.0, d - 2 * s_a)))
    
    if v_reach < v_target * 0.9:
        # Couldn't reach requested v_target → accel/jerk limited
        # Crude heuristic: if jerk is very small relative to accel, blame jerk
        lim = "jerk" if j < a * 2 else "accel"
        return 2.0 * math.sqrt(d / max(1e-6, a)), lim
    
    # Reached v_target → no accel limit (cruise exists)
    s_cruise = max(0.0, d - 2 * s_a)
    t_cruise = s_cruise / max(1e-6, v_target)
    return (2 * t_a) + t_cruise, "none"


# =============================================================================
# BOTTLENECK TAGGING (MOVE ANALYSIS)
# =============================================================================

def jerk_aware_time_with_profile_and_tags(
    moves: List[Dict[str, Any]],
    profile: Dict[str, Any],
) -> Tuple[float, List[Dict[str, Any]], Dict[str, int]]:
    """Machine profile-aware time estimator with bottleneck tagging (M.1.1)."""
    limits = profile.get("limits", {})
    accel = float(limits.get("accel", 800))
    jerk = float(limits.get("jerk", 2000))
    rapid = float(limits.get("rapid", 3000)) / 60.0  # mm/s
    feed_cap = float(limits.get("feed_xy", 1200))  # mm/min
    corner_tol_mm = float(limits.get("corner_tol_mm", 0.2))

    total_time = 0.0
    last_xy = None
    caps = {"feed_cap": 0, "accel": 0, "jerk": 0, "none": 0}
    tagged = []

    for m in moves:
        # Shallow copy to write meta (preserve original moves)
        mm = dict(m)
        mm.setdefault("meta", {})
        
        code = mm.get("code")
        nx = mm.get("x", None)
        ny = mm.get("y", None)
        
        # Calculate distance
        d = 0.0
        if last_xy is not None and nx is not None and ny is not None:
            d = math.hypot(nx - last_xy[0], ny - last_xy[1])
        
        if nx is not None and ny is not None:
            last_xy = (nx, ny)

        # Rapid moves (G0)
        if code == "G0":
            dt, lim = _tri_time_and_limit(d, rapid, accel, jerk)
            total_time += dt
            mm["meta"]["limit"] = "none" if lim == "none" else lim
            caps[mm["meta"]["limit"]] += 1
            tagged.append(mm)
            continue

        # Cutting moves (G1/G2/G3)
        if code in ("G1", "G2", "G3"):
            base_f = float(mm.get("f", feed_cap))
            slowdown = float(mm.get("meta", {}).get("slowdown", 1.0))
            is_troch = bool(mm.get("meta", {}).get("trochoid"))
            
            # Calculate effective feed (with slowdown, arc penalty, etc.)
            v_req_mm_min = effective_feed_for_segment(
                code, base_f, {"limits": limits}, is_troch, slowdown
            )
            
            # Check if feed cap is limiting
            feed_limited = v_req_mm_min > feed_cap
            v_eff = min(v_req_mm_min, feed_cap) / 60.0  # mm/s

            dt, lim = _tri_time_and_limit(d, v_eff, accel, jerk)
            total_time += dt

            # Determine dominant limiter
            if feed_limited:
                mm["meta"]["limit"] = "feed_cap"
            else:
                mm["meta"]["limit"] = lim
            
            caps[mm["meta"]["limit"]] += 1
            tagged.append(mm)
            continue

        # Non-motion lines (no limit annotation)
        tagged.append(mm)

    # Corner blending benefit
    blending_factor = 1.0 - min(0.1, corner_tol_mm / 10.0)
    total_time *= blending_factor

    return total_time, tagged, caps
