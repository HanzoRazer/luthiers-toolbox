"""
Edge-to-DXF Router
==================

Exposes the edge_to_dxf.py high-fidelity converter as an API endpoint.

This is the technology that produced the excellent cuatro_puertoriqueno_simple.dxf
(15.5MB, 129,000 LINE entities) - multi-scale edge fusion creates extremely
detailed DXF files suitable for archival or manual CAD tracing.

Endpoints:
    POST /edge-to-dxf/convert       - Standard edge conversion
    POST /edge-to-dxf/enhanced      - Multi-scale edge fusion (highest quality)
    GET  /edge-to-dxf/status        - Check module availability

Output characteristics:
- DXF R2010 format (per CLAUDE.md standard)
- Individual LINE entities (CAD-friendly)
- 50,000-300,000+ LINE entities (10-50MB files)
- Every edge pixel preserved

Author: Production Shop
"""

from __future__ import annotations

import logging
import sys
import tempfile
import time
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Import phase2 file registry for persisting output files
from .phase2_router import _output_file_registry

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/edge-to-dxf", tags=["Edge-to-DXF"])

# Optional import of edge_to_dxf module
EDGE_TO_DXF_AVAILABLE = False
_import_error = ""

try:
    _pv_path = Path(__file__).parents[3] / "photo-vectorizer"
    if str(_pv_path) not in sys.path:
        sys.path.insert(0, str(_pv_path))

    from edge_to_dxf import EdgeToDXF, EdgeToDXFResult
    EDGE_TO_DXF_AVAILABLE = True
except Exception as e:
    _import_error = str(e)


# PDF rendering support
PYMUPDF_AVAILABLE = False
try:
    import fitz
    PYMUPDF_AVAILABLE = True
except ImportError:
    pass


class EdgeToDXFResponse(BaseModel):
    """Response from edge-to-DXF conversion."""
    success: bool
    dxf_path: Optional[str] = None
    line_count: int = 0
    edge_pixel_count: int = 0
    image_size_px: list = []  # [width, height]
    output_size_mm: list = []  # [width, height]
    mm_per_px: float = 0.0
    processing_time_ms: float = 0.0
    file_size_mb: float = 0.0
    method: str = ""  # "standard" or "enhanced"
    error: Optional[str] = None


class EdgeToDXFStatusResponse(BaseModel):
    """Status of edge-to-DXF module."""
    available: bool
    pdf_support: bool
    error: Optional[str] = None


def _render_pdf_first_page(pdf_bytes: bytes, dpi: int = 300):
    """Render first page of PDF to image bytes."""
    import cv2
    import numpy as np

    if not PYMUPDF_AVAILABLE:
        raise HTTPException(501, "PDF support requires PyMuPDF: pip install PyMuPDF")

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    if len(doc) == 0:
        raise HTTPException(400, "PDF has no pages")

    page = doc[0]
    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)

    img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
        pix.height, pix.width, 3
    )

    doc.close()

    # Encode as PNG for the converter
    _, png_bytes = cv2.imencode('.png', cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR))
    return png_bytes.tobytes()


@router.get("/status", response_model=EdgeToDXFStatusResponse)
async def edge_to_dxf_status():
    """Check if edge-to-DXF module is available."""
    return EdgeToDXFStatusResponse(
        available=EDGE_TO_DXF_AVAILABLE,
        pdf_support=PYMUPDF_AVAILABLE,
        error=_import_error if not EDGE_TO_DXF_AVAILABLE else None,
    )


@router.post("/convert", response_model=EdgeToDXFResponse)
async def convert_edges(
    file: UploadFile = File(..., description="Image or PDF file"),
    target_height_mm: float = Form(500.0, description="Target height in mm"),
    canny_low: int = Form(50, ge=1, le=255, description="Canny low threshold"),
    canny_high: int = Form(150, ge=1, le=255, description="Canny high threshold"),
    adjacency: float = Form(3.0, ge=1.0, le=10.0, description="Max pixel distance to connect"),
    return_file: bool = Form(False, description="Return DXF file directly"),
):
    """
    Convert image/PDF edges to high-fidelity DXF.

    Standard conversion with single-pass Canny edge detection.
    For maximum quality, use /enhanced endpoint instead.
    """
    if not EDGE_TO_DXF_AVAILABLE:
        raise HTTPException(503, f"Edge-to-DXF not available: {_import_error}")

    contents = await file.read()
    filename = file.filename or ""

    # Create persistent output directory
    output_dir = Path(tempfile.mkdtemp(prefix="edge_to_dxf_"))

    # Handle PDF
    is_pdf = contents[:4] == b'%PDF' or filename.lower().endswith('.pdf')
    if is_pdf:
        logger.info("Rendering PDF at 300 DPI for edge extraction")
        contents = _render_pdf_first_page(contents, dpi=300)
        input_path = output_dir / "input.png"
    else:
        ext = Path(filename).suffix or ".png"
        input_path = output_dir / f"input{ext}"

    input_path.write_bytes(contents)

    try:
        converter = EdgeToDXF(
            canny_low=canny_low,
            canny_high=canny_high,
            adjacency_threshold=adjacency,
        )

        output_path = output_dir / f"{Path(filename).stem or 'edges'}_edges.dxf"

        result = converter.convert(
            str(input_path),
            output_path=str(output_path),
            target_height_mm=target_height_mm,
        )

        # Clean up input
        input_path.unlink(missing_ok=True)

        # Register output for download
        _output_file_registry[output_path.name] = str(output_path)

        if return_file:
            return FileResponse(
                str(output_path),
                media_type="application/dxf",
                filename=output_path.name,
            )

        return EdgeToDXFResponse(
            success=True,
            dxf_path=str(output_path),
            line_count=result.line_count,
            edge_pixel_count=result.edge_pixel_count,
            image_size_px=list(result.image_size_px),
            output_size_mm=list(result.output_size_mm),
            mm_per_px=result.mm_per_px,
            processing_time_ms=result.processing_time_ms,
            file_size_mb=result.file_size_bytes / 1024 / 1024,
            method="standard",
        )

    except Exception as e:
        logger.exception("Edge-to-DXF conversion failed")
        return EdgeToDXFResponse(
            success=False,
            method="standard",
            error=str(e),
        )


@router.post("/enhanced", response_model=EdgeToDXFResponse)
async def convert_edges_enhanced(
    file: UploadFile = File(..., description="Image or PDF file"),
    target_height_mm: float = Form(500.0, description="Target height in mm"),
    return_file: bool = Form(False, description="Return DXF file directly"),
):
    """
    Convert image/PDF edges to DXF with MULTI-SCALE EDGE FUSION.

    This is the highest-quality option - combines edges from three
    Canny threshold levels (30/100, 50/150, 80/200) for complete
    edge coverage. Produces 50,000-300,000+ LINE entities.

    This is the method that produced the excellent cuatro_puertoriqueno_simple.dxf.

    WARNING: Output files are large (10-50MB). Use for archival or manual CAD tracing.
    """
    if not EDGE_TO_DXF_AVAILABLE:
        raise HTTPException(503, f"Edge-to-DXF not available: {_import_error}")

    contents = await file.read()
    filename = file.filename or ""

    # Create persistent output directory
    output_dir = Path(tempfile.mkdtemp(prefix="edge_to_dxf_enhanced_"))

    # Handle PDF
    is_pdf = contents[:4] == b'%PDF' or filename.lower().endswith('.pdf')
    if is_pdf:
        logger.info("Rendering PDF at 300 DPI for multi-scale edge extraction")
        contents = _render_pdf_first_page(contents, dpi=300)
        input_path = output_dir / "input.png"
    else:
        ext = Path(filename).suffix or ".png"
        input_path = output_dir / f"input{ext}"

    input_path.write_bytes(contents)

    try:
        converter = EdgeToDXF()

        output_path = output_dir / f"{Path(filename).stem or 'edges'}_enhanced.dxf"

        # Use enhanced multi-scale edge fusion
        result = converter.convert_enhanced(
            str(input_path),
            output_path=str(output_path),
            target_height_mm=target_height_mm,
        )

        # Clean up input
        input_path.unlink(missing_ok=True)

        # Register output for download
        _output_file_registry[output_path.name] = str(output_path)

        if return_file:
            return FileResponse(
                str(output_path),
                media_type="application/dxf",
                filename=output_path.name,
            )

        return EdgeToDXFResponse(
            success=True,
            dxf_path=str(output_path),
            line_count=result.line_count,
            edge_pixel_count=result.edge_pixel_count,
            image_size_px=list(result.image_size_px),
            output_size_mm=list(result.output_size_mm),
            mm_per_px=result.mm_per_px,
            processing_time_ms=result.processing_time_ms,
            file_size_mb=result.file_size_bytes / 1024 / 1024,
            method="enhanced",
        )

    except Exception as e:
        logger.exception("Edge-to-DXF enhanced conversion failed")
        return EdgeToDXFResponse(
            success=False,
            method="enhanced",
            error=str(e),
        )
