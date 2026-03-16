"""Vision Analyze-Generated Router — CAS → Segmentation → Blueprint bridge.

Provides:
- POST /analyze-generated  Retrieve a previously generated image from CAS,
  run AI body segmentation, and optionally forward to Blueprint Phase 1.

Closes the Generation → Segmentation → Blueprint pipeline gap (AI-1).

LANE: PRODUCER (analyzes assets via AI, writes to CAS)
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.rmos.runs_v2.attachments import get_bytes_attachment
from app.ai.transport import get_vision_client
from app.vision.segmentation_service import (
    GuitarSegmentationService,
    SegmentationError,
    SegmentationResult,
)
from app.rmos.runs_v2.attachments import put_bytes_attachment

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Vision", "AnalyzeGenerated"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class AnalyzeGeneratedRequest(BaseModel):
    """Request to analyze a previously generated AI image from CAS."""
    asset_sha256: str = Field(..., description="SHA256 of the image stored in CAS")
    instrument_type: str = Field("auto", description="Guitar category hint: auto, acoustic, electric")
    target_width_mm: float = Field(400.0, gt=0, description="Target body width in mm")
    simplify_tolerance_mm: float = Field(1.0, gt=0, description="Douglas-Peucker tolerance in mm")
    forward_to_blueprint: bool = Field(False, description="If true, also run Blueprint Phase 1 analysis")


class SegmentationBlock(BaseModel):
    """Body segmentation results."""
    ok: bool
    polygon: List[List[float]] = Field(default_factory=list, description="Body outline [[x,y],...] in mm")
    confidence: float = 0.0
    guitar_type: str = "unknown"
    point_count: int = 0
    target_width_mm: float = 0.0
    target_height_mm: float = 0.0
    notes: str = ""
    dxf_sha256: Optional[str] = None
    dxf_url: Optional[str] = None
    svg_sha256: Optional[str] = None
    svg_url: Optional[str] = None


class BlueprintBlock(BaseModel):
    """Blueprint Phase 1 analysis results (optional)."""
    success: bool
    analysis: Dict[str, Any] = Field(default_factory=dict)
    analysis_id: str = ""
    message: Optional[str] = None


class AnalyzeGeneratedResponse(BaseModel):
    """Combined segmentation + optional blueprint analysis."""
    ok: bool
    asset_sha256: str
    segmentation: Optional[SegmentationBlock] = None
    blueprint: Optional[BlueprintBlock] = None
    error: Optional[str] = None
    request_id: str = ""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _blob_download_url(sha256: str) -> str:
    return f"/api/advisory/blobs/{sha256}/download"


def _extract_request_id(req: Request) -> str:
    return req.headers.get("x-request-id") or ""


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.post(
    "/analyze-generated",
    response_model=AnalyzeGeneratedResponse,
    summary="Analyze a previously generated AI image",
)
async def analyze_generated(
    request: Request,
    payload: AnalyzeGeneratedRequest,
) -> AnalyzeGeneratedResponse:
    """Retrieve image from CAS → AI segmentation → optional Blueprint Phase 1.

    Bridges the generation → segmentation → blueprint pipeline:
    1. Fetches image bytes from CAS by sha256
    2. Runs GuitarSegmentationService (via ai/transport VisionClient)
    3. Exports DXF + SVG to CAS
    4. Optionally forwards to Blueprint Phase 1 (Claude dimensional analysis)
    """
    request_id = _extract_request_id(request)

    # ── 1. Retrieve image bytes from CAS ─────────────────────────────────
    image_bytes = get_bytes_attachment(payload.asset_sha256)
    if image_bytes is None:
        raise HTTPException(
            status_code=404,
            detail=f"CAS_ASSET_NOT_FOUND: no blob for sha256={payload.asset_sha256!r}",
        )

    # ── 2. Run AI segmentation ───────────────────────────────────────────
    try:
        vision_client = get_vision_client("openai")
        service = GuitarSegmentationService(vision_client)
    except HTTPException:
        raise
    except (ValueError, TypeError, RuntimeError, OSError) as exc:
        raise HTTPException(status_code=503, detail=f"VISION_SERVICE_UNAVAILABLE: {exc}") from exc

    try:
        result = service.segment(
            image_bytes=image_bytes,
            target_width_mm=payload.target_width_mm,
            simplify_tolerance_mm=payload.simplify_tolerance_mm,
            guitar_category=payload.instrument_type,
        )
    except HTTPException:
        raise
    except (ValueError, TypeError, RuntimeError, OSError) as exc:
        return AnalyzeGeneratedResponse(
            ok=False,
            asset_sha256=payload.asset_sha256,
            error=f"SEGMENTATION_FAILED: {exc}",
            request_id=request_id,
        )

    if isinstance(result, SegmentationError):
        return AnalyzeGeneratedResponse(
            ok=False,
            asset_sha256=payload.asset_sha256,
            segmentation=SegmentationBlock(ok=False, notes=result.error, confidence=result.confidence),
            error=result.error,
            request_id=request_id,
        )

    # ── 3. Build segmentation block + export DXF/SVG  ────────────────────
    seg_block = SegmentationBlock(
        ok=True,
        polygon=[[p[0], p[1]] for p in result.polygon_mm],
        confidence=result.confidence,
        guitar_type=result.guitar_type,
        point_count=result.point_count,
        target_width_mm=result.target_width_mm,
        target_height_mm=result.target_height_mm,
        notes=result.notes,
    )

    # DXF export
    try:
        dxf_bytes = service.export_to_dxf(result)
        att, _ = put_bytes_attachment(
            dxf_bytes,
            kind="advisory",
            mime="application/dxf",
            filename=f"guitar_body_{result.guitar_type}.dxf",
        )
        seg_block.dxf_sha256 = att.sha256
        seg_block.dxf_url = _blob_download_url(att.sha256)
    except HTTPException:
        raise
    except (ValueError, TypeError, OSError, RuntimeError) as exc:
        seg_block.notes += f" DXF export failed: {exc}"

    # SVG export
    try:
        svg_content = service.export_to_svg(result)
        svg_bytes = svg_content.encode("utf-8")
        att, _ = put_bytes_attachment(
            svg_bytes,
            kind="advisory",
            mime="image/svg+xml",
            filename=f"guitar_body_{result.guitar_type}.svg",
        )
        seg_block.svg_sha256 = att.sha256
        seg_block.svg_url = _blob_download_url(att.sha256)
    except HTTPException:
        raise
    except (ValueError, TypeError, OSError, RuntimeError) as exc:
        seg_block.notes += f" SVG export failed: {exc}"

    # ── 4. Optional Blueprint Phase 1 ────────────────────────────────────
    blueprint_block: Optional[BlueprintBlock] = None

    if payload.forward_to_blueprint:
        blueprint_block = await _run_blueprint_phase1(image_bytes, payload.asset_sha256)

    return AnalyzeGeneratedResponse(
        ok=True,
        asset_sha256=payload.asset_sha256,
        segmentation=seg_block,
        blueprint=blueprint_block,
        request_id=request_id,
    )


async def _run_blueprint_phase1(
    image_bytes: bytes,
    sha256: str,
) -> BlueprintBlock:
    """Run Blueprint Phase 1 dimensional analysis on the image bytes.

    Uses the same analyzer as POST /api/blueprint/analyze but called
    programmatically (no UploadFile needed).
    """
    import os

    try:
        from app.routers.blueprint.constants import ANALYZER_AVAILABLE, create_analyzer
    except (ImportError, OSError) as exc:
        return BlueprintBlock(success=False, message=f"Blueprint analyzer import failed: {exc}")

    api_key = os.environ.get("EMERGENT_LLM_KEY") or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return BlueprintBlock(success=False, message="AI_DISABLED: no API key configured")

    if not ANALYZER_AVAILABLE or not create_analyzer:
        return BlueprintBlock(
            success=False,
            message="Blueprint analyzer not available (dependencies not installed)",
        )

    try:
        analyzer = create_analyzer()
        analysis_data = await analyzer.analyze_from_bytes(image_bytes, f"cas_{sha256}.png")
    except HTTPException:
        raise
    except (ValueError, TypeError, RuntimeError, OSError, ConnectionError, TimeoutError) as exc:
        return BlueprintBlock(success=False, message=f"Blueprint analysis failed: {exc}")

    if analysis_data.get("error"):
        return BlueprintBlock(
            success=False,
            analysis=analysis_data,
            message=analysis_data.get("notes", "Analysis failed"),
        )

    import uuid
    dimensions_count = len(analysis_data.get("dimensions", []))
    return BlueprintBlock(
        success=True,
        analysis=analysis_data,
        analysis_id=str(uuid.uuid4()),
        message=f"Detected {dimensions_count} dimensions",
    )


__all__ = [
    "router",
    "AnalyzeGeneratedRequest",
    "AnalyzeGeneratedResponse",
]
