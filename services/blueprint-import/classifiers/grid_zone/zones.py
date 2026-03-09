"""
Grid Zone Definitions
====================

Defines the STEM Guitar grid zone system for electric guitar body design.

The grid provides semantic regions that enable:
1. Auto-classification of contours by position
2. Proportion validation
3. Symmetry analysis
4. ML feature extraction

Zone coordinate system:
- Origin (0, 0) is top-left of grid
- Coordinates normalized to [0, 1] range
- Y increases downward (top=0, bottom=1)
- X increases rightward (left=0, right=1)

Author: The Production Shop
Version: 4.0.0
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Tuple, List, Optional, Dict, Any
import json
from pathlib import Path


class GridZoneType(Enum):
    """Grid zone type identifiers."""
    NECK_POCKET = "neck_pocket"
    UPPER_BOUT_LEFT = "upper_bout_left"
    UPPER_BOUT_RIGHT = "upper_bout_right"
    WING_LIMIT_LEFT = "wing_limit_left"
    WING_LIMIT_RIGHT = "wing_limit_right"
    BRIDGE_ZONE = "bridge_zone"
    BODY_CANVAS = "body_canvas"
    HEADSTOCK_ZONE = "headstock_zone"
    LOWER_BOUT = "lower_bout"
    WAIST_LEFT = "waist_left"
    WAIST_RIGHT = "waist_right"
    CENTERLINE = "centerline"
    OUT_OF_BOUNDS = "out_of_bounds"


@dataclass
class GridZone:
    """
    A rectangular zone in the grid coordinate system.

    Attributes:
        zone_type: The semantic type of this zone
        x_min: Left boundary (normalized 0-1)
        x_max: Right boundary (normalized 0-1)
        y_min: Top boundary (normalized 0-1)
        y_max: Bottom boundary (normalized 0-1)
        color_name: Human-readable color name
        color_rgb: RGB tuple for visualization
        contour_category: Suggested ContourCategory for contours in this zone
        description: Human-readable description
        priority: Higher priority zones override lower ones for point-in-zone tests
    """
    zone_type: GridZoneType
    x_min: float
    x_max: float
    y_min: float
    y_max: float
    color_name: str
    color_rgb: Tuple[int, int, int]
    contour_category: str  # Maps to ContourCategory enum value
    description: str
    priority: int = 0

    def contains_point(self, x: float, y: float) -> bool:
        """Check if normalized point (x, y) is within this zone."""
        return (self.x_min <= x <= self.x_max and
                self.y_min <= y <= self.y_max)

    def contains_bbox(self, x_min: float, y_min: float,
                      x_max: float, y_max: float) -> float:
        """
        Calculate overlap percentage between bbox and this zone.

        Returns:
            Float 0-1 indicating percentage of bbox inside zone
        """
        # Calculate intersection
        inter_x_min = max(self.x_min, x_min)
        inter_x_max = min(self.x_max, x_max)
        inter_y_min = max(self.y_min, y_min)
        inter_y_max = min(self.y_max, y_max)

        if inter_x_max <= inter_x_min or inter_y_max <= inter_y_min:
            return 0.0

        inter_area = (inter_x_max - inter_x_min) * (inter_y_max - inter_y_min)
        bbox_area = (x_max - x_min) * (y_max - y_min)

        if bbox_area <= 0:
            return 0.0

        return min(inter_area / bbox_area, 1.0)

    @property
    def center(self) -> Tuple[float, float]:
        """Return center point of zone."""
        return ((self.x_min + self.x_max) / 2,
                (self.y_min + self.y_max) / 2)

    @property
    def area(self) -> float:
        """Return area of zone in normalized units."""
        return (self.x_max - self.x_min) * (self.y_max - self.y_min)

    def to_dict(self) -> Dict[str, Any]:
        """Export zone as dictionary."""
        return {
            "zone_type": self.zone_type.value,
            "bounds": {
                "x_min": self.x_min,
                "x_max": self.x_max,
                "y_min": self.y_min,
                "y_max": self.y_max
            },
            "color_name": self.color_name,
            "color_rgb": list(self.color_rgb),
            "contour_category": self.contour_category,
            "description": self.description,
            "priority": self.priority
        }


@dataclass
class GridDefinition:
    """
    Complete grid definition with all zones.

    Attributes:
        name: Grid configuration name
        version: Schema version
        zones: List of GridZone objects
        grid_dimensions: Grid cell counts (columns, rows)
        centerline_x: X coordinate of centerline (normalized)
        proportion_rules: Expected proportions for validation
    """
    name: str
    version: str
    zones: List[GridZone]
    grid_dimensions: Tuple[int, int] = (24, 32)  # columns, rows
    centerline_x: float = 0.5
    proportion_rules: Dict[str, Any] = field(default_factory=dict)

    def get_zone_at_point(self, x: float, y: float) -> Optional[GridZone]:
        """
        Get the highest-priority zone containing the point.

        Args:
            x: Normalized x coordinate (0-1)
            y: Normalized y coordinate (0-1)

        Returns:
            GridZone or None if out of bounds
        """
        matching_zones = [z for z in self.zones if z.contains_point(x, y)]
        if not matching_zones:
            return None
        return max(matching_zones, key=lambda z: z.priority)

    def get_zones_for_bbox(self, x_min: float, y_min: float,
                           x_max: float, y_max: float,
                           min_overlap: float = 0.1) -> List[Tuple[GridZone, float]]:
        """
        Get all zones overlapping with bbox, with overlap percentages.

        Args:
            x_min, y_min, x_max, y_max: Normalized bbox coordinates
            min_overlap: Minimum overlap percentage to include

        Returns:
            List of (GridZone, overlap_percentage) tuples, sorted by overlap desc
        """
        results = []
        for zone in self.zones:
            overlap = zone.contains_bbox(x_min, y_min, x_max, y_max)
            if overlap >= min_overlap:
                results.append((zone, overlap))
        return sorted(results, key=lambda x: -x[1])

    def calculate_symmetry_score(self, contour_bbox: Tuple[float, float, float, float]) -> float:
        """
        Calculate symmetry score relative to centerline.

        Args:
            contour_bbox: (x_min, y_min, x_max, y_max) normalized

        Returns:
            Float 0-1 where 1.0 is perfectly centered
        """
        x_min, y_min, x_max, y_max = contour_bbox
        contour_center_x = (x_min + x_max) / 2

        # Distance from centerline
        offset = abs(contour_center_x - self.centerline_x)

        # Score: 1.0 at center, decreasing linearly
        return max(0.0, 1.0 - offset * 2)

    def validate_body_proportions(self, width_cells: int, height_cells: int) -> Dict[str, Any]:
        """
        Validate body dimensions against expected proportions.

        Args:
            width_cells: Body width in grid cells
            height_cells: Body height in grid cells

        Returns:
            Validation result dict with pass/fail and notes
        """
        rules = self.proportion_rules
        results = {
            "valid": True,
            "checks": [],
            "warnings": []
        }

        # Check max width
        max_width = rules.get("body_width_max_cells", 18)
        if width_cells > max_width:
            results["warnings"].append(
                f"Body width ({width_cells} cells) exceeds max ({max_width})"
            )

        # Check aspect ratio
        if height_cells > 0:
            aspect = width_cells / height_cells
            expected_aspect = rules.get("typical_aspect_ratio", 0.7)
            if abs(aspect - expected_aspect) > 0.2:
                results["warnings"].append(
                    f"Aspect ratio ({aspect:.2f}) differs from typical ({expected_aspect})"
                )

        results["valid"] = len(results["warnings"]) == 0
        return results

    def to_dict(self) -> Dict[str, Any]:
        """Export grid definition as dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "grid_dimensions": list(self.grid_dimensions),
            "centerline_x": self.centerline_x,
            "zones": [z.to_dict() for z in self.zones],
            "proportion_rules": self.proportion_rules
        }

    @classmethod
    def from_json(cls, json_path: Path) -> 'GridDefinition':
        """Load grid definition from JSON file."""
        with open(json_path, 'r') as f:
            data = json.load(f)

        zones = []
        for zone_name, zone_data in data.get("zones", {}).items():
            bounds = zone_data.get("bounds_normalized", {})
            zones.append(GridZone(
                zone_type=GridZoneType(zone_data.get("contour_category", "body_canvas").lower()),
                x_min=bounds.get("x_min", 0),
                x_max=bounds.get("x_max", 1),
                y_min=bounds.get("y_min", 0),
                y_max=bounds.get("y_max", 1),
                color_name=zone_data.get("color", "white"),
                color_rgb=tuple(zone_data.get("rgb", [255, 255, 255])),
                contour_category=zone_data.get("contour_category", "BODY_OUTLINE"),
                description=zone_data.get("description", ""),
                priority=zone_data.get("priority", 0)
            ))

        return cls(
            name=data.get("description", "Custom Grid"),
            version=data.get("schema_version", "1.0.0"),
            zones=zones,
            grid_dimensions=tuple(data.get("grid_dimensions", {}).values())[:2] or (24, 32),
            centerline_x=data.get("centerline", {}).get("x_normalized", 0.5),
            proportion_rules=data.get("proportion_rules", {})
        )


# =============================================================================
# Pre-defined Grid: Electric Guitar Body Grid (STEM Guitar)
# =============================================================================

ELECTRIC_GUITAR_GRID = GridDefinition(
    name="STEM Guitar Electric Body Grid",
    version="1.0.0",
    grid_dimensions=(24, 32),
    centerline_x=0.5,
    zones=[
        # Neck pocket (brown) - highest priority
        GridZone(
            zone_type=GridZoneType.NECK_POCKET,
            x_min=0.417, x_max=0.583,
            y_min=0.0, y_max=0.25,
            color_name="brown",
            color_rgb=(139, 90, 43),
            contour_category="NECK_POCKET",
            description="Neck heel insertion area",
            priority=10
        ),
        # Upper bout left (cream)
        GridZone(
            zone_type=GridZoneType.UPPER_BOUT_LEFT,
            x_min=0.0, x_max=0.417,
            y_min=0.0, y_max=0.188,
            color_name="cream",
            color_rgb=(255, 235, 205),
            contour_category="UPPER_BOUT",
            description="Upper bout wing area (treble side)",
            priority=5
        ),
        # Upper bout right (cream)
        GridZone(
            zone_type=GridZoneType.UPPER_BOUT_RIGHT,
            x_min=0.583, x_max=1.0,
            y_min=0.0, y_max=0.188,
            color_name="cream",
            color_rgb=(255, 235, 205),
            contour_category="UPPER_BOUT",
            description="Upper bout wing area (bass side)",
            priority=5
        ),
        # Wing limit left (blue)
        GridZone(
            zone_type=GridZoneType.WING_LIMIT_LEFT,
            x_min=0.0, x_max=0.125,
            y_min=0.188, y_max=0.813,
            color_name="blue",
            color_rgb=(135, 206, 235),
            contour_category="BODY_WING_LIMIT",
            description="Maximum body width boundary (treble side)",
            priority=3
        ),
        # Wing limit right (blue)
        GridZone(
            zone_type=GridZoneType.WING_LIMIT_RIGHT,
            x_min=0.875, x_max=1.0,
            y_min=0.188, y_max=0.813,
            color_name="blue",
            color_rgb=(135, 206, 235),
            contour_category="BODY_WING_LIMIT",
            description="Maximum body width boundary (bass side)",
            priority=3
        ),
        # Bridge zone (gray)
        GridZone(
            zone_type=GridZoneType.BRIDGE_ZONE,
            x_min=0.375, x_max=0.625,
            y_min=0.688, y_max=0.813,
            color_name="gray",
            color_rgb=(169, 169, 169),
            contour_category="BRIDGE_ROUTE",
            description="Bridge placement and routing area",
            priority=8
        ),
        # Body canvas (white) - lowest priority, catch-all
        GridZone(
            zone_type=GridZoneType.BODY_CANVAS,
            x_min=0.125, x_max=0.875,
            y_min=0.188, y_max=1.0,
            color_name="white",
            color_rgb=(255, 255, 255),
            contour_category="BODY_OUTLINE",
            description="Main body design area",
            priority=1
        ),
        # Waist regions (implicit - for symmetry analysis)
        GridZone(
            zone_type=GridZoneType.WAIST_LEFT,
            x_min=0.125, x_max=0.35,
            y_min=0.35, y_max=0.55,
            color_name="waist",
            color_rgb=(245, 245, 245),
            contour_category="BODY_OUTLINE",
            description="Waist cutaway region (treble side)",
            priority=2
        ),
        GridZone(
            zone_type=GridZoneType.WAIST_RIGHT,
            x_min=0.65, x_max=0.875,
            y_min=0.35, y_max=0.55,
            color_name="waist",
            color_rgb=(245, 245, 245),
            contour_category="BODY_OUTLINE",
            description="Waist cutaway region (bass side)",
            priority=2
        ),
        # Lower bout
        GridZone(
            zone_type=GridZoneType.LOWER_BOUT,
            x_min=0.125, x_max=0.875,
            y_min=0.813, y_max=1.0,
            color_name="white",
            color_rgb=(255, 255, 255),
            contour_category="BODY_OUTLINE",
            description="Lower bout area",
            priority=2
        ),
    ],
    proportion_rules={
        "neck_pocket_width_cells": 4,
        "body_width_max_cells": 18,
        "upper_bout_height_cells": 6,
        "bridge_zone_cells": (6, 4),
        "typical_body_length_cells": 26,
        "typical_aspect_ratio": 0.69,  # width/height
        "symmetry_tolerance": 0.05
    }
)


# =============================================================================
# Helper Functions
# =============================================================================

def load_grid_from_json(json_path: str) -> GridDefinition:
    """
    Load a grid definition from a JSON file.

    Args:
        json_path: Path to grid_zones.json file

    Returns:
        GridDefinition object
    """
    return GridDefinition.from_json(Path(json_path))


def get_default_grid(instrument_type: str = "electric") -> GridDefinition:
    """
    Get the default grid for an instrument type.

    Args:
        instrument_type: "electric", "acoustic", "bass"

    Returns:
        GridDefinition object
    """
    # Currently only electric is defined
    if instrument_type in ("electric", "bass"):
        return ELECTRIC_GUITAR_GRID
    else:
        # For acoustic, use modified proportions (future)
        return ELECTRIC_GUITAR_GRID
