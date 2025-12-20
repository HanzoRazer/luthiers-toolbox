"""
GRBL Post-Processor

Renders toolpaths to GRBL-compatible G-code with:
- No line numbers (GRBL standard)
- Semicolon comments
- Simplified M-codes
- Standard GRBL modal groups

Reference: GRBL 1.1 G-code documentation
https://github.com/gnea/grbl/wiki/Grbl-v1.1-Commands
"""
from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

# GRBL G-code constants
RAPID_MOVE = "G0"
LINEAR_MOVE = "G1"
CW_ARC = "G2"
CCW_ARC = "G3"
DWELL = "G4"
ABSOLUTE_MODE = "G90"
INCREMENTAL_MODE = "G91"
UNITS_MM = "G21"
UNITS_INCH = "G20"
SPINDLE_CW = "M3"
SPINDLE_CCW = "M4"
SPINDLE_STOP = "M5"
COOLANT_FLOOD = "M8"
COOLANT_MIST = "M7"
COOLANT_OFF = "M9"
PROGRAM_END = "M2"
PROGRAM_STOP = "M0"


def _format_coord(axis: str, value: float, decimals: int = 3) -> str:
    """Format axis coordinate."""
    return f"{axis}{value:.{decimals}f}"


def _format_feed(feed: float) -> str:
    """Format feedrate value."""
    if feed == int(feed):
        return f"F{int(feed)}"
    return f"F{feed:.1f}"


def _format_speed(speed: int) -> str:
    """Format spindle speed value."""
    return f"S{speed}"


def _render_comment(text: str) -> str:
    """Render GRBL-style semicolon comment."""
    return f"; {text}"


def _render_header(
    comment: Optional[str],
    context: Dict[str, Any],
) -> List[str]:
    """Render GRBL program header."""
    lines = []
    
    # Header comment
    if comment:
        lines.append(_render_comment(comment))
    
    # Timestamp
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines.append(_render_comment(f"Generated: {ts}"))
    
    # Tool info if provided
    if "tool" in context:
        tool = context["tool"]
        tool_desc = tool.get("description", f"Tool #{tool.get('number', 1)}")
        lines.append(_render_comment(f"Tool: {tool_desc}"))
    
    # Material info if provided
    if "material" in context:
        mat = context["material"]
        mat_name = mat.get("name", "Unknown")
        lines.append(_render_comment(f"Material: {mat_name}"))
    
    # Setup block
    lines.append("")
    units = UNITS_MM if context.get("units", "mm") == "mm" else UNITS_INCH
    lines.append(f"{units} {ABSOLUTE_MODE}")
    
    return lines


def _render_footer() -> List[str]:
    """Render GRBL program footer."""
    return [
        "",
        _render_comment("END OF PROGRAM"),
        SPINDLE_STOP,
        COOLANT_OFF,
        PROGRAM_END,
    ]


def _render_spindle_start(
    speed: int,
    direction: str,
) -> str:
    """Render spindle start command."""
    spindle_code = SPINDLE_CW if direction.upper() == "CW" else SPINDLE_CCW
    return f"{_format_speed(speed)} {spindle_code}"


def _render_moves(
    moves: List[Dict[str, Any]],
    feed_xy: float,
    feed_z: float,
) -> List[str]:
    """Render a series of moves."""
    lines = []
    
    for move in moves:
        move_type = move.get("type", "linear")
        
        if move_type == "rapid":
            # Rapid move
            parts = [RAPID_MOVE]
            if "x" in move:
                parts.append(_format_coord("X", move["x"]))
            if "y" in move:
                parts.append(_format_coord("Y", move["y"]))
            if "z" in move:
                parts.append(_format_coord("Z", move["z"]))
            lines.append(" ".join(parts))
            
        elif move_type == "linear":
            # Linear interpolation
            parts = [LINEAR_MOVE]
            if "x" in move:
                parts.append(_format_coord("X", move["x"]))
            if "y" in move:
                parts.append(_format_coord("Y", move["y"]))
            if "z" in move:
                parts.append(_format_coord("Z", move["z"]))
                parts.append(_format_feed(feed_z))
            else:
                parts.append(_format_feed(feed_xy))
            lines.append(" ".join(parts))
            
        elif move_type in ("cw_arc", "ccw_arc"):
            # Arc interpolation
            arc_code = CW_ARC if move_type == "cw_arc" else CCW_ARC
            parts = [arc_code]
            parts.append(_format_coord("X", move["x"]))
            parts.append(_format_coord("Y", move["y"]))
            if "i" in move:
                parts.append(_format_coord("I", move["i"]))
            if "j" in move:
                parts.append(_format_coord("J", move["j"]))
            if "r" in move:
                parts.append(_format_coord("R", move["r"]))
            parts.append(_format_feed(feed_xy))
            lines.append(" ".join(parts))
            
        elif move_type == "dwell":
            # Dwell (P in seconds for GRBL)
            dwell_sec = move.get("seconds", 0)
            lines.append(f"{DWELL} P{dwell_sec:.2f}")
    
    return lines


def _render_segments(
    segments: List[Dict[str, Any]],
    context: Dict[str, Any],
) -> List[str]:
    """Render all segments (operations)."""
    lines = []
    
    feed_xy = context.get("feed_xy", 1000)
    feed_z = context.get("feed_z", 200)
    safe_z = context.get("safe_z", 10.0)
    
    for idx, seg in enumerate(segments):
        # Segment comment
        seg_name = seg.get("name", f"Segment {idx + 1}")
        lines.append("")
        lines.append(_render_comment(f"--- {seg_name} ---"))
        
        # Optional coolant on
        if seg.get("coolant", False):
            coolant_type = seg.get("coolant_type", "flood")
            coolant_code = COOLANT_MIST if coolant_type == "mist" else COOLANT_FLOOD
            lines.append(coolant_code)
        
        # Retract to safe Z
        lines.append(f"{RAPID_MOVE} {_format_coord('Z', safe_z)}")
        
        # Render moves
        moves = seg.get("moves", [])
        move_lines = _render_moves(moves, feed_xy, feed_z)
        lines.extend(move_lines)
        
        # Retract after segment
        lines.append(f"{RAPID_MOVE} {_format_coord('Z', safe_z)}")
        
        # Optional coolant off
        if seg.get("coolant", False):
            lines.append(COOLANT_OFF)
    
    return lines


def render(
    toolpaths: Dict[str, Any],
    context: Dict[str, Any],
    *,
    program_comment: Optional[str] = None,
) -> str:
    """
    Render toolpaths to GRBL G-code.
    
    Args:
        toolpaths: Toolpath data with 'segments' list
        context: Machining context (feeds, speeds, tool info)
        program_comment: Header comment
    
    Returns:
        GRBL G-code as string
    """
    comment = program_comment or context.get("program_comment", "LUTHIER TOOLBOX")
    
    lines = []
    
    # Header
    lines.extend(_render_header(comment, context))
    
    # Spindle start if specified
    if "tool" in context:
        tool = context["tool"]
        spindle_speed = tool.get("spindle_speed", 18000)
        spindle_dir = tool.get("spindle_direction", "CW")
        lines.append("")
        lines.append(_render_spindle_start(spindle_speed, spindle_dir))
    
    # Segments
    segments = toolpaths.get("segments", [])
    seg_lines = _render_segments(segments, context)
    lines.extend(seg_lines)
    
    # Footer
    lines.extend(_render_footer())
    
    return "\n".join(lines)


def get_grbl_settings_report(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get recommended GRBL settings based on context.
    
    Returns dict with recommended $$ settings.
    """
    settings = {
        "$0": 10,      # Step pulse (microseconds)
        "$1": 25,      # Step idle delay (milliseconds)
        "$2": 0,       # Step port invert mask
        "$3": 0,       # Direction port invert mask
        "$4": 0,       # Step enable invert (0=active low)
        "$5": 0,       # Limit pins invert (0=active low)
        "$6": 0,       # Probe pin invert (0=active low)
        "$10": 1,      # Status report options
        "$11": 0.010,  # Junction deviation (mm)
        "$12": 0.002,  # Arc tolerance (mm)
        "$13": 0,      # Report in inches (0=mm)
        "$20": 0,      # Soft limits enable
        "$21": 0,      # Hard limits enable
        "$22": 0,      # Homing cycle enable
        "$23": 0,      # Homing direction invert mask
        "$24": 25.0,   # Homing locate feed rate (mm/min)
        "$25": 500.0,  # Homing search seek rate (mm/min)
        "$26": 250,    # Homing switch debounce delay (ms)
        "$27": 1.0,    # Homing switch pull-off distance (mm)
        "$30": 24000,  # Maximum spindle speed (RPM)
        "$31": 0,      # Minimum spindle speed (RPM)
        "$32": 0,      # Laser mode enable
    }
    
    # Adjust max spindle based on tool
    if "tool" in context:
        max_speed = context["tool"].get("max_spindle_speed", 24000)
        settings["$30"] = max_speed
    
    # Adjust for machine type
    machine_type = context.get("machine_type", "router")
    if machine_type == "laser":
        settings["$32"] = 1  # Enable laser mode
    
    return settings


def validate_for_grbl(
    toolpaths: Dict[str, Any],
    context: Dict[str, Any],
) -> List[str]:
    """
    Validate toolpaths for GRBL compatibility.
    
    Returns list of warning messages (empty if OK).
    """
    warnings = []
    
    # Check for required fields
    if "segments" not in toolpaths:
        warnings.append("Missing 'segments' in toolpaths")
    
    # Check feed rates
    feed_xy = context.get("feed_xy", 0)
    if feed_xy <= 0:
        warnings.append("Invalid or missing feed_xy")
    elif feed_xy > 5000:
        warnings.append(f"feed_xy ({feed_xy}) may exceed typical GRBL machine limits")
    
    # Check spindle speed
    if "tool" in context:
        speed = context["tool"].get("spindle_speed", 0)
        if speed <= 0:
            warnings.append("Invalid or missing spindle_speed")
        elif speed > 24000:
            warnings.append(
                f"Spindle speed ({speed}) exceeds typical GRBL max (24000)"
            )
    
    # Check segments for GRBL-specific issues
    segments = toolpaths.get("segments", [])
    total_moves = 0
    
    for idx, seg in enumerate(segments):
        moves = seg.get("moves", [])
        if not moves:
            warnings.append(f"Segment {idx} has no moves")
        
        total_moves += len(moves)
        
        for move_idx, move in enumerate(moves):
            # Check for NaN/Inf values
            for axis in ["x", "y", "z", "i", "j", "r"]:
                if axis in move:
                    val = move[axis]
                    if not math.isfinite(val):
                        warnings.append(
                            f"Segment {idx} move {move_idx}: "
                            f"invalid {axis.upper()} value ({val})"
                        )
            
            # GRBL arc checks
            if move.get("type") in ("cw_arc", "ccw_arc"):
                # Arcs need either I/J or R
                has_ij = "i" in move or "j" in move
                has_r = "r" in move
                if not has_ij and not has_r:
                    warnings.append(
                        f"Segment {idx} move {move_idx}: "
                        "arc needs I/J or R parameter"
                    )
    
    # GRBL planner buffer warning
    if total_moves > 1000:
        warnings.append(
            f"Program has {total_moves} moves. "
            "Consider breaking into smaller programs for GRBL planner."
        )
    
    return warnings
