"""
Peck Drilling Cycle (G83)

G83 peck drilling is used for deep holes to clear chips and prevent
drill binding. The drill advances by a peck depth, retracts fully to
clear chips, then advances to the next peck depth.

G83 format:
    G83 X... Y... Z... R... Q... F...
    - X, Y: hole position
    - Z: final depth (negative)
    - R: retract plane (above material)
    - Q: peck depth (positive, depth per peck)
    - F: feed rate

Resolves: FV-GAP-06 (String-through drilling)
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple

from app.core.safety import safety_critical

Pt = Tuple[float, float]


@dataclass
class DrillHole:
    """A single drill hole position."""
    x: float
    y: float
    depth_mm: Optional[float] = None  # Override default depth
    diameter_mm: Optional[float] = None  # For documentation
    label: str = ""  # e.g., "string_1", "bolt_neck_1"


@dataclass
class DrillConfig:
    """Configuration for peck drilling."""

    # Hole parameters
    hole_depth_mm: float = 25.0  # Total depth
    peck_depth_mm: float = 5.0  # Depth per peck (Q value)
    drill_diameter_mm: float = 3.0  # For documentation/validation

    # Heights
    safe_z_mm: float = 10.0  # Safe travel height
    retract_z_mm: float = 2.0  # R plane (rapid retract between pecks)

    # Feed rates
    feed_rate: float = 100.0  # mm/min plunge rate
    rapid_rate: float = 3000.0  # mm/min rapid (for time estimate)

    # Spindle
    spindle_rpm: int = 2000

    # Dwell at bottom (ms) - helps chip clearing
    dwell_ms: int = 0

    # Use canned cycle (G83) vs expanded G-code
    use_canned_cycle: bool = True


@dataclass
class DrillResult:
    """Result of drill operation generation."""
    gcode: str
    hole_count: int
    total_depth_mm: float
    estimated_time_seconds: float
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gcode": self.gcode,
            "hole_count": self.hole_count,
            "total_depth_mm": self.total_depth_mm,
            "estimated_time_seconds": self.estimated_time_seconds,
            "warnings": self.warnings,
        }


class PeckDrill:
    """
    Peck drilling cycle generator.

    Generates G83 peck drilling cycles for deep holes.
    Supports both canned cycle (G83) and expanded G-code output.
    """

    def __init__(
        self,
        holes: List[DrillHole],
        config: Optional[DrillConfig] = None,
    ):
        """
        Initialize peck drill generator.

        Args:
            holes: List of hole positions
            config: Drilling configuration
        """
        self.holes = holes
        self.config = config or DrillConfig()
        self._warnings: List[str] = []

    @safety_critical
    def generate(self) -> DrillResult:
        """
        Generate drilling G-code.

        Returns:
            DrillResult with G-code and metadata
        """
        self._warnings = []

        if not self.holes:
            self._warnings.append("No holes specified")
            return self._empty_result()

        # Validate
        self._validate()

        # Generate G-code
        if self.config.use_canned_cycle:
            gcode_lines = self._generate_canned_cycle()
        else:
            gcode_lines = self._generate_expanded()

        # Calculate metrics
        total_depth = sum(
            (h.depth_mm or self.config.hole_depth_mm) for h in self.holes
        )
        estimated_time = self._estimate_time()

        return DrillResult(
            gcode="\n".join(gcode_lines),
            hole_count=len(self.holes),
            total_depth_mm=round(total_depth, 2),
            estimated_time_seconds=round(estimated_time, 1),
            warnings=self._warnings,
        )

    def generate_gcode(self) -> str:
        """Generate G-code string (convenience method)."""
        return self.generate().gcode

    def _validate(self) -> None:
        """Validate drilling parameters."""
        if self.config.peck_depth_mm <= 0:
            self._warnings.append("Peck depth must be positive")

        if self.config.peck_depth_mm > self.config.hole_depth_mm:
            self._warnings.append(
                f"Peck depth ({self.config.peck_depth_mm}mm) exceeds "
                f"hole depth ({self.config.hole_depth_mm}mm)"
            )

        # Check for reasonable depth/diameter ratio
        ratio = self.config.hole_depth_mm / self.config.drill_diameter_mm
        if ratio > 10:
            self._warnings.append(
                f"Deep hole warning: depth/diameter ratio is {ratio:.1f}. "
                "Consider using smaller peck depth or pilot hole."
            )

    def _generate_canned_cycle(self) -> List[str]:
        """Generate G-code using G83 canned cycle."""
        lines = []

        # Header
        lines.append("(Peck Drilling - G83 Canned Cycle)")
        lines.append(f"(Holes: {len(self.holes)})")
        lines.append(f"(Depth: {self.config.hole_depth_mm}mm, Peck: {self.config.peck_depth_mm}mm)")
        lines.append(f"(Drill: {self.config.drill_diameter_mm}mm)")
        lines.append("")

        # Setup
        lines.append("G21 (Units: mm)")
        lines.append("G90 (Absolute positioning)")
        lines.append("G98 (Return to initial Z after cycle)")
        lines.append(f"G0 Z{self.config.safe_z_mm:.3f} (Safe height)")
        lines.append(f"M3 S{self.config.spindle_rpm} (Spindle on)")
        lines.append("")

        # First hole with full G83 parameters
        first = self.holes[0]
        depth = first.depth_mm or self.config.hole_depth_mm
        z_depth = -depth

        lines.append(f"(Hole 1{': ' + first.label if first.label else ''})")
        lines.append(
            f"G83 X{first.x:.3f} Y{first.y:.3f} "
            f"Z{z_depth:.3f} R{self.config.retract_z_mm:.3f} "
            f"Q{self.config.peck_depth_mm:.3f} F{self.config.feed_rate:.0f}"
        )

        # Subsequent holes - can use abbreviated form
        for i, hole in enumerate(self.holes[1:], start=2):
            depth = hole.depth_mm or self.config.hole_depth_mm
            z_depth = -depth

            label = f"(Hole {i}{': ' + hole.label if hole.label else ''})"
            lines.append(label)

            # If depth differs, include Z and Q
            if hole.depth_mm and hole.depth_mm != self.config.hole_depth_mm:
                lines.append(
                    f"X{hole.x:.3f} Y{hole.y:.3f} Z{z_depth:.3f}"
                )
            else:
                lines.append(f"X{hole.x:.3f} Y{hole.y:.3f}")

        # Cancel canned cycle
        lines.append("")
        lines.append("G80 (Cancel canned cycle)")
        lines.append(f"G0 Z{self.config.safe_z_mm:.3f} (Safe height)")
        lines.append("M5 (Spindle off)")
        lines.append("M30 (Program end)")

        return lines

    def _generate_expanded(self) -> List[str]:
        """Generate expanded G-code (no canned cycle)."""
        lines = []

        # Header
        lines.append("(Peck Drilling - Expanded G-code)")
        lines.append(f"(Holes: {len(self.holes)})")
        lines.append(f"(Depth: {self.config.hole_depth_mm}mm, Peck: {self.config.peck_depth_mm}mm)")
        lines.append("")

        # Setup
        lines.append("G21 (Units: mm)")
        lines.append("G90 (Absolute positioning)")
        lines.append(f"G0 Z{self.config.safe_z_mm:.3f}")
        lines.append(f"M3 S{self.config.spindle_rpm}")
        lines.append("")

        for i, hole in enumerate(self.holes, start=1):
            depth = hole.depth_mm or self.config.hole_depth_mm

            lines.append(f"(Hole {i}{': ' + hole.label if hole.label else ''})")

            # Rapid to position
            lines.append(f"G0 X{hole.x:.3f} Y{hole.y:.3f}")
            lines.append(f"G0 Z{self.config.retract_z_mm:.3f}")

            # Peck drilling loop
            current_depth = 0.0
            while current_depth < depth:
                current_depth += self.config.peck_depth_mm
                if current_depth > depth:
                    current_depth = depth

                z = -current_depth

                # Plunge to current depth
                lines.append(f"G1 Z{z:.3f} F{self.config.feed_rate:.0f}")

                # Dwell if configured
                if self.config.dwell_ms > 0:
                    lines.append(f"G4 P{self.config.dwell_ms}")

                # Retract to clear chips
                if current_depth < depth:
                    lines.append(f"G0 Z{self.config.retract_z_mm:.3f}")

            # Final retract
            lines.append(f"G0 Z{self.config.safe_z_mm:.3f}")
            lines.append("")

        # Footer
        lines.append("M5 (Spindle off)")
        lines.append("M30 (Program end)")

        return lines

    def _estimate_time(self) -> float:
        """Estimate drilling time in seconds."""
        time_seconds = 0.0

        for hole in self.holes:
            depth = hole.depth_mm or self.config.hole_depth_mm
            peck_count = math.ceil(depth / self.config.peck_depth_mm)

            # Time for each peck cycle
            for p in range(peck_count):
                # Plunge time
                peck = min(self.config.peck_depth_mm, depth - p * self.config.peck_depth_mm)
                time_seconds += (peck / self.config.feed_rate) * 60

                # Retract time (rapid)
                retract_dist = self.config.retract_z_mm + p * self.config.peck_depth_mm
                time_seconds += (retract_dist / self.config.rapid_rate) * 60

                # Rapid back down time
                if p < peck_count - 1:
                    time_seconds += (retract_dist / self.config.rapid_rate) * 60

            # Dwell time
            time_seconds += (self.config.dwell_ms / 1000.0) * peck_count

        # Add rapid move time between holes
        if len(self.holes) > 1:
            total_xy_dist = 0.0
            for i in range(1, len(self.holes)):
                dx = self.holes[i].x - self.holes[i-1].x
                dy = self.holes[i].y - self.holes[i-1].y
                total_xy_dist += math.hypot(dx, dy)
            time_seconds += (total_xy_dist / self.config.rapid_rate) * 60

        # Add overhead
        time_seconds *= 1.1

        return time_seconds

    def _empty_result(self) -> DrillResult:
        """Return empty result for error cases."""
        return DrillResult(
            gcode="",
            hole_count=0,
            total_depth_mm=0.0,
            estimated_time_seconds=0.0,
            warnings=self._warnings,
        )
