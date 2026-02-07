# services/api/app/vision/router.py
"""
Vision Producer Plane - Canonical API for AI Image Generation

This module provides the producer plane for the hybrid architecture:
- Generates assets via AI providers
- Writes to CAS (Content-Addressed Storage)
- Returns sha256 as the authoritative identity

The Ledger Plane (RMOS) handles attach/review/promote governance.
"""
from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form
from pydantic import BaseModel

from app.ai.transport import get_image_client, get_vision_client
from app.rmos.runs_v2.attachments import put_bytes_attachment
from app.vision.vocabulary import as_dict as vision_vocabulary
from app.vision.prompt_engine import engineer_guitar_prompt
from app.vision.schemas import (
    VisionAsset,
    VisionGenerateRequest,
    VisionGenerateResponse,
    VisionPromptPreviewRequest,
    VisionPromptPreviewResponse,
    VisionVocabularyResponse,
    SegmentRequest,
    SegmentResponse,
    PhotoToGcodeRequest,
    PhotoToGcodeResponse,
)
from app.vision.segmentation_service import (
    GuitarSegmentationService,
    SegmentationResult,
    SegmentationError,
)

router = APIRouter(prefix="/api/vision", tags=["Vision"])


class ProvidersResponse(BaseModel):
    providers: List[Dict[str, Any]]


def _extract_request_id(req: Request) -> str:
    return req.headers.get("x-request-id") or ""


def _format_to_mime(fmt: str) -> str:
    """Convert format string to MIME type."""
    mapping = {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "webp": "image/webp",
    }
    return mapping.get(fmt.lower(), "image/png")


def _filename(provider: str, model: str, size: str, fmt: str, i: int) -> str:
    ext = f".{fmt}" if fmt else ".png"
    safe_model = (model or "model").replace("/", "_").replace(" ", "_")
    return f"vision_{provider}_{safe_model}_{size}_{i+1}{ext}"


def _blob_download_url(sha256: str) -> str:
    """Return browser-loadable URL for CAS blob (same-origin, no auth required)."""
    return f"/api/advisory/blobs/{sha256}/download"


@router.get("/providers", response_model=ProvidersResponse)
def list_providers() -> ProvidersResponse:
    """List available AI image providers and their configuration status."""
    providers = []
    for name in ("openai", "stub"):
        try:
            c = get_image_client(provider=name)
            configured = bool(getattr(c, "is_configured", True))
        except HTTPException:
            raise
        except Exception:  # WP-1: governance catch-all — HTTP endpoint
            configured = False
        providers.append({"name": name, "configured": configured})
    return ProvidersResponse(providers=providers)


@router.post("/generate", response_model=VisionGenerateResponse)
def generate(req: Request, payload: VisionGenerateRequest) -> VisionGenerateResponse:
    """
    Generate images via AI provider and store in CAS.

    Returns assets with sha256 identity for subsequent RMOS attachment.
    """
    request_id = _extract_request_id(req)

    try:
        client = get_image_client(provider=payload.provider)
    except HTTPException:
        raise
    except Exception as e:  # WP-1: governance catch-all — HTTP endpoint
        raise HTTPException(status_code=409, detail=f"AI_PROVIDER_NOT_CONFIGURED: {payload.provider}") from e

    if getattr(client, "is_configured", True) is False:
        raise HTTPException(status_code=409, detail=f"AI_PROVIDER_NOT_CONFIGURED: {payload.provider}")

    assets: List[VisionAsset] = []

    for i in range(payload.num_images):
        try:
            # Use the canonical .generate() method from ImageClient
            response = client.generate(
                prompt=payload.prompt,
                model=payload.model,
                size=payload.size,
                quality=payload.quality,
            )
        except HTTPException:
            raise
        except Exception as e:  # WP-1: governance catch-all — HTTP endpoint
            raise HTTPException(status_code=502, detail=f"AI_PROVIDER_UNAVAILABLE: {str(e)}") from e

        # Extract from ImageResponse dataclass
        img_bytes = response.image_bytes
        fmt = response.format or "png"
        mime = _format_to_mime(fmt)
        model_used = response.model or payload.model or ""
        revised_prompt = response.revised_prompt

        # CAS store via canonical RMOS attachments module (content-addressed)
        try:
            attachment, _storage_path = put_bytes_attachment(
                img_bytes,
                kind="advisory",
                mime=mime,
                filename=_filename(payload.provider, model_used, payload.size, fmt, i),
            )
        except HTTPException:
            raise
        except Exception as e:  # WP-1: governance catch-all — HTTP endpoint
            raise HTTPException(status_code=500, detail=f"CAS_WRITE_FAILED: {str(e)}") from e

        assets.append(
            VisionAsset(
                sha256=attachment.sha256,
                url=_blob_download_url(attachment.sha256),
                mime=attachment.mime,
                filename=attachment.filename,
                size_bytes=attachment.size_bytes,
                provider=str(payload.provider),
                model=model_used,
                revised_prompt=revised_prompt,
                request_id=request_id,
            )
        )

    return VisionGenerateResponse(assets=assets, request_id=request_id)


@router.get("/vocabulary", response_model=VisionVocabularyResponse)
def get_vocabulary() -> VisionVocabularyResponse:
    """Return vocabulary lists for UI dropdowns."""
    return VisionVocabularyResponse(vocabulary=vision_vocabulary())


@router.post("/prompt", response_model=VisionPromptPreviewResponse)
def preview_prompt(payload: VisionPromptPreviewRequest) -> VisionPromptPreviewResponse:
    """Return an engineered prompt preview (no generation)."""
    p = engineer_guitar_prompt(payload.prompt, style=payload.style)
    return VisionPromptPreviewResponse(
        raw_prompt=p.raw_prompt,
        engineered_prompt=p.engineered_prompt,
        photography_style=p.photography_style,
    )


@router.post("/feedback")
def feedback() -> Dict[str, Any]:
    """Deprecated endpoint.

    Frontend should use RMOS advisory review/promote as the governance path.
    This endpoint remains for backward compatibility but does not affect routing.
    """
    return {"ok": True, "message": "feedback endpoint deprecated; use RMOS review/promote"}


# ---------------------------------------------------------------------------
# Segmentation Endpoints
# ---------------------------------------------------------------------------


@router.post("/segment", response_model=SegmentResponse)
async def segment_guitar(
    file: UploadFile = File(..., description="Guitar image (PNG, JPG, WebP)"),
    target_width_mm: float = Form(400.0, description="Target body width in mm"),
    simplify_tolerance_mm: float = Form(1.0, description="Simplification tolerance in mm"),
    guitar_category: str = Form("auto", description="Guitar type: auto, acoustic, electric"),
    output_format: str = Form("json", description="Output: json, dxf, svg, all"),
) -> SegmentResponse:
    """
    Segment guitar body from uploaded image using AI vision.

    Extracts the guitar body outline as a polygon, optionally exporting
    to DXF or SVG format for CAM processing.

    Pipeline:
    1. Send image to GPT-4o Vision
    2. Extract body polygon coordinates
    3. Scale to target dimensions (mm)
    4. Simplify and ensure proper winding
    5. Optionally export to DXF/SVG

    Returns polygon coordinates and optional asset URLs.
    """
    # Validate file type
    if file.content_type not in ("image/png", "image/jpeg", "image/webp"):
        return SegmentResponse(
            ok=False,
            error=f"Unsupported image type: {file.content_type}. Use PNG, JPG, or WebP."
        )

    # Read image bytes
    try:
        image_bytes = await file.read()
        if len(image_bytes) > 10 * 1024 * 1024:  # 10MB limit
            return SegmentResponse(
                ok=False,
                error="Image too large. Maximum size is 10MB."
            )
    except HTTPException:
        raise
    except Exception as e:  # WP-1: governance catch-all — HTTP endpoint
        return SegmentResponse(ok=False, error=f"Failed to read image: {e}")

    # Initialize service
    try:
        vision_client = get_vision_client("openai")
        service = GuitarSegmentationService(vision_client)
    except HTTPException:
        raise
    except Exception as e:  # WP-1: governance catch-all — HTTP endpoint
        raise HTTPException(status_code=503, detail=f"Vision service unavailable: {e}")

    # Run segmentation
    result = service.segment(
        image_bytes=image_bytes,
        target_width_mm=target_width_mm,
        simplify_tolerance_mm=simplify_tolerance_mm,
        guitar_category=guitar_category,
    )

    # Handle error
    if isinstance(result, SegmentationError):
        return SegmentResponse(
            ok=False,
            error=result.error,
            confidence=result.confidence,
        )

    # Build response
    response = SegmentResponse(
        ok=True,
        polygon=[[p[0], p[1]] for p in result.polygon_mm],
        confidence=result.confidence,
        guitar_type=result.guitar_type,
        point_count=result.point_count,
        target_width_mm=result.target_width_mm,
        target_height_mm=result.target_height_mm,
        notes=result.notes,
    )

    # Export to DXF if requested
    if output_format in ("dxf", "all"):
        try:
            dxf_bytes = service.export_to_dxf(result)
            attachment, _ = put_bytes_attachment(
                dxf_bytes,
                kind="advisory",
                mime="application/dxf",
                filename=f"guitar_body_{result.guitar_type}.dxf",
            )
            response.dxf_sha256 = attachment.sha256
            response.dxf_url = _blob_download_url(attachment.sha256)
        except HTTPException:
            raise
        except Exception as e:  # WP-1: governance catch-all — HTTP endpoint
            response.notes += f" DXF export failed: {e}"

    # Export to SVG if requested
    if output_format in ("svg", "all"):
        try:
            svg_content = service.export_to_svg(result)
            svg_bytes = svg_content.encode("utf-8")
            attachment, _ = put_bytes_attachment(
                svg_bytes,
                kind="advisory",
                mime="image/svg+xml",
                filename=f"guitar_body_{result.guitar_type}.svg",
            )
            response.svg_sha256 = attachment.sha256
            response.svg_url = _blob_download_url(attachment.sha256)
        except HTTPException:
            raise
        except Exception as e:  # WP-1: governance catch-all — HTTP endpoint
            response.notes += f" SVG export failed: {e}"

    return response


@router.post("/photo-to-gcode", response_model=PhotoToGcodeResponse)
async def photo_to_gcode(
    file: UploadFile = File(..., description="Guitar image (PNG, JPG, WebP)"),
    target_width_mm: float = Form(400.0, description="Target body width in mm"),
    simplify_tolerance_mm: float = Form(1.0, description="Simplification tolerance"),
    guitar_category: str = Form("auto", description="Guitar type hint"),
    tool_diameter_mm: float = Form(6.0, description="Tool diameter in mm"),
    stepover: float = Form(0.45, description="Stepover fraction"),
    stepdown_mm: float = Form(2.0, description="Stepdown per pass in mm"),
    feed_rate_mm_min: float = Form(1200.0, description="Feed rate mm/min"),
    post_processor: str = Form("GRBL", description="Post processor"),
) -> PhotoToGcodeResponse:
    """
    Complete pipeline: Photo → AI Segmentation → DXF → G-code

    Extracts guitar body outline from image and generates CNC-ready G-code
    for pocket machining operations.

    Pipeline:
    1. AI Vision (GPT-4o) extracts body outline
    2. Polygon scaled and simplified
    3. DXF generated for CAM
    4. Adaptive pocket toolpath planned
    5. G-code generated with post-processor

    Returns:
    - SVG preview of segmented outline
    - DXF file for CAM software
    - G-code file ready for CNC
    - CAM statistics (area, time, moves)
    """
    from app.routers.adaptive_router import Loop, PlanIn, plan

    # Validate file type
    if file.content_type not in ("image/png", "image/jpeg", "image/webp"):
        return PhotoToGcodeResponse(
            ok=False,
            error=f"Unsupported image type: {file.content_type}"
        )

    # Read image
    try:
        image_bytes = await file.read()
        if len(image_bytes) > 10 * 1024 * 1024:
            return PhotoToGcodeResponse(ok=False, error="Image too large (max 10MB)")
    except HTTPException:
        raise
    except Exception as e:  # WP-1: governance catch-all — HTTP endpoint
        return PhotoToGcodeResponse(ok=False, error=f"Failed to read image: {e}")

    # Step 1: AI Segmentation
    try:
        vision_client = get_vision_client("openai")
        service = GuitarSegmentationService(vision_client)
        seg_result = service.segment(
            image_bytes=image_bytes,
            target_width_mm=target_width_mm,
            simplify_tolerance_mm=simplify_tolerance_mm,
            guitar_category=guitar_category,
        )
    except HTTPException:
        raise
    except Exception as e:  # WP-1: governance catch-all — HTTP endpoint
        return PhotoToGcodeResponse(ok=False, error=f"Segmentation failed: {e}")

    if isinstance(seg_result, SegmentationError):
        return PhotoToGcodeResponse(
            ok=False,
            error=seg_result.error,
            confidence=seg_result.confidence,
        )

    # Step 2: Generate SVG preview
    svg_url = None
    try:
        svg_content = service.export_to_svg(seg_result)
        svg_bytes = svg_content.encode("utf-8")
        attachment, _ = put_bytes_attachment(
            svg_bytes,
            kind="advisory",
            mime="image/svg+xml",
            filename=f"guitar_body_{seg_result.guitar_type}_preview.svg",
        )
        svg_url = _blob_download_url(attachment.sha256)
    except HTTPException:
        raise
    except Exception:  # WP-1: governance catch-all — HTTP endpoint
        pass  # Non-fatal

    # Step 3: Generate DXF
    dxf_url = None
    try:
        dxf_bytes = service.export_to_dxf(seg_result)
        attachment, _ = put_bytes_attachment(
            dxf_bytes,
            kind="advisory",
            mime="application/dxf",
            filename=f"guitar_body_{seg_result.guitar_type}.dxf",
        )
        dxf_url = _blob_download_url(attachment.sha256)
    except HTTPException:
        raise
    except Exception as e:  # WP-1: governance catch-all — HTTP endpoint
        return PhotoToGcodeResponse(
            ok=False,
            error=f"DXF generation failed: {e}",
            confidence=seg_result.confidence,
            guitar_type=seg_result.guitar_type,
        )

    # Step 4: Create CAM plan
    try:
        # Convert polygon to Loop format
        loop = Loop(pts=[tuple(p) for p in seg_result.polygon_mm])

        plan_request = PlanIn(
            loops=[loop],
            units="mm",
            tool_d=tool_diameter_mm,
            stepover=stepover,
            stepdown=stepdown_mm,
            margin=0.5,
            strategy="Spiral",
            feed_xy=feed_rate_mm_min,
            safe_z=5.0,
            z_rough=-stepdown_mm,
        )

        # Call planner
        plan_result = plan(plan_request)
    except HTTPException:
        raise
    except Exception as e:  # WP-1: governance catch-all — HTTP endpoint
        return PhotoToGcodeResponse(
            ok=False,
            error=f"CAM planning failed: {e}",
            confidence=seg_result.confidence,
            guitar_type=seg_result.guitar_type,
            svg_preview_url=svg_url,
            dxf_url=dxf_url,
        )

    # Step 5: Generate G-code from plan
    gcode_url = None
    cam_stats = None
    try:
        # Convert plan moves to G-code
        moves = plan_result.get("moves", []) if isinstance(plan_result, dict) else plan_result.moves
        stats = plan_result.get("stats", {}) if isinstance(plan_result, dict) else plan_result.stats
        cam_stats = stats

        # Build G-code
        gcode_lines = [
            f"; Guitar Body Pocket - {seg_result.guitar_type}",
            f"; Generated by Luthier's Toolbox Photo-to-Gcode Pipeline",
            f"; Tool: {tool_diameter_mm}mm, Stepover: {stepover}, Feed: {feed_rate_mm_min}mm/min",
            "",
            "G90 G17 G21",  # Absolute, XY plane, mm
            f"G0 Z{5.0:.3f}",  # Safe Z
            "",
        ]

        for move in moves:
            code = move.get("code", "G1")
            x = move.get("x")
            y = move.get("y")
            z = move.get("z")
            f = move.get("f")

            parts = [code]
            if x is not None:
                parts.append(f"X{x:.3f}")
            if y is not None:
                parts.append(f"Y{y:.3f}")
            if z is not None:
                parts.append(f"Z{z:.3f}")
            if f is not None and code != "G0":
                parts.append(f"F{f:.0f}")

            gcode_lines.append(" ".join(parts))

        gcode_lines.extend(["", "G0 Z5.0", "M30", ""])
        gcode_content = "\n".join(gcode_lines)

        # Store G-code in CAS
        gcode_bytes = gcode_content.encode("utf-8")
        attachment, _ = put_bytes_attachment(
            gcode_bytes,
            kind="advisory",
            mime="text/plain",
            filename=f"guitar_body_{seg_result.guitar_type}_{post_processor}.nc",
        )
        gcode_url = _blob_download_url(attachment.sha256)
    except HTTPException:
        raise
    except Exception as e:  # WP-1: governance catch-all — HTTP endpoint
        return PhotoToGcodeResponse(
            ok=False,
            error=f"G-code generation failed: {e}",
            confidence=seg_result.confidence,
            guitar_type=seg_result.guitar_type,
            svg_preview_url=svg_url,
            dxf_url=dxf_url,
        )

    return PhotoToGcodeResponse(
        ok=True,
        confidence=seg_result.confidence,
        guitar_type=seg_result.guitar_type,
        polygon_points=seg_result.point_count,
        svg_preview_url=svg_url,
        dxf_url=dxf_url,
        gcode_url=gcode_url,
        cam_stats=cam_stats,
    )
