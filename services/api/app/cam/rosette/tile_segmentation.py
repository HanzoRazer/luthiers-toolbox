"""
Rosette Tile Segmentation - Real Geometry Implementation

Computes tile geometry for rosette rings based on:
- Ring inner/outer radius
- Tile width (arc length at average radius)
- Pattern type (checkerboard, herringbone, etc.)
- Kerf compensation for cutting

A tile is a trapezoidal segment spanning from inner to outer radius
over an angular arc around the ring.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum


class TilePattern(str, Enum):
    """Supported tile patterns."""
    CHECKERBOARD = "checkerboard"
    HERRINGBONE = "herringbone"
    RADIAL = "radial"
    SOLID = "solid"


@dataclass
class Point2D:
    """2D point in mm coordinates."""
    x: float
    y: float

    def to_tuple(self) -> Tuple[float, float]:
        return (self.x, self.y)

    def rotate(self, angle_rad: float, cx: float = 0, cy: float = 0) -> 'Point2D':
        """Rotate point around center (cx, cy)."""
        dx = self.x - cx
        dy = self.y - cy
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        return Point2D(
            cx + dx * cos_a - dy * sin_a,
            cy + dx * sin_a + dy * cos_a
        )


@dataclass
class TileGeometry:
    """
    Complete geometry for a single rosette tile.

    Tiles are trapezoids with 4 corners:
    - inner_start: inner radius at start angle
    - inner_end: inner radius at end angle
    - outer_start: outer radius at start angle
    - outer_end: outer radius at end angle

    Winding order is counter-clockwise for CAM compatibility.
    """
    tile_index: int
    theta_start_rad: float
    theta_end_rad: float
    inner_start: Point2D
    inner_end: Point2D
    outer_start: Point2D
    outer_end: Point2D
    color_index: int = 0  # For alternating patterns

    @property
    def theta_start_deg(self) -> float:
        return math.degrees(self.theta_start_rad)

    @property
    def theta_end_deg(self) -> float:
        return math.degrees(self.theta_end_rad)

    @property
    def arc_length_mm(self) -> float:
        """Arc length at average radius."""
        avg_r = (self.inner_radius + self.outer_radius) / 2
        return avg_r * abs(self.theta_end_rad - self.theta_start_rad)

    @property
    def inner_radius(self) -> float:
        """Inner radius derived from geometry."""
        return math.sqrt(self.inner_start.x**2 + self.inner_start.y**2)

    @property
    def outer_radius(self) -> float:
        """Outer radius derived from geometry."""
        return math.sqrt(self.outer_start.x**2 + self.outer_start.y**2)

    def polygon_points(self) -> List[Point2D]:
        """Return CCW polygon for CAM/DXF export."""
        return [
            self.inner_start,
            self.outer_start,
            self.outer_end,
            self.inner_end,
        ]

    def polygon_tuples(self) -> List[Tuple[float, float]]:
        """Return polygon as list of (x, y) tuples."""
        return [p.to_tuple() for p in self.polygon_points()]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "tile_index": self.tile_index,
            "theta_start_deg": self.theta_start_deg,
            "theta_end_deg": self.theta_end_deg,
            "inner_start": self.inner_start.to_tuple(),
            "inner_end": self.inner_end.to_tuple(),
            "outer_start": self.outer_start.to_tuple(),
            "outer_end": self.outer_end.to_tuple(),
            "color_index": self.color_index,
            "arc_length_mm": self.arc_length_mm,
        }


@dataclass
class RingSegmentation:
    """Complete segmentation result for a ring."""
    ring_id: int
    inner_radius_mm: float
    outer_radius_mm: float
    tile_count: int
    tile_width_mm: float
    pattern: TilePattern
    tiles: List[TileGeometry]
    kerf_mm: float = 0.0

    @property
    def circumference_mm(self) -> float:
        """Average circumference."""
        avg_r = (self.inner_radius_mm + self.outer_radius_mm) / 2
        return 2 * math.pi * avg_r

    @property
    def ring_width_mm(self) -> float:
        return self.outer_radius_mm - self.inner_radius_mm

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "segmentation_id": f"seg_{self.ring_id}",
            "ring_id": self.ring_id,
            "inner_radius_mm": self.inner_radius_mm,
            "outer_radius_mm": self.outer_radius_mm,
            "tile_count": self.tile_count,
            "tile_width_mm": self.tile_width_mm,
            "pattern": self.pattern.value,
            "kerf_mm": self.kerf_mm,
            "circumference_mm": self.circumference_mm,
            "ring_width_mm": self.ring_width_mm,
            "tiles": [t.to_dict() for t in self.tiles],
        }


def compute_tile_count(
    inner_radius_mm: float,
    outer_radius_mm: float,
    tile_width_mm: float,
    min_tiles: int = 4,
) -> int:
    """
    Calculate how many tiles fit around the ring circumference.

    Uses average radius for circumference calculation.
    """
    avg_radius = (inner_radius_mm + outer_radius_mm) / 2
    circumference = 2 * math.pi * avg_radius
    count = max(min_tiles, int(round(circumference / tile_width_mm)))
    return count


def compute_tile_geometry(
    inner_radius_mm: float,
    outer_radius_mm: float,
    tile_index: int,
    tile_count: int,
    kerf_mm: float = 0.0,
) -> TileGeometry:
    """
    Calculate exact polygon geometry for one tile.

    Args:
        inner_radius_mm: Inner ring radius
        outer_radius_mm: Outer ring radius
        tile_index: 0-based tile index
        tile_count: Total tiles in ring
        kerf_mm: Kerf compensation (shrinks tile by this amount on each edge)

    Returns:
        TileGeometry with all corner points
    """
    # Angular extent of tile
    angle_step = 2 * math.pi / tile_count
    theta_start = tile_index * angle_step
    theta_end = (tile_index + 1) * angle_step

    # Apply kerf compensation by shrinking the tile
    if kerf_mm > 0:
        # Convert kerf to angular offset at each radius
        inner_kerf_angle = kerf_mm / inner_radius_mm / 2
        outer_kerf_angle = kerf_mm / outer_radius_mm / 2
        inner_r = inner_radius_mm + kerf_mm / 2
        outer_r = outer_radius_mm - kerf_mm / 2
        theta_start_inner = theta_start + inner_kerf_angle
        theta_end_inner = theta_end - inner_kerf_angle
        theta_start_outer = theta_start + outer_kerf_angle
        theta_end_outer = theta_end - outer_kerf_angle
    else:
        inner_r = inner_radius_mm
        outer_r = outer_radius_mm
        theta_start_inner = theta_start
        theta_end_inner = theta_end
        theta_start_outer = theta_start
        theta_end_outer = theta_end

    # Calculate corner points
    inner_start = Point2D(
        inner_r * math.cos(theta_start_inner),
        inner_r * math.sin(theta_start_inner)
    )
    inner_end = Point2D(
        inner_r * math.cos(theta_end_inner),
        inner_r * math.sin(theta_end_inner)
    )
    outer_start = Point2D(
        outer_r * math.cos(theta_start_outer),
        outer_r * math.sin(theta_start_outer)
    )
    outer_end = Point2D(
        outer_r * math.cos(theta_end_outer),
        outer_r * math.sin(theta_end_outer)
    )

    return TileGeometry(
        tile_index=tile_index,
        theta_start_rad=theta_start,
        theta_end_rad=theta_end,
        inner_start=inner_start,
        inner_end=inner_end,
        outer_start=outer_start,
        outer_end=outer_end,
        color_index=tile_index % 2,  # Alternating for checkerboard
    )


def compute_ring_segmentation(
    ring_id: int,
    inner_radius_mm: float,
    outer_radius_mm: float,
    tile_width_mm: float = 5.0,
    pattern: TilePattern = TilePattern.CHECKERBOARD,
    kerf_mm: float = 0.0,
    min_tiles: int = 4,
    force_even: bool = True,
) -> RingSegmentation:
    """
    Compute complete tile segmentation for a ring.

    Args:
        ring_id: Ring identifier
        inner_radius_mm: Inner radius in mm
        outer_radius_mm: Outer radius in mm
        tile_width_mm: Target arc length per tile
        pattern: Tile pattern type
        kerf_mm: Saw kerf compensation
        min_tiles: Minimum number of tiles
        force_even: Force even tile count (for alternating patterns)

    Returns:
        RingSegmentation with all tiles
    """
    # Calculate tile count
    tile_count = compute_tile_count(
        inner_radius_mm, outer_radius_mm, tile_width_mm, min_tiles
    )

    # Force even for checkerboard/herringbone
    if force_even and pattern in (TilePattern.CHECKERBOARD, TilePattern.HERRINGBONE):
        if tile_count % 2 != 0:
            tile_count += 1

    # Generate all tiles
    tiles = []
    for i in range(tile_count):
        tile = compute_tile_geometry(
            inner_radius_mm=inner_radius_mm,
            outer_radius_mm=outer_radius_mm,
            tile_index=i,
            tile_count=tile_count,
            kerf_mm=kerf_mm,
        )
        tiles.append(tile)

    return RingSegmentation(
        ring_id=ring_id,
        inner_radius_mm=inner_radius_mm,
        outer_radius_mm=outer_radius_mm,
        tile_count=tile_count,
        tile_width_mm=tile_width_mm,
        pattern=pattern,
        tiles=tiles,
        kerf_mm=kerf_mm,
    )


def compute_tile_segmentation(ring: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main entry point - compute tile segmentation from ring config dict.

    This is the facade function that replaces the old stub.

    Args:
        ring: Dictionary with keys:
            - ring_id: int
            - radius_mm: float (average radius, used to compute inner/outer)
            - width_mm: float (ring width)
            - tile_length_mm: float (target tile arc length)
            - pattern: str (optional, default "checkerboard")
            - kerf_mm: float (optional, default 0)

    Returns:
        Segmentation result dictionary
    """
    ring_id = ring.get("ring_id", 0)
    radius_mm = ring.get("radius_mm", 50.0)
    width_mm = ring.get("width_mm", 5.0)
    tile_length_mm = ring.get("tile_length_mm", 5.0)
    pattern_str = ring.get("pattern", "checkerboard")
    kerf_mm = ring.get("kerf_mm", 0.0)

    # Convert average radius + width to inner/outer
    inner_radius_mm = radius_mm - width_mm / 2
    outer_radius_mm = radius_mm + width_mm / 2

    # Parse pattern
    try:
        pattern = TilePattern(pattern_str.lower())
    except ValueError:
        pattern = TilePattern.CHECKERBOARD

    # Compute segmentation
    segmentation = compute_ring_segmentation(
        ring_id=ring_id,
        inner_radius_mm=inner_radius_mm,
        outer_radius_mm=outer_radius_mm,
        tile_width_mm=tile_length_mm,
        pattern=pattern,
        kerf_mm=kerf_mm,
    )

    return segmentation.to_dict()


# Legacy alias for backward compatibility
compute_tile_segmentation_stub = compute_tile_segmentation


if __name__ == "__main__":
    # Test the implementation
    test_ring = {
        "ring_id": 1,
        "radius_mm": 50.0,
        "width_mm": 5.0,
        "tile_length_mm": 5.0,
        "pattern": "checkerboard",
        "kerf_mm": 0.2,
    }

    result = compute_tile_segmentation(test_ring)
    print(f"Ring ID: {result['ring_id']}")
    print(f"Tile count: {result['tile_count']}")
    print(f"Circumference: {result['circumference_mm']:.2f} mm")
    print(f"First tile: {result['tiles'][0]}")
