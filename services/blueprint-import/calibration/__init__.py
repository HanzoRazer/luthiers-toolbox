"""
Blueprint Calibration Module
============================

Provides pixel-to-real-world dimension calibration for guitar blueprints.

Methods:
1. Scale reference detection (find labeled scale length)
2. Ruler/grid detection (find measurement rulers)
3. Known dimension calibration (user provides reference)
4. Standard paper size detection (A4, Letter, etc.)

Author: The Production Shop
Version: 4.0.0
"""

from .pixel_calibrator import (
    PixelCalibrator,
    CalibrationResult,
    CalibrationMethod,
)
from .scale_detector import (
    ScaleReferenceDetector,
    ScaleReference,
)
from .dimension_extractor import (
    CalibratedDimensionExtractor,
    GuitarDimensions,
)

__all__ = [
    'PixelCalibrator',
    'CalibrationResult',
    'CalibrationMethod',
    'ScaleReferenceDetector',
    'ScaleReference',
    'CalibratedDimensionExtractor',
    'GuitarDimensions',
]
