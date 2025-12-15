# services/api/app/services/rosette_cam_bridge.py

from __future__ import annotations

from dataclasses import dataclass
from math import cos, sin, tau
from typing import Any, Dict, List, Tuple, Literal


Units = Literal["mm", "inch"]


@dataclass
class RosetteGeometry:
    """Simple rosette geometry for CAM planning."""
    center_x_mm: float
    center_y_mm: float
    inner_radius_mm: float
    outer_radius_mm: float
    units: Units = "mm"


@dataclass
class CamParams:
    """CAM parameters for rosette toolpath generation."""
    tool_diameter_mm: float
    stepover_pct: float  # 0.0-1.0
    stepdown_mm: float
    feed_xy_mm_min: float
    safe_z_mm: float
    cut_depth_mm: float


def _frange(start: float, stop: float, step: float) -> List[float]:
    """
    Generate a range of floats.
    Similar to range() but for floats.
    """
    result = []
    current = start
    if step > 0:
        while current < stop:
            result.append(current)
            current += step
    elif step < 0:
        while current > stop:
            result.append(current)
            current += step
    return result


def plan_rosette_toolpath(
    geom: RosetteGeometry,
    params: CamParams,
    circle_segments: int = 64,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Plan a simple concentric-ring toolpath for a rosette.
    
    Returns:
        (moves, stats)
        moves: list of move dicts with keys: code, x, y, z, f
        stats: dict with keys: rings, z_passes, length_mm, move_count
    """
    moves: List[Dict[str, Any]] = []
    
    # Calculate radial passes
    radial_step = params.tool_diameter_mm * params.stepover_pct
    radii = _frange(
        geom.inner_radius_mm,
        geom.outer_radius_mm + radial_step / 2,
        radial_step
    )
    if not radii:
        radii = [geom.inner_radius_mm]
    
    # Calculate Z passes
    z_passes = max(1, int(abs(params.cut_depth_mm) / params.stepdown_mm))
    z_increments = [
        -abs(params.cut_depth_mm) * (i + 1) / z_passes
        for i in range(z_passes)
    ]
    
    total_length = 0.0
    
    # Initial move to safe Z
    moves.append({"code": "G0", "z": params.safe_z_mm})
    
    for z_level in z_increments:
        for radius in radii:
            # Move to start of ring at safe Z
            x_start = geom.center_x_mm + radius
            y_start = geom.center_y_mm
            moves.append({"code": "G0", "x": x_start, "y": y_start})
            
            # Plunge to Z level
            moves.append({"code": "G1", "z": z_level, "f": params.feed_xy_mm_min})
            
            # Generate circle as line segments
            for i in range(1, circle_segments + 1):
                angle = (i / circle_segments) * tau
                x = geom.center_x_mm + radius * cos(angle)
                y = geom.center_y_mm + radius * sin(angle)
                
                # Calculate length for this segment
                if moves:
                    prev = moves[-1]
                    if "x" in prev and "y" in prev:
                        dx = x - prev["x"]
                        dy = y - prev["y"]
                        total_length += (dx**2 + dy**2)**0.5
                
                moves.append({
                    "code": "G1",
                    "x": x,
                    "y": y,
                    "f": params.feed_xy_mm_min
                })
            
            # Retract to safe Z after each ring
            moves.append({"code": "G0", "z": params.safe_z_mm})
    
    stats = {
        "rings": len(radii),
        "z_passes": z_passes,
        "length_mm": round(total_length, 2),
        "move_count": len(moves)
    }
    
    return moves, stats


def postprocess_toolpath_grbl(
    moves: List[Dict[str, Any]],
    units: Units,
    spindle_rpm: float,
) -> Tuple[str, Dict[str, Any]]:
    """
    Convert neutral moves to GRBL-flavored G-code.
    
    Returns:
        (gcode_text, gcode_stats)
    """
    lines = []
    
    # Header
    lines.append("G21" if units == "mm" else "G20")  # Units
    lines.append("G90")  # Absolute positioning
    lines.append("G17")  # XY plane
    lines.append(f"M3 S{int(spindle_rpm)}")  # Spindle on
    lines.append("G4 P2")  # Dwell 2 seconds
    
    # Convert moves to G-code
    for move in moves:
        parts = [move["code"]]
        if "x" in move:
            parts.append(f"X{move['x']:.4f}")
        if "y" in move:
            parts.append(f"Y{move['y']:.4f}")
        if "z" in move:
            parts.append(f"Z{move['z']:.4f}")
        if "f" in move:
            parts.append(f"F{move['f']:.1f}")
        lines.append(" ".join(parts))
    
    # Footer
    lines.append("M5")  # Spindle off
    lines.append("G0 Z10.0")  # Safe retract
    lines.append("M30")  # Program end
    
    gcode_text = "\n".join(lines)
    
    gcode_stats = {
        "lines": len(lines),
        "bytes": len(gcode_text)
    }
    
    return gcode_text, gcode_stats
