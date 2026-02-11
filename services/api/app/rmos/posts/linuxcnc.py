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

from .base import (
    DialectConfig, Dialect, DIALECT_CONFIGS,
    format_coord, format_feed, format_speed,
    render_comment, render_spindle_start, render_footer,
    render_moves_base, render_segments_base,
)

# LinuxCNC-specific constants
COORD_DECIMALS = 4  # LinuxCNC uses 4 decimal places


def _render_header(
    comment: Optional[str],
    context: Dict[str, Any],
) -> List[str]:
    """Render LinuxCNC program header."""
    lines = []

    # Header comment
    if comment:
        lines.append(render_comment(comment))

    # Timestamp
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines.append(render_comment(f"Generated: {ts}"))
    lines.append(render_comment("Post: LinuxCNC (RS274NGC)"))

    # Tool info if provided
    if "tool" in context:
        tool = context["tool"]
        tool_desc = tool.get("description", f"Tool #{tool.get('number', 1)}")
        lines.append(render_comment(f"Tool: {tool_desc}"))

    # Material info if provided
    if "material" in context:
        mat = context["material"]
        mat_name = mat.get("name", "Unknown")
        lines.append(render_comment(f"Material: {mat_name}"))

    # Setup block
    lines.append("")
    units = "G21" if context.get("units", "mm") == "mm" else "G20"
    lines.append(f"{units} G90 G17")  # G17 = XY plane

    # Path blending (LinuxCNC-specific)
    path_tolerance = context.get("path_tolerance", 0.002)
    if context.get("enable_path_blending", True):
        lines.append(f"G64 P{path_tolerance}")
        lines.append(render_comment(f"Path blending tolerance: {path_tolerance}mm"))

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
        lines.append(render_spindle_start(spindle_speed, spindle_dir))

    # Segments (use shared function)
    segments = toolpaths.get("segments", [])
    seg_lines = render_segments_base(
        segments, context,
        coord_decimals=COORD_DECIMALS,
        dwell_in_seconds=True,  # LinuxCNC uses seconds for G4
    )
    lines.extend(seg_lines)

    # Footer
    lines.extend(render_footer())

    return chr(10).join(lines)


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
    return render_moves_base(
        moves, feed_xy, feed_z,
        coord_decimals=COORD_DECIMALS,
        dwell_in_seconds=True,
    )


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
