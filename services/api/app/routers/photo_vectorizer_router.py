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

router = APIRouter(tags=["vectorizer"])

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
    sys.stderr.write(f"[photo_vectorizer_router] __file__ = {__file__}\n")
    sys.stderr.write(f"[photo_vectorizer_router] _pv_path = {_pv_path}\n")

    if _pv_path and _pv_path.exists():
        sys.stderr.write(f"[photo_vectorizer_router] _pv_path.exists() = True\n")
        if str(_pv_path) not in sys.path:
            sys.path.insert(0, str(_pv_path))
            sys.stderr.write(f"[photo_vectorizer_router] Added to sys.path\n")
    else:
        sys.stderr.write(f"[photo_vectorizer_router] _pv_path not found, relying on PYTHONPATH\n")

    from photo_vectorizer_v2 import PhotoVectorizerV2  # type: ignore
    VECTORIZER_AVAILABLE = True
    sys.stderr.write(f"[photo_vectorizer_router] SUCCESS - PhotoVectorizerV2 imported\n")
except Exception as e:  # audited: http-500 — ValueError,IOError
    _vectorizer_error = str(e)
    sys.stderr.write(f"[photo_vectorizer_router] FAILED - {type(e).__name__}: {e}\n")

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

class VectorizeResponse(BaseModel):
    ok:                 bool
    svg_path_d:         str   = ""      # combined SVG path for ImportView
    svg_path:           str   = ""      # file path for Blueprint workflow
    dxf_path:           str   = ""      # file path for Blueprint workflow
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

        # Collect all path d= attributes, filtering out tiny artifacts
        parts: list[str] = []
        for elem in root.iter("{http://www.w3.org/2000/svg}path"):
            d = elem.get("d", "").strip()
            if d and len(d) > 10:
                parts.append(d)

        # If no namespaced paths, try without namespace
        if not parts:
            for elem in root.iter("path"):
                d = elem.get("d", "").strip()
                if d and len(d) > 10:
                    parts.append(d)

        return " ".join(parts)
    except Exception:  # audited: optional-import
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

    # ── Decode base64 image ────────────────────────────────────────────────
    try:
        img_bytes = base64.b64decode(req.image_b64)
    except Exception as e:  # audited: http-500 — ValueError,IOError
        raise HTTPException(status_code=422, detail=f"Invalid base64: {e}")

    ext = ".jpg" if "jpeg" in req.media_type else ".png"

    with tempfile.TemporaryDirectory() as tmpdir:
        img_path = Path(tmpdir) / f"upload{ext}"
        out_dir  = Path(tmpdir) / "out"
        out_dir.mkdir()

        img_path.write_bytes(img_bytes)

        # ── Run vectorizer ─────────────────────────────────────────────────
        try:
            vectorizer = PhotoVectorizerV2()
            result = vectorizer.extract(
                source_path=img_path,
                output_dir=out_dir,
                known_dimension_mm=req.known_width_mm,
                correct_perspective=req.correct_perspective,
                export_svg=req.export_svg,
                export_dxf=req.export_dxf,
                export_json=False,
                debug_images=False,
                source_type=req.source_type,
                gap_closing_level=req.gap_closing_level,
            )
        except Exception as e:  # audited: http-500 — ValueError,IOError
            return VectorizeResponse(
                ok=False,
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
            svg_path_d = _extract_svg_paths(result.output_svg)

        # Fallback: try body_contour points directly if SVG extraction empty
        if not svg_path_d and result.body_contour and hasattr(result.body_contour, "points"):
            pts = result.body_contour.points
            if pts and len(pts) >= 3:
                svg_path_d = "M " + " L ".join(f"{p[0]:.2f},{p[1]:.2f}" for p in pts) + " Z"

        w_mm, h_mm = result.body_dimensions_mm
        w_in, h_in = result.body_dimensions_inch

        # ── Persist files for Blueprint workflow ────────────────────────────
        svg_file_path = ""
        dxf_file_path = ""
        contour_count = 1 if svg_path_d else 0
        
        # Create persistent output directory (same pattern as phase2)
        persist_dir = Path(tempfile.gettempdir()) / f"blueprint_phase_silhouette_{int(time.time()*1000)}"
        persist_dir.mkdir(exist_ok=True)
        
        # Copy SVG if exists
        if result.output_svg and Path(result.output_svg).exists():
            dest_svg = persist_dir / "silhouette_vectorized.svg"
            import shutil
            shutil.copy2(result.output_svg, dest_svg)
            svg_file_path = str(dest_svg)
            _output_file_registry[dest_svg.name] = svg_file_path
        
        # Copy DXF if exists
        if result.output_dxf and Path(result.output_dxf).exists():
            dest_dxf = persist_dir / "silhouette_vectorized.dxf"
            import shutil
            shutil.copy2(result.output_dxf, dest_dxf)
            dxf_file_path = str(dest_dxf)
            _output_file_registry[dest_dxf.name] = dxf_file_path

        return VectorizeResponse(
            ok=bool(svg_path_d and not result.export_blocked),
            svg_path_d=svg_path_d,
            svg_path=svg_file_path,
            dxf_path=dxf_file_path,
            contour_count=contour_count,
            line_count=0,
            body_width_mm=round(w_mm, 2),
            body_height_mm=round(h_mm, 2),
            body_width_in=round(w_in, 3),
            body_height_in=round(h_in, 3),
            scale_source=result.calibration.source.value if result.calibration else "estimated",
            bg_method=result.bg_method_used,
            perspective_corrected=result.perspective_corrected,
            warnings=result.warnings,
            processing_ms=processing_ms,
            export_blocked=result.export_blocked,
            export_block_reason=result.export_block_reason or "",
        )
