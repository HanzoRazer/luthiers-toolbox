"""
Production Shop — Enhanced Site Generation API
FastAPI router with security, rate limiting, webhooks, and job management

Features:
- API key authentication
- Rate limiting (configurable per hour)
- Auto-cleanup of old jobs
- Webhook notifications on completion
- Preview endpoints for generated files
- Comprehensive error handling
- Job cancellation support

Wire into your main app:
    from api.site_generator_router import router
    app.include_router(router)
"""

import asyncio
import hashlib
import hmac
import json
import os
import shutil
import uuid
import zipfile
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse
from pydantic import BaseModel, Field, validator

import sys
sys.path.append(str(Path(__file__).parent.parent / "site_agent"))
from agent import generate_site

from .auth import verify_api_key, optional_api_key
from .config import settings


router = APIRouter(prefix="/api/site-generator", tags=["site-generator"])
_executor = ThreadPoolExecutor(max_workers=settings.max_concurrent_jobs)
_jobs: dict[str, dict] = {}
_cancelled_jobs: set[str] = set()


# ── Models ──────────────────────────────────────────────────────────────────

class PageSpec(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    filename: str = Field(..., pattern=r'^[a-zA-Z0-9_-]+\.html$')
    description: str = Field(..., min_length=10, max_length=500)
    sections: list[str] = Field(default_factory=list, max_items=20)

    @validator('filename')
    def validate_filename(cls, v):
        """Ensure filename is safe"""
        if '..' in v or '/' in v or '\\' in v:
            raise ValueError('Invalid filename')
        return v


class SiteSpec(BaseModel):
    site_name: str = Field(..., min_length=2, max_length=80)
    description: str = Field(..., min_length=10, max_length=1000)
    colors: dict[str, str] = Field(default_factory=dict, max_items=20)
    typography: dict[str, str] = Field(default_factory=dict, max_items=15)
    js_features: list[str] = Field(default_factory=list, max_items=20)
    pages: list[PageSpec] = Field(..., min_length=1, max_items=20)

    @validator('colors')
    def validate_colors(cls, v):
        """Validate hex color format"""
        for key, color in v.items():
            if not color.startswith('#') or len(color) not in [4, 7]:
                raise ValueError(f'Invalid color format for {key}: {color}')
        return v


class GenerateRequest(BaseModel):
    spec: SiteSpec
    job_label: Optional[str] = Field(None, max_length=100)
    webhook_url: Optional[str] = Field(None, description="URL to POST when job completes")


class JobStatus(BaseModel):
    job_id: str
    label: str
    status: str  # pending, running, complete, failed, cancelled
    progress: int
    files_written: int
    total_files: int
    started_at: str
    completed_at: Optional[str] = None
    error: Optional[str] = None
    download_url: Optional[str] = None
    preview_url: Optional[str] = None


class JobsList(BaseModel):
    jobs: list[JobStatus]
    total: int
    active: int
    completed: int
    failed: int


# ── Helpers ──────────────────────────────────────────────────────────────────

def _clean(job: dict) -> dict:
    """Remove internal fields from job dict"""
    return {k: v for k, v in job.items() if k not in ("out_dir", "zip_path", "webhook_url", "webhook_secret")}


def _get(job_id: str) -> dict:
    """Get job by ID or raise 404"""
    if job_id not in _jobs:
        raise HTTPException(404, f"Job {job_id} not found")
    return _jobs[job_id]


def _validate_job_id(job_id: str):
    """Validate job ID format"""
    if not job_id.isalnum() or len(job_id) > 12:
        raise HTTPException(400, "Invalid job ID format")


async def _send_webhook(webhook_url: str, job: dict, secret: Optional[str] = None):
    """Send webhook notification with optional HMAC signature"""
    try:
        payload = {
            "job_id": job["job_id"],
            "status": job["status"],
            "label": job["label"],
            "completed_at": job.get("completed_at"),
            "download_url": job.get("download_url"),
            "error": job.get("error"),
        }

        headers = {"Content-Type": "application/json"}

        # Add HMAC signature if secret provided
        if secret:
            payload_bytes = json.dumps(payload).encode()
            signature = hmac.new(
                secret.encode(),
                payload_bytes,
                hashlib.sha256
            ).hexdigest()
            headers["X-Webhook-Signature"] = f"sha256={signature}"

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(webhook_url, json=payload, headers=headers)
            response.raise_for_status()
            print(f"[WEBHOOK] Sent to {webhook_url} - {response.status_code}")

    except Exception as e:
        print(f"[WEBHOOK ERROR] Failed to send to {webhook_url}: {e}")


async def _cleanup_old_jobs():
    """Background task to remove jobs older than retention period"""
    cutoff = datetime.utcnow() - timedelta(hours=settings.job_retention_hours)
    deleted = []

    for job_id, job in list(_jobs.items()):
        if job["status"] in ("complete", "failed", "cancelled"):
            started = datetime.fromisoformat(job["started_at"])
            if started < cutoff:
                # Delete files
                for path in [settings.jobs_dir / job_id, settings.jobs_dir / f"{job_id}.zip"]:
                    if path.exists():
                        try:
                            shutil.rmtree(path) if path.is_dir() else path.unlink()
                        except Exception as e:
                            print(f"[CLEANUP ERROR] {path}: {e}")

                del _jobs[job_id]
                deleted.append(job_id)

    if deleted:
        print(f"[CLEANUP] Deleted {len(deleted)} old jobs: {deleted}")

    return deleted


# ── Background worker ────────────────────────────────────────────────────────

def _run(job_id: str, spec: dict, out_dir: Path, webhook_url: Optional[str] = None):
    """Background worker that generates the site"""
    job = _jobs[job_id]
    job["status"] = "running"
    total = 2 + len(spec["pages"])
    job["total_files"] = total

    try:
        # Check for cancellation
        if job_id in _cancelled_jobs:
            raise Exception("Job cancelled by user")

        # Monkey-patch write_file to track progress
        import agent as a
        orig_write = a.write_file

        def tracked_write(d, fn, content, resume):
            if job_id in _cancelled_jobs:
                raise Exception("Job cancelled by user")

            result = orig_write(d, fn, content, resume)
            if result:
                job["files_written"] += 1
                job["progress"] = min(90, int(job["files_written"] / total * 90))
            return result

        a.write_file = tracked_write

        # Set API key in environment
        os.environ["ANTHROPIC_API_KEY"] = settings.anthropic_api_key

        # Generate the site
        generate_site(spec, out_dir, resume=False)

        # Restore original write_file
        a.write_file = orig_write

        # Check cancellation again
        if job_id in _cancelled_jobs:
            raise Exception("Job cancelled by user")

        # Create zip file (exclude .agent_logs)
        job["progress"] = 95
        zip_path = settings.jobs_dir / f"{job_id}.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in out_dir.rglob("*"):
                if f.is_file() and ".agent_logs" not in str(f):
                    zf.write(f, f.relative_to(out_dir))

        # Job complete
        job.update(
            status="complete",
            progress=100,
            completed_at=datetime.utcnow().isoformat(),
            download_url=f"/api/site-generator/download/{job_id}",
            preview_url=f"/api/site-generator/preview/{job_id}",
            zip_path=str(zip_path),
        )

        # Send webhook notification
        if webhook_url:
            asyncio.run(_send_webhook(webhook_url, job, settings.webhook_secret))

    except Exception as e:
        error_msg = str(e)
        job.update(
            status="cancelled" if "cancelled" in error_msg.lower() else "failed",
            error=error_msg,
            completed_at=datetime.utcnow().isoformat(),
        )

        # Send webhook for failure
        if webhook_url:
            asyncio.run(_send_webhook(webhook_url, job, settings.webhook_secret))

    finally:
        # Clean up cancelled jobs set
        _cancelled_jobs.discard(job_id)


# ── Routes ───────────────────────────────────────────────────────────────────

@router.post("/generate", response_model=JobStatus, status_code=202)
async def generate(
    req: GenerateRequest,
    bg: BackgroundTasks,
    client_id: str = Depends(verify_api_key)
):
    """
    Generate a new website from specification

    Requires API key authentication via X-API-Key header or Bearer token
    Rate limited to configured requests per hour
    """
    # Check concurrent job limit
    running_jobs = sum(1 for j in _jobs.values() if j["status"] == "running")
    if running_jobs >= settings.max_concurrent_jobs:
        raise HTTPException(
            503,
            f"Server busy. Max {settings.max_concurrent_jobs} concurrent jobs allowed. Try again later."
        )

    # Generate job ID
    job_id = str(uuid.uuid4())[:8]
    spec_dict = req.spec.model_dump()
    label = req.job_label or req.spec.site_name
    out_dir = settings.jobs_dir / job_id / "site"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Save spec for reference
    with open(settings.jobs_dir / job_id / "spec.json", "w") as f:
        json.dump(spec_dict, f, indent=2)

    # Create job record
    _jobs[job_id] = dict(
        job_id=job_id,
        label=label,
        status="pending",
        progress=0,
        files_written=0,
        total_files=2 + len(spec_dict["pages"]),
        started_at=datetime.utcnow().isoformat(),
        completed_at=None,
        error=None,
        download_url=None,
        preview_url=None,
        out_dir=str(out_dir),
        webhook_url=req.webhook_url,
    )

    # Start background generation
    loop = asyncio.get_event_loop()
    bg.add_task(loop.run_in_executor, _executor, _run, job_id, spec_dict, out_dir, req.webhook_url)

    # Schedule cleanup
    bg.add_task(_cleanup_old_jobs)

    return JobStatus(**_clean(_jobs[job_id]))


@router.get("/status/{job_id}", response_model=JobStatus)
async def get_status(
    job_id: str,
    api_key: Optional[str] = Depends(optional_api_key)
):
    """
    Get status of a generation job

    No authentication required for status checks
    """
    _validate_job_id(job_id)
    return JobStatus(**_clean(_get(job_id)))


@router.get("/download/{job_id}")
async def download(
    job_id: str,
    client_id: str = Depends(verify_api_key)
):
    """
    Download completed site as ZIP file

    Requires API key authentication
    """
    _validate_job_id(job_id)
    job = _get(job_id)

    if job["status"] != "complete":
        raise HTTPException(400, f"Job is '{job['status']}', not complete")

    zip_path = Path(job["zip_path"])
    if not zip_path.exists():
        raise HTTPException(404, "Zip file missing. Job may have been cleaned up.")

    filename = job["label"].lower().replace(" ", "_") + "_site.zip"
    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename=filename,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Job-ID": job_id,
        }
    )


@router.get("/preview/{job_id}/{filename:path}", response_class=HTMLResponse)
async def preview_file(
    job_id: str,
    filename: str,
    api_key: Optional[str] = Depends(optional_api_key)
):
    """
    Preview a generated file in the browser

    Useful for viewing pages before downloading the full site
    """
    _validate_job_id(job_id)
    job = _get(job_id)

    if job["status"] != "complete":
        raise HTTPException(400, f"Job is '{job['status']}', not complete")

    # Security: prevent directory traversal
    if '..' in filename or filename.startswith('/'):
        raise HTTPException(400, "Invalid filename")

    file_path = Path(job["out_dir"]) / filename
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(404, f"File not found: {filename}")

    # Determine content type
    suffix = file_path.suffix.lower()
    content_types = {
        '.html': 'text/html',
        '.css': 'text/css',
        '.js': 'application/javascript',
        '.json': 'application/json',
    }
    content_type = content_types.get(suffix, 'text/plain')

    content = file_path.read_text(encoding='utf-8')

    return PlainTextResponse(
        content,
        media_type=content_type,
        headers={"X-Job-ID": job_id}
    )


@router.get("/preview/{job_id}", response_class=HTMLResponse)
async def preview_index(
    job_id: str,
    api_key: Optional[str] = Depends(optional_api_key)
):
    """Preview index.html (convenience endpoint)"""
    return await preview_file(job_id, "index.html", api_key)


@router.get("/jobs", response_model=JobsList)
async def list_jobs(
    status: Optional[str] = None,
    limit: int = 50,
    client_id: str = Depends(verify_api_key)
):
    """
    List all generation jobs

    Requires API key authentication
    Query params:
    - status: Filter by status (pending, running, complete, failed, cancelled)
    - limit: Max number of jobs to return (default: 50, max: 100)
    """
    limit = min(limit, 100)

    jobs_list = [_clean(j) for j in _jobs.values()]

    # Filter by status if requested
    if status:
        jobs_list = [j for j in jobs_list if j["status"] == status]

    # Sort by start time (newest first)
    jobs_list = sorted(
        jobs_list,
        key=lambda j: j["started_at"],
        reverse=True
    )[:limit]

    # Calculate stats
    all_jobs = list(_jobs.values())
    stats = {
        "jobs": jobs_list,
        "total": len(_jobs),
        "active": sum(1 for j in all_jobs if j["status"] in ("pending", "running")),
        "completed": sum(1 for j in all_jobs if j["status"] == "complete"),
        "failed": sum(1 for j in all_jobs if j["status"] in ("failed", "cancelled")),
    }

    return JobsList(**stats)


@router.post("/jobs/{job_id}/cancel")
async def cancel_job(
    job_id: str,
    client_id: str = Depends(verify_api_key)
):
    """
    Cancel a running job

    Requires API key authentication
    """
    _validate_job_id(job_id)
    job = _get(job_id)

    if job["status"] not in ("pending", "running"):
        raise HTTPException(400, f"Cannot cancel job with status '{job['status']}'")

    _cancelled_jobs.add(job_id)
    job["status"] = "cancelled"
    job["completed_at"] = datetime.utcnow().isoformat()
    job["error"] = "Cancelled by user"

    return {"job_id": job_id, "status": "cancelled"}


@router.delete("/jobs/{job_id}")
async def delete_job(
    job_id: str,
    client_id: str = Depends(verify_api_key)
):
    """
    Delete a job and all its files

    Requires API key authentication
    Cannot delete running jobs - cancel first
    """
    _validate_job_id(job_id)
    job = _get(job_id)

    if job["status"] == "running":
        raise HTTPException(400, "Cannot delete a running job. Cancel it first.")

    # Delete files
    deleted_files = []
    for path in [settings.jobs_dir / job_id, settings.jobs_dir / f"{job_id}.zip"]:
        if path.exists():
            try:
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()
                deleted_files.append(str(path))
            except Exception as e:
                raise HTTPException(500, f"Failed to delete {path}: {e}")

    del _jobs[job_id]

    return {
        "deleted": job_id,
        "files_removed": deleted_files
    }


@router.get("/health")
async def health_check():
    """
    Health check endpoint (no auth required)

    Returns service status and stats
    """
    all_jobs = list(_jobs.values())

    return {
        "status": "healthy",
        "version": "2.0.0",
        "jobs": {
            "total": len(_jobs),
            "pending": sum(1 for j in all_jobs if j["status"] == "pending"),
            "running": sum(1 for j in all_jobs if j["status"] == "running"),
            "complete": sum(1 for j in all_jobs if j["status"] == "complete"),
            "failed": sum(1 for j in all_jobs if j["status"] == "failed"),
        },
        "config": {
            "max_concurrent_jobs": settings.max_concurrent_jobs,
            "job_retention_hours": settings.job_retention_hours,
            "rate_limit_enabled": settings.rate_limit_enabled,
            "rate_limit_per_hour": settings.rate_limit_per_hour if settings.rate_limit_enabled else None,
        }
    }


# ── Startup cleanup ──────────────────────────────────────────────────────────

@router.on_event("startup")
async def startup_cleanup():
    """Clean up old jobs on startup"""
    print("[STARTUP] Running job cleanup...")
    deleted = await _cleanup_old_jobs()
    print(f"[STARTUP] Cleaned up {len(deleted)} old jobs")
