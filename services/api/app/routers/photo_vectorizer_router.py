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
from fastapi.responses import JSONResponse
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


class Selection(BaseModel):
    """Contour selection diagnostics."""
    candidate_count: int = 0
    selected_index: Optional[int] = None
    selection_score: float = 0.0
    runner_up_score: float = 0.0
    winner_margin: float = 0.0
    reasons: list[str] = []


class Recommendation(BaseModel):
    """Product acceptance recommendation."""
    action: str = "reject"  # accept | review | reject
    confidence: float = 0.0
    reasons: list[str] = []


class VectorizeResponse(BaseModel):
    """
    Canonical photo vectorizer response.

    ok = true ONLY when recommendation.action == "accept".
    processed = true when pipeline completed (transport-level).
    """
    ok: bool
    processed: bool = True
    stage: str = "complete"
    error: str = ""
    warnings: list[str] = []
    artifacts: Artifacts = Artifacts()
    dimensions: Dimensions = Dimensions()
    selection: Selection = Selection()
    recommendation: Recommendation = Recommendation()
    metrics: dict = {}
    debug: Optional[dict] = None


# Legacy top-level fields still consumed by ImportView / BlueprintWorkflow.
# Populated at serialization time only — not part of the canonical contract.
_LEGACY_WIRE_FIELDS = (
    "svg_path_d",
    "svg_path",
    "dxf_path",
    "contour_count",
    "line_count",
    "body_width_mm",
    "body_height_mm",
    "body_width_in",
    "body_height_in",
    "scale_source",
    "bg_method",
    "perspective_corrected",
    "processing_ms",
    "export_blocked",
    "export_block_reason",
    "success",  # silhouette workflow still checks this alias
)


def _extract_svg_path_d_from_content(svg_content: str) -> str:
    """Extract path d= attributes from SVG content for legacy svg_path_d shim."""
    import xml.etree.ElementTree as ET

    try:
        root = ET.fromstring(svg_content)
        parts: list[str] = []

        for elem in root.iter("{http://www.w3.org/2000/svg}path"):
            d = elem.get("d", "").strip()
            if d and len(d) > 10:
                parts.append(d)

        if not parts:
            for elem in root.iter("path"):
                d = elem.get("d", "").strip()
                if d and len(d) > 10:
                    parts.append(d)

        return " ".join(parts)
    except Exception:
        return ""


def _legacy_vectorizer_fields(response: VectorizeResponse) -> dict[str, object]:
    """Deprecation shim: map canonical response → legacy top-level wire fields."""
    metrics = response.metrics or {}
    debug = response.debug or {}
    svg_content = response.artifacts.svg.content if response.artifacts.svg.present else ""

    export_blocked = bool(debug.get("export_blocked", False))
    export_block_reason = str(debug.get("export_block_reason", "") or "")
    if not export_blocked and not response.ok and response.recommendation.action == "reject":
        export_blocked = True
        export_block_reason = export_block_reason or response.error or (
            response.recommendation.reasons[0] if response.recommendation.reasons else ""
        )

    return {
        "svg_path_d": _extract_svg_path_d_from_content(svg_content),
        "svg_path": "",
        "dxf_path": "",
        "contour_count": response.artifacts.svg.path_count,
        "line_count": response.artifacts.dxf.entity_count,
        "body_width_mm": response.dimensions.width_mm,
        "body_height_mm": response.dimensions.height_mm,
        "body_width_in": response.dimensions.width_in,
        "body_height_in": response.dimensions.height_in,
        "scale_source": metrics.get("scale_source", ""),
        "bg_method": metrics.get("bg_method", ""),
        "perspective_corrected": metrics.get("perspective_corrected", False),
        "processing_ms": metrics.get("processing_ms", 0.0),
        "export_blocked": export_blocked,
        "export_block_reason": export_block_reason,
        "success": response.ok,
    }


def _vectorize_response_payload(response: VectorizeResponse) -> dict[str, object]:
    """Canonical payload plus legacy wire shim for frontend consumers."""
    payload = response.model_dump()
    payload.update(_legacy_vectorizer_fields(response))
    return payload


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


@router.post("/extract")
async def extract_from_photo(req: VectorizeRequest):
    """
    Run the Photo Vectorizer v2 pipeline on an uploaded image.

    Returns the body outline as a compound SVG path that ImportView
    can feed directly into useDxfImport.loadFromVectorizerResult().

    The caller should set known_width_mm if they have a reference
    dimension (e.g. a coin or ruler in the photo, or a known guitar
    body width). Without it, scale_source will be "estimated".

    Architecture note: Business logic lives in PhotoOrchestrator.
    This router is a thin HTTP wrapper that handles request decoding,
    input validation, and canonical response mapping.

    Wire response includes deprecated legacy top-level fields (svg_path_d,
    body_width_mm, etc.) synthesized from the canonical structure so existing
    frontend consumers keep working until they migrate to vectorizerArtifacts.ts.
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

    # Final diagnostics
    mem_final = log_memory("EXTRACT_COMPLETE")
    total_elapsed = time.time() - t0
    logger.info(
        f"VECTORIZER_RESULT | ok={result.ok} stage={result.stage} elapsed={total_elapsed:.1f}s | "
        f"mem_delta={mem_final - mem_start:.0f}MB | "
        f"body={result.dimensions.width_mm:.0f}x{result.dimensions.height_mm:.0f}mm | "
        f"rec={result.recommendation.action.value} confidence={result.recommendation.confidence:.3f}"
    )

    response_dict = result.to_response_dict(include_debug=include_debug)
    if response_dict.get("metrics", {}).get("processing_ms", 0) <= 0:
        response_dict.setdefault("metrics", {})["processing_ms"] = processing_ms
    canonical = VectorizeResponse(**response_dict)
    return JSONResponse(content=_vectorize_response_payload(canonical))
