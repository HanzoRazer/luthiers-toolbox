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
import sys
import time
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..utils.stage_timer import is_debug_enabled
from ..services.photo_orchestrator import PhotoOrchestrator

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

# Singleton orchestrator instance
_orchestrator = PhotoOrchestrator()

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
    debug:              bool = False     # Include diagnostics (requires VECTORIZER_DEBUG=1)


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
    debug:              Optional[dict] = None  # Ownership diagnostics (requires VECTORIZER_DEBUG=1)


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

    Architecture note: Business logic has been moved to PhotoOrchestrator.
    This router is now a thin HTTP wrapper that handles:
    - Request decoding
    - Input validation
    - Legacy field mapping
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

    # ── Determine filename from media type ─────────────────────────────────
    ext = ".jpg" if "jpeg" in req.media_type else ".png"
    filename = f"upload{ext}"

    # ── Check if debug output is allowed ───────────────────────────────────
    include_debug = req.debug and is_debug_enabled()

    # ── Delegate to orchestrator ───────────────────────────────────────────
    result = _orchestrator.process_image(
        image_bytes=img_bytes,
        filename=filename,
        spec_name=req.spec_name,
        known_dimension_mm=req.known_width_mm,
        correct_perspective=req.correct_perspective,
        export_svg=req.export_svg,
        export_dxf=req.export_dxf,
        source_type=req.source_type,
        gap_closing_level=req.gap_closing_level,
        debug=include_debug,
    )

    # Force garbage collection after heavy processing
    gc.collect()
    log_memory("AFTER_ORCHESTRATOR")

    processing_ms = round((time.time() - t0) * 1000, 1)

    # ── Extract svg_path_d for legacy compatibility ────────────────────────
    svg_path_d = ""
    if result.svg.present and result.svg.content:
        svg_path_d = _extract_svg_path_d_from_content(result.svg.content)

    # ── Build response with legacy field mapping ───────────────────────────
    # Canonical fields come from orchestrator result
    # Legacy fields are mapped for backward compatibility
    artifacts = Artifacts(
        svg=SVGArtifact(
            present=result.svg.present,
            content=result.svg.content,
            path_count=result.svg.path_count,
        ),
        dxf=DXFArtifact(
            present=result.dxf.present,
            base64=result.dxf.base64,
            entity_count=result.dxf.entity_count,
            closed_contours=result.dxf.closed_contours,
        ),
    )
    dimensions = Dimensions(
        width_mm=result.dimensions.width_mm,
        height_mm=result.dimensions.height_mm,
        width_in=result.dimensions.width_in,
        height_in=result.dimensions.height_in,
        spec_match=result.dimensions.spec_match,
        confidence=result.dimensions.confidence,  # Now from real scorer
    )

    # Final diagnostics
    mem_final = log_memory("EXTRACT_COMPLETE")
    total_elapsed = time.time() - t0
    logger.info(
        f"VECTORIZER_RESULT | ok={result.ok} stage={result.stage} elapsed={total_elapsed:.1f}s | "
        f"mem_delta={mem_final - mem_start:.0f}MB | "
        f"body={result.dimensions.width_mm:.0f}x{result.dimensions.height_mm:.0f}mm | "
        f"confidence={result.dimensions.confidence:.3f}"
    )

    return VectorizeResponse(
        ok=result.ok,
        stage=result.stage,
        artifacts=artifacts,
        dimensions=dimensions,
        # Legacy fields for backward compatibility
        svg_path_d=svg_path_d,
        svg_path="",  # DEPRECATED: no file paths in stateless deploy
        dxf_path="",  # DEPRECATED: no file paths in stateless deploy
        contour_count=result.svg.path_count,
        line_count=result.dxf.entity_count,
        body_width_mm=result.dimensions.width_mm,
        body_height_mm=result.dimensions.height_mm,
        body_width_in=result.dimensions.width_in,
        body_height_in=result.dimensions.height_in,
        scale_source=result.scale_source,
        bg_method=result.bg_method,
        perspective_corrected=result.perspective_corrected,
        warnings=result.warnings,
        processing_ms=processing_ms,
        export_blocked=result.export_blocked,
        export_block_reason=result.export_block_reason,
        error=result.error,
        debug=result.debug if include_debug else None,
    )


def _extract_svg_path_d_from_content(svg_content: str) -> str:
    """
    Extract path d= attributes from SVG content string.
    Used for legacy svg_path_d field.
    """
    import xml.etree.ElementTree as ET
    try:
        root = ET.fromstring(svg_content)
        parts: list[str] = []

        # Try with namespace
        for elem in root.iter("{http://www.w3.org/2000/svg}path"):
            d = elem.get("d", "").strip()
            if d and len(d) > 10:
                parts.append(d)

        # Try without namespace if none found
        if not parts:
            for elem in root.iter("path"):
                d = elem.get("d", "").strip()
                if d and len(d) > 10:
                    parts.append(d)

        return " ".join(parts)
    except Exception:
        return ""
