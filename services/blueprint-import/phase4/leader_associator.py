"""
Leader Line Association for Blueprint Dimensions
=================================================

Links detected arrows and leader lines to dimension text and geometry.

Author: Luthier's Toolbox
Version: 4.0.0-alpha
"""

import logging
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any, Callable
import numpy as np

from .arrow_detector import Arrow

logger = logging.getLogger(__name__)


@dataclass
class TextRegion:
    """OCR-detected text region with position."""
    text: str
    bbox: Tuple[int, int, int, int]  # x, y, w, h
    confidence: float
    center: Tuple[float, float] = field(default=(0.0, 0.0))
    parsed_value: Optional[float] = None
    unit: str = "unknown"

    def __post_init__(self):
        if self.center == (0.0, 0.0):
            x, y, w, h = self.bbox
            self.center = (x + w / 2, y + h / 2)


@dataclass
class WitnessLineGroup:
    """Group of witness/extension lines for a dimension."""
    lines: List[np.ndarray]  # List of line contours
    dimension_line: Optional[np.ndarray] = None
    endpoints: List[Tuple[float, float]] = field(default_factory=list)
    span_mm: float = 0.0


@dataclass
class AssociatedDimension:
    """A dimension text associated with geometry."""
    text_region: TextRegion
    target_feature: Any  # ContourInfo reference
    arrow: Optional[Arrow] = None
    witness_group: Optional[WitnessLineGroup] = None
    association_confidence: float = 0.0
    association_method: str = "proximity"  # proximity, leader, witness

    @property
    def value_mm(self) -> Optional[float]:
        return self.text_region.parsed_value

    def to_dict(self) -> Dict[str, Any]:
        return {
            'text': self.text_region.text,
            'value_mm': self.value_mm,
            'unit': self.text_region.unit,
            'target_category': self.target_feature.category.value if hasattr(self.target_feature, 'category') else 'unknown',
            'confidence': self.association_confidence,
            'method': self.association_method,
            'has_arrow': self.arrow is not None,
            'has_witness': self.witness_group is not None
        }


class LeaderLineAssociator:
    """
    Links arrows to dimension text and geometry.

    The core intelligence of Phase 4.0.

    Association Strategy:
        1. Find arrows pointing toward text regions
        2. Trace leader lines from arrow tails to geometry
        3. Match dimension values to measured geometry
        4. Group witness lines into dimension entities
    """

    # Scoring weights for multi-factor ranking
    WEIGHT_PROXIMITY = 50
    WEIGHT_PLAUSIBILITY = 30
    WEIGHT_TYPE_MATCH = 20

    def __init__(
        self,
        search_radius_calculator: Optional[Callable] = None,
        mm_per_px: float = 0.0635  # Default 400 DPI
    ):
        """
        Initialize leader line associator.

        Args:
            search_radius_calculator: Function to calculate adaptive search radius
            mm_per_px: Millimeters per pixel for measurements
        """
        self.calc_radius = search_radius_calculator or self._default_radius
        self.mm_per_px = mm_per_px

    def associate(
        self,
        arrows: List[Arrow],
        text_regions: List[TextRegion],
        geometry: Dict[str, List[Any]],  # category -> ContourInfo list
        blueprint_width_mm: float = 500.0
    ) -> List[AssociatedDimension]:
        """
        Associate dimension text with geometry features.

        Args:
            arrows: Detected arrows from ArrowDetector
            text_regions: OCR text regions with dimension values
            geometry: Categorized contours from Phase 3.6
            blueprint_width_mm: Blueprint width for adaptive radius

        Returns:
            List of associated dimensions with target features
        """
        associations = []

        # Calculate adaptive search radius
        avg_text_size = self._average_text_size(text_regions)
        search_radius = self.calc_radius(blueprint_width_mm, avg_text_size)

        logger.info(f"Associating {len(text_regions)} text regions with "
                   f"{len(arrows)} arrows (radius: {search_radius:.1f}mm)")

        # Strategy 1: Arrow-based association
        for arrow in arrows:
            # Find text region near arrow tip
            text = self._find_text_near_point(
                arrow.tip_point,
                text_regions,
                max_distance=search_radius / self.mm_per_px
            )

            if text is None:
                continue

            # Find geometry near arrow tail (where it points to)
            candidates = self._find_geometry_near_point(
                arrow.tail_point,
                geometry,
                max_distance=search_radius / self.mm_per_px * 2
            )

            if not candidates:
                continue

            # Rank candidates
            ranked = self._rank_candidates(text, candidates)

            if ranked:
                best_feature, score = ranked[0]
                associations.append(AssociatedDimension(
                    text_region=text,
                    target_feature=best_feature,
                    arrow=arrow,
                    association_confidence=score / 100.0,
                    association_method="leader"
                ))

        # Strategy 2: Proximity-based for unmatched text
        matched_texts = {a.text_region.text for a in associations}

        for text in text_regions:
            if text.text in matched_texts:
                continue

            # Direct proximity match
            candidates = self._find_geometry_near_point(
                text.center,
                geometry,
                max_distance=search_radius / self.mm_per_px * 1.5
            )

            if candidates:
                ranked = self._rank_candidates(text, candidates)
                if ranked and ranked[0][1] > 30:  # Minimum score
                    best_feature, score = ranked[0]
                    associations.append(AssociatedDimension(
                        text_region=text,
                        target_feature=best_feature,
                        association_confidence=score / 100.0 * 0.8,  # Lower confidence
                        association_method="proximity"
                    ))

        logger.info(f"Created {len(associations)} dimension associations "
                   f"(leader: {sum(1 for a in associations if a.arrow)}, "
                   f"proximity: {sum(1 for a in associations if not a.arrow)})")

        return associations

    def _find_text_near_point(
        self,
        point: Tuple[float, float],
        text_regions: List[TextRegion],
        max_distance: float
    ) -> Optional[TextRegion]:
        """Find closest text region to a point."""
        best = None
        best_dist = float('inf')

        for text in text_regions:
            dist = np.sqrt(
                (text.center[0] - point[0])**2 +
                (text.center[1] - point[1])**2
            )
            if dist < max_distance and dist < best_dist:
                best = text
                best_dist = dist

        return best

    def _find_geometry_near_point(
        self,
        point: Tuple[float, float],
        geometry: Dict[str, List[Any]],
        max_distance: float
    ) -> List[Tuple[Any, float]]:
        """Find geometry features near a point with distances."""
        candidates = []

        for category, features in geometry.items():
            # Skip text and page borders
            if category in ('text', 'page_border', 'small_feature'):
                continue

            for feature in features:
                # Get feature center
                if hasattr(feature, 'bbox'):
                    x, y, w, h = feature.bbox
                    fx, fy = x + w / 2, y + h / 2
                elif hasattr(feature, 'contour'):
                    M = self._contour_centroid(feature.contour)
                    fx, fy = M
                else:
                    continue

                dist = np.sqrt((fx - point[0])**2 + (fy - point[1])**2)

                if dist < max_distance:
                    candidates.append((feature, dist))

        return candidates

    def _rank_candidates(
        self,
        text: TextRegion,
        candidates: List[Tuple[Any, float]]
    ) -> List[Tuple[Any, float]]:
        """
        Rank geometry candidates for a dimension text.

        Scoring factors:
        1. Proximity to leader line endpoint (0-50 points)
        2. Dimensional plausibility (0-30 points)
        3. Feature type appropriateness (0-20 points)
        """
        scored = []

        for feature, distance in candidates:
            score = 0

            # Factor 1: Proximity (closer = better)
            if distance < 10:
                score += self.WEIGHT_PROXIMITY
            elif distance < 50:
                score += self.WEIGHT_PROXIMITY * 0.6
            elif distance < 100:
                score += self.WEIGHT_PROXIMITY * 0.2

            # Factor 2: Dimensional plausibility
            if text.parsed_value is not None:
                measured = self._measure_feature(feature)
                if measured is not None:
                    diff_ratio = abs(measured - text.parsed_value) / (text.parsed_value + 0.001)
                    if diff_ratio < 0.02:  # Within 2%
                        score += self.WEIGHT_PLAUSIBILITY
                    elif diff_ratio < 0.05:  # Within 5%
                        score += self.WEIGHT_PLAUSIBILITY * 0.7
                    elif diff_ratio < 0.10:  # Within 10%
                        score += self.WEIGHT_PLAUSIBILITY * 0.3

            # Factor 3: Feature type appropriateness
            category = getattr(feature, 'category', None)
            if category:
                appropriate = self._is_appropriate_feature(text.text, category)
                if appropriate:
                    score += self.WEIGHT_TYPE_MATCH

            scored.append((feature, score))

        return sorted(scored, key=lambda x: -x[1])

    def _measure_feature(self, feature: Any) -> Optional[float]:
        """Measure a feature's primary dimension in mm."""
        if hasattr(feature, 'width_mm') and hasattr(feature, 'height_mm'):
            # Return the larger dimension
            return max(feature.width_mm, feature.height_mm)
        elif hasattr(feature, 'contour'):
            # Measure from contour
            rect = self._cv2_import().minAreaRect(feature.contour)
            w, h = rect[1]
            return max(w, h) * self.mm_per_px
        return None

    def _is_appropriate_feature(self, text: str, category: Any) -> bool:
        """Check if feature type matches dimension text context."""
        text_lower = text.lower()
        category_value = category.value if hasattr(category, 'value') else str(category)

        # Build mapping of text keywords to appropriate categories
        CATEGORY_KEYWORDS = {
            'body_outline': ['body', 'length', 'width', 'overall'],
            'neck_pocket': ['pocket', 'neck', 'joint'],
            'pickup_route': ['pickup', 'route', 'humbucker', 'single'],
            'control_cavity': ['cavity', 'control', 'electronics'],
            'soundhole': ['soundhole', 'sound hole', 'diameter'],
            'bridge_route': ['bridge', 'saddle'],
        }

        keywords = CATEGORY_KEYWORDS.get(category_value, [])
        return any(kw in text_lower for kw in keywords)

    def _contour_centroid(self, contour: np.ndarray) -> Tuple[float, float]:
        """Calculate contour centroid."""
        M = self._cv2_import().moments(contour)
        if M['m00'] == 0:
            return (0.0, 0.0)
        cx = M['m10'] / M['m00']
        cy = M['m01'] / M['m00']
        return (cx, cy)

    def _average_text_size(self, text_regions: List[TextRegion]) -> float:
        """Calculate average text height in mm."""
        if not text_regions:
            return 2.5  # Default

        heights = [tr.bbox[3] * self.mm_per_px for tr in text_regions]
        return np.mean(heights)

    def _default_radius(
        self,
        blueprint_width_mm: float,
        text_size_mm: float
    ) -> float:
        """
        Default adaptive search radius calculator.

        Args:
            blueprint_width_mm: Total blueprint width in mm
            text_size_mm: Height of dimension text in mm

        Returns:
            Search radius in mm
        """
        # Base radius: 10% of blueprint width
        base_radius = blueprint_width_mm * 0.1

        # Scale by text size (larger text = longer leaders typically)
        text_scale = max(1.0, text_size_mm / 2.5)

        # Cap at reasonable maximum
        return min(base_radius * text_scale, 200.0)

    def _cv2_import(self):
        """Lazy import cv2."""
        try:
            import cv2
            return cv2
        except ImportError:
            raise ImportError("OpenCV required for leader line association")


class WitnessLineDetector:
    """
    Detect and group witness/extension lines.

    Witness lines are the perpendicular lines that extend from
    the measured feature to the dimension line.
    """

    def __init__(self, mm_per_px: float = 0.0635):
        self.mm_per_px = mm_per_px

    def detect_witness_groups(
        self,
        contours: List[np.ndarray],
        arrows: List[Arrow]
    ) -> List[WitnessLineGroup]:
        """
        Detect and group witness lines into dimension entities.

        Args:
            contours: All detected contours
            arrows: Detected arrows (dimension line endpoints)

        Returns:
            List of witness line groups
        """
        groups = []

        # Find thin, straight lines (potential witness lines)
        witness_candidates = self._find_witness_candidates(contours)

        # Group witness lines by proximity and parallelism
        for arrow in arrows:
            nearby_witnesses = self._find_witnesses_near_arrow(
                arrow, witness_candidates
            )

            if len(nearby_witnesses) >= 2:
                group = WitnessLineGroup(
                    lines=nearby_witnesses,
                    endpoints=self._extract_endpoints(nearby_witnesses),
                    span_mm=self._calculate_span(nearby_witnesses)
                )
                groups.append(group)

        return groups

    def _find_witness_candidates(
        self,
        contours: List[np.ndarray]
    ) -> List[np.ndarray]:
        """Find contours that could be witness lines."""
        candidates = []

        for contour in contours:
            if self._is_thin_straight_line(contour):
                candidates.append(contour)

        return candidates

    def _is_thin_straight_line(self, contour: np.ndarray) -> bool:
        """Check if contour is a thin, straight line."""
        if len(contour) < 2:
            return False

        # Check aspect ratio (should be very elongated)
        rect = self._cv2_import().minAreaRect(contour)
        w, h = rect[1]
        if min(w, h) == 0:
            return False

        aspect = max(w, h) / min(w, h)
        if aspect < 5:  # Should be at least 5:1
            return False

        # Check straightness using polygon approximation
        epsilon = 0.02 * self._cv2_import().arcLength(contour, True)
        approx = self._cv2_import().approxPolyDP(contour, epsilon, True)

        # A straight line should approximate to 2 points
        return len(approx) <= 3

    def _find_witnesses_near_arrow(
        self,
        arrow: Arrow,
        candidates: List[np.ndarray]
    ) -> List[np.ndarray]:
        """Find witness line candidates near an arrow."""
        nearby = []
        search_radius = 50  # pixels

        for contour in candidates:
            # Check if contour is near arrow's perpendicular direction
            centroid = contour.mean(axis=0)[0]

            # Distance from arrow line
            dist = self._point_line_distance(
                centroid,
                arrow.tail_point,
                arrow.tip_point
            )

            if dist < search_radius:
                nearby.append(contour)

        return nearby

    def _point_line_distance(
        self,
        point: np.ndarray,
        line_start: Tuple[float, float],
        line_end: Tuple[float, float]
    ) -> float:
        """Calculate perpendicular distance from point to line."""
        p = np.array(point)
        a = np.array(line_start)
        b = np.array(line_end)

        # Line vector
        ab = b - a
        ap = p - a

        # Project point onto line
        t = np.dot(ap, ab) / (np.dot(ab, ab) + 1e-8)
        t = np.clip(t, 0, 1)

        # Closest point on line
        closest = a + t * ab

        return np.linalg.norm(p - closest)

    def _extract_endpoints(
        self,
        witnesses: List[np.ndarray]
    ) -> List[Tuple[float, float]]:
        """Extract endpoints from witness lines."""
        endpoints = []

        for contour in witnesses:
            pts = contour.reshape(-1, 2)
            endpoints.append(tuple(pts[0]))
            endpoints.append(tuple(pts[-1]))

        return endpoints

    def _calculate_span(self, witnesses: List[np.ndarray]) -> float:
        """Calculate span between witness lines in mm."""
        if len(witnesses) < 2:
            return 0.0

        # Find centroids
        centroids = []
        for contour in witnesses:
            M = self._cv2_import().moments(contour)
            if M['m00'] > 0:
                cx = M['m10'] / M['m00']
                cy = M['m01'] / M['m00']
                centroids.append((cx, cy))

        if len(centroids) < 2:
            return 0.0

        # Maximum distance between centroids
        max_dist = 0
        for i, c1 in enumerate(centroids):
            for c2 in centroids[i+1:]:
                dist = np.sqrt((c1[0] - c2[0])**2 + (c1[1] - c2[1])**2)
                max_dist = max(max_dist, dist)

        return max_dist * self.mm_per_px

    def _cv2_import(self):
        """Lazy import cv2."""
        try:
            import cv2
            return cv2
        except ImportError:
            raise ImportError("OpenCV required for witness line detection")
