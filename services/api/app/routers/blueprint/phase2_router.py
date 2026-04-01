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

from typing import Dict

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from ..blueprint_schemas import ExportRequest, VectorizeResponse

from .constants import (
    MIN_SCALE_FACTOR,
    MAX_SCALE_FACTOR,
    PHASE2_AVAILABLE,
    PHASE2_EXTENSIONS,
    CALIBRATION_AVAILABLE,
    create_phase2_vectorizer,
    create_calibration_pipeline,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["blueprint"])

# Registry of generated output files: filename -> full_path
# Enables serving files via /static/{filename} after vectorization
_output_file_registry: Dict[str, str] = {}


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
    analysis_data: str = Form(""),
    scale_factor: float = Form(1.0),
    calibration_id: str = Form(""),
    instrument_type: str = Form("electric"),
    dark_threshold: str = Form("auto"),
    gap_close_size: int = Form(0),
    extraction_mode: str = Form("smart"),
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
        calibration_id: UUID from /calibrate endpoint for PPI-aware scaling
        instrument_type: "electric" or "acoustic" for feature classification
        dark_threshold: "auto" or 0-255 for line extraction threshold
        gap_close_size: Morphological closing kernel (0=disabled, 5=recommended)
        extraction_mode: "smart" (ML-filtered) or "simple" (all contours, any instrument)

    Returns:
        VectorizeResponse with svg_path, dxf_path, contours_detected, lines_detected

    Processing Pipeline:
        1. Calibration lookup (if calibration_id provided)
        2. Canny edge detection with adaptive thresholds
        3. Contour extraction with guitar-aware scoring
        4. Feature classification by instrument type
        5. SVG + DXF R12 generation with semantic layers

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

        # Get calibration-based scale factor if calibration_id provided
        effective_scale = scale_factor
        calibration_info = None

        if calibration_id and CALIBRATION_AVAILABLE:
            from .calibration_router import _calibration_cache
            if calibration_id in _calibration_cache:
                cached = _calibration_cache[calibration_id]
                calibration = cached["calibration"]
                # Convert PPI to mm_per_pixel scale correction
                # Standard assumption is 300 DPI (0.0847 mm/px)
                calibrated_mm_per_px = 25.4 / calibration.ppi
                standard_mm_per_px = 25.4 / 300.0
                effective_scale = scale_factor * (calibrated_mm_per_px / standard_mm_per_px)
                calibration_info = {
                    "ppi": calibration.ppi,
                    "method": calibration.method.value if hasattr(calibration.method, 'value') else str(calibration.method),
                    "confidence": calibration.confidence,
                    "applied_scale": effective_scale,
                }
                logger.info(f"Applied calibration: PPI={calibration.ppi}, scale={effective_scale:.3f}")

        # Parse dark_threshold
        threshold_value = dark_threshold if dark_threshold == "auto" else int(dark_threshold)

        # Run Phase 2 vectorization with guitar feature extraction
        vectorizer = create_phase2_vectorizer()
        # Map frontend extraction_mode to vectorizer mode
        vectorizer_mode = "simple" if extraction_mode == "simple" else "guitar"
        
        result = vectorizer.analyze_and_vectorize(
            source_path=tmp_path,
            analysis_data=analysis_dict,
            output_dir=output_dir,
            scale_factor=effective_scale,
            extraction_mode=vectorizer_mode,
            instrument_type=instrument_type,
            dark_threshold=threshold_value,
            gap_close_size=gap_close_size,
        )

        # Calculate processing time
        processing_time = int((time.time() - start_time) * 1000)

        # Extract counts from result (vectorizer returns total_contours/total_lines)
        contours_count = result.get('total_contours', 0)
        lines_count = result.get('total_lines', 0)

        logger.info(f"Phase 2 complete: {contours_count} contours, {lines_count} lines in {processing_time}ms")

        message = f"Detected {contours_count} contours and {lines_count} line segments"
        if calibration_info:
            message += f" (calibrated at {calibration_info['ppi']:.0f} PPI)"

        # Register output files for serving via /static/{filename}
        svg_path = result['svg']
        dxf_path = result['dxf']
        if svg_path:
            _output_file_registry[Path(svg_path).name] = svg_path
        if dxf_path:
            _output_file_registry[Path(dxf_path).name] = dxf_path

        return VectorizeResponse(
            success=True,
            svg_path=svg_path,
            dxf_path=dxf_path,
            contours_detected=contours_count,
            lines_detected=lines_count,
            processing_time_ms=processing_time,
            message=message
        )
    except HTTPException:
        raise
    except (ValueError, TypeError, OSError, KeyError) as e:  # WP-1: vectorization
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

@router.get("/static/{filename}")
async def serve_static_file(filename: str) -> FileResponse:
    """
    Serve generated DXF/SVG files by filename.
    
    Files are registered in _output_file_registry after vectorization.
    This enables the frontend to download files via /api/blueprint/static/{filename}.
    
    Args:
        filename: The filename (e.g., 'blueprint_vectorized.dxf')
        
    Returns:
        FileResponse with the requested file
        
    Raises:
        HTTPException 404: File not found in registry or on disk
    """
    # Check registry first
    if filename in _output_file_registry:
        file_path = _output_file_registry[filename]
        if Path(file_path).exists():
            media_type = "application/dxf" if filename.endswith(".dxf") else "image/svg+xml"
            return FileResponse(
                file_path,
                media_type=media_type,
                filename=filename,
            )
    
    # Fallback: search temp directories with blueprint_phase prefix
    import glob
    import os

    temp_base = tempfile.gettempdir()
    # Use os.path.join for cross-platform path construction
    pattern = os.path.join(temp_base, "blueprint_phase*", filename)

    matches = glob.glob(pattern)
    if matches:
        file_path = matches[0]
        # Register for future lookups
        _output_file_registry[filename] = file_path
        media_type = "application/dxf" if filename.endswith(".dxf") else "image/svg+xml"
        return FileResponse(
            file_path,
            media_type=media_type,
            filename=filename,
        )
    
    raise HTTPException(
        status_code=404,
        detail=f"File not found: {filename}. Run vectorization first."
    )
