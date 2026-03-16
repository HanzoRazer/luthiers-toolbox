# app/cam/neck/truss_rod_channel.py

"""
Truss Rod Channel Generator (LP-GAP-03)

Generates G-code for truss rod channel routing.
Rectangular pocket with optional access pocket at nut end.

Coordinate convention (VINE-05):
- Y=0 at nut centerline
- +Y toward bridge
- X=0 centerline
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Optional

from .config import NeckPipelineConfig, TrussRodConfig, NeckToolSpec


@dataclass
class TrussRodResult:
    """Result of truss rod channel generation."""
    gcode_lines: List[str] = field(default_factory=list)
    operation_name: str = "OP10: Truss Rod Channel"
    tool_number: int = 2
    cut_time_seconds: float = 0.0
    passes: int = 0
    channel_volume_mm3: float = 0.0

    def to_dict(self) -> dict:
        return {
            "operation_name": self.operation_name,
            "tool_number": self.tool_number,
            "cut_time_seconds": round(self.cut_time_seconds, 1),
            "passes": self.passes,
            "channel_volume_mm3": round(self.channel_volume_mm3, 2),
            "gcode_line_count": len(self.gcode_lines),
        }


class TrussRodChannelGenerator:
    """
    Generate truss rod channel G-code.

    The truss rod channel is a rectangular pocket routed into the back of the neck.
    Typical dimensions:
    - Width: 6.35mm (1/4")
    - Depth: 9.525mm (3/8")
    - Length: ~406mm (16"), from nut area to ~12th fret

    Uses multi-pass depth strategy with configurable stepdown.
    """

    def __init__(self, config: NeckPipelineConfig):
        self.config = config
        self.tr_config = config.truss_rod
        self.tool = config.tools.get(2)  # Default truss rod tool

        self.safe_z_mm = 25.0
        self.retract_z_mm = 5.0

    def generate(self, tool: Optional[NeckToolSpec] = None) -> TrussRodResult:
        """Generate truss rod channel G-code."""
        if tool:
            self.tool = tool

        if not self.tool:
            raise ValueError("No tool specified for truss rod channel")

        result = TrussRodResult(tool_number=self.tool.tool_number)
        lines = result.gcode_lines

        # Header
        lines.append("")
        lines.append("( ============================================ )")
        lines.append(f"( {result.operation_name} )")
        lines.append("( ============================================ )")
        lines.append(f"( Width: {self.tr_config.width_mm:.2f}mm )")
        lines.append(f"( Depth: {self.tr_config.depth_mm:.2f}mm )")
        lines.append(f"( Length: {self.tr_config.length_mm:.2f}mm )")
        lines.append(f"( Tool: T{self.tool.tool_number} - {self.tool.name} )")

        # Tool change
        lines.extend(self._tool_change())

        # Calculate passes
        depth = self.tr_config.depth_mm
        stepdown = self.tool.stepdown_mm
        num_passes = max(1, math.ceil(depth / stepdown))
        result.passes = num_passes

        lines.append(f"( {num_passes} passes @ {stepdown:.2f}mm DOC )")

        # Calculate channel geometry
        # Channel is centered on X=0, starts at Y=start_offset, ends at Y=start_offset+length
        half_width = self.tr_config.width_mm / 2 - self.tool.diameter_mm / 2
        start_y = self.tr_config.start_offset_mm
        end_y = start_y + self.tr_config.length_mm

        # Generate passes
        for pass_num in range(num_passes):
            current_depth = -stepdown * (pass_num + 1)
            if current_depth < -depth:
                current_depth = -depth

            lines.append("")
            lines.append(f"( Pass {pass_num + 1}/{num_passes}: Z = {current_depth:.3f}mm )")

            # Move to start position
            lines.append(f"G0 Z{self.safe_z_mm:.3f}")
            lines.append(f"G0 X0.000 Y{start_y:.3f}")
            lines.append(f"G0 Z{self.retract_z_mm:.3f}")

            # Plunge
            lines.append(f"G1 Z{current_depth:.3f} F{self.tool.plunge_mm_min:.0f}")

            # Cut channel - zigzag pattern for full width coverage
            # First pass: move to +X side, cut along Y
            lines.append(f"G1 X{half_width:.3f} F{self.tool.feed_mm_min:.0f}")
            lines.append(f"G1 Y{end_y:.3f}")

            # Move to -X side
            lines.append(f"G1 X{-half_width:.3f}")

            # Cut back to start
            lines.append(f"G1 Y{start_y:.3f}")

            # Retract
            lines.append(f"G0 Z{self.retract_z_mm:.3f}")

        # Final retract
        lines.append(f"G0 Z{self.safe_z_mm:.3f}")

        # Calculate volume
        result.channel_volume_mm3 = (
            self.tr_config.width_mm *
            self.tr_config.depth_mm *
            self.tr_config.length_mm
        )

        # Estimate cut time (rough)
        total_distance = num_passes * (self.tr_config.length_mm * 2 + self.tr_config.width_mm * 2)
        result.cut_time_seconds = (total_distance / self.tool.feed_mm_min) * 60

        return result

    def _tool_change(self) -> List[str]:
        """Generate tool change sequence."""
        return [
            "",
            f"( Tool Change: T{self.tool.tool_number} - {self.tool.name} )",
            "M5",  # Spindle off
            f"T{self.tool.tool_number} M6",
            f"S{self.tool.rpm} M3",
            "G4 P2",  # Dwell for spindle
            f"G0 Z{self.safe_z_mm:.3f}",
        ]

    def generate_access_pocket(self) -> List[str]:
        """
        Generate optional access pocket at nut end.

        This wider pocket allows access for truss rod adjustment wrench.
        """
        if self.tr_config.access_pocket_width_mm <= self.tr_config.width_mm:
            return []

        lines = []
        lines.append("")
        lines.append("( Access Pocket at Nut End )")

        pocket_depth = self.tr_config.depth_mm * 0.75  # Shallower
        half_width = self.tr_config.access_pocket_width_mm / 2 - self.tool.diameter_mm / 2
        start_y = 0.0
        end_y = self.tr_config.access_pocket_length_mm

        num_passes = max(1, math.ceil(pocket_depth / self.tool.stepdown_mm))

        for pass_num in range(num_passes):
            current_depth = -self.tool.stepdown_mm * (pass_num + 1)
            if current_depth < -pocket_depth:
                current_depth = -pocket_depth

            lines.append(f"G0 Z{self.safe_z_mm:.3f}")
            lines.append(f"G0 X{-half_width:.3f} Y{start_y:.3f}")
            lines.append(f"G0 Z{self.retract_z_mm:.3f}")
            lines.append(f"G1 Z{current_depth:.3f} F{self.tool.plunge_mm_min:.0f}")
            lines.append(f"G1 X{half_width:.3f} F{self.tool.feed_mm_min:.0f}")
            lines.append(f"G1 Y{end_y:.3f}")
            lines.append(f"G1 X{-half_width:.3f}")
            lines.append(f"G1 Y{start_y:.3f}")
            lines.append(f"G0 Z{self.retract_z_mm:.3f}")

        lines.append(f"G0 Z{self.safe_z_mm:.3f}")
        return lines
