"""
Blueprint Phase 3 Router - Production ML + OCR Vectorizer
==========================================================

API endpoint wrapping vectorizer_phase3.py (Phase 3.6/3.7) for
production-grade blueprint extraction with ML classification,
OCR dimension extraction, and CAM-ready DXF output.

Resolves: VEC-GAP-01 (Phase 3.6 Vectorizer has no API endpoint)

Endpoints:
    POST /phase3/vectorize     - Full extraction pipeline
    POST /phase3/quick         - Quick extraction (no ML/OCR)
    GET  /phase3/info          - Module availability info
"""

from __future__ import annotations

import logging
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from .constants import (
    PHASE3_AVAILABLE,
    extract_guitar_blueprint,
    MAX_FILE_SIZE_BYTES,
    ALLOWED_EXTENSIONS,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/phase3", tags=["Blueprint Phase 3"])


class Phase3Response(BaseModel):
    """Response from Phase 3 vectorization."""
    success: bool
    dxf_path: Optional[str] = None
    svg_path: Optional[str] = None
    body_size_mm: Optional[Dict[str, float]] = None
    contours_found: int = 0
    primitives_detected: int = 0
    validation_passed: bool = False
    processing_time_ms: int = 0
    ml_available: bool = False
    ocr_available: bool = False
    message: Optional[str] = None


class Phase3InfoResponse(BaseModel):
    """Phase 3 module availability info."""
    available: bool
    version: str = "3.7.0"
    features: Dict[str, bool]
    supported_formats: list
    instrument_types: list


@router.get("/info", response_model=Phase3InfoResponse)
def get_phase3_info() -> Phase3InfoResponse:
    """Get Phase 3 vectorizer availability and feature info."""
    ml_available = False
    enhancements_available = False
    
    if PHASE3_AVAILABLE:
        try:
            from vectorizer_phase3 import SKLEARN_AVAILABLE, ENHANCEMENTS_AVAILABLE
            ml_available = SKLEARN_AVAILABLE
            enhancements_available = ENHANCEMENTS_AVAILABLE
        except ImportError:
            pass
    
    return Phase3InfoResponse(
        available=PHASE3_AVAILABLE,
        version="3.7.0",
        features={
            "ml_classification": ml_available,
            "phase37_enhancements": enhancements_available,
            "dual_pass_extraction": True,
            "primitive_detection": True,
            "dimension_validation": True,
            "cam_ready_dxf": True,
        },
        supported_formats=[".pdf", ".png", ".jpg", ".jpeg"],
        instrument_types=["electric", "acoustic", "archtop", "bass", "ukulele", "mandolin"],
    )


@router.post("/vectorize", response_model=Phase3Response)
async def vectorize_blueprint(
    file: UploadFile = File(..., description="Blueprint PDF or image"),
    instrument_type: str = Form("electric"),
    spec_name: Optional[str] = Form(None),
    dual_pass: bool = Form(True),
    use_ml: bool = Form(True),
    detect_primitives: bool = Form(True),
    validate: bool = Form(True),
    dpi: int = Form(400, ge=72, le=1200),
    return_dxf: bool = Form(False),
) -> Phase3Response:
    """
    Full Phase 3 vectorization pipeline.
    
    Extracts vector geometry from blueprint PDF/image using:
    - Dual-pass extraction (aggressive for body, lighter for details)
    - ML contour classification (optional)
    - Dimension validation against known instrument specs
    - CAM-ready DXF output with closed LWPOLYLINE contours
    """
    if not PHASE3_AVAILABLE:
        raise HTTPException(503, "Phase 3 vectorizer not available")
    
    if not file.filename:
        raise HTTPException(400, "No filename provided")
    
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Unsupported format. Allowed: {ALLOWED_EXTENSIONS}")
    
    content = await file.read()
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(400, "File too large")
    
    start_time = time.time()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / f"input{ext}"
        input_path.write_bytes(content)
        
        output_dir = Path(tmpdir) / "output"
        output_dir.mkdir()
        
        try:
            result = extract_guitar_blueprint(
                source_path=str(input_path),
                output_dir=str(output_dir),
                instrument_type=instrument_type,
                spec_name=spec_name,
                dual_pass=dual_pass,
                use_ml=use_ml,
                detect_primitives=detect_primitives,
                validate=validate,
                dpi=dpi,
            )
            
            processing_time = int((time.time() - start_time) * 1000)
            
            dxf_path = result.get("dxf")
            if dxf_path and Path(dxf_path).exists() and return_dxf:
                return FileResponse(
                    dxf_path,
                    media_type="application/dxf",
                    filename=f"{Path(file.filename).stem}_phase3.dxf",
                )
            
            return Phase3Response(
                success=True,
                dxf_path=result.get("dxf"),
                svg_path=result.get("svg"),
                body_size_mm=result.get("body_size_mm"),
                contours_found=result.get("contours_found", 0),
                primitives_detected=result.get("primitives_detected", 0),
                validation_passed=result.get("validation_passed", False),
                processing_time_ms=processing_time,
                ml_available=result.get("ml_used", False),
                ocr_available=result.get("ocr_used", False),
                message=result.get("message"),
            )
            
        except Exception as e:
            logger.exception("Phase 3 vectorization failed")
            raise HTTPException(500, f"Vectorization failed: {e}")


@router.post("/quick")
async def quick_vectorize(
    file: UploadFile = File(...),
    instrument_type: str = Form("electric"),
) -> Phase3Response:
    """Quick vectorization without ML/OCR (faster, less accurate)."""
    if not PHASE3_AVAILABLE:
        raise HTTPException(503, "Phase 3 vectorizer not available")
    
    return await vectorize_blueprint(
        file=file,
        instrument_type=instrument_type,
        dual_pass=False,
        use_ml=False,
        detect_primitives=False,
        validate=False,
        dpi=300,
        return_dxf=False,
    )
