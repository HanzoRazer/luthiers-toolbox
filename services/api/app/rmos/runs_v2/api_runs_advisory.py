"""
RMOS Runs v2 — Advisory sub-router.

Endpoints:
- POST /{run_id}/attach-advisory
- GET  /{run_id}/advisories
- POST /{run_id}/suggest-and-attach
"""

from __future__ import annotations

import json
import time
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from .schemas import AdvisoryInputRef
from .store import get_run, attach_advisory
from .attachments import put_json_attachment
from .hashing import summarize_request

router = APIRouter()


# ── Request / Response Models ────────────────────────────────────────────────


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

    generate_explanation: bool = Field(
        False, description="Generate placeholder explanation"
    )
    async_explanation: bool = Field(
        False, description="Reserved for future async support"
    )
    kind: str = Field("explanation", description="Type: explanation, advisory, note")
    prompt: Optional[str] = Field(None, description="User prompt for explanation")
    advisory_markdown: Optional[str] = Field(
        None, description="Pre-generated markdown content"
    )
    advisory_json: Optional[Dict[str, Any]] = Field(
        None, description="Pre-generated JSON data"
    )
    engine_id: Optional[str] = Field(None, description="AI engine that created it")
    engine_version: Optional[str] = Field(None, description="Engine version")


class SuggestAndAttachResponse(BaseModel):
    """Response from suggest-and-attach endpoint."""

    run_id: str
    advisory_sha256: str
    explanation_status: str
    explanation_summary: Optional[str] = None
    compute_ms: float


# ── Endpoints ────────────────────────────────────────────────────────────────


@router.post("/{run_id}/attach-advisory", summary="Attach an advisory to a run.")
def attach_advisory_endpoint(run_id: str, req: AttachAdvisoryRequest, request: Request):
    """
    Attach an advisory reference to a run artifact.

    APPEND-ONLY: This creates a separate link file, preserving
    the original artifact's immutability.
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

    1. Loads an existing RunArtifact
    2. Optionally generates an explanation (sync now; async reserved)
    3. Stores the canonical payload as a content-addressed attachment
    4. Appends an AdvisoryInputRef to the run (append-only)
    5. Sets inline explanation_status + summary (preview only)
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
