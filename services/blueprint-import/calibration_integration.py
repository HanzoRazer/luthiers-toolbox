"""
Calibration Integration Module
==============================

Integrates the pixel calibration module with the Phase 3 vectorizer.

Provides:
- Enhanced scale detection using multiple calibration methods
- Dimension extraction pipeline
- Quality assessment for calibration results

Author: The Production Shop
Version: 4.0.0
"""

import logging
from typing import Dict, Optional, Tuple, List
from pathlib import Path
import numpy as np
import cv2

from calibration import (
    PixelCalibrator,
    CalibrationResult,
    CalibrationMethod,
    ScaleReferenceDetector,
    CalibratedDimensionExtractor,
    GuitarDimensions,
)

logger = logging.getLogger(__name__)


class EnhancedCalibrationPipeline:
    """
    Enhanced calibration pipeline that combines multiple calibration methods.

    Calibration priority:
    1. Known dimension (user-provided reference)
    2. Scale length detection (if hint provided)
    3. Ruler/grid detection (automated)
    4. Paper size estimation (fallback)
    5. Body heuristic (last resort)

    Usage:
        pipeline = EnhancedCalibrationPipeline()

        # With known scale length
        result = pipeline.calibrate(image, known_scale_length=25.5)

        # Auto-detect from image
        result = pipeline.calibrate(image)

        # Extract dimensions
        dims = pipeline.extract_dimensions(image, name="Stratocaster")
    """

    def __init__(self):
        self.calibrator = PixelCalibrator()
        self.scale_detector = ScaleReferenceDetector()
        self.dimension_extractor = CalibratedDimensionExtractor()
        self.last_calibration: Optional[CalibrationResult] = None

    def calibrate(
        self,
        image: np.ndarray,
        known_scale_length: Optional[float] = None,
        known_reference: Optional[Tuple[float, float, str]] = None,
        paper_size: str = "letter",
        prefer_method: Optional[str] = None,
    ) -> CalibrationResult:
        """
        Perform enhanced calibration using multiple methods.

        Args:
            image: OpenCV BGR image
            known_scale_length: Known scale length in inches (e.g., 25.5 for Fender)
            known_reference: Tuple of (pixels, inches, name) for manual calibration
            paper_size: Assumed paper size for fallback
            prefer_method: Force a specific method ("paper", "scale", "body_heuristic")

        Returns:
            CalibrationResult with best calibration found
        """
        height, width = image.shape[:2]

        # Priority 1: User-provided reference dimension
        if known_reference:
            pixels, inches, name = known_reference
            result = self.calibrator.calibrate_from_reference(pixels, inches, name)
            result.notes.append("User-provided reference dimension")
            self.last_calibration = result
            return result

        # Priority 2: Scale length detection with hint
        if known_scale_length:
            scale_ref = self.scale_detector.detect(
                image,
                hint_scale=known_scale_length,
            )
            if scale_ref and scale_ref.confidence > 0.5:
                ppi = scale_ref.pixel_length / known_scale_length
                result = CalibrationResult(
                    method=CalibrationMethod.SCALE_LENGTH,
                    ppi=ppi,
                    ppmm=ppi / 25.4,
                    confidence=scale_ref.confidence,
                    reference_name="scale_length",
                    reference_value_inches=known_scale_length,
                    reference_pixels=scale_ref.pixel_length,
                    notes=[
                        f"Scale length detected: {known_scale_length}\" = {scale_ref.pixel_length:.0f}px",
                        f"Method: {scale_ref.detection_method}",
                    ],
                )
                self.last_calibration = result
                return result

        # Priority 3: Try preferred method if specified
        if prefer_method:
            result = self.calibrator.calibrate(
                image,
                method=prefer_method,
                paper_size=paper_size,
                known_scale_length=known_scale_length,
            )
            self.last_calibration = result
            return result

        # Priority 4: Auto-detect (tries scale, ruler, then paper size)
        result = self.calibrator.calibrate(
            image,
            method="auto",
            paper_size=paper_size,
            known_scale_length=known_scale_length,
        )
        self.last_calibration = result
        return result

    def extract_dimensions(
        self,
        image: np.ndarray,
        name: str = "",
        source_file: str = "",
        known_scale_length: Optional[float] = None,
        use_cached_calibration: bool = False,
    ) -> GuitarDimensions:
        """
        Extract dimensions from guitar blueprint.

        Args:
            image: OpenCV BGR image
            name: Guitar name for identification
            source_file: Source file name
            known_scale_length: Known scale length if available
            use_cached_calibration: Use last calibration instead of re-calibrating

        Returns:
            GuitarDimensions with extracted measurements
        """
        if use_cached_calibration and self.last_calibration:
            self.dimension_extractor.set_calibration(
                self.last_calibration.ppi,
                self.last_calibration.method.value
            )

        return self.dimension_extractor.extract(
            image,
            name=name,
            source_file=source_file,
            known_scale_length=known_scale_length,
        )

    def get_calibration_quality(self, dims: GuitarDimensions) -> Dict:
        """
        Assess the quality of a dimension extraction result.

        Returns dict with:
            - quality: "good", "uncertain", "poor"
            - confidence: float 0-1
            - issues: list of detected problems
            - recommendations: list of suggested improvements
        """
        issues = []
        recommendations = []

        # Check body dimensions
        body_len = dims.body_length_inches or 0
        body_wid = dims.body_width_inches or 0

        # Expected ranges for electric guitar bodies
        if body_len < 14 or body_len > 22:
            issues.append(f"Body length {body_len:.1f}\" outside typical range (14-22\")")
            recommendations.append("Verify calibration with known reference dimension")

        if body_wid < 10 or body_wid > 16:
            issues.append(f"Body width {body_wid:.1f}\" outside typical range (10-16\")")
            recommendations.append("Check contour detection - may have found wrong element")

        # Check pixel measurements
        px_w = dims.pixel_measurements.get("body_width_px", 0)
        px_h = dims.pixel_measurements.get("body_height_px", 0)

        if max(px_w, px_h) < 200:
            issues.append(f"Very small contour detected ({px_h:.0f}x{px_w:.0f}px)")
            recommendations.append("Blueprint may be a thumbnail or wrong element was found")

        # Check aspect ratio
        if dims.body_aspect_ratio:
            if dims.body_aspect_ratio < 1.0:
                issues.append("Body appears wider than long (unusual)")
            elif dims.body_aspect_ratio > 2.0:
                issues.append("Body appears very elongated")

        # Check calibration confidence
        confidence = dims.calibration_confidence

        # Determine overall quality
        if len(issues) == 0 and confidence > 0.7:
            quality = "good"
        elif len(issues) <= 1 and confidence > 0.4:
            quality = "uncertain"
        else:
            quality = "poor"

        # Add dimension-specific recommendations
        if dims.calibration_method == "paper_size" and confidence < 0.5:
            recommendations.append("Consider providing known scale length for better accuracy")

        if dims.calibration_method == "body_heuristic":
            recommendations.append("Body heuristic has low reliability - provide reference dimension if possible")

        return {
            "quality": quality,
            "confidence": confidence,
            "issues": issues,
            "recommendations": recommendations,
            "calibration_method": dims.calibration_method,
        }


def integrate_with_vectorizer(
    vectorizer,
    image: np.ndarray,
    known_scale_length: Optional[float] = None,
) -> Tuple[float, Dict]:
    """
    Integration function for Phase 3 vectorizer.

    Call this from the vectorizer to get enhanced calibration:

        from calibration_integration import integrate_with_vectorizer

        scale_factor, cal_info = integrate_with_vectorizer(
            self,
            image,
            known_scale_length=known_scale
        )

    Args:
        vectorizer: Phase 3 vectorizer instance (for accessing mm_per_px)
        image: OpenCV BGR image
        known_scale_length: Optional scale length hint

    Returns:
        Tuple of (scale_factor, calibration_info_dict)
    """
    pipeline = EnhancedCalibrationPipeline()

    # Calibrate
    calibration = pipeline.calibrate(
        image,
        known_scale_length=known_scale_length,
    )

    # Calculate scale factor relative to vectorizer's mm_per_px
    # If vectorizer assumes 300 DPI (0.0847 mm/px), and calibration says 150 PPI:
    # scale_factor = (1/150 * 25.4) / 0.0847 = 2.0
    if hasattr(vectorizer, 'mm_per_px'):
        calibrated_mm_per_px = 25.4 / calibration.ppi
        scale_factor = calibrated_mm_per_px / vectorizer.mm_per_px
    else:
        scale_factor = 1.0

    cal_info = {
        "method": calibration.method.value,
        "ppi": calibration.ppi,
        "confidence": calibration.confidence,
        "scale_factor": scale_factor,
        "notes": calibration.notes,
    }

    return scale_factor, cal_info


# Convenience function for standalone use
def calibrate_blueprint(
    image_path: str,
    known_scale_length: Optional[float] = None,
) -> Dict:
    """
    Quick calibration function for standalone use.

    Args:
        image_path: Path to blueprint image
        known_scale_length: Optional scale length hint

    Returns:
        Dict with calibration results and extracted dimensions
    """
    image = cv2.imread(image_path)
    if image is None:
        return {"error": f"Could not load image: {image_path}"}

    pipeline = EnhancedCalibrationPipeline()

    # Calibrate
    calibration = pipeline.calibrate(image, known_scale_length=known_scale_length)

    # Extract dimensions
    name = Path(image_path).stem
    dims = pipeline.extract_dimensions(
        image,
        name=name,
        source_file=image_path,
        known_scale_length=known_scale_length,
        use_cached_calibration=True,
    )

    # Get quality assessment
    quality = pipeline.get_calibration_quality(dims)

    return {
        "calibration": calibration.to_dict(),
        "dimensions": dims.to_dict(),
        "quality": quality,
    }
