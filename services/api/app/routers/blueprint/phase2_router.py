"""
Blueprint Phase 2 Router - OpenCV Geometry Vectorization
=========================================================

Computer vision pipeline for blueprint geometry extraction.

Endpoints:
- POST /to-dxf: DXF export (placeholder, use /vectorize-geometry)
- POST /vectorize-geometry: OpenCV edge detection + DXF/SVG export
"""

import json
import logging
import tempfile
import time
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from ..blueprint_schemas import ExportRequest, VectorizeResponse

from .constants import (
    MIN_SCALE_FACTOR,
    MAX_SCALE_FACTOR,
    PHASE2_AVAILABLE,
    PHASE2_EXTENSIONS,
    create_phase2_vectorizer,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["blueprint"])


@router.post("/to-dxf")
async def export_to_dxf(request: ExportRequest) -> FileResponse:
    """
    Convert AI analysis to DXF R12 file with intelligent geometry detection.

    **STATUS: PLANNED - Phase 2 implementation in progress**

    Use /vectorize-geometry for current DXF export functionality.

    Raises:
        HTTPException 501: Not implemented
    """
    if not PHASE2_AVAILABLE:
        raise HTTPException(
            status_code=501,
            detail="Phase 2 vectorizer not available. Install opencv-python and ezdxf."
        )

    raise HTTPException(
        status_code=501,
        detail="DXF export endpoint under development. Use /vectorize-geometry for now."
    )


@router.post("/vectorize-geometry", response_model=VectorizeResponse)
async def vectorize_geometry(
    file: UploadFile = File(...),
    analysis_data: str = "",  # JSON string from /analyze
    scale_factor: float = 1.0
):
    """
    Phase 2: Intelligent geometry detection from blueprint image using OpenCV.

    Combines AI dimensional analysis with edge detection to produce CAM-ready
    vector files (SVG + DXF R12). Uses Canny edge detection, Hough transforms,
    and contour extraction for precise geometry.

    Args:
        file: Blueprint image file (PNG, JPG, JPEG)
        analysis_data: JSON string from /analyze endpoint (optional)
        scale_factor: Scaling multiplier for output coordinates (0.1-10.0)

    Returns:
        VectorizeResponse with svg_path, dxf_path, contours_detected, lines_detected

    Processing Pipeline:
        1. Canny edge detection (thresholds: 50, 150)
        2. Hough line transform for straight edges
        3. Contour extraction and simplification
        4. SVG generation with layers
        5. DXF R12 generation with closed polylines

    Raises:
        HTTPException 400: Invalid file type, JSON parse error
        HTTPException 500: OpenCV error or vectorization crash
        HTTPException 501: Phase 2 not available
    """
    if not PHASE2_AVAILABLE:
        raise HTTPException(
            status_code=501,
            detail="Phase 2 not available. Install: pip install opencv-python scikit-image"
        )

    start_time = time.time()
    tmp_path = None

    try:
        # Parse analysis data
        try:
            analysis_dict = json.loads(analysis_data) if analysis_data else {}
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=400,
                detail="Invalid analysis_data JSON"
            )

        # Validate file
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in PHASE2_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file_ext}. Phase 2 requires PNG/JPG"
            )

        # Validate scale factor
        if not (MIN_SCALE_FACTOR <= scale_factor <= MAX_SCALE_FACTOR):
            raise HTTPException(
                status_code=400,
                detail=f"scale_factor must be between {MIN_SCALE_FACTOR} and {MAX_SCALE_FACTOR}"
            )

        # Save uploaded image to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
            file_bytes = await file.read()
            tmp.write(file_bytes)
            tmp_path = tmp.name

        logger.info(f"Starting Phase 2 vectorization: {file.filename} ({len(file_bytes)} bytes)")

        # Create output directory
        output_dir = tempfile.mkdtemp(prefix="blueprint_phase2_")

        # Run Phase 2 vectorization
        vectorizer = create_phase2_vectorizer()
        result = vectorizer.analyze_and_vectorize(
            image_path=tmp_path,
            analysis_data=analysis_dict,
            output_dir=output_dir,
            scale_factor=scale_factor
        )

        # Calculate processing time
        processing_time = int((time.time() - start_time) * 1000)

        logger.info(f"Phase 2 complete: {result['contours']} contours, {result['lines']} lines in {processing_time}ms")

        return VectorizeResponse(
            success=True,
            svg_path=result['svg'],
            dxf_path=result['dxf'],
            contours_detected=result['contours'],
            lines_detected=result['lines'],
            processing_time_ms=processing_time,
            message=f"Detected {result['contours']} contours and {result['lines']} line segments"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Phase 2 vectorization failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Geometry detection failed: {str(e)}"
        )
    finally:
        # Clean up temp file
        try:
            if tmp_path:
                Path(tmp_path).unlink(missing_ok=True)
        except OSError as e:
            logger.warning(f"Failed to clean up temp file: {e}")
