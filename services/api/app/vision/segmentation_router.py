"""Vision Segmentation Router - AI Vision/Segmentation Endpoints.

Provides:
- POST /segment - Segment guitar body from image
- POST /photo-to-gcode - Complete pipeline: Photo → AI → DXF → G-code

LANE: PRODUCER (analyzes images via AI, writes to CAS)
"""
# NOTE: Do NOT use "from __future__ import annotations" here - causes Pydantic ForwardRef issues
from typing import Optional, Dict, Any, List, Union

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Request

from app.middleware.rate_limit import limiter, rate_limit_tier

from app.ai.transport import get_vision_client
from app.rmos.runs_v2.attachments import put_bytes_attachment
from app.vision.schemas import (
    SegmentResponse,
    PhotoToGcodeResponse,
)
from app.vision.segmentation_service import (
    GuitarSegmentationService,
    SegmentationError,
)

router = APIRouter(tags=["Vision", "Segmentation"])


def _blob_download_url(sha256: str) -> str:
    """Return browser-loadable URL for CAS blob (same-origin, no auth required)."""
    return f"/api/advisory/blobs/{sha256}/download"


@router.post("/segment", response_model=SegmentResponse, summary="Segment guitar body from image")
@limiter.limit(rate_limit_tier("ai"))
async def segment_guitar(
    request: Request,
    file: UploadFile = File(..., description="Guitar image (PNG, JPG, WebP)"),
    target_width_mm: float = Form(400.0, description="Target body width in mm"),
    simplify_tolerance_mm: float = Form(1.0, description="Simplification tolerance in mm"),
    guitar_category: str = Form("auto", description="Guitar type: auto, acoustic, electric, other"),
    output_format: str = Form("json", description="Output: json, dxf, svg, all"),
) -> SegmentResponse:
    """Segment guitar body from uploaded image using AI vision."""
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
    except (OSError, ValueError) as e:  # WP-1: governance catch-all — HTTP endpoint
        return SegmentResponse(ok=False, error=f"Failed to read image: {e}")

    # Initialize service
    try:
        vision_client = get_vision_client("openai")
        service = GuitarSegmentationService(vision_client)
    except HTTPException:
        raise
    except (ValueError, TypeError, RuntimeError, OSError) as e:  # WP-1: governance catch-all — HTTP endpoint
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
        except (ValueError, TypeError, OSError, RuntimeError) as e:  # WP-1: governance catch-all — HTTP endpoint
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
        except (ValueError, TypeError, OSError, RuntimeError) as e:  # WP-1: governance catch-all — HTTP endpoint
            response.notes += f" SVG export failed: {e}"

    return response


@router.post("/photo-to-gcode", response_model=PhotoToGcodeResponse, summary="Convert photo to G-code")
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
    """Complete pipeline: Photo → AI Segmentation → DXF → G-code"""
    from app.routers.adaptive_schemas import Loop, PlanIn
    from app.routers.adaptive.plan_router import plan

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
    except (OSError, ValueError) as e:  # WP-1: governance catch-all — HTTP endpoint
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
    except (ValueError, TypeError, RuntimeError, OSError) as e:  # WP-1: governance catch-all — HTTP endpoint
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
    except (ValueError, TypeError, OSError, RuntimeError):  # WP-1: governance catch-all — HTTP endpoint
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
    except (ValueError, TypeError, OSError, RuntimeError) as e:  # WP-1: governance catch-all — HTTP endpoint
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
    except (ValueError, TypeError, KeyError, RuntimeError) as e:  # WP-1: governance catch-all — HTTP endpoint
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
            f"; Generated by The Production Shop Photo-to-Gcode Pipeline",
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
    except (KeyError, ValueError, TypeError, OSError, RuntimeError) as e:  # WP-1: governance catch-all — HTTP endpoint
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


__all__ = ["router"]
