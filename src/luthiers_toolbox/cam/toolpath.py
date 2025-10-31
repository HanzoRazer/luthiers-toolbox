"""
Toolpath generation for CNC operations.
"""

from typing import List, Tuple, Optional
from enum import Enum


class ToolpathType(Enum):
    """Types of toolpath operations."""

    PROFILE = "profile"
    POCKET = "pocket"
    DRILL = "drill"
    ENGRAVE = "engrave"


class Toolpath:
    """
    Represents a CNC toolpath.
    
    Contains a sequence of movements and cutting operations.
    """

    def __init__(
        self,
        name: str,
        toolpath_type: ToolpathType,
        tool_diameter: float,
        feedrate: float,
        plunge_rate: float,
        depth: float,
    ):
        """
        Initialize a toolpath.
        
        Args:
            name: Toolpath name
            toolpath_type: Type of operation
            tool_diameter: Tool diameter in inches
            feedrate: Cutting feedrate in inches/min
            plunge_rate: Plunge feedrate in inches/min
            depth: Target depth in inches
        """
        self.name = name
        self.toolpath_type = toolpath_type
        self.tool_diameter = tool_diameter
        self.feedrate = feedrate
        self.plunge_rate = plunge_rate
        self.depth = depth
        self.points: List[Tuple[float, float, float]] = []

    def add_point(self, x: float, y: float, z: float) -> None:
        """Add a point to the toolpath."""
        self.points.append((x, y, z))

    def add_rapid_move(self, x: float, y: float, z: float) -> None:
        """Add a rapid positioning move."""
        self.points.append((x, y, z))

    def get_estimated_time(self) -> float:
        """
        Estimate machining time in minutes.
        
        Returns:
            Estimated time in minutes
        """
        if len(self.points) < 2:
            return 0.0

        total_distance = 0.0
        for i in range(1, len(self.points)):
            x1, y1, z1 = self.points[i - 1]
            x2, y2, z2 = self.points[i]

            # Calculate 3D distance
            distance = ((x2 - x1) ** 2 + (y2 - y1) ** 2 + (z2 - z1) ** 2) ** 0.5
            total_distance += distance

        # Estimate time based on average feedrate
        # Using feedrate for XY moves, plunge_rate for Z moves
        return total_distance / self.feedrate

    def __repr__(self) -> str:
        return (
            f"Toolpath('{self.name}', type={self.toolpath_type.value}, "
            f"points={len(self.points)})"
        )


class ToolpathGenerator:
    """
    Generates toolpaths from CAD geometry.
    """

    def __init__(self, stock_thickness: float = 2.0):
        """
        Initialize toolpath generator.
        
        Args:
            stock_thickness: Material thickness in inches
        """
        self.stock_thickness = stock_thickness
        self.toolpaths: List[Toolpath] = []

    def add_toolpath(self, toolpath: Toolpath) -> None:
        """Add a toolpath to the collection."""
        self.toolpaths.append(toolpath)

    def generate_profile_toolpath(
        self,
        points: List[Tuple[float, float]],
        depth: float,
        tool_diameter: float = 0.25,
        feedrate: float = 40.0,
        name: str = "Profile",
    ) -> Toolpath:
        """
        Generate a profile cutting toolpath.
        
        Args:
            points: List of (x, y) points defining the profile
            depth: Cutting depth
            tool_diameter: Tool diameter
            feedrate: Feedrate
            name: Toolpath name
            
        Returns:
            Generated toolpath
        """
        toolpath = Toolpath(
            name=name,
            toolpath_type=ToolpathType.PROFILE,
            tool_diameter=tool_diameter,
            feedrate=feedrate,
            plunge_rate=feedrate * 0.5,
            depth=depth,
        )

        # Rapid to start position above work
        if points:
            toolpath.add_rapid_move(points[0][0], points[0][1], 0.1)

            # Plunge to depth
            toolpath.add_point(points[0][0], points[0][1], -depth)

            # Cut along profile
            for x, y in points[1:]:
                toolpath.add_point(x, y, -depth)

            # Return to start
            toolpath.add_point(points[0][0], points[0][1], -depth)

            # Retract
            toolpath.add_rapid_move(points[0][0], points[0][1], 0.1)

        self.add_toolpath(toolpath)
        return toolpath

    def generate_pocket_toolpath(
        self,
        bounds: Tuple[float, float, float, float],
        depth: float,
        tool_diameter: float = 0.25,
        stepover: float = 0.2,
        feedrate: float = 40.0,
        name: str = "Pocket",
    ) -> Toolpath:
        """
        Generate a pocket clearing toolpath.
        
        Args:
            bounds: (x_min, y_min, x_max, y_max) bounding box
            depth: Pocket depth
            tool_diameter: Tool diameter
            stepover: Stepover distance
            feedrate: Feedrate
            name: Toolpath name
            
        Returns:
            Generated toolpath
        """
        toolpath = Toolpath(
            name=name,
            toolpath_type=ToolpathType.POCKET,
            tool_diameter=tool_diameter,
            feedrate=feedrate,
            plunge_rate=feedrate * 0.5,
            depth=depth,
        )

        x_min, y_min, x_max, y_max = bounds

        # Simple zigzag pattern
        y = y_min
        direction = 1
        while y <= y_max:
            if direction > 0:
                toolpath.add_point(x_min, y, -depth)
                toolpath.add_point(x_max, y, -depth)
            else:
                toolpath.add_point(x_max, y, -depth)
                toolpath.add_point(x_min, y, -depth)

            y += stepover
            direction *= -1

        self.add_toolpath(toolpath)
        return toolpath

    def get_total_time(self) -> float:
        """Get estimated total machining time."""
        return sum(tp.get_estimated_time() for tp in self.toolpaths)

    def __repr__(self) -> str:
        return f"ToolpathGenerator(toolpaths={len(self.toolpaths)})"
