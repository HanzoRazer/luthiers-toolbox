"""
Blueprint Vectorize Router (Consolidated)
==========================================

Single production endpoint for blueprint vectorization.
Thin HTTP wrapper that calls BlueprintOrchestrator.

Endpoint:
    POST /api/blueprint/vectorize

Author: Production Shop
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from ...services.blueprint_orchestrator import BlueprintOrchestrator
from ...services.blueprint_limits import LIMITS
from ...utils.stage_timer import is_debug_enabled

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Blueprint Vectorize"])

# Singleton orchestrator instance
_orchestrator = BlueprintOrchestrator()


# ─── Response Models (Canonical Schema) ───────────────────────────────────────

class SVGArtifact(BaseModel):
    present: bool = False
    content: str = ""
    path_count: int = 0


class DXFArtifact(BaseModel):
    present: bool = False
    base64: str = ""
    entity_count: int = 0
    closed_contours: int = 0


class Artifacts(BaseModel):
    svg: SVGArtifact = SVGArtifact()
    dxf: DXFArtifact = DXFArtifact()


class Dimensions(BaseModel):
    width_mm: float = 0.0
    height_mm: float = 0.0


class BlueprintVectorizeResponse(BaseModel):
    ok: bool
    stage: str = "complete"
    error: str = ""
    warnings: list[str] = []
    artifacts: Artifacts = Artifacts()
    dimensions: Dimensions = Dimensions()
    metrics: dict = {}
    debug: Optional[dict] = None  # Only present when debug=true and VECTORIZER_DEBUG=1


# ─── Endpoint ─────────────────────────────────────────────────────────────────

@router.post("/vectorize", response_model=BlueprintVectorizeResponse)
async def vectorize_blueprint(
    file: UploadFile = File(...),
    page_num: int = Form(0),
    target_height_mm: float = Form(500.0),
    min_contour_length_mm: float = Form(100.0),
    close_gaps_mm: float = Form(1.0),
    debug: bool = Form(False),
):
    """
    Vectorize a blueprint image or PDF to SVG + DXF.

    Single consolidated endpoint that:
    1. Loads image/PDF
    2. Runs edge detection
    3. Traces contours
    4. Filters/cleans contours
    5. Generates SVG preview
    6. Generates DXF output
    7. Validates both artifacts
    8. Returns canonical artifacts schema

    Args:
        file: Image (JPEG/PNG) or PDF file
        page_num: Page number for PDFs (0-indexed)
        target_height_mm: Target height for scaling (default 500mm)
        min_contour_length_mm: Minimum contour length to keep
        close_gaps_mm: Maximum gap to close between endpoints
        debug: Include stage timings in response (requires VECTORIZER_DEBUG=1)

    Returns:
        BlueprintVectorizeResponse with artifacts.svg and artifacts.dxf
    """
    # Read file content
    file_bytes = await file.read()
    filename = file.filename or "upload"

    # Guardrail: reject oversized uploads
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    if len(file_bytes) > LIMITS.max_upload_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"Blueprint file exceeds {LIMITS.max_upload_mb} MB limit. Please upload a smaller file.",
        )

    # Check if debug output is allowed
    include_debug = debug and is_debug_enabled()

    # Delegate to orchestrator
    result = _orchestrator.process_file(
        file_bytes=file_bytes,
        filename=filename,
        page_num=page_num,
        target_height_mm=target_height_mm,
        min_contour_length_mm=min_contour_length_mm,
        close_gaps_mm=close_gaps_mm,
        debug=include_debug,
    )

    # Convert to response dict
    response_dict = result.to_response_dict(include_debug=include_debug)

    return BlueprintVectorizeResponse(**response_dict)
