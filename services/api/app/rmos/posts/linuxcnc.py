"""
LinuxCNC Post-Processor

Renders toolpaths to LinuxCNC-compatible G-code with:
- No line numbers (standard)
- Semicolon comments
- G64 path blending support
- Standard RS274NGC compliant output

Reference: LinuxCNC G-code Quick Reference
https://linuxcnc.org/docs/html/gcode/g-code.html
"""
from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .base import DialectConfig, Dialect, DIALECT_CONFIGS

# LinuxCNC G-code constants
RAPID_MOVE = "G0"
LINEAR_MOVE = "G1"
CW_ARC = "G2"
CCW_ARC = "G3"
DWELL = "G4"
ABSOLUTE_MODE = "G90"
INCREMENTAL_MODE = "G91"
UNITS_MM = "G21"
UNITS_INCH = "G20"
XY_PLANE = "G17"
XZ_PLANE = "G18"
YZ_PLANE = "G19"
PATH_BLEND = "G64"
EXACT_STOP = "G61"
SPINDLE_CW = "M3"
SPINDLE_CCW = "M4"
SPINDLE_STOP = "M5"
COOLANT_FLOOD = "M8"
COOLANT_MIST = "M7"
COOLANT_OFF = "M9"
PROGRAM_END = "M2"
PROGRAM_STOP = "M0"
OPTIONAL_STOP = "M1"


def _format_coord(axis: str, value: float, decimals: int = 4) -> str:
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
    """Render LinuxCNC-style semicolon comment."""
    return f"; {text}"


def _render_header(
    comment: Optional[str],
    context: Dict[str, Any],
) -> List[str]:
    """Render LinuxCNC program header."""
    lines = []

    # Header comment
    if comment:
        lines.append(_render_comment(comment))

    # Timestamp
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines.append(_render_comment(f"Generated: {ts}"))
    lines.append(_render_comment("Post: LinuxCNC (RS274NGC)"))

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
    lines.append(f"{units} {ABSOLUTE_MODE} {XY_PLANE}")

    # Path blending (LinuxCNC-specific)
    path_tolerance = context.get("path_tolerance", 0.002)
    if context.get("enable_path_blending", True):
        lines.append(f"{PATH_BLEND} P{path_tolerance}")
        lines.append(_render_comment(f"Path blending tolerance: {path_tolerance}mm"))

    return lines


def _render_footer() -> List[str]:
    """Render LinuxCNC program footer."""
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
            # Arc interpolation (LinuxCNC prefers I/J mode)
            arc_code = CW_ARC if move_type == "cw_arc" else CCW_ARC
            parts = [arc_code]
            parts.append(_format_coord("X", move["x"]))
            parts.append(_format_coord("Y", move["y"]))
            if "z" in move:
                parts.append(_format_coord("Z", move["z"]))
            if "i" in move:
                parts.append(_format_coord("I", move["i"]))
            if "j" in move:
                parts.append(_format_coord("J", move["j"]))
            if "r" in move:
                parts.append(_format_coord("R", move["r"]))
            parts.append(_format_feed(feed_xy))
            lines.append(" ".join(parts))

        elif move_type == "dwell":
            # Dwell (P in seconds for LinuxCNC)
            dwell_ms = move.get("p", move.get("seconds", 0) * 1000)
            dwell_sec = dwell_ms / 1000.0
            lines.append(f"{DWELL} P{dwell_sec:.3f}")

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
    Render toolpaths to LinuxCNC G-code.

    Args:
        toolpaths: Toolpath data with 'segments' list
        context: Machining context (feeds, speeds, tool info)
        program_comment: Header comment

    Returns:
        LinuxCNC G-code as string

    LinuxCNC-specific features:
    - G64 path blending for smooth motion
    - RS274NGC compliant output
    - P-word in seconds for G4 dwell
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


def render_moves(
    moves: List[Dict[str, Any]],
    context: Dict[str, Any],
) -> List[str]:
    """
    Render just the moves without program structure.

    Useful for inserting moves into existing programs.
    """
    feed_xy = context.get("feed_xy", 1000)
    feed_z = context.get("feed_z", 200)
    return _render_moves(moves, feed_xy, feed_z)


def get_dialect_config() -> DialectConfig:
    """Return LinuxCNC dialect configuration."""
    return DIALECT_CONFIGS[Dialect.LINUXCNC]


def validate_for_linuxcnc(
    toolpaths: Dict[str, Any],
    context: Dict[str, Any],
) -> List[str]:
    """
    Validate toolpaths for LinuxCNC compatibility.

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
        warnings.append(f"feed_xy ({feed_xy}) may be high for typical machines")

    # Check spindle speed
    if "tool" in context:
        speed = context["tool"].get("spindle_speed", 0)
        if speed <= 0:
            warnings.append("Invalid or missing spindle_speed")
        elif speed > 24000:
            warnings.append(
                f"Spindle speed ({speed}) exceeds typical max (24000)"
            )

    # Check path tolerance
    path_tolerance = context.get("path_tolerance", 0.002)
    if path_tolerance < 0.0001:
        warnings.append(
            f"Path tolerance ({path_tolerance}) is very tight, may cause jerky motion"
        )
    elif path_tolerance > 0.1:
        warnings.append(
            f"Path tolerance ({path_tolerance}) is loose, may affect accuracy"
        )

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

            # Arc checks
            if move.get("type") in ("cw_arc", "ccw_arc"):
                has_ij = "i" in move or "j" in move
                has_r = "r" in move
                if not has_ij and not has_r:
                    warnings.append(
                        f"Segment {idx} move {move_idx}: "
                        "arc needs I/J or R parameter"
                    )

    return warnings


# Alias for consistency with other post-processors
validate = validate_for_linuxcnc
