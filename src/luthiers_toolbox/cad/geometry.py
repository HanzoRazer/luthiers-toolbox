"""
Basic geometric primitives for CAD operations.
"""

from typing import Tuple
import math


class Point:
    """Represents a 2D point in space."""

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def distance_to(self, other: "Point") -> float:
        """Calculate distance to another point."""
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)

    def __repr__(self) -> str:
        return f"Point({self.x}, {self.y})"

    def to_tuple(self) -> Tuple[float, float]:
        """Convert to tuple representation."""
        return (self.x, self.y)


class Line:
    """Represents a line segment between two points."""

    def __init__(self, start: Point, end: Point):
        self.start = start
        self.end = end

    def length(self) -> float:
        """Calculate the length of the line."""
        return self.start.distance_to(self.end)

    def midpoint(self) -> Point:
        """Calculate the midpoint of the line."""
        return Point((self.start.x + self.end.x) / 2, (self.start.y + self.end.y) / 2)

    def __repr__(self) -> str:
        return f"Line({self.start}, {self.end})"


class Arc:
    """Represents a circular arc."""

    def __init__(self, center: Point, radius: float, start_angle: float, end_angle: float):
        self.center = center
        self.radius = radius
        self.start_angle = start_angle  # in degrees
        self.end_angle = end_angle  # in degrees

    def length(self) -> float:
        """Calculate the arc length."""
        angle_diff = abs(self.end_angle - self.start_angle)
        return (angle_diff / 360) * 2 * math.pi * self.radius

    def __repr__(self) -> str:
        return f"Arc({self.center}, r={self.radius}, {self.start_angle}° to {self.end_angle}°)"


class Circle:
    """Represents a circle."""

    def __init__(self, center: Point, radius: float):
        self.center = center
        self.radius = radius

    def circumference(self) -> float:
        """Calculate the circumference."""
        return 2 * math.pi * self.radius

    def area(self) -> float:
        """Calculate the area."""
        return math.pi * self.radius ** 2

    def __repr__(self) -> str:
        return f"Circle({self.center}, r={self.radius})"
