# N16.3 + N16.5 - G-code skeleton generator for ToolpathPlan
#
# N16.3: Basic G-code generation from ToolpathPlan
# N16.5: Machine profile variants (GRBL vs FANUC) + tool changes
#
# This is a minimal, conservative G-code exporter that:
#   - Supports multiple machine profiles (GRBL, FANUC)
#   - Uses metric units (G21) and absolute coordinates (G90)
#   - Includes tool change (Tn M6) and spindle control
#   - For each toolpath segment:
#       - Rapids to safe Z
#       - Rapids to segment start XY
#       - Plunges to segment Z at feed
#       - Cuts to segment end XY at feed

from __future__ import annotations

from app.core.safety import safety_critical

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

from .cnc_toolpath import ToolpathPlan, ToolpathSegment  # type: ignore


class MachineProfile(str, Enum):
    """Supported machine G-code profiles."""
    GRBL = "grbl"
    FANUC = "fanuc"


@dataclass
class GCodePostConfig:
    """Configuration for G-code post-processor."""
    profile: MachineProfile
    program_number: Optional[int] = None  # FANUC O-number
    safe_z_mm: float = 5.0
    spindle_rpm: int = 12000
    tool_id: int = 1


@safety_critical
def generate_gcode_from_toolpaths(
    plan: ToolpathPlan,
    post: GCodePostConfig,
) -> str:
    """
    Convert ToolpathPlan into a profile-aware G-code program.

    Arguments:
      plan: ToolpathPlan with segments in machine coordinates.
      post: Post-processor configuration (profile, tool, spindle, etc.).

    Returns:
      A string containing G-code lines, separated by newlines.
    """
    lines: List[str] = []

    # Profile-specific headers
    if post.profile == MachineProfile.FANUC:
        if post.program_number is not None:
            lines.append(f"O{post.program_number:04d}")
        lines.append(f"( RMOS Studio Rosette Ring {plan.ring_id} )")
        lines.append("G21")
        lines.append("G90")
        lines.append(f"T{post.tool_id} M6")
        lines.append(f"G0 Z{post.safe_z_mm:.3f}")
        lines.append(f"S{post.spindle_rpm} M3")
    else:  # GRBL and generic
        lines.append(f"( RMOS Studio Rosette Ring {plan.ring_id} )")
        lines.append("G21  ; mm")
        lines.append("G90  ; absolute")
        lines.append(f"T{post.tool_id} M6  ; tool change")
        lines.append(f"G0 Z{post.safe_z_mm:.3f}")
        lines.append(f"M3 S{post.spindle_rpm}")

    current_z = post.safe_z_mm
    current_x: Optional[float] = None
    current_y: Optional[float] = None

    for seg in plan.segments:
        # If Z for this segment is different, re-position:
        if current_z != post.safe_z_mm:
            lines.append(f"G0 Z{post.safe_z_mm:.3f}")
            current_z = post.safe_z_mm

        # Rapid to start XY if we've moved or this is the first segment
        if (
            current_x is None
            or current_y is None
            or abs(current_x - seg.x_start_mm) > 1e-6
            or abs(current_y - seg.y_start_mm) > 1e-6
        ):
            lines.append(
                f"G0 X{seg.x_start_mm:.3f} Y{seg.y_start_mm:.3f}"
            )
            current_x = seg.x_start_mm
            current_y = seg.y_start_mm

        # Plunge to cutting Z
        if current_z != seg.z_start_mm:
            lines.append(
                f"G1 Z{seg.z_start_mm:.3f} F{seg.feed_mm_per_min:.1f}"
            )
            current_z = seg.z_start_mm

        # Linear cut to end point
        lines.append(
            f"G1 X{seg.x_end_mm:.3f} Y{seg.y_end_mm:.3f} F{seg.feed_mm_per_min:.1f}"
        )
        current_x = seg.x_end_mm
        current_y = seg.y_end_mm

    # Profile-specific footers
    lines.append(f"G0 Z{post.safe_z_mm:.3f}")

    if post.profile == MachineProfile.FANUC:
        lines.append("M5")
        lines.append("G0 X0 Y0")
        lines.append("M30")
    else:  # GRBL
        lines.append("M5        ; spindle stop")
        lines.append("G0 X0 Y0  ; return home")
        lines.append("M30       ; program end")

    return "\n".join(lines)

