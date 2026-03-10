"""
Profile Toolpath Generator

Generates outside-contour toolpaths for body perimeter routing.
This is the core module that resolves 4 instrument gaps:
- OM-GAP-02: OM-28 body perimeter profiling
- BEN-GAP-03: Benedetto body perimeter profiling
- VINE-07: J45 Vine body perimeter profiling
- FV-GAP-03: Flying V body perimeter profiling

Features:
- Cutter compensation (tool radius offset)
- Holding tabs to keep workpiece attached
- Lead-in/lead-out arcs for smooth entry/exit
- Climb vs conventional milling direction
- Multi-pass depth stepping
- Safe-Z retract between operations
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Tuple, Dict, Any

from app.core.safety import safety_critical
from app.cam.polygon_offset_n17 import offset_polygon_mm

Pt = Tuple[float, float]


class MillingDirection(str, Enum):
    """Milling direction relative to tool rotation."""
    CLIMB = "climb"  # Tool moves with rotation (preferred for CNC)
    CONVENTIONAL = "conventional"  # Tool moves against rotation


@dataclass
class ProfileConfig:
    """Configuration for profile toolpath generation."""

    # Tool parameters
    tool_diameter_mm: float = 6.35  # 1/4" endmill default
    tool_flute_length_mm: float = 25.0

    # Cut parameters
    cut_depth_mm: float = 25.0  # Total depth to cut
    stepdown_mm: float = 6.0  # Depth per pass
    stepover_mm: Optional[float] = None  # For finishing passes

    # Feed rates (mm/min)
    feed_rate_xy: float = 1500.0
    feed_rate_z: float = 500.0
    plunge_rate: float = 300.0

    # Safety
    safe_z_mm: float = 5.0
    retract_z_mm: float = 2.0  # Quick retract above material

    # Tabs
    tab_count: int = 4
    tab_width_mm: float = 10.0
    tab_height_mm: float = 3.0  # Leave 3mm for tabs

    # Lead-in/out
    lead_in_radius_mm: float = 5.0  # Arc radius for entry
    lead_in_angle_deg: float = 90.0  # Arc sweep angle

    # Direction
    direction: MillingDirection = MillingDirection.CLIMB

    # Compensation
    compensation_side: str = "outside"  # "outside" or "inside"

    # Finishing
    finishing_pass: bool = True
    finishing_allowance_mm: float = 0.3  # Leave for finishing


@dataclass
class ProfileResult:
    """Result of profile toolpath generation."""

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


class ProfileToolpath:
    """
    Outside-contour toolpath generator.

    Takes a closed polygon (body outline) and generates G-code for
    perimeter routing with tabs, lead-in arcs, and multi-pass depth.
    """

    def __init__(
        self,
        outline: List[Pt],
        config: Optional[ProfileConfig] = None,
    ):
        """
        Initialize profile toolpath generator.

        Args:
            outline: Closed polygon as list of (x, y) points in mm
            config: Toolpath configuration (uses defaults if None)
        """
        self.outline = outline
        self.config = config or ProfileConfig()
        self._warnings: List[str] = []

    @safety_critical
    def generate(self) -> ProfileResult:
        """
        Generate the profile toolpath.

        Returns:
            ProfileResult with G-code and metadata
        """
        self._warnings = []

        # Validate outline
        if len(self.outline) < 3:
            self._warnings.append("Outline has fewer than 3 points")
            return self._empty_result()

        # Calculate tool radius offset
        tool_radius = self.config.tool_diameter_mm / 2.0

        # Apply cutter compensation (offset polygon outward)
        if self.config.compensation_side == "outside":
            offset = tool_radius
        else:
            offset = -tool_radius

        # For roughing, add finishing allowance
        if self.config.finishing_pass:
            roughing_offset = offset + self.config.finishing_allowance_mm
        else:
            roughing_offset = offset

        # Generate offset path for roughing
        roughing_paths = offset_polygon_mm(
            self.outline,
            roughing_offset,
            join_type="round",
        )

        if not roughing_paths:
            self._warnings.append("Failed to offset outline - check geometry")
            return self._empty_result()

        roughing_path = roughing_paths[0]  # Use largest polygon

        # Generate offset path for finishing (if enabled)
        finishing_path = None
        if self.config.finishing_pass:
            finishing_paths = offset_polygon_mm(
                self.outline,
                offset,
                join_type="round",
            )
            if finishing_paths:
                finishing_path = finishing_paths[0]

        # Calculate number of depth passes
        passes = self._calculate_passes()

        # Generate tabs
        from .tabs import TabGenerator, TabConfig
        tab_gen = TabGenerator(TabConfig(
            count=self.config.tab_count,
            width_mm=self.config.tab_width_mm,
            height_mm=self.config.tab_height_mm,
        ))

        perimeter_length = self._perimeter_length(roughing_path)
        tabs = tab_gen.generate_tabs(roughing_path, perimeter_length)

        # Reorder path for climb/conventional
        if self.config.direction == MillingDirection.CONVENTIONAL:
            roughing_path = list(reversed(roughing_path))
            if finishing_path:
                finishing_path = list(reversed(finishing_path))

        # Generate G-code
        gcode_lines = self._generate_gcode(
            roughing_path=roughing_path,
            finishing_path=finishing_path,
            passes=passes,
            tabs=tabs,
        )

        # Calculate toolpath metrics
        toolpath_points = self._extract_toolpath_points(gcode_lines)
        total_length = self._calculate_total_length(toolpath_points)
        estimated_time = self._estimate_time(total_length)

        gcode = "\n".join(gcode_lines)

        return ProfileResult(
            gcode=gcode,
            toolpath_points=toolpath_points,
            total_length_mm=round(total_length, 2),
            estimated_time_seconds=round(estimated_time, 1),
            pass_count=len(passes) + (1 if finishing_path else 0),
            warnings=self._warnings,
        )

    def generate_gcode(self) -> str:
        """Generate G-code string (convenience method)."""
        return self.generate().gcode

    def _calculate_passes(self) -> List[float]:
        """Calculate Z depths for each roughing pass."""
        passes = []
        current_depth = 0.0

        # Reserve tab height at bottom
        effective_depth = self.config.cut_depth_mm - self.config.tab_height_mm

        while current_depth < effective_depth:
            current_depth += self.config.stepdown_mm
            if current_depth > effective_depth:
                current_depth = effective_depth
            passes.append(-current_depth)  # Negative Z for depth

        return passes

    def _generate_gcode(
        self,
        roughing_path: List[Pt],
        finishing_path: Optional[List[Pt]],
        passes: List[float],
        tabs: List,
    ) -> List[str]:
        """Generate complete G-code program."""
        lines = []

        # Header
        lines.append("(Profile Toolpath - Body Perimeter)")
        lines.append(f"(Tool: {self.config.tool_diameter_mm}mm endmill)")
        lines.append(f"(Depth: {self.config.cut_depth_mm}mm in {len(passes)} passes)")
        lines.append(f"(Direction: {self.config.direction.value})")
        lines.append(f"(Tabs: {len(tabs)})")
        lines.append("")

        # Setup
        lines.append("G21 (Units: mm)")
        lines.append("G90 (Absolute positioning)")
        lines.append("G17 (XY plane)")
        lines.append(f"G0 Z{self.config.safe_z_mm:.3f} (Safe height)")
        lines.append("M3 S18000 (Spindle on)")
        lines.append("")

        # Find start point and lead-in position
        start_pt = roughing_path[0]
        lead_in_pt = self._calculate_lead_in_point(roughing_path)

        # Rapid to lead-in position
        lines.append(f"G0 X{lead_in_pt[0]:.3f} Y{lead_in_pt[1]:.3f} (Lead-in position)")

        # Roughing passes
        for pass_idx, z_depth in enumerate(passes):
            lines.append("")
            lines.append(f"(Pass {pass_idx + 1} - Z={z_depth:.3f})")

            # Plunge to depth
            lines.append(f"G0 Z{self.config.retract_z_mm:.3f} (Quick retract)")
            lines.append(f"G1 Z{z_depth:.3f} F{self.config.plunge_rate:.0f} (Plunge)")

            # Lead-in arc
            lines.extend(self._generate_lead_in_arc(lead_in_pt, start_pt, z_depth))

            # Cut perimeter with tabs
            lines.extend(self._generate_perimeter_cut(
                roughing_path,
                z_depth,
                tabs,
                is_final_pass=(pass_idx == len(passes) - 1),
            ))

            # Lead-out arc back to lead-in point
            lines.extend(self._generate_lead_out_arc(roughing_path[-1], lead_in_pt, z_depth))

            # Retract
            lines.append(f"G0 Z{self.config.safe_z_mm:.3f} (Retract)")

        # Finishing pass (if enabled)
        if finishing_path:
            lines.append("")
            lines.append("(Finishing pass)")

            finish_start = finishing_path[0]
            finish_lead_in = self._calculate_lead_in_point(finishing_path)

            lines.append(f"G0 X{finish_lead_in[0]:.3f} Y{finish_lead_in[1]:.3f}")
            lines.append(f"G0 Z{self.config.retract_z_mm:.3f}")

            # Full depth for finishing
            z_finish = -self.config.cut_depth_mm + self.config.tab_height_mm
            lines.append(f"G1 Z{z_finish:.3f} F{self.config.plunge_rate:.0f}")

            lines.extend(self._generate_lead_in_arc(finish_lead_in, finish_start, z_finish))
            lines.extend(self._generate_perimeter_cut(
                finishing_path,
                z_finish,
                tabs,
                is_final_pass=True,
            ))
            lines.extend(self._generate_lead_out_arc(finishing_path[-1], finish_lead_in, z_finish))

            lines.append(f"G0 Z{self.config.safe_z_mm:.3f}")

        # Footer
        lines.append("")
        lines.append("M5 (Spindle off)")
        lines.append("G0 Z{:.3f} (Final retract)".format(self.config.safe_z_mm))
        lines.append("M30 (Program end)")

        return lines

    def _calculate_lead_in_point(self, path: List[Pt]) -> Pt:
        """Calculate lead-in point offset from start of path."""
        if len(path) < 2:
            return path[0]

        # Get direction from first segment
        dx = path[1][0] - path[0][0]
        dy = path[1][1] - path[0][1]
        length = math.hypot(dx, dy) or 1.0

        # Perpendicular offset (outward for outside profile)
        nx = -dy / length
        ny = dx / length

        # Lead-in point is offset perpendicular to path start
        offset = self.config.lead_in_radius_mm
        return (
            path[0][0] + nx * offset,
            path[0][1] + ny * offset,
        )

    def _generate_lead_in_arc(
        self,
        start: Pt,
        end: Pt,
        z: float,
    ) -> List[str]:
        """Generate lead-in arc from start to end point."""
        lines = []

        # Calculate arc center and radius
        # Use G2 (CW) for climb milling lead-in
        cx = (start[0] + end[0]) / 2.0
        cy = (start[1] + end[1]) / 2.0

        # I, J are offsets from start to center
        i = cx - start[0]
        j = cy - start[1]

        if self.config.direction == MillingDirection.CLIMB:
            arc_code = "G2"  # Clockwise
        else:
            arc_code = "G3"  # Counter-clockwise

        lines.append(
            f"{arc_code} X{end[0]:.3f} Y{end[1]:.3f} I{i:.3f} J{j:.3f} "
            f"F{self.config.feed_rate_xy:.0f} (Lead-in arc)"
        )

        return lines

    def _generate_lead_out_arc(
        self,
        start: Pt,
        end: Pt,
        z: float,
    ) -> List[str]:
        """Generate lead-out arc from end of path back to lead-in point."""
        lines = []

        cx = (start[0] + end[0]) / 2.0
        cy = (start[1] + end[1]) / 2.0

        i = cx - start[0]
        j = cy - start[1]

        if self.config.direction == MillingDirection.CLIMB:
            arc_code = "G2"
        else:
            arc_code = "G3"

        lines.append(
            f"{arc_code} X{end[0]:.3f} Y{end[1]:.3f} I{i:.3f} J{j:.3f} "
            f"F{self.config.feed_rate_xy:.0f} (Lead-out arc)"
        )

        return lines

    def _generate_perimeter_cut(
        self,
        path: List[Pt],
        z_depth: float,
        tabs: List,
        is_final_pass: bool,
    ) -> List[str]:
        """Generate G-code for cutting around the perimeter."""
        lines = []

        # Create set of tab indices for quick lookup
        tab_ranges = set()
        for tab in tabs:
            for idx in range(tab.start_index, tab.end_index + 1):
                tab_ranges.add(idx % len(path))

        # Cut around perimeter
        for i, pt in enumerate(path):
            # Check if in tab region
            in_tab = i in tab_ranges and is_final_pass

            if in_tab:
                # Lift for tab
                tab_z = z_depth + self.config.tab_height_mm
                lines.append(f"G1 Z{tab_z:.3f} F{self.config.feed_rate_z:.0f} (Tab lift)")
                lines.append(
                    f"G1 X{pt[0]:.3f} Y{pt[1]:.3f} F{self.config.feed_rate_xy:.0f}"
                )
            else:
                # Normal cut
                lines.append(
                    f"G1 X{pt[0]:.3f} Y{pt[1]:.3f} F{self.config.feed_rate_xy:.0f}"
                )

                # Return to depth after tab
                if i > 0 and (i - 1) in tab_ranges and is_final_pass:
                    lines.append(f"G1 Z{z_depth:.3f} F{self.config.feed_rate_z:.0f} (Tab exit)")

        # Close the profile (return to start)
        if path:
            lines.append(
                f"G1 X{path[0][0]:.3f} Y{path[0][1]:.3f} F{self.config.feed_rate_xy:.0f} (Close profile)"
            )

        return lines

    def _perimeter_length(self, path: List[Pt]) -> float:
        """Calculate total perimeter length."""
        if len(path) < 2:
            return 0.0

        length = 0.0
        for i in range(len(path)):
            p1 = path[i]
            p2 = path[(i + 1) % len(path)]
            length += math.hypot(p2[0] - p1[0], p2[1] - p1[1])

        return length

    def _extract_toolpath_points(self, gcode_lines: List[str]) -> List[Dict[str, Any]]:
        """Extract toolpath points from G-code for visualization."""
        points = []
        current = {"x": 0.0, "y": 0.0, "z": 0.0}

        for line in gcode_lines:
            if line.startswith("G0") or line.startswith("G1"):
                point = dict(current)
                point["rapid"] = line.startswith("G0")

                # Parse coordinates
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
            length += math.hypot(dx, dy, dz) if hasattr(math, 'hypot') else (dx**2 + dy**2 + dz**2)**0.5

        return length

    def _estimate_time(self, total_length: float) -> float:
        """Estimate machining time in seconds."""
        if total_length <= 0:
            return 0.0

        # Average feed rate (weighted toward cut rate)
        avg_feed = self.config.feed_rate_xy * 0.8  # mm/min

        # Time = length / feed (convert to seconds)
        time_seconds = (total_length / avg_feed) * 60.0

        # Add overhead for retracts, accelerations
        time_seconds *= 1.2

        return time_seconds

    def _empty_result(self) -> ProfileResult:
        """Return empty result for error cases."""
        return ProfileResult(
            gcode="",
            toolpath_points=[],
            total_length_mm=0.0,
            estimated_time_seconds=0.0,
            pass_count=0,
            warnings=self._warnings,
        )
