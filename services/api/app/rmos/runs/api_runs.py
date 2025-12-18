"""
RMOS Runs API Router

Provides endpoints for:
- Listing run artifacts
- Getting run details
- Run diffs
- Attachment listing and download
- Attachment verification
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from .schemas import RunArtifact
from .store import get_run, list_runs_filtered, persist_run, create_run_id, patch_run_meta
from .diff import diff_runs
from .attachments import get_attachment_path
from .hashing import summarize_request


router = APIRouter(prefix="/runs", tags=["runs"])


# =============================================================================
# Response Models
# =============================================================================

class RunArtifactSummary(BaseModel):
    """Summary view of a run artifact for list endpoints."""
    run_id: str
    created_at_utc: str
    event_type: str
    status: str
    workflow_session_id: Optional[str] = None
    tool_id: Optional[str] = None
    material_id: Optional[str] = None
    machine_id: Optional[str] = None
    workflow_mode: Optional[str] = None
    request_hash: Optional[str] = None
    toolpaths_hash: Optional[str] = None
    gcode_hash: Optional[str] = None
    notes: Optional[str] = None


def _to_summary(r: RunArtifact) -> RunArtifactSummary:
    return RunArtifactSummary(
        run_id=r.run_id,
        created_at_utc=r.created_at_utc,
        event_type=r.event_type,
        status=r.status,
        workflow_session_id=r.workflow_session_id,
        tool_id=r.tool_id,
        material_id=r.material_id,
        machine_id=r.machine_id,
        workflow_mode=r.workflow_mode,
        request_hash=r.request_hash,
        toolpaths_hash=r.toolpaths_hash,
        gcode_hash=r.gcode_hash,
        notes=r.notes,
    )


# =============================================================================
# Request Models (NEW - From Gap Analysis)
# =============================================================================

class RunCreateRequest(BaseModel):
    """Request body for creating a new run artifact."""
    mode: str = Field(default="unknown", description="Operation mode (cam, preview, simulation)")
    tool_id: str = Field(default="unknown", description="Tool identifier")
    status: str = Field(default="OK", description="Run status (OK, BLOCKED, ERROR)")
    event_type: str = Field(default="unknown", description="Event type (approval, toolpaths, etc)")
    request_summary: Dict[str, Any] = Field(default_factory=dict, description="Redacted request summary")
    feasibility: Dict[str, Any] = Field(default_factory=dict, description="Feasibility evaluation result")
    meta: Dict[str, Any] = Field(default_factory=dict, description="Free-form metadata")


class PatchMetaRequest(BaseModel):
    """Request body for patching run metadata."""
    meta_updates: Dict[str, Any] = Field(default_factory=dict, description="Key-value pairs to merge into meta")


# =============================================================================
# Create / Patch Endpoints (NEW - From Gap Analysis)
# =============================================================================

@router.post("", response_model=Dict[str, Any], summary="Create a new run artifact.")
def create_run_endpoint(req: RunCreateRequest, request: Request):
    """
    Create a new run artifact.

    POST /api/rmos/runs

    Request body:
    ```json
    {
      "mode": "cam",
      "tool_id": "T102",
      "status": "OK",
      "event_type": "approval",
      "request_summary": {"design": {...}},
      "feasibility": {...},
      "meta": {"client_version": "1.2.3"}
    }
    ```

    Response:
    ```json
    {
      "run_id": "run_abc123...",
      "status": "created"
    }
    ```
    """
    from datetime import datetime, timezone

    run_id = create_run_id()
    req_id = getattr(request.state, "request_id", None) or request.headers.get("x-request-id")

    # Build the artifact
    artifact = RunArtifact(
        run_id=run_id,
        created_at_utc=datetime.now(timezone.utc).isoformat(),
        event_type=req.event_type,
        status=req.status,
        tool_id=req.tool_id,
        mode=req.mode,
        request_summary=req.request_summary,
        feasibility=req.feasibility,
        meta={**req.meta, **({"request_id": req_id} if req_id else {})},
    )

    persist_run(artifact)
    return {"run_id": run_id, "status": "created"}


@router.patch("/{run_id}/meta", response_model=Dict[str, Any], summary="Patch run metadata.")
def patch_meta_endpoint(run_id: str, req: PatchMetaRequest):
    """
    Update the meta field of a run artifact.

    PATCH /api/rmos/runs/{run_id}/meta

    Request body:
    ```json
    {
      "meta_updates": {
        "note": "Updated via API",
        "reviewed_by": "user@example.com"
      }
    }
    ```

    Response:
    ```json
    {
      "run_id": "run_abc123...",
      "meta": {...updated meta...},
      "status": "updated"
    }
    ```
    """
    try:
        artifact = patch_run_meta(run_id, req.meta_updates)
        return {"run_id": run_id, "meta": artifact.meta, "status": "updated"}
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")


# =============================================================================
# List / Detail Endpoints
# =============================================================================

@router.get("", response_model=List[RunArtifactSummary], summary="List run artifacts.")
def list_runs_endpoint(
    limit: int = Query(50, ge=1, le=500),
    event_type: Optional[str] = None,
    status: Optional[str] = None,
    workflow_session_id: Optional[str] = None,
    tool_id: Optional[str] = None,
    material_id: Optional[str] = None,
    machine_id: Optional[str] = None,
):
    """List run artifacts with optional filtering."""
    runs = list_runs_filtered(
        limit=limit,
        event_type=event_type,
        status=status,
        workflow_session_id=workflow_session_id,
        tool_id=tool_id,
        material_id=material_id,
        machine_id=machine_id,
    )
    return [_to_summary(r) for r in runs]


@router.get("/diff", summary="Diff two run artifacts by id.")
def diff_two_runs(a: str, b: str) -> Dict[str, Any]:
    """
    Compute authoritative diff between two runs.
    
    Returns severity (CRITICAL/WARNING/INFO) and structured diff.
    """
    try:
        ra = get_run(a)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Run {a} not found")
    
    try:
        rb = get_run(b)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Run {b} not found")
    
    return diff_runs(ra, rb)


@router.get("/{run_id}", response_model=Dict[str, Any], summary="Get run artifact details.")
def read_run(run_id: str) -> Dict[str, Any]:
    """Get full details of a run artifact."""
    try:
        r = get_run(run_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {
        "run_id": r.run_id,
        "created_at_utc": r.created_at_utc,
        "workflow_session_id": r.workflow_session_id,
        "tool_id": r.tool_id,
        "material_id": r.material_id,
        "machine_id": r.machine_id,
        "workflow_mode": r.workflow_mode,
        "toolchain_id": r.toolchain_id,
        "post_processor_id": r.post_processor_id,
        "geometry_ref": r.geometry_ref,
        "geometry_hash": r.geometry_hash,
        "event_type": r.event_type,
        "status": r.status,
        "feasibility": r.feasibility,
        "request_hash": r.request_hash,
        "toolpaths_hash": r.toolpaths_hash,
        "gcode_hash": r.gcode_hash,
        "attachments": [
            {
                "sha256": a.sha256,
                "kind": a.kind,
                "mime": a.mime,
                "filename": a.filename,
                "size_bytes": a.size_bytes,
                "created_at_utc": a.created_at_utc,
            }
            for a in (r.attachments or [])
        ],
        "parent_run_id": r.parent_run_id,
        "drift_detected": r.drift_detected,
        "drift_summary": r.drift_summary,
        "gate_decision": r.gate_decision,
        "engine_version": r.engine_version,
        "toolchain_version": r.toolchain_version,
        "config_fingerprint": r.config_fingerprint,
        "notes": r.notes,
        "errors": r.errors,
    }


# =============================================================================
# Attachment Endpoints
# =============================================================================

@router.get("/{run_id}/attachments", summary="List attachments for a run.")
def list_run_attachments(run_id: str):
    """List all attachments for a run artifact."""
    try:
        r = get_run(run_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    
    atts = r.attachments or []
    return {
        "run_id": r.run_id,
        "count": len(atts),
        "attachments": [
            {
                "sha256": a.sha256,
                "kind": a.kind,
                "mime": a.mime,
                "filename": a.filename,
                "size_bytes": a.size_bytes,
                "created_at_utc": a.created_at_utc,
                "download_url": f"/api/runs/{r.run_id}/attachments/{a.sha256}",
            }
            for a in atts
        ],
    }


@router.get("/{run_id}/attachments/{sha256}", summary="Download a run attachment.")
def download_run_attachment(run_id: str, sha256: str):
    """Download attachment blob by SHA256."""
    try:
        r = get_run(run_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    
    atts = r.attachments or []
    if not any(a.sha256 == sha256 for a in atts):
        raise HTTPException(status_code=404, detail="Attachment not found on run.")

    path = get_attachment_path(sha256)
    if not path:
        raise HTTPException(status_code=404, detail="Attachment blob not found on disk.")

    meta = next(a for a in atts if a.sha256 == sha256)
    return FileResponse(path, media_type=meta.mime, filename=meta.filename)


@router.get("/{run_id}/attachments/verify", summary="Verify attachment integrity.")
def verify_run_attachments(run_id: str):
    """Verify all attachment SHA256 hashes match stored blobs."""
    from .attachments import get_attachment_path
    from .hashing import sha256_file
    
    try:
        r = get_run(run_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    
    atts = r.attachments or []
    results = []
    ok = True

    for a in atts:
        path = get_attachment_path(a.sha256)
        if not path:
            ok = False
            results.append({
                "sha256": a.sha256,
                "kind": a.kind,
                "filename": a.filename,
                "ok": False,
                "error": "blob_not_found",
            })
            continue

        import os
        actual = sha256_file(path)
        match = (actual == a.sha256)
        if not match:
            ok = False

        results.append({
            "sha256": a.sha256,
            "kind": a.kind,
            "filename": a.filename,
            "ok": match,
            "path": path,
            "size_bytes": os.path.getsize(path),
            "actual_sha256": actual,
        })

    return {
        "run_id": r.run_id,
        "verification": {
            "ok": ok,
            "count": len(atts),
            "results": results,
        },
    }
