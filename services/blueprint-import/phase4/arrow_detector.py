"""
Arrow Detection for Blueprint Dimension Association
====================================================

Hybrid arrow detection system using:
1. Contour analysis (primary) - Works for all blueprint styles
2. Template matching (secondary) - Standard arrow shapes
3. Image-based detection (fallback) - Line + triangle pattern matching

Author: The Production Shop
Version: 4.0.0
"""

import logging
import math
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any
from enum import Enum
import numpy as np

try:
    import cv2
except ImportError:
    cv2 = None

logger = logging.getLogger(__name__)


class ArrowOrientation(Enum):
    """Expected arrow orientations in dimension drawings."""
    HORIZONTAL = "horizontal"  # 0° or 180°
    VERTICAL = "vertical"      # 90° or 270°
    DIAGONAL = "diagonal"      # 45°, 135°, etc.
    ANY = "any"


@dataclass
class Arrow:
    """Detected arrow with position and direction."""
    tip_point: Tuple[float, float]      # Arrow tip (x, y) in pixels
    tail_point: Tuple[float, float]     # Arrow tail (x, y) in pixels
    direction: Tuple[float, float]      # Normalized direction vector
    confidence: float                    # Detection confidence (0-1)
    contour_index: int                   # Reference to source contour
    detection_method: str = "contour"   # "contour" or "template"

    @property
    def length(self) -> float:
        """Arrow length in pixels."""
        dx = self.tip_point[0] - self.tail_point[0]
        dy = self.tip_point[1] - self.tail_point[1]
        return np.sqrt(dx**2 + dy**2)

    @property
    def angle_degrees(self) -> float:
        """Arrow angle in degrees (0 = right, 90 = up)."""
        return np.degrees(np.arctan2(-self.direction[1], self.direction[0]))

    def to_dict(self) -> Dict[str, Any]:
        return {
            'tip': self.tip_point,
            'tail': self.tail_point,
            'direction': self.direction,
            'confidence': self.confidence,
            'length': self.length,
            'angle': self.angle_degrees,
            'method': self.detection_method
        }


@dataclass
class ArrowDetectionStats:
    """Statistics from arrow detection run."""
    contour_detections: int = 0
    template_matches: int = 0
    image_detections: int = 0
    total_arrows: int = 0
    processing_time_ms: float = 0.0
    filtered_by_angle: int = 0
    filtered_by_size: int = 0


class ArrowDetector:
    """
    Hybrid arrow detection system.

    Usage:
        detector = ArrowDetector()
        arrows = detector.detect_arrows(contours)

        # Early testing with mock data
        detector.debug_mode = True  # Returns simulated arrows

    Detection Strategy:
        1. Analyze contour endpoints for triangular terminations
        2. If contour analysis yields low confidence, try template matching
        3. Combine results and remove duplicates
    """

    # Template arrow shapes (normalized, tip at origin pointing right)
    ARROW_TEMPLATES = {
        'standard': np.array([
            [0, 0], [-10, 5], [-7, 0], [-10, -5]
        ], dtype=np.float32),
        'open': np.array([
            [0, 0], [-10, 5], [0, 0], [-10, -5]
        ], dtype=np.float32),
        'filled': np.array([
            [0, 0], [-12, 6], [-8, 0], [-12, -6]
        ], dtype=np.float32),
    }

    # Detection thresholds
    MIN_ARROW_LENGTH = 5.0      # pixels
    MAX_ARROW_LENGTH = 50.0     # pixels
    TRIANGULAR_DEFECT_THRESHOLD = 20  # convexity defect depth
    TEMPLATE_MATCH_THRESHOLD = 0.7

    # Angle tolerance for axis-aligned arrows (degrees)
    AXIS_ANGLE_TOLERANCE = 15.0

    # Arrowhead geometry thresholds
    MIN_TIP_ANGLE = 20.0   # degrees - too sharp is noise
    MAX_TIP_ANGLE = 90.0   # degrees - too blunt isn't an arrow

    def __init__(
        self,
        debug_mode: bool = False,
        orientation_filter: ArrowOrientation = ArrowOrientation.ANY,
        prefer_axis_aligned: bool = True
    ):
        """
        Initialize arrow detector.

        Args:
            debug_mode: If True, return mock arrows for testing
            orientation_filter: Filter arrows by expected orientation
            prefer_axis_aligned: Boost confidence for horizontal/vertical arrows
        """
        self.debug_mode = debug_mode
        self.orientation_filter = orientation_filter
        self.prefer_axis_aligned = prefer_axis_aligned
        self.stats = ArrowDetectionStats()
        self._template_cache = {}

        if cv2 is None:
            logger.warning("OpenCV not available - arrow detection disabled")

    def detect_arrows(
        self,
        contours: List[np.ndarray],
        min_confidence: float = 0.5
    ) -> List[Arrow]:
        """
        Detect arrows in a list of contours.

        Args:
            contours: List of OpenCV contours (numpy arrays)
            min_confidence: Minimum confidence threshold

        Returns:
            List of detected Arrow objects
        """
        import time
        start_time = time.time()

        if self.debug_mode:
            return self._get_mock_arrows()

        if cv2 is None:
            logger.warning("OpenCV not available")
            return []

        arrows = []
        self.stats = ArrowDetectionStats()

        for idx, contour in enumerate(contours):
            # Skip very small or very large contours
            if len(contour) < 4:
                continue

            # Primary: Contour analysis
            arrow = self._detect_arrow_from_contour(contour, idx)
            if arrow and arrow.confidence >= min_confidence:
                arrows.append(arrow)
                self.stats.contour_detections += 1
                continue

            # Secondary: Template matching (only if contour analysis failed)
            arrow = self._detect_arrow_from_template(contour, idx)
            if arrow and arrow.confidence >= min_confidence:
                arrows.append(arrow)
                self.stats.template_matches += 1

        # Remove duplicate detections
        arrows = self._remove_duplicates(arrows)

        # Apply orientation filter
        if self.orientation_filter != ArrowOrientation.ANY:
            arrows = self._filter_by_orientation(arrows)

        # Boost confidence for axis-aligned arrows
        if self.prefer_axis_aligned:
            arrows = self._boost_axis_aligned(arrows)

        self.stats.total_arrows = len(arrows)
        self.stats.processing_time_ms = (time.time() - start_time) * 1000

        logger.info(f"Detected {len(arrows)} arrows "
                   f"(contour: {self.stats.contour_detections}, "
                   f"template: {self.stats.template_matches})")

        return arrows

    def detect_arrows_in_image(
        self,
        image: np.ndarray,
        min_confidence: float = 0.5
    ) -> List[Arrow]:
        """
        Detect arrows directly from image using line detection.

        This is a fallback method when contour detection misses arrows
        that are part of the line work (not separate contours).

        Args:
            image: Grayscale or BGR image
            min_confidence: Minimum confidence threshold

        Returns:
            List of detected Arrow objects
        """
        if cv2 is None:
            return []

        import time
        start_time = time.time()

        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        # Edge detection
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)

        # Detect lines using probabilistic Hough transform
        lines = cv2.HoughLinesP(
            edges,
            rho=1,
            theta=np.pi/180,
            threshold=30,
            minLineLength=self.MIN_ARROW_LENGTH,
            maxLineGap=5
        )

        if lines is None:
            return []

        arrows = []

        # Group nearby line endpoints to find potential arrowheads
        endpoints = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            endpoints.append(((x1, y1), (x2, y2), line[0]))

        # Find clusters of 3+ lines meeting at a point (arrowhead pattern)
        for i, (ep1, ep2, line) in enumerate(endpoints):
            for point in [ep1, ep2]:
                nearby_lines = self._find_lines_near_point(
                    point, endpoints, radius=15
                )

                if len(nearby_lines) >= 2:
                    # Potential arrowhead - analyze angles
                    arrow = self._analyze_arrowhead_cluster(
                        point, nearby_lines, i
                    )
                    if arrow and arrow.confidence >= min_confidence:
                        arrows.append(arrow)
                        self.stats.image_detections += 1

        arrows = self._remove_duplicates(arrows)
        self.stats.processing_time_ms += (time.time() - start_time) * 1000

        return arrows

    def _find_lines_near_point(
        self,
        point: Tuple[float, float],
        endpoints: List[Tuple],
        radius: float
    ) -> List[Tuple]:
        """Find lines with endpoints near a given point."""
        nearby = []
        px, py = point

        for ep1, ep2, line in endpoints:
            for ep in [ep1, ep2]:
                dist = math.sqrt((ep[0] - px)**2 + (ep[1] - py)**2)
                if dist < radius:
                    nearby.append((ep1, ep2, line, ep))
                    break

        return nearby

    def _analyze_arrowhead_cluster(
        self,
        center: Tuple[float, float],
        lines: List[Tuple],
        contour_idx: int
    ) -> Optional[Arrow]:
        """
        Analyze a cluster of lines meeting at a point.

        An arrowhead has:
        - 2-3 lines meeting at the tip
        - Lines at symmetric angles (30-60 degrees from shaft)
        - One longer line (the shaft)
        """
        if len(lines) < 2:
            return None

        # Calculate angles of all lines from the center point
        angles_and_lengths = []
        for ep1, ep2, line, near_ep in lines:
            # Get the far endpoint
            far_ep = ep2 if near_ep == ep1 else ep1

            dx = far_ep[0] - center[0]
            dy = far_ep[1] - center[1]
            angle = math.degrees(math.atan2(dy, dx))
            length = math.sqrt(dx**2 + dy**2)

            angles_and_lengths.append({
                'angle': angle,
                'length': length,
                'far_point': far_ep,
                'line': line
            })

        # Find the shaft (longest line)
        shaft = max(angles_and_lengths, key=lambda x: x['length'])
        others = [a for a in angles_and_lengths if a != shaft]

        if not others:
            return None

        # Check if other lines form symmetric arrowhead barbs
        shaft_angle = shaft['angle']
        barb_angles = [a['angle'] for a in others]

        # Normalize angles relative to shaft
        relative_angles = []
        for ba in barb_angles:
            rel = (ba - shaft_angle + 180) % 360 - 180
            relative_angles.append(abs(rel))

        # Arrowhead barbs should be 20-80 degrees from shaft
        valid_barbs = [a for a in relative_angles
                       if self.MIN_TIP_ANGLE <= a <= self.MAX_TIP_ANGLE]

        if len(valid_barbs) < 1:
            return None

        # Calculate confidence based on symmetry and angle
        if len(valid_barbs) >= 2:
            # Check symmetry
            angle_diff = abs(valid_barbs[0] - valid_barbs[1])
            symmetry_score = 1.0 - min(angle_diff / 30.0, 1.0)
            confidence = 0.7 + 0.3 * symmetry_score
        else:
            confidence = 0.6

        # Arrow tip is the center, tail is end of shaft
        tip = center
        tail = shaft['far_point']

        dx = tip[0] - tail[0]
        dy = tip[1] - tail[1]
        length = math.sqrt(dx**2 + dy**2)

        if length < self.MIN_ARROW_LENGTH:
            return None

        direction = (dx / length, dy / length)

        return Arrow(
            tip_point=(float(tip[0]), float(tip[1])),
            tail_point=(float(tail[0]), float(tail[1])),
            direction=direction,
            confidence=confidence,
            contour_index=contour_idx,
            detection_method="image"
        )

    def _filter_by_orientation(self, arrows: List[Arrow]) -> List[Arrow]:
        """Filter arrows by expected orientation."""
        filtered = []

        for arrow in arrows:
            angle = abs(arrow.angle_degrees)

            if self.orientation_filter == ArrowOrientation.HORIZONTAL:
                # 0° or 180° (±tolerance)
                if angle <= self.AXIS_ANGLE_TOLERANCE or \
                   abs(angle - 180) <= self.AXIS_ANGLE_TOLERANCE:
                    filtered.append(arrow)
                else:
                    self.stats.filtered_by_angle += 1

            elif self.orientation_filter == ArrowOrientation.VERTICAL:
                # 90° or 270° (±tolerance)
                if abs(angle - 90) <= self.AXIS_ANGLE_TOLERANCE or \
                   abs(angle - 270) <= self.AXIS_ANGLE_TOLERANCE:
                    filtered.append(arrow)
                else:
                    self.stats.filtered_by_angle += 1

            elif self.orientation_filter == ArrowOrientation.DIAGONAL:
                # 45°, 135°, 225°, 315° (±tolerance)
                for target in [45, 135, 225, 315]:
                    if abs(angle - target) <= self.AXIS_ANGLE_TOLERANCE:
                        filtered.append(arrow)
                        break
                else:
                    self.stats.filtered_by_angle += 1

            else:
                filtered.append(arrow)

        return filtered

    def _boost_axis_aligned(self, arrows: List[Arrow]) -> List[Arrow]:
        """Boost confidence for axis-aligned arrows (common in dimensions)."""
        boosted = []

        for arrow in arrows:
            angle = abs(arrow.angle_degrees)

            # Check if close to 0°, 90°, 180°, 270°
            is_axis_aligned = False
            for target in [0, 90, 180, 270]:
                if abs(angle - target) <= self.AXIS_ANGLE_TOLERANCE:
                    is_axis_aligned = True
                    break

            if is_axis_aligned:
                # Boost confidence by 10%
                boosted_confidence = min(arrow.confidence * 1.1, 1.0)
                boosted.append(Arrow(
                    tip_point=arrow.tip_point,
                    tail_point=arrow.tail_point,
                    direction=arrow.direction,
                    confidence=boosted_confidence,
                    contour_index=arrow.contour_index,
                    detection_method=arrow.detection_method
                ))
            else:
                boosted.append(arrow)

        return boosted

    def validate_arrow_geometry(self, arrow: Arrow) -> Tuple[bool, str]:
        """
        Validate arrow geometry for dimension association.

        Returns:
            (is_valid, reason) tuple
        """
        # Check length
        if arrow.length < self.MIN_ARROW_LENGTH:
            return False, f"Too short: {arrow.length:.1f}px < {self.MIN_ARROW_LENGTH}px"

        if arrow.length > self.MAX_ARROW_LENGTH:
            return False, f"Too long: {arrow.length:.1f}px > {self.MAX_ARROW_LENGTH}px"

        # Check confidence
        if arrow.confidence < 0.3:
            return False, f"Low confidence: {arrow.confidence:.2f}"

        # Check for degenerate direction
        dir_length = math.sqrt(arrow.direction[0]**2 + arrow.direction[1]**2)
        if abs(dir_length - 1.0) > 0.01:
            return False, f"Invalid direction vector: length={dir_length:.3f}"

        return True, "OK"

    def _detect_arrow_from_contour(
        self,
        contour: np.ndarray,
        contour_idx: int
    ) -> Optional[Arrow]:
        """
        Detect arrow using contour analysis.

        Looks for triangular terminations at line endpoints.
        """
        # Need enough points for convex hull
        if len(contour) < 5:
            return None

        try:
            # Get convex hull
            hull = cv2.convexHull(contour, returnPoints=False)
            if hull is None or len(hull) < 3:
                return None

            # Find convexity defects
            defects = cv2.convexityDefects(contour, hull)
            if defects is None:
                return None

            # Look for significant triangular protrusions
            triangular_points = []
            for i in range(defects.shape[0]):
                s, e, f, d = defects[i, 0]
                if d > self.TRIANGULAR_DEFECT_THRESHOLD:
                    # This could be an arrowhead
                    start_pt = tuple(contour[s][0])
                    end_pt = tuple(contour[e][0])
                    far_pt = tuple(contour[f][0])
                    triangular_points.append({
                        'start': start_pt,
                        'end': end_pt,
                        'far': far_pt,
                        'depth': d / 256.0  # Normalize
                    })

            if not triangular_points:
                return None

            # Find the most prominent triangular feature (likely arrowhead)
            best = max(triangular_points, key=lambda x: x['depth'])

            # Calculate arrow geometry
            tip = self._find_arrow_tip(contour, best)
            tail = self._find_arrow_tail(contour, tip)

            if tip is None or tail is None:
                return None

            # Calculate direction
            dx = tip[0] - tail[0]
            dy = tip[1] - tail[1]
            length = np.sqrt(dx**2 + dy**2)

            if length < self.MIN_ARROW_LENGTH or length > self.MAX_ARROW_LENGTH:
                return None

            direction = (dx / length, dy / length)

            # Confidence based on triangular depth
            confidence = min(best['depth'] / 50.0, 1.0)

            return Arrow(
                tip_point=tip,
                tail_point=tail,
                direction=direction,
                confidence=confidence,
                contour_index=contour_idx,
                detection_method="contour"
            )

        except Exception as e:
            logger.debug(f"Contour arrow detection failed: {e}")
            return None

    def _detect_arrow_from_template(
        self,
        contour: np.ndarray,
        contour_idx: int
    ) -> Optional[Arrow]:
        """
        Detect arrow using template matching.

        Compares contour endpoints against known arrow shapes.
        """
        # Get bounding box
        x, y, w, h = cv2.boundingRect(contour)

        # Skip if not arrow-like proportions
        aspect = max(w, h) / (min(w, h) + 1)
        if aspect < 1.5 or aspect > 10:
            return None

        # Extract endpoints
        endpoints = self._extract_endpoints(contour)
        if len(endpoints) < 2:
            return None

        best_match = None
        best_score = 0

        for template_name, template in self.ARROW_TEMPLATES.items():
            for endpoint in endpoints:
                score = self._match_template_at_point(contour, endpoint, template)
                if score > best_score:
                    best_score = score
                    best_match = {
                        'point': endpoint,
                        'template': template_name,
                        'score': score
                    }

        if best_match and best_score >= self.TEMPLATE_MATCH_THRESHOLD:
            # Reconstruct arrow from match
            tip = best_match['point']
            tail = self._find_opposite_endpoint(contour, tip, endpoints)

            if tail is None:
                return None

            dx = tip[0] - tail[0]
            dy = tip[1] - tail[1]
            length = np.sqrt(dx**2 + dy**2)

            if length < self.MIN_ARROW_LENGTH:
                return None

            direction = (dx / length, dy / length)

            return Arrow(
                tip_point=tip,
                tail_point=tail,
                direction=direction,
                confidence=best_score,
                contour_index=contour_idx,
                detection_method="template"
            )

        return None

    def _find_arrow_tip(
        self,
        contour: np.ndarray,
        triangular_feature: dict
    ) -> Optional[Tuple[float, float]]:
        """Find the arrow tip point from triangular feature."""
        # The tip is typically the far point of the convexity defect
        # or the midpoint between start and end
        start = np.array(triangular_feature['start'])
        end = np.array(triangular_feature['end'])
        far = np.array(triangular_feature['far'])

        # Check which point extends furthest from centroid
        centroid = contour.mean(axis=0)[0]

        candidates = [
            (start, np.linalg.norm(start - centroid)),
            (end, np.linalg.norm(end - centroid)),
            (far, np.linalg.norm(far - centroid)),
        ]

        tip = max(candidates, key=lambda x: x[1])[0]
        return (float(tip[0]), float(tip[1]))

    def _find_arrow_tail(
        self,
        contour: np.ndarray,
        tip: Tuple[float, float]
    ) -> Optional[Tuple[float, float]]:
        """Find the arrow tail (opposite end from tip)."""
        tip_arr = np.array(tip)

        # Find point furthest from tip
        max_dist = 0
        tail = None

        for point in contour:
            pt = point[0]
            dist = np.linalg.norm(pt - tip_arr)
            if dist > max_dist:
                max_dist = dist
                tail = pt

        if tail is not None:
            return (float(tail[0]), float(tail[1]))
        return None

    def _extract_endpoints(self, contour: np.ndarray) -> List[Tuple[float, float]]:
        """Extract endpoint candidates from contour."""
        # Use contour approximation to find key points
        epsilon = 0.02 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)

        endpoints = []
        for point in approx:
            endpoints.append((float(point[0][0]), float(point[0][1])))

        return endpoints

    def _match_template_at_point(
        self,
        contour: np.ndarray,
        point: Tuple[float, float],
        template: np.ndarray
    ) -> float:
        """Match template shape at a specific point."""
        # Extract local region around point
        # Compare shape similarity using Hu moments or shape matching
        # This is a simplified implementation

        # Get nearby contour points
        pt = np.array(point)
        distances = np.linalg.norm(contour.reshape(-1, 2) - pt, axis=1)
        nearby_mask = distances < 20  # pixels

        if nearby_mask.sum() < 3:
            return 0.0

        nearby_points = contour.reshape(-1, 2)[nearby_mask]

        # Simple shape comparison using variance
        variance = np.var(nearby_points, axis=0).sum()

        # Higher variance = more likely to be arrowhead
        score = min(variance / 100.0, 1.0)

        return score

    def _find_opposite_endpoint(
        self,
        contour: np.ndarray,
        tip: Tuple[float, float],
        endpoints: List[Tuple[float, float]]
    ) -> Optional[Tuple[float, float]]:
        """Find the endpoint furthest from the tip."""
        tip_arr = np.array(tip)

        max_dist = 0
        opposite = None

        for endpoint in endpoints:
            if endpoint == tip:
                continue
            dist = np.linalg.norm(np.array(endpoint) - tip_arr)
            if dist > max_dist:
                max_dist = dist
                opposite = endpoint

        return opposite

    def _remove_duplicates(
        self,
        arrows: List[Arrow],
        distance_threshold: float = 10.0
    ) -> List[Arrow]:
        """Remove duplicate arrow detections."""
        if len(arrows) <= 1:
            return arrows

        unique = []
        for arrow in sorted(arrows, key=lambda a: -a.confidence):
            is_duplicate = False
            for existing in unique:
                tip_dist = np.sqrt(
                    (arrow.tip_point[0] - existing.tip_point[0])**2 +
                    (arrow.tip_point[1] - existing.tip_point[1])**2
                )
                if tip_dist < distance_threshold:
                    is_duplicate = True
                    break

            if not is_duplicate:
                unique.append(arrow)

        return unique

    def _get_mock_arrows(self) -> List[Arrow]:
        """Return mock arrows for testing."""
        return [
            Arrow(
                tip_point=(450.0, 320.0),
                tail_point=(380.0, 320.0),
                direction=(1.0, 0.0),
                confidence=0.95,
                contour_index=12,
                detection_method="mock"
            ),
            Arrow(
                tip_point=(200.0, 150.0),
                tail_point=(200.0, 80.0),
                direction=(0.0, 1.0),
                confidence=0.88,
                contour_index=24,
                detection_method="mock"
            ),
            Arrow(
                tip_point=(600.0, 400.0),
                tail_point=(520.0, 400.0),
                direction=(1.0, 0.0),
                confidence=0.82,
                contour_index=37,
                detection_method="mock"
            ),
        ]

    def is_triangular_tip(self, contour: np.ndarray) -> bool:
        """
        Public method to check if contour ends in a triangular shape.

        Useful for external callers to pre-filter contours.
        """
        if cv2 is None or len(contour) < 5:
            return False

        try:
            hull = cv2.convexHull(contour, returnPoints=False)
            if hull is None:
                return False

            defects = cv2.convexityDefects(contour, hull)
            if defects is None:
                return False

            for i in range(defects.shape[0]):
                s, e, f, d = defects[i, 0]
                if d > self.TRIANGULAR_DEFECT_THRESHOLD:
                    return True

            return False

        except Exception:
            return False
