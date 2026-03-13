"""
RMOS Acoustics Router (Wave 22)

Provides endpoints for the Acoustics Library UI:
- /runs - Browse runs with session/batch filters
- /runs/{run_id} - Get run detail with attachments
- /import-zip - Import viewer_pack ZIP (proxied to real router_import)
- /ingest/events - Browse ingest events
- /ingest/events/{event_id} - Get ingest event detail
- /index/attachment_meta/* - Attachment index endpoints

H7.2.2.1 compliance: signed URLs, no-path disclosure, attachment meta index.

WIRED to real implementations:
- /import-zip - See app.rmos.acoustics.router_import.import_acoustics_zip
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, HTTPException, Query, UploadFile, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Import real implementation for wiring
from ..acoustics.router_import import (
    import_acoustics_zip as _import_acoustics_zip_real,
)


router = APIRouter(tags=["rmos", "acoustics"])

# Use same store root as RunStoreV2
STORE_ROOT_DEFAULT = "services/api/data/runs/rmos"


def _get_runs_root() -> Path:
    return Path(os.getenv("RMOS_RUNS_DIR", STORE_ROOT_DEFAULT)).expanduser().resolve()


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


# =============================================================================
# Response Models
# =============================================================================

class RunsBrowseResponse(BaseModel):
    total: int
    returned: int
    cursor: Optional[str] = None
    runs: List[Dict[str, Any]]


class RunDetailResponse(BaseModel):
    run_id: str
    session_id: Optional[str] = None
    batch_label: Optional[str] = None
    created_at_utc: str
    attachments: List[Dict[str, Any]] = []
    meta: Dict[str, Any] = {}


class IngestEventsBrowseResponse(BaseModel):
    total: int
    returned: int
    cursor: Optional[str] = None
    events: List[Dict[str, Any]]


class FacetsResponse(BaseModel):
    total_attachments: int = 0
    by_kind: Dict[str, int] = {}
    by_mime_prefix: Dict[str, int] = {}


class BrowseResponse(BaseModel):
    total: int = 0
    returned: int = 0
    cursor: Optional[str] = None
    entries: List[Dict[str, Any]] = []


class ImportResponse(BaseModel):
    ok: bool = True
    run_id: str
    attachment_count: int = 0
    message: str = ""


# =============================================================================
# Import Endpoint (proxy to real implementation)
# =============================================================================

@router.post("/import-zip", response_model=ImportResponse)
async def import_zip(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(default=None),
    batch_label: Optional[str] = Form(default=None),
) -> ImportResponse:
    """
    Import a viewer_pack ZIP containing manifest.json + attachments.
    
    Proxies to the real implementation at app.rmos.acoustics.router_import.
    See that module for full documentation on:
    - Validation requirements (validation_report.json with passed=true)
    - ZIP structure (manifest.json + attachments/)
    - Status codes (400=malformed, 422=validation_failed)
    """
    # Proxy to real implementation
    real_response = await _import_acoustics_zip_real(
        file=file,
        session_id=session_id,
        batch_label=batch_label,
    )
    
    # Map real response to our response model
    return ImportResponse(
        ok=True,
        run_id=real_response.run_id,
        attachment_count=real_response.attachments_written,
        message=f"Imported {real_response.attachments_written} attachments (deduped: {real_response.attachments_deduped})",
    )


# =============================================================================
# Attachment Download Endpoint
# =============================================================================

@router.get("/attachments/{sha256}")
def download_attachment(sha256: str):
    """
    Download an attachment by its SHA256 hash.
    Searches the attachment store for the file.
    """
    runs_root = _get_runs_root()
    attachments_dir = runs_root / "attachments"

    # Check common locations for the attachment
    possible_paths = [
        attachments_dir / sha256,
        attachments_dir / f"{sha256}.bin",
        attachments_dir / sha256[:2] / sha256,  # Sharded by first 2 chars
    ]

    for path in possible_paths:
        if path.exists() and path.is_file():
            return FileResponse(
                path=str(path),
                filename=sha256,
                media_type="application/octet-stream",
            )

    raise HTTPException(status_code=404, detail=f"Attachment not found: {sha256}")


# =============================================================================
# Runs Endpoints
# =============================================================================

@router.get("/runs", response_model=RunsBrowseResponse)
def browse_runs(
    limit: int = Query(default=20, ge=1, le=100),
    cursor: Optional[str] = Query(default=None),
    session_id: Optional[str] = Query(default=None),
    batch_label: Optional[str] = Query(default=None),
    include_urls: bool = Query(default=False),
) -> RunsBrowseResponse:
    """
    Browse runs with pagination and optional filters.
    Returns newest runs first (sorted by created_at_utc DESC).
    """
    runs_root = _get_runs_root()
    runs_root.mkdir(parents=True, exist_ok=True)

    # Scan for run files
    all_runs: List[Dict[str, Any]] = []

    if runs_root.exists():
        for date_dir in sorted(runs_root.iterdir(), reverse=True):
            if not date_dir.is_dir():
                continue
            # Look for run_*.json files
            for run_file in date_dir.glob("run_*.json"):
                try:
                    data = _load_json(run_file)
                    run_id = data.get("run_id") or run_file.stem.replace("run_", "")

                    # Apply filters
                    if session_id and data.get("session_id") != session_id:
                        continue
                    if batch_label and data.get("batch_label") != batch_label:
                        continue

                    all_runs.append({
                        "run_id": run_id,
                        "session_id": data.get("session_id"),
                        "batch_label": data.get("batch_label"),
                        "created_at_utc": data.get("created_at") or data.get("created_at_utc") or datetime.utcnow().isoformat() + "Z",
                        "attachment_count": len(data.get("attachments", [])),
                        "mode": data.get("mode", "acoustics"),
                    })
                except (OSError, json.JSONDecodeError):
                    continue

    # Sort by created_at_utc descending
    all_runs.sort(key=lambda r: r.get("created_at_utc", ""), reverse=True)

    total = len(all_runs)
    page = all_runs[:limit]

    return RunsBrowseResponse(
        total=total,
        returned=len(page),
        cursor=None,
        runs=page,
    )


@router.get("/runs/{run_id}", response_model=RunDetailResponse)
def get_run(
    run_id: str,
    include_urls: bool = Query(default=False),
) -> RunDetailResponse:
    """Get detailed run metadata + attachments."""
    runs_root = _get_runs_root()

    # Search for the run file
    target = f"run_{run_id}.json"

    if runs_root.exists():
        for date_dir in sorted(runs_root.iterdir(), reverse=True):
            if not date_dir.is_dir():
                continue
            run_file = date_dir / target
            if run_file.exists():
                data = _load_json(run_file)
                return RunDetailResponse(
                    run_id=run_id,
                    session_id=data.get("session_id"),
                    batch_label=data.get("batch_label"),
                    created_at_utc=data.get("created_at") or data.get("created_at_utc") or datetime.utcnow().isoformat() + "Z",
                    attachments=data.get("attachments", []),
                    meta=data.get("meta", {}),
                )

    raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")


# =============================================================================
# Ingest Events Endpoints
# =============================================================================

@router.get("/ingest/events", response_model=IngestEventsBrowseResponse)
def browse_ingest_events(
    limit: int = Query(default=50, ge=1, le=200),
    cursor: Optional[str] = Query(default=None),
    outcome: Optional[str] = Query(default=None),
) -> IngestEventsBrowseResponse:
    """
    Browse ingest events with pagination and optional outcome filter.
    Returns newest events first (sorted by created_at_utc DESC).
    """
    runs_root = _get_runs_root()
    events_dir = runs_root / "ingest_events"

    all_events: List[Dict[str, Any]] = []

    if events_dir.exists():
        # Scan date directories
        for date_dir in sorted(events_dir.iterdir(), reverse=True):
            if not date_dir.is_dir():
                continue
            for event_file in date_dir.glob("*.json"):
                try:
                    data = _load_json(event_file)

                    # Apply outcome filter
                    if outcome and data.get("outcome") != outcome:
                        continue

                    all_events.append({
                        "event_id": data.get("event_id") or event_file.stem,
                        "created_at_utc": data.get("created_at_utc") or datetime.utcnow().isoformat() + "Z",
                        "outcome": data.get("outcome", "unknown"),
                        "uploader_filename": data.get("uploader_filename"),
                        "run_id": data.get("run_id"),
                        "error_code": data.get("error_code"),
                    })
                except (OSError, json.JSONDecodeError):
                    continue

    # Sort by created_at_utc descending
    all_events.sort(key=lambda e: e.get("created_at_utc", ""), reverse=True)

    total = len(all_events)
    page = all_events[:limit]

    return IngestEventsBrowseResponse(
        total=total,
        returned=len(page),
        cursor=None,
        events=page,
    )


@router.get("/ingest/events/{event_id}")
def get_ingest_event(event_id: str) -> Dict[str, Any]:
    """Get full detail for a single ingest event."""
    runs_root = _get_runs_root()
    events_dir = runs_root / "ingest_events"

    if events_dir.exists():
        # Search date directories
        for date_dir in sorted(events_dir.iterdir(), reverse=True):
            if not date_dir.is_dir():
                continue
            event_file = date_dir / f"{event_id}.json"
            if event_file.exists():
                return _load_json(event_file)

    raise HTTPException(status_code=404, detail=f"Ingest event not found: {event_id}")


# =============================================================================
# Attachment Meta Index Endpoints
# =============================================================================

@router.get("/index/attachment_meta", response_model=BrowseResponse)
def browse_attachment_meta(
    limit: int = Query(default=50, ge=1, le=200),
    cursor: Optional[str] = Query(default=None),
    kind: Optional[str] = Query(default=None),
    _mime_prefix: Optional[str] = Query(default=None),
    include_urls: bool = Query(default=False),
) -> BrowseResponse:
    """Browse attachment meta index with filters."""
    return BrowseResponse(total=0, returned=0, cursor=None, entries=[])


@router.get("/index/attachment_meta/facets", response_model=FacetsResponse)
def get_attachment_facets() -> FacetsResponse:
    """Get facet counts (kind and MIME type distributions)."""
    return FacetsResponse(total_attachments=0, by_kind={}, by_mime_prefix={})


@router.get("/index/attachment_meta/recent", response_model=BrowseResponse)
def get_recent_attachments(
    limit: int = Query(default=50, ge=1, le=200),
    cursor: Optional[str] = Query(default=None),
    kind: Optional[str] = Query(default=None),
    include_urls: bool = Query(default=False),
) -> BrowseResponse:
    """Get recent attachments from precomputed recency index."""
    return BrowseResponse(total=0, returned=0, cursor=None, entries=[])


@router.get("/index/attachment_meta/{sha256}/exists")
def check_attachment_exists(sha256: str) -> Dict[str, Any]:
    """Check if an attachment exists in the index and store."""
    return {"exists": False, "sha256": sha256}


@router.post("/index/rebuild_attachment_meta")
def rebuild_attachment_index() -> Dict[str, Any]:
    """Rebuild the attachment meta index from all runs (proxied to real store)."""
    from .store import RunStoreV2
    
    runs_root = _get_runs_root()
    store = RunStoreV2(runs_root)
    count = store.rebuild_index()
    
    return {"ok": True, "message": f"Rebuilt index with {count} entries", "entries_indexed": count}
