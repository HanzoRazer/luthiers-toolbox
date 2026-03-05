"""
Leader Line Association for Blueprint Dimensions
=================================================

Links detected arrows and leader lines to dimension text and geometry.

Author: Luthier's Toolbox
Version: 4.0.0
"""

import logging
import math
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any, Callable
from enum import Enum
import numpy as np

from .arrow_detector import Arrow

logger = logging.getLogger(__name__)


class AssociationMethod(Enum):
    """How a dimension was associated with geometry."""
    LEADER = "leader"           # Via arrow/leader line
    WITNESS = "witness"         # Via witness/extension lines
    PROXIMITY = "proximity"     # Direct proximity match
    PAIRED_ARROWS = "paired"    # Dimension line with arrows at both ends
    INFERENCE = "inference"     # Inferred from context


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
    WEIGHT_PROXIMITY = 40
    WEIGHT_PLAUSIBILITY = 30
    WEIGHT_TYPE_MATCH = 15
    WEIGHT_DIRECTION = 15  # New: directional alignment

    # Unit conversion factors to mm
    UNIT_TO_MM = {
        'mm': 1.0,
        'cm': 10.0,
        'inch': 25.4,
        'in': 25.4,
        '"': 25.4,
        'ft': 304.8,
    }

    def __init__(
        self,
        search_radius_calculator: Optional[Callable] = None,
        mm_per_px: float = 0.0635,  # Default 400 DPI
        dimension_tolerance: float = 0.05  # 5% tolerance for dimension matching
    ):
        """
        Initialize leader line associator.

        Args:
            search_radius_calculator: Function to calculate adaptive search radius
            mm_per_px: Millimeters per pixel for measurements
            dimension_tolerance: Tolerance for dimension matching (0.05 = 5%)
        """
        self.calc_radius = search_radius_calculator or self._default_radius
        self.mm_per_px = mm_per_px
        self.dimension_tolerance = dimension_tolerance

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

        # Strategy 0: Paired arrows (dimension line with arrows at both ends)
        paired_associations = self._find_paired_arrow_dimensions(
            arrows, text_regions, geometry, search_radius
        )
        associations.extend(paired_associations)
        matched_texts = {a.text_region.text for a in associations}

        # Strategy 1: Arrow-based association (single arrows)
        for arrow in arrows:
            # Find text region near arrow tip (text is usually at arrow head)
            text = self._find_text_near_point(
                arrow.tip_point,
                text_regions,
                max_distance=search_radius / self.mm_per_px
            )

            if text is None:
                # Try finding text near tail (some dimension styles)
                text = self._find_text_near_point(
                    arrow.tail_point,
                    text_regions,
                    max_distance=search_radius / self.mm_per_px * 0.5
                )

            if text is None or text.text in matched_texts:
                continue

            # Find geometry in the direction the arrow points
            # Arrow points from tail to tip, so geometry is near tail
            candidates = self._find_geometry_near_point(
                arrow.tail_point,
                geometry,
                max_distance=search_radius / self.mm_per_px * 2
            )

            if not candidates:
                # Try other end
                candidates = self._find_geometry_near_point(
                    arrow.tip_point,
                    geometry,
                    max_distance=search_radius / self.mm_per_px * 2
                )

            if not candidates:
                continue

            # Rank candidates with directional awareness
            ranked = self._rank_candidates(text, candidates, arrow=arrow)

            if ranked:
                best_feature, score = ranked[0]
                if score > 20:  # Minimum score threshold
                    associations.append(AssociatedDimension(
                        text_region=text,
                        target_feature=best_feature,
                        arrow=arrow,
                        association_confidence=score / 100.0,
                        association_method="leader"
                    ))
                    matched_texts.add(text.text)

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

        # Count by method
        method_counts = {}
        for a in associations:
            method_counts[a.association_method] = method_counts.get(a.association_method, 0) + 1

        logger.info(f"Created {len(associations)} dimension associations: {method_counts}")

        return associations

    def _find_paired_arrow_dimensions(
        self,
        arrows: List[Arrow],
        text_regions: List[TextRegion],
        geometry: Dict[str, List[Any]],
        search_radius: float
    ) -> List[AssociatedDimension]:
        """
        Find dimension lines with arrows pointing at both ends.

        These are the classic dimension line pattern:
        <-------- 24.625 -------->

        Args:
            arrows: Detected arrows
            text_regions: OCR text regions
            geometry: Categorized contours
            search_radius: Search radius in mm

        Returns:
            List of associated dimensions from paired arrows
        """
        associations = []

        # Find arrow pairs (pointing in opposite directions, roughly collinear)
        for i, arrow1 in enumerate(arrows):
            for arrow2 in arrows[i + 1:]:
                if not self._are_opposing_arrows(arrow1, arrow2):
                    continue

                # Found a pair - find text between them
                midpoint = (
                    (arrow1.tip_point[0] + arrow2.tip_point[0]) / 2,
                    (arrow1.tip_point[1] + arrow2.tip_point[1]) / 2
                )

                text = self._find_text_near_point(
                    midpoint,
                    text_regions,
                    max_distance=search_radius / self.mm_per_px
                )

                if text is None:
                    continue

                # Calculate dimension span
                span_px = math.sqrt(
                    (arrow1.tip_point[0] - arrow2.tip_point[0])**2 +
                    (arrow1.tip_point[1] - arrow2.tip_point[1])**2
                )
                span_mm = span_px * self.mm_per_px

                # Find geometry at both ends
                candidates1 = self._find_geometry_near_point(
                    arrow1.tip_point, geometry,
                    max_distance=search_radius / self.mm_per_px
                )
                candidates2 = self._find_geometry_near_point(
                    arrow2.tip_point, geometry,
                    max_distance=search_radius / self.mm_per_px
                )

                # Pick the best overall match
                all_candidates = candidates1 + candidates2
                if all_candidates:
                    ranked = self._rank_candidates(text, all_candidates)
                    if ranked:
                        best_feature, score = ranked[0]

                        # Boost confidence for paired arrows
                        confidence = min(score / 100.0 * 1.2, 1.0)

                        associations.append(AssociatedDimension(
                            text_region=text,
                            target_feature=best_feature,
                            arrow=arrow1,  # Store one of the arrows
                            association_confidence=confidence,
                            association_method="paired"
                        ))

        return associations

    def _are_opposing_arrows(
        self,
        arrow1: Arrow,
        arrow2: Arrow,
        angle_tolerance: float = 30.0,
        max_perpendicular_dist: float = 20.0
    ) -> bool:
        """
        Check if two arrows are opposing (pointing at each other on same line).

        Args:
            arrow1: First arrow
            arrow2: Second arrow
            angle_tolerance: Maximum angle deviation from opposite (degrees)
            max_perpendicular_dist: Maximum perpendicular distance between arrow lines

        Returns:
            True if arrows appear to be a dimension line pair
        """
        # Calculate angle between directions
        dot = (arrow1.direction[0] * arrow2.direction[0] +
               arrow1.direction[1] * arrow2.direction[1])

        # For opposing arrows, dot product should be close to -1
        # cos(180°) = -1, so angles near 180° have dot near -1
        if dot > -0.5:  # More than 60° from opposing
            return False

        # Check collinearity: distance from arrow2's tip to arrow1's line
        # should be small
        perp_dist = self._point_to_line_distance(
            arrow2.tip_point,
            arrow1.tail_point,
            arrow1.tip_point
        )

        if perp_dist > max_perpendicular_dist:
            return False

        # Check that tips are pointing toward each other
        # Vector from arrow1 tip to arrow2 tip
        tip_vec = (
            arrow2.tip_point[0] - arrow1.tip_point[0],
            arrow2.tip_point[1] - arrow1.tip_point[1]
        )

        # Normalize
        tip_len = math.sqrt(tip_vec[0]**2 + tip_vec[1]**2)
        if tip_len < 1:
            return False

        tip_dir = (tip_vec[0] / tip_len, tip_vec[1] / tip_len)

        # Arrow1 should point toward arrow2 (in direction of tip_vec)
        dot1 = arrow1.direction[0] * tip_dir[0] + arrow1.direction[1] * tip_dir[1]

        # Arrow2 should point away from arrow1 (opposite of tip_vec)
        dot2 = arrow2.direction[0] * (-tip_dir[0]) + arrow2.direction[1] * (-tip_dir[1])

        return dot1 > 0.5 and dot2 > 0.5

    def _point_to_line_distance(
        self,
        point: Tuple[float, float],
        line_start: Tuple[float, float],
        line_end: Tuple[float, float]
    ) -> float:
        """Calculate perpendicular distance from point to line segment."""
        px, py = point
        x1, y1 = line_start
        x2, y2 = line_end

        # Line vector
        dx, dy = x2 - x1, y2 - y1
        line_len_sq = dx * dx + dy * dy

        if line_len_sq < 1e-8:
            # Degenerate line
            return math.sqrt((px - x1)**2 + (py - y1)**2)

        # Perpendicular distance
        dist = abs(dy * px - dx * py + x2 * y1 - y2 * x1) / math.sqrt(line_len_sq)
        return dist

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
        candidates: List[Tuple[Any, float]],
        arrow: Optional[Arrow] = None
    ) -> List[Tuple[Any, float]]:
        """
        Rank geometry candidates for a dimension text.

        Scoring factors:
        1. Proximity to leader line endpoint (0-40 points)
        2. Dimensional plausibility (0-30 points)
        3. Feature type appropriateness (0-15 points)
        4. Directional alignment with arrow (0-15 points)
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
                    # Convert text value to mm if needed
                    text_value_mm = self._convert_to_mm(
                        text.parsed_value, text.unit
                    )

                    diff_ratio = abs(measured - text_value_mm) / (text_value_mm + 0.001)
                    if diff_ratio < self.dimension_tolerance / 2:  # Very close
                        score += self.WEIGHT_PLAUSIBILITY
                    elif diff_ratio < self.dimension_tolerance:
                        score += self.WEIGHT_PLAUSIBILITY * 0.7
                    elif diff_ratio < self.dimension_tolerance * 2:
                        score += self.WEIGHT_PLAUSIBILITY * 0.3

            # Factor 3: Feature type appropriateness
            category = getattr(feature, 'category', None)
            if category:
                appropriate = self._is_appropriate_feature(text.text, category)
                if appropriate:
                    score += self.WEIGHT_TYPE_MATCH

            # Factor 4: Directional alignment (if arrow provided)
            if arrow is not None:
                direction_score = self._score_direction_alignment(
                    arrow, text.center, feature
                )
                score += direction_score * self.WEIGHT_DIRECTION

            scored.append((feature, score))

        return sorted(scored, key=lambda x: -x[1])

    def _convert_to_mm(self, value: float, unit: str) -> float:
        """Convert a value to millimeters."""
        unit_lower = unit.lower().strip()
        factor = self.UNIT_TO_MM.get(unit_lower, 1.0)
        return value * factor

    def _score_direction_alignment(
        self,
        arrow: Arrow,
        text_center: Tuple[float, float],
        feature: Any
    ) -> float:
        """
        Score how well arrow direction aligns text to feature.

        Arrow should point from text toward feature (or vice versa).

        Returns:
            Score from 0 to 1
        """
        # Get feature center
        if hasattr(feature, 'bbox'):
            x, y, w, h = feature.bbox
            feature_center = (x + w / 2, y + h / 2)
        elif hasattr(feature, 'contour'):
            feature_center = self._contour_centroid(feature.contour)
        else:
            return 0.5  # Neutral score

        # Vector from arrow tail to feature
        to_feature = (
            feature_center[0] - arrow.tail_point[0],
            feature_center[1] - arrow.tail_point[1]
        )

        # Normalize
        length = math.sqrt(to_feature[0]**2 + to_feature[1]**2)
        if length < 1:
            return 0.5

        to_feature_norm = (to_feature[0] / length, to_feature[1] / length)

        # Arrow should point toward feature (or opposite)
        dot = (arrow.direction[0] * to_feature_norm[0] +
               arrow.direction[1] * to_feature_norm[1])

        # abs(dot) because either direction is valid
        return abs(dot)

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

    def detect_witness_lines(
        self,
        dimension_text: TextRegion,
        geometry: List[Any],
        contours: List[np.ndarray]
    ) -> Tuple[Optional[Tuple[float, float]], Optional[Tuple[float, float]]]:
        """
        Detect witness lines and return geometry contact points.

        This method is used by DimensionLinker to populate LinearDimension
        point1 and point2 fields.

        Args:
            dimension_text: TextRegion from OCR
            geometry: List of ContourInfo objects
            contours: Raw contours for line detection

        Returns:
            (point1, point2) where witness lines touch geometry,
            or (None, None) if not detected
        """
        cv2 = self._cv2_import()

        # Find perpendicular lines near dimension text
        text_center = dimension_text.center
        candidates = self._find_witness_candidates(contours)

        # Filter candidates near the text region
        nearby_candidates = []
        search_radius = 100  # pixels

        for contour in candidates:
            centroid = contour.mean(axis=0)[0]
            dist = np.sqrt(
                (centroid[0] - text_center[0])**2 +
                (centroid[1] - text_center[1])**2
            )
            if dist < search_radius:
                nearby_candidates.append(contour)

        if len(nearby_candidates) < 2:
            return None, None

        # Find the two most likely witness lines (parallel, similar length)
        witness_pair = self._find_parallel_pair(nearby_candidates)

        if not witness_pair:
            return None, None

        # Trace each witness line to nearest geometry intersection
        point1 = self._trace_to_geometry(witness_pair[0], geometry)
        point2 = self._trace_to_geometry(witness_pair[1], geometry)

        return point1, point2

    def _find_parallel_pair(
        self,
        candidates: List[np.ndarray]
    ) -> Optional[Tuple[np.ndarray, np.ndarray]]:
        """Find the most likely parallel pair of witness lines."""
        if len(candidates) < 2:
            return None

        cv2 = self._cv2_import()
        best_pair = None
        best_score = float('inf')

        for i in range(len(candidates)):
            for j in range(i + 1, len(candidates)):
                # Get line angles
                angle1 = self._get_line_angle(candidates[i])
                angle2 = self._get_line_angle(candidates[j])

                # Angular difference (should be near 0 for parallel)
                angle_diff = abs(angle1 - angle2)
                if angle_diff > 90:
                    angle_diff = 180 - angle_diff

                # Length similarity
                len1 = cv2.arcLength(candidates[i], False)
                len2 = cv2.arcLength(candidates[j], False)
                len_ratio = min(len1, len2) / max(len1, len2) if max(len1, len2) > 0 else 0

                # Score: lower is better (parallel + similar length)
                score = angle_diff + (1 - len_ratio) * 45  # Weight length similarity

                if score < best_score:
                    best_score = score
                    best_pair = (candidates[i], candidates[j])

        # Only accept if reasonably parallel (within 15 degrees)
        if best_score > 20:
            return None

        return best_pair

    def _get_line_angle(self, contour: np.ndarray) -> float:
        """Get the angle of a line contour in degrees."""
        pts = contour.reshape(-1, 2)
        if len(pts) < 2:
            return 0

        # Use first and last points
        dx = pts[-1][0] - pts[0][0]
        dy = pts[-1][1] - pts[0][1]

        return np.degrees(np.arctan2(dy, dx))

    def _trace_to_geometry(
        self,
        witness_line: np.ndarray,
        geometry: List[Any]
    ) -> Optional[Tuple[float, float]]:
        """
        Trace witness line to find geometry intersection.

        Args:
            witness_line: Witness line contour
            geometry: List of geometry objects (ContourInfo)

        Returns:
            Intersection point or endpoint if no intersection found
        """
        pts = witness_line.reshape(-1, 2)
        if len(pts) < 2:
            return None

        # Get line endpoints
        p1 = tuple(pts[0])
        p2 = tuple(pts[-1])

        # Try to find intersection with geometry
        for geom in geometry:
            if hasattr(geom, 'contour'):
                intersection = self._find_line_contour_intersection(
                    p1, p2, geom.contour
                )
                if intersection:
                    return intersection

        # If no intersection, return the endpoint further from text center
        # (likely the geometry contact point)
        return tuple(float(x) for x in p2)

    def _find_line_contour_intersection(
        self,
        line_p1: Tuple[float, float],
        line_p2: Tuple[float, float],
        contour: np.ndarray
    ) -> Optional[Tuple[float, float]]:
        """Find intersection point between line and contour."""
        cv2 = self._cv2_import()

        # Check if line endpoints are near contour
        for point in contour:
            pt = point[0] if len(point.shape) > 1 else point
            dist1 = np.sqrt((pt[0] - line_p1[0])**2 + (pt[1] - line_p1[1])**2)
            dist2 = np.sqrt((pt[0] - line_p2[0])**2 + (pt[1] - line_p2[1])**2)

            # If either endpoint is very close to contour, that's our intersection
            if dist1 < 5:
                return (float(line_p1[0]), float(line_p1[1]))
            if dist2 < 5:
                return (float(line_p2[0]), float(line_p2[1]))

        return None
