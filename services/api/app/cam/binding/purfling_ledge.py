"""
Purfling Ledge Toolpath Generator

Generates G-code for routing the purfling ledge inside the binding channel.
Purfling is a thin decorative strip inset from the binding.

The purfling ledge is a shallow channel cut inside the binding area
to accept the purfling strip.

Resolves:
- OM-PURF-02: No purfling ledge operation
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict, Any

from app.core.safety import safety_critical
from .offset_geometry import generate_purfling_offset

Pt = Tuple[float, float]


@dataclass
class PurflingConfig:
    """Configuration for purfling ledge routing."""

    # Ledge dimensions
    ledge_width_mm: float = 1.0  # Width of purfling strip
    ledge_depth_mm: float = 0.8  # Shallow depth for purfling

    # Position relative to body edge
    offset_from_edge_mm: float = 1.5  # Typically binding width

    # Tool parameters
    tool_diameter_mm: float = 1.5  # Small bit for purfling
    tool_flute_length_mm: float = 6.0

    # Cut parameters (single pass typically)
    stepdown_mm: float = 0.8  # Usually single pass

    # Feed rates (mm/min) - slower for small bit
    feed_rate_xy: float = 600.0
    feed_rate_z: float = 200.0
    plunge_rate: float = 100.0

    # Safety
    safe_z_mm: float = 5.0
    retract_z_mm: float = 2.0

    # Direction
    climb_milling: bool = True


@dataclass
class PurflingResult:
    """Result of purfling ledge generation."""

    gcode: str
    toolpath_points: List[Dict[str, Any]]
    total_length_mm: float
    estimated_time_seconds: float
    pass_count: int
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gcode": self.gcode,
            "toolpath_points": self.toolpath_points,
            "total_length_mm": self.total_length_mm,
            "estimated_time_seconds": self.estimated_time_seconds,
            "pass_count": self.pass_count,
            "warnings": self.warnings,
        }


class PurflingLedge:
    """
    Purfling ledge toolpath generator.

    Routes a shallow ledge inside the binding channel to accept
    decorative purfling strips. This is typically run after the
    binding channel is cut.
    """

    def __init__(
        self,
        outline: List[Pt],
        config: Optional[PurflingConfig] = None,
    ):
        """
        Initialize purfling ledge generator.

        Args:
            outline: Body outline polygon (closed)
            config: Ledge configuration
        """
        self.outline = outline
        self.config = config or PurflingConfig()
        self._warnings: List[str] = []

    @safety_critical
    def generate(self) -> PurflingResult:
        """
        Generate purfling ledge toolpath.

        Returns:
            PurflingResult with G-code and metadata
        """
        self._warnings = []

        # Validate
        if len(self.outline) < 3:
            self._warnings.append("Outline has fewer than 3 points")
            return self._empty_result()

        # Validate tool size
        if self.config.tool_diameter_mm > self.config.ledge_width_mm:
            self._warnings.append(
                f"Tool diameter ({self.config.tool_diameter_mm}mm) exceeds "
                f"ledge width ({self.config.ledge_width_mm}mm). "
                "Ledge will be wider than specified."
            )

        # Generate offset path
        path = generate_purfling_offset(
            self.outline,
            self.config.offset_from_edge_mm,
            self.config.ledge_width_mm,
            self.config.tool_diameter_mm,
        )

        if not path:
            self._warnings.append("Failed to generate purfling offset path")
            return self._empty_result()

        # Calculate depth passes
        depth_passes = self._calculate_depth_passes()

        # Generate G-code
        gcode_lines = self._generate_gcode(path, depth_passes)

        # Calculate metrics
        toolpath_points = self._extract_toolpath_points(gcode_lines)
        total_length = self._calculate_total_length(toolpath_points)
        estimated_time = self._estimate_time(total_length, len(depth_passes))

        return PurflingResult(
            gcode="\n".join(gcode_lines),
            toolpath_points=toolpath_points,
            total_length_mm=round(total_length, 2),
            estimated_time_seconds=round(estimated_time, 1),
            pass_count=len(depth_passes),
            warnings=self._warnings,
        )

    def generate_gcode(self) -> str:
        """Generate G-code string (convenience method)."""
        return self.generate().gcode

    def _calculate_depth_passes(self) -> List[float]:
        """Calculate Z depths for each pass."""
        passes = []
        current_depth = 0.0

        while current_depth < self.config.ledge_depth_mm:
            current_depth += self.config.stepdown_mm
            if current_depth > self.config.ledge_depth_mm:
                current_depth = self.config.ledge_depth_mm
            passes.append(-current_depth)

        return passes

    def _generate_gcode(
        self,
        path: List[Pt],
        depth_passes: List[float],
    ) -> List[str]:
        """Generate complete G-code program."""
        lines = []

        # Header
        lines.append("(Purfling Ledge Toolpath)")
        lines.append(f"(Ledge: {self.config.ledge_width_mm}mm W x {self.config.ledge_depth_mm}mm D)")
        lines.append(f"(Offset from edge: {self.config.offset_from_edge_mm}mm)")
        lines.append(f"(Tool: {self.config.tool_diameter_mm}mm bit)")
        lines.append(f"(Depth passes: {len(depth_passes)})")
        lines.append("")

        # Setup
        lines.append("G21 (Units: mm)")
        lines.append("G90 (Absolute positioning)")
        lines.append("G17 (XY plane)")
        lines.append(f"G0 Z{self.config.safe_z_mm:.3f} (Safe height)")
        lines.append("M3 S20000 (Spindle on - high RPM for small bit)")
        lines.append("")

        # Reverse for conventional if not climb
        if not self.config.climb_milling:
            path = list(reversed(path))

        for pass_idx, z_depth in enumerate(depth_passes):
            lines.append(f"(Pass {pass_idx + 1}: Z={z_depth:.3f})")

            # Rapid to start
            start = path[0]
            lines.append(f"G0 X{start[0]:.3f} Y{start[1]:.3f}")
            lines.append(f"G0 Z{self.config.retract_z_mm:.3f}")

            # Plunge
            lines.append(f"G1 Z{z_depth:.3f} F{self.config.plunge_rate:.0f}")

            # Cut around path
            for pt in path[1:]:
                lines.append(
                    f"G1 X{pt[0]:.3f} Y{pt[1]:.3f} F{self.config.feed_rate_xy:.0f}"
                )

            # Close path
            lines.append(
                f"G1 X{start[0]:.3f} Y{start[1]:.3f} F{self.config.feed_rate_xy:.0f}"
            )

            # Retract
            lines.append(f"G0 Z{self.config.safe_z_mm:.3f}")
            lines.append("")

        # Footer
        lines.append("M5 (Spindle off)")
        lines.append("G0 Z{:.3f} (Final retract)".format(self.config.safe_z_mm))
        lines.append("M30 (Program end)")

        return lines

    def _extract_toolpath_points(self, gcode_lines: List[str]) -> List[Dict[str, Any]]:
        """Extract toolpath points for visualization."""
        points = []
        current = {"x": 0.0, "y": 0.0, "z": 0.0}

        for line in gcode_lines:
            if line.startswith("G0") or line.startswith("G1"):
                point = dict(current)
                point["rapid"] = line.startswith("G0")

                for part in line.split():
                    if part.startswith("X"):
                        point["x"] = float(part[1:])
                        current["x"] = point["x"]
                    elif part.startswith("Y"):
                        point["y"] = float(part[1:])
                        current["y"] = point["y"]
                    elif part.startswith("Z"):
                        point["z"] = float(part[1:])
                        current["z"] = point["z"]

                points.append(point)

        return points

    def _calculate_total_length(self, points: List[Dict[str, Any]]) -> float:
        """Calculate total toolpath length."""
        if len(points) < 2:
            return 0.0

        length = 0.0
        for i in range(1, len(points)):
            p1 = points[i - 1]
            p2 = points[i]
            dx = p2.get("x", 0) - p1.get("x", 0)
            dy = p2.get("y", 0) - p1.get("y", 0)
            dz = p2.get("z", 0) - p1.get("z", 0)
            length += (dx**2 + dy**2 + dz**2) ** 0.5

        return length

    def _estimate_time(self, total_length: float, depth_passes: int) -> float:
        """Estimate machining time in seconds."""
        if total_length <= 0:
            return 0.0

        # Time for cutting moves
        cut_time = (total_length / self.config.feed_rate_xy) * 60.0

        # Add time for plunges
        plunge_time = (
            self.config.ledge_depth_mm *
            depth_passes /
            self.config.plunge_rate
        ) * 60.0

        # Add overhead
        total_time = (cut_time + plunge_time) * 1.2

        return total_time

    def _empty_result(self) -> PurflingResult:
        """Return empty result for error cases."""
        return PurflingResult(
            gcode="",
            toolpath_points=[],
            total_length_mm=0.0,
            estimated_time_seconds=0.0,
            pass_count=0,
            warnings=self._warnings,
        )
