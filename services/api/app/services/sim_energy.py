"""
Core simulation engine for realistic time/energy estimation.

Calculates:
- Total cutting distance (mm)
- Realistic time with accel/decel (seconds)
- Material removal rate (mm³/min)
- Average power consumption (W)
- Total energy (J)

Material-specific SCE (Specific Cutting Energy) values and energy distribution.
"""

from typing import List, Tuple, Optional
from math import sqrt, hypot


def _to_mm(v: Optional[float]) -> float:
    """Convert None to 0.0 for safe math."""
    return v if v is not None else 0.0


def _len2d_mm(dx: float, dy: float) -> float:
    """2D distance in mm."""
    return hypot(dx, dy)


def _feed_capped(f: Optional[float], cap: float) -> float:
    """Cap feed rate (mm/min) at machine maximum."""
    if f is None or f <= 0:
        return cap
    return min(f, cap)


def _mrr_mm3_per_min(
    width_mm: float,
    depth_mm: float,
    feed_mm_per_min: float,
    engagement_pct: float
) -> float:
    """
    Material Removal Rate (mm3/min).
    
    MRR = width x depth x feed x (engagement_pct / 100)
    
    Args:
        width_mm: Radial engagement (typically stepover)
        depth_mm: Axial engagement (typically stepdown)
        feed_mm_per_min: Feed rate in mm/min
        engagement_pct: Percentage of tool engaged (0-100)
    
    Returns:
        MRR in mm3/min
    """
    return width_mm * depth_mm * feed_mm_per_min * (engagement_pct / 100.0)


def simulate_energy(
    moves: List[dict],
    sce_j_per_mm3: float = 1.4,
    energy_split_chip: float = 0.60,
    energy_split_tool: float = 0.25,
    energy_split_workpiece: float = 0.15,
    feed_xy_max: float = 3000.0,
    rapid_xy: float = 6000.0,
    accel_xy: float = 800.0,
    stepover_frac: float = 0.45,
    stepdown_mm: float = 1.5,
    engagement_pct: float = 40.0,
    tool_d_mm: float = 6.0
) -> dict:
    """
    Simulate cutting energy and realistic time estimation.
    
    Args:
        moves: List of move dicts with code, x, y, z, f
        sce_j_per_mm3: Specific Cutting Energy (J/mm³) - material dependent
        energy_split_*: Energy distribution percentages (sum to 1.0)
        feed_xy_max: Maximum XY feed rate (mm/min)
        rapid_xy: Rapid traverse feed rate (mm/min)
        accel_xy: XY acceleration (mm/s²)
        stepover_frac: Stepover as fraction of tool diameter
        stepdown_mm: Depth of cut per pass (mm)
        engagement_pct: Percentage of tool engaged in cut
        tool_d_mm: Tool diameter (mm)
    
    Returns:
        dict with length_mm, time_s, volume_mm3, mrr_mm3_min, power_w, energy_j, energy_splits
    """
    
    # Initialize tracking
    total_cutting_len = 0.0
    total_rapid_len = 0.0
    total_time = 0.0
    
    px = py = pz = 0.0  # Previous position
    
    for mv in moves:
        code = mv.get("code", "")
        x, y, z = _to_mm(mv.get("x")), _to_mm(mv.get("y")), _to_mm(mv.get("z"))
        f = mv.get("f")
        
        # Calculate distance
        dx, dy, dz = x - px, y - py, z - pz
        dist_2d = _len2d_mm(dx, dy)
        dist_3d = sqrt(dx**2 + dy**2 + dz**2)
        
        if code == "G0":  # Rapid
            total_rapid_len += dist_3d
            feed_rate = rapid_xy
        else:  # Cutting (G1/G2/G3)
            total_cutting_len += dist_2d
            feed_rate = _feed_capped(f, feed_xy_max)
        
        # Realistic time with accel/decel
        # Simple trapezoid profile (ignore jerk for now)
        feed_mm_per_sec = feed_rate / 60.0
        
        # Time to accelerate to full speed
        t_accel = feed_mm_per_sec / accel_xy
        s_accel = 0.5 * accel_xy * t_accel**2
        
        if dist_3d < 2 * s_accel:
            # Triangular profile (too short for full speed)
            t_seg = 2 * sqrt(dist_3d / accel_xy)
        else:
            # Trapezoid profile (accel → cruise → decel)
            s_cruise = dist_3d - 2 * s_accel
            t_cruise = s_cruise / feed_mm_per_sec
            t_seg = 2 * t_accel + t_cruise
        
        total_time += t_seg
        
        # Update position
        px, py, pz = x, y, z
    
    # Volume calculation
    width_mm = stepover_frac * tool_d_mm
    depth_mm = stepdown_mm
    volume_mm3 = total_cutting_len * width_mm * depth_mm
    
    # MRR calculation
    avg_feed = feed_xy_max * 0.8  # Assume 80% of max during cutting
    mrr_mm3_min = _mrr_mm3_per_min(width_mm, depth_mm, avg_feed, engagement_pct)
    
    # Energy calculation
    energy_j = volume_mm3 * sce_j_per_mm3
    
    # Power calculation (assuming cutting time is dominant)
    cutting_time_s = (total_cutting_len / avg_feed) * 60.0  # Convert to seconds
    power_w = energy_j / cutting_time_s if cutting_time_s > 0 else 0.0
    
    # Energy distribution
    energy_chip_j = energy_j * energy_split_chip
    energy_tool_j = energy_j * energy_split_tool
    energy_workpiece_j = energy_j * energy_split_workpiece
    
    return {
        "length_cutting_mm": round(total_cutting_len, 2),
        "length_rapid_mm": round(total_rapid_len, 2),
        "time_s": round(total_time, 2),
        "volume_mm3": round(volume_mm3, 2),
        "mrr_mm3_min": round(mrr_mm3_min, 2),
        "power_avg_w": round(power_w, 2),
        "energy_total_j": round(energy_j, 2),
        "energy_chip_j": round(energy_chip_j, 2),
        "energy_tool_j": round(energy_tool_j, 2),
        "energy_workpiece_j": round(energy_workpiece_j, 2)
    }


def simulate_with_timeseries(
    moves: List[dict],
    sce_j_per_mm3: float = 1.4,
    feed_xy_max: float = 3000.0,
    rapid_xy: float = 6000.0,
    accel_xy: float = 800.0,
    stepover_frac: float = 0.45,
    stepdown_mm: float = 1.5,
    engagement_pct: float = 40.0,
    tool_d_mm: float = 6.0
) -> Tuple[dict, List[dict]]:
    """
    Same as simulate_energy but also returns per-segment timeseries.
    
    Returns:
        Tuple of (summary_dict, timeseries_list)
        
        timeseries_list contains dicts with:
        - seg_idx: Segment index
        - code: G0/G1/G2/G3
        - dist_mm: Segment distance
        - time_s: Segment time
        - mrr_mm3_min: Instantaneous MRR (0 for rapids)
        - power_w: Instantaneous power (0 for rapids)
    """
    
    # Initialize tracking
    total_cutting_len = 0.0
    total_rapid_len = 0.0
    total_time = 0.0
    total_energy = 0.0
    
    px = py = pz = 0.0
    timeseries = []
    
    width_mm = stepover_frac * tool_d_mm
    depth_mm = stepdown_mm
    
    for idx, mv in enumerate(moves):
        code = mv.get("code", "")
        x, y, z = _to_mm(mv.get("x")), _to_mm(mv.get("y")), _to_mm(mv.get("z"))
        f = mv.get("f")
        
        dx, dy, dz = x - px, y - py, z - pz
        dist_2d = _len2d_mm(dx, dy)
        dist_3d = sqrt(dx**2 + dy**2 + dz**2)
        
        if code == "G0":
            total_rapid_len += dist_3d
            feed_rate = rapid_xy
            is_cutting = False
        else:
            total_cutting_len += dist_2d
            feed_rate = _feed_capped(f, feed_xy_max)
            is_cutting = True
        
        # Time calculation
        feed_mm_per_sec = feed_rate / 60.0
        t_accel = feed_mm_per_sec / accel_xy
        s_accel = 0.5 * accel_xy * t_accel**2
        
        if dist_3d < 2 * s_accel:
            t_seg = 2 * sqrt(dist_3d / accel_xy)
        else:
            s_cruise = dist_3d - 2 * s_accel
            t_cruise = s_cruise / feed_mm_per_sec
            t_seg = 2 * t_accel + t_cruise
        
        total_time += t_seg
        
        # MRR and power for cutting moves
        if is_cutting:
            mrr = _mrr_mm3_per_min(width_mm, depth_mm, feed_rate, engagement_pct)
            seg_volume = dist_2d * width_mm * depth_mm
            seg_energy = seg_volume * sce_j_per_mm3
            seg_power = seg_energy / t_seg if t_seg > 0 else 0.0
            total_energy += seg_energy
        else:
            mrr = 0.0
            seg_power = 0.0
        
        timeseries.append({
            "seg_idx": idx,
            "code": code,
            "dist_mm": round(dist_3d, 3),
            "time_s": round(t_seg, 3),
            "mrr_mm3_min": round(mrr, 2),
            "power_w": round(seg_power, 2)
        })
        
        px, py, pz = x, y, z
    
    # Summary
    volume_mm3 = total_cutting_len * width_mm * depth_mm
    avg_feed = feed_xy_max * 0.8
    mrr_avg = _mrr_mm3_per_min(width_mm, depth_mm, avg_feed, engagement_pct)
    power_avg = total_energy / total_time if total_time > 0 else 0.0
    
    summary = {
        "length_cutting_mm": round(total_cutting_len, 2),
        "length_rapid_mm": round(total_rapid_len, 2),
        "time_s": round(total_time, 2),
        "volume_mm3": round(volume_mm3, 2),
        "mrr_mm3_min": round(mrr_avg, 2),
        "power_avg_w": round(power_avg, 2),
        "energy_total_j": round(total_energy, 2)
    }
    
    return summary, timeseries
