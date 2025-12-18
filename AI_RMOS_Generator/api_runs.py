"""
RMOS Runs v2 API Router

REST endpoints for run artifact operations.
Per: docs/governance/RUN_ARTIFACT_PERSISTENCE_CONTRACT_v1.md

GOVERNANCE:
- NO PATCH endpoints (artifacts are immutable)
- Advisory attachment via separate link files
- Policy B: Auto-approve GREEN explanations only
"""
from __future__ import annotations

import logging
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

from .schemas import RunArtifact, RunDecision, Hashes
from .store import RunStoreV2, ImmutabilityViolation, get_store
from .hashing import sha256_json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/rmos/runs", tags=["RMOS Runs v2"])


# ---------------------------------------------------------------------------
# Request/Response Models
# ---------------------------------------------------------------------------

class RunCreateRequest(BaseModel):
    """Request to create a new run artifact."""
    mode: str
    tool_id: str
    status: str  # OK, BLOCKED, ERROR

    request_summary: Dict[str, Any]
    feasibility: Dict[str, Any]

    # Decision fields (risk_level REQUIRED)
    risk_level: str
    score: Optional[float] = None
    block_reason: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)

    meta: Dict[str, Any] = Field(default_factory=dict)


class AttachAdvisoryRequest(BaseModel):
    """Request to attach an advisory reference."""
    advisory_id: str
    kind: str = "unknown"
    engine_id: Optional[str] = None
    engine_version: Optional[str] = None


class SetExplanationRequest(BaseModel):
    """Request to set explanation status."""
    status: str  # NONE, PENDING, READY, ERROR
    summary: Optional[str] = None


class RunListResponse(BaseModel):
    """Response for run listing."""
    items: List[RunArtifact]
    count: int
    total: Optional[int] = None


class DiffResponse(BaseModel):
    """Response for run diff."""
    severity: str
    run_a: str
    run_b: str
    differences: List[Dict[str, Any]]
    difference_count: int


# ---------------------------------------------------------------------------
# CREATE (POST) - Write-once
# ---------------------------------------------------------------------------

@router.post("", response_model=RunArtifact, status_code=201)
def create_run(req: RunCreateRequest, request: Request) -> RunArtifact:
    """
    Create a new immutable run artifact.

    GOVERNANCE:
    - Required fields enforced by Pydantic
    - feasibility_sha256 computed from feasibility payload
    - Write-once (cannot be modified after creation)
    """
    run_id = f"run_{uuid.uuid4().hex[:12]}"
    req_id = getattr(request.state, "request_id", None) or request.headers.get("x-request-id")

    # Compute REQUIRED hash
    feasibility_hash = sha256_json(req.feasibility)

    decision = RunDecision(
        risk_level=req.risk_level,
        score=req.score,
        block_reason=req.block_reason,
        warnings=req.warnings,
    )

    hashes = Hashes(feasibility_sha256=feasibility_hash)

    artifact = RunArtifact(
        run_id=run_id,
        mode=req.mode,
        tool_id=req.tool_id,
        status=req.status,
        request_summary=req.request_summary,
        feasibility=req.feasibility,
        decision=decision,
        hashes=hashes,
        meta={**req.meta, **({"request_id": req_id} if req_id else {})},
    )

    store = get_store()
    try:
        store.put(artifact)
    except ImmutabilityViolation as e:
        raise HTTPException(status_code=409, detail={"error": "ARTIFACT_EXISTS", "message": str(e)})

    logger.info("run.created", extra={"run_id": run_id, "status": req.status, "risk_level": req.risk_level})
    return artifact


# ---------------------------------------------------------------------------
# READ (GET)
# ---------------------------------------------------------------------------

@router.get("", response_model=RunListResponse)
def list_runs(
    limit: int = Query(default=50, ge=1, le=200),
    status: Optional[str] = Query(default=None),
    mode: Optional[str] = Query(default=None),
    tool_id: Optional[str] = Query(default=None),
    risk_level: Optional[str] = Query(default=None),
) -> RunListResponse:
    """List run artifacts with optional filtering."""
    store = get_store()
    runs = store.list_filtered(
        limit=limit,
        status=status,
        mode=mode,
        tool_id=tool_id,
        risk_level=risk_level,
    )
    total = store.count()
    return RunListResponse(items=runs, count=len(runs), total=total)


@router.get("/{run_id}", response_model=RunArtifact)
def get_run(run_id: str) -> RunArtifact:
    """Get a run artifact by ID."""
    store = get_store()
    run = store.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail={"error": "RUN_NOT_FOUND", "run_id": run_id})
    return run


# ---------------------------------------------------------------------------
# DIFF (GET)
# ---------------------------------------------------------------------------

@router.get("/diff", response_model=DiffResponse)
def diff_runs(
    a: str = Query(..., description="First run ID"),
    b: str = Query(..., description="Second run ID"),
) -> DiffResponse:
    """Compare two run artifacts."""
    from .diff import diff_runs as do_diff

    store = get_store()
    run_a = store.get(a)
    run_b = store.get(b)

    if run_a is None:
        raise HTTPException(status_code=404, detail={"error": "RUN_NOT_FOUND", "run_id": a})
    if run_b is None:
        raise HTTPException(status_code=404, detail={"error": "RUN_NOT_FOUND", "run_id": b})

    result = do_diff(run_a, run_b)
    return DiffResponse(**result)


# ---------------------------------------------------------------------------
# ADVISORY INTEGRATION (append-only, preserves immutability)
# ---------------------------------------------------------------------------

@router.post("/{run_id}/attach-advisory", response_model=RunArtifact)
def attach_advisory(run_id: str, req: AttachAdvisoryRequest, request: Request) -> RunArtifact:
    """
    Attach an advisory reference to a run.

    GOVERNANCE:
    - Creates separate link file (preserves artifact immutability)
    - Idempotent (duplicate attachments ignored)
    """
    store = get_store()
    req_id = getattr(request.state, "request_id", None) or request.headers.get("x-request-id")

    run = store.attach_advisory(
        run_id=run_id,
        advisory_id=req.advisory_id,
        kind=req.kind,
        engine_id=req.engine_id,
        engine_version=req.engine_version,
        request_id=req_id,
    )

    if run is None:
        raise HTTPException(status_code=404, detail={"error": "RUN_NOT_FOUND", "run_id": run_id})

    logger.info("advisory.attached", extra={"run_id": run_id, "advisory_id": req.advisory_id})
    return run


@router.get("/{run_id}/advisories")
def list_advisories(run_id: str) -> Dict[str, Any]:
    """List all advisory references attached to a run."""
    store = get_store()
    run = store.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail={"error": "RUN_NOT_FOUND", "run_id": run_id})

    return {
        "run_id": run_id,
        "advisory_inputs": [ref.model_dump(mode="json") for ref in run.advisory_inputs],
        "count": len(run.advisory_inputs),
        "explanation_status": run.explanation_status,
        "explanation_summary": run.explanation_summary,
    }


@router.post("/{run_id}/explanation", response_model=RunArtifact)
def set_explanation(run_id: str, req: SetExplanationRequest) -> RunArtifact:
    """
    Set explanation status for a run.

    GOVERNANCE:
    - Stored in separate file (preserves artifact immutability)
    """
    store = get_store()
    run = store.set_explanation(run_id, req.status, req.summary)

    if run is None:
        raise HTTPException(status_code=404, detail={"error": "RUN_NOT_FOUND", "run_id": run_id})

    logger.info("explanation.set", extra={"run_id": run_id, "status": req.status})
    return run


# ---------------------------------------------------------------------------
# ATTACHMENTS
# ---------------------------------------------------------------------------

@router.get("/{run_id}/attachments")
def list_attachments(run_id: str) -> Dict[str, Any]:
    """List file attachments for a run."""
    store = get_store()
    run = store.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail={"error": "RUN_NOT_FOUND", "run_id": run_id})

    attachments = run.attachments or []
    return {
        "run_id": run_id,
        "attachments": [att.model_dump(mode="json") for att in attachments],
        "count": len(attachments),
    }


@router.get("/{run_id}/attachments/{sha256}")
def get_attachment(run_id: str, sha256: str) -> Dict[str, Any]:
    """Get attachment metadata and download path."""
    from .attachments import get_attachment_path

    store = get_store()
    run = store.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail={"error": "RUN_NOT_FOUND", "run_id": run_id})

    attachments = run.attachments or []
    att = next((a for a in attachments if a.sha256 == sha256), None)
    if att is None:
        raise HTTPException(status_code=404, detail={"error": "ATTACHMENT_NOT_FOUND", "sha256": sha256})

    path = get_attachment_path(sha256)
    return {
        "run_id": run_id,
        "attachment": att.model_dump(mode="json"),
        "path": path,
        "exists": path is not None,
    }


@router.get("/{run_id}/attachments/verify")
def verify_attachments(run_id: str) -> Dict[str, Any]:
    """Verify integrity of all attachments."""
    from .attachments import verify_attachment

    store = get_store()
    run = store.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail={"error": "RUN_NOT_FOUND", "run_id": run_id})

    attachments = run.attachments or []
    results = []
    all_valid = True

    for att in attachments:
        valid = verify_attachment(att.sha256)
        results.append({
            "sha256": att.sha256,
            "filename": att.filename,
            "valid": valid,
        })
        if not valid:
            all_valid = False

    return {
        "run_id": run_id,
        "all_valid": all_valid,
        "results": results,
    }


# ---------------------------------------------------------------------------
# NO PATCH ENDPOINT
# ---------------------------------------------------------------------------
# GOVERNANCE: Run artifacts are immutable.
# patch_run_meta() has been removed per governance contract.
# Use attach_advisory() or set_explanation() for additional context.
