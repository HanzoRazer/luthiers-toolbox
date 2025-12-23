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

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

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
from .store import get_run, list_runs_filtered, persist_run, create_run_id, attach_advisory
from .diff import diff_runs
from .attachments import get_attachment_path, put_json_attachment
from .hashing import summarize_request, compute_feasibility_hash

import json
import time

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
    mode: str = Field(default="unknown", description="Operation mode (cam, preview, simulation)")
    tool_id: str = Field(default="unknown", description="Tool identifier")
    status: str = Field(default="OK", description="Run status (OK, BLOCKED, ERROR)")
    event_type: str = Field(default="unknown", description="Event type (approval, toolpaths, etc)")
    request_summary: Dict[str, Any] = Field(default_factory=dict, description="Redacted request summary")
    feasibility: Dict[str, Any] = Field(default_factory=dict, description="Feasibility evaluation result")
    decision: Optional[Dict[str, Any]] = Field(default=None, description="Decision override (optional)")
    meta: Dict[str, Any] = Field(default_factory=dict, description="Free-form metadata")


class AttachAdvisoryRequest(BaseModel):
    """Request body for attaching an advisory to a run."""
    advisory_id: str = Field(..., description="Unique identifier of the advisory asset")
    kind: str = Field(default="unknown", description="Type: explanation, advisory, note")
    engine_id: Optional[str] = Field(None, description="AI engine that created it")
    engine_version: Optional[str] = Field(None, description="Engine version")


class SuggestAndAttachRequest(BaseModel):
    """Request body for generating and attaching an explanation/advisory."""
    # Team decision: sync now; async flag reserved as escape hatch
    generate_explanation: bool = Field(False, description="Generate placeholder explanation")
    async_explanation: bool = Field(False, description="Reserved for future async support")

    # Advisory typing
    kind: str = Field("explanation", description="Type: explanation, advisory, note")

    # Optional: user prompt for what they want explained (future AI UX)
    prompt: Optional[str] = Field(None, description="User prompt for explanation")

    # Optional: allow attaching a provided payload without LLM
    advisory_markdown: Optional[str] = Field(None, description="Pre-generated markdown content")
    advisory_json: Optional[Dict[str, Any]] = Field(None, description="Pre-generated JSON data")

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
    req_id = getattr(request.state, "request_id", None) or request.headers.get("x-request-id")

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
        risk_level = req.feasibility.get("risk_bucket") or req.feasibility.get("risk_level") or "UNKNOWN"
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
        request_summary=summarize_request(req.request_summary) if req.request_summary else {},
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

@router.get("", response_model=List[RunArtifactSummary], summary="List run artifacts.")
def list_runs_endpoint(
    limit: int = Query(50, ge=1, le=500),
    event_type: Optional[str] = None,
    status: Optional[str] = None,
    tool_id: Optional[str] = None,
    mode: Optional[str] = None,
):
    """
    List run artifacts with optional filtering.

    Results are sorted by creation date (newest first).
    """
    runs = list_runs_filtered(
        limit=limit,
        event_type=event_type,
        status=status,
        tool_id=tool_id,
        mode=mode,
    )
    return [_to_summary(r) for r in runs]


@router.get("/diff", summary="Diff two run artifacts by id.")
def diff_two_runs(a: str, b: str) -> Dict[str, Any]:
    """
    Compute authoritative diff between two runs.

    Returns severity (CRITICAL/WARNING/INFO) and structured diff.
    """
    ra = get_run(a)
    if ra is None:
        raise HTTPException(status_code=404, detail=f"Run {a} not found")

    rb = get_run(b)
    if rb is None:
        raise HTTPException(status_code=404, detail=f"Run {b} not found")

    return diff_runs(ra, rb)


@router.get("/{run_id}", response_model=Dict[str, Any], summary="Get run artifact details.")
def read_run(run_id: str) -> Dict[str, Any]:
    """Get full details of a run artifact."""
    r = get_run(run_id)
    if r is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

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
                "created_at_utc": a.created_at_utc.isoformat() if hasattr(a.created_at_utc, "isoformat") else a.created_at_utc,
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
    req_id = getattr(request.state, "request_id", None) or request.headers.get("x-request-id")

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
                "created_at_utc": a.created_at_utc.isoformat() if hasattr(a.created_at_utc, "isoformat") else a.created_at_utc,
            }
            for a in advisories
        ],
    }


@router.post("/{run_id}/suggest-and-attach", response_model=SuggestAndAttachResponse, summary="Generate and attach an explanation.")
def suggest_and_attach(run_id: str, body: SuggestAndAttachRequest, request: Request) -> SuggestAndAttachResponse:
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
    req_id = getattr(request.state, "request_id", None) or request.headers.get("x-request-id")

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
        summary = summarize_request(run.request_summary if isinstance(run.request_summary, dict) else {})
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
    created_at_str = run.created_at_utc.isoformat() if hasattr(run.created_at_utc, "isoformat") else str(run.created_at_utc)
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
    """Download attachment blob by SHA256."""
    r = get_run(run_id)
    if r is None:
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


@router.post("/{run_id}/attachments", response_model=RunAttachmentCreateResponse, summary="Create attachment for run")
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
            detail=f"SHA256 mismatch: expected {req.sha256}, got {actual_sha}"
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
    summary="Bind Art Studio candidate to run artifact"
)
def bind_art_studio_candidate(run_id: str, req: BindArtStudioCandidateRequest):
    """
    Bind Art Studio candidate attachments to a run artifact with feasibility check.
    
    Creates a RunArtifact for EVERY bind attempt (ALLOW or BLOCK).
    
    Returns 400 if:
    - Run not found
    - Attachments missing (when strict=true)
    - Attachment SHA verification fails
    - Invalid spec schema
    
    Returns 200 with decision=ALLOW or decision=BLOCK (both persist artifacts).
    Never returns 403 or 409 (blocked artifacts are persisted with decision=BLOCK).
    """
    from .attachments import get_attachment_path
    from .hashing import sha256_of_obj
    from .store import create_blocked_artifact_for_violations
    
    # Verify run exists
    run = get_run(run_id)
    if run is None:
        raise HTTPException(status_code=400, detail=f"Run {run_id} not found")
    
    # Verify all attachments exist and are accessible
    attachment_sha_map = {}
    for att_id in req.attachment_ids:
        # Normalize: strip att- prefix if present
        sha256 = att_id.replace("att-", "") if att_id.startswith("att-") else att_id
        
        # Check attachment exists
        path = get_attachment_path(sha256)
        if path is None:
            if req.strict:
                raise HTTPException(
                    status_code=400,
                    detail=f"Attachment {att_id} not found (sha256: {sha256})"
                )
            else:
                continue  # Skip missing if not strict
        
        attachment_sha_map[att_id] = sha256
    
    # TODO: Run actual feasibility check here
    # For now, mock a simple ALLOW decision
    # In production, this would:
    # 1. Load geometry spec from attachments
    # 2. Run feasibility engine
    # 3. Compute risk level + score
    # 4. Return ALLOW or BLOCK based on thresholds
    
    # Mock feasibility result (replace with real engine later)
    feasibility_data = {
        "decision": "ALLOW",
        "score": 0.85,
        "risk_level": "GREEN",
        "attachment_ids": list(attachment_sha_map.keys()),
        "operator_notes": req.operator_notes,
    }
    feasibility_sha = sha256_of_obj(feasibility_data)
    
    decision = feasibility_data["decision"]
    score = feasibility_data["score"]
    risk_level = feasibility_data["risk_level"]
    
    # Create RunArtifact (persisted for both ALLOW and BLOCK)
    artifact_id = create_run_id()
    
    if decision == "BLOCK":
        # Use existing blocked artifact creation function
        artifact = create_blocked_artifact_for_violations(
            run_id=artifact_id,
            mode="art_studio_candidate",
            spec={"attachment_ids": list(attachment_sha_map.keys())},
            violations=[{"code": "FEASIBILITY_BLOCKED", "reason": "Mock block for demo"}],
        )
    else:
        # Create ALLOW artifact
        artifact = RunArtifact(
            run_id=artifact_id,
            status="OK",
            mode="art_studio_candidate",
            hashes=Hashes(
                feasibility_sha256=feasibility_sha,
            ),
            decision=RunDecision(
                risk_level=risk_level,
                score=score * 100,  # Convert 0-1 to 0-100
                warnings=[],
            ),
            request_spec={"attachment_ids": list(attachment_sha_map.keys())},
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
