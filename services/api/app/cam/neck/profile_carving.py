# app/cam/neck/profile_carving.py

"""
Neck Profile Carving Generator (LP-GAP-03)

Generates G-code for neck profile carving with full-scale station awareness.
This resolves the "12-inch limit" problem by generating profile stations
from nut through heel to body joint.

Key features:
- Dynamic station generation based on scale length
- Profile interpolation between stations
- Roughing and finishing passes
- Compound profile support (V→C transition)

Coordinate convention (VINE-05):
- Y=0 at nut centerline
- +Y toward bridge
- X=0 centerline
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from .config import (
    NeckPipelineConfig,
    ProfileCarvingConfig,
    NeckProfileType,
    NeckToolSpec,
)


@dataclass
class ProfileStation:
    """Profile data at a specific Y position along the neck."""
    y_mm: float  # Y position from nut
    width_mm: float  # Neck width at this station
    depth_mm: float  # Neck depth at this station
    profile_points: List[Tuple[float, float]] = field(default_factory=list)  # (x, z) pairs

    def to_dict(self) -> dict:
        return {
            "y_mm": round(self.y_mm, 2),
            "width_mm": round(self.width_mm, 2),
            "depth_mm": round(self.depth_mm, 2),
            "point_count": len(self.profile_points),
        }


@dataclass
class ProfileCarvingResult:
    """Result of profile carving generation."""
    gcode_lines: List[str] = field(default_factory=list)
    operation_name: str = "OP40: Neck Profile"
    tool_number: int = 1
    cut_time_seconds: float = 0.0
    stations: List[ProfileStation] = field(default_factory=list)
    roughing_passes: int = 0
    finishing_passes: int = 0

    def to_dict(self) -> dict:
        return {
            "operation_name": self.operation_name,
            "tool_number": self.tool_number,
            "cut_time_seconds": round(self.cut_time_seconds, 1),
            "station_count": len(self.stations),
            "roughing_passes": self.roughing_passes,
            "finishing_passes": self.finishing_passes,
            "gcode_line_count": len(self.gcode_lines),
            "stations": [s.to_dict() for s in self.stations],
        }


class ProfileCarvingGenerator:
    """
    Generate neck profile carving G-code.

    The neck profile is carved using a ball-end mill with multiple stations
    along the neck length. Each station defines a cross-sectional profile
    (C, D, V, U, or compound shape).

    Station-aware carving:
    - Generates stations from Y=0 (nut) to body joint + extension
    - Interpolates width and depth between reference points
    - Supports compound profiles that transition shape along length
    """

    def __init__(self, config: NeckPipelineConfig):
        self.config = config
        self.pc_config = config.profile_carving
        self.rough_tool = config.tools.get(1)  # Ball end for roughing
        self.finish_tool = config.tools.get(3)  # Larger ball end for finishing

        self.safe_z_mm = 25.0
        self.retract_z_mm = 5.0

        # Reference positions for interpolation
        self._fret_12_y = self._fret_position(12)
        self._body_joint_y = config.body_joint_y_mm

    def _fret_position(self, fret_number: int) -> float:
        """Calculate fret position in mm from nut."""
        if fret_number <= 0:
            return 0.0
        return self.config.scale_length_mm * (1 - (1 / (2 ** (fret_number / 12))))

    def _interpolate_width(self, y_mm: float) -> float:
        """Interpolate neck width at Y position (linear taper)."""
        if y_mm <= 0:
            return self.config.nut_width_mm
        if y_mm >= self._body_joint_y:
            return self.config.heel_width_mm

        t = y_mm / self._body_joint_y
        return self.config.nut_width_mm + t * (self.config.heel_width_mm - self.config.nut_width_mm)

    def _interpolate_depth(self, y_mm: float) -> float:
        """Interpolate neck depth at Y position."""
        if y_mm <= 0:
            return self.pc_config.depth_at_nut_mm
        if y_mm >= self._body_joint_y:
            return self.pc_config.depth_at_heel_mm

        # Use 12th fret as midpoint reference
        if y_mm <= self._fret_12_y:
            t = y_mm / self._fret_12_y
            return self.pc_config.depth_at_nut_mm + t * (
                self.pc_config.depth_at_12th_mm - self.pc_config.depth_at_nut_mm
            )
        else:
            t = (y_mm - self._fret_12_y) / (self._body_joint_y - self._fret_12_y)
            return self.pc_config.depth_at_12th_mm + t * (
                self.pc_config.depth_at_heel_mm - self.pc_config.depth_at_12th_mm
            )

    def _generate_profile_points(
        self,
        y_mm: float,
        width_mm: float,
        depth_mm: float,
        resolution: int = 20,
    ) -> List[Tuple[float, float]]:
        """
        Generate (x, z) profile points for a cross-section.

        Args:
            y_mm: Station Y position (for compound profile blending)
            width_mm: Neck width at this station
            depth_mm: Neck depth at this station
            resolution: Number of points across half-width

        Returns:
            List of (x, z) tuples from -half_width to +half_width
        """
        profile_type = self.pc_config.profile_type
        half_width = width_mm / 2

        points = []

        # For compound profiles, blend from V to C based on position
        blend_factor = 0.0
        if profile_type == NeckProfileType.COMPOUND:
            if y_mm <= self._fret_12_y:
                blend_factor = y_mm / self._fret_12_y  # 0 at nut, 1 at 12th
            else:
                blend_factor = 1.0  # Full C after 12th fret
            profile_type = NeckProfileType.C_SHAPE  # Base on C, blend with V

        for i in range(resolution * 2 + 1):
            # X position: -half_width to +half_width
            t = i / (resolution * 2)  # 0 to 1
            x = -half_width + t * width_mm

            # Normalized position from centerline (0 to 1 to 0)
            x_norm = abs(x) / half_width

            # Calculate Z based on profile type
            if profile_type == NeckProfileType.C_SHAPE:
                # C shape: circular arc
                z = -depth_mm * math.sqrt(1 - x_norm ** 2)

            elif profile_type == NeckProfileType.D_SHAPE:
                # D shape: flattened ellipse
                z = -depth_mm * math.sqrt(1 - x_norm ** 1.5)

            elif profile_type == NeckProfileType.V_SHAPE:
                # V shape: linear taper
                z = -depth_mm * (1 - x_norm)

            elif profile_type == NeckProfileType.U_SHAPE:
                # U shape: steep sides, flat back
                if x_norm < 0.7:
                    z = -depth_mm
                else:
                    z = -depth_mm * (1 - (x_norm - 0.7) / 0.3)

            elif profile_type == NeckProfileType.ASYMMETRIC:
                # Asymmetric: bass side thicker
                if x < 0:  # Bass side
                    z = -depth_mm * math.sqrt(1 - (x_norm * 0.9) ** 2)
                else:  # Treble side
                    z = -depth_mm * math.sqrt(1 - (x_norm * 1.1) ** 2)

            else:
                # Default to C shape
                z = -depth_mm * math.sqrt(1 - x_norm ** 2)

            # Apply compound blending (V to C)
            if self.pc_config.profile_type == NeckProfileType.COMPOUND:
                z_v = -depth_mm * (1 - x_norm)  # V shape
                z_c = -depth_mm * math.sqrt(max(0, 1 - x_norm ** 2))  # C shape
                z = z_v * (1 - blend_factor) + z_c * blend_factor

            points.append((x, z))

        return points

    def generate_stations(self) -> List[ProfileStation]:
        """Generate all profile stations along neck length."""
        stations = []
        y_positions = self.config.get_station_y_positions()

        for y in y_positions:
            width = self._interpolate_width(y)
            depth = self._interpolate_depth(y)
            points = self._generate_profile_points(y, width, depth)

            station = ProfileStation(
                y_mm=y,
                width_mm=width,
                depth_mm=depth,
                profile_points=points,
            )
            stations.append(station)

        return stations

    def generate_roughing(self, tool: Optional[NeckToolSpec] = None) -> ProfileCarvingResult:
        """Generate roughing pass G-code."""
        if tool:
            self.rough_tool = tool

        if not self.rough_tool:
            raise ValueError("No tool specified for profile roughing")

        result = ProfileCarvingResult(
            operation_name="OP40: Neck Profile Rough",
            tool_number=self.rough_tool.tool_number,
        )
        lines = result.gcode_lines

        # Generate stations
        stations = self.generate_stations()
        result.stations = stations

        # Header
        lines.append("")
        lines.append("( ============================================ )")
        lines.append(f"( {result.operation_name} )")
        lines.append("( ============================================ )")
        lines.append(f"( Profile: {self.pc_config.profile_type.value} )")
        lines.append(f"( Stations: {len(stations)} (full scale length) )")
        lines.append(f"( Finish allowance: {self.pc_config.finish_allowance_mm:.3f}mm )")
        lines.append(f"( Tool: T{self.rough_tool.tool_number} - {self.rough_tool.name} )")

        # Tool change
        lines.extend(self._tool_change(self.rough_tool))

        stepover = self.rough_tool.stepover_mm
        allowance = self.pc_config.finish_allowance_mm

        lines.append(f"( Stepover: {stepover:.3f}mm )")

        # Generate profile cuts at each station
        for station in stations:
            lines.append("")
            lines.append(f"( Station: Y = {station.y_mm:.2f}mm, Width = {station.width_mm:.2f}mm )")

            # Move to station
            lines.append(f"G0 Z{self.safe_z_mm:.3f}")
            lines.append(f"G0 Y{station.y_mm:.3f}")

            # Cut profile points with finish allowance
            for x, z in station.profile_points:
                z_with_allowance = z + allowance
                lines.append(f"G0 X{x:.3f}")
                lines.append(f"G1 Z{z_with_allowance:.3f} F{self.rough_tool.feed_mm_min:.0f}")

            lines.append(f"G0 Z{self.retract_z_mm:.3f}")
            result.roughing_passes += 1

        lines.append(f"G0 Z{self.safe_z_mm:.3f}")

        # Estimate cut time
        total_points = sum(len(s.profile_points) for s in stations)
        avg_move_mm = 5.0  # Rough estimate
        result.cut_time_seconds = (total_points * avg_move_mm / self.rough_tool.feed_mm_min) * 60

        return result

    def generate_finishing(self, tool: Optional[NeckToolSpec] = None) -> ProfileCarvingResult:
        """Generate finishing pass G-code."""
        if tool:
            self.finish_tool = tool

        if not self.finish_tool:
            raise ValueError("No tool specified for profile finishing")

        result = ProfileCarvingResult(
            operation_name="OP45: Neck Profile Finish",
            tool_number=self.finish_tool.tool_number,
        )
        lines = result.gcode_lines

        # Use same stations but with tighter stepover and no allowance
        stations = self.generate_stations()
        result.stations = stations

        # Header
        lines.append("")
        lines.append("( ============================================ )")
        lines.append(f"( {result.operation_name} )")
        lines.append("( ============================================ )")
        lines.append(f"( Profile: {self.pc_config.profile_type.value} )")
        lines.append(f"( Stations: {len(stations)} )")
        lines.append(f"( Tool: T{self.finish_tool.tool_number} - {self.finish_tool.name} )")

        # Tool change
        lines.extend(self._tool_change(self.finish_tool))

        stepover = self.finish_tool.stepover_mm  # Tighter for finishing

        lines.append(f"( Finish stepover: {stepover:.3f}mm )")

        # Generate finishing cuts - no allowance, tighter stepover
        for station in stations:
            lines.append("")
            lines.append(f"( Station: Y = {station.y_mm:.2f}mm )")

            lines.append(f"G0 Z{self.safe_z_mm:.3f}")
            lines.append(f"G0 Y{station.y_mm:.3f}")

            for x, z in station.profile_points:
                lines.append(f"G0 X{x:.3f}")
                lines.append(f"G1 Z{z:.3f} F{self.finish_tool.feed_mm_min:.0f}")

            lines.append(f"G0 Z{self.retract_z_mm:.3f}")
            result.finishing_passes += 1

        lines.append(f"G0 Z{self.safe_z_mm:.3f}")

        # Estimate cut time
        total_points = sum(len(s.profile_points) for s in stations)
        avg_move_mm = 5.0
        result.cut_time_seconds = (total_points * avg_move_mm / self.finish_tool.feed_mm_min) * 60

        return result

    def _tool_change(self, tool: NeckToolSpec) -> List[str]:
        """Generate tool change sequence."""
        return [
            "",
            f"( Tool Change: T{tool.tool_number} - {tool.name} )",
            "M5",
            f"T{tool.tool_number} M6",
            f"S{tool.rpm} M3",
            "G4 P2",
            f"G0 Z{self.safe_z_mm:.3f}",
        ]
