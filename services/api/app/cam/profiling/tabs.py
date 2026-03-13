"""
Tab Generation for Perimeter Profiling

Tabs hold the workpiece to the stock during perimeter routing.
Without tabs, the part would fly off when the perimeter cut completes.

Tab placement strategy:
- Evenly distributed around perimeter
- Avoid corners (stress concentrators)
- Configurable width and height
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Tuple

Pt = Tuple[float, float]


@dataclass
class Tab:
    """A holding tab along the perimeter."""

    # Tab center point on the toolpath
    center_x: float
    center_y: float

    # Tab dimensions
    width_mm: float
    height_mm: float  # How much material to leave (Z lift)

    # Position along perimeter (0.0 to 1.0)
    position_ratio: float

    # Index in the point sequence where tab starts/ends
    start_index: int
    end_index: int


@dataclass
class TabConfig:
    """Configuration for tab generation."""

    count: int = 4
    width_mm: float = 10.0
    height_mm: float = 3.0  # Leave 3mm of material

    # Minimum distance from corners (mm)
    corner_clearance_mm: float = 15.0

    # Minimum distance between tabs (mm)
    min_spacing_mm: float = 50.0


class TabGenerator:
    """
    Generates holding tabs along a perimeter toolpath.

    Tabs are placed at even intervals, avoiding sharp corners
    where they would be weak.
    """

    def __init__(self, config: TabConfig = None):
        self.config = config or TabConfig()

    def generate_tabs(
        self,
        points: List[Pt],
        _perimeter_length_mm: float,  # Reserved for future spacing algorithm
    ) -> List[Tab]:
        """
        Generate tabs along the perimeter.

        Args:
            points: Closed polygon points (perimeter toolpath)
            _perimeter_length_mm: Total perimeter length (reserved)

        Returns:
            List of Tab objects with positions and indices
        """
        if self.config.count <= 0:
            return []

        if len(points) < 4:
            return []

        # Find corner indices to avoid
        corner_indices = self._find_corners(points)

        # Calculate cumulative distances along perimeter
        cumulative_dist = self._cumulative_distances(points)
        total_length = cumulative_dist[-1]

        if total_length < self.config.min_spacing_mm * self.config.count:
            # Perimeter too short for requested tabs
            return []

        # Calculate ideal tab positions (evenly spaced)
        tab_spacing = total_length / self.config.count

        tabs = []
        for i in range(self.config.count):
            # Ideal position along perimeter
            target_dist = (i + 0.5) * tab_spacing  # Offset by half spacing

            # Find point index at this distance
            center_idx = self._index_at_distance(cumulative_dist, target_dist)

            # Check if too close to a corner
            if self._is_near_corner(center_idx, corner_indices, points):
                # Shift tab position away from corner
                center_idx = self._shift_from_corner(
                    center_idx, corner_indices, len(points)
                )

            # Calculate tab start/end indices based on width
            half_width = self.config.width_mm / 2.0
            start_idx = self._index_at_distance(
                cumulative_dist,
                max(0, target_dist - half_width)
            )
            end_idx = self._index_at_distance(
                cumulative_dist,
                min(total_length, target_dist + half_width)
            )

            # Get center point coordinates
            cx, cy = points[center_idx % len(points)]

            tabs.append(Tab(
                center_x=cx,
                center_y=cy,
                width_mm=self.config.width_mm,
                height_mm=self.config.height_mm,
                position_ratio=target_dist / total_length,
                start_index=start_idx,
                end_index=end_idx,
            ))

        return tabs

    def _find_corners(self, points: List[Pt], angle_threshold: float = 45.0) -> List[int]:
        """Find indices of sharp corners (angle < threshold)."""
        corners = []
        n = len(points)

        for i in range(n):
            p1 = points[(i - 1) % n]
            p2 = points[i]
            p3 = points[(i + 1) % n]

            # Vectors
            v1 = (p2[0] - p1[0], p2[1] - p1[1])
            v2 = (p3[0] - p2[0], p3[1] - p2[1])

            # Angle between vectors
            angle = self._angle_between(v1, v2)

            if angle < angle_threshold:
                corners.append(i)

        return corners

    def _angle_between(self, v1: Pt, v2: Pt) -> float:
        """Calculate angle between two vectors in degrees."""
        dot = v1[0] * v2[0] + v1[1] * v2[1]
        mag1 = math.hypot(v1[0], v1[1])
        mag2 = math.hypot(v2[0], v2[1])

        if mag1 < 1e-9 or mag2 < 1e-9:
            return 180.0  # Treat degenerate as straight

        cos_angle = max(-1.0, min(1.0, dot / (mag1 * mag2)))
        return math.degrees(math.acos(cos_angle))

    def _cumulative_distances(self, points: List[Pt]) -> List[float]:
        """Calculate cumulative distance along the perimeter."""
        distances = [0.0]

        for i in range(1, len(points)):
            dx = points[i][0] - points[i - 1][0]
            dy = points[i][1] - points[i - 1][1]
            distances.append(distances[-1] + math.hypot(dx, dy))

        # Add closing segment
        dx = points[0][0] - points[-1][0]
        dy = points[0][1] - points[-1][1]
        distances.append(distances[-1] + math.hypot(dx, dy))

        return distances

    def _index_at_distance(self, cumulative: List[float], target: float) -> int:
        """Find point index at given distance along perimeter."""
        for i, d in enumerate(cumulative):
            if d >= target:
                return max(0, i - 1)
        return len(cumulative) - 2

    def _is_near_corner(
        self,
        idx: int,
        corners: List[int],
        points: List[Pt],
    ) -> bool:
        """Check if index is within clearance of any corner."""
        n = len(points)
        clearance_points = int(self.config.corner_clearance_mm / 2.0)  # Approximate

        for corner_idx in corners:
            dist = min(abs(idx - corner_idx), n - abs(idx - corner_idx))
            if dist < clearance_points:
                return True

        return False

    def _shift_from_corner(
        self,
        idx: int,
        corners: List[int],
        n_points: int,
    ) -> int:
        """Shift index away from nearest corner."""
        if not corners:
            return idx

        # Find nearest corner
        nearest = min(corners, key=lambda c: min(abs(idx - c), n_points - abs(idx - c)))

        # Shift away
        clearance = int(self.config.corner_clearance_mm / 2.0)
        if idx > nearest:
            return (idx + clearance) % n_points
        else:
            return (idx - clearance) % n_points
