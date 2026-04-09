"""
Blueprint Vectorize Router (Consolidated)
==========================================

Single production endpoint for blueprint vectorization.
Replaces the multi-stage edge-to-dxf + clean flow.

Accepts image or PDF, returns final validated artifacts.

Endpoint:
    POST /api/blueprint/vectorize

Author: Production Shop
"""

from __future__ import annotations

import base64
import logging
import os
import tempfile
import time
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from ...utils.stage_timer import DebugInfo, StageTimer, is_debug_enabled

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Blueprint Vectorize"])


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


# ─── Validation Thresholds ────────────────────────────────────────────────────

SVG_MIN_CHARS = 50
DXF_MIN_BYTES = 800


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
    timer = StageTimer()
    debug_info = DebugInfo()
    warnings: list[str] = []

    # Check if debug output is allowed
    include_debug = debug and is_debug_enabled()

    try:
        # ─── Stage: File upload/load ──────────────────────────────────────
        with timer.stage("upload"):
            content = await file.read()
            filename = file.filename or "upload"
            file_ext = Path(filename).suffix.lower()

            if not content:
                return BlueprintVectorizeResponse(
                    ok=False, stage="upload", error="Empty file uploaded"
                )

            logger.info(f"BLUEPRINT_VECTORIZE | file={filename} size={len(content)} bytes")

        # ─── Stage: Image extraction (PDF → image if needed) ─────────────
        with timer.stage("image_extract"):
            if file_ext == ".pdf":
                image_bytes = _extract_pdf_page(content, page_num)
                if not image_bytes:
                    return BlueprintVectorizeResponse(
                        ok=False,
                        stage="image_extract",
                        error=f"Failed to extract page {page_num} from PDF",
                    )
            else:
                image_bytes = content

        # Write to temp file for edge_to_dxf
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            input_path = tmpdir_path / f"input{file_ext if file_ext != '.pdf' else '.png'}"
            input_path.write_bytes(image_bytes)

            # ─── Stage: Edge detection + DXF generation ───────────────────
            with timer.stage("edge_to_dxf"):
                edge_result = _run_edge_to_dxf(
                    str(input_path),
                    str(tmpdir_path / "raw_edges.dxf"),
                    target_height_mm,
                )

                if not edge_result:
                    return BlueprintVectorizeResponse(
                        ok=False,
                        stage="edge_to_dxf",
                        error="Edge detection failed",
                    )

                # Merge service-level timings
                if hasattr(edge_result, "stage_timings"):
                    for k, v in edge_result.stage_timings.items():
                        timer.mark(f"edge_{k.replace('_ms', '')}", v)

            # ─── Stage: Contour cleanup/filtering ─────────────────────────
            with timer.stage("clean"):
                clean_result = _run_cleaner(
                    edge_result.output_path,
                    str(tmpdir_path / "cleaned.dxf"),
                    min_contour_length_mm,
                    close_gaps_mm,
                )

                if not clean_result or not clean_result.get("success"):
                    error_msg = clean_result.get("error", "Cleanup failed") if clean_result else "Cleanup failed"
                    return BlueprintVectorizeResponse(
                        ok=False,
                        stage="clean",
                        error=error_msg,
                        metrics={
                            "original_entities": edge_result.line_count,
                            "contours_found": 0,
                        },
                    )

            # ─── Stage: SVG generation ────────────────────────────────────
            with timer.stage("svg_generate"):
                svg_content = clean_result.get("svg_preview", "")
                svg_path_count = svg_content.count("<path") if svg_content else 0

            # ─── Stage: DXF read + encode ─────────────────────────────────
            with timer.stage("dxf_encode"):
                cleaned_dxf_path = tmpdir_path / "cleaned.dxf"
                dxf_b64 = ""
                dxf_entity_count = 0

                if cleaned_dxf_path.exists():
                    dxf_bytes = cleaned_dxf_path.read_bytes()
                    dxf_b64 = base64.b64encode(dxf_bytes).decode("ascii")
                    # Count entities
                    dxf_text = dxf_bytes.decode("utf-8", errors="ignore")
                    dxf_entity_count = dxf_text.count("\nLINE\n") + dxf_text.count("\nLWPOLYLINE\n")

            # ─── Validation gate ──────────────────────────────────────────
            svg_valid = len(svg_content) > SVG_MIN_CHARS
            dxf_valid = len(dxf_b64) > 0 and dxf_entity_count > 0

            if not svg_valid:
                warnings.append("SVG content below minimum threshold")
            if not dxf_valid:
                warnings.append("DXF content missing or empty")

            is_ok = svg_valid and dxf_valid

            # Build artifacts
            artifacts = Artifacts(
                svg=SVGArtifact(
                    present=svg_valid,
                    content=svg_content,
                    path_count=svg_path_count,
                ),
                dxf=DXFArtifact(
                    present=dxf_valid,
                    base64=dxf_b64,
                    entity_count=dxf_entity_count,
                    closed_contours=clean_result.get("contours_found", 0),
                ),
            )

            dimensions = Dimensions(
                width_mm=edge_result.output_size_mm[0],
                height_mm=edge_result.output_size_mm[1],
            )

            metrics = {
                "original_entities": edge_result.line_count,
                "cleaned_entities": clean_result.get("cleaned_entity_count", 0),
                "contours_found": clean_result.get("contours_found", 0),
                "chains_found": clean_result.get("chains_found", 0),
                "processing_ms": timer.total_ms,
            }

            # Log timing summary
            timer.log_summary("BLUEPRINT_VECTORIZE")

            # Build debug info if requested
            debug_dict = None
            if include_debug:
                debug_info.stage_timings = timer.get_timings()
                debug_dict = debug_info.to_dict()

            return BlueprintVectorizeResponse(
                ok=is_ok,
                stage="complete" if is_ok else "validation",
                error="" if is_ok else "; ".join(warnings),
                warnings=warnings,
                artifacts=artifacts,
                dimensions=dimensions,
                metrics=metrics,
                debug=debug_dict,
            )

    except Exception as e:
        logger.exception("Blueprint vectorization failed")
        return BlueprintVectorizeResponse(
            ok=False,
            stage="error",
            error=str(e),
            debug={"stage_timings": timer.get_timings()} if include_debug else None,
        )


# ─── Internal Helpers ─────────────────────────────────────────────────────────

def _extract_pdf_page(pdf_bytes: bytes, page_num: int) -> Optional[bytes]:
    """Extract a page from PDF as PNG bytes."""
    try:
        import fitz  # PyMuPDF

        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        if page_num >= len(doc):
            logger.error(f"Page {page_num} out of range (PDF has {len(doc)} pages)")
            return None

        page = doc[page_num]
        # Render at 2x for better quality
        mat = fitz.Matrix(2.0, 2.0)
        pix = page.get_pixmap(matrix=mat)
        return pix.tobytes("png")

    except ImportError:
        logger.error("PyMuPDF (fitz) not available for PDF extraction")
        return None
    except Exception as e:
        logger.error(f"PDF extraction failed: {e}")
        return None


def _run_edge_to_dxf(input_path: str, output_path: str, target_height_mm: float):
    """Run edge-to-DXF conversion."""
    try:
        # Import from photo-vectorizer service
        import sys
        from pathlib import Path as PPath

        # Add photo-vectorizer to path if needed
        pv_path = PPath(__file__).parents[4] / "photo-vectorizer"
        if pv_path.exists() and str(pv_path) not in sys.path:
            sys.path.insert(0, str(pv_path))

        # Try alternative path for Docker
        alt_path = PPath("/app/services/photo-vectorizer")
        if alt_path.exists() and str(alt_path) not in sys.path:
            sys.path.insert(0, str(alt_path))

        from edge_to_dxf import EdgeToDXF

        converter = EdgeToDXF()
        return converter.convert(
            input_path,
            output_path=output_path,
            target_height_mm=target_height_mm,
        )

    except Exception as e:
        logger.error(f"Edge-to-DXF failed: {e}")
        return None


def _run_cleaner(input_path: str, output_path: str, min_length: float, close_gaps: float) -> Optional[dict]:
    """Run DXF cleaner."""
    try:
        from ...cam.unified_dxf_cleaner import DXFCleaner

        cleaner = DXFCleaner(
            min_contour_length_mm=min_length,
            closure_tolerance=close_gaps,
            keep_open_chains=False,
        )

        result = cleaner.clean_file(input_path, output_path)

        if not result.success:
            return {"success": False, "error": result.error}

        # Generate SVG preview if we have contours
        svg_preview = ""
        if result.contours_found > 0:
            try:
                import ezdxf
                from ...cam.unified_dxf_cleaner import Chain, Point

                doc = ezdxf.readfile(output_path)
                msp = doc.modelspace()

                chains = []
                for e in msp:
                    if e.dxftype() == "LWPOLYLINE":
                        points = [Point(x, y) for x, y in e.get_points("xy")]
                        if points:
                            chains.append(Chain(points=points))

                if chains:
                    svg_preview = cleaner.generate_svg_preview(chains)

            except Exception as e:
                logger.warning(f"SVG preview generation failed: {e}")

        return {
            "success": True,
            "svg_preview": svg_preview,
            "original_entity_count": result.original_entity_count,
            "cleaned_entity_count": result.cleaned_entity_count,
            "contours_found": result.contours_found,
            "chains_found": result.chains_found,
            "discarded_short": result.discarded_short,
            "discarded_open": result.discarded_open,
        }

    except Exception as e:
        logger.error(f"DXF cleaner failed: {e}")
        return {"success": False, "error": str(e)}
