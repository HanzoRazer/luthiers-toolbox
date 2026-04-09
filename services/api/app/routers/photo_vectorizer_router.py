"""
Production Shop — Photo Vectorizer FastAPI Router
=================================================

Wraps the photo-vectorizer service (services/photo-vectorizer/photo_vectorizer_v2.py)
as a Production Shop API endpoint so the ImportView photo drop path can call it.

The pipeline:
    POST /api/vectorizer/extract   ← base64 image upload
        → PhotoVectorizerV2.extract()
        → returns SVG path + bounding box + warnings + metadata
        → ImportView feeds result into useDxfImport.loadFromVectorizerResult()
        → normalise → send to workspace

Add to main.py:
    from photo_vectorizer_router import router as vectorizer_router
    app.include_router(vectorizer_router, prefix="/api/vectorizer")

PYTHONPATH must include:
    services/photo-vectorizer
    services/api
"""

from __future__ import annotations

import base64
import gc
import logging
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Import phase2 file registry for persisting output files
from .blueprint.phase2_router import _output_file_registry

logger = logging.getLogger(__name__)
router = APIRouter(tags=["vectorizer"])


# ─── Memory diagnostics (works in Railway/Linux containers) ──────────────────

def get_memory_mb() -> float:
    """
    Get current process memory (RSS) in MB.
    Uses /proc/self/status on Linux (Railway containers).
    Falls back to -1 if unavailable.
    """
    try:
        with open('/proc/self/status') as f:
            for line in f:
                if line.startswith('VmRSS:'):
                    return int(line.split()[1]) / 1024  # KB to MB
    except Exception:
        pass
    return -1.0


def log_memory(stage: str) -> float:
    """Log memory usage at a given stage, return MB used."""
    mem_mb = get_memory_mb()
    logger.info(f"VECTORIZER_MEM | {stage} | {mem_mb:.0f} MB")
    return mem_mb

# ─── Optional import of the vectorizer (graceful fallback) ────────────────────
#
# The vectorizer lives in services/photo-vectorizer which has heavy deps
# (cv2, rembg, potrace). If they're not installed the endpoint returns
# a 503 with a clear message rather than crashing the whole API.

VECTORIZER_AVAILABLE = False
_vectorizer_error    = ""
_debug_pv_path = ""

def _find_photo_vectorizer_path() -> Optional[Path]:
    """
    Find photo-vectorizer directory. Tries multiple locations to handle
    different Docker build contexts (docker/api/Dockerfile vs services/api/Dockerfile).
    """
    candidates = [
        # docker/api/Dockerfile layout: /app/services/photo-vectorizer
        Path(__file__).parents[3] / "photo-vectorizer",
        # Alternative: /app/services/photo-vectorizer (explicit)
        Path("/app/services/photo-vectorizer"),
        # Local dev: services/photo-vectorizer relative to repo root
        Path(__file__).parents[4] / "services" / "photo-vectorizer",
    ]
    for p in candidates:
        if p.exists():
            return p
    return None

try:
    _pv_path = _find_photo_vectorizer_path()
    _debug_pv_path = str(_pv_path) if _pv_path else "NOT_FOUND"

    if _pv_path and _pv_path.exists():
        if str(_pv_path) not in sys.path:
            sys.path.insert(0, str(_pv_path))

    from photo_vectorizer_v2 import PhotoVectorizerV2  # type: ignore
    VECTORIZER_AVAILABLE = True
except Exception as e:  # audited: http-500 — ValueError,IOError
    _vectorizer_error = str(e)

# ─── Request / response models ────────────────────────────────────────────────

class VectorizeRequest(BaseModel):
    image_b64:          str              # base64-encoded image (JPEG/PNG)
    media_type:         str = "image/jpeg"
    known_width_mm:     Optional[float] = None   # pass guitar body width if known
    correct_perspective:bool = True
    export_svg:         bool = True
    export_dxf:         bool = False
    label:              str  = "photo-extract"
    source_type:        str  = "auto"    # auto, ai, photo, blueprint, silhouette
    gap_closing_level:  str  = "normal"  # normal, aggressive, extreme (blueprint mode only)
    spec_name:          Optional[str] = None  # instrument spec for AI pipeline scaling


# ─── Canonical Artifact Schema (Production Contract) ──────────────────────────

class SVGArtifact(BaseModel):
    present: bool = False
    content: str = ""          # Full SVG string or path_d for ImportView
    path_count: int = 0        # Number of paths in SVG


class DXFArtifact(BaseModel):
    present: bool = False
    base64: str = ""           # Base64-encoded DXF content (no file paths)
    entity_count: int = 0      # LINE/LWPOLYLINE count
    closed_contours: int = 0   # Validated closed contours


class Artifacts(BaseModel):
    svg: SVGArtifact = SVGArtifact()
    dxf: DXFArtifact = DXFArtifact()


class Dimensions(BaseModel):
    width_mm: float = 0.0
    height_mm: float = 0.0
    width_in: float = 0.0
    height_in: float = 0.0
    spec_match: Optional[str] = None
    confidence: float = 0.0


class VectorizeResponse(BaseModel):
    ok:                 bool
    stage:              str   = "complete"  # upload, contour_detection, svg_generation, dxf_generation, validation, complete
    artifacts:          Artifacts = Artifacts()
    dimensions:         Dimensions = Dimensions()
    # Legacy fields (deprecated — use artifacts/dimensions instead)
    svg_path_d:         str   = ""      # combined SVG path for ImportView
    svg_path:           str   = ""      # DEPRECATED: file path (stateless deploy)
    dxf_path:           str   = ""      # DEPRECATED: file path (stateless deploy)
    contour_count:      int   = 0       # for Blueprint workflow compatibility
    line_count:         int   = 0       # for Blueprint workflow compatibility
    body_width_mm:      float = 0.0
    body_height_mm:     float = 0.0
    body_width_in:      float = 0.0
    body_height_in:     float = 0.0
    scale_source:       str   = ""
    bg_method:          str   = ""
    perspective_corrected: bool = False
    warnings:           list[str] = []
    processing_ms:      float = 0.0
    export_blocked:     bool  = False
    export_block_reason:str   = ""
    error:              str   = ""


# ─── Validation Thresholds ────────────────────────────────────────────────────

SVG_MIN_CHARS = 50       # SVG content must be > 50 chars
DXF_MIN_BYTES = 800      # DXF must be > 800 bytes (empty DXF is ~700 bytes)

# ─── Helpers ──────────────────────────────────────────────────────────────────

def _extract_svg_paths(svg_path: str) -> str:
    """
    Pull all <path d="..."> elements from the SVG file and join them
    into a single compound path string suitable for useDxfImport.
    """
    import xml.etree.ElementTree as ET
    try:
        tree = ET.parse(svg_path)
        root = tree.getroot()
        ns = {"svg": "http://www.w3.org/2000/svg"}

        # Log SVG structure for diagnosis
        logger.info(f"SVG_PARSE | file={svg_path}")
        logger.info(f"SVG_PARSE | root_tag={root.tag}")

        # Get viewBox for dimension info
        viewbox = root.get("viewBox", "none")
        width = root.get("width", "none")
        height = root.get("height", "none")
        logger.info(f"SVG_PARSE | viewBox={viewbox} width={width} height={height}")

        # Collect all path d= attributes, filtering out tiny artifacts
        parts: list[str] = []
        for elem in root.iter("{http://www.w3.org/2000/svg}path"):
            d = elem.get("d", "").strip()
            if d and len(d) > 10:
                parts.append(d)
                logger.info(f"SVG_PATH | len={len(d)} preview={d[:100]}...")

        # If no namespaced paths, try without namespace
        if not parts:
            logger.info("SVG_PARSE | No namespaced paths, trying without namespace")
            for elem in root.iter("path"):
                d = elem.get("d", "").strip()
                if d and len(d) > 10:
                    parts.append(d)
                    logger.info(f"SVG_PATH | len={len(d)} preview={d[:100]}...")

        combined = " ".join(parts)
        logger.info(f"SVG_RESULT | paths_found={len(parts)} total_len={len(combined)}")
        return combined
    except Exception as e:  # audited: optional-import
        logger.error(f"SVG_PARSE_ERROR | {e}")
        return ""

# ─── Route ────────────────────────────────────────────────────────────────────

@router.get("/status")
async def vectorizer_status():
    """Health check — confirms whether the vectorizer pipeline is available."""
    # Debug: try to import right now to check current state
    import sys
    try:
        # Check if module is in sys.modules
        has_module = "photo_vectorizer_v2" in sys.modules
        pv_in_path = any("photo-vectorizer" in p for p in sys.path)
    except Exception:
        has_module = False
        pv_in_path = False

    return {
        "available": VECTORIZER_AVAILABLE,
        "error":     _vectorizer_error if not VECTORIZER_AVAILABLE else "",
        "note":      "POST /extract with base64 image when available=true",
        "debug_pv_path": _debug_pv_path,
        "debug_has_module": has_module,
        "debug_pv_in_path": pv_in_path,
    }


@router.post("/extract", response_model=VectorizeResponse)
async def extract_from_photo(req: VectorizeRequest):
    """
    Run the Photo Vectorizer v2 pipeline on an uploaded image.

    Returns the body outline as a compound SVG path that ImportView
    can feed directly into useDxfImport.loadFromVectorizerResult().

    The caller should set known_width_mm if they have a reference
    dimension (e.g. a coin or ruler in the photo, or a known guitar
    body width). Without it, scale_source will be "estimated".
    """
    if not VECTORIZER_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail=(
                f"Photo vectorizer unavailable: {_vectorizer_error}. "
                "Ensure services/photo-vectorizer is on PYTHONPATH and deps installed: "
                "pip install opencv-python rembg"
            )
        )

    t0 = time.time()
    mem_start = log_memory("EXTRACT_START")

    # Log input size for diagnosis
    input_size_kb = len(req.image_b64) * 3 / 4 / 1024  # Approx decoded size
    logger.info(f"VECTORIZER_INPUT | size={input_size_kb:.0f}KB | spec={req.spec_name} | source_type={req.source_type}")

    # ── Decode base64 image ────────────────────────────────────────────────
    try:
        img_bytes = base64.b64decode(req.image_b64)
    except Exception as e:  # audited: http-500 — ValueError,IOError
        raise HTTPException(status_code=422, detail=f"Invalid base64: {e}")

    log_memory("AFTER_DECODE")
    ext = ".jpg" if "jpeg" in req.media_type else ".png"

    with tempfile.TemporaryDirectory() as tmpdir:
        img_path = Path(tmpdir) / f"upload{ext}"
        out_dir  = Path(tmpdir) / "out"
        out_dir.mkdir()

        img_path.write_bytes(img_bytes)
        log_memory("AFTER_WRITE_TEMP")

        # ── Run vectorizer ─────────────────────────────────────────────────
        try:
            log_memory("BEFORE_VECTORIZER_INIT")
            vectorizer = PhotoVectorizerV2()
            log_memory("AFTER_VECTORIZER_INIT")

            logger.info("VECTORIZER_STAGE | Starting extract()")
            result = vectorizer.extract(
                source_path=img_path,
                output_dir=out_dir,
                spec_name=req.spec_name,
                known_dimension_mm=req.known_width_mm,
                correct_perspective=req.correct_perspective,
                export_svg=req.export_svg,
                export_dxf=req.export_dxf,
                export_json=False,
                debug_images=False,
                source_type=req.source_type,
                gap_closing_level=req.gap_closing_level,
            )
            log_memory("AFTER_EXTRACT")

            # Force garbage collection after heavy processing
            gc.collect()
            log_memory("AFTER_GC")

        except Exception as e:  # audited: http-500 — ValueError,IOError
            mem_at_crash = log_memory("EXTRACT_CRASHED")
            logger.error(f"VECTORIZER_CRASH | mem={mem_at_crash:.0f}MB | error={type(e).__name__}: {e}")
            return VectorizeResponse(
                ok=False,
                stage="contour_detection",
                artifacts=Artifacts(),  # Empty artifacts
                dimensions=Dimensions(),
                error=str(e),
                warnings=[f"Pipeline exception: {type(e).__name__}: {e}"],
                processing_ms=round((time.time() - t0) * 1000, 1),
            )

        # Handle multi-instrument result — take the first (largest) body
        if isinstance(result, list):
            result = max(result, key=lambda r: r.body_dimensions_mm[0] * r.body_dimensions_mm[1])

        processing_ms = round((time.time() - t0) * 1000, 1)

        # ── Extract SVG path string ────────────────────────────────────────
        svg_path_d = ""
        if result.output_svg and Path(result.output_svg).exists():
            logger.info(f"SVG_SOURCE | file={result.output_svg}")
            svg_path_d = _extract_svg_paths(result.output_svg)
            logger.info(f"SVG_EXTRACTED | len={len(svg_path_d)} chars")
        else:
            logger.warning(f"SVG_SOURCE | no output_svg or file missing: {result.output_svg}")

        # Fallback: try body_contour points directly if SVG extraction empty
        if not svg_path_d and result.body_contour and hasattr(result.body_contour, "points"):
            pts = result.body_contour.points
            if pts and len(pts) >= 3:
                svg_path_d = "M " + " L ".join(f"{p[0]:.2f},{p[1]:.2f}" for p in pts) + " Z"
                logger.info(f"SVG_FALLBACK | built from {len(pts)} contour points, len={len(svg_path_d)}")

        # Log final path preview for diagnosis
        if svg_path_d:
            logger.info(f"SVG_CONTENT_PREVIEW | {svg_path_d[:200]}...")
        else:
            logger.warning("SVG_CONTENT_PREVIEW | EMPTY - no path data generated")

        # body_dimensions_mm is stored as (height, width) — unpack correctly
        h_mm, w_mm = result.body_dimensions_mm
        h_in, w_in = result.body_dimensions_inch
        logger.info(f"BODY_DIMENSIONS | {w_mm:.1f}mm x {h_mm:.1f}mm")

        # ── Build Artifacts (inline content, no file paths) ────────────────────
        svg_artifact = SVGArtifact()
        dxf_artifact = DXFArtifact()
        contour_count = 0
        stage = "complete"
        validation_errors = []

        # Read full SVG content if available
        svg_content = ""
        if result.output_svg and Path(result.output_svg).exists():
            try:
                svg_content = Path(result.output_svg).read_text(encoding='utf-8')
                path_count = svg_content.count('<path')
                svg_artifact = SVGArtifact(
                    present=len(svg_content) > SVG_MIN_CHARS,
                    content=svg_content,
                    path_count=path_count
                )
                contour_count = path_count if path_count > 0 else 1
                logger.info(f"SVG_ARTIFACT | present={svg_artifact.present} chars={len(svg_content)} paths={path_count}")
            except Exception as e:
                logger.error(f"SVG_READ_ERROR | {e}")
                validation_errors.append(f"SVG read failed: {e}")
                stage = "svg_generation"
        elif svg_path_d:
            # Fallback: wrap path_d in minimal SVG
            svg_content = f'<svg xmlns="http://www.w3.org/2000/svg"><path d="{svg_path_d}"/></svg>'
            svg_artifact = SVGArtifact(
                present=len(svg_path_d) > SVG_MIN_CHARS,
                content=svg_content,
                path_count=1
            )
            contour_count = 1
            logger.info(f"SVG_ARTIFACT | fallback from path_d, len={len(svg_path_d)}")

        # Read and encode DXF content if available
        dxf_b64 = ""
        entity_count = 0
        if result.output_dxf and Path(result.output_dxf).exists():
            try:
                dxf_bytes = Path(result.output_dxf).read_bytes()
                dxf_b64 = base64.b64encode(dxf_bytes).decode('ascii')

                # Count LINE entities in DXF
                dxf_text = dxf_bytes.decode('utf-8', errors='ignore')
                entity_count = dxf_text.count('\nLINE\n') + dxf_text.count('\nLWPOLYLINE\n')

                dxf_artifact = DXFArtifact(
                    present=len(dxf_bytes) > DXF_MIN_BYTES and entity_count > 0,
                    base64=dxf_b64,
                    entity_count=entity_count,
                    closed_contours=contour_count
                )
                logger.info(f"DXF_ARTIFACT | present={dxf_artifact.present} bytes={len(dxf_bytes)} entities={entity_count}")
            except Exception as e:
                logger.error(f"DXF_READ_ERROR | {e}")
                validation_errors.append(f"DXF read failed: {e}")
                stage = "dxf_generation"
        else:
            logger.warning(f"DXF_ARTIFACT | no output_dxf or file missing: {result.output_dxf}")
            if req.export_dxf:
                validation_errors.append("DXF requested but not generated")
                stage = "dxf_generation"

        # ── Validation Gate ─────────────────────────────────────────────────
        # Success requires BOTH artifacts when both are requested
        is_valid = True
        if req.export_svg and not svg_artifact.present:
            is_valid = False
            validation_errors.append("SVG artifact missing or invalid")
            if stage == "complete":
                stage = "validation"
        if req.export_dxf and not dxf_artifact.present:
            is_valid = False
            validation_errors.append("DXF artifact missing or invalid")
            if stage == "complete":
                stage = "validation"

        # Block if export was blocked upstream
        if result.export_blocked:
            is_valid = False
            stage = "contour_detection"
            validation_errors.append(result.export_block_reason or "Export blocked")

        # Build artifacts object
        artifacts = Artifacts(svg=svg_artifact, dxf=dxf_artifact)
        dimensions = Dimensions(
            width_mm=round(w_mm, 2),
            height_mm=round(h_mm, 2),
            width_in=round(w_in, 3),
            height_in=round(h_in, 3),
            spec_match=req.spec_name,
            confidence=0.9 if is_valid else 0.0
        )

        # Final diagnostics
        mem_final = log_memory("EXTRACT_COMPLETE")
        total_elapsed = time.time() - t0
        logger.info(
            f"VECTORIZER_RESULT | ok={is_valid} stage={stage} elapsed={total_elapsed:.1f}s | "
            f"mem_delta={mem_final - mem_start:.0f}MB | "
            f"body={w_mm:.0f}x{h_mm:.0f}mm | svg={svg_artifact.present} dxf={dxf_artifact.present}"
        )

        # Combine warnings
        all_warnings = list(result.warnings) + validation_errors

        return VectorizeResponse(
            ok=is_valid and not result.export_blocked,
            stage=stage,
            artifacts=artifacts,
            dimensions=dimensions,
            # Legacy fields for backward compatibility
            svg_path_d=svg_path_d,
            svg_path="",  # DEPRECATED: no file paths in stateless deploy
            dxf_path="",  # DEPRECATED: no file paths in stateless deploy
            contour_count=contour_count,
            line_count=entity_count,
            body_width_mm=round(w_mm, 2),
            body_height_mm=round(h_mm, 2),
            body_width_in=round(w_in, 3),
            body_height_in=round(h_in, 3),
            scale_source=result.calibration.source.value if result.calibration else "estimated",
            bg_method=result.bg_method_used,
            perspective_corrected=result.perspective_corrected,
            warnings=all_warnings,
            processing_ms=processing_ms,
            export_blocked=result.export_blocked,
            export_block_reason=result.export_block_reason or "",
            error="; ".join(validation_errors) if validation_errors else "",
        )
