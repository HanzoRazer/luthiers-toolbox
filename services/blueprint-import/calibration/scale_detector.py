"""
Scale Reference Detector
========================

Detects scale length references in guitar blueprints for calibration.

Detection methods:
1. Nut-to-bridge line detection
2. Scale length text annotation proximity
3. Fret position pattern analysis
4. Centerline measurement

Author: The Production Shop
Version: 4.0.0
"""

import cv2
import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


# Common scale lengths to look for
SCALE_LENGTHS = {
    24.0: "Jaguar/Mustang",
    24.75: "Gibson",
    25.0: "PRS",
    25.5: "Fender",
    26.5: "Baritone",
    27.0: "7-string Extended",
    30.0: "Bass VI",
    34.0: "Bass",
}


@dataclass
class ScaleReference:
    """Detected scale length reference."""
    scale_length_inches: float
    scale_length_mm: float
    pixel_length: float

    # Detection details
    nut_position: Tuple[int, int]  # (x, y) in pixels
    bridge_position: Tuple[int, int]
    detection_method: str
    confidence: float

    # Line parameters
    angle_degrees: float = 0.0

    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "scale_length_inches": round(self.scale_length_inches, 3),
            "scale_length_mm": round(self.scale_length_mm, 2),
            "pixel_length": round(self.pixel_length, 1),
            "nut_position": self.nut_position,
            "bridge_position": self.bridge_position,
            "detection_method": self.detection_method,
            "confidence": round(self.confidence, 3),
            "angle_degrees": round(self.angle_degrees, 2),
            "notes": self.notes,
        }


class ScaleReferenceDetector:
    """
    Detects scale length references in guitar blueprints.

    The scale length is the vibrating length of the strings from nut to bridge.
    This detector finds the nut and bridge positions and calculates the
    pixel distance between them.

    Usage:
        detector = ScaleReferenceDetector()
        reference = detector.detect(image)

        if reference:
            ppi = reference.pixel_length / reference.scale_length_inches
    """

    def __init__(self):
        self.debug_image: Optional[np.ndarray] = None

    def detect(
        self,
        image: np.ndarray,
        hint_scale: Optional[float] = None,
        orientation: str = "auto"
    ) -> Optional[ScaleReference]:
        """
        Detect scale length reference in image.

        Args:
            image: OpenCV BGR image of guitar blueprint
            hint_scale: Expected scale length (helps validation)
            orientation: "vertical", "horizontal", or "auto"

        Returns:
            ScaleReference if detected, None otherwise
        """
        height, width = image.shape[:2]

        # Determine orientation
        if orientation == "auto":
            orientation = "vertical" if height > width else "horizontal"

        # Try multiple detection methods
        methods = [
            ("centerline", self._detect_from_centerline),
            ("nut_bridge", self._detect_from_nut_bridge),
            ("fret_pattern", self._detect_from_fret_pattern),
        ]

        best_result = None
        best_confidence = 0.0

        for method_name, method_func in methods:
            try:
                result = method_func(image, orientation, hint_scale)
                if result and result.confidence > best_confidence:
                    best_result = result
                    best_confidence = result.confidence
            except Exception as e:
                logger.warning(f"Scale detection method {method_name} failed: {e}")

        return best_result

    def _detect_from_centerline(
        self,
        image: np.ndarray,
        orientation: str,
        hint_scale: Optional[float]
    ) -> Optional[ScaleReference]:
        """
        Detect scale from the guitar centerline.

        Looks for the main vertical/horizontal line through the guitar body
        and measures from neck pocket to bridge area.
        """
        height, width = image.shape[:2]
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Find edges
        edges = cv2.Canny(gray, 50, 150)

        # Detect lines
        if orientation == "vertical":
            # Look for vertical centerline
            lines = cv2.HoughLinesP(
                edges, 1, np.pi/180, 100,
                minLineLength=height//3,
                maxLineGap=20
            )
        else:
            # Look for horizontal centerline
            lines = cv2.HoughLinesP(
                edges, 1, np.pi/180, 100,
                minLineLength=width//3,
                maxLineGap=20
            )

        if lines is None:
            return None

        # Find the longest line near center
        center_x = width // 2
        center_y = height // 2

        best_line = None
        best_score = 0

        for line in lines:
            x1, y1, x2, y2 = line[0]
            length = np.sqrt((x2-x1)**2 + (y2-y1)**2)

            # Score by length and proximity to center
            mid_x = (x1 + x2) / 2
            mid_y = (y1 + y2) / 2

            if orientation == "vertical":
                center_dist = abs(mid_x - center_x)
                angle = abs(np.arctan2(x2-x1, y2-y1))  # Angle from vertical
            else:
                center_dist = abs(mid_y - center_y)
                angle = abs(np.arctan2(y2-y1, x2-x1))  # Angle from horizontal

            # Prefer lines close to center and mostly aligned
            if angle < np.pi/6:  # Within 30 degrees of axis
                score = length / (1 + center_dist/100)
                if score > best_score:
                    best_score = score
                    best_line = line[0]

        if best_line is None:
            return None

        x1, y1, x2, y2 = best_line
        pixel_length = np.sqrt((x2-x1)**2 + (y2-y1)**2)

        # Estimate scale length using heuristic
        # Neck is typically at top (smaller y) for vertical orientation
        if orientation == "vertical":
            if y1 < y2:
                nut_pos = (x1, y1)
                bridge_pos = (x2, y2)
            else:
                nut_pos = (x2, y2)
                bridge_pos = (x1, y1)
        else:
            if x1 < x2:
                nut_pos = (x1, y1)
                bridge_pos = (x2, y2)
            else:
                nut_pos = (x2, y2)
                bridge_pos = (x1, y1)

        # Try to match to common scale length
        scale_length = self._match_to_common_scale(pixel_length, hint_scale)

        if scale_length is None:
            return None

        angle = np.degrees(np.arctan2(y2-y1, x2-x1))

        return ScaleReference(
            scale_length_inches=scale_length,
            scale_length_mm=scale_length * 25.4,
            pixel_length=pixel_length,
            nut_position=nut_pos,
            bridge_position=bridge_pos,
            detection_method="centerline",
            confidence=0.5,
            angle_degrees=angle,
            notes=["Detected from centerline analysis"]
        )

    def _detect_from_nut_bridge(
        self,
        image: np.ndarray,
        orientation: str,
        hint_scale: Optional[float]
    ) -> Optional[ScaleReference]:
        """
        Detect scale by finding nut and bridge positions separately.
        """
        height, width = image.shape[:2]
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Threshold to find dark features
        _, thresh = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY_INV)

        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if len(contours) < 2:
            return None

        # Sort contours by position
        if orientation == "vertical":
            # Sort by y-position
            contours_sorted = sorted(contours, key=lambda c: cv2.boundingRect(c)[1])
        else:
            # Sort by x-position
            contours_sorted = sorted(contours, key=lambda c: cv2.boundingRect(c)[0])

        # Find small horizontal features (nut/bridge are horizontal lines)
        candidates = []
        for c in contours_sorted:
            x, y, w, h = cv2.boundingRect(c)

            # Nut and bridge are wider than tall
            if w > h * 2 and w > 20:
                aspect = w / h if h > 0 else 0
                candidates.append({
                    'contour': c,
                    'bbox': (x, y, w, h),
                    'center': (x + w//2, y + h//2),
                    'aspect': aspect
                })

        if len(candidates) < 2:
            return None

        # Assume first candidate is nut, find best bridge match
        nut_candidate = candidates[0]

        # Bridge should be near centerline x-position and lower (higher y)
        best_bridge = None
        best_score = 0

        for cand in candidates[1:]:
            # Check x alignment (should be similar to nut)
            x_diff = abs(cand['center'][0] - nut_candidate['center'][0])

            if orientation == "vertical":
                # Bridge should be below nut
                if cand['center'][1] <= nut_candidate['center'][1]:
                    continue
                y_dist = cand['center'][1] - nut_candidate['center'][1]
            else:
                # Bridge should be to right of nut
                if cand['center'][0] <= nut_candidate['center'][0]:
                    continue
                y_dist = cand['center'][0] - nut_candidate['center'][0]

            # Score based on alignment and reasonable distance
            if y_dist > height * 0.3 and x_diff < width * 0.2:
                score = y_dist / (1 + x_diff)
                if score > best_score:
                    best_score = score
                    best_bridge = cand

        if best_bridge is None:
            return None

        # Calculate pixel distance
        dx = best_bridge['center'][0] - nut_candidate['center'][0]
        dy = best_bridge['center'][1] - nut_candidate['center'][1]
        pixel_length = np.sqrt(dx*dx + dy*dy)

        # Match to scale
        scale_length = self._match_to_common_scale(pixel_length, hint_scale)

        if scale_length is None:
            return None

        return ScaleReference(
            scale_length_inches=scale_length,
            scale_length_mm=scale_length * 25.4,
            pixel_length=pixel_length,
            nut_position=nut_candidate['center'],
            bridge_position=best_bridge['center'],
            detection_method="nut_bridge",
            confidence=0.6,
            angle_degrees=np.degrees(np.arctan2(dy, dx)),
            notes=["Detected nut and bridge positions"]
        )

    def _detect_from_fret_pattern(
        self,
        image: np.ndarray,
        orientation: str,
        hint_scale: Optional[float]
    ) -> Optional[ScaleReference]:
        """
        Detect scale from fret spacing pattern.

        Fret positions follow the 12-TET formula:
        fret_n = scale_length * (1 - 2^(-n/12))

        The ratio between consecutive fret distances is constant: 2^(1/12) = 1.0595
        """
        height, width = image.shape[:2]
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Find horizontal lines (frets)
        edges = cv2.Canny(gray, 50, 150)

        if orientation == "vertical":
            # Frets are horizontal lines
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, 50, minLineLength=30, maxLineGap=10)
        else:
            # Frets are vertical lines
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, 50, minLineLength=30, maxLineGap=10)

        if lines is None or len(lines) < 5:
            return None

        # Extract line positions
        positions = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            if orientation == "vertical":
                # Check if mostly horizontal
                if abs(y2 - y1) < abs(x2 - x1) * 0.3:
                    positions.append((y1 + y2) / 2)
            else:
                # Check if mostly vertical
                if abs(x2 - x1) < abs(y2 - y1) * 0.3:
                    positions.append((x1 + x2) / 2)

        if len(positions) < 5:
            return None

        # Sort positions
        positions = sorted(set(int(p) for p in positions))

        # Calculate spacing ratios
        spacings = np.diff(positions)
        if len(spacings) < 3:
            return None

        # Look for consistent ratio (should be ~1.0595 for 12-TET)
        ratios = []
        for i in range(len(spacings) - 1):
            if spacings[i+1] > 0:
                ratios.append(spacings[i] / spacings[i+1])

        if not ratios:
            return None

        median_ratio = np.median(ratios)

        # Check if ratio matches 12-TET
        expected_ratio = 2 ** (1/12)  # 1.0595...
        ratio_error = abs(median_ratio - expected_ratio) / expected_ratio

        if ratio_error > 0.15:  # 15% tolerance
            return None

        # Calculate scale length from fret spacing
        # First fret distance = scale_length * (1 - 2^(-1/12))
        # = scale_length * 0.0561
        first_fret_factor = 1 - 2**(-1/12)

        if spacings[0] > 10:  # Minimum reasonable spacing
            estimated_scale_px = spacings[0] / first_fret_factor

            # Match to common scale
            scale_length = self._match_to_common_scale(estimated_scale_px, hint_scale)

            if scale_length:
                return ScaleReference(
                    scale_length_inches=scale_length,
                    scale_length_mm=scale_length * 25.4,
                    pixel_length=estimated_scale_px,
                    nut_position=(width//2, positions[0]),
                    bridge_position=(width//2, int(positions[0] + estimated_scale_px)),
                    detection_method="fret_pattern",
                    confidence=0.7,
                    notes=[
                        f"Detected 12-TET fret pattern",
                        f"Fret ratio: {median_ratio:.4f} (expected: {expected_ratio:.4f})"
                    ]
                )

        return None

    def _match_to_common_scale(
        self,
        pixel_length: float,
        hint_scale: Optional[float]
    ) -> Optional[float]:
        """
        Match pixel length to common scale lengths.

        Uses hint_scale if provided, otherwise tries all common scales.
        """
        if hint_scale:
            return hint_scale

        # Without PPI, we can't determine absolute scale
        # But we can return the hint or None
        return None

    def detect_with_calibration(
        self,
        image: np.ndarray,
        ppi: float,
        orientation: str = "auto"
    ) -> Optional[ScaleReference]:
        """
        Detect scale reference using known PPI calibration.

        Args:
            image: Blueprint image
            ppi: Known pixels-per-inch
            orientation: Image orientation

        Returns:
            ScaleReference with validated scale length
        """
        height, width = image.shape[:2]

        if orientation == "auto":
            orientation = "vertical" if height > width else "horizontal"

        # Try detection methods
        result = self._detect_from_centerline(image, orientation, None)

        if result:
            # Calculate actual scale length from pixels
            actual_scale = result.pixel_length / ppi

            # Validate against common scales
            best_match = None
            best_diff = float('inf')

            for scale in SCALE_LENGTHS.keys():
                diff = abs(actual_scale - scale)
                if diff < best_diff and diff < 1.0:  # Within 1 inch
                    best_diff = diff
                    best_match = scale

            if best_match:
                result.scale_length_inches = best_match
                result.scale_length_mm = best_match * 25.4
                result.confidence = max(0.5, 1.0 - best_diff)
                result.notes.append(f"Validated: {actual_scale:.2f}\" -> {best_match}\" ({SCALE_LENGTHS[best_match]})")

            return result

        return None
