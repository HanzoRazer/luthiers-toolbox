"""
RMOS Runs API Router v2 - Governance Compliant

Provides endpoints for:
- Listing run artifacts (date-partitioned)
- Getting run details
- Creating run artifacts (immutable)
- Run diffs
- Attachment listing and download
- Attachment verification
- Advisory attachment (append-only)

REMOVED (Strict Immutability):
- PATCH /runs/{run_id}/meta - Artifacts are immutable
- All post-creation modifications go through append-only advisory links
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.auth import Principal, require_roles

from .schemas import (
    RunArtifact,
    RunDecision,
    Hashes,
    AdvisoryInputRef,
    RunAttachmentCreateRequest,
    RunAttachmentCreateResponse,
    BindArtStudioCandidateRequest,
    BindArtStudioCandidateResponse,
)
from .store import (
    get_run,
    list_runs_filtered,
    persist_run,
    create_run_id,
    attach_advisory,
)
from .diff import build_diff
from .attachments import get_attachment_path, put_json_attachment
from .hashing import summarize_request, compute_feasibility_hash
from app.rmos.api.response_utils import runs_list_response

import json
import time

router = APIRouter(prefix="/runs", tags=["runs"])

# Mount batch-tree endpoints in the same /runs router namespace
from .api_batch_tree import router as batch_tree_router

router.include_router(batch_tree_router)

# Option B: batch audit export
from .api_audit_export import router as audit_export_router

router.include_router(audit_export_router)

# Option B: batch timeline
from .api_batch_timeline import router as batch_timeline_router

router.include_router(batch_timeline_router)

# Option B: grouped (tree-aware) timeline feed
from .api_grouped_timeline import router as grouped_timeline_router

router.include_router(grouped_timeline_router)

# Option B: batch summary dashboard with KPI rollups
from .api_batch_dashboard import router as batch_dashboard_router

router.include_router(batch_dashboard_router)

# Option B: batch summary (session/batch scoped)
from .api_batch_summary import router as batch_summary_router

router.include_router(batch_summary_router)

# Global content-addressed attachment fetch (fixes truncated diffs)
from .api_global_attachments import router as global_attachments_router

router.include_router(global_attachments_router)


# =============================================================================
# Response Models
# =============================================================================


class RunArtifactSummary(BaseModel):
    """Summary view of a run artifact for list endpoints."""

    run_id: str
    created_at_utc: str
    event_type: str
    status: str
    mode: str
    tool_id: str
    material_id: Optional[str] = None
    machine_id: Optional[str] = None
    workflow_session_id: Optional[str] = None
    risk_level: Optional[str] = None
    feasibility_sha256: Optional[str] = None
    toolpaths_sha256: Optional[str] = None
    gcode_sha256: Optional[str] = None
    explanation_status: Optional[str] = None
    advisory_count: int = 0


def _to_summary(r: RunArtifact) -> RunArtifactSummary:
    """Convert RunArtifact to summary view."""
    created_at = r.created_at_utc
    if hasattr(created_at, "isoformat"):
        created_at = created_at.isoformat()

    return RunArtifactSummary(
        run_id=r.run_id,
        created_at_utc=created_at,
        event_type=r.event_type,
        status=r.status,
        mode=r.mode,
        tool_id=r.tool_id,
        material_id=r.material_id,
        machine_id=r.machine_id,
        workflow_session_id=r.workflow_session_id,
        risk_level=r.decision.risk_level if r.decision else None,
        feasibility_sha256=r.hashes.feasibility_sha256 if r.hashes else None,
        toolpaths_sha256=r.hashes.toolpaths_sha256 if r.hashes else None,
        gcode_sha256=r.hashes.gcode_sha256 if r.hashes else None,
        explanation_status=r.explanation_status,
        advisory_count=len(r.advisory_inputs) if r.advisory_inputs else 0,
    )


# =============================================================================
# Request Models
# =============================================================================


class RunCreateRequest(BaseModel):
    """Request body for creating a new run artifact."""

    mode: str = Field(
        default="unknown", description="Operation mode (cam, preview, simulation)"
    )
    tool_id: str = Field(default="unknown", description="Tool identifier")
    status: str = Field(default="OK", description="Run status (OK, BLOCKED, ERROR)")
    event_type: str = Field(
        default="unknown", description="Event type (approval, toolpaths, etc)"
    )
    request_summary: Dict[str, Any] = Field(
        default_factory=dict, description="Redacted request summary"
    )
    feasibility: Dict[str, Any] = Field(
        default_factory=dict, description="Feasibility evaluation result"
    )
    decision: Optional[Dict[str, Any]] = Field(
        default=None, description="Decision override (optional)"
    )
    meta: Dict[str, Any] = Field(default_factory=dict, description="Free-form metadata")


class AttachAdvisoryRequest(BaseModel):
    """Request body for attaching an advisory to a run."""

    advisory_id: str = Field(..., description="Unique identifier of the advisory asset")
    kind: str = Field(
        default="unknown", description="Type: explanation, advisory, note"
    )
    engine_id: Optional[str] = Field(None, description="AI engine that created it")
    engine_version: Optional[str] = Field(None, description="Engine version")


class SuggestAndAttachRequest(BaseModel):
    """Request body for generating and attaching an explanation/advisory."""

    # Team decision: sync now; async flag reserved as escape hatch
    generate_explanation: bool = Field(
        False, description="Generate placeholder explanation"
    )
    async_explanation: bool = Field(
        False, description="Reserved for future async support"
    )

    # Advisory typing
    kind: str = Field("explanation", description="Type: explanation, advisory, note")

    # Optional: user prompt for what they want explained (future AI UX)
    prompt: Optional[str] = Field(None, description="User prompt for explanation")

    # Optional: allow attaching a provided payload without LLM
    advisory_markdown: Optional[str] = Field(
        None, description="Pre-generated markdown content"
    )
    advisory_json: Optional[Dict[str, Any]] = Field(
        None, description="Pre-generated JSON data"
    )

    # Optional provenance
    engine_id: Optional[str] = Field(None, description="AI engine that created it")
    engine_version: Optional[str] = Field(None, description="Engine version")


class SuggestAndAttachResponse(BaseModel):
    """Response from suggest-and-attach endpoint."""

    run_id: str
    advisory_sha256: str
    explanation_status: str
    explanation_summary: Optional[str] = None
    compute_ms: float


# =============================================================================
# Create Endpoint (Immutable)
# =============================================================================


@router.post("", response_model=Dict[str, Any], summary="Create a new run artifact.")
def create_run_endpoint(req: RunCreateRequest, request: Request):
    """
    Create a new run artifact.

    IMMUTABLE: Once created, artifacts cannot be modified.
    Use advisory attachments for post-creation data.

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
      "status": "created",
      "feasibility_sha256": "..."
    }
    ```
    """
    run_id = create_run_id()
    req_id = getattr(request.state, "request_id", None) or request.headers.get(
        "x-request-id"
    )

    # Compute required feasibility hash
    feasibility_sha256 = compute_feasibility_hash(req.feasibility)

    # Build hashes
    hashes = Hashes(
        feasibility_sha256=feasibility_sha256,
    )

    # Build decision
    if req.decision:
        decision = RunDecision(
            risk_level=req.decision.get("risk_level", "UNKNOWN"),
            score=req.decision.get("score"),
            block_reason=req.decision.get("block_reason"),
            warnings=req.decision.get("warnings", []),
            details=req.decision.get("details", {}),
        )
    else:
        # Extract from feasibility if available
        risk_level = (
            req.feasibility.get("risk_bucket")
            or req.feasibility.get("risk_level")
            or "UNKNOWN"
        )
        decision = RunDecision(
            risk_level=risk_level,
            score=req.feasibility.get("score"),
            block_reason=req.feasibility.get("block_reason"),
            warnings=req.feasibility.get("warnings", []),
        )

    # Build the artifact
    artifact = RunArtifact(
        run_id=run_id,
        created_at_utc=datetime.now(timezone.utc),
        event_type=req.event_type,
        status=req.status,
        tool_id=req.tool_id,
        mode=req.mode,
        request_summary=(
            summarize_request(req.request_summary) if req.request_summary else {}
        ),
        feasibility=req.feasibility,
        decision=decision,
        hashes=hashes,
        meta={**req.meta, **({"request_id": req_id} if req_id else {})},
    )

    persist_run(artifact)
    return {
        "run_id": run_id,
        "status": "created",
        "feasibility_sha256": feasibility_sha256,
    }


# =============================================================================
# NOTE: PATCH endpoint REMOVED per strict immutability decision
# =============================================================================
# The following endpoint was intentionally removed:
#
# @router.patch("/{run_id}/meta")
# def patch_meta_endpoint(...)
#
# Run artifacts are IMMUTABLE per governance contract.
# Use attach_advisory() for post-creation data.
# =============================================================================


# =============================================================================
# List / Detail Endpoints
# =============================================================================


@router.get("", response_model=Dict[str, Any], summary="List run artifacts.")
def list_runs_endpoint(
    limit: int = Query(50, ge=1, le=500),
    event_type: Optional[str] = None,
    kind: Optional[str] = Query(None, description="Alias for event_type"),
    status: Optional[str] = None,
    tool_id: Optional[str] = None,
    mode: Optional[str] = None,
    batch_label: Optional[str] = Query(
        None, description="Filter runs by batch_label (from meta)"
    ),
    session_id: Optional[str] = Query(
        None, description="Filter runs by session_id (from meta)"
    ),
    parent_batch_plan_artifact_id: Optional[str] = Query(
        None, description="Filter runs by parent batch plan artifact ID"
    ),
    parent_batch_spec_artifact_id: Optional[str] = Query(
        None, description="Filter runs by parent batch spec artifact ID"
    ),
):
    """
    List run artifacts with optional filtering.

    Results are sorted by creation date (newest first).
    Supports filtering by batch_label and session_id from run metadata.
    """
    runs = list_runs_filtered(
        limit=limit,
        event_type=event_type,
        kind=kind,
        status=status,
        tool_id=tool_id,
        mode=mode,
        batch_label=batch_label,
        session_id=session_id,
        parent_batch_plan_artifact_id=parent_batch_plan_artifact_id,
        parent_batch_spec_artifact_id=parent_batch_spec_artifact_id,
    )
    items = [_to_summary(r).model_dump() for r in runs]
    return runs_list_response(items, limit=limit)


@router.get("/diff", summary="Diff two run artifacts by id.")
def diff_two_runs(
    left_id: str = Query(..., description="Left run artifact id"),
    right_id: str = Query(..., description="Right run artifact id"),
    preview_max_chars: int = Query(20000, ge=1000, le=200000),
    force_attachment: bool = Query(
        False, description="Always persist full diff as attachment"
    ),
) -> Dict[str, Any]:
    """
    Diff two runs.

    Contract:
      - preview is always present (bounded)
      - full diff is persisted as a run attachment when needed
      - NEVER returns full diff inline (prevents truncation by server/UI)

    Download full diff (when provided):
      GET /api/rmos/runs/{run_id}/attachments/{sha256}
      where run_id is right_id in the response payload.
    """
    from .diff_attachments import persist_diff_as_attachment_if_needed

    left = get_run(left_id)
    if left is None:
        raise HTTPException(status_code=404, detail=f"Run {left_id} not found")

    right = get_run(right_id)
    if right is None:
        raise HTTPException(status_code=404, detail=f"Run {right_id} not found")

    diff_text = build_diff(left, right)

    att = persist_diff_as_attachment_if_needed(
        left_id=left_id,
        right_id=right_id,
        diff_text=diff_text,
        preview_max_chars=preview_max_chars,
        force_attachment=force_attachment,
    )

    return {
        "left_id": left_id,
        "right_id": right_id,
        "diff_kind": "unified",
        "preview": att.preview,
        "truncated": att.truncated,
        "full_bytes": att.full_bytes,
        "diff_attachment": (
            {
                "run_id": right_id,  # IMPORTANT: route requires run_id
                "sha256": att.attachment_sha256,
                "content_type": att.attachment_content_type,
                "filename": att.attachment_filename,
                "kind": "run_diff",
            }
            if att.attachment_sha256
            else None
        ),
    }


@router.get(
    "/{run_id}", response_model=Dict[str, Any], summary="Get run artifact details."
)
def read_run(run_id: str) -> Dict[str, Any]:
    """Get full details of a run artifact."""
    r = get_run(run_id)
    if r is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "RUN_NOT_FOUND", "run_id": run_id},
        )

    created_at = r.created_at_utc
    if hasattr(created_at, "isoformat"):
        created_at = created_at.isoformat()

    return {
        "run_id": r.run_id,
        "created_at_utc": created_at,
        "event_type": r.event_type,
        "status": r.status,
        "mode": r.mode,
        "tool_id": r.tool_id,
        # Context
        "workflow_session_id": r.workflow_session_id,
        "material_id": r.material_id,
        "machine_id": r.machine_id,
        "workflow_mode": r.workflow_mode,
        "toolchain_id": r.toolchain_id,
        "post_processor_id": r.post_processor_id,
        # Geometry
        "geometry_ref": r.geometry_ref,
        "geometry_hash": r.geometry_hash,
        # Hashes (v2 nested model)
        "hashes": {
            "feasibility_sha256": r.hashes.feasibility_sha256,
            "toolpaths_sha256": r.hashes.toolpaths_sha256,
            "gcode_sha256": r.hashes.gcode_sha256,
            "opplan_sha256": r.hashes.opplan_sha256,
        },
        # Decision (v2 nested model)
        "decision": {
            "risk_level": r.decision.risk_level,
            "score": r.decision.score,
            "block_reason": r.decision.block_reason,
            "warnings": r.decision.warnings,
            "details": r.decision.details,
        },
        # Feasibility
        "feasibility": r.feasibility,
        "request_summary": r.request_summary,
        # Outputs
        "outputs": {
            "gcode_text": r.outputs.gcode_text if r.outputs else None,
            "gcode_path": r.outputs.gcode_path if r.outputs else None,
            "opplan_json": r.outputs.opplan_json if r.outputs else None,
            "opplan_path": r.outputs.opplan_path if r.outputs else None,
            "preview_svg_path": r.outputs.preview_svg_path if r.outputs else None,
        },
        # Advisory
        "advisory_inputs": [
            {
                "advisory_id": a.advisory_id,
                "kind": a.kind,
                "engine_id": a.engine_id,
                "engine_version": a.engine_version,
                "request_id": a.request_id,
                "created_at_utc": (
                    a.created_at_utc.isoformat()
                    if hasattr(a.created_at_utc, "isoformat")
                    else a.created_at_utc
                ),
            }
            for a in (r.advisory_inputs or [])
        ],
        "explanation_status": r.explanation_status,
        "explanation_summary": r.explanation_summary,
        # Attachments
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
        # Drift
        "parent_run_id": r.parent_run_id,
        "drift_detected": r.drift_detected,
        "drift_summary": r.drift_summary,
        # Gating
        "gate_policy_id": r.gate_policy_id,
        "gate_decision": r.gate_decision,
        # Versions
        "engine_version": r.engine_version,
        "toolchain_version": r.toolchain_version,
        "config_fingerprint": r.config_fingerprint,
        # Notes
        "notes": r.notes,
        "errors": r.errors,
        # Meta
        "meta": r.meta,
    }


# =============================================================================
# Advisory Endpoints (NEW - Append-Only Pattern)
# =============================================================================


@router.post("/{run_id}/attach-advisory", summary="Attach an advisory to a run.")
def attach_advisory_endpoint(run_id: str, req: AttachAdvisoryRequest, request: Request):
    """
    Attach an advisory reference to a run artifact.

    APPEND-ONLY: This creates a separate link file, preserving
    the original artifact's immutability.

    POST /api/rmos/runs/{run_id}/attach-advisory

    Request body:
    ```json
    {
      "advisory_id": "adv_abc123...",
      "kind": "explanation",
      "engine_id": "claude-3-5-sonnet",
      "engine_version": "20241022"
    }
    ```

    Response:
    ```json
    {
      "run_id": "run_abc123...",
      "advisory_id": "adv_abc123...",
      "status": "attached"
    }
    ```
    """
    req_id = getattr(request.state, "request_id", None) or request.headers.get(
        "x-request-id"
    )

    ref = attach_advisory(
        run_id=run_id,
        advisory_id=req.advisory_id,
        kind=req.kind,
        engine_id=req.engine_id,
        engine_version=req.engine_version,
        request_id=req_id,
    )

    if ref is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    return {
        "run_id": run_id,
        "advisory_id": req.advisory_id,
        "status": "attached",
    }


@router.get("/{run_id}/advisories", summary="List advisories attached to a run.")
def list_advisories(run_id: str):
    """List all advisory references attached to a run."""
    r = get_run(run_id)
    if r is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    advisories = r.advisory_inputs or []
    return {
        "run_id": run_id,
        "count": len(advisories),
        "advisories": [
            {
                "advisory_id": a.advisory_id,
                "kind": a.kind,
                "engine_id": a.engine_id,
                "engine_version": a.engine_version,
                "request_id": a.request_id,
                "created_at_utc": (
                    a.created_at_utc.isoformat()
                    if hasattr(a.created_at_utc, "isoformat")
                    else a.created_at_utc
                ),
            }
            for a in advisories
        ],
    }


@router.post(
    "/{run_id}/suggest-and-attach",
    response_model=SuggestAndAttachResponse,
    summary="Generate and attach an explanation.",
)
def suggest_and_attach(
    run_id: str, body: SuggestAndAttachRequest, request: Request
) -> SuggestAndAttachResponse:
    """
    Orchestrator endpoint for generating and attaching explanations/advisories.

    This endpoint:
    1. Loads an existing RunArtifact
    2. Optionally generates an explanation (sync now; async reserved)
    3. Stores the canonical payload as a content-addressed attachment
    4. Appends an AdvisoryInputRef to the run (append-only)
    5. Sets inline explanation_status + summary (preview only)

    POST /api/runs/{run_id}/suggest-and-attach

    Request body:
    ```json
    {
      "generate_explanation": true,
      "kind": "explanation",
      "engine_id": "placeholder",
      "engine_version": "1.0"
    }
    ```

    Or provide pre-generated content:
    ```json
    {
      "kind": "explanation",
      "advisory_markdown": "# My Explanation\\n\\nDetails here...",
      "engine_id": "claude-3-5-sonnet"
    }
    ```
    """
    t0 = time.perf_counter()
    req_id = getattr(request.state, "request_id", None) or request.headers.get(
        "x-request-id"
    )

    # 1) Load run
    run = get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    # 2) Enforce sync-only for now (escape hatch reserved)
    if body.async_explanation:
        raise HTTPException(
            status_code=409,
            detail="async_explanation not enabled yet (sync-only MVP).",
        )

    # 3) Build canonical advisory payload
    markdown: Optional[str] = None
    payload_json: Dict[str, Any] = {}

    if body.advisory_markdown:
        markdown = body.advisory_markdown

    if body.advisory_json:
        payload_json.update(body.advisory_json)

    if markdown is None and not payload_json and body.generate_explanation:
        # MVP placeholder until LLM transport is wired
        summary = summarize_request(
            run.request_summary if isinstance(run.request_summary, dict) else {}
        )
        markdown = (
            f"# RMOS {body.kind.title()}\n\n"
            f"**Run:** `{run.run_id}`\n\n"
            f"## Summary\n"
            f"This is a placeholder explanation (LLM not wired yet).\n\n"
            f"## Request Summary\n"
            f"```json\n{json.dumps(summary, indent=2, ensure_ascii=False)}\n```\n"
        )
        payload_json = {
            "kind": body.kind,
            "run_id": run.run_id,
            "request_id": req_id,
            "note": "placeholder explanation until LLM transport is wired",
        }

    if markdown is None and not payload_json:
        raise HTTPException(
            status_code=400,
            detail="No advisory content provided. Set generate_explanation=true or supply advisory_markdown/advisory_json.",
        )

    # 4) Build envelope and store as content-addressed attachment
    created_at_str = (
        run.created_at_utc.isoformat()
        if hasattr(run.created_at_utc, "isoformat")
        else str(run.created_at_utc)
    )
    envelope = {
        "kind": body.kind,
        "run_id": run.run_id,
        "request_id": req_id,
        "engine_id": body.engine_id,
        "engine_version": body.engine_version,
        "prompt": body.prompt,
        "markdown": markdown,
        "data": payload_json,
        "created_at_utc": created_at_str,
    }

    # Store as JSON attachment (returns RunAttachment, path, sha256)
    _, _, advisory_sha256 = put_json_attachment(
        obj=envelope,
        kind=body.kind,
        filename=f"{run.run_id}_{body.kind}.json",
        ext=".json",
    )

    # 5) Append advisory ref to run (append-only)
    attach_advisory(
        run_id=run.run_id,
        advisory_id=advisory_sha256,
        kind=body.kind,
        engine_id=body.engine_id,
        engine_version=body.engine_version,
        request_id=req_id,
    )

    # 6) Determine explanation status and summary
    explanation_status = "READY" if body.kind == "explanation" else "NONE"
    explanation_summary = (markdown or "").strip()[:500] if markdown else None

    compute_ms = (time.perf_counter() - t0) * 1000.0

    return SuggestAndAttachResponse(
        run_id=run.run_id,
        advisory_sha256=advisory_sha256,
        explanation_status=explanation_status,
        explanation_summary=explanation_summary,
        compute_ms=compute_ms,
    )


# =============================================================================
# Attachment Endpoints
# =============================================================================


@router.get("/{run_id}/attachments", summary="List attachments for a run.")
def list_run_attachments(run_id: str):
    """List all attachments for a run artifact."""
    r = get_run(run_id)
    if r is None:
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
                "download_url": f"/api/rmos/runs/{r.run_id}/attachments/{a.sha256}",
            }
            for a in atts
        ],
    }


@router.get("/{run_id}/attachments/{sha256}", summary="Download a run attachment.")
def download_run_attachment(run_id: str, sha256: str):
    """
    Download attachment blob by SHA256.

    Supports both registered attachments (on run's attachments list) and
    content-addressed blobs stored via persist_diff_as_attachment_if_needed.
    """
    # First check if file exists on disk (content-addressed)
    path = get_attachment_path(sha256)
    if not path:
        raise HTTPException(
            status_code=404, detail="Attachment blob not found on disk."
        )

    # Try to get metadata from run's attachments list
    r = get_run(run_id)
    if r is not None:
        atts = getattr(r, "attachments", None) or []
        meta = next((a for a in atts if a.sha256 == sha256), None)
        if meta is not None:
            return FileResponse(path, media_type=meta.mime, filename=meta.filename)

    # Content-addressed blob exists but not registered on run
    # (e.g., diff attachments created on-the-fly)
    # Serve with generic mime type
    return FileResponse(
        path,
        media_type="application/octet-stream",
        filename=f"{sha256[:16]}.bin",
    )


@router.get("/{run_id}/attachments/verify", summary="Verify attachment integrity.")
def verify_run_attachments(run_id: str):
    """Verify all attachment SHA256 hashes match stored blobs."""
    from .attachments import verify_attachment

    r = get_run(run_id)
    if r is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    atts = r.attachments or []
    results = []
    ok = True

    for a in atts:
        result = verify_attachment(a.sha256)
        result["kind"] = a.kind
        result["filename"] = a.filename
        if not result["ok"]:
            ok = False
        results.append(result)

    return {
        "run_id": r.run_id,
        "verification": {
            "ok": ok,
            "count": len(atts),
            "results": results,
        },
    }


@router.post(
    "/{run_id}/attachments",
    response_model=RunAttachmentCreateResponse,
    summary="Create attachment for run",
)
def create_run_attachment(run_id: str, req: RunAttachmentCreateRequest):
    """
    Upload attachment to a run with SHA256 verification.

    Returns 400 if:
    - Run not found
    - SHA256 mismatch between declared and actual content
    - Invalid base64 payload

    Returns 200 with attachment metadata if successful.
    """
    import base64
    from .attachments import put_bytes_attachment
    from .hashing import sha256_of_bytes

    # Verify run exists
    run = get_run(run_id)
    if run is None:
        raise HTTPException(status_code=400, detail=f"Run {run_id} not found")

    # Decode base64 payload
    try:
        data = base64.b64decode(req.b64)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid base64 payload: {e}")

    # Verify SHA256 matches
    actual_sha = sha256_of_bytes(data)
    if actual_sha != req.sha256:
        raise HTTPException(
            status_code=400,
            detail=f"SHA256 mismatch: expected {req.sha256}, got {actual_sha}",
        )

    # Store attachment (content-addressed, auto-deduplicates)
    attachment, _path = put_bytes_attachment(
        data=data,
        kind=req.kind,
        mime=req.content_type,
        filename=req.filename,
        ext="",  # Extension determined from mime/filename if needed
    )

    # Return response
    return RunAttachmentCreateResponse(
        attachment_id=attachment.sha256,  # Content-addressed: sha256 is the ID
        sha256=attachment.sha256,
        kind=attachment.kind,
    )


@router.post(
    "/{run_id}/artifacts/bind-art-studio-candidate",
    response_model=BindArtStudioCandidateResponse,
    summary="Bind Art Studio candidate to run artifact",
)
def bind_art_studio_candidate_route(
    run_id: str, req: BindArtStudioCandidateRequest, request: Request
):
    """
    RMOS authority gate: Bind Art Studio candidate attachments into a RunArtifact
    with ALLOW/BLOCK + risk + hashes.

    Creates a RunArtifact for EVERY bind attempt (ALLOW or BLOCK).

    Returns 400 if:
    - Run not found
    - Attachments missing (when strict=true)
    - Attachment SHA verification fails
    - Invalid spec schema

    Returns 200 with decision=ALLOW or decision=BLOCK (both persist artifacts).
    Never returns 403 or 409 (blocked artifacts are persisted with decision=BLOCK).
    """
    from .bind_art_studio_service import bind_art_studio_candidate, ENGINE_VERSION

    # Verify run exists
    run = get_run(run_id)
    if run is None:
        raise HTTPException(status_code=400, detail=f"Run {run_id} not found")

    # Get request ID for tracing
    req_id = getattr(request.state, "request_id", None) or request.headers.get(
        "x-request-id"
    )

    try:
        # Run the real binding service with SVG safety checks
        result = bind_art_studio_candidate(
            run_id=run_id,
            attachment_ids=req.attachment_ids,
            operator_notes=req.operator_notes,
            strict=req.strict,
            request_id=req_id,
        )
    except ValueError as e:
        # Invalid request / integrity / missing required components: fail closed, do not mint
        raise HTTPException(status_code=400, detail=str(e))

    decision = result["decision"]
    risk_level = result["risk_level"]
    score = result["feasibility_score"]
    feasibility_sha = result["feasibility_sha256"]
    attachment_sha_map = result["attachment_sha256_map"]

    # Create RunArtifact (persisted for both ALLOW and BLOCK)
    artifact_id = create_run_id()

    if decision == "BLOCK":
        # Create blocked artifact
        artifact = RunArtifact(
            run_id=artifact_id,
            status="BLOCKED",
            mode="art_studio_candidate",
            tool_id="art_studio",
            hashes=Hashes(
                feasibility_sha256=feasibility_sha,
            ),
            decision=RunDecision(
                risk_level=risk_level,
                score=score * 100,  # Convert 0-1 to 0-100
                block_reason=result.get("reason"),
                warnings=[],
            ),
            request_summary={"attachment_ids": list(attachment_sha_map.keys())},
            meta={
                "engine_version": ENGINE_VERSION,
                "operator_notes": req.operator_notes,
            },
        )
    else:
        # Create ALLOW artifact
        artifact = RunArtifact(
            run_id=artifact_id,
            status="OK",
            mode="art_studio_candidate",
            tool_id="art_studio",
            hashes=Hashes(
                feasibility_sha256=feasibility_sha,
            ),
            decision=RunDecision(
                risk_level=risk_level,
                score=score * 100,  # Convert 0-1 to 0-100
                warnings=[],
            ),
            request_summary={"attachment_ids": list(attachment_sha_map.keys())},
            meta={
                "engine_version": ENGINE_VERSION,
                "operator_notes": req.operator_notes,
            },
        )

    persist_run(artifact)

    # Return response (200 for both ALLOW and BLOCK)
    return BindArtStudioCandidateResponse(
        artifact_id=artifact_id,
        decision=decision,
        feasibility_score=score,
        risk_level=risk_level,
        feasibility_sha256=feasibility_sha,
        attachment_sha256_map=attachment_sha_map,
    )


# =============================================================================
# Advisory Blob Browser Endpoints (Run-Scoped)
# =============================================================================

from .advisory_blob_schemas import AdvisoryBlobListResponse, SvgPreviewStatusResponse
from .advisory_blob_service import (
    list_advisory_blobs,
    download_advisory_blob,
    preview_svg,
    check_svg_preview_status,
    download_all_zip,
)


@router.get("/{run_id}/advisory/blobs", response_model=AdvisoryBlobListResponse)
def list_run_advisory_blobs(run_id: str):
    """
    List all advisory blobs linked to this run.
    Source of truth: run.advisory_inputs[*].advisory_id
    """
    items = list_advisory_blobs(run_id)
    return AdvisoryBlobListResponse(run_id=run_id, count=len(items), items=items)


@router.get("/{run_id}/advisory/blobs/{sha256}/download")
def download_run_advisory_blob(run_id: str, sha256: str):
    """
    Download an advisory blob by sha256.
    Only allowed if sha256 is linked to this run's advisory_inputs.
    """
    return download_advisory_blob(run_id, sha256)


@router.get("/{run_id}/advisory/blobs/{sha256}/preview/svg")
def preview_run_advisory_svg(run_id: str, sha256: str):
    """
    Inline SVG preview (run-authorized).
    Applies safety gate (blocks script/foreignObject/image).
    """
    return preview_svg(run_id, sha256)


@router.get(
    "/{run_id}/advisory/blobs/{sha256}/preview/status",
    response_model=SvgPreviewStatusResponse,
)
def check_run_advisory_svg_status(run_id: str, sha256: str):
    """
    Check if SVG preview is available and safe.
    Returns status response with reason if blocked, plus recommended action.
    Useful for UI to show friendly message instead of error.
    """
    return check_svg_preview_status(run_id, sha256)


@router.get("/{run_id}/advisory/blobs/download-all.zip")
def download_all_run_advisory_blobs_zip(run_id: str, background_tasks: BackgroundTasks):
    """
    Download all advisory blobs linked to this run as a zip.
    """
    return download_all_zip(run_id, background_tasks)


# =============================================================================
# H3.4: Cursor-based Pagination Endpoint
# =============================================================================

from .store import query_recent


@router.get("/query/recent", summary="Query runs with cursor pagination")
def query_runs_cursor_endpoint(
    limit: int = Query(50, ge=1, le=500, description="Max results per page"),
    cursor: Optional[str] = Query(
        None, description="Pagination cursor (format: timestamp|run_id)"
    ),
    mode: Optional[str] = Query(None, description="Filter by mode"),
    tool_id: Optional[str] = Query(None, description="Filter by tool_id"),
    status: Optional[str] = Query(
        None, description="Filter by status (OK, BLOCKED, ERROR)"
    ),
    risk_level: Optional[str] = Query(None, description="Filter by risk level"),
    source: Optional[str] = Query(None, description="Filter by source"),
):
    """
    Query runs with cursor-based pagination.

    Cursor pagination is more efficient than offset for large datasets
    and avoids page drift when new items are added.

    GET /api/rmos/runs/query/recent?limit=50&mode=art_studio

    Response:
    ```json
    {
        "items": [...],
        "next_cursor": "2025-12-23T10:00:00Z|run_abc123"
    }
    ```

    Use `next_cursor` from the response as the `cursor` param for the next page.
    When `next_cursor` is null, you've reached the end.
    """
    return query_recent(
        limit=limit,
        cursor=cursor,
        mode=mode,
        tool_id=tool_id,
        status=status,
        risk_level=risk_level,
        source=source,
    )


# =============================================================================
# H3.5/H3.6: DELETE Endpoint with Policy Enforcement
# =============================================================================

from fastapi import Header
from .store import delete_run, DeleteRateLimitError
from .delete_policy import (
    get_delete_policy,
    is_admin_request,
    check_delete_allowed,
    resolve_effective_mode,
)
from .delete_audit import append_delete_audit, build_delete_audit_event


@router.delete("/{run_id}", summary="Delete a run artifact")
def delete_run_endpoint(
    request: Request,
    run_id: str,
    mode: Optional[str] = Query(
        None,
        description="Delete mode: 'soft' (tombstone, default) or 'hard' (remove files)",
    ),
    reason: str = Query(
        ...,
        min_length=6,
        max_length=500,
        description="Audit reason for deletion (required)",
    ),
    actor: Optional[str] = Query(None, description="Actor performing deletion"),
    cascade: bool = Query(True, description="Also delete advisory links"),
    x_rmos_admin: Optional[str] = Header(None, alias="X-RMOS-Admin"),
):
    """
    Delete a run artifact with policy enforcement and audit logging.

    H3.5: Supports soft (tombstone) and hard (file removal) delete modes.
    H3.6: Policy-enforced - hard delete requires admin header + env allow.
    H3.6.1: Rate-limited and requires audit reason.
    H3.6.2: All attempts logged to append-only audit log.

    DELETE /api/rmos/runs/{run_id}?reason=cleanup%20test%20data

    Soft delete (default):
    - Writes tombstone to index
    - Artifact file preserved for audit
    - Run excluded from listings

    Hard delete (requires admin):
    - Removes index entry
    - Removes artifact file
    - Optionally removes advisory links (cascade=true)

    Returns 200 on success, 400/403/404/429 on error.
    """
    # Extract request context
    req_id = getattr(request.state, "request_id", None) or request.headers.get(
        "x-request-id"
    )
    client_ip = request.client.host if request.client else None
    effective_actor = actor.strip() if actor else None

    # Resolve policy and mode
    policy = get_delete_policy()
    effective_mode = resolve_effective_mode(mode, policy)
    is_admin = is_admin_request(x_rmos_admin)

    # Check policy
    allowed, deny_reason = check_delete_allowed(effective_mode, is_admin, policy)

    if not allowed:
        # Audit the forbidden attempt
        try:
            from .store import _get_default_store

            store = _get_default_store()
            event = build_delete_audit_event(
                run_id=run_id,
                mode=effective_mode,
                reason=reason,
                actor=effective_actor,
                request_id=req_id,
                index_updated=False,
                artifact_deleted=False,
                attachments_deleted=0,
                allowed_by_policy=False,
                allowed_by_rate_limit=True,
                client_ip=client_ip,
                outcome="forbidden",
                errors=deny_reason,
            )
            append_delete_audit(store_root=store.root, event=event)
        except Exception:
            pass  # Audit must never block
        raise HTTPException(status_code=403, detail=deny_reason)

    # Attempt delete
    try:
        result = delete_run(
            run_id,
            mode=effective_mode,
            reason=reason,
            actor=effective_actor,
            request_id=req_id,
            cascade=cascade,
        )

        return {
            "run_id": run_id,
            "mode": effective_mode,
            "deleted": result["deleted"],
            "tombstoned": result.get("index_updated") and effective_mode == "soft",
            "artifact_deleted": result.get("artifact_deleted", False),
            "advisory_links_deleted": result.get("advisory_links_deleted", 0),
            "reason": reason,
            "request_id": req_id,
        }

    except KeyError:
        # Run not found - already audited by delete_run
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    except DeleteRateLimitError as e:
        # Rate limited - already audited by delete_run
        raise HTTPException(status_code=429, detail=str(e))

    except ValueError as e:
        # Invalid input (e.g., empty reason) - shouldn't happen due to Query validation
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# Variant Review, Rating, and Promotion (Product Bundle)
# =============================================================================

from .schemas_variant_review import (
    AdvisoryVariantListResponse,
    AdvisoryVariantReviewRequest,
    AdvisoryVariantReviewRecord,
    PromoteVariantRequest,
    PromoteVariantResponse,
    RejectVariantRequest,
    RejectVariantResponse,
    UnrejectVariantResponse,
)
from .variant_review_service import (
    list_variants,
    save_review,
    promote_variant,
    reject_variant,
    unreject_variant,
)


@router.get("/{run_id}/advisory/variants", response_model=AdvisoryVariantListResponse)
def get_advisory_variants(run_id: str):
    """
    List all advisory variants attached to a run with review status.

    Returns variant info including:
    - advisory_id (SHA256)
    - mime type
    - filename
    - size_bytes
    - preview_blocked (true if SVG has unsafe content)
    - rating (if reviewed)
    - notes (if reviewed)
    - promoted status

    Use this to populate the VariantReviewPanel UI.
    """
    return list_variants(run_id)


@router.post(
    "/{run_id}/advisory/{advisory_id}/review",
    response_model=AdvisoryVariantReviewRecord,
)
def post_advisory_variant_review(
    run_id: str,
    advisory_id: str,
    payload: AdvisoryVariantReviewRequest,
    request: Request,
):
    """
    Save rating and notes for an advisory variant.

    This stores the review in RunArtifact.advisory_reviews.
    The advisory blob itself is never mutated.

    Rating: 1-5 stars (optional)
    Notes: Free-form review text (optional, max 4000 chars)

    User identity extracted from x-user-id header.
    """
    return save_review(run_id, advisory_id, payload, request)


@router.post(
    "/{run_id}/advisory/{advisory_id}/promote", response_model=PromoteVariantResponse
)
def post_promote_advisory_variant(
    run_id: str,
    advisory_id: str,
    payload: PromoteVariantRequest,
    principal: Principal = Depends(require_roles("admin", "operator", "engineer")),
):
    """
    Promote an advisory variant to a manufacturing candidate.

    Requires authenticated user with role: admin, operator, or engineer.
    Auth via JWT Bearer token, session cookie, or x-user-role header (dev mode).

    SVG bind-time policy:
    - BLOCK: script, foreignObject, image elements
    - ALLOW + YELLOW: text elements (requires outline conversion)
    - ALLOW + GREEN: path/geometry only

    Non-SVG files get ALLOW + YELLOW with lower score.

    Promotion is recorded in manufacturing_candidates list on the run.

    Returns 401 if not authenticated.
    Returns 403 if role insufficient.
    Returns 409 if already promoted.
    """
    return promote_variant(run_id, advisory_id, payload, principal)


@router.post(
    "/{run_id}/advisory/{advisory_id}/reject", response_model=RejectVariantResponse
)
def post_reject_advisory_variant(
    run_id: str,
    advisory_id: str,
    payload: RejectVariantRequest,
    principal: Principal = Depends(require_roles("admin", "operator")),
):
    """
    Reject an advisory variant.

    Requires authenticated user with role: admin or operator.

    Rejection stores metadata on the run (does not delete the advisory blob).
    Use unreject to clear rejection status.

    Reason codes:
    - GEOMETRY_UNSAFE: Geometry has safety concerns
    - TEXT_REQUIRES_OUTLINE: Contains text that needs outline conversion
    - AESTHETIC: Aesthetic/design concerns
    - DUPLICATE: Duplicate of another variant
    - OTHER: Other reason (use reason_detail)

    Returns 401 if not authenticated.
    Returns 403 if role insufficient.
    Returns 404 if run or advisory not found.
    """
    return reject_variant(run_id, advisory_id, payload, principal)


@router.post(
    "/{run_id}/advisory/{advisory_id}/unreject", response_model=UnrejectVariantResponse
)
def post_unreject_advisory_variant(
    run_id: str,
    advisory_id: str,
    principal: Principal = Depends(require_roles("admin", "operator")),
):
    """
    Clear rejection status for an advisory variant.

    Requires authenticated user with role: admin or operator.

    Removes rejection metadata from the run artifact.
    Returns cleared=true if rejection was removed, false if not rejected.

    Returns 401 if not authenticated.
    Returns 403 if role insufficient.
    Returns 404 if run or advisory not found.
    """
    return unreject_variant(run_id, advisory_id, principal)


# =============================================================================
# Bulk Promote (Product Bundle)
# =============================================================================

from .schemas_variant_review import (
    BulkPromoteRequest,
    BulkPromoteResponse,
)
from .variant_review_service import bulk_promote_variants


@router.post("/{run_id}/advisory/bulk-promote", response_model=BulkPromoteResponse)
def post_bulk_promote_advisory_variants(
    run_id: str,
    payload: BulkPromoteRequest,
    principal: Principal = Depends(require_roles("admin", "operator", "engineer")),
):
    """
    Bulk-promote multiple advisory variants to manufacturing candidates.

    Requires authenticated user with role: admin, operator, or engineer.
    Auth via JWT Bearer token, session cookie, or x-user-role header (dev mode).

    Each variant is evaluated against the SVG bind-time policy:
    - BLOCK: script, foreignObject, image elements
    - ALLOW + YELLOW: text elements (requires outline conversion)
    - ALLOW + GREEN: path/geometry only

    Processing continues on individual failures to maximize throughput.

    Returns aggregate statistics:
    - total: Number of advisory IDs submitted
    - succeeded: Number successfully promoted
    - failed: Number that failed (not found, already promoted, etc.)
    - blocked: Number blocked by bind-time policy

    Also returns per-item results with decision, risk_level, and any error.
    """
    return bulk_promote_variants(run_id, payload, principal)


# =============================================================================
# Variant Rejection (Product Bundle)
# =============================================================================

from .schemas_advisory_reject import (
    RejectVariantRequest,
    AdvisoryVariantRejectionRecord,
)
from .advisory_variant_state import write_rejection, clear_rejection


@router.post(
    "/{run_id}/advisory/{advisory_id}/reject",
    response_model=AdvisoryVariantRejectionRecord,
    summary="Reject an advisory variant with a reason code.",
)
def post_reject_advisory_variant(
    run_id: str,
    advisory_id: str,
    payload: RejectVariantRequest,
):
    """
    Reject an advisory variant with a structured reason code.

    This creates an explicit rejection record separate from the immutable
    RunArtifact. Rejection records are stored in a simple per-run directory
    structure for easy debugging and audit.

    Reason codes (tight vocabulary):
    - GEOMETRY_UNSAFE: Contains unsafe geometry for CNC
    - TEXT_REQUIRES_OUTLINE: Text elements need outline conversion
    - AESTHETIC: Rejected for aesthetic reasons
    - DUPLICATE: Duplicate of another variant
    - OTHER: Other reason (use reason_detail for specifics)

    Optional fields:
    - reason_detail: Short clarification (max 500 chars)
    - operator_note: Longer note for audit trail (max 2000 chars)

    Rejecting an already-rejected variant overwrites the previous rejection.
    """
    return write_rejection(run_id=run_id, advisory_id=advisory_id, req=payload)


@router.post(
    "/{run_id}/advisory/{advisory_id}/unreject",
    response_model=dict,
    summary="Undo rejection of an advisory variant (clear rejection record).",
)
def post_unreject_advisory_variant(run_id: str, advisory_id: str):
    """
    Clear/undo a rejection for an advisory variant.

    This removes the rejection record, returning the variant to its
    previous status (NEW or REVIEWED depending on whether it has ratings/notes).

    Returns:
    - run_id: The run ID
    - advisory_id: The advisory ID
    - cleared: True if a rejection was cleared, False if none existed
    """
    existed = clear_rejection(run_id=run_id, advisory_id=advisory_id)
    return {"run_id": run_id, "advisory_id": advisory_id, "cleared": existed}


# =============================================================================
# Bulk Promote (Product Bundle)
# =============================================================================

from .schemas_variant_review import (
    BulkPromoteRequest,
    BulkPromoteResponse,
)
from .variant_review_service import bulk_promote_variants


@router.post("/{run_id}/advisory/bulk-promote", response_model=BulkPromoteResponse)
def post_bulk_promote_advisory_variants(
    run_id: str,
    payload: BulkPromoteRequest,
    principal: Principal = Depends(require_roles("admin", "operator", "engineer")),
):
    """
    Bulk-promote multiple advisory variants to manufacturing candidates.

    Requires authenticated user with role: admin, operator, or engineer.
    Auth via JWT Bearer token, session cookie, or x-user-role header (dev mode).

    Each variant is evaluated against the SVG bind-time policy:
    - BLOCK: script, foreignObject, image elements
    - ALLOW + YELLOW: text elements (requires outline conversion)
    - ALLOW + GREEN: path/geometry only

    Processing continues on individual failures to maximize throughput.

    Returns aggregate statistics:
    - total: Number of advisory IDs submitted
    - succeeded: Number successfully promoted
    - failed: Number that failed (not found, already promoted, etc.)
    - blocked: Number blocked by bind-time policy

    Also returns per-item results with decision, risk_level, and any error.
    """
    return bulk_promote_variants(run_id, payload, principal)


# =============================================================================
# Variant Rejection (Product Bundle)
# =============================================================================

from .schemas_advisory_reject import (
    RejectVariantRequest,
    AdvisoryVariantRejectionRecord,
)
from .advisory_variant_state import write_rejection, clear_rejection


@router.post(
    "/{run_id}/advisory/{advisory_id}/reject",
    response_model=AdvisoryVariantRejectionRecord,
    summary="Reject an advisory variant with a reason code.",
)
def post_reject_advisory_variant(
    run_id: str,
    advisory_id: str,
    payload: RejectVariantRequest,
):
    """
    Reject an advisory variant with a structured reason code.

    This creates an explicit rejection record separate from the immutable
    RunArtifact. Rejection records are stored in a simple per-run directory
    structure for easy debugging and audit.

    Reason codes (tight vocabulary):
    - GEOMETRY_UNSAFE: Contains unsafe geometry for CNC
    - TEXT_REQUIRES_OUTLINE: Text elements need outline conversion
    - AESTHETIC: Rejected for aesthetic reasons
    - DUPLICATE: Duplicate of another variant
    - OTHER: Other reason (use reason_detail for specifics)

    Optional fields:
    - reason_detail: Short clarification (max 500 chars)
    - operator_note: Longer note for audit trail (max 2000 chars)

    Rejecting an already-rejected variant overwrites the previous rejection.
    """
    return write_rejection(run_id=run_id, advisory_id=advisory_id, req=payload)


@router.post(
    "/{run_id}/advisory/{advisory_id}/unreject",
    response_model=dict,
    summary="Undo rejection of an advisory variant (clear rejection record).",
)
def post_unreject_advisory_variant(run_id: str, advisory_id: str):
    """
    Clear/undo a rejection for an advisory variant.

    This removes the rejection record, returning the variant to its
    previous status (NEW or REVIEWED depending on whether it has ratings/notes).

    Returns:
    - run_id: The run ID
    - advisory_id: The advisory ID
    - cleared: True if a rejection was cleared, False if none existed
    """
    existed = clear_rejection(run_id=run_id, advisory_id=advisory_id)
    return {"run_id": run_id, "advisory_id": advisory_id, "cleared": existed}


# =============================================================================
# Manufacturing Candidate Queue (Product Bundle)
# =============================================================================

from .schemas_manufacturing_ops import (
    CandidateListResponse,
    CandidateDecisionRequest,
    CandidateDecisionResponse,
)
from .manufacturing_candidate_service import (
    list_candidates,
    decide_candidate,
    download_candidate_zip,
)


@router.get("/{run_id}/manufacturing/candidates", response_model=CandidateListResponse)
def get_manufacturing_candidates(run_id: str):
    """
    List all manufacturing candidates for a run.

    Returns candidates with their status (PROPOSED, ACCEPTED, REJECTED).
    Candidates are sorted newest-first by updated_at_utc.
    """
    return list_candidates(run_id)


@router.post(
    "/{run_id}/manufacturing/candidates/{candidate_id}/decision",
    response_model=CandidateDecisionResponse,
)
def post_candidate_decision(
    run_id: str,
    candidate_id: str,
    payload: CandidateDecisionRequest,
    principal: Principal = Depends(require_roles("admin", "operator")),
):
    """
    Approve or reject a manufacturing candidate.

    Requires authenticated user with role: admin or operator.

    Decision: ACCEPT or REJECT
    Note: Optional decision note (max 2000 chars)

    Returns 401 if not authenticated.
    Returns 403 if role insufficient (requires admin/operator).
    Returns 404 if run or candidate not found.
    """
    return decide_candidate(run_id, candidate_id, payload, principal)


@router.get("/{run_id}/manufacturing/candidates/{candidate_id}/download-zip")
def get_candidate_zip(
    run_id: str,
    candidate_id: str,
    principal: Principal = Depends(
        require_roles("admin", "operator", "engineer", "viewer")
    ),
):
    """
    Download a ZIP containing the candidate's advisory blob and manifest.

    Product-facing export for manufacturing workflow.

    ZIP contents:
    - manifest.json: candidate metadata
    - blob/<advisory_id>.<ext>: the advisory blob

    Requires any authenticated role (admin/operator/engineer/viewer).

    Returns 401 if not authenticated.
    Returns 404 if run, candidate, or blob not found.
    """
    return download_candidate_zip(run_id, candidate_id)
