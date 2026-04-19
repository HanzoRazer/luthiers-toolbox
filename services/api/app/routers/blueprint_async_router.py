"""
Blueprint Async Router
======================

Async job wrapper for blueprint vectorization.
Thin HTTP layer that creates jobs and calls BlueprintOrchestrator in background.

Endpoints:
    POST /api/blueprint/vectorize/async   - Submit job, return job_id
    GET  /api/blueprint/vectorize/status/{job_id} - Poll job status
    GET  /api/blueprint/vectorize/download/{job_id} - Download DXF artifact

Author: Production Shop
"""

from __future__ import annotations

import asyncio
import logging
from base64 import b64decode
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import Response

from ..jobs.models import JobStatus
from ..jobs.store import job_store
from ..services.blueprint_orchestrator import BlueprintOrchestrator
from ..services.blueprint_clean import CleanupMode
from ..services.blueprint_limits import LIMITS

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/blueprint", tags=["Blueprint Async"])

# Singleton orchestrator instance
_orchestrator = BlueprintOrchestrator()


def _serialize_job(job) -> dict[str, Any]:
    """Convert job to JSON-serializable dict."""
    return {
        "job_id": job.job_id,
        "status": job.status.value,
        "progress": job.progress,
        "stage": job.stage,
        "error": job.error,
        "created_at": job.created_at.isoformat() + "Z",
        "updated_at": job.updated_at.isoformat() + "Z",
        "result": job.result if job.status == JobStatus.COMPLETE else None,
        "debug": job.debug if job.debug else None,
    }


async def _run_blueprint_job(
    *,
    job_id: str,
    file_bytes: bytes,
    filename: str,
    page_num: int,
    target_height_mm: float,
    min_contour_length_mm: float,
    close_gaps_mm: float,
    debug: bool,
    mode: CleanupMode = CleanupMode.REFINED,
    spec_name: str | None = None,
) -> None:
    """
    Background task that runs the blueprint orchestrator.

    Updates job status/progress throughout processing.
    """

    def progress_callback(stage: str, progress: int) -> None:
        """Called by orchestrator to report progress."""
        job_store.update(
            job_id,
            status=JobStatus.PROCESSING,
            stage=stage,
            progress=progress,
        )

    try:
        job_store.update(
            job_id,
            status=JobStatus.PROCESSING,
            stage="starting",
            progress=1,
        )

        # Run sync orchestrator in thread pool
        result = await asyncio.to_thread(
            _orchestrator.process_file,
            file_bytes=file_bytes,
            filename=filename,
            page_num=page_num,
            target_height_mm=target_height_mm,
            min_contour_length_mm=min_contour_length_mm,
            close_gaps_mm=close_gaps_mm,
            debug=debug,
            progress_callback=progress_callback,
            mode=mode,
            spec_name=spec_name,
        )

        payload = result.to_response_dict(include_debug=debug)

        # Orchestrator completed successfully (regardless of recommendation)
        # JobStatus = execution outcome, payload.ok = product outcome
        job_store.update(
            job_id,
            status=JobStatus.COMPLETE,
            stage=result.stage,
            progress=100,
            result=payload,
            debug=payload.get("debug") or {},
        )

        if result.ok:
            logger.info(f"BLUEPRINT_JOB_COMPLETE_ACCEPT | job_id={job_id}")
        else:
            # Non-accept is still a successful job execution
            rec_action = payload.get("recommendation", {}).get("action", "unknown")
            logger.info(
                f"BLUEPRINT_JOB_COMPLETE_NONACCEPT | job_id={job_id} "
                f"recommendation={rec_action} stage={result.stage}"
            )

    except Exception as e:
        logger.exception(f"BLUEPRINT_JOB_ERROR | job_id={job_id}")
        job_store.update(
            job_id,
            status=JobStatus.FAILED,
            stage="error",
            progress=100,
            error=str(e),
        )


@router.post("/vectorize/async")
async def vectorize_blueprint_async(
    file: UploadFile = File(...),
    page_num: int = Form(0),
    target_height_mm: float = Form(500.0),
    min_contour_length_mm: float = Form(50.0),
    close_gaps_mm: float = Form(1.0),
    debug: bool = Form(False),
    mode: str = Form("refined"),
    spec_name: str | None = Form(None),
):
    """
    Submit a blueprint for async vectorization.

    Returns immediately with a job_id. Poll /vectorize/status/{job_id}
    to track progress and retrieve results.

    For large blueprints (>5MB or high-res PDFs), this avoids HTTP timeouts.

    Args:
        mode: Cleanup mode - "refined" (default), "baseline", "restored_baseline",
              "layered_dual_pass" (classified layers), "enhanced" (full detail)
        spec_name: Instrument spec for scale correction (e.g., "dreadnought")
    """
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # Guardrail: reject oversized uploads before creating job
    if len(file_bytes) > LIMITS.max_upload_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"Blueprint file exceeds {LIMITS.max_upload_mb} MB limit. Please upload a smaller file.",
        )

    # Parse cleanup mode (default to refined if invalid)
    try:
        cleanup_mode = CleanupMode(mode.lower())
    except ValueError:
        cleanup_mode = CleanupMode.REFINED

    filename = file.filename or "upload.bin"
    job = job_store.create(filename=filename)

    logger.info(f"BLUEPRINT_JOB_CREATED | job_id={job.job_id} filename={filename} size={len(file_bytes)} mode={cleanup_mode.value}")

    # Start background task
    asyncio.create_task(
        _run_blueprint_job(
            job_id=job.job_id,
            file_bytes=file_bytes,
            filename=filename,
            page_num=page_num,
            target_height_mm=target_height_mm,
            min_contour_length_mm=min_contour_length_mm,
            close_gaps_mm=close_gaps_mm,
            debug=debug,
            mode=cleanup_mode,
            spec_name=spec_name,
        )
    )

    return {
        "job_id": job.job_id,
        "status": job.status.value,
        "progress": job.progress,
        "stage": job.stage,
        "message": "Blueprint job accepted. Poll /vectorize/status/{job_id} for progress.",
    }


@router.get("/vectorize/status/{job_id}")
async def get_blueprint_job_status(job_id: str):
    """
    Get the current status of a blueprint job.

    Returns progress, stage, and result (if complete).
    """
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return _serialize_job(job)


@router.get("/vectorize/download/{job_id}")
async def download_blueprint_dxf(job_id: str):
    """
    Download the DXF artifact from a completed job.

    Returns 409 if job is not complete, 404 if DXF not found.
    """
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    if job.status != JobStatus.COMPLETE or not job.result:
        raise HTTPException(
            status_code=409,
            detail=f"Job not complete. Status: {job.status.value}, Stage: {job.stage}",
        )

    # Navigate to DXF artifact
    dxf = (((job.result or {}).get("artifacts") or {}).get("dxf") or {})
    if not dxf.get("present") or not dxf.get("base64"):
        raise HTTPException(status_code=404, detail="DXF artifact not found in job result.")

    # Decode and return
    data = b64decode(dxf["base64"])
    output_filename = job.filename.rsplit(".", 1)[0] + "_vectorized.dxf"

    return Response(
        content=data,
        media_type="application/dxf",
        headers={
            "Content-Disposition": f'attachment; filename="{output_filename}"',
            "Cache-Control": "no-cache, no-store, must-revalidate",
        },
    )
