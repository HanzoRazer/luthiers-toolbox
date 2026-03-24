# app/cam/neck/fret_slots.py

"""
Fret Slot Generator (LP-GAP-03)

Generates G-code for fret slot cutting, integrating with the neck CNC pipeline.
Connects to existing fret_slots_cam.py calculator for position calculations.

Features:
- 12-TET equal temperament fret positions
- Compound radius support (depth varies across width)
- Fan-fret angle support (future)
- Station-aware slot depths for curved fretboards

Coordinate convention (VINE-05):
- Y=0 at nut centerline
- +Y toward bridge
- X=0 centerline
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Optional

from .config import NeckPipelineConfig, FretSlotConfig, NeckToolSpec
from ..post_processor import PostProcessor, PostConfig, ToolSpec

from app.core.safety import safety_critical


@dataclass
class FretSlotPosition:
    """Position data for a single fret slot."""
    fret_number: int
    y_mm: float  # Distance from nut along Y axis
    width_at_fret_mm: float  # Fretboard width at this fret
    slot_depth_mm: float  # Slot cutting depth
    angle_deg: float = 0.0  # For fan-fret (0 = perpendicular)

    def to_dict(self) -> dict:
        return {
            "fret_number": self.fret_number,
            "y_mm": round(self.y_mm, 3),
            "width_at_fret_mm": round(self.width_at_fret_mm, 2),
            "slot_depth_mm": round(self.slot_depth_mm, 3),
            "angle_deg": round(self.angle_deg, 2),
        }


@dataclass
class FretSlotResult:
    """Result of fret slot generation."""
    gcode_lines: List[str] = field(default_factory=list)
    operation_name: str = "OP50: Fret Slots"
    tool_number: int = 4
    cut_time_seconds: float = 0.0
    slots: List[FretSlotPosition] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "operation_name": self.operation_name,
            "tool_number": self.tool_number,
            "cut_time_seconds": round(self.cut_time_seconds, 1),
            "slot_count": len(self.slots),
            "gcode_line_count": len(self.gcode_lines),
            "slots": [s.to_dict() for s in self.slots],
        }


class FretSlotGenerator:
    """
    Generate fret slot cutting G-code.

    Uses 12-TET (12-tone equal temperament) formula for fret positions:
        fret_position = scale_length * (1 - 1 / 2^(fret/12))

    Slot cutting is done with a thin kerf saw blade, typically:
    - 0.023" (0.584mm) for standard fret wire
    - 0.020" (0.508mm) for narrow fret wire

    For compound radius fretboards, slot depth is adjusted based on
    the difference between surface height at center vs edges.
    """

    def __init__(self, config: NeckPipelineConfig, post_processor: Optional[PostProcessor] = None):
        self.config = config
        self.fs_config = config.fret_slots
        self.tool = config.tools.get(4)  # Fret slot saw

        self.safe_z_mm = 25.0
        self.retract_z_mm = 5.0

        # Use provided post-processor or create default
        if post_processor is not None:
            self.post_processor = post_processor
        else:
            self.post_processor = PostProcessor(PostConfig(safe_z_mm=self.safe_z_mm))

    def _fret_position(self, fret_number: int) -> float:
        """Calculate fret position in mm from nut using 12-TET formula."""
        if fret_number <= 0:
            return 0.0
        return self.config.scale_length_mm * (1 - (1 / (2 ** (fret_number / 12))))

    def _width_at_y(self, y_mm: float) -> float:
        """Calculate fretboard width at Y position (linear taper)."""
        if y_mm <= 0:
            return self.config.nut_width_mm

        body_joint_y = self.config.body_joint_y_mm
        if y_mm >= body_joint_y:
            return self.config.heel_width_mm

        t = y_mm / body_joint_y
        return self.config.nut_width_mm + t * (self.config.heel_width_mm - self.config.nut_width_mm)

    @safety_critical
    def _slot_depth_at_position(self, fret_number: int, x_mm: float = 0.0) -> float:
        """
        Calculate slot depth at position, accounting for compound radius.

        For compound radius fretboards, the surface curves differently at
        nut vs heel. The slot must be deep enough to accommodate the fret
        tang at the highest point of the curve.
        """
        base_depth = self.fs_config.slot_depth_mm

        if not self.fs_config.compound_radius:
            return base_depth

        # For compound radius: interpolate radius based on fret position
        y = self._fret_position(fret_number)
        body_joint_y = self.config.body_joint_y_mm

        if y >= body_joint_y:
            t = 1.0
        else:
            t = y / body_joint_y

        radius_at_fret = (
            self.fs_config.radius_at_nut_mm +
            t * (self.fs_config.radius_at_heel_mm - self.fs_config.radius_at_nut_mm)
        )

        # Calculate surface height difference from center to edge
        half_width = self._width_at_y(y) / 2
        if radius_at_fret > 0:
            # Height drop from center to edge: r - sqrt(r^2 - x^2)
            height_drop = radius_at_fret - math.sqrt(max(0, radius_at_fret ** 2 - half_width ** 2))
            # Add extra depth to ensure full slot at edges
            return base_depth + height_drop * 0.5
        else:
            return base_depth

    def calculate_slot_positions(self) -> List[FretSlotPosition]:
        """Calculate all fret slot positions."""
        slots = []

        for fret in range(1, self.fs_config.fret_count + 1):
            y = self._fret_position(fret)
            width = self._width_at_y(y)
            depth = self._slot_depth_at_position(fret)

            slot = FretSlotPosition(
                fret_number=fret,
                y_mm=y,
                width_at_fret_mm=width,
                slot_depth_mm=depth,
            )
            slots.append(slot)

        return slots

    @safety_critical
    def generate(self, tool: Optional[NeckToolSpec] = None) -> FretSlotResult:
        """Generate fret slot cutting G-code."""
        if tool:
            self.tool = tool

        if not self.tool:
            raise ValueError("No tool specified for fret slots")

        result = FretSlotResult(tool_number=self.tool.tool_number)
        lines = result.gcode_lines

        # Calculate slot positions
        slots = self.calculate_slot_positions()
        result.slots = slots

        # Header
        lines.append("")
        lines.append("( ============================================ )")
        lines.append(f"( {result.operation_name} )")
        lines.append("( ============================================ )")
        lines.append(f"( Fret count: {self.fs_config.fret_count} )")
        lines.append(f"( Scale length: {self.config.scale_length_mm:.2f}mm )")
        lines.append(f"( Slot width: {self.fs_config.slot_width_mm:.3f}mm )")
        lines.append(f"( Slot depth: {self.fs_config.slot_depth_mm:.3f}mm )")
        lines.append(f"( Tool: T{self.tool.tool_number} - {self.tool.name} )")

        if self.fs_config.compound_radius:
            lines.append(f"( Compound radius: {self.fs_config.radius_at_nut_mm:.0f}mm -> {self.fs_config.radius_at_heel_mm:.0f}mm )")

        # Tool change
        lines.extend(self._tool_change())

        # Generate slot cuts
        for slot in slots:
            lines.append("")
            lines.append(f"( Fret {slot.fret_number}: Y = {slot.y_mm:.3f}mm )")

            half_width = slot.width_at_fret_mm / 2 - 2.0  # 2mm margin from edge
            slot_z = -slot.slot_depth_mm

            # Move to slot start position (bass side)
            lines.append(f"G0 Z{self.safe_z_mm:.3f}")
            lines.append(f"G0 X{-half_width:.3f} Y{slot.y_mm:.3f}")
            lines.append(f"G0 Z{self.retract_z_mm:.3f}")

            # Plunge to depth
            lines.append(f"G1 Z{slot_z:.3f} F{self.tool.plunge_mm_min:.0f}")

            # Cut across fretboard (bass to treble)
            lines.append(f"G1 X{half_width:.3f} F{self.tool.feed_mm_min:.0f}")

            # Retract
            lines.append(f"G0 Z{self.retract_z_mm:.3f}")

        lines.append(f"G0 Z{self.safe_z_mm:.3f}")

        # Estimate cut time
        total_cut_distance = sum(s.width_at_fret_mm for s in slots)
        result.cut_time_seconds = (total_cut_distance / self.tool.feed_mm_min) * 60

        return result

    def _tool_change(self) -> List[str]:
        """Generate tool change sequence via PostProcessor."""
        tool_spec = ToolSpec(
            tool_number=self.tool.tool_number,
            name=self.tool.name,
            rpm=self.tool.rpm,
            diameter_mm=self.tool.diameter_mm,
        )
        return self.post_processor.tool_change(tool=tool_spec)
