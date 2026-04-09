"""
Blueprint DXF Clean Router
==========================

Cleans raw edge-to-dxf output to isolate body outline.

The edge_to_dxf endpoint produces 100k-600k LINE entities capturing
every edge pixel. This endpoint filters to body-relevant geometry.

Endpoints:
    POST /clean          - Clean DXF, return SVG preview + stats
    GET  /clean/download - Stream cleaned DXF file
    GET  /clean/info     - Check cleaner status

Author: Production Shop
"""

from __future__ import annotations

import base64
import logging
import tempfile
import time
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from .phase2_router import _output_file_registry

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/clean", tags=["Blueprint Clean"])

# Registry for cleaned files (filename -> path)
_clean_file_registry: dict[str, str] = {}


class CleanRequest(BaseModel):
    """Request to clean a DXF file."""
    dxf_b64: Optional[str] = None  # Base64 encoded DXF content
    dxf_filename: Optional[str] = None  # Filename from prior extraction (in registry)
    dxf_path: Optional[str] = None  # Full filesystem path (from edge-to-dxf response)
    min_contour_length_mm: float = 100.0  # Minimum contour length to keep
    close_gaps_mm: float = 1.0  # Maximum gap to close
    keep_open_chains: bool = False  # Keep open chains (not just closed loops)


class CleanResponse(BaseModel):
    """Response from DXF cleaning."""
    success: bool
    svg_preview: Optional[str] = None  # SVG preview of cleaned contours
    dxf_b64: Optional[str] = None  # Base64 encoded cleaned DXF (for files < 10MB)
    download_filename: Optional[str] = None  # Filename for /clean/download endpoint (fallback)
    original_entity_count: int = 0
    cleaned_entity_count: int = 0
    contours_found: int = 0
    chains_found: int = 0
    discarded_short: int = 0
    discarded_open: int = 0
    file_size_kb: float = 0.0
    processing_time_ms: float = 0.0
    error: Optional[str] = None


class CleanInfoResponse(BaseModel):
    """Status of DXF cleaner."""
    available: bool
    method: str = "line_chaining"
    description: str = ""


@router.get("/info", response_model=CleanInfoResponse)
async def clean_info():
    """Check DXF cleaner availability and method."""
    return CleanInfoResponse(
        available=True,
        method="line_chaining",
        description="Chains LINE entities into closed contours, filters by length"
    )


@router.post("", response_model=CleanResponse)
async def clean_dxf(req: CleanRequest):
    """
    Clean raw edge-to-dxf output to isolate body outline.

    Accepts either:
    - dxf_b64: Base64-encoded DXF content
    - dxf_path: Full filesystem path (from edge-to-dxf response)
    - dxf_filename: Filename from prior extraction (looked up in registry)

    Returns SVG preview and download filename (NOT the full base64).
    Use GET /clean/download/{filename} to stream the cleaned DXF.
    """
    start = time.perf_counter()

    # Import cleaner
    try:
        from ...cam.unified_dxf_cleaner import DXFCleaner
    except ImportError as e:
        raise HTTPException(503, f"DXF cleaner not available: {e}")

    # Get input DXF - priority: dxf_b64 > dxf_path > dxf_filename (registry)
    dxf_bytes = None
    source_name = "input"

    if req.dxf_b64:
        dxf_bytes = base64.b64decode(req.dxf_b64)
        source_name = "base64_input"
    elif req.dxf_path:
        # Direct filesystem path (works on Railway where registry doesn't persist)
        file_path = Path(req.dxf_path)
        if not file_path.exists():
            raise HTTPException(404, f"File not found: {req.dxf_path}")
        dxf_bytes = file_path.read_bytes()
        source_name = file_path.stem
        logger.info(f"Reading DXF from path: {req.dxf_path} ({len(dxf_bytes)} bytes)")
    elif req.dxf_filename:
        # Registry lookup (works locally, may fail on Railway multi-worker)
        if req.dxf_filename not in _output_file_registry:
            raise HTTPException(404, f"File not found in registry: {req.dxf_filename}")
        file_path = Path(_output_file_registry[req.dxf_filename])
        dxf_bytes = file_path.read_bytes()
        source_name = file_path.stem
    else:
        raise HTTPException(400, "Must provide dxf_b64, dxf_path, or dxf_filename")

    # Write to temp file for cleaner
    input_dir = Path(tempfile.mkdtemp(prefix="dxf_clean_input_"))
    input_path = input_dir / f"{source_name}.dxf"
    input_path.write_bytes(dxf_bytes)

    # Output path
    output_dir = Path(tempfile.mkdtemp(prefix="dxf_clean_output_"))
    output_filename = f"{source_name}_cleaned.dxf"
    output_path = output_dir / output_filename

    try:
        # Run cleaner
        cleaner = DXFCleaner(
            min_contour_length_mm=req.min_contour_length_mm,
            closure_tolerance=req.close_gaps_mm,
            keep_open_chains=req.keep_open_chains,
        )

        result = cleaner.clean_file(input_path, output_path)

        if not result.success:
            return CleanResponse(
                success=False,
                error=result.error,
                processing_time_ms=(time.perf_counter() - start) * 1000
            )

        # Generate SVG preview
        # Re-read the chains for preview (cleaner doesn't expose them directly)
        # For now, generate a simple stats-based response
        svg_preview = None
        if result.contours_found > 0:
            # Read the cleaned file and generate preview
            try:
                import ezdxf
                doc = ezdxf.readfile(str(output_path))
                msp = doc.modelspace()

                # Extract polyline points for preview
                from ...cam.unified_dxf_cleaner import Chain, Point
                chains = []
                for e in msp:
                    if e.dxftype() == "LWPOLYLINE":
                        points = [Point(x, y) for x, y in e.get_points("xy")]
                        if points:
                            chain = Chain(points=points)
                            chains.append(chain)

                if chains:
                    svg_preview = cleaner.generate_svg_preview(chains)
            except Exception as e:
                logger.warning(f"Failed to generate SVG preview: {e}")

        # Register cleaned file for download (fallback for large files)
        _clean_file_registry[output_filename] = str(output_path)
        _output_file_registry[output_filename] = str(output_path)

        # Calculate file size and read as base64 if small enough
        file_size_kb = output_path.stat().st_size / 1024 if output_path.exists() else 0
        dxf_b64 = None

        # Include base64 for files under 10MB (avoids streaming endpoint issues on Railway)
        if file_size_kb < 10240:  # 10MB limit
            dxf_b64 = base64.b64encode(output_path.read_bytes()).decode()
            logger.info(f"Including dxf_b64 ({file_size_kb:.1f} KB)")

        elapsed_ms = (time.perf_counter() - start) * 1000

        return CleanResponse(
            success=True,
            svg_preview=svg_preview,
            dxf_b64=dxf_b64,
            download_filename=output_filename,
            original_entity_count=result.original_entity_count,
            cleaned_entity_count=result.cleaned_entity_count,
            contours_found=result.contours_found,
            chains_found=result.chains_found,
            discarded_short=result.discarded_short,
            discarded_open=result.discarded_open,
            file_size_kb=file_size_kb,
            processing_time_ms=elapsed_ms,
        )

    except Exception as e:
        logger.exception("DXF cleaning failed")
        return CleanResponse(
            success=False,
            error=str(e),
            processing_time_ms=(time.perf_counter() - start) * 1000
        )
    finally:
        # Clean up input
        input_path.unlink(missing_ok=True)
        try:
            input_dir.rmdir()
        except OSError:
            pass


@router.get("/download/{filename}")
async def download_cleaned_dxf(filename: str):
    """
    Stream cleaned DXF file.

    Use the download_filename from POST /clean response.
    """
    # Check clean registry first
    if filename in _clean_file_registry:
        file_path = _clean_file_registry[filename]
        if Path(file_path).exists():
            return FileResponse(
                file_path,
                media_type="application/dxf",
                filename=filename,
                headers={
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0",
                }
            )

    # Fallback to main registry
    if filename in _output_file_registry:
        file_path = _output_file_registry[filename]
        if Path(file_path).exists():
            return FileResponse(
                file_path,
                media_type="application/dxf",
                filename=filename,
                headers={
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0",
                }
            )

    raise HTTPException(404, f"File not found: {filename}. Run /clean first.")
