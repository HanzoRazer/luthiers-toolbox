"""
Drill Hole Patterns

Parametric hole pattern generators for common guitar drilling operations:
- String-through ferrules (6-string, 7-string, bass)
- Bolt patterns (neck pocket, pickguard, tremolo)
- Grid patterns (ventilation, weight relief)
- Circular patterns (control cavity, sound holes)

Each pattern generator produces a list of DrillHole objects that can
be passed to PeckDrill for G-code generation.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional

from .peck_cycle import DrillHole


@dataclass
class StringThroughPattern:
    """
    String-through ferrule drilling pattern.

    For string-through body guitars (Telecaster, etc.) where strings
    pass through the body and anchor in ferrules on the back.

    Standard spacings:
    - 6-string guitar: 10.5mm (Fender), 10.8mm (Gibson)
    - 7-string guitar: 9.5mm typical
    - 4-string bass: 19mm typical
    - 5-string bass: 16mm typical
    """

    string_count: int = 6
    spacing_mm: float = 10.5  # String to string spacing
    start_x: float = 0.0  # X position of first string (low E)
    start_y: float = 0.0  # Y position (usually bridge location)
    angle_deg: float = 0.0  # Angle of string line (for angled bridges)
    depth_mm: Optional[float] = None  # Override depth per hole

    def get_holes(self) -> List[DrillHole]:
        """Generate drill hole positions for string-through."""
        holes = []
        angle_rad = math.radians(self.angle_deg)

        for i in range(self.string_count):
            # Calculate position along string line
            offset = i * self.spacing_mm

            x = self.start_x + offset * math.cos(angle_rad)
            y = self.start_y + offset * math.sin(angle_rad)

            string_num = i + 1
            string_name = self._string_name(i)

            holes.append(DrillHole(
                x=x,
                y=y,
                depth_mm=self.depth_mm,
                label=f"string_{string_num}_{string_name}",
            ))

        return holes

    def _string_name(self, index: int) -> str:
        """Get string name for labeling."""
        if self.string_count == 6:
            names = ["E_low", "A", "D", "G", "B", "E_high"]
        elif self.string_count == 7:
            names = ["B_low", "E_low", "A", "D", "G", "B", "E_high"]
        elif self.string_count == 4:
            names = ["E", "A", "D", "G"]
        elif self.string_count == 5:
            names = ["B", "E", "A", "D", "G"]
        else:
            names = [str(i + 1) for i in range(self.string_count)]

        return names[index] if index < len(names) else str(index + 1)


@dataclass
class BoltPattern:
    """
    Bolt/screw hole pattern generator.

    Common patterns:
    - Neck pocket: 4 bolts in rectangle (Fender style)
    - Neck pocket: 3 bolts in triangle (some Gibsons)
    - Pickguard: varies by model
    - Tremolo: typically 2-6 mounting screws
    """

    # Pattern type
    pattern_type: str = "rectangle"  # rectangle, triangle, line, custom

    # Rectangle/square pattern
    width_mm: float = 50.0  # X span
    height_mm: float = 40.0  # Y span
    center_x: float = 0.0
    center_y: float = 0.0

    # Number of bolts (for line/rectangle)
    bolt_count: int = 4

    # Custom positions (list of (x, y) tuples)
    custom_positions: Optional[List[tuple]] = None

    # Depth
    depth_mm: Optional[float] = None

    # Labels
    label_prefix: str = "bolt"

    def get_holes(self) -> List[DrillHole]:
        """Generate drill hole positions."""
        if self.pattern_type == "rectangle":
            return self._rectangle_pattern()
        elif self.pattern_type == "triangle":
            return self._triangle_pattern()
        elif self.pattern_type == "line":
            return self._line_pattern()
        elif self.pattern_type == "custom" and self.custom_positions:
            return self._custom_pattern()
        else:
            return self._rectangle_pattern()

    def _rectangle_pattern(self) -> List[DrillHole]:
        """Generate 4-corner rectangle pattern."""
        half_w = self.width_mm / 2.0
        half_h = self.height_mm / 2.0

        positions = [
            (self.center_x - half_w, self.center_y - half_h),  # Bottom-left
            (self.center_x + half_w, self.center_y - half_h),  # Bottom-right
            (self.center_x + half_w, self.center_y + half_h),  # Top-right
            (self.center_x - half_w, self.center_y + half_h),  # Top-left
        ]

        return [
            DrillHole(
                x=x, y=y,
                depth_mm=self.depth_mm,
                label=f"{self.label_prefix}_{i+1}",
            )
            for i, (x, y) in enumerate(positions[:self.bolt_count])
        ]

    def _triangle_pattern(self) -> List[DrillHole]:
        """Generate 3-point triangle pattern."""
        # Equilateral triangle inscribed in rectangle
        half_w = self.width_mm / 2.0
        half_h = self.height_mm / 2.0

        positions = [
            (self.center_x, self.center_y + half_h),  # Top center
            (self.center_x - half_w, self.center_y - half_h),  # Bottom-left
            (self.center_x + half_w, self.center_y - half_h),  # Bottom-right
        ]

        return [
            DrillHole(
                x=x, y=y,
                depth_mm=self.depth_mm,
                label=f"{self.label_prefix}_{i+1}",
            )
            for i, (x, y) in enumerate(positions)
        ]

    def _line_pattern(self) -> List[DrillHole]:
        """Generate holes in a line."""
        if self.bolt_count < 2:
            return [DrillHole(
                x=self.center_x,
                y=self.center_y,
                depth_mm=self.depth_mm,
                label=f"{self.label_prefix}_1",
            )]

        spacing = self.width_mm / (self.bolt_count - 1)
        start_x = self.center_x - self.width_mm / 2.0

        return [
            DrillHole(
                x=start_x + i * spacing,
                y=self.center_y,
                depth_mm=self.depth_mm,
                label=f"{self.label_prefix}_{i+1}",
            )
            for i in range(self.bolt_count)
        ]

    def _custom_pattern(self) -> List[DrillHole]:
        """Generate holes from custom positions."""
        return [
            DrillHole(
                x=x + self.center_x,
                y=y + self.center_y,
                depth_mm=self.depth_mm,
                label=f"{self.label_prefix}_{i+1}",
            )
            for i, (x, y) in enumerate(self.custom_positions or [])
        ]


@dataclass
class GridPattern:
    """
    Rectangular grid drilling pattern.

    Used for:
    - Weight relief chambers
    - Ventilation holes
    - Decorative patterns
    """

    rows: int = 3
    cols: int = 4
    row_spacing_mm: float = 20.0
    col_spacing_mm: float = 20.0
    center_x: float = 0.0
    center_y: float = 0.0
    depth_mm: Optional[float] = None
    label_prefix: str = "grid"

    def get_holes(self) -> List[DrillHole]:
        """Generate grid hole positions."""
        holes = []

        # Calculate start position to center the grid
        start_x = self.center_x - (self.cols - 1) * self.col_spacing_mm / 2.0
        start_y = self.center_y - (self.rows - 1) * self.row_spacing_mm / 2.0

        for row in range(self.rows):
            for col in range(self.cols):
                x = start_x + col * self.col_spacing_mm
                y = start_y + row * self.row_spacing_mm

                holes.append(DrillHole(
                    x=x,
                    y=y,
                    depth_mm=self.depth_mm,
                    label=f"{self.label_prefix}_r{row+1}c{col+1}",
                ))

        return holes


@dataclass
class CircularPattern:
    """
    Circular/radial drilling pattern.

    Used for:
    - Control cavity covers
    - Sound hole decorations
    - Speaker mounting
    """

    hole_count: int = 6
    radius_mm: float = 30.0
    center_x: float = 0.0
    center_y: float = 0.0
    start_angle_deg: float = 0.0  # Angle of first hole
    depth_mm: Optional[float] = None
    label_prefix: str = "circle"

    # Optional center hole
    include_center: bool = False

    def get_holes(self) -> List[DrillHole]:
        """Generate circular hole positions."""
        holes = []

        # Center hole if requested
        if self.include_center:
            holes.append(DrillHole(
                x=self.center_x,
                y=self.center_y,
                depth_mm=self.depth_mm,
                label=f"{self.label_prefix}_center",
            ))

        # Circumference holes
        angle_step = 360.0 / self.hole_count
        start_rad = math.radians(self.start_angle_deg)

        for i in range(self.hole_count):
            angle = start_rad + math.radians(i * angle_step)
            x = self.center_x + self.radius_mm * math.cos(angle)
            y = self.center_y + self.radius_mm * math.sin(angle)

            holes.append(DrillHole(
                x=x,
                y=y,
                depth_mm=self.depth_mm,
                label=f"{self.label_prefix}_{i+1}",
            ))

        return holes


# -----------------------------------------------------------------------------
# Preset Patterns
# -----------------------------------------------------------------------------

def fender_string_through_6() -> StringThroughPattern:
    """Fender-style 6-string through-body pattern."""
    return StringThroughPattern(
        string_count=6,
        spacing_mm=10.5,
    )


def gibson_string_through_6() -> StringThroughPattern:
    """Gibson-style 6-string through-body pattern."""
    return StringThroughPattern(
        string_count=6,
        spacing_mm=10.8,
    )


def fender_neck_pocket_4bolt() -> BoltPattern:
    """Fender 4-bolt neck pocket pattern."""
    return BoltPattern(
        pattern_type="rectangle",
        width_mm=51.0,  # ~2 inches
        height_mm=38.0,  # ~1.5 inches
        bolt_count=4,
        label_prefix="neck_bolt",
    )


def gibson_neck_pocket_4bolt() -> BoltPattern:
    """Gibson 4-bolt neck pocket pattern (set-neck conversion)."""
    return BoltPattern(
        pattern_type="rectangle",
        width_mm=44.0,
        height_mm=35.0,
        bolt_count=4,
        label_prefix="neck_bolt",
    )
