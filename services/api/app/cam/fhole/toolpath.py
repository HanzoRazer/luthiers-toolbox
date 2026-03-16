# app/cam/fhole/toolpath.py

"""
F-Hole Toolpath Generator (BEN-GAP-09)

Generates G-code toolpaths for routing F-holes through carved archtop tops.

Features:
- Inside-contour toolpath (tool offset inward)
- Multiple depth passes for through-cut
- Helical or ramp plunge entry
- Lead-in/out for smooth entry/exit
- No holding tabs (cut-out is scrap)
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Tuple, Optional, Dict, Any

from .config import FHoleRoutingConfig, PlungeStrategy
from .geometry import FHoleContour, generate_fhole_pair

Pt = Tuple[float, float]


@dataclass
class FHoleToolpathResult:
    """Result of F-hole toolpath generation."""

    gcode_lines: List[str] = field(default_factory=list)
    config: Optional[FHoleRoutingConfig] = None

    # Contours used
    treble_contour: Optional[FHoleContour] = None
    bass_contour: Optional[FHoleContour] = None

    # Statistics
    total_cut_length_mm: float = 0.0
    total_passes: int = 0
    estimated_time_seconds: float = 0.0
    generated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def get_gcode(self) -> str:
        """Return complete G-code as string."""
        return "\n".join(self.gcode_lines)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "total_cut_length_mm": round(self.total_cut_length_mm, 1),
            "total_passes": self.total_passes,
            "estimated_time_seconds": round(self.estimated_time_seconds, 1),
            "estimated_time_minutes": round(self.estimated_time_seconds / 60, 1),
            "gcode_line_count": len(self.gcode_lines),
            "treble_contour": self.treble_contour.to_dict() if self.treble_contour else None,
            "bass_contour": self.bass_contour.to_dict() if self.bass_contour else None,
        }


class FHoleToolpathGenerator:
    """
    Generates G-code toolpaths for F-hole routing.

    The generator creates inside-contour toolpaths where the tool
    is offset inward by tool_radius to cut exactly on the line.
    """

    def __init__(self, config: FHoleRoutingConfig):
        self.config = config
        self.tool_radius = config.tool.diameter_mm / 2

    def generate(self) -> FHoleToolpathResult:
        """
        Generate complete F-hole routing program.

        Creates toolpaths for both F-holes (treble and bass side).
        """
        result = FHoleToolpathResult(config=self.config)
        lines = result.gcode_lines

        # Generate F-hole contours
        treble, bass = generate_fhole_pair(
            self.config.geometry,
            self.config.position,
        )
        result.treble_contour = treble
        result.bass_contour = bass

        # Program header
        lines.extend(self._program_header())

        # Tool change
        lines.extend(self._tool_change())

        # Route treble-side F-hole
        lines.append("")
        lines.append("( ============================================ )")
        lines.append("( TREBLE-SIDE F-HOLE )")
        lines.append("( ============================================ )")
        treble_stats = self._route_fhole(treble, lines, "treble")
        result.total_cut_length_mm += treble_stats["cut_length"]
        result.total_passes += treble_stats["passes"]
        result.estimated_time_seconds += treble_stats["time"]

        # Route bass-side F-hole
        lines.append("")
        lines.append("( ============================================ )")
        lines.append("( BASS-SIDE F-HOLE )")
        lines.append("( ============================================ )")
        bass_stats = self._route_fhole(bass, lines, "bass")
        result.total_cut_length_mm += bass_stats["cut_length"]
        result.total_passes += bass_stats["passes"]
        result.estimated_time_seconds += bass_stats["time"]

        # Program footer
        lines.extend(self._program_footer())

        return result

    def generate_single(
        self,
        contour: FHoleContour,
        side: str = "treble",
    ) -> FHoleToolpathResult:
        """Generate toolpath for a single F-hole."""
        result = FHoleToolpathResult(config=self.config)
        lines = result.gcode_lines

        if side == "treble":
            result.treble_contour = contour
        else:
            result.bass_contour = contour

        lines.extend(self._program_header())
        lines.extend(self._tool_change())

        stats = self._route_fhole(contour, lines, side)
        result.total_cut_length_mm = stats["cut_length"]
        result.total_passes = stats["passes"]
        result.estimated_time_seconds = stats["time"]

        lines.extend(self._program_footer())

        return result

    def _program_header(self) -> List[str]:
        """Generate program header."""
        cfg = self.config
        return [
            "( ============================================ )",
            "( F-HOLE ROUTING PROGRAM )",
            "( ============================================ )",
            f"( Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC )",
            f"( F-hole length: {cfg.geometry.length_mm:.1f}mm )",
            f"( F-hole width: {cfg.geometry.width_mm:.1f}mm )",
            f"( Top thickness: {cfg.top_thickness_mm:.1f}mm )",
            f"( Cut depth: {cfg.cut_depth_mm:.1f}mm )",
            f"( Tool: {cfg.tool.name} ({cfg.tool.diameter_mm:.3f}mm) )",
            "( ============================================ )",
            "",
            "G90 G94 G17",  # Absolute, feed/min, XY plane
            "G21" if cfg.output_units == "mm" else "G20",
            "G40 G49 G80",  # Cancel cutter comp, tool length, canned cycles
            "",
        ]

    def _program_footer(self) -> List[str]:
        """Generate program footer."""
        return [
            "",
            "( ============================================ )",
            "( END OF F-HOLE ROUTING PROGRAM )",
            "( ============================================ )",
            "M5",  # Spindle off
            f"G0 Z{self.config.safe_z_mm:.3f}",
            "G0 X0.000 Y0.000",
            "M30",
            "%",
        ]

    def _tool_change(self) -> List[str]:
        """Generate tool change sequence."""
        tool = self.config.tool
        return [
            f"( Tool {tool.tool_number}: {tool.name} )",
            f"T{tool.tool_number} M6",
            f"S{tool.spindle_rpm} M3",
            f"G0 Z{self.config.safe_z_mm:.3f}",
            "G4 P2.0",  # Dwell for spindle spin-up
            "",
        ]

    def _route_fhole(
        self,
        contour: FHoleContour,
        lines: List[str],
        side: str,
    ) -> Dict[str, float]:
        """
        Route a single F-hole with multiple depth passes.

        Returns statistics dict with cut_length, passes, time.
        """
        cfg = self.config
        offset_contour = self._offset_contour_inward(contour.points)

        # Calculate Z levels
        z_levels = self._calculate_z_levels()
        passes = len(z_levels)

        lines.append(f"( F-hole {side} side: {len(offset_contour)} points )")
        lines.append(f"( Center: X{contour.center[0]:.3f} Y{contour.center[1]:.3f} )")
        lines.append(f"( Passes: {passes} )")

        # Find plunge point (center of F-hole for helical, first point for ramp)
        plunge_x, plunge_y = contour.center

        total_length = 0.0
        total_time = 0.0

        for pass_idx, z in enumerate(z_levels):
            lines.append("")
            lines.append(f"( Pass {pass_idx + 1}/{passes}: Z={z:.3f}mm )")

            # Rapid to plunge position
            lines.append(f"G0 X{plunge_x:.3f} Y{plunge_y:.3f}")
            lines.append(f"G0 Z{cfg.retract_z_mm:.3f}")

            # Plunge to depth
            plunge_lines, plunge_length = self._generate_plunge(
                plunge_x, plunge_y, z
            )
            lines.extend(plunge_lines)
            total_length += plunge_length

            # Cut contour
            cut_lines, cut_length = self._cut_contour(offset_contour, z)
            lines.extend(cut_lines)
            total_length += cut_length

            # Retract
            lines.append(f"G0 Z{cfg.retract_z_mm:.3f}")

        # Estimate time
        feed_rate = cfg.tool.feed_rate_mm_min
        total_time = (total_length / feed_rate) * 60  # seconds

        return {
            "cut_length": total_length,
            "passes": passes,
            "time": total_time,
        }

    def _offset_contour_inward(self, points: List[Pt]) -> List[Pt]:
        """
        Offset contour inward by tool radius.

        For inside cuts, the tool center follows a path that is
        tool_radius inside the target contour.
        """
        if len(points) < 3:
            return points

        offset_points = []
        n = len(points)

        for i in range(n):
            # Get neighboring points
            p_prev = points[(i - 1) % n]
            p_curr = points[i]
            p_next = points[(i + 1) % n]

            # Calculate edge vectors
            v1 = (p_curr[0] - p_prev[0], p_curr[1] - p_prev[1])
            v2 = (p_next[0] - p_curr[0], p_next[1] - p_curr[1])

            # Normalize
            len1 = math.sqrt(v1[0] ** 2 + v1[1] ** 2)
            len2 = math.sqrt(v2[0] ** 2 + v2[1] ** 2)

            if len1 < 0.001 or len2 < 0.001:
                offset_points.append(p_curr)
                continue

            v1 = (v1[0] / len1, v1[1] / len1)
            v2 = (v2[0] / len2, v2[1] / len2)

            # Calculate inward normals (perpendicular, pointing right/inward for CW contour)
            n1 = (v1[1], -v1[0])
            n2 = (v2[1], -v2[0])

            # Average normal at corner
            n_avg = ((n1[0] + n2[0]) / 2, (n1[1] + n2[1]) / 2)
            n_len = math.sqrt(n_avg[0] ** 2 + n_avg[1] ** 2)

            if n_len < 0.001:
                offset_points.append(p_curr)
                continue

            n_avg = (n_avg[0] / n_len, n_avg[1] / n_len)

            # Calculate offset distance (handle sharp corners)
            # For sharp corners, need to extend further
            dot = v1[0] * v2[0] + v1[1] * v2[1]
            angle_factor = 1.0 / max(0.5, math.sqrt((1 + dot) / 2))
            offset_dist = self.tool_radius * angle_factor

            # Offset point inward
            offset_x = p_curr[0] - n_avg[0] * offset_dist
            offset_y = p_curr[1] - n_avg[1] * offset_dist

            offset_points.append((offset_x, offset_y))

        return offset_points

    def _calculate_z_levels(self) -> List[float]:
        """Calculate Z levels for depth passes."""
        cfg = self.config
        z_top = 0.0
        z_bottom = -cfg.cut_depth_mm

        levels = []
        z = -cfg.stepdown_mm

        while z > z_bottom:
            levels.append(z)
            z -= cfg.stepdown_mm

        # Always include final depth
        if not levels or levels[-1] > z_bottom:
            levels.append(z_bottom)

        return levels

    def _generate_plunge(
        self,
        x: float,
        y: float,
        z: float,
    ) -> Tuple[List[str], float]:
        """
        Generate plunge entry to depth.

        Returns (gcode_lines, plunge_length).
        """
        cfg = self.config
        lines = []
        length = 0.0

        if cfg.plunge_strategy == PlungeStrategy.HELICAL:
            # Helical plunge in a small circle
            helix_r = cfg.helical_diameter_mm / 2
            pitch = cfg.helical_pitch_mm
            z_start = cfg.retract_z_mm
            z_end = z

            # Calculate revolutions needed
            z_travel = z_start - z_end
            revolutions = z_travel / pitch

            lines.append(f"( Helical plunge: {revolutions:.1f} revolutions )")

            # Plunge in helical motion
            steps = int(revolutions * 36)  # 36 steps per revolution
            for i in range(steps + 1):
                angle = 2 * math.pi * i / 36
                z_curr = z_start - (z_travel * i / steps)
                x_curr = x + helix_r * math.cos(angle)
                y_curr = y + helix_r * math.sin(angle)

                if i == 0:
                    lines.append(f"G1 X{x_curr:.3f} Y{y_curr:.3f} Z{z_curr:.3f} F{cfg.tool.plunge_rate_mm_min:.0f}")
                else:
                    lines.append(f"G1 X{x_curr:.3f} Y{y_curr:.3f} Z{z_curr:.3f}")

            # Move to center at final depth
            lines.append(f"G1 X{x:.3f} Y{y:.3f}")

            length = 2 * math.pi * helix_r * revolutions + z_travel

        elif cfg.plunge_strategy == PlungeStrategy.RAMP:
            # Ramped plunge along first segment
            lines.append(f"( Ramp plunge )")
            lines.append(f"G1 Z{z:.3f} F{cfg.tool.plunge_rate_mm_min:.0f}")
            length = abs(cfg.retract_z_mm - z)

        else:  # DRILL
            # Simple plunge (assumes pre-drilled hole)
            lines.append(f"( Direct plunge - ensure pre-drilled )")
            lines.append(f"G1 Z{z:.3f} F{cfg.tool.plunge_rate_mm_min:.0f}")
            length = abs(cfg.retract_z_mm - z)

        return lines, length

    def _cut_contour(
        self,
        points: List[Pt],
        z: float,
    ) -> Tuple[List[str], float]:
        """
        Cut the contour at given Z depth.

        Returns (gcode_lines, cut_length).
        """
        if not points:
            return [], 0.0

        cfg = self.config
        lines = []
        length = 0.0

        # Move to first point
        x0, y0 = points[0]
        lines.append(f"G1 X{x0:.3f} Y{y0:.3f} F{cfg.tool.feed_rate_mm_min:.0f}")

        # Cut along contour
        prev_x, prev_y = x0, y0
        for x, y in points[1:]:
            lines.append(f"G1 X{x:.3f} Y{y:.3f}")
            length += math.sqrt((x - prev_x) ** 2 + (y - prev_y) ** 2)
            prev_x, prev_y = x, y

        # Close the contour
        lines.append(f"G1 X{x0:.3f} Y{y0:.3f}")
        length += math.sqrt((x0 - prev_x) ** 2 + (y0 - prev_y) ** 2)

        return lines, length
