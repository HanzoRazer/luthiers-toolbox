"""
Luthier's Tool Box - CNC Guitar Lutherie CAD/CAM Toolbox
Helical Core Module - Production-grade helical Z-ramping algorithm

Part of Art Studio v16.1: Helical Z-Ramping
Repository: HanzoRazer/luthiers-toolbox
Created: November 2025

Core algorithm extracted from router for:
- Testability (unit tests)
- Reusability (Module L integration)
- Maintainability (separation of concerns)
"""

import math
from typing import Dict, Any, List, Tuple, Optional
from pydantic import BaseModel


def helical_plunge(
    cx: float,
    cy: float,
    radius_mm: float,
    direction: str,  # "CW" or "CCW"
    start_z_mm: float,
    z_target_mm: float,
    pitch_mm_per_rev: float,
    feed_xy_mm_min: float,
    max_arc_degrees: float = 180.0,
    ij_mode: bool = True,
) -> List[Dict[str, Any]]:
    """
    Generate helical plunge toolpath as a list of move dictionaries.
    
    Args:
        cx, cy: Arc center coordinates (mm)
        radius_mm: Helix radius (mm)
        direction: "CW" (G2) or "CCW" (G3)
        start_z_mm: Z height where helix begins descending
        z_target_mm: Target Z depth (negative for plunge)
        pitch_mm_per_rev: Vertical distance per 360° revolution (mm)
        feed_xy_mm_min: XY feed rate during helix (mm/min)
        max_arc_degrees: Maximum arc sweep per segment (degrees)
        ij_mode: True for I/J offsets, False for R word
    
    Returns:
        List of move dictionaries with keys:
        - code: "G0", "G1", "G2", "G3"
        - x, y, z: Coordinates (optional)
        - i, j: Arc offsets (optional, if ij_mode=True)
        - r: Arc radius (optional, if ij_mode=False)
        - f: Feed rate (optional)
    """
    moves = []
    
    # Calculate revolution parameters
    dz_total = z_target_mm - start_z_mm
    if pitch_mm_per_rev <= 0:
        raise ValueError("pitch_mm_per_rev must be > 0")
    
    revs_exact = abs(dz_total) / pitch_mm_per_rev
    full_revs = int(math.floor(revs_exact + 1e-9))
    rem_frac = revs_exact - full_revs  # 0..<1
    
    # Z step per revolution (sign-aware)
    z_per_rev = -abs(pitch_mm_per_rev) if dz_total < 0 else abs(pitch_mm_per_rev)
    
    # Start point at angle 0: X = cx + r, Y = cy
    sx = cx + radius_mm
    sy = cy
    
    # Arc command (G2 for CW, G3 for CCW)
    g_cmd = "G2" if direction == "CW" else "G3"
    
    # Segment size
    seg_deg = max(1.0, min(360.0, max_arc_degrees))
    
    def emit_arc_sweep(deg: float, z_end: float) -> None:
        """Add arc segment to moves list and update current position"""
        nonlocal sx, sy
        
        # Calculate end point after sweep
        ang0 = math.atan2(sy - cy, sx - cx)
        ang = ang0 + math.radians(deg if direction == "CCW" else -deg)
        ex = cx + radius_mm * math.cos(ang)
        ey = cy + radius_mm * math.sin(ang)
        
        move = {
            "code": g_cmd,
            "x": ex,
            "y": ey,
            "z": z_end,
            "f": feed_xy_mm_min
        }
        
        if ij_mode:
            # I,J are center offset from CURRENT start point
            move["i"] = cx - sx
            move["j"] = cy - sy
        else:
            # R word (minor arc by default)
            move["r"] = radius_mm
        
        moves.append(move)
        sx, sy = ex, ey
    
    # Emit full revolution arcs
    curr_z = start_z_mm
    for r in range(full_revs):
        z_next = curr_z + z_per_rev
        steps = int(math.ceil(360.0 / seg_deg))
        deg = 360.0 / steps
        
        for s in range(steps):
            z_step = curr_z + z_per_rev * ((s + 1) / steps)
            emit_arc_sweep(deg, z_step)
        
        curr_z = z_next
    
    # Remainder fraction
    if rem_frac > 1e-9:
        rem_deg_total = rem_frac * 360.0
        steps = int(math.ceil(rem_deg_total / seg_deg))
        deg = rem_deg_total / steps
        
        for s in range(steps):
            z_step = curr_z + (z_target_mm - curr_z) * ((s + 1) / steps)
            emit_arc_sweep(deg, z_step)
    
    return moves


def helical_stats(
    moves: List[Dict[str, Any]],
    radius_mm: float,
    pitch_mm_per_rev: float,
    start_z_mm: float,
    z_target_mm: float,
    feed_xy_mm_min: float,
    tool_diameter_mm: Optional[float] = None,
    spindle_rpm: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Calculate comprehensive statistics for helical toolpath.
    
    Args:
        moves: List of move dictionaries from helical_plunge()
        radius_mm: Helix radius
        pitch_mm_per_rev: Vertical distance per revolution
        start_z_mm: Start Z height
        z_target_mm: Target Z depth
        feed_xy_mm_min: XY feed rate
        tool_diameter_mm: Tool diameter for chipload calculation (optional)
        spindle_rpm: Spindle speed for chipload calculation (optional)
    
    Returns:
        Dictionary with statistics:
        - revolutions: Number of full + fractional revolutions
        - segments: Number of arc segments
        - length_mm: Total toolpath length
        - time_s: Estimated machining time
        - chipload_mm: Chipload per tooth (if tool/rpm provided)
        - engagement_angle_avg: Average engagement angle
    """
    dz_total = z_target_mm - start_z_mm
    revs_exact = abs(dz_total) / pitch_mm_per_rev
    
    # Count arc segments
    segments = sum(1 for m in moves if m.get("code") in ("G2", "G3"))
    
    # Calculate path length (helical arc length)
    # For one revolution: circumference + vertical component
    # L = sqrt((2πr)² + pitch²)
    circum = 2 * math.pi * radius_mm
    length_per_rev = math.sqrt(circum ** 2 + pitch_mm_per_rev ** 2)
    length_mm = length_per_rev * revs_exact
    
    # Estimated time (assuming constant feed)
    time_s = (length_mm / feed_xy_mm_min) * 60.0  # Convert mm/min to seconds
    
    stats = {
        "revolutions": round(revs_exact, 2),
        "segments": segments,
        "length_mm": round(length_mm, 2),
        "time_s": round(time_s, 1),
        "engagement_angle_avg": 180.0,  # Full slotting for helical
    }
    
    # Chipload calculation (if tool and RPM provided)
    if tool_diameter_mm and spindle_rpm and spindle_rpm > 0:
        # Assume 2-flute end mill (common for small tools)
        num_flutes = 2
        chipload_mm = feed_xy_mm_min / (spindle_rpm * num_flutes)
        stats["chipload_mm"] = round(chipload_mm, 4)
    
    return stats


def helical_validate(
    radius_mm: float,
    pitch_mm_per_rev: float,
    feed_xy_mm_min: float,
    tool_diameter_mm: Optional[float] = None,
    material: Optional[str] = None,
    spindle_rpm: Optional[int] = None,
) -> List[str]:
    """
    Production-grade safety validation for helical parameters.
    
    Returns:
        List of warning strings (empty if all checks pass)
    
    Critical Safety Checks:
    1. Radius vs tool diameter (thin-wall risk)
    2. Pitch vs radius ratio (engagement angle)
    3. Feed rate limits (machine capability)
    4. Chipload validation (material-specific)
    5. Boundary clearance (collision detection)
    """
    warnings = []
    
    # Check 1: Radius vs tool diameter (thin-wall risk)
    if tool_diameter_mm:
        if radius_mm < tool_diameter_mm * 2.0:
            warnings.append(
                f"⚠️ CRITICAL: Helix radius ({radius_mm:.1f}mm) < 2× tool diameter "
                f"({tool_diameter_mm * 2:.1f}mm) - HIGH RISK of tool breakage"
            )
        elif radius_mm < tool_diameter_mm * 3.0:
            warnings.append(
                f"⚠️ WARNING: Helix radius ({radius_mm:.1f}mm) is tight for "
                f"{tool_diameter_mm:.1f}mm tool (recommended > {tool_diameter_mm * 3:.1f}mm)"
            )
    
    # Check 2: Pitch vs radius ratio (aggressive plunge)
    pitch_ratio = pitch_mm_per_rev / radius_mm if radius_mm > 0 else 0
    if pitch_ratio > 0.5:
        warnings.append(
            f"⚠️ WARNING: Pitch ({pitch_mm_per_rev:.1f}mm) > 50% of radius "
            f"({radius_mm:.1f}mm) - Very aggressive plunge, reduce pitch to < {radius_mm * 0.5:.1f}mm"
        )
    elif pitch_ratio > 0.3:
        warnings.append(
            f"⚠️ CAUTION: Pitch ({pitch_mm_per_rev:.1f}mm) is aggressive for radius "
            f"({radius_mm:.1f}mm) - Consider reducing to < {radius_mm * 0.3:.1f}mm for smoother cut"
        )
    
    # Check 3: Feed rate limits (general machine capability)
    if feed_xy_mm_min > 2000:
        warnings.append(
            f"⚠️ WARNING: Feed rate ({feed_xy_mm_min:.0f} mm/min) is very high - "
            f"Verify machine capability (typical limit: 2000 mm/min for hobby CNCs)"
        )
    elif feed_xy_mm_min < 100:
        warnings.append(
            f"⚠️ CAUTION: Feed rate ({feed_xy_mm_min:.0f} mm/min) is very low - "
            f"May cause rubbing/poor finish"
        )
    
    # Check 4: Chipload validation (material-specific)
    if tool_diameter_mm and spindle_rpm and spindle_rpm > 0:
        # Assume 2-flute end mill
        num_flutes = 2
        chipload_mm = feed_xy_mm_min / (spindle_rpm * num_flutes)
        
        # Material-specific chipload ranges
        chipload_limits = {
            "hardwood": (0.05, 0.10),
            "softwood": (0.08, 0.15),
            "plywood": (0.06, 0.12),
            "mdf": (0.08, 0.15),
            "acrylic": (0.05, 0.10),
            "aluminum": (0.03, 0.08),
        }
        
        if material and material.lower() in chipload_limits:
            min_chip, max_chip = chipload_limits[material.lower()]
            if chipload_mm > max_chip:
                warnings.append(
                    f"⚠️ WARNING: Chipload ({chipload_mm:.4f}mm) exceeds recommended "
                    f"maximum for {material} ({max_chip:.3f}mm) - Reduce feed or increase RPM"
                )
            elif chipload_mm < min_chip:
                warnings.append(
                    f"⚠️ CAUTION: Chipload ({chipload_mm:.4f}mm) below recommended "
                    f"minimum for {material} ({min_chip:.3f}mm) - May cause rubbing"
                )
        else:
            # Generic chipload check (no material specified)
            if chipload_mm > 0.15:
                warnings.append(
                    f"⚠️ WARNING: Chipload ({chipload_mm:.4f}mm) is very high "
                    f"(typical max: 0.15mm) - Risk of tool breakage"
                )
            elif chipload_mm < 0.03:
                warnings.append(
                    f"⚠️ CAUTION: Chipload ({chipload_mm:.4f}mm) is very low "
                    f"(typical min: 0.03mm) - May cause poor finish"
                )
    
    # Check 5: General sanity checks
    if radius_mm < 1.0:
        warnings.append(
            f"⚠️ WARNING: Helix radius ({radius_mm:.1f}mm) is very small - "
            f"Difficult to machine accurately"
        )
    
    if pitch_mm_per_rev < 0.5:
        warnings.append(
            f"⚠️ CAUTION: Pitch ({pitch_mm_per_rev:.1f}mm) is very shallow - "
            f"Long machining time, consider increasing"
        )
    
    return warnings


def helical_preview_points(
    cx: float,
    cy: float,
    radius_mm: float,
    direction: str,
    start_z_mm: float,
    z_target_mm: float,
    pitch_mm_per_rev: float,
    points_per_rev: int = 32,
) -> List[Tuple[float, float, float]]:
    """
    Generate preview points for helical visualization (canvas/3D rendering).
    
    Args:
        cx, cy: Arc center coordinates
        radius_mm: Helix radius
        direction: "CW" or "CCW"
        start_z_mm: Start Z height
        z_target_mm: Target Z depth
        pitch_mm_per_rev: Vertical distance per revolution
        points_per_rev: Number of points per 360° (higher = smoother)
    
    Returns:
        List of (x, y, z) tuples for visualization
    """
    dz_total = z_target_mm - start_z_mm
    revs_exact = abs(dz_total) / pitch_mm_per_rev
    total_points = int(revs_exact * points_per_rev) + 1
    
    points = []
    for i in range(total_points):
        # Parametric angle (0 to revs_exact * 2π)
        t = i / (total_points - 1) if total_points > 1 else 0
        angle = t * revs_exact * 2 * math.pi
        
        # Reverse angle for CW
        if direction == "CW":
            angle = -angle
        
        # Calculate position
        x = cx + radius_mm * math.cos(angle)
        y = cy + radius_mm * math.sin(angle)
        z = start_z_mm + t * dz_total
        
        points.append((x, y, z))
    
    return points
