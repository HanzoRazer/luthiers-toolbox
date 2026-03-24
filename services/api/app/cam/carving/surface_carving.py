# app/cam/carving/surface_carving.py

"""
3D Surface Carving Toolpath Generator (BEN-GAP-08)

Generates roughing and finishing toolpaths for graduated thickness carving.
Supports archtop tops/backs, Les Paul carved tops, and other 3D surfaces.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from .config import (
    CarvingConfig,
    CarvingStrategy,
    CarvingToolSpec,
    RoughingConfig,
    FinishingConfig,
)
from .graduation_map import GraduationMap
from ..post_processor import PostProcessor, PostConfig, ToolSpec, ToolChangeMode

from app.core.safety import safety_critical


@dataclass
class CarvingMove:
    """Single toolpath move."""
    x_mm: float
    y_mm: float
    z_mm: float
    feed_mm_min: Optional[float] = None  # None = rapid
    is_plunge: bool = False

    def to_gcode(self) -> str:
        if self.feed_mm_min is None:
            return f"G0 X{self.x_mm:.3f} Y{self.y_mm:.3f} Z{self.z_mm:.3f}"
        else:
            return f"G1 X{self.x_mm:.3f} Y{self.y_mm:.3f} Z{self.z_mm:.3f} F{self.feed_mm_min:.0f}"


@dataclass
class CarvingPass:
    """A single carving pass (one Z level or one raster line)."""
    moves: List[CarvingMove] = field(default_factory=list)
    z_level_mm: Optional[float] = None
    pass_type: str = "roughing"  # roughing, semi_finish, finish

    def to_gcode_lines(self) -> List[str]:
        return [m.to_gcode() for m in self.moves]


@dataclass
class CarvingResult:
    """Result of carving toolpath generation."""
    gcode_lines: List[str] = field(default_factory=list)
    operation_name: str = "3D Carving"
    tool_number: int = 1
    cut_time_seconds: float = 0.0
    passes: List[CarvingPass] = field(default_factory=list)
    pass_count: int = 0
    total_distance_mm: float = 0.0

    def to_dict(self) -> dict:
        return {
            "operation_name": self.operation_name,
            "tool_number": self.tool_number,
            "cut_time_seconds": round(self.cut_time_seconds, 1),
            "pass_count": self.pass_count,
            "total_distance_mm": round(self.total_distance_mm, 1),
            "gcode_line_count": len(self.gcode_lines),
        }


class SurfaceCarvingGenerator:
    """
    Generate 3D surface carving toolpaths.

    Strategies:
    - PARALLEL_PLANE: Horizontal slices at Z levels (waterline)
    - RASTER_X: Back-and-forth along X axis (for finishing)
    - RASTER_Y: Back-and-forth along Y axis
    - CONTOUR_FOLLOW: Follow thickness contours

    Ball-end tool compensation:
    - Tool center follows path offset by tool radius
    - Scallop height controlled by stepover
    """

    def __init__(
        self,
        config: CarvingConfig,
        graduation_map: GraduationMap,
    ):
        self.config = config
        self.grad_map = graduation_map
        self.safe_z = config.safe_z_mm
        self.retract_z = config.retract_z_mm

    @safety_critical
    def generate_roughing(
        self,
        tool: Optional[CarvingToolSpec] = None,
    ) -> CarvingResult:
        """
        Generate roughing passes using parallel-plane (waterline) strategy.

        Removes bulk material in horizontal slices, leaving finish allowance.
        """
        if tool is None:
            tool = self.config.tools.get(self.config.rough_tool_number)
        if tool is None:
            raise ValueError("No roughing tool specified")

        result = CarvingResult(
            operation_name="OP10: Carving Roughing",
            tool_number=tool.tool_number,
        )
        lines = result.gcode_lines

        # Header
        lines.extend(self._header(result.operation_name, tool, self.config.roughing))

        # Tool change
        lines.extend(self._tool_change(tool))

        # Generate Z levels
        z_levels = self.grad_map.generate_z_levels(
            stock_thickness_mm=self.config.stock_thickness_mm,
            stepdown_mm=self.config.roughing.stepdown_mm,
            finish_allowance_mm=self.config.roughing.finish_allowance_mm,
        )

        lines.append(f"( {len(z_levels)} Z levels )")

        # Generate passes at each Z level
        for z_level in z_levels:
            carving_pass = self._generate_parallel_plane_pass(
                z_level=z_level,
                tool=tool,
                stepover_mm=tool.diameter_mm * (self.config.roughing.stepover_percent / 100),
                finish_allowance_mm=self.config.roughing.finish_allowance_mm,
            )

            if carving_pass.moves:
                result.passes.append(carving_pass)
                lines.append("")
                lines.append(f"( Z Level: {z_level:.3f}mm )")
                lines.extend(carving_pass.to_gcode_lines())

        # Footer
        lines.extend(self._footer())

        result.pass_count = len(result.passes)
        result.cut_time_seconds = self._estimate_time(result.passes, tool.feed_mm_min)

        return result

    @safety_critical
    def generate_finishing(
        self,
        tool: Optional[CarvingToolSpec] = None,
    ) -> CarvingResult:
        """
        Generate finishing passes using raster strategy.

        Creates smooth surface by following graduation map with tight stepover.
        """
        if tool is None:
            tool = self.config.tools.get(self.config.finish_tool_number)
        if tool is None:
            raise ValueError("No finishing tool specified")

        result = CarvingResult(
            operation_name="OP20: Carving Finishing",
            tool_number=tool.tool_number,
        )
        lines = result.gcode_lines

        # Header
        lines.extend(self._header(result.operation_name, tool, self.config.finishing))

        # Tool change
        lines.extend(self._tool_change(tool))

        # Calculate stepover from scallop height or percentage
        if self.config.finishing.scallop_height_mm > 0:
            stepover_mm = self._scallop_to_stepover(
                scallop_height_mm=self.config.finishing.scallop_height_mm,
                tool_radius_mm=tool.diameter_mm / 2,
            )
        else:
            stepover_mm = tool.diameter_mm * (self.config.finishing.stepover_percent / 100)

        lines.append(f"( Finish stepover: {stepover_mm:.3f}mm )")

        # Generate raster passes
        strategy = self.config.finishing.strategy
        if strategy == CarvingStrategy.RASTER_X:
            passes = self._generate_raster_passes(
                tool=tool,
                stepover_mm=stepover_mm,
                axis="x",
            )
        elif strategy == CarvingStrategy.RASTER_Y:
            passes = self._generate_raster_passes(
                tool=tool,
                stepover_mm=stepover_mm,
                axis="y",
            )
        else:
            # Default to raster X
            passes = self._generate_raster_passes(
                tool=tool,
                stepover_mm=stepover_mm,
                axis="x",
            )

        for i, carving_pass in enumerate(passes):
            result.passes.append(carving_pass)
            lines.append("")
            lines.append(f"( Pass {i + 1}/{len(passes)} )")
            lines.extend(carving_pass.to_gcode_lines())

        # Spring passes (extra light finishing)
        for spring in range(self.config.finishing.spring_passes):
            lines.append("")
            lines.append(f"( Spring pass {spring + 1} )")
            # Repeat last pass at same depth
            if passes:
                lines.extend(passes[-1].to_gcode_lines())
                result.pass_count += 1

        # Footer
        lines.extend(self._footer())

        result.pass_count = len(result.passes)
        result.cut_time_seconds = self._estimate_time(result.passes, tool.feed_mm_min)

        return result

    @safety_critical
    def _generate_parallel_plane_pass(
        self,
        z_level: float,
        tool: CarvingToolSpec,
        stepover_mm: float,
        finish_allowance_mm: float = 0.0,
    ) -> CarvingPass:
        """Generate a single parallel-plane (waterline) pass."""
        carving_pass = CarvingPass(z_level_mm=z_level, pass_type="roughing")
        moves = carving_pass.moves

        x_min, x_max = self.grad_map.config.bounds_x_mm
        y_min, y_max = self.grad_map.config.bounds_y_mm

        # Tool radius compensation
        tool_radius = tool.diameter_mm / 2

        # Inset bounds by tool radius
        x_start = x_min + tool_radius
        x_end = x_max - tool_radius
        y_start = y_min + tool_radius
        y_end = y_max - tool_radius

        # Generate zigzag pattern
        y = y_start
        direction = 1  # 1 = forward, -1 = reverse

        first_move = True

        while y <= y_end:
            # Scan along X at this Y
            x_points = []
            x = x_start if direction == 1 else x_end
            x_step = stepover_mm if direction == 1 else -stepover_mm

            while (direction == 1 and x <= x_end) or (direction == -1 and x >= x_start):
                # Get surface Z at this point
                surface_z = self.grad_map.get_surface_z_at(
                    x, y, self.config.stock_thickness_mm
                )

                # Only cut if surface is below current Z level
                # (after accounting for ball radius and finish allowance)
                cutting_z = surface_z + tool_radius + finish_allowance_mm

                if cutting_z < z_level:
                    # Need to cut here
                    x_points.append((x, max(cutting_z, z_level - tool.stepdown_mm)))

                x += x_step

            # Generate moves for this row
            if x_points:
                # Rapid to start
                start_x, start_z = x_points[0]
                if first_move:
                    moves.append(CarvingMove(start_x, y, self.safe_z))
                    first_move = False
                else:
                    moves.append(CarvingMove(start_x, y, self.retract_z))

                # Plunge
                moves.append(CarvingMove(
                    start_x, y, start_z,
                    feed_mm_min=tool.plunge_mm_min,
                    is_plunge=True,
                ))

                # Cut along row
                for x_pt, z_pt in x_points[1:]:
                    moves.append(CarvingMove(x_pt, y, z_pt, feed_mm_min=tool.feed_mm_min))

                # Retract
                moves.append(CarvingMove(x_points[-1][0], y, self.retract_z))

            # Next row
            y += stepover_mm
            direction *= -1  # Reverse direction

        return carving_pass

    @safety_critical
    def _generate_raster_passes(
        self,
        tool: CarvingToolSpec,
        stepover_mm: float,
        axis: str = "x",
    ) -> List[CarvingPass]:
        """Generate raster finishing passes along specified axis."""
        passes = []

        x_min, x_max = self.grad_map.config.bounds_x_mm
        y_min, y_max = self.grad_map.config.bounds_y_mm

        tool_radius = tool.diameter_mm / 2

        # Resolution along cut direction
        cut_resolution_mm = 1.0  # 1mm between points

        if axis == "x":
            # Raster along X, step along Y
            y = y_min + tool_radius
            direction = 1

            while y <= y_max - tool_radius:
                carving_pass = CarvingPass(pass_type="finish")
                moves = carving_pass.moves

                # Generate points along X
                points = []
                x = x_min + tool_radius if direction == 1 else x_max - tool_radius
                x_step = cut_resolution_mm if direction == 1 else -cut_resolution_mm

                while (direction == 1 and x <= x_max - tool_radius) or \
                      (direction == -1 and x >= x_min + tool_radius):

                    if self.grad_map.is_inside_outline(x, y):
                        surface_z = self.grad_map.get_surface_z_at(
                            x, y, self.config.stock_thickness_mm
                        )
                        # Compensate for ball end
                        cutting_z = surface_z + tool_radius
                        points.append((x, y, cutting_z))

                    x += x_step

                # Generate moves
                if points:
                    # Rapid to start
                    moves.append(CarvingMove(points[0][0], points[0][1], self.safe_z))
                    # Plunge
                    moves.append(CarvingMove(
                        points[0][0], points[0][1], points[0][2],
                        feed_mm_min=tool.plunge_mm_min,
                        is_plunge=True,
                    ))
                    # Cut
                    for px, py, pz in points[1:]:
                        moves.append(CarvingMove(px, py, pz, feed_mm_min=tool.feed_mm_min))
                    # Retract
                    moves.append(CarvingMove(points[-1][0], points[-1][1], self.retract_z))

                    passes.append(carving_pass)

                y += stepover_mm
                direction *= -1

        else:  # axis == "y"
            # Raster along Y, step along X
            x = x_min + tool_radius
            direction = 1

            while x <= x_max - tool_radius:
                carving_pass = CarvingPass(pass_type="finish")
                moves = carving_pass.moves

                points = []
                y = y_min + tool_radius if direction == 1 else y_max - tool_radius
                y_step = cut_resolution_mm if direction == 1 else -cut_resolution_mm

                while (direction == 1 and y <= y_max - tool_radius) or \
                      (direction == -1 and y >= y_min + tool_radius):

                    if self.grad_map.is_inside_outline(x, y):
                        surface_z = self.grad_map.get_surface_z_at(
                            x, y, self.config.stock_thickness_mm
                        )
                        cutting_z = surface_z + tool_radius
                        points.append((x, y, cutting_z))

                    y += y_step

                if points:
                    moves.append(CarvingMove(points[0][0], points[0][1], self.safe_z))
                    moves.append(CarvingMove(
                        points[0][0], points[0][1], points[0][2],
                        feed_mm_min=tool.plunge_mm_min,
                        is_plunge=True,
                    ))
                    for px, py, pz in points[1:]:
                        moves.append(CarvingMove(px, py, pz, feed_mm_min=tool.feed_mm_min))
                    moves.append(CarvingMove(points[-1][0], points[-1][1], self.retract_z))

                    passes.append(carving_pass)

                x += stepover_mm
                direction *= -1

        return passes

    def _scallop_to_stepover(
        self,
        scallop_height_mm: float,
        tool_radius_mm: float,
    ) -> float:
        """
        Calculate stepover from desired scallop height.

        For ball-end mill: stepover = 2 * sqrt(2 * R * h - h^2)
        where R = tool radius, h = scallop height
        """
        r = tool_radius_mm
        h = scallop_height_mm

        if h >= r:
            return r  # Max stepover is tool radius

        stepover = 2 * math.sqrt(2 * r * h - h * h)
        return stepover

    def _header(
        self,
        operation_name: str,
        tool: CarvingToolSpec,
        pass_config,
    ) -> List[str]:
        """Generate G-code header."""
        return [
            "",
            "( ============================================ )",
            f"( {operation_name} )",
            "( ============================================ )",
            f"( Surface: {self.grad_map.config.surface_type.value} )",
            f"( Apex: {self.grad_map.config.apex_thickness_mm:.2f}mm )",
            f"( Edge: {self.grad_map.config.edge_thickness_mm:.2f}mm )",
            f"( Stock: {self.config.stock_thickness_mm:.2f}mm )",
            f"( Tool: T{tool.tool_number} - {tool.name} )",
            f"( Strategy: {pass_config.strategy.value if hasattr(pass_config, 'strategy') else 'parallel_plane'} )",
        ]

    def _tool_change(self, tool: CarvingToolSpec) -> List[str]:
        """Generate tool change sequence."""
        return [
            "",
            f"( Tool Change: T{tool.tool_number} - {tool.name} )",
            "M5",
            f"T{tool.tool_number} M6",
            f"S{tool.rpm} M3",
            "G4 P2",
            f"G0 Z{self.safe_z:.3f}",
        ]

    def _footer(self) -> List[str]:
        """Generate G-code footer."""
        return [
            "",
            f"G0 Z{self.safe_z:.3f}",
        ]

    def _estimate_time(
        self,
        passes: List[CarvingPass],
        feed_mm_min: float,
    ) -> float:
        """Estimate cutting time in seconds."""
        total_distance = 0.0

        for carving_pass in passes:
            for i in range(1, len(carving_pass.moves)):
                prev = carving_pass.moves[i - 1]
                curr = carving_pass.moves[i]
                dist = math.sqrt(
                    (curr.x_mm - prev.x_mm) ** 2 +
                    (curr.y_mm - prev.y_mm) ** 2 +
                    (curr.z_mm - prev.z_mm) ** 2
                )
                total_distance += dist

        # Rough estimate: feed moves at feed rate, rapids at 2x
        return (total_distance / feed_mm_min) * 60
