"""
FANUC Post-Processor

Renders toolpaths to FANUC-style G-code with:
- O-number program headers
- N-code line numbers
- FANUC-style comments in parentheses
- Standard M-codes for spindle, coolant, tool changes

Reference: FANUC Series 0i/0i Mate Operator's Manual
"""
from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Union

# FANUC G-code constants
RAPID_MOVE = "G00"
LINEAR_MOVE = "G01"
CW_ARC = "G02"
CCW_ARC = "G03"
DWELL = "G04"
ABSOLUTE_MODE = "G90"
INCREMENTAL_MODE = "G91"
WORK_OFFSET_G54 = "G54"
CANCEL_CUTTER_COMP = "G40"
SPINDLE_CW = "M03"
SPINDLE_CCW = "M04"
SPINDLE_STOP = "M05"
COOLANT_ON = "M08"
COOLANT_OFF = "M09"
TOOL_CHANGE = "M06"
PROGRAM_END = "M30"
OPTIONAL_STOP = "M01"


def _format_coord(axis: str, value: float, decimals: int = 4) -> str:
    """Format axis coordinate with sign and precision."""
    return f"{axis}{value:+.{decimals}f}".replace("+", "")


def _format_feed(feed: float) -> str:
    """Format feedrate value."""
    if feed == int(feed):
        return f"F{int(feed)}"
    return f"F{feed:.1f}"


def _format_speed(speed: int) -> str:
    """Format spindle speed value."""
    return f"S{speed}"


def _format_tool(tool: int) -> str:
    """Format tool number."""
    return f"T{tool:02d}"


def _render_comment(text: str) -> str:
    """Render FANUC-style parentheses comment."""
    # FANUC comments must be in parentheses, no nested parens allowed
    safe_text = text.replace("(", "[").replace(")", "]")
    return f"({safe_text})"


def _render_header(
    program_number: int,
    comment: Optional[str],
    context: Dict[str, Any],
) -> List[str]:
    """Render FANUC program header."""
    lines = []
    
    # O-number
    lines.append(f"O{program_number:04d}")
    
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
    
    # Safety block
    lines.append("")
    lines.append(f"N10 {ABSOLUTE_MODE} {WORK_OFFSET_G54} {CANCEL_CUTTER_COMP}")
    
    return lines


def _render_footer() -> List[str]:
    """Render FANUC program footer."""
    return [
        "",
        _render_comment("END OF PROGRAM"),
        f"N9990 {SPINDLE_STOP}",
        f"N9995 {COOLANT_OFF}",
        f"N9999 {PROGRAM_END}",
        "%",
    ]


def _render_tool_change(
    tool_num: int,
    spindle_speed: int,
    spindle_dir: str,
    line_num: int,
) -> Tuple[List[str], int]:
    """Render tool change sequence."""
    lines = []
    
    # Tool change
    lines.append(f"N{line_num} {_format_tool(tool_num)} {TOOL_CHANGE}")
    line_num += 5
    
    # Spindle start
    spindle_code = SPINDLE_CW if spindle_dir.upper() == "CW" else SPINDLE_CCW
    lines.append(f"N{line_num} {_format_speed(spindle_speed)} {spindle_code}")
    line_num += 5
    
    return lines, line_num


def _render_moves(
    moves: List[Dict[str, Any]],
    start_line: int,
    feed_xy: float,
    feed_z: float,
) -> Tuple[List[str], int]:
    """Render a series of moves."""
    lines = []
    line_num = start_line
    
    for move in moves:
        move_type = move.get("type", "linear")
        
        if move_type == "rapid":
            # Rapid move
            parts = [f"N{line_num}", RAPID_MOVE]
            if "x" in move:
                parts.append(_format_coord("X", move["x"]))
            if "y" in move:
                parts.append(_format_coord("Y", move["y"]))
            if "z" in move:
                parts.append(_format_coord("Z", move["z"]))
            lines.append(" ".join(parts))
            
        elif move_type == "linear":
            # Linear interpolation
            parts = [f"N{line_num}", LINEAR_MOVE]
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
            parts = [f"N{line_num}", arc_code]
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
            # Dwell (P in milliseconds for FANUC)
            dwell_ms = int(move.get("seconds", 0) * 1000)
            lines.append(f"N{line_num} {DWELL} P{dwell_ms}")
        
        line_num += 5
    
    return lines, line_num


def _render_segments(
    segments: List[Dict[str, Any]],
    start_line: int,
    context: Dict[str, Any],
) -> Tuple[List[str], int]:
    """Render all segments (operations)."""
    lines = []
    line_num = start_line
    
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
            lines.append(f"N{line_num} {COOLANT_ON}")
            line_num += 5
        
        # Retract to safe Z
        lines.append(f"N{line_num} {RAPID_MOVE} {_format_coord('Z', safe_z)}")
        line_num += 5
        
        # Render moves
        moves = seg.get("moves", [])
        move_lines, line_num = _render_moves(moves, line_num, feed_xy, feed_z)
        lines.extend(move_lines)
        
        # Retract after segment
        lines.append(f"N{line_num} {RAPID_MOVE} {_format_coord('Z', safe_z)}")
        line_num += 5
        
        # Optional coolant off
        if seg.get("coolant", False):
            lines.append(f"N{line_num} {COOLANT_OFF}")
            line_num += 5
    
    return lines, line_num


def render(
    toolpaths: Dict[str, Any],
    context: Dict[str, Any],
    *,
    program_number: Optional[int] = None,
    program_comment: Optional[str] = None,
) -> str:
    """
    Render toolpaths to FANUC G-code.
    
    Args:
        toolpaths: Toolpath data with 'segments' list
        context: Machining context (feeds, speeds, tool info)
        program_number: O-number (default: 1)
        program_comment: Header comment
    
    Returns:
        FANUC G-code as string
    """
    prog_num = program_number or context.get("program_number", 1)
    comment = program_comment or context.get("program_comment", "LUTHIER TOOLBOX")
    
    lines = ["%"]
    
    # Header
    lines.extend(_render_header(prog_num, comment, context))
    
    # Tool change if specified
    line_num = 100
    if "tool" in context:
        tool = context["tool"]
        tool_num = tool.get("number", 1)
        spindle_speed = tool.get("spindle_speed", 18000)
        spindle_dir = tool.get("spindle_direction", "CW")
        tc_lines, line_num = _render_tool_change(
            tool_num, spindle_speed, spindle_dir, line_num
        )
        lines.extend(tc_lines)
    
    # Segments
    segments = toolpaths.get("segments", [])
    seg_lines, line_num = _render_segments(segments, line_num, context)
    lines.extend(seg_lines)
    
    # Footer
    lines.extend(_render_footer())
    
    return "\n".join(lines)


def get_fanuc_parameter_recommendations(
    tool_diameter: float,
    material: str,
) -> Dict[str, Any]:
    """
    Get recommended FANUC parameters based on tool and material.
    
    Returns dict with recommended feeds, speeds, and safety settings.
    """
    # Base recommendations (conservative)
    recs = {
        "feed_xy": 800,
        "feed_z": 150,
        "spindle_speed": 12000,
        "safe_z": 10.0,
        "spindle_direction": "CW",
    }
    
    # Adjust for material
    material_lower = material.lower()
    if "aluminum" in material_lower:
        recs["feed_xy"] = 1200
        recs["feed_z"] = 250
        recs["spindle_speed"] = 18000
    elif "steel" in material_lower:
        recs["feed_xy"] = 400
        recs["feed_z"] = 80
        recs["spindle_speed"] = 6000
    elif "wood" in material_lower or "mdf" in material_lower:
        recs["feed_xy"] = 2000
        recs["feed_z"] = 400
        recs["spindle_speed"] = 18000
    elif "plastic" in material_lower or "acrylic" in material_lower:
        recs["feed_xy"] = 1500
        recs["feed_z"] = 300
        recs["spindle_speed"] = 15000
    
    # Adjust for tool diameter (smaller = slower)
    if tool_diameter < 3.0:
        recs["feed_xy"] *= 0.6
        recs["feed_z"] *= 0.5
    elif tool_diameter < 6.0:
        recs["feed_xy"] *= 0.8
        recs["feed_z"] *= 0.7
    
    return recs


def validate_for_fanuc(
    toolpaths: Dict[str, Any],
    context: Dict[str, Any],
) -> List[str]:
    """
    Validate toolpaths for FANUC compatibility.
    
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
    elif feed_xy > 10000:
        warnings.append(f"feed_xy ({feed_xy}) exceeds typical FANUC max (10000)")
    
    # Check spindle speed
    if "tool" in context:
        speed = context["tool"].get("spindle_speed", 0)
        if speed <= 0:
            warnings.append("Invalid or missing spindle_speed")
        elif speed > 30000:
            warnings.append(f"Spindle speed ({speed}) exceeds typical max (30000)")
    
    # Check segments for issues
    segments = toolpaths.get("segments", [])
    for idx, seg in enumerate(segments):
        moves = seg.get("moves", [])
        if not moves:
            warnings.append(f"Segment {idx} has no moves")
        
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
    
    return warnings
