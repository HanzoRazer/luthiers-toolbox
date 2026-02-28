"""
Rosette Photo Batch Processing Router

Exposes the BatchProcessor functionality via REST API endpoints.
Enables batch conversion of rosette photos to SVG/DXF for CAM workflows.

Endpoints:
    POST /api/cam/rosette/photo-batch/convert - Convert uploaded images
    POST /api/cam/rosette/photo-batch/convert-urls - Convert from URLs
    GET  /api/cam/rosette/photo-batch/{batch_id} - Get batch status
    GET  /api/cam/rosette/photo-batch/{batch_id}/download - Download results ZIP
"""

from __future__ import annotations

import hashlib
import logging
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from .photo_batch import BatchProcessor, BatchResult
from .photo_converter import ConversionSettings

router = APIRouter(prefix="/api/cam/rosette/photo-batch", tags=["CAM", "Rosette", "Batch"])
logger = logging.getLogger(__name__)

# In-memory batch job store (use Redis/DB for production)
_batch_jobs: Dict[str, Dict[str, Any]] = {}

# Output directory for batch results
_BATCH_OUTPUT_ROOT = Path(tempfile.gettempdir()) / "rosette_batch_output"


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class ConversionSettingsRequest(BaseModel):
    """Settings for photo-to-SVG/DXF conversion."""

    output_width_mm: float = Field(default=100.0, description="Target output width in mm")
    threshold_method: Literal["otsu", "adaptive", "manual"] = Field(
        default="adaptive", description="Thresholding method for binarization"
    )
    manual_threshold: int = Field(default=127, ge=0, le=255, description="Manual threshold (0-255)")
    simplify_epsilon: float = Field(default=1.0, ge=0, description="Path simplification factor")
    fit_to_circle: bool = Field(default=False, description="Fit pattern to circular ring")
    circle_inner_mm: float = Field(default=45.0, description="Inner ring diameter if fitting")
    circle_outer_mm: float = Field(default=55.0, description="Outer ring diameter if fitting")
    invert: bool = Field(default=False, description="Invert black/white")
    output_formats: List[Literal["svg", "dxf"]] = Field(
        default=["svg", "dxf"], description="Output formats to generate"
    )


class BatchJobResponse(BaseModel):
    """Response for batch job creation."""

    batch_id: str
    status: Literal["pending", "processing", "complete", "error"]
    total_jobs: int
    message: str


class BatchStatusResponse(BaseModel):
    """Response for batch job status."""

    batch_id: str
    status: Literal["pending", "processing", "complete", "error"]
    total_jobs: int
    successful: int
    failed: int
    processing_time_sec: Optional[float] = None
    created_at: str
    jobs: List[Dict[str, Any]]
    download_url: Optional[str] = None
    error: Optional[str] = None


class UrlConvertRequest(BaseModel):
    """Request to convert images from URLs."""

    urls: List[str] = Field(..., min_length=1, max_length=50, description="Image URLs to convert")
    settings: ConversionSettingsRequest = Field(default_factory=ConversionSettingsRequest)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _settings_from_request(req: ConversionSettingsRequest) -> ConversionSettings:
    """Convert request schema to ConversionSettings dataclass."""
    return ConversionSettings(
        output_width_mm=req.output_width_mm,
        threshold_method=req.threshold_method,
        manual_threshold=req.manual_threshold,
        simplify_epsilon=req.simplify_epsilon,
        fit_to_circle=req.fit_to_circle,
        circle_inner_mm=req.circle_inner_mm,
        circle_outer_mm=req.circle_outer_mm,
        invert=req.invert,
    )


def _generate_batch_id() -> str:
    """Generate unique batch ID."""
    return f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"


def _process_batch(
    batch_id: str,
    file_paths: List[str],
    settings: ConversionSettings,
    output_formats: List[str],
) -> BatchResult:
    """Process a batch of files."""
    output_dir = _BATCH_OUTPUT_ROOT / batch_id
    output_dir.mkdir(parents=True, exist_ok=True)

    processor = BatchProcessor(
        default_settings=settings,
        output_dir=str(output_dir),
        parallel=True,
        max_workers=4,
    )

    processor.add_files(file_paths, output_formats=output_formats)
    result = processor.process(create_zip=True, create_manifest=True)

    return result


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/convert", response_model=BatchJobResponse)
async def convert_uploaded_images(
    files: List[UploadFile] = File(..., description="Image files to convert"),
    output_width_mm: float = Form(default=100.0),
    threshold_method: Literal["otsu", "adaptive", "manual"] = Form(default="adaptive"),
    simplify_epsilon: float = Form(default=1.0),
    fit_to_circle: bool = Form(default=False),
    circle_inner_mm: float = Form(default=45.0),
    circle_outer_mm: float = Form(default=55.0),
    output_formats: str = Form(default="svg,dxf", description="Comma-separated: svg,dxf"),
) -> BatchJobResponse:
    """
    Convert uploaded rosette images to SVG/DXF.

    Upload multiple image files (PNG, JPG, etc.) and convert them to
    vector formats suitable for CNC machining.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    if len(files) > 50:
        raise HTTPException(status_code=400, detail="Maximum 50 files per batch")

    batch_id = _generate_batch_id()
    upload_dir = _BATCH_OUTPUT_ROOT / batch_id / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Save uploaded files
    saved_paths = []
    for f in files:
        if not f.filename:
            continue
        # Sanitize filename
        safe_name = hashlib.sha256(f.filename.encode()).hexdigest()[:12] + Path(f.filename).suffix
        file_path = upload_dir / safe_name
        content = await f.read()
        file_path.write_bytes(content)
        saved_paths.append(str(file_path))

    if not saved_paths:
        raise HTTPException(status_code=400, detail="No valid files uploaded")

    # Parse settings
    settings = ConversionSettings(
        output_width_mm=output_width_mm,
        threshold_method=threshold_method,
        simplify_epsilon=simplify_epsilon,
        fit_to_circle=fit_to_circle,
        circle_inner_mm=circle_inner_mm,
        circle_outer_mm=circle_outer_mm,
    )

    formats = [fmt.strip() for fmt in output_formats.split(",") if fmt.strip() in ("svg", "dxf")]
    if not formats:
        formats = ["svg", "dxf"]

    # Process batch
    try:
        result = _process_batch(batch_id, saved_paths, settings, formats)

        # Store result
        _batch_jobs[batch_id] = {
            "batch_id": batch_id,
            "status": "complete" if result.failed == 0 else "complete",
            "result": result,
            "created_at": datetime.now().isoformat(),
        }

        return BatchJobResponse(
            batch_id=batch_id,
            status="complete",
            total_jobs=result.total_jobs,
            message=f"Processed {result.successful}/{result.total_jobs} files successfully",
        )

    except (ValueError, TypeError, OSError) as e:
        logger.exception(f"Batch processing failed: {e}")
        _batch_jobs[batch_id] = {
            "batch_id": batch_id,
            "status": "error",
            "error": str(e),
            "created_at": datetime.now().isoformat(),
        }
        raise HTTPException(status_code=500, detail=f"Batch processing failed: {e}")


@router.post("/convert-urls", response_model=BatchJobResponse)
async def convert_from_urls(request: UrlConvertRequest) -> BatchJobResponse:
    """
    Convert rosette images from URLs to SVG/DXF.

    Provide a list of image URLs to download and convert.
    """
    import httpx

    batch_id = _generate_batch_id()
    upload_dir = _BATCH_OUTPUT_ROOT / batch_id / "downloads"
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Download images
    saved_paths = []
    async with httpx.AsyncClient(timeout=30.0) as client:
        for i, url in enumerate(request.urls):
            try:
                resp = await client.get(url)
                resp.raise_for_status()

                # Determine extension from content-type or URL
                ext = ".png"
                content_type = resp.headers.get("content-type", "")
                if "jpeg" in content_type or "jpg" in content_type:
                    ext = ".jpg"
                elif "png" in content_type:
                    ext = ".png"
                elif "webp" in content_type:
                    ext = ".webp"

                file_path = upload_dir / f"image_{i:03d}{ext}"
                file_path.write_bytes(resp.content)
                saved_paths.append(str(file_path))

            except httpx.HTTPError as e:
                logger.warning(f"Failed to download {url}: {e}")
                continue

    if not saved_paths:
        raise HTTPException(status_code=400, detail="No images could be downloaded")

    # Process batch
    settings = _settings_from_request(request.settings)
    formats = list(request.settings.output_formats)

    try:
        result = _process_batch(batch_id, saved_paths, settings, formats)

        _batch_jobs[batch_id] = {
            "batch_id": batch_id,
            "status": "complete",
            "result": result,
            "created_at": datetime.now().isoformat(),
        }

        return BatchJobResponse(
            batch_id=batch_id,
            status="complete",
            total_jobs=result.total_jobs,
            message=f"Processed {result.successful}/{result.total_jobs} files successfully",
        )

    except (ValueError, TypeError, OSError) as e:
        logger.exception(f"Batch processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Batch processing failed: {e}")


@router.get("/{batch_id}", response_model=BatchStatusResponse)
def get_batch_status(batch_id: str) -> BatchStatusResponse:
    """
    Get status of a batch processing job.
    """
    if batch_id not in _batch_jobs:
        raise HTTPException(status_code=404, detail=f"Batch {batch_id} not found")

    job = _batch_jobs[batch_id]
    result: Optional[BatchResult] = job.get("result")

    if result:
        jobs_summary = [
            {
                "input": j.input_path,
                "status": j.status,
                "output_svg": j.output_svg,
                "output_dxf": j.output_dxf,
                "error": j.error_message,
            }
            for j in result.jobs
        ]

        return BatchStatusResponse(
            batch_id=batch_id,
            status=job["status"],
            total_jobs=result.total_jobs,
            successful=result.successful,
            failed=result.failed,
            processing_time_sec=result.processing_time_sec,
            created_at=job["created_at"],
            jobs=jobs_summary,
            download_url=f"/api/cam/rosette/photo-batch/{batch_id}/download" if result.zip_path else None,
        )
    else:
        return BatchStatusResponse(
            batch_id=batch_id,
            status=job["status"],
            total_jobs=0,
            successful=0,
            failed=0,
            created_at=job.get("created_at", ""),
            jobs=[],
            error=job.get("error"),
        )


@router.get("/{batch_id}/download")
def download_batch_results(batch_id: str) -> FileResponse:
    """
    Download batch results as ZIP archive.

    Contains all converted SVG/DXF files and a manifest.json.
    """
    if batch_id not in _batch_jobs:
        raise HTTPException(status_code=404, detail=f"Batch {batch_id} not found")

    job = _batch_jobs[batch_id]
    result: Optional[BatchResult] = job.get("result")

    if not result or not result.zip_path:
        raise HTTPException(status_code=404, detail="No download available for this batch")

    zip_path = Path(result.zip_path)
    if not zip_path.exists():
        raise HTTPException(status_code=404, detail="ZIP file not found")

    return FileResponse(
        path=str(zip_path),
        media_type="application/zip",
        filename=zip_path.name,
    )


@router.delete("/{batch_id}")
def delete_batch(batch_id: str) -> Dict[str, str]:
    """
    Delete a batch job and its output files.
    """
    if batch_id not in _batch_jobs:
        raise HTTPException(status_code=404, detail=f"Batch {batch_id} not found")

    # Remove from memory
    del _batch_jobs[batch_id]

    # Remove output directory
    output_dir = _BATCH_OUTPUT_ROOT / batch_id
    if output_dir.exists():
        import shutil
        shutil.rmtree(output_dir, ignore_errors=True)

    return {"message": f"Batch {batch_id} deleted"}


@router.get("/", response_model=List[BatchStatusResponse])
def list_batches(limit: int = 20) -> List[BatchStatusResponse]:
    """
    List recent batch jobs.
    """
    responses = []
    for batch_id in list(_batch_jobs.keys())[-limit:]:
        try:
            responses.append(get_batch_status(batch_id))
        except HTTPException:
            continue
    return responses
