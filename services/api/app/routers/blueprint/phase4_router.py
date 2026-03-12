"""
Blueprint Phase 4 Router - Dimension Linking Pipeline
======================================================

API endpoint wrapping the Phase 4.0 dimension linker for associating
OCR-extracted dimensions with detected geometry features via leader lines.

Resolves: VEC-GAP-02 (Phase 4 Dimension Linking is CLI-only)

Endpoints:
    POST /phase4/link          - Full dimension linking pipeline
    POST /phase4/link-from-p3  - Link dimensions from Phase 3 result
    GET  /phase4/info          - Module availability info
"""

from __future__ import annotations

import logging
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .constants import (
    PHASE4_AVAILABLE,
    process_blueprint,
    BlueprintPipeline,
    PipelineResult,
    MAX_FILE_SIZE_BYTES,
    ALLOWED_EXTENSIONS,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/phase4", tags=["Blueprint Phase 4"])


class LinkedDimensionInfo(BaseModel):
    """Info about a linked dimension."""
    text: str
    value_mm: Optional[float] = None
    target_feature: Optional[str] = None
    confidence: float = 0.0


class Phase4Response(BaseModel):
    """Response from Phase 4 dimension linking."""
    success: bool
    source_file: str = ""
    dimensions_mm: Tuple[float, float] = (0.0, 0.0)
    features_count: Dict[str, int] = {}
    ocr_dimensions_found: int = 0
    arrows_detected: int = 0
    dimensions_linked: int = 0
    unmatched_dimensions: int = 0
    association_rate: float = 0.0
    processing_time_ms: int = 0
    linked_dimensions: List[LinkedDimensionInfo] = []
    message: Optional[str] = None


class Phase4InfoResponse(BaseModel):
    """Phase 4 module availability info."""
    available: bool
    version: str = "4.0.0"
    features: Dict[str, bool]
    description: str


@router.get("/info", response_model=Phase4InfoResponse)
def get_phase4_info() -> Phase4InfoResponse:
    """Get Phase 4 dimension linker availability and feature info."""
    return Phase4InfoResponse(
        available=PHASE4_AVAILABLE,
        version="4.0.0",
        features={
            "arrow_detection": PHASE4_AVAILABLE,
            "leader_line_association": PHASE4_AVAILABLE,
            "dimension_geometry_linking": PHASE4_AVAILABLE,
            "ocr_integration": PHASE4_AVAILABLE,
        },
        description="Links OCR-extracted dimensions to geometry features via leader line detection",
    )


@router.post("/link", response_model=Phase4Response)
async def link_dimensions(
    file: UploadFile = File(..., description="Blueprint PDF"),
    dpi: int = Form(300, ge=72, le=600, description="DPI for rendering"),
    instrument_type: Optional[str] = Form(None, description="Instrument type hint"),
    debug_mode: bool = Form(False, description="Enable debug mode"),
) -> Phase4Response:
    """
    Full Phase 4 dimension linking pipeline.
    
    Processes a blueprint PDF through:
    1. Phase 3 extraction (geometry + OCR)
    2. Arrow/arrowhead detection
    3. Leader line association
    4. Dimension-to-feature linking
    
    Returns linked dimensions with their target features.
    """
    if not PHASE4_AVAILABLE:
        raise HTTPException(503, "Phase 4 dimension linker not available")
    
    if not file.filename:
        raise HTTPException(400, "No filename provided")
    
    ext = Path(file.filename).suffix.lower()
    if ext not in {'.pdf'}:
        raise HTTPException(400, "Phase 4 requires PDF input")
    
    content = await file.read()
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(400, "File too large")
    
    start_time = time.time()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / f"input{ext}"
        input_path.write_bytes(content)
        
        try:
            result = process_blueprint(
                pdf_path=str(input_path),
                dpi=dpi,
                instrument_type=instrument_type,
                debug_mode=debug_mode,
            )
            
            processing_time = int((time.time() - start_time) * 1000)
            
            # Extract linked dimension details
            linked_dims = []
            if result.linked_dimensions:
                for dim in getattr(result.linked_dimensions, 'dimensions', []):
                    linked_dims.append(LinkedDimensionInfo(
                        text=getattr(dim.text_region, 'text', ''),
                        value_mm=getattr(dim.text_region, 'value_mm', None),
                        target_feature=getattr(dim.target_feature, 'category', None) if dim.target_feature else None,
                        confidence=getattr(dim, 'confidence', 0.0),
                    ))
            
            return Phase4Response(
                success=True,
                source_file=file.filename,
                dimensions_mm=result.dimensions_mm,
                features_count=result.features_count,
                ocr_dimensions_found=result.ocr_dimensions_found,
                arrows_detected=result.arrows_detected,
                dimensions_linked=result.dimensions_linked,
                unmatched_dimensions=result.unmatched_dimensions,
                association_rate=result.association_rate,
                processing_time_ms=processing_time,
                linked_dimensions=linked_dims,
            )
            
        except Exception as e:  # WP-2: API endpoint catch-all
            logger.exception("Phase 4 dimension linking failed")
            raise HTTPException(500, f"Dimension linking failed: {e}")


@router.post("/link-json")
async def link_dimensions_json(
    file: UploadFile = File(..., description="Blueprint PDF"),
    dpi: int = Form(300),
    instrument_type: Optional[str] = Form(None),
) -> JSONResponse:
    """
    Phase 4 dimension linking with full JSON export.
    
    Returns the complete PipelineResult as JSON, including
    all linked dimensions with detailed association data.
    """
    if not PHASE4_AVAILABLE:
        raise HTTPException(503, "Phase 4 dimension linker not available")
    
    if not file.filename:
        raise HTTPException(400, "No filename provided")
    
    content = await file.read()
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(400, "File too large")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "input.pdf"
        input_path.write_bytes(content)
        
        try:
            result = process_blueprint(
                pdf_path=str(input_path),
                dpi=dpi,
                instrument_type=instrument_type,
            )
            
            return JSONResponse(content=result.to_dict())
            
        except Exception as e:  # WP-2: API endpoint catch-all
            logger.exception("Phase 4 dimension linking failed")
            raise HTTPException(500, f"Dimension linking failed: {e}")
