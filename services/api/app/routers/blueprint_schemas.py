"""Blueprint Router Schemas — Extracted from blueprint_router.py (Phase 9).

Pydantic models for blueprint AI analysis and vectorization API.
"""

import uuid
from typing import Optional

from pydantic import BaseModel, Field

# Default values from blueprint_router.py constants
DEFAULT_SVG_WIDTH_MM: float = 300.0
DEFAULT_SVG_HEIGHT_MM: float = 200.0
DEFAULT_EDGE_THRESHOLD_LOW: int = 50
DEFAULT_EDGE_THRESHOLD_HIGH: int = 150
DEFAULT_MIN_CONTOUR_AREA: float = 100.0


class AnalysisResponse(BaseModel):
    """
    Response from AI blueprint analysis.

    Contains dimensional analysis results from Claude Sonnet 4 including
    detected measurements, scale factors, and confidence scores.

    Fields:
        success: bool - Analysis completed without errors
        filename: str - Original uploaded filename
        analysis: dict - Full analysis data from Claude (dimensions, scale, type)
        analysis_id: str - Unique UUID for tracking this analysis
        message: Optional[str] - Human-readable status message
    """
    success: bool
    filename: str
    analysis: dict
    analysis_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    message: Optional[str] = None


class ExportRequest(BaseModel):
    """
    Request for DXF/SVG export from blueprint analysis.

    Provides parameters for vector file generation from AI analysis data.
    Phase 1 supports SVG only, Phase 2 adds DXF R12.

    Fields:
        analysis_data: dict - Output from /analyze endpoint
        format: str - Export format ("svg" or "dxf")
        scale_correction: float - Manual scaling multiplier (0.1-10.0)
        width_mm: float - Canvas width in millimeters
        height_mm: float - Canvas height in millimeters
    """
    analysis_data: dict
    format: str = "svg"  # "svg" or "dxf" (Phase 2)
    scale_correction: float = 1.0
    width_mm: float = DEFAULT_SVG_WIDTH_MM
    height_mm: float = DEFAULT_SVG_HEIGHT_MM


class VectorizeRequest(BaseModel):
    """
    Request for Phase 2 intelligent geometry detection.

    Parameters for OpenCV-based edge detection and vectorization.
    Used internally for parameter validation.

    Fields:
        analysis_id: str - UUID from previous /analyze call
        image_data: Optional[str] - Base64 encoded image (alternative to file upload)
        scale_factor: float - Scaling multiplier (0.1-10.0)
        edge_threshold_low: int - Canny low threshold (0-255)
        edge_threshold_high: int - Canny high threshold (0-255)
        min_contour_area: float - Minimum contour area to keep (pixels²)
    """
    analysis_id: str
    image_data: Optional[str] = None  # Base64 encoded image
    scale_factor: float = 1.0
    edge_threshold_low: int = DEFAULT_EDGE_THRESHOLD_LOW
    edge_threshold_high: int = DEFAULT_EDGE_THRESHOLD_HIGH
    min_contour_area: float = DEFAULT_MIN_CONTOUR_AREA


class VectorizeResponse(BaseModel):
    """
    Response from Phase 2 geometry detection.

    Contains paths to generated vector files and detection statistics.

    Fields:
        success: bool - Vectorization completed without errors
        svg_path: Optional[str] - Path to generated SVG file
        dxf_path: Optional[str] - Path to generated DXF R12 file
        contours_detected: int - Number of closed contours found
        lines_detected: int - Number of line segments detected
        processing_time_ms: int - Total processing time in milliseconds
        message: Optional[str] - Human-readable status message
    """
    success: bool
    svg_path: Optional[str] = None
    dxf_path: Optional[str] = None
    contours_detected: int = 0
    lines_detected: int = 0
    processing_time_ms: int = 0
    message: Optional[str] = None


# Re-export all schemas
__all__ = [
    "AnalysisResponse",
    "ExportRequest",
    "VectorizeRequest",
    "VectorizeResponse",
    "DEFAULT_SVG_WIDTH_MM",
    "DEFAULT_SVG_HEIGHT_MM",
    "DEFAULT_EDGE_THRESHOLD_LOW",
    "DEFAULT_EDGE_THRESHOLD_HIGH",
    "DEFAULT_MIN_CONTOUR_AREA",
]
