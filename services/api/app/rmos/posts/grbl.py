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
from typing import Any, Dict, List, Optional

from .base import (
    DialectConfig, Dialect, DIALECT_CONFIGS,
    format_coord, format_feed, format_speed,
    render_comment, render_spindle_start, render_footer,
    render_moves_base, render_segments_base,
)

# GRBL-specific constants
COORD_DECIMALS = 3  # GRBL uses 3 decimal places


def _render_header(
    comment: Optional[str],
    context: Dict[str, Any],
) -> List[str]:
    """Render GRBL program header."""
    lines = []

    # Header comment
    if comment:
        lines.append(render_comment(comment))

    # Timestamp
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines.append(render_comment(f"Generated: {ts}"))

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
    lines.append(f"{units} G90")

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
        lines.append(render_spindle_start(spindle_speed, spindle_dir))

    # Segments (use shared function)
    segments = toolpaths.get("segments", [])
    seg_lines = render_segments_base(
        segments, context,
        coord_decimals=COORD_DECIMALS,
        dwell_in_seconds=True,  # GRBL uses seconds for G4
    )
    lines.extend(seg_lines)

    # Footer
    lines.extend(render_footer())

    return chr(10).join(lines)


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


def get_dialect_config() -> DialectConfig:
    """Return GRBL dialect configuration."""
    return DIALECT_CONFIGS[Dialect.GRBL]


# Alias for consistency
validate = validate_for_grbl
