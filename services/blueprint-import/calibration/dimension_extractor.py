"""
Calibrated Dimension Extractor
==============================

Extracts real-world dimensions from guitar blueprints using pixel calibration.

Measures:
- Body length and width
- Upper/lower bout widths
- Waist width
- Neck pocket dimensions
- Control cavity areas

Author: Luthier's Toolbox
Version: 4.0.0
"""

import cv2
import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
import logging

from .pixel_calibrator import PixelCalibrator, CalibrationResult, CalibrationMethod

logger = logging.getLogger(__name__)


@dataclass
class GuitarDimensions:
    """Extracted guitar dimensions in real-world units."""
    # Identification
    name: str = ""
    source_file: str = ""

    # Calibration used
    calibration_method: str = ""
    ppi: float = 0.0
    calibration_confidence: float = 0.0

    # Scale length (if detected)
    scale_length_inches: Optional[float] = None
    scale_length_mm: Optional[float] = None

    # Body dimensions
    body_length_inches: Optional[float] = None
    body_width_inches: Optional[float] = None
    body_length_mm: Optional[float] = None
    body_width_mm: Optional[float] = None

    # Bout measurements
    upper_bout_width_inches: Optional[float] = None
    lower_bout_width_inches: Optional[float] = None
    waist_width_inches: Optional[float] = None

    upper_bout_width_mm: Optional[float] = None
    lower_bout_width_mm: Optional[float] = None
    waist_width_mm: Optional[float] = None

    # Body thickness (if side view available)
    body_thickness_inches: Optional[float] = None
    body_thickness_mm: Optional[float] = None

    # Neck dimensions
    neck_pocket_length_inches: Optional[float] = None
    neck_pocket_width_inches: Optional[float] = None
    nut_width_inches: Optional[float] = None

    # Computed properties
    body_aspect_ratio: Optional[float] = None
    upper_to_lower_bout_ratio: Optional[float] = None

    # Raw pixel measurements
    pixel_measurements: Dict[str, float] = field(default_factory=dict)

    # Notes and warnings
    notes: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "source_file": self.source_file,
            "calibration": {
                "method": self.calibration_method,
                "ppi": round(self.ppi, 2),
                "confidence": round(self.calibration_confidence, 3),
            },
            "scale_length": {
                "inches": self.scale_length_inches,
                "mm": round(self.scale_length_mm, 1) if self.scale_length_mm else None,
            },
            "body": {
                "length_inches": round(self.body_length_inches, 2) if self.body_length_inches else None,
                "width_inches": round(self.body_width_inches, 2) if self.body_width_inches else None,
                "length_mm": round(self.body_length_mm, 1) if self.body_length_mm else None,
                "width_mm": round(self.body_width_mm, 1) if self.body_width_mm else None,
                "thickness_inches": round(self.body_thickness_inches, 2) if self.body_thickness_inches else None,
                "aspect_ratio": round(self.body_aspect_ratio, 3) if self.body_aspect_ratio else None,
            },
            "bouts": {
                "upper_inches": round(self.upper_bout_width_inches, 2) if self.upper_bout_width_inches else None,
                "lower_inches": round(self.lower_bout_width_inches, 2) if self.lower_bout_width_inches else None,
                "waist_inches": round(self.waist_width_inches, 2) if self.waist_width_inches else None,
                "upper_to_lower_ratio": round(self.upper_to_lower_bout_ratio, 3) if self.upper_to_lower_bout_ratio else None,
            },
            "neck": {
                "pocket_length_inches": round(self.neck_pocket_length_inches, 2) if self.neck_pocket_length_inches else None,
                "pocket_width_inches": round(self.neck_pocket_width_inches, 2) if self.neck_pocket_width_inches else None,
                "nut_width_inches": round(self.nut_width_inches, 3) if self.nut_width_inches else None,
            },
            "pixel_measurements": {k: round(v, 1) for k, v in self.pixel_measurements.items()},
            "notes": self.notes,
            "warnings": self.warnings,
        }

    def summary(self) -> str:
        """Generate human-readable summary."""
        lines = [f"=== {self.name} ==="]

        if self.scale_length_inches:
            lines.append(f"Scale Length: {self.scale_length_inches:.2f}\" ({self.scale_length_mm:.1f}mm)")

        if self.body_length_inches and self.body_width_inches:
            lines.append(f"Body: {self.body_length_inches:.2f}\" x {self.body_width_inches:.2f}\"")
            lines.append(f"      ({self.body_length_mm:.1f}mm x {self.body_width_mm:.1f}mm)")

        if self.upper_bout_width_inches:
            lines.append(f"Upper Bout: {self.upper_bout_width_inches:.2f}\"")
        if self.lower_bout_width_inches:
            lines.append(f"Lower Bout: {self.lower_bout_width_inches:.2f}\"")
        if self.waist_width_inches:
            lines.append(f"Waist: {self.waist_width_inches:.2f}\"")

        if self.calibration_method:
            lines.append(f"Calibration: {self.calibration_method} (PPI: {self.ppi:.1f}, conf: {self.calibration_confidence:.0%})")

        if self.warnings:
            lines.append("Warnings:")
            for w in self.warnings:
                lines.append(f"  - {w}")

        return "\n".join(lines)


class CalibratedDimensionExtractor:
    """
    Extracts dimensions from guitar blueprints using pixel calibration.

    Usage:
        extractor = CalibratedDimensionExtractor()

        # Extract with auto-calibration
        dims = extractor.extract(image, name="Stratocaster")

        # Or with known scale length
        dims = extractor.extract(image, name="Les Paul", known_scale_length=24.75)

        # Or with manual calibration
        extractor.set_calibration(ppi=150.0)
        dims = extractor.extract(image)
    """

    def __init__(self):
        self.calibrator = PixelCalibrator()
        self.calibration: Optional[CalibrationResult] = None

    def set_calibration(self, ppi: float, method: str = "manual"):
        """Set manual calibration."""
        self.calibration = CalibrationResult(
            method=CalibrationMethod.KNOWN_DIMENSION,
            ppi=ppi,
            ppmm=ppi / 25.4,
            confidence=1.0,
            reference_name="manual",
            notes=[f"Manual calibration: {ppi} PPI"]
        )

    def extract(
        self,
        image: np.ndarray,
        name: str = "",
        source_file: str = "",
        known_scale_length: Optional[float] = None,
        paper_size: str = "letter",
        calibration_method: str = "auto"
    ) -> GuitarDimensions:
        """
        Extract dimensions from blueprint image.

        Args:
            image: OpenCV BGR image
            name: Guitar name for identification
            source_file: Source file name
            known_scale_length: Known scale length if available
            paper_size: Assumed paper size for calibration
            calibration_method: "auto", "paper", "body_heuristic", "scale"

        Returns:
            GuitarDimensions with extracted measurements
        """
        dims = GuitarDimensions(name=name, source_file=source_file)
        height, width = image.shape[:2]

        # Step 1: Calibrate
        if self.calibration:
            cal = self.calibration
        else:
            # Use the specified calibration method (or auto)
            # known_scale_length is stored separately but doesn't override method
            cal = self.calibrator.calibrate(
                image,
                method=calibration_method,
                paper_size=paper_size,
                known_scale_length=known_scale_length
            )

        dims.calibration_method = cal.method.value
        dims.ppi = cal.ppi
        dims.calibration_confidence = cal.confidence

        if known_scale_length:
            dims.scale_length_inches = known_scale_length
            dims.scale_length_mm = known_scale_length * 25.4

        # Step 2: Find body contour
        body_contour, body_bbox = self._find_body_contour(image)

        if body_contour is None:
            dims.warnings.append("Could not detect body contour")
            return dims

        x, y, w, h = body_bbox
        dims.pixel_measurements['body_bbox_x'] = float(x)
        dims.pixel_measurements['body_bbox_y'] = float(y)
        dims.pixel_measurements['body_width_px'] = float(w)
        dims.pixel_measurements['body_height_px'] = float(h)

        # Step 3: Calculate body dimensions
        # Determine orientation - body length is the longer dimension
        if h > w:
            # Portrait - height is length
            dims.body_length_inches = cal.pixels_to_inches(h)
            dims.body_width_inches = cal.pixels_to_inches(w)
        else:
            # Landscape - width is length
            dims.body_length_inches = cal.pixels_to_inches(w)
            dims.body_width_inches = cal.pixels_to_inches(h)

        dims.body_length_mm = dims.body_length_inches * 25.4
        dims.body_width_mm = dims.body_width_inches * 25.4

        if dims.body_width_inches > 0:
            dims.body_aspect_ratio = dims.body_length_inches / dims.body_width_inches

        # Step 4: Measure bout widths
        bout_measurements = self._measure_bouts(image, body_contour, body_bbox)

        if bout_measurements:
            if 'upper_bout_px' in bout_measurements:
                upper_px = bout_measurements['upper_bout_px']
                dims.upper_bout_width_inches = cal.pixels_to_inches(upper_px)
                dims.upper_bout_width_mm = dims.upper_bout_width_inches * 25.4
                dims.pixel_measurements['upper_bout_px'] = upper_px

            if 'lower_bout_px' in bout_measurements:
                lower_px = bout_measurements['lower_bout_px']
                dims.lower_bout_width_inches = cal.pixels_to_inches(lower_px)
                dims.lower_bout_width_mm = dims.lower_bout_width_inches * 25.4
                dims.pixel_measurements['lower_bout_px'] = lower_px

            if 'waist_px' in bout_measurements:
                waist_px = bout_measurements['waist_px']
                dims.waist_width_inches = cal.pixels_to_inches(waist_px)
                dims.waist_width_mm = dims.waist_width_inches * 25.4
                dims.pixel_measurements['waist_px'] = waist_px

        # Calculate bout ratio
        if dims.upper_bout_width_inches and dims.lower_bout_width_inches:
            dims.upper_to_lower_bout_ratio = dims.upper_bout_width_inches / dims.lower_bout_width_inches

        # Step 5: Validate dimensions
        self._validate_dimensions(dims)

        # Add notes
        dims.notes.append(f"Calibration: {cal.method.value}")
        dims.notes.extend(cal.notes)

        return dims

    def _find_body_contour(
        self,
        image: np.ndarray
    ) -> Tuple[Optional[np.ndarray], Optional[Tuple[int, int, int, int]]]:
        """Find the main guitar body contour."""
        height, width = image.shape[:2]

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Threshold
        _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)

        # Clean up
        kernel = np.ones((3, 3), np.uint8)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)

        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            # Try edge detection
            edges = cv2.Canny(gray, 50, 150)
            edges = cv2.dilate(edges, kernel, iterations=2)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            return None, None

        # Find largest contour that's at least 5% of image area
        min_area = (width * height) * 0.05
        valid_contours = [c for c in contours if cv2.contourArea(c) > min_area]

        if not valid_contours:
            valid_contours = contours

        largest = max(valid_contours, key=cv2.contourArea)
        bbox = cv2.boundingRect(largest)

        return largest, bbox

    def _measure_bouts(
        self,
        image: np.ndarray,
        contour: np.ndarray,
        bbox: Tuple[int, int, int, int]
    ) -> Dict[str, float]:
        """
        Measure upper bout, lower bout, and waist widths.

        For a typical guitar body:
        - Upper bout: widest point in upper 1/3
        - Lower bout: widest point in lower 1/3
        - Waist: narrowest point in middle 1/3
        """
        height, width = image.shape[:2]
        x, y, w, h = bbox

        # Create mask from contour
        mask = np.zeros((height, width), dtype=np.uint8)
        cv2.drawContours(mask, [contour], -1, 255, -1)

        measurements = {}

        # Divide body into thirds
        third_h = h // 3

        # Measure width at each row and find extremes
        widths = []
        for row_offset in range(h):
            row_y = y + row_offset
            if 0 <= row_y < height:
                row = mask[row_y, x:x+w]
                nonzero = np.where(row > 0)[0]
                if len(nonzero) > 0:
                    row_width = nonzero[-1] - nonzero[0]
                    widths.append((row_offset, row_width))

        if not widths:
            return measurements

        # Upper third (neck end)
        upper_widths = [(off, wid) for off, wid in widths if off < third_h]
        if upper_widths:
            _, max_upper = max(upper_widths, key=lambda x: x[1])
            measurements['upper_bout_px'] = float(max_upper)

        # Lower third (bridge end)
        lower_widths = [(off, wid) for off, wid in widths if off > 2 * third_h]
        if lower_widths:
            _, max_lower = max(lower_widths, key=lambda x: x[1])
            measurements['lower_bout_px'] = float(max_lower)

        # Middle third (waist)
        middle_widths = [(off, wid) for off, wid in widths if third_h <= off <= 2 * third_h]
        if middle_widths:
            _, min_middle = min(middle_widths, key=lambda x: x[1])
            measurements['waist_px'] = float(min_middle)

        return measurements

    def _validate_dimensions(self, dims: GuitarDimensions):
        """Add warnings for unusual dimensions."""
        # Body length typically 14-22 inches for electric guitars
        if dims.body_length_inches:
            if dims.body_length_inches < 12:
                dims.warnings.append(f"Body length ({dims.body_length_inches:.1f}\") seems too short")
            elif dims.body_length_inches > 24:
                dims.warnings.append(f"Body length ({dims.body_length_inches:.1f}\") seems too long")

        # Body width typically 10-16 inches
        if dims.body_width_inches:
            if dims.body_width_inches < 8:
                dims.warnings.append(f"Body width ({dims.body_width_inches:.1f}\") seems too narrow")
            elif dims.body_width_inches > 20:
                dims.warnings.append(f"Body width ({dims.body_width_inches:.1f}\") seems too wide")

        # Aspect ratio typically 1.2-1.6 for guitar bodies
        if dims.body_aspect_ratio:
            if dims.body_aspect_ratio < 1.0:
                dims.warnings.append("Body appears wider than long (unusual)")
            elif dims.body_aspect_ratio > 2.0:
                dims.warnings.append("Body appears very elongated")

        # Lower bout should be wider than upper for most guitars
        if dims.upper_to_lower_bout_ratio and dims.upper_to_lower_bout_ratio > 1.1:
            dims.warnings.append("Upper bout wider than lower (unusual for electric guitar)")

    def extract_batch(
        self,
        images: List[Tuple[np.ndarray, str, str]],
        **kwargs
    ) -> List[GuitarDimensions]:
        """
        Extract dimensions from multiple images.

        Args:
            images: List of (image, name, source_file) tuples
            **kwargs: Arguments passed to extract()

        Returns:
            List of GuitarDimensions
        """
        results = []
        for image, name, source_file in images:
            dims = self.extract(image, name=name, source_file=source_file, **kwargs)
            results.append(dims)
        return results
