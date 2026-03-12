"""
Blueprint Calibration Router
=============================

Pixel calibration endpoints for accurate dimension extraction from blueprints.

Endpoints:
- POST /calibrate: Auto-calibrate image, return PPI + confidence
- POST /calibrate/manual: User provides two points + real measurement
- POST /dimensions: Extract dimensions using calibration
- GET /calibration/{calibration_id}: Retrieve stored calibration

Author: Production Shop
"""

import base64
import io
import logging
import tempfile
import uuid
from pathlib import Path
from typing import Dict, Optional

import cv2
import numpy as np
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from .constants import CALIBRATION_AVAILABLE, create_calibration_pipeline

logger = logging.getLogger(__name__)
router = APIRouter(tags=["blueprint-calibration"])

# In-memory calibration cache (for session persistence)
# In production, use Redis or database
_calibration_cache: Dict[str, dict] = {}


# =============================================================================
# SCHEMAS
# =============================================================================

class CalibrationRequest(BaseModel):
    """Request for auto-calibration."""
    known_scale_length: Optional[float] = Field(
        None, description="Known scale length in inches (e.g., 25.5 for Fender)"
    )
    paper_size: str = Field(
        "letter", description="Assumed paper size: letter, a4, tabloid"
    )
    prefer_method: str = Field(
        "auto", description="Calibration method: auto, paper, scale, body_heuristic"
    )


class ManualCalibrationRequest(BaseModel):
    """Request for manual two-point calibration."""
    point1_x: float = Field(..., description="First point X coordinate (pixels)")
    point1_y: float = Field(..., description="First point Y coordinate (pixels)")
    point2_x: float = Field(..., description="Second point X coordinate (pixels)")
    point2_y: float = Field(..., description="Second point Y coordinate (pixels)")
    real_dimension: float = Field(..., description="Real-world distance (inches)")
    dimension_name: str = Field(
        "user_reference", description="Name of the reference dimension"
    )


class CalibrationResponse(BaseModel):
    """Calibration result."""
    calibration_id: str
    method: str
    ppi: float
    ppmm: float
    confidence: float
    reference_name: Optional[str] = None
    reference_value_inches: Optional[float] = None
    reference_pixels: Optional[float] = None
    notes: list = []


class DimensionRequest(BaseModel):
    """Request for dimension extraction."""
    calibration_id: str = Field(..., description="Calibration ID from /calibrate")
    name: str = Field("", description="Guitar name for identification")


class DimensionResponse(BaseModel):
    """Extracted dimensions."""
    name: str
    body_length_inches: Optional[float] = None
    body_width_inches: Optional[float] = None
    body_length_mm: Optional[float] = None
    body_width_mm: Optional[float] = None
    upper_bout_width_inches: Optional[float] = None
    lower_bout_width_inches: Optional[float] = None
    waist_width_inches: Optional[float] = None
    scale_length_inches: Optional[float] = None
    body_aspect_ratio: Optional[float] = None
    calibration_method: str = ""
    calibration_confidence: float = 0.0
    pixel_measurements: dict = {}
    warnings: list = []


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _decode_image(file_bytes: bytes) -> np.ndarray:
    """Decode uploaded file to OpenCV image."""
    nparr = np.frombuffer(file_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(status_code=400, detail="Could not decode image")
    return img


def _calculate_pixel_distance(x1: float, y1: float, x2: float, y2: float) -> float:
    """Calculate Euclidean distance between two points."""
    return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/calibrate", response_model=CalibrationResponse)
async def calibrate_blueprint(
    file: UploadFile = File(...),
    known_scale_length: Optional[float] = Form(None),
    paper_size: str = Form("letter"),
    prefer_method: str = Form("auto"),
):
    """
    Auto-calibrate blueprint image to determine pixels-per-inch (PPI).

    Calibration methods (priority order):
    1. Scale length detection (if known_scale_length provided)
    2. Ruler/grid detection (automated)
    3. Paper size estimation (fallback)
    4. Body heuristic (last resort)

    Args:
        file: Blueprint image (PNG, JPG, JPEG)
        known_scale_length: Known scale length in inches (optional)
        paper_size: Assumed paper size for fallback (letter, a4, tabloid)
        prefer_method: Force specific method (auto, paper, scale, body_heuristic)

    Returns:
        CalibrationResponse with PPI, confidence, and method used
    """
    if not CALIBRATION_AVAILABLE:
        raise HTTPException(
            status_code=501,
            detail="Calibration module not available. Check blueprint-import installation."
        )

    # Read and decode image
    contents = await file.read()
    image = _decode_image(contents)

    # Create calibration pipeline
    pipeline = create_calibration_pipeline()

    # Run calibration
    try:
        calibration = pipeline.calibrate(
            image,
            known_scale_length=known_scale_length,
            paper_size=paper_size,
            prefer_method=prefer_method if prefer_method != "auto" else None,
        )
    except Exception as e:  # WP-2: API endpoint catch-all
        logger.exception("Calibration failed")
        raise HTTPException(status_code=500, detail=f"Calibration failed: {str(e)}")

    # Generate calibration ID and cache result
    calibration_id = str(uuid.uuid4())
    _calibration_cache[calibration_id] = {
        "calibration": calibration,
        "image_shape": image.shape,
    }

    return CalibrationResponse(
        calibration_id=calibration_id,
        method=calibration.method.value,
        ppi=calibration.ppi,
        ppmm=calibration.ppmm,
        confidence=calibration.confidence,
        reference_name=calibration.reference_name,
        reference_value_inches=calibration.reference_value_inches,
        reference_pixels=calibration.reference_pixels,
        notes=calibration.notes,
    )


@router.post("/calibrate/manual", response_model=CalibrationResponse)
async def manual_calibrate(
    file: UploadFile = File(...),
    point1_x: float = Form(...),
    point1_y: float = Form(...),
    point2_x: float = Form(...),
    point2_y: float = Form(...),
    real_dimension: float = Form(...),
    dimension_name: str = Form("user_reference"),
):
    """
    Manual two-point calibration.

    User clicks two points on a known dimension and provides the real measurement.
    System calculates PPI from the pixel distance and real dimension.

    Args:
        file: Blueprint image
        point1_x, point1_y: First point coordinates (pixels)
        point2_x, point2_y: Second point coordinates (pixels)
        real_dimension: Real-world distance in inches
        dimension_name: Name of the reference (e.g., "scale_length", "body_width")

    Returns:
        CalibrationResponse with calculated PPI (100% confidence)
    """
    if not CALIBRATION_AVAILABLE:
        raise HTTPException(
            status_code=501,
            detail="Calibration module not available."
        )

    # Read image for shape info
    contents = await file.read()
    image = _decode_image(contents)

    # Calculate pixel distance
    pixel_distance = _calculate_pixel_distance(point1_x, point1_y, point2_x, point2_y)

    if pixel_distance < 1:
        raise HTTPException(status_code=400, detail="Points too close together")

    if real_dimension <= 0:
        raise HTTPException(status_code=400, detail="Real dimension must be positive")

    # Calculate PPI
    ppi = pixel_distance / real_dimension
    ppmm = ppi / 25.4

    # Create calibration pipeline for result format
    pipeline = create_calibration_pipeline()
    calibration = pipeline.calibrator.calibrate_from_reference(
        pixel_distance, real_dimension, dimension_name
    )

    # Cache result
    calibration_id = str(uuid.uuid4())
    _calibration_cache[calibration_id] = {
        "calibration": calibration,
        "image_shape": image.shape,
        "manual": True,
        "points": [(point1_x, point1_y), (point2_x, point2_y)],
    }

    return CalibrationResponse(
        calibration_id=calibration_id,
        method="manual",
        ppi=ppi,
        ppmm=ppmm,
        confidence=1.0,  # Manual calibration is authoritative
        reference_name=dimension_name,
        reference_value_inches=real_dimension,
        reference_pixels=pixel_distance,
        notes=[f"Manual calibration: {pixel_distance:.1f}px = {real_dimension}\""],
    )


@router.get("/calibration/{calibration_id}")
async def get_calibration(calibration_id: str):
    """
    Retrieve a stored calibration result.

    Args:
        calibration_id: UUID from /calibrate or /calibrate/manual

    Returns:
        Calibration details
    """
    if calibration_id not in _calibration_cache:
        raise HTTPException(status_code=404, detail="Calibration not found")

    cached = _calibration_cache[calibration_id]
    cal = cached["calibration"]

    return {
        "calibration_id": calibration_id,
        "method": cal.method.value if hasattr(cal.method, 'value') else str(cal.method),
        "ppi": cal.ppi,
        "ppmm": cal.ppmm,
        "confidence": cal.confidence,
        "reference_name": cal.reference_name,
        "notes": cal.notes,
        "manual": cached.get("manual", False),
    }


@router.post("/dimensions", response_model=DimensionResponse)
async def extract_dimensions(
    file: UploadFile = File(...),
    calibration_id: str = Form(...),
    name: str = Form(""),
):
    """
    Extract real-world dimensions from blueprint using stored calibration.

    Extracts:
    - Body length and width
    - Upper/lower bout widths
    - Waist width
    - Aspect ratio

    Args:
        file: Blueprint image
        calibration_id: UUID from /calibrate or /calibrate/manual
        name: Guitar name for identification

    Returns:
        DimensionResponse with extracted measurements in inches and mm
    """
    if not CALIBRATION_AVAILABLE:
        raise HTTPException(
            status_code=501,
            detail="Calibration module not available."
        )

    if calibration_id not in _calibration_cache:
        raise HTTPException(status_code=404, detail="Calibration not found. Run /calibrate first.")

    # Get cached calibration
    cached = _calibration_cache[calibration_id]
    calibration = cached["calibration"]

    # Read and decode image
    contents = await file.read()
    image = _decode_image(contents)

    # Create pipeline and extract dimensions
    pipeline = create_calibration_pipeline()

    # Set the calibration
    pipeline.dimension_extractor.set_calibration(calibration.ppi, calibration.method.value)

    try:
        dims = pipeline.dimension_extractor.extract(
            image,
            name=name,
            source_file=file.filename or "",
        )
    except Exception as e:  # WP-2: API endpoint catch-all
        logger.exception("Dimension extraction failed")
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")

    return DimensionResponse(
        name=dims.name,
        body_length_inches=dims.body_length_inches,
        body_width_inches=dims.body_width_inches,
        body_length_mm=dims.body_length_mm,
        body_width_mm=dims.body_width_mm,
        upper_bout_width_inches=dims.upper_bout_width_inches,
        lower_bout_width_inches=dims.lower_bout_width_inches,
        waist_width_inches=dims.waist_width_inches,
        scale_length_inches=dims.scale_length_inches,
        body_aspect_ratio=dims.body_aspect_ratio,
        calibration_method=dims.calibration_method,
        calibration_confidence=dims.calibration_confidence,
        pixel_measurements=dims.pixel_measurements,
        warnings=dims.warnings,
    )


@router.get("/scale-lengths")
async def get_known_scale_lengths():
    """
    Get known scale lengths for common guitar brands/models.

    Returns a lookup table for auto-filling calibration hints.
    """
    return {
        "fender": {
            "stratocaster": 25.5,
            "telecaster": 25.5,
            "jazzmaster": 25.5,
            "jaguar": 24.0,
            "mustang": 24.0,
            "jazz_bass": 34.0,
            "precision_bass": 34.0,
        },
        "gibson": {
            "les_paul": 24.75,
            "sg": 24.75,
            "es_335": 24.75,
            "explorer": 24.75,
            "flying_v": 24.75,
            "firebird": 24.75,
            "thunderbird_bass": 34.0,
        },
        "prs": {
            "custom_24": 25.0,
            "custom_22": 25.0,
            "mccarty": 25.0,
            "se": 25.0,
        },
        "other": {
            "rickenbacker": 24.75,
            "gretsch": 24.6,
            "danelectro": 25.0,
            "steinberger": 25.5,
            "strandberg": 25.5,
        },
    }
