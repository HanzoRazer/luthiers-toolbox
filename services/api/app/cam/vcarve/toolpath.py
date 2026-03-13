"""
Production V-Carve Toolpath Generator

Generates production-quality G-code for V-carving operations with:
- Proper chipload-based feed rates
- Multi-pass stepdown for deep cuts
- V-bit geometry calculations
- Corner slowdown for quality
- Cutter compensation awareness

Resolves: VINE-03 (V-carve G-code is demo quality)
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple, Iterable

from app.core.safety import safety_critical

from .geometry import (
    vbit_depth_for_width,
    vbit_width_at_depth,
    calculate_stepdown,
)
from .chipload import (
    calculate_feed_rate,
    adjust_feed_for_depth,
    validate_chipload,
    ChiploadParams,
)

# Type alias for points
Pt = Tuple[float, float]


@dataclass
class MLPath:
    """Multi-line path (compatible with existing MLPath)."""
    points: List[Pt]
    is_closed: bool = False


@dataclass
class VCarveConfig:
    """Configuration for production V-carve toolpath."""

    # V-bit parameters
    bit_angle_deg: float = 60.0
    tip_diameter_mm: float = 0.0  # 0 for sharp tip

    # Target dimensions
    target_line_width_mm: float = 2.0  # Desired width at surface
    target_depth_mm: Optional[float] = None  # Override auto-calculated depth

    # Material and feed calculation
    material: str = "hardwood"
    spindle_rpm: int = 18000
    flute_count: int = 2
    chipload_factor: float = 0.8  # Conservative = 0.5, aggressive = 1.0

    # Multi-pass
    max_stepdown_mm: float = 2.0
    min_passes: int = 1

    # Heights
    safe_z_mm: float = 5.0
    retract_z_mm: float = 2.0

    # Feed rates (calculated if None)
    feed_rate_mm_min: Optional[float] = None
    plunge_rate_mm_min: float = 300.0

    # Corner handling
    corner_slowdown: bool = True
    corner_angle_threshold_deg: float = 90.0  # Slow down for corners sharper than this
    corner_feed_factor: float = 0.6  # Reduce feed to 60% at sharp corners

    # Optimization
    optimize_path_order: bool = True  # Reorder paths to minimize rapids


@dataclass
class VCarveResult:
    """Result of V-carve toolpath generation."""

    gcode: str
    path_count: int
    total_length_mm: float
    cut_depth_mm: float
    line_width_mm: float
    pass_count: int
    feed_rate_mm_min: float
    estimated_time_seconds: float
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gcode": self.gcode,
            "path_count": self.path_count,
            "total_length_mm": self.total_length_mm,
            "cut_depth_mm": self.cut_depth_mm,
            "line_width_mm": self.line_width_mm,
            "pass_count": self.pass_count,
            "feed_rate_mm_min": self.feed_rate_mm_min,
            "estimated_time_seconds": self.estimated_time_seconds,
            "warnings": self.warnings,
        }


class VCarveToolpath:
    """
    Production V-carve toolpath generator.

    Generates proper CAM-quality G-code with chipload calculation,
    multi-pass stepdown, and corner handling.
    """

    def __init__(
        self,
        paths: Iterable[MLPath],
        config: Optional[VCarveConfig] = None,
    ):
        """
        Initialize V-carve toolpath generator.

        Args:
            paths: Iterable of MLPath objects (geometry to carve)
            config: V-carve configuration
        """
        self.paths = list(paths)
        self.config = config or VCarveConfig()
        self._warnings: List[str] = []

    @safety_critical
    def generate(self) -> VCarveResult:
        """
        Generate V-carve toolpath.

        Returns:
            VCarveResult with G-code and metadata
        """
        self._warnings = []

        if not self.paths:
            self._warnings.append("No paths provided")
            return self._empty_result()

        # Calculate cut depth from target width (or use override)
        if self.config.target_depth_mm is not None:
            cut_depth = self.config.target_depth_mm
            line_width = vbit_width_at_depth(cut_depth, self.config.bit_angle_deg)
        else:
            cut_depth = vbit_depth_for_width(
                self.config.target_line_width_mm,
                self.config.bit_angle_deg,
            )
            line_width = self.config.target_line_width_mm

        # Calculate feed rate
        if self.config.feed_rate_mm_min is not None:
            feed_rate = self.config.feed_rate_mm_min
        else:
            feed_rate = calculate_feed_rate(ChiploadParams(
                material=self.config.material,
                spindle_rpm=self.config.spindle_rpm,
                flute_count=self.config.flute_count,
                chipload_factor=self.config.chipload_factor,
            ))

        # Validate chipload
        from .chipload import calculate_chipload
        chipload = calculate_chipload(
            feed_rate,
            self.config.spindle_rpm,
            self.config.flute_count,
        )
        valid, msg = validate_chipload(chipload, self.config.material)
        if not valid:
            self._warnings.append(msg)

        # Calculate stepdown passes
        pass_count, stepdown = calculate_stepdown(
            cut_depth,
            self.config.bit_angle_deg,
            self.config.max_stepdown_mm,
            self.config.min_passes,
        )

        # Optimize path order if requested
        paths = self.paths
        if self.config.optimize_path_order and len(paths) > 1:
            paths = self._optimize_path_order(paths)

        # Generate G-code
        gcode_lines = self._generate_gcode(
            paths=paths,
            cut_depth=cut_depth,
            pass_count=pass_count,
            stepdown=stepdown,
            feed_rate=feed_rate,
        )

        # Calculate metrics
        total_length = self._calculate_total_length(paths)
        estimated_time = self._estimate_time(
            total_length, cut_depth, pass_count, feed_rate
        )

        return VCarveResult(
            gcode="\n".join(gcode_lines),
            path_count=len(paths),
            total_length_mm=round(total_length, 2),
            cut_depth_mm=round(cut_depth, 3),
            line_width_mm=round(line_width, 3),
            pass_count=pass_count,
            feed_rate_mm_min=round(feed_rate, 1),
            estimated_time_seconds=round(estimated_time, 1),
            warnings=self._warnings,
        )

    def generate_gcode(self) -> str:
        """Generate G-code string (convenience method)."""
        return self.generate().gcode

    def _generate_gcode(
        self,
        paths: List[MLPath],
        cut_depth: float,
        pass_count: int,
        stepdown: float,
        feed_rate: float,
    ) -> List[str]:
        """Generate complete G-code program."""
        lines = []

        # Header
        lines.append("(Production V-Carve Toolpath)")
        lines.append(f"(Bit: {self.config.bit_angle_deg}deg V-bit)")
        lines.append(f"(Depth: {cut_depth:.3f}mm in {pass_count} pass(es))")
        lines.append(f"(Material: {self.config.material})")
        lines.append(f"(Feed: {feed_rate:.0f}mm/min, Spindle: {self.config.spindle_rpm}RPM)")
        lines.append("")

        # Setup
        lines.append("G21 (Units: mm)")
        lines.append("G90 (Absolute positioning)")
        lines.append("G17 (XY plane)")
        lines.append(f"G0 Z{self.config.safe_z_mm:.3f} (Safe height)")
        lines.append(f"M3 S{self.config.spindle_rpm} (Spindle on)")
        lines.append("")

        # Generate passes
        for pass_num in range(pass_count):
            current_depth = (pass_num + 1) * stepdown
            if current_depth > cut_depth:
                current_depth = cut_depth

            z_depth = -current_depth

            # Adjust feed for depth
            pass_feed = adjust_feed_for_depth(
                feed_rate,
                current_depth,
                self.config.bit_angle_deg,
            )

            lines.append(f"(Pass {pass_num + 1}/{pass_count} - Z={z_depth:.3f})")

            for path_idx, path in enumerate(paths):
                if not path.points:
                    continue

                lines.append(f"(Path {path_idx + 1})")

                # Rapid to start
                x0, y0 = path.points[0]
                lines.append(f"G0 X{x0:.3f} Y{y0:.3f}")
                lines.append(f"G0 Z{self.config.retract_z_mm:.3f}")

                # Plunge
                lines.append(f"G1 Z{z_depth:.3f} F{self.config.plunge_rate_mm_min:.0f}")

                # Cut path with corner slowdown
                prev_pt = path.points[0]
                for i, pt in enumerate(path.points[1:], start=1):
                    # Calculate corner angle if needed
                    if self.config.corner_slowdown and i < len(path.points) - 1:
                        corner_feed = self._get_corner_feed(
                            prev_pt, pt, path.points[i + 1], pass_feed
                        )
                    else:
                        corner_feed = pass_feed

                    lines.append(
                        f"G1 X{pt[0]:.3f} Y{pt[1]:.3f} F{corner_feed:.0f}"
                    )
                    prev_pt = pt

                # Close path if needed
                if path.is_closed and path.points[0] != path.points[-1]:
                    x0, y0 = path.points[0]
                    lines.append(f"G1 X{x0:.3f} Y{y0:.3f} F{pass_feed:.0f}")

                # Retract
                lines.append(f"G0 Z{self.config.safe_z_mm:.3f}")

            lines.append("")

        # Footer
        lines.append("M5 (Spindle off)")
        lines.append(f"G0 Z{self.config.safe_z_mm:.3f} (Final retract)")
        lines.append("M30 (Program end)")

        return lines

    def _get_corner_feed(
        self,
        p1: Pt,
        p2: Pt,
        p3: Pt,
        base_feed: float,
    ) -> float:
        """Calculate feed rate for a corner."""
        # Vectors
        v1 = (p2[0] - p1[0], p2[1] - p1[1])
        v2 = (p3[0] - p2[0], p3[1] - p2[1])

        # Magnitudes
        mag1 = math.hypot(v1[0], v1[1])
        mag2 = math.hypot(v2[0], v2[1])

        if mag1 < 1e-9 or mag2 < 1e-9:
            return base_feed

        # Angle between vectors
        dot = v1[0] * v2[0] + v1[1] * v2[1]
        cos_angle = max(-1.0, min(1.0, dot / (mag1 * mag2)))
        angle_deg = math.degrees(math.acos(cos_angle))

        # If corner is sharper than threshold, reduce feed
        if angle_deg < self.config.corner_angle_threshold_deg:
            # Linear interpolation based on angle
            factor = angle_deg / self.config.corner_angle_threshold_deg
            return base_feed * (self.config.corner_feed_factor +
                               (1.0 - self.config.corner_feed_factor) * factor)

        return base_feed

    def _optimize_path_order(self, paths: List[MLPath]) -> List[MLPath]:
        """Reorder paths to minimize rapid travel distance."""
        if len(paths) <= 1:
            return paths

        # Simple nearest-neighbor optimization
        remaining = list(paths)
        ordered = [remaining.pop(0)]
        current_end = ordered[0].points[-1] if ordered[0].points else (0, 0)

        while remaining:
            # Find nearest path start
            nearest_idx = 0
            nearest_dist = float('inf')

            for i, path in enumerate(remaining):
                if not path.points:
                    continue
                start = path.points[0]
                dist = math.hypot(start[0] - current_end[0], start[1] - current_end[1])
                if dist < nearest_dist:
                    nearest_dist = dist
                    nearest_idx = i

            # Move nearest to ordered list
            ordered.append(remaining.pop(nearest_idx))
            if ordered[-1].points:
                current_end = ordered[-1].points[-1]

        return ordered

    def _calculate_total_length(self, paths: List[MLPath]) -> float:
        """Calculate total path length."""
        total = 0.0
        for path in paths:
            if len(path.points) < 2:
                continue
            for i in range(1, len(path.points)):
                dx = path.points[i][0] - path.points[i-1][0]
                dy = path.points[i][1] - path.points[i-1][1]
                total += math.hypot(dx, dy)
        return total

    def _estimate_time(
        self,
        total_length: float,
        cut_depth: float,
        pass_count: int,
        feed_rate: float,
    ) -> float:
        """Estimate machining time in seconds."""
        if total_length <= 0 or feed_rate <= 0:
            return 0.0

        # Cut time (all passes)
        cut_time = (total_length * pass_count / feed_rate) * 60.0

        # Plunge time
        plunge_time = (cut_depth * pass_count * len(self.paths) /
                      self.config.plunge_rate_mm_min) * 60.0

        # Rapid time (rough estimate)
        rapid_time = (total_length * 0.5 / 3000.0) * 60.0  # Assume rapids at 3000mm/min

        # Add overhead
        return (cut_time + plunge_time + rapid_time) * 1.15

    def _empty_result(self) -> VCarveResult:
        """Return empty result for error cases."""
        return VCarveResult(
            gcode="",
            path_count=0,
            total_length_mm=0.0,
            cut_depth_mm=0.0,
            line_width_mm=0.0,
            pass_count=0,
            feed_rate_mm_min=0.0,
            estimated_time_seconds=0.0,
            warnings=self._warnings,
        )
