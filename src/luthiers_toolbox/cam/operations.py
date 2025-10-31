"""
Common CAM operations for guitar manufacturing.
"""

from typing import List, Tuple
from .toolpath import Toolpath, ToolpathType


class PocketOperation:
    """Pocket milling operation."""

    def __init__(
        self,
        bounds: Tuple[float, float, float, float],
        depth: float,
        tool_diameter: float = 0.25,
        stepover_ratio: float = 0.4,
        feedrate: float = 40.0,
    ):
        """
        Initialize pocket operation.
        
        Args:
            bounds: (x_min, y_min, x_max, y_max)
            depth: Pocket depth
            tool_diameter: Tool diameter
            stepover_ratio: Stepover as ratio of tool diameter
            feedrate: Cutting feedrate
        """
        self.bounds = bounds
        self.depth = depth
        self.tool_diameter = tool_diameter
        self.stepover_ratio = stepover_ratio
        self.feedrate = feedrate

    def generate(self, name: str = "Pocket") -> Toolpath:
        """Generate the toolpath."""
        toolpath = Toolpath(
            name=name,
            toolpath_type=ToolpathType.POCKET,
            tool_diameter=self.tool_diameter,
            feedrate=self.feedrate,
            plunge_rate=self.feedrate * 0.5,
            depth=self.depth,
        )

        x_min, y_min, x_max, y_max = self.bounds
        stepover = self.tool_diameter * self.stepover_ratio

        # Zigzag pattern
        y = y_min
        direction = 1
        while y <= y_max:
            if direction > 0:
                toolpath.add_point(x_min, y, -self.depth)
                toolpath.add_point(x_max, y, -self.depth)
            else:
                toolpath.add_point(x_max, y, -self.depth)
                toolpath.add_point(x_min, y, -self.depth)

            y += stepover
            direction *= -1

        return toolpath


class ProfileOperation:
    """Profile cutting operation."""

    def __init__(
        self,
        points: List[Tuple[float, float]],
        depth: float,
        tool_diameter: float = 0.25,
        offset: float = 0.0,
        feedrate: float = 40.0,
    ):
        """
        Initialize profile operation.
        
        Args:
            points: Profile points (x, y)
            depth: Cutting depth
            tool_diameter: Tool diameter
            offset: Offset from profile (positive = outside, negative = inside)
            feedrate: Cutting feedrate
        """
        self.points = points
        self.depth = depth
        self.tool_diameter = tool_diameter
        self.offset = offset
        self.feedrate = feedrate

    def generate(self, name: str = "Profile") -> Toolpath:
        """Generate the toolpath."""
        toolpath = Toolpath(
            name=name,
            toolpath_type=ToolpathType.PROFILE,
            tool_diameter=self.tool_diameter,
            feedrate=self.feedrate,
            plunge_rate=self.feedrate * 0.5,
            depth=self.depth,
        )

        # Apply offset if specified
        # For simplicity, we'll use the points as-is
        # In a production system, this would calculate proper offset curves
        offset_points = self.points

        if offset_points:
            # Rapid to start
            toolpath.add_rapid_move(offset_points[0][0], offset_points[0][1], 0.1)

            # Plunge
            toolpath.add_point(offset_points[0][0], offset_points[0][1], -self.depth)

            # Cut profile
            for x, y in offset_points[1:]:
                toolpath.add_point(x, y, -self.depth)

            # Close path
            toolpath.add_point(offset_points[0][0], offset_points[0][1], -self.depth)

            # Retract
            toolpath.add_rapid_move(offset_points[0][0], offset_points[0][1], 0.1)

        return toolpath


class DrillOperation:
    """Drilling operation for holes."""

    def __init__(
        self,
        positions: List[Tuple[float, float]],
        depth: float,
        drill_diameter: float = 0.125,
        peck_depth: float = 0.1,
        feedrate: float = 20.0,
    ):
        """
        Initialize drill operation.
        
        Args:
            positions: Hole positions (x, y)
            depth: Hole depth
            drill_diameter: Drill bit diameter
            peck_depth: Peck drilling increment
            feedrate: Drilling feedrate
        """
        self.positions = positions
        self.depth = depth
        self.drill_diameter = drill_diameter
        self.peck_depth = peck_depth
        self.feedrate = feedrate

    def generate(self, name: str = "Drill") -> Toolpath:
        """Generate the toolpath."""
        toolpath = Toolpath(
            name=name,
            toolpath_type=ToolpathType.DRILL,
            tool_diameter=self.drill_diameter,
            feedrate=self.feedrate,
            plunge_rate=self.feedrate,
            depth=self.depth,
        )

        for x, y in self.positions:
            # Rapid to position
            toolpath.add_rapid_move(x, y, 0.1)

            # Peck drill
            current_depth = 0
            while current_depth < self.depth:
                current_depth = min(current_depth + self.peck_depth, self.depth)
                toolpath.add_point(x, y, -current_depth)
                # Retract slightly for chip clearing
                if current_depth < self.depth:
                    toolpath.add_point(x, y, -current_depth + self.peck_depth * 0.5)

            # Full retract
            toolpath.add_rapid_move(x, y, 0.1)

        return toolpath
