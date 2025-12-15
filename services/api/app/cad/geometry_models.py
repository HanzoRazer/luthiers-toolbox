# services/api/app/cad/geometry_models.py
"""
Pydantic models for CAD geometry primitives.

All coordinates are in model units (mm by default).
These models enforce structural validation before geometry reaches the DXF engine.
"""

from __future__ import annotations

from typing import List, Literal, Optional, Tuple, Union
from pydantic import BaseModel, Field, field_validator, model_validator
import math


Number = float  # Type alias for clarity


class Point2D(BaseModel):
    """2D point in model space."""
    
    x: Number = Field(..., description="X coordinate in model units (mm or inches).")
    y: Number = Field(..., description="Y coordinate in model units (mm or inches).")
    
    def to_tuple(self) -> Tuple[float, float]:
        return (self.x, self.y)
    
    def distance_to(self, other: "Point2D") -> float:
        """Euclidean distance to another point."""
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)
    
    def __hash__(self) -> int:
        return hash((self.x, self.y))


class Point3D(BaseModel):
    """3D point in model space (for future STL/3D support)."""
    
    x: Number = Field(..., description="X coordinate.")
    y: Number = Field(..., description="Y coordinate.")
    z: Number = Field(default=0.0, description="Z coordinate.")
    
    def to_tuple(self) -> Tuple[float, float, float]:
        return (self.x, self.y, self.z)


class Polyline2D(BaseModel):
    """
    2D polyline (sequence of connected line segments).
    
    Can be open or closed. Minimum 2 points required.
    """
    
    points: List[Point2D] = Field(..., min_length=2)
    closed: bool = Field(
        default=False,
        description="Whether to close the polyline by connecting last point to first.",
    )
    
    @field_validator("points")
    @classmethod
    def validate_points(cls, points: List[Point2D]) -> List[Point2D]:
        if len(points) < 2:
            raise ValueError("Polyline must have at least 2 points.")
        return points
    
    def to_tuples(self) -> List[Tuple[float, float]]:
        """Convert to list of coordinate tuples for ezdxf."""
        return [p.to_tuple() for p in self.points]
    
    def total_length(self) -> float:
        """Calculate total polyline length."""
        length = 0.0
        for i in range(len(self.points) - 1):
            length += self.points[i].distance_to(self.points[i + 1])
        if self.closed and len(self.points) > 2:
            length += self.points[-1].distance_to(self.points[0])
        return length
    
    def bounds(self) -> Tuple[float, float, float, float]:
        """Return (min_x, min_y, max_x, max_y) bounding box."""
        xs = [p.x for p in self.points]
        ys = [p.y for p in self.points]
        return (min(xs), min(ys), max(xs), max(ys))


class Circle2D(BaseModel):
    """2D circle defined by center and radius."""
    
    center: Point2D
    radius: Number = Field(..., gt=0.0, description="Circle radius (must be positive).")
    
    def bounds(self) -> Tuple[float, float, float, float]:
        """Return bounding box."""
        return (
            self.center.x - self.radius,
            self.center.y - self.radius,
            self.center.x + self.radius,
            self.center.y + self.radius,
        )
    
    def circumference(self) -> float:
        return 2 * math.pi * self.radius
    
    def area(self) -> float:
        return math.pi * self.radius ** 2


class Arc2D(BaseModel):
    """2D circular arc defined by center, radius, and angle range."""
    
    center: Point2D
    radius: Number = Field(..., gt=0.0)
    start_angle_deg: Number = Field(..., ge=0.0, le=360.0)
    end_angle_deg: Number = Field(..., ge=0.0, le=360.0)
    
    @model_validator(mode="after")
    def validate_angles(self) -> "Arc2D":
        if self.start_angle_deg == self.end_angle_deg:
            raise ValueError("Arc start and end angles cannot be equal (use Circle2D for full circle).")
        return self
    
    def arc_length(self) -> float:
        """Calculate arc length."""
        angle_diff = abs(self.end_angle_deg - self.start_angle_deg)
        return (angle_diff / 360.0) * 2 * math.pi * self.radius


class Line2D(BaseModel):
    """2D line segment between two points."""
    
    start: Point2D
    end: Point2D
    
    @model_validator(mode="after")
    def validate_different_points(self) -> "Line2D":
        if self.start.x == self.end.x and self.start.y == self.end.y:
            raise ValueError("Line start and end points cannot be identical.")
        return self
    
    def length(self) -> float:
        return self.start.distance_to(self.end)
    
    def midpoint(self) -> Point2D:
        return Point2D(
            x=(self.start.x + self.end.x) / 2,
            y=(self.start.y + self.end.y) / 2,
        )


class LayerStyle(BaseModel):
    """DXF layer configuration."""
    
    name: str = Field(..., min_length=1, max_length=64)
    color_index: int = Field(
        default=7, ge=1, le=255, 
        description="AutoCAD color index (1–255). 7=white/black."
    )
    lineweight_mm: Optional[Number] = Field(
        default=None, 
        description="Optional lineweight in mm. None=default."
    )
    linetype: str = Field(
        default="CONTINUOUS",
        description="Line type name (CONTINUOUS, DASHED, etc.)"
    )


class DxfDocumentConfig(BaseModel):
    """
    Configuration for a DXF document.
    
    Includes safety guardrails to prevent runaway geometry.
    """
    
    version: Literal["R2000", "R2010", "R2013", "R2018"] = Field(
        default="R2010",
        description="DXF version. R2010 is widely compatible."
    )
    units: Literal["mm", "inch"] = Field(
        default="mm",
        description="Model units."
    )
    max_entities: int = Field(
        default=10000,
        ge=1,
        le=100000,
        description="Hard guardrail for entity count in a single document.",
    )
    coord_limit: Number = Field(
        default=1_000_000.0,
        gt=0.0,
        description="Maximum absolute coordinate allowed (safety guardrail).",
    )
    precision: int = Field(
        default=6,
        ge=1,
        le=12,
        description="Decimal precision for coordinates."
    )
    
    # Feature flags
    create_default_layers: bool = Field(
        default=True,
        description="Whether to create standard layers (OUTLINE, CONSTRUCTION, etc.)"
    )
    validate_geometry: bool = Field(
        default=True,
        description="Whether to validate geometry bounds before adding."
    )


# Type aliases for entity collections
EntityList = List[Union[Polyline2D, Circle2D, Arc2D, Line2D]]
PointList = List[Point2D]
