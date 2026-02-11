"""
Blueprint Phase 1 Router - AI-Powered Dimensional Analysis
===========================================================

Claude Sonnet 4 AI integration for blueprint dimensional extraction.

Endpoints:
- POST /analyze: AI dimensional analysis with Claude
- POST /to-svg: Export annotated SVG with dimensions
"""

import logging
import os
import tempfile
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from ..blueprint_schemas import AnalysisResponse, ExportRequest

from .constants import (
    ALLOWED_EXTENSIONS,
    ANALYZER_AVAILABLE,
    ANALYZER_IMPORT_ERROR,
    MAX_FILE_SIZE_BYTES,
    MIN_SCALE_FACTOR,
    MAX_SCALE_FACTOR,
    VECTORIZER_AVAILABLE,
    create_analyzer,
    create_vectorizer,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["blueprint"])


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_blueprint(file: UploadFile = File(...)):
    """
    Upload and analyze blueprint PDF or image with Claude Sonnet 4 AI.

    Performs dimensional analysis using Anthropic's Claude API to extract:
    - Scale factor (e.g., "1/4 inch = 1 foot")
    - Dimensions with measurements and units
    - Blueprint type classification
    - Confidence scores per detected dimension

    Args:
        file: Uploaded blueprint file (PDF, PNG, JPG, JPEG)

    Returns:
        AnalysisResponse with analysis_id, dimensions, scale, blueprint_type

    Raises:
        HTTPException 400: Invalid file type or file too large
        HTTPException 503: AI disabled (missing API key or dependencies)
        HTTPException 500: Analysis failed
    """
    # --- AI availability gate ---
    api_key = os.environ.get("EMERGENT_LLM_KEY") or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "AI_DISABLED",
                "message": "Blueprint AI is disabled: no API key configured (set EMERGENT_LLM_KEY or ANTHROPIC_API_KEY).",
            },
        )
    if not ANALYZER_AVAILABLE or not create_analyzer:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "AI_DISABLED",
                "message": "Blueprint AI is disabled: analyzer dependencies not installed.",
                "detail": ANALYZER_IMPORT_ERROR,
            },
        )

    try:
        # Validate file type
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file_ext}. Allowed: {ALLOWED_EXTENSIONS}"
            )

        # Validate file size (20MB max)
        file_bytes = await file.read()
        if len(file_bytes) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {MAX_FILE_SIZE_BYTES / 1024 / 1024:.0f}MB"
            )

        # Analyze with Claude
        analyzer = create_analyzer()
        logger.info(f"Starting analysis of {file.filename} ({len(file_bytes)} bytes)")
        analysis_data = await analyzer.analyze_from_bytes(file_bytes, file.filename)

        # Check for errors
        if analysis_data.get('error'):
            return AnalysisResponse(
                success=False,
                filename=file.filename,
                analysis=analysis_data,
                message=analysis_data.get('notes', 'Analysis failed')
            )

        dimensions_count = len(analysis_data.get('dimensions', []))
        logger.info(f"Analysis complete: {dimensions_count} dimensions detected")

        return AnalysisResponse(
            success=True,
            filename=file.filename,
            analysis=analysis_data,
            message=f"Detected {dimensions_count} dimensions"
        )

    except ValueError as e:
        # ValueError from analyzer = missing API key or config issue
        logger.error(f"AI configuration error: {e}")
        raise HTTPException(
            status_code=503,
            detail={"error": "AI_DISABLED", "message": str(e)},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing blueprint: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/to-svg")
async def export_to_svg(request: ExportRequest) -> FileResponse:
    """
    Convert AI analysis to SVG file with dimension annotations.

    Phase 1 implementation: Generates SVG visualization of detected dimensions
    with annotation lines and measurement labels.

    Args:
        request: ExportRequest with analysis_data, scale_correction, dimensions

    Returns:
        FileResponse with SVG file download

    Raises:
        HTTPException 400: Invalid format or scale_correction
        HTTPException 501: Vectorizer not available
        HTTPException 500: SVG generation error
    """
    try:
        if request.format != "svg":
            raise HTTPException(
                status_code=400,
                detail="Only SVG format supported in Phase 1. DXF coming in Phase 2."
            )

        # Check if vectorizer is available (not in Docker)
        if not VECTORIZER_AVAILABLE:
            raise HTTPException(
                status_code=501,
                detail="Blueprint vectorizer not available in this deployment. Use local development environment."
            )

        # Validate scale correction bounds
        if not (MIN_SCALE_FACTOR <= request.scale_correction <= MAX_SCALE_FACTOR):
            raise HTTPException(
                status_code=400,
                detail=f"scale_correction must be between {MIN_SCALE_FACTOR} and {MAX_SCALE_FACTOR}"
            )

        # Create temporary SVG file
        temp_dir = tempfile.gettempdir()
        svg_filename = f"blueprint_{uuid.uuid4().hex[:8]}.svg"
        svg_path = os.path.join(temp_dir, svg_filename)

        # Generate SVG
        vectorizer = create_vectorizer(units="mm")
        vectorizer.dimensions_to_svg(
            request.analysis_data,
            svg_path,
            width_mm=request.width_mm,
            height_mm=request.height_mm
        )

        logger.info(f"Generated SVG: {svg_path}")

        return FileResponse(
            svg_path,
            media_type="image/svg+xml",
            filename=svg_filename,
            headers={
                "Content-Disposition": f"attachment; filename={svg_filename}",
                "X-Scale-Factor": str(request.scale_correction)
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting SVG: {e}")
        raise HTTPException(status_code=500, detail=f"SVG export failed: {str(e)}")
