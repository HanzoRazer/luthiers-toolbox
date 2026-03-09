"""
Pixel Calibrator
================

Calculates pixels-per-inch (PPI) ratio from known reference dimensions,
enabling conversion of pixel measurements to real-world units.

Calibration Methods:
1. SCALE_LENGTH - Use labeled scale length (e.g., "25.5 scale")
2. RULER - Detect ruler markings in image
3. PAPER_SIZE - Assume standard paper size (A4, Letter)
4. KNOWN_DIMENSION - User-provided reference
5. GRID - Use STEM Guitar grid (known cell size)

Author: The Production Shop
Version: 4.0.0
"""

import cv2
import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class CalibrationMethod(Enum):
    """Available calibration methods."""
    SCALE_LENGTH = "scale_length"      # Detected scale length reference
    RULER = "ruler"                     # Detected ruler markings
    PAPER_SIZE = "paper_size"           # Assumed paper size
    KNOWN_DIMENSION = "known_dimension" # User-provided reference
    GRID = "grid"                       # STEM Guitar grid cells
    BODY_HEURISTIC = "body_heuristic"   # Assume typical body proportions
    UNCALIBRATED = "uncalibrated"       # No calibration available


# Standard paper sizes in inches
PAPER_SIZES = {
    "letter": (8.5, 11.0),
    "legal": (8.5, 14.0),
    "tabloid": (11.0, 17.0),
    "a4": (8.27, 11.69),
    "a3": (11.69, 16.54),
    "a2": (16.54, 23.39),
    "a1": (23.39, 33.11),
    "a0": (33.11, 46.81),
    "arch_d": (24.0, 36.0),  # Common for blueprints
    "arch_e": (36.0, 48.0),
}

# Common guitar scale lengths in inches
COMMON_SCALE_LENGTHS = {
    24.0: "Fender Jaguar/Mustang",
    24.75: "Gibson",
    25.0: "PRS",
    25.5: "Fender Stratocaster",
    26.5: "Baritone",
    27.0: "Extended Range 7-string",
    30.0: "Bass VI",
    34.0: "Standard Bass",
}

# Typical electric guitar body dimensions (for heuristic calibration)
TYPICAL_BODY_DIMENSIONS = {
    "stratocaster": {"length": 17.75, "width": 12.75},
    "les_paul": {"length": 17.5, "width": 13.0},
    "telecaster": {"length": 15.75, "width": 12.5},
    "sg": {"length": 15.5, "width": 13.5},
    "explorer": {"length": 18.0, "width": 15.0},
    "flying_v": {"length": 21.0, "width": 19.0},
    "default": {"length": 17.0, "width": 13.0},
}


@dataclass
class CalibrationResult:
    """Result of pixel calibration."""
    method: CalibrationMethod
    ppi: float  # Pixels per inch
    ppmm: float  # Pixels per mm
    confidence: float  # 0-1 confidence score

    # Reference used for calibration
    reference_name: str = ""
    reference_value_inches: float = 0.0
    reference_pixels: float = 0.0

    # Detected orientation
    orientation: str = "portrait"  # portrait or landscape

    # Notes about calibration
    notes: List[str] = field(default_factory=list)

    def pixels_to_inches(self, pixels: float) -> float:
        """Convert pixels to inches."""
        return pixels / self.ppi if self.ppi > 0 else 0.0

    def pixels_to_mm(self, pixels: float) -> float:
        """Convert pixels to millimeters."""
        return pixels / self.ppmm if self.ppmm > 0 else 0.0

    def inches_to_pixels(self, inches: float) -> float:
        """Convert inches to pixels."""
        return inches * self.ppi

    def to_dict(self) -> Dict:
        return {
            "method": self.method.value,
            "ppi": round(self.ppi, 2),
            "ppmm": round(self.ppmm, 2),
            "confidence": round(self.confidence, 3),
            "reference_name": self.reference_name,
            "reference_value_inches": self.reference_value_inches,
            "reference_pixels": self.reference_pixels,
            "orientation": self.orientation,
            "notes": self.notes,
        }


class PixelCalibrator:
    """
    Calibrates pixel measurements to real-world units.

    Usage:
        calibrator = PixelCalibrator()

        # Auto-calibrate from image
        result = calibrator.calibrate(image, method="auto")

        # Or provide known reference
        result = calibrator.calibrate_from_reference(
            reference_pixels=500,
            reference_inches=25.5,
            reference_name="scale_length"
        )

        # Convert measurements
        body_length_inches = result.pixels_to_inches(body_length_px)
    """

    def __init__(self):
        self.last_calibration: Optional[CalibrationResult] = None

    def calibrate(
        self,
        image: np.ndarray,
        method: str = "auto",
        paper_size: str = "letter",
        known_scale_length: Optional[float] = None,
    ) -> CalibrationResult:
        """
        Calibrate pixel-to-inch ratio from image.

        Args:
            image: OpenCV BGR image
            method: "auto", "paper", "scale", "ruler", "body_heuristic"
            paper_size: Paper size if using paper method
            known_scale_length: Known scale length if available

        Returns:
            CalibrationResult with PPI and conversion methods
        """
        height, width = image.shape[:2]
        orientation = "landscape" if width > height else "portrait"

        if method == "auto":
            # Try methods in order of preference
            result = self._try_scale_detection(image)
            if result and result.confidence > 0.7:
                result.orientation = orientation
                return result

            result = self._try_ruler_detection(image)
            if result and result.confidence > 0.7:
                result.orientation = orientation
                return result

            # Fall back to paper size estimation
            result = self._calibrate_from_paper_size(width, height, paper_size)
            result.orientation = orientation
            return result

        elif method == "paper":
            result = self._calibrate_from_paper_size(width, height, paper_size)
            result.orientation = orientation
            return result

        elif method == "scale" and known_scale_length:
            # Try to find scale length reference in image
            result = self._try_scale_detection(image, expected_scale=known_scale_length)
            if result:
                result.orientation = orientation
                return result
            # Fall back to body heuristic
            return self._calibrate_from_body_heuristic(image, known_scale_length)

        elif method == "body_heuristic":
            return self._calibrate_from_body_heuristic(image)

        else:
            # Return uncalibrated result
            return CalibrationResult(
                method=CalibrationMethod.UNCALIBRATED,
                ppi=72.0,  # Default screen DPI
                ppmm=72.0 / 25.4,
                confidence=0.0,
                notes=["No calibration method succeeded"]
            )

    def calibrate_from_reference(
        self,
        reference_pixels: float,
        reference_inches: float,
        reference_name: str = "user_reference"
    ) -> CalibrationResult:
        """
        Calibrate using a known reference dimension.

        Args:
            reference_pixels: Length of reference in pixels
            reference_inches: Actual length in inches
            reference_name: Name of the reference (for logging)

        Returns:
            CalibrationResult
        """
        if reference_pixels <= 0 or reference_inches <= 0:
            return CalibrationResult(
                method=CalibrationMethod.UNCALIBRATED,
                ppi=72.0,
                ppmm=72.0 / 25.4,
                confidence=0.0,
                notes=["Invalid reference values"]
            )

        ppi = reference_pixels / reference_inches

        return CalibrationResult(
            method=CalibrationMethod.KNOWN_DIMENSION,
            ppi=ppi,
            ppmm=ppi / 25.4,
            confidence=1.0,
            reference_name=reference_name,
            reference_value_inches=reference_inches,
            reference_pixels=reference_pixels,
            notes=[f"Calibrated from {reference_name}: {reference_inches}\" = {reference_pixels}px"]
        )

    def calibrate_from_grid(
        self,
        image: np.ndarray,
        grid_cell_inches: float = 0.5,
    ) -> CalibrationResult:
        """
        Calibrate using detected grid cells (like STEM Guitar grid).

        Args:
            image: Image with visible grid
            grid_cell_inches: Known size of grid cells

        Returns:
            CalibrationResult
        """
        # Detect grid line spacing
        cell_pixels = self._detect_grid_spacing(image)

        if cell_pixels > 0:
            ppi = cell_pixels / grid_cell_inches
            return CalibrationResult(
                method=CalibrationMethod.GRID,
                ppi=ppi,
                ppmm=ppi / 25.4,
                confidence=0.85,
                reference_name="grid_cell",
                reference_value_inches=grid_cell_inches,
                reference_pixels=cell_pixels,
                notes=[f"Grid cell: {grid_cell_inches}\" = {cell_pixels:.1f}px"]
            )

        return CalibrationResult(
            method=CalibrationMethod.UNCALIBRATED,
            ppi=72.0,
            ppmm=72.0 / 25.4,
            confidence=0.0,
            notes=["Grid detection failed"]
        )

    def _calibrate_from_paper_size(
        self,
        width_px: int,
        height_px: int,
        paper_size: str
    ) -> CalibrationResult:
        """Estimate PPI from assumed paper size."""
        if paper_size.lower() not in PAPER_SIZES:
            paper_size = "letter"

        paper_w, paper_h = PAPER_SIZES[paper_size.lower()]

        # Determine orientation
        if width_px > height_px:
            # Landscape
            ppi_w = width_px / paper_h
            ppi_h = height_px / paper_w
        else:
            # Portrait
            ppi_w = width_px / paper_w
            ppi_h = height_px / paper_h

        # Average and use
        ppi = (ppi_w + ppi_h) / 2

        # Confidence based on how close aspect ratios match
        image_aspect = width_px / height_px
        paper_aspect = paper_w / paper_h
        aspect_diff = abs(image_aspect - paper_aspect) / paper_aspect
        confidence = max(0.3, 1.0 - aspect_diff)

        return CalibrationResult(
            method=CalibrationMethod.PAPER_SIZE,
            ppi=ppi,
            ppmm=ppi / 25.4,
            confidence=confidence,
            reference_name=f"paper_{paper_size}",
            reference_value_inches=paper_w,
            reference_pixels=width_px if width_px < height_px else height_px,
            notes=[
                f"Assumed {paper_size.upper()} paper ({paper_w}\" x {paper_h}\")",
                f"Calculated PPI: {ppi:.1f}"
            ]
        )

    def _calibrate_from_body_heuristic(
        self,
        image: np.ndarray,
        known_scale_length: Optional[float] = None
    ) -> CalibrationResult:
        """
        Estimate PPI by assuming detected body is typical guitar size.
        """
        height, width = image.shape[:2]

        # Find largest contour (assume it's guitar body)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)

        kernel = np.ones((3, 3), np.uint8)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)

        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            return CalibrationResult(
                method=CalibrationMethod.UNCALIBRATED,
                ppi=72.0,
                ppmm=72.0 / 25.4,
                confidence=0.0,
                notes=["No body contour found for heuristic calibration"]
            )

        # Get largest contour
        largest = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest)

        # Use typical body dimensions
        typical = TYPICAL_BODY_DIMENSIONS["default"]

        # Assume the larger dimension is body length
        if h > w:
            # Portrait orientation - height is length
            ppi = h / typical["length"]
            ref_dim = "body_length"
            ref_value = typical["length"]
            ref_px = h
        else:
            # Landscape or body viewed from side
            ppi = w / typical["length"]
            ref_dim = "body_length"
            ref_value = typical["length"]
            ref_px = w

        return CalibrationResult(
            method=CalibrationMethod.BODY_HEURISTIC,
            ppi=ppi,
            ppmm=ppi / 25.4,
            confidence=0.4,  # Low confidence for heuristic
            reference_name=ref_dim,
            reference_value_inches=ref_value,
            reference_pixels=ref_px,
            notes=[
                f"Assumed typical body {ref_dim}: {ref_value}\"",
                f"Body contour: {w}x{h}px",
                "Low confidence - heuristic estimate"
            ]
        )

    def _try_scale_detection(
        self,
        image: np.ndarray,
        expected_scale: Optional[float] = None
    ) -> Optional[CalibrationResult]:
        """
        Try to detect scale length reference in image.

        Looks for horizontal lines that could be scale length markings.
        """
        # This would integrate with OCR if available
        # For now, return None to fall back to other methods
        return None

    def _try_ruler_detection(self, image: np.ndarray) -> Optional[CalibrationResult]:
        """
        Try to detect ruler markings in image.

        Looks for evenly spaced tick marks.
        """
        # Detect lines
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)

        # Look for regular patterns that could be ruler ticks
        # This is a simplified implementation

        # Find horizontal lines
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, 50, minLineLength=30, maxLineGap=5)

        if lines is None or len(lines) < 10:
            return None

        # Look for evenly spaced vertical lines (ruler ticks)
        vertical_lines = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            angle = abs(np.arctan2(y2 - y1, x2 - x1))
            if angle > np.pi/4:  # More vertical than horizontal
                vertical_lines.append((x1 + x2) / 2)

        if len(vertical_lines) < 5:
            return None

        # Sort and find spacing
        vertical_lines.sort()
        spacings = np.diff(vertical_lines)

        # Look for consistent spacing
        median_spacing = np.median(spacings)
        consistent = [s for s in spacings if abs(s - median_spacing) < median_spacing * 0.2]

        if len(consistent) < 3:
            return None

        avg_spacing = np.mean(consistent)

        # Assume 1-inch tick marks (common on blueprints)
        ppi = avg_spacing

        return CalibrationResult(
            method=CalibrationMethod.RULER,
            ppi=ppi,
            ppmm=ppi / 25.4,
            confidence=0.6,
            reference_name="ruler_ticks",
            reference_value_inches=1.0,
            reference_pixels=avg_spacing,
            notes=[
                f"Detected ruler ticks at {avg_spacing:.1f}px spacing",
                "Assumed 1\" tick marks"
            ]
        )

    def _detect_grid_spacing(self, image: np.ndarray) -> float:
        """Detect grid cell spacing in pixels."""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Find grid lines using FFT or line detection
        edges = cv2.Canny(gray, 30, 100)

        # Project to find line positions
        h_proj = np.sum(edges, axis=1)
        v_proj = np.sum(edges, axis=0)

        # Find peaks (grid lines)
        def find_spacing(projection):
            threshold = np.mean(projection) + np.std(projection)
            peaks = np.where(projection > threshold)[0]
            if len(peaks) < 3:
                return 0
            spacings = np.diff(peaks)
            # Filter outliers
            median = np.median(spacings)
            valid = [s for s in spacings if 0.5 * median < s < 1.5 * median]
            return np.mean(valid) if valid else 0

        h_spacing = find_spacing(h_proj)
        v_spacing = find_spacing(v_proj)

        if h_spacing > 0 and v_spacing > 0:
            return (h_spacing + v_spacing) / 2
        return max(h_spacing, v_spacing)
