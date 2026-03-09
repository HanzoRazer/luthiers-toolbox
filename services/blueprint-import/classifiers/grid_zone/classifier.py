"""
Grid Zone Classifier
====================

Classifies contours based on their position within the STEM Guitar grid system.

This classifier provides:
1. Zone-based contour classification (neck pocket, bridge, wing limits, etc.)
2. Symmetry analysis relative to centerline
3. Proportion validation against expected ratios
4. ML feature extraction for downstream classifiers

Usage:
    from classifiers.grid_zone import GridZoneClassifier, ELECTRIC_GUITAR_GRID

    classifier = GridZoneClassifier(ELECTRIC_GUITAR_GRID)

    # Classify a contour by its bounding box
    result = classifier.classify_bbox(x_min, y_min, x_max, y_max)
    print(f"Category: {result.primary_category}")
    print(f"Symmetry: {result.symmetry_score:.2f}")

    # Or classify by centroid
    result = classifier.classify_point(0.5, 0.3)

Author: The Production Shop
Version: 4.0.0
"""

import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

from .zones import (
    GridZone,
    GridZoneType,
    GridDefinition,
    ELECTRIC_GUITAR_GRID
)

logger = logging.getLogger(__name__)


@dataclass
class ZoneMatch:
    """A single zone match with overlap score."""
    zone: GridZone
    overlap: float  # 0-1 overlap percentage
    is_primary: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "zone_type": self.zone.zone_type.value,
            "contour_category": self.zone.contour_category,
            "overlap": round(self.overlap, 3),
            "is_primary": self.is_primary,
            "color": self.zone.color_name
        }


@dataclass
class ZoneClassificationResult:
    """
    Complete classification result for a contour.

    Attributes:
        primary_category: The main contour category (from highest-overlap zone)
        primary_zone: The GridZone with highest overlap
        all_zones: All overlapping zones with their scores
        symmetry_score: How centered the contour is (0-1)
        wing_extend_left: How far contour extends into left wing zone
        wing_extend_right: How far contour extends into right wing zone
        proportion_valid: Whether proportions pass validation
        ml_features: Extracted features for ML classifiers
        notes: Human-readable classification notes
    """
    primary_category: str
    primary_zone: Optional[GridZone]
    all_zones: List[ZoneMatch]
    symmetry_score: float
    wing_extend_left: float
    wing_extend_right: float
    proportion_valid: bool
    ml_features: Dict[str, float]
    notes: List[str] = field(default_factory=list)

    @property
    def is_confident(self) -> bool:
        """Check if classification is confident (primary zone overlap > 0.5)."""
        return (self.primary_zone is not None and
                len(self.all_zones) > 0 and
                self.all_zones[0].overlap > 0.5)

    @property
    def needs_review(self) -> bool:
        """Check if classification needs human review."""
        if self.primary_zone is None:
            return True
        if len(self.all_zones) > 1:
            # Close second place
            if self.all_zones[1].overlap > self.all_zones[0].overlap * 0.8:
                return True
        if not self.proportion_valid:
            return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "primary_category": self.primary_category,
            "primary_zone": self.primary_zone.zone_type.value if self.primary_zone else None,
            "all_zones": [z.to_dict() for z in self.all_zones],
            "symmetry_score": round(self.symmetry_score, 3),
            "wing_extend": {
                "left": round(self.wing_extend_left, 3),
                "right": round(self.wing_extend_right, 3)
            },
            "proportion_valid": self.proportion_valid,
            "ml_features": {k: round(v, 4) for k, v in self.ml_features.items()},
            "is_confident": self.is_confident,
            "needs_review": self.needs_review,
            "notes": self.notes
        }


class GridZoneClassifier:
    """
    Classifies contours based on their position in the grid zone system.

    The classifier maps contour bounding boxes to semantic zones, enabling:
    - Automatic contour category assignment
    - Body proportion validation
    - Symmetry analysis
    - ML feature extraction for training

    Usage:
        classifier = GridZoneClassifier()  # Uses default electric guitar grid

        # From pixel bbox (provide image dimensions for normalization)
        result = classifier.classify_contour(
            contour,
            image_width=1200,
            image_height=1600
        )

        # From normalized bbox (0-1 range)
        result = classifier.classify_bbox(0.2, 0.1, 0.8, 0.9)
    """

    def __init__(
        self,
        grid: Optional[GridDefinition] = None,
        min_overlap_threshold: float = 0.1,
        body_bbox: Optional[Tuple[float, float, float, float]] = None
    ):
        """
        Initialize the classifier.

        Args:
            grid: Grid definition to use (default: ELECTRIC_GUITAR_GRID)
            min_overlap_threshold: Minimum overlap to consider a zone match
            body_bbox: Optional body bounding box for relative positioning
        """
        self.grid = grid or ELECTRIC_GUITAR_GRID
        self.min_overlap = min_overlap_threshold
        self.body_bbox = body_bbox  # For normalizing to body, not image

        logger.info(
            f"Initialized GridZoneClassifier with '{self.grid.name}' "
            f"({len(self.grid.zones)} zones)"
        )

    def classify_point(
        self,
        x: float,
        y: float
    ) -> ZoneClassificationResult:
        """
        Classify a single point (e.g., contour centroid).

        Args:
            x: Normalized x coordinate (0-1)
            y: Normalized y coordinate (0-1)

        Returns:
            ZoneClassificationResult
        """
        # Treat point as tiny bbox
        epsilon = 0.001
        return self.classify_bbox(
            x - epsilon, y - epsilon,
            x + epsilon, y + epsilon
        )

    def classify_bbox(
        self,
        x_min: float,
        y_min: float,
        x_max: float,
        y_max: float
    ) -> ZoneClassificationResult:
        """
        Classify a bounding box by its zone overlaps.

        Args:
            x_min, y_min, x_max, y_max: Normalized bbox coordinates (0-1)

        Returns:
            ZoneClassificationResult with all zone matches
        """
        # Get all overlapping zones
        zone_overlaps = self.grid.get_zones_for_bbox(
            x_min, y_min, x_max, y_max,
            min_overlap=self.min_overlap
        )

        # Build zone matches
        all_zones = []
        for i, (zone, overlap) in enumerate(zone_overlaps):
            all_zones.append(ZoneMatch(
                zone=zone,
                overlap=overlap,
                is_primary=(i == 0)
            ))

        # Determine primary category
        if all_zones:
            primary_zone = all_zones[0].zone
            primary_category = primary_zone.contour_category
        else:
            primary_zone = None
            primary_category = "UNKNOWN"

        # Calculate symmetry
        symmetry_score = self.grid.calculate_symmetry_score(
            (x_min, y_min, x_max, y_max)
        )

        # Calculate wing extensions
        wing_extend_left = self._calculate_wing_extend(
            x_min, y_min, x_max, y_max, side="left"
        )
        wing_extend_right = self._calculate_wing_extend(
            x_min, y_min, x_max, y_max, side="right"
        )

        # Validate proportions
        width = x_max - x_min
        height = y_max - y_min
        grid_cols, grid_rows = self.grid.grid_dimensions
        width_cells = int(width * grid_cols)
        height_cells = int(height * grid_rows)
        proportion_result = self.grid.validate_body_proportions(
            width_cells, height_cells
        )

        # Extract ML features
        ml_features = self._extract_ml_features(
            x_min, y_min, x_max, y_max,
            all_zones, symmetry_score,
            wing_extend_left, wing_extend_right
        )

        # Build notes
        notes = []
        if primary_zone:
            notes.append(f"Primary zone: {primary_zone.zone_type.value}")
        if len(all_zones) > 1:
            notes.append(f"Spans {len(all_zones)} zones")
        if symmetry_score > 0.9:
            notes.append("Well-centered on axis")
        elif symmetry_score < 0.5:
            notes.append("Offset from centerline")
        for warning in proportion_result.get("warnings", []):
            notes.append(f"Proportion: {warning}")

        return ZoneClassificationResult(
            primary_category=primary_category,
            primary_zone=primary_zone,
            all_zones=all_zones,
            symmetry_score=symmetry_score,
            wing_extend_left=wing_extend_left,
            wing_extend_right=wing_extend_right,
            proportion_valid=proportion_result["valid"],
            ml_features=ml_features,
            notes=notes
        )

    def classify_contour(
        self,
        contour: np.ndarray,
        image_width: int,
        image_height: int,
        body_bbox: Optional[Tuple[int, int, int, int]] = None
    ) -> ZoneClassificationResult:
        """
        Classify an OpenCV contour by normalizing its bbox.

        Args:
            contour: OpenCV contour array
            image_width: Image width in pixels
            image_height: Image height in pixels
            body_bbox: Optional (x, y, w, h) of body for relative positioning

        Returns:
            ZoneClassificationResult
        """
        # Get contour bbox
        x, y, w, h = cv2.boundingRect(contour) if hasattr(contour, 'shape') else contour

        # Normalize to image or body coordinates
        if body_bbox:
            bx, by, bw, bh = body_bbox
            x_min = (x - bx) / bw if bw > 0 else 0
            y_min = (y - by) / bh if bh > 0 else 0
            x_max = (x + w - bx) / bw if bw > 0 else 1
            y_max = (y + h - by) / bh if bh > 0 else 1
        else:
            x_min = x / image_width
            y_min = y / image_height
            x_max = (x + w) / image_width
            y_max = (y + h) / image_height

        # Clamp to valid range
        x_min = max(0, min(1, x_min))
        y_min = max(0, min(1, y_min))
        x_max = max(0, min(1, x_max))
        y_max = max(0, min(1, y_max))

        return self.classify_bbox(x_min, y_min, x_max, y_max)

    def _calculate_wing_extend(
        self,
        x_min: float,
        y_min: float,
        x_max: float,
        y_max: float,
        side: str
    ) -> float:
        """Calculate how far a bbox extends into a wing zone."""
        # Determine target zone type
        target_type = (
            GridZoneType.WING_LIMIT_LEFT if side == "left"
            else GridZoneType.WING_LIMIT_RIGHT
        )

        # Find wing zone for this side
        wing_zones = [
            z for z in self.grid.zones
            if z.zone_type == target_type
        ]

        if not wing_zones:
            return 0.0

        wing = wing_zones[0]
        overlap = wing.contains_bbox(x_min, y_min, x_max, y_max)
        return overlap

    def _extract_ml_features(
        self,
        x_min: float,
        y_min: float,
        x_max: float,
        y_max: float,
        zone_matches: List[ZoneMatch],
        symmetry_score: float,
        wing_left: float,
        wing_right: float
    ) -> Dict[str, float]:
        """
        Extract ML features for downstream classifiers.

        Returns dict with features suitable for RandomForest or neural network.
        """
        # Zone overlap features
        zone_features = {}
        for zone_type in GridZoneType:
            key = f"zone_{zone_type.value}_overlap"
            matches = [m for m in zone_matches if m.zone.zone_type == zone_type]
            zone_features[key] = matches[0].overlap if matches else 0.0

        # Position features
        center_x = (x_min + x_max) / 2
        center_y = (y_min + y_max) / 2
        width = x_max - x_min
        height = y_max - y_min

        position_features = {
            "center_x_norm": center_x,
            "center_y_norm": center_y,
            "width_norm": width,
            "height_norm": height,
            "aspect_ratio": width / height if height > 0 else 1.0,
            "area_norm": width * height,
        }

        # Symmetry features
        symmetry_features = {
            "symmetry_score": symmetry_score,
            "offset_from_center": abs(center_x - 0.5),
            "wing_extend_left": wing_left,
            "wing_extend_right": wing_right,
            "wing_balance": abs(wing_left - wing_right),
        }

        # Zone count features
        zone_count_features = {
            "zone_count": len(zone_matches),
            "primary_zone_confidence": zone_matches[0].overlap if zone_matches else 0.0,
            "zone_ambiguity": (
                zone_matches[1].overlap / zone_matches[0].overlap
                if len(zone_matches) > 1 and zone_matches[0].overlap > 0
                else 0.0
            ),
        }

        # Combine all features
        return {
            **zone_features,
            **position_features,
            **symmetry_features,
            **zone_count_features
        }

    def get_zone_by_type(self, zone_type: GridZoneType) -> Optional[GridZone]:
        """Get a specific zone by type."""
        for zone in self.grid.zones:
            if zone.zone_type == zone_type:
                return zone
        return None

    def visualize_zones(self, width: int = 800, height: int = 1000) -> np.ndarray:
        """
        Create a visualization of the grid zones.

        Args:
            width: Image width in pixels
            height: Image height in pixels

        Returns:
            BGR image with colored zones
        """
        # Create white canvas
        img = np.ones((height, width, 3), dtype=np.uint8) * 255

        # Draw each zone
        for zone in sorted(self.grid.zones, key=lambda z: z.priority):
            x1 = int(zone.x_min * width)
            y1 = int(zone.y_min * height)
            x2 = int(zone.x_max * width)
            y2 = int(zone.y_max * height)

            # Convert RGB to BGR for OpenCV
            color = (zone.color_rgb[2], zone.color_rgb[1], zone.color_rgb[0])

            # Draw filled rectangle with transparency
            overlay = img.copy()
            cv2.rectangle(overlay, (x1, y1), (x2, y2), color, -1)
            cv2.addWeighted(overlay, 0.5, img, 0.5, 0, img)

            # Draw border
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 0), 1)

        # Draw centerline
        center_x = int(self.grid.centerline_x * width)
        cv2.line(img, (center_x, 0), (center_x, height), (0, 0, 0), 2)

        return img

    def classify_contours_batch(
        self,
        contours: List[np.ndarray],
        image_width: int,
        image_height: int,
        body_bbox: Optional[Tuple[int, int, int, int]] = None
    ) -> List[ZoneClassificationResult]:
        """
        Classify multiple contours in batch.

        Args:
            contours: List of OpenCV contours
            image_width: Image width
            image_height: Image height
            body_bbox: Optional body bbox for relative positioning

        Returns:
            List of ZoneClassificationResult
        """
        results = []
        for contour in contours:
            result = self.classify_contour(
                contour, image_width, image_height, body_bbox
            )
            results.append(result)
        return results


# Import cv2 for contour operations (optional)
try:
    import cv2
except ImportError:
    cv2 = None
    logger.warning("OpenCV not available - contour classification disabled")
