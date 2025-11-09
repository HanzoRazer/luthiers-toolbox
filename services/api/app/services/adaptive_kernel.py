"""
Real Adaptive Pocket Kernel Integration
========================================

Bridges the unified pipeline's PlanIn model to the existing adaptive_core_l1
engine with full L.2/L.3/M.* parameter support.

This module is the single source of truth for adaptive pocket planning,
used by both:
- Direct /cam/pocket/adaptive/plan endpoint
- Pipeline's AdaptivePocket operation
- DXF → Adaptive bridge endpoints
"""

from typing import List, Tuple, Dict, Any
from ..cam.adaptive_core_l1 import plan_adaptive_l1, to_toolpath


def plan_adaptive(
    loops: List[List[Tuple[float, float]]],
    tool_d: float,
    stepover: float = 0.45,
    stepdown: float = 2.0,
    margin: float = 0.5,
    strategy: str = "Spiral",
    smoothing_radius: float = 0.3,
    climb: bool = True,
    feed_xy: float = 1200,
    feed_z: float = 600,
    rapid: float = 3000,
    safe_z: float = 5.0,
    z_rough: float = -1.5,
    # L.2 parameters (reserved for future)
    corner_radius_min: float = 0.0,
    target_stepover: float = 0.0,
    slowdown_feed_pct: float = 1.0,
    # L.3 parameters (reserved for future)
    use_trochoids: bool = False,
    trochoid_radius: float = 1.5,
    trochoid_pitch: float = 0.5,
    jerk_aware: bool = False,
    # M.* machine profile parameters (reserved for future)
    machine_feed_xy: float = 0.0,
    machine_rapid: float = 0.0,
    machine_accel: float = 0.0,
    machine_jerk: float = 0.0,
    corner_tol_mm: float = 0.0,
    machine_profile_id: str | None = None,
    # Override system (reserved for future)
    adopt_overrides: bool = False,
    session_override_factor: float = 1.0,
) -> Dict[str, Any]:
    """
    Real adaptive pocket planner using Module L.1 (robust pyclipper offsetting).
    
    Input: All PlanIn parameters (loops + tool specs + advanced features)
    Output: { "moves": [...], "stats": {...}, "overlays": [...] }
    
    Current implementation uses L.1 core (pyclipper offsetting + island handling).
    Future upgrades will wire in L.2 (true spiralizer + adaptive stepover + fillets + HUD)
    and L.3 (trochoidal passes + jerk-aware motion).
    
    Args:
        loops: List of polygons; first = outer boundary, rest = islands
        tool_d: Tool diameter (mm)
        stepover: Stepover fraction (0-1) of tool diameter
        stepdown: Depth per pass (mm)
        margin: Clearance from boundary (mm)
        strategy: "Spiral" or "Lanes"
        smoothing_radius: Arc tolerance for rounded joins (mm)
        climb: Climb milling (True) or conventional (False)
        feed_xy: Cutting feed rate (mm/min)
        feed_z: Plunge feed rate (mm/min) [not used in L.1]
        rapid: Rapid traverse rate (mm/min) [not used in L.1]
        safe_z: Safe retract height (mm)
        z_rough: Cutting depth (negative mm)
        
        # L.2/L.3/M.* parameters reserved for future engine upgrades
        corner_radius_min: Minimum fillet radius for sharp corners
        target_stepover: Target stepover for adaptive local densification
        slowdown_feed_pct: Feed reduction percentage in tight zones
        use_trochoids: Enable trochoidal milling in overload zones
        trochoid_radius: Trochoid circle radius
        trochoid_pitch: Forward pitch per trochoid cycle
        jerk_aware: Enable jerk-aware time estimation
        machine_feed_xy: Machine profile cutting feed limit
        machine_rapid: Machine profile rapid feed limit
        machine_accel: Machine profile acceleration limit
        machine_jerk: Machine profile jerk limit
        corner_tol_mm: Corner tolerance for smoothing
        machine_profile_id: Machine profile identifier
        adopt_overrides: Use session override factors
        session_override_factor: Global speed override multiplier
    
    Returns:
        {
            "moves": [{"code": "G0|G1|G2|G3", "x": float, "y": float, "z": float, "f": float}, ...],
            "stats": {
                "length_mm": float,
                "area_mm2": float,
                "time_s": float,
                "volume_mm3": float,
                "move_count": int,
                "cutting_moves": int
            },
            "overlays": []  # Reserved for L.2 HUD system
        }
    """
    
    # Validate inputs
    if not loops or len(loops) == 0:
        raise ValueError("At least one loop (outer boundary) is required")
    
    if tool_d <= 0:
        raise ValueError(f"tool_d must be positive, got {tool_d}")
    
    if not (0 < stepover <= 1.0):
        raise ValueError(f"stepover must be in (0, 1], got {stepover}")
    
    if strategy not in ("Spiral", "Lanes"):
        raise ValueError(f"strategy must be 'Spiral' or 'Lanes', got {strategy}")
    
    # Call L.1 adaptive planner (robust pyclipper offsetting)
    path_pts = plan_adaptive_l1(
        loops=loops,
        tool_d=tool_d,
        stepover=stepover,
        stepdown=stepdown,
        margin=margin,
        strategy=strategy,
        smoothing_radius=smoothing_radius
    )
    
    # Convert path points to G-code moves
    moves_list = to_toolpath(
        path_pts=path_pts,
        z_rough=z_rough,
        safe_z=safe_z,
        feed_xy=feed_xy,
        lead_r=0.0  # No lead-in for now
    )
    
    # Calculate statistics
    total_length = 0.0
    cutting_moves = 0
    
    for i in range(1, len(moves_list)):
        move = moves_list[i]
        prev = moves_list[i-1]
        
        if move.get('code') == 'G1':
            dx = move.get('x', prev.get('x', 0)) - prev.get('x', 0)
            dy = move.get('y', prev.get('y', 0)) - prev.get('y', 0)
            dz = move.get('z', prev.get('z', 0)) - prev.get('z', 0)
            total_length += (dx**2 + dy**2 + dz**2)**0.5
            cutting_moves += 1
    
    # Estimate time (classic method with 10% overhead)
    time_s = (total_length / feed_xy) * 60 * 1.1 if feed_xy > 0 else 0
    
    # Calculate approximate area from first loop
    area_mm2 = _polygon_area(loops[0]) if loops else 0
    
    # Estimate volume removed
    volume_mm3 = area_mm2 * abs(z_rough) if area_mm2 > 0 else 0
    
    # Build response
    return {
        "moves": moves_list,
        "stats": {
            "length_mm": round(total_length, 2),
            "area_mm2": round(area_mm2, 2),
            "time_s": round(time_s, 1),
            "time_min": round(time_s / 60, 2),
            "volume_mm3": round(volume_mm3, 0),
            "move_count": len(moves_list),
            "cutting_moves": cutting_moves
        },
        "overlays": []  # Reserved for L.2 HUD overlays
    }


def _polygon_area(loop: List[Tuple[float, float]]) -> float:
    """Calculate polygon area using shoelace formula"""
    area = 0.0
    n = len(loop)
    for i in range(n):
        x1, y1 = loop[i]
        x2, y2 = loop[(i+1) % n]
        area += x1*y2 - x2*y1
    return abs(area) / 2.0
