# services/api/app/services/rosette_cam_bridge.py
"""
Rosette CAM bridge — toolpath generation for rosette channel clearing.

Phase 4: per-ring, pattern-aware toolpath strategies.
- plan_rosette_toolpath()      — original single-geometry (backward compat)
- plan_per_ring_toolpath()     — per-ring with pattern-aware strategy dispatch
- postprocess_toolpath_grbl()  — neutral moves → GRBL G-code
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import ceil, cos, pi, sin, tau
from typing import Any, Dict, List, Optional, Tuple, Literal


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


@dataclass
class RingCamSpec:
    """Per-ring spec for pattern-aware toolpath generation."""
    inner_radius_mm: float
    outer_radius_mm: float
    pattern_type: str = "solid"
    tile_angle_deg: float = 45.0
    tile_width_mm: float = 2.0
    ring_index: int = 0


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


# ── Pattern-aware strategy dispatch (Phase 4) ──────────────────────────────

def _strategy_concentric(
    ring: RingCamSpec,
    center_x: float,
    center_y: float,
    params: CamParams,
    z_level: float,
    segments: int,
) -> Tuple[List[Dict[str, Any]], float]:
    """Concentric circular passes — pocket-clearing strategy for SOLID rings."""
    moves: List[Dict[str, Any]] = []
    length = 0.0
    radial_step = params.tool_diameter_mm * params.stepover_pct

    radii = _frange(
        ring.inner_radius_mm,
        ring.outer_radius_mm + radial_step / 2,
        radial_step,
    )
    if not radii:
        radii = [ring.inner_radius_mm]

    for radius in radii:
        x_start = center_x + radius
        y_start = center_y
        moves.append({"code": "G0", "x": x_start, "y": y_start})
        moves.append({"code": "G1", "z": z_level, "f": params.feed_xy_mm_min})

        prev_x, prev_y = x_start, y_start
        for i in range(1, segments + 1):
            angle = (i / segments) * tau
            x = center_x + radius * cos(angle)
            y = center_y + radius * sin(angle)
            dx, dy = x - prev_x, y - prev_y
            length += (dx**2 + dy**2) ** 0.5
            moves.append({"code": "G1", "x": x, "y": y, "f": params.feed_xy_mm_min})
            prev_x, prev_y = x, y

        moves.append({"code": "G0", "z": params.safe_z_mm})

    return moves, length


def _strategy_zigzag(
    ring: RingCamSpec,
    center_x: float,
    center_y: float,
    params: CamParams,
    z_level: float,
    segments: int,
) -> Tuple[List[Dict[str, Any]], float]:
    """Alternating-angle raster passes for HERRINGBONE rings.

    Cuts alternating diagonal lines across the annulus, switching
    angle direction every pass to create the V-pattern.
    """
    moves: List[Dict[str, Any]] = []
    length = 0.0

    avg_r = (ring.inner_radius_mm + ring.outer_radius_mm) / 2.0
    circumference = tau * avg_r
    tile_w = max(ring.tile_width_mm, params.tool_diameter_mm)
    tile_count = max(4, int(circumference / tile_w))
    angle_step = tau / tile_count
    tilt = ring.tile_angle_deg * pi / 180.0

    for i in range(tile_count):
        base_angle = i * angle_step
        direction = 1.0 if i % 2 == 0 else -1.0
        skew = direction * tilt

        # Start point on inner radius, end on outer radius
        r_in = ring.inner_radius_mm
        r_out = ring.outer_radius_mm
        x0 = center_x + r_in * cos(base_angle - skew * 0.5)
        y0 = center_y + r_in * sin(base_angle - skew * 0.5)
        x1 = center_x + r_out * cos(base_angle + skew * 0.5)
        y1 = center_y + r_out * sin(base_angle + skew * 0.5)

        moves.append({"code": "G0", "x": x0, "y": y0})
        moves.append({"code": "G1", "z": z_level, "f": params.feed_xy_mm_min})
        moves.append({"code": "G1", "x": x1, "y": y1, "f": params.feed_xy_mm_min})
        moves.append({"code": "G0", "z": params.safe_z_mm})
        length += ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5

    return moves, length


def _strategy_spiral(
    ring: RingCamSpec,
    center_x: float,
    center_y: float,
    params: CamParams,
    z_level: float,
    segments: int,
) -> Tuple[List[Dict[str, Any]], float]:
    """Spiral pass for ROPE rings — single continuous inward-winding path."""
    moves: List[Dict[str, Any]] = []
    length = 0.0

    radial_step = params.tool_diameter_mm * params.stepover_pct
    total_radial = ring.outer_radius_mm - ring.inner_radius_mm
    turns = max(1, int(total_radial / radial_step))

    # Spiral from outer to inner
    total_points = turns * segments
    if total_points < 1:
        return _strategy_concentric(ring, center_x, center_y, params, z_level, segments)

    r_start = ring.outer_radius_mm
    r_end = ring.inner_radius_mm

    x0 = center_x + r_start
    y0 = center_y
    moves.append({"code": "G0", "x": x0, "y": y0})
    moves.append({"code": "G1", "z": z_level, "f": params.feed_xy_mm_min})

    prev_x, prev_y = x0, y0
    for step in range(1, total_points + 1):
        t = step / total_points
        radius = r_start + (r_end - r_start) * t
        angle = tau * turns * t
        x = center_x + radius * cos(angle)
        y = center_y + radius * sin(angle)
        dx, dy = x - prev_x, y - prev_y
        length += (dx**2 + dy**2) ** 0.5
        moves.append({"code": "G1", "x": x, "y": y, "f": params.feed_xy_mm_min})
        prev_x, prev_y = x, y

    moves.append({"code": "G0", "z": params.safe_z_mm})
    return moves, length


def _strategy_grid(
    ring: RingCamSpec,
    center_x: float,
    center_y: float,
    params: CamParams,
    z_level: float,
    segments: int,
) -> Tuple[List[Dict[str, Any]], float]:
    """Two-pass grid for CHECKERBOARD rings — radial lines + circumferential arcs."""
    moves: List[Dict[str, Any]] = []
    length = 0.0

    avg_r = (ring.inner_radius_mm + ring.outer_radius_mm) / 2.0
    circumference = tau * avg_r
    tile_w = max(ring.tile_width_mm, params.tool_diameter_mm)
    divisions = max(4, int(circumference / tile_w))
    angle_step = tau / divisions

    # Pass 1: radial lines (spokes)
    for i in range(divisions):
        angle = i * angle_step
        x_in = center_x + ring.inner_radius_mm * cos(angle)
        y_in = center_y + ring.inner_radius_mm * sin(angle)
        x_out = center_x + ring.outer_radius_mm * cos(angle)
        y_out = center_y + ring.outer_radius_mm * sin(angle)

        moves.append({"code": "G0", "x": x_in, "y": y_in})
        moves.append({"code": "G1", "z": z_level, "f": params.feed_xy_mm_min})
        moves.append({"code": "G1", "x": x_out, "y": y_out, "f": params.feed_xy_mm_min})
        moves.append({"code": "G0", "z": params.safe_z_mm})
        length += ((x_out - x_in) ** 2 + (y_out - y_in) ** 2) ** 0.5

    # Pass 2: circumferential arcs (concentric ring boundaries)
    radial_step = params.tool_diameter_mm * params.stepover_pct
    radii = _frange(
        ring.inner_radius_mm,
        ring.outer_radius_mm + radial_step / 2,
        radial_step,
    )
    for radius in radii:
        x_start = center_x + radius
        y_start = center_y
        moves.append({"code": "G0", "x": x_start, "y": y_start})
        moves.append({"code": "G1", "z": z_level, "f": params.feed_xy_mm_min})

        prev_x, prev_y = x_start, y_start
        for i in range(1, segments + 1):
            angle = (i / segments) * tau
            x = center_x + radius * cos(angle)
            y = center_y + radius * sin(angle)
            dx, dy = x - prev_x, y - prev_y
            length += (dx**2 + dy**2) ** 0.5
            moves.append({"code": "G1", "x": x, "y": y, "f": params.feed_xy_mm_min})
            prev_x, prev_y = x, y

        moves.append({"code": "G0", "z": params.safe_z_mm})

    return moves, length


def _strategy_sinusoidal(
    ring: RingCamSpec,
    center_x: float,
    center_y: float,
    params: CamParams,
    z_level: float,
    segments: int,
) -> Tuple[List[Dict[str, Any]], float]:
    """Sinusoidal-modulated concentric passes for WAVE rings."""
    moves: List[Dict[str, Any]] = []
    length = 0.0

    mid_r = (ring.inner_radius_mm + ring.outer_radius_mm) / 2.0
    amplitude = (ring.outer_radius_mm - ring.inner_radius_mm) / 4.0
    waves = max(3, int(tau * mid_r / max(ring.tile_width_mm, 2.0)))

    x0 = center_x + (mid_r + amplitude)
    y0 = center_y
    moves.append({"code": "G0", "x": x0, "y": y0})
    moves.append({"code": "G1", "z": z_level, "f": params.feed_xy_mm_min})

    prev_x, prev_y = x0, y0
    total_pts = max(segments, waves * 8)
    for i in range(1, total_pts + 1):
        t = i / total_pts
        angle = tau * t
        r = mid_r + amplitude * sin(waves * angle)
        x = center_x + r * cos(angle)
        y = center_y + r * sin(angle)
        dx, dy = x - prev_x, y - prev_y
        length += (dx**2 + dy**2) ** 0.5
        moves.append({"code": "G1", "x": x, "y": y, "f": params.feed_xy_mm_min})
        prev_x, prev_y = x, y

    moves.append({"code": "G0", "z": params.safe_z_mm})
    return moves, length


# Strategy registry — maps pattern_type → generator function
_PATTERN_STRATEGIES = {
    "solid": _strategy_concentric,
    "rope": _strategy_spiral,
    "herringbone": _strategy_zigzag,
    "checkerboard": _strategy_grid,
    "wave": _strategy_sinusoidal,
    # Complex patterns fall back to concentric channel clearing
    "spanish": _strategy_concentric,
    "celtic_knot": _strategy_concentric,
    "custom_matrix": _strategy_concentric,
}


def plan_per_ring_toolpath(
    rings: List[RingCamSpec],
    center_x_mm: float,
    center_y_mm: float,
    params: CamParams,
    circle_segments: int = 64,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Plan pattern-aware toolpaths, processing each ring individually.

    Each ring is cut with a strategy chosen by its pattern_type:
      solid / spanish / celtic_knot → concentric circular passes
      herringbone                    → alternating zigzag raster
      rope                           → inward spiral
      checkerboard                   → two-pass radial grid + arcs
      wave                           → sinusoidal-modulated path

    Returns:
        (moves, stats) — combined neutral moves + per-ring statistics.
    """
    all_moves: List[Dict[str, Any]] = []
    ring_stats: List[Dict[str, Any]] = []
    total_length = 0.0

    z_passes = max(1, int(abs(params.cut_depth_mm) / params.stepdown_mm))
    z_levels = [
        -abs(params.cut_depth_mm) * (i + 1) / z_passes
        for i in range(z_passes)
    ]

    # Initial safe-Z
    all_moves.append({"code": "G0", "z": params.safe_z_mm})

    for ring in rings:
        strategy_fn = _PATTERN_STRATEGIES.get(
            ring.pattern_type, _strategy_concentric
        )
        ring_moves: List[Dict[str, Any]] = []
        ring_length = 0.0

        for z_level in z_levels:
            moves, seg_len = strategy_fn(
                ring, center_x_mm, center_y_mm, params, z_level, circle_segments,
            )
            ring_moves.extend(moves)
            ring_length += seg_len

        all_moves.extend(ring_moves)
        total_length += ring_length

        ring_stats.append({
            "ring_index": ring.ring_index,
            "pattern_type": ring.pattern_type,
            "strategy": strategy_fn.__name__.replace("_strategy_", ""),
            "move_count": len(ring_moves),
            "length_mm": round(ring_length, 2),
            "inner_radius_mm": ring.inner_radius_mm,
            "outer_radius_mm": ring.outer_radius_mm,
        })

    stats = {
        "rings": len(rings),
        "z_passes": z_passes,
        "length_mm": round(total_length, 2),
        "move_count": len(all_moves),
        "per_ring": ring_stats,
    }

    return all_moves, stats


# ── Original single-geometry toolpath (backward compat) ─────────────────────

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
