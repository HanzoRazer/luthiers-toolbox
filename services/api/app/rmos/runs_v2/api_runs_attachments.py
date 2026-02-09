"""
RMOS Runs v2 — Attachment sub-router.

Endpoints:
- GET  /{run_id}/attachments
- GET  /{run_id}/attachments/{sha256}
- GET  /{run_id}/attachments/verify
- POST /{run_id}/attachments
- POST /{run_id}/artifacts/bind-art-studio-candidate
"""

from __future__ import annotations

import binascii
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse

from .schemas import (
    RunArtifact,
    RunDecision,
    Hashes,
    RunAttachmentCreateRequest,
    RunAttachmentCreateResponse,
    BindArtStudioCandidateRequest,
    BindArtStudioCandidateResponse,
)
from .store import get_run, persist_run, create_run_id
from .attachments import get_attachment_path

router = APIRouter()


# ── Endpoints ────────────────────────────────────────────────────────────────


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
    path = get_attachment_path(sha256)
    if not path:
        raise HTTPException(
            status_code=404, detail="Attachment blob not found on disk."
        )

    r = get_run(run_id)
    if r is not None:
        atts = getattr(r, "attachments", None) or []
        meta = next((a for a in atts if a.sha256 == sha256), None)
        if meta is not None:
            return FileResponse(path, media_type=meta.mime, filename=meta.filename)

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

    Returns 400 if run not found, SHA256 mismatch, or invalid base64.
    Returns 200 with attachment metadata if successful.
    """
    import base64
    from .attachments import put_bytes_attachment
    from .hashing import sha256_of_bytes

    run = get_run(run_id)
    if run is None:
        raise HTTPException(status_code=400, detail=f"Run {run_id} not found")

    try:
        data = base64.b64decode(req.b64)
    except (binascii.Error, ValueError) as e:
        raise HTTPException(status_code=400, detail=f"Invalid base64 payload: {e}")

    actual_sha = sha256_of_bytes(data)
    if actual_sha != req.sha256:
        raise HTTPException(
            status_code=400,
            detail=f"SHA256 mismatch: expected {req.sha256}, got {actual_sha}",
        )

    attachment, _path = put_bytes_attachment(
        data=data,
        kind=req.kind,
        mime=req.content_type,
        filename=req.filename,
        ext="",
    )

    return RunAttachmentCreateResponse(
        attachment_id=attachment.sha256,
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
    Never returns 403 or 409 (blocked artifacts are persisted with decision=BLOCK).
    """
    from .bind_art_studio_service import bind_art_studio_candidate, ENGINE_VERSION

    run = get_run(run_id)
    if run is None:
        raise HTTPException(status_code=400, detail=f"Run {run_id} not found")

    req_id = getattr(request.state, "request_id", None) or request.headers.get(
        "x-request-id"
    )

    try:
        result = bind_art_studio_candidate(
            run_id=run_id,
            attachment_ids=req.attachment_ids,
            operator_notes=req.operator_notes,
            strict=req.strict,
            request_id=req_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    decision = result["decision"]
    risk_level = result["risk_level"]
    score = result["feasibility_score"]
    feasibility_sha = result["feasibility_sha256"]
    attachment_sha_map = result["attachment_sha256_map"]

    artifact_id = create_run_id()

    if decision == "BLOCK":
        artifact = RunArtifact(
            run_id=artifact_id,
            status="BLOCKED",
            mode="art_studio_candidate",
            tool_id="art_studio",
            hashes=Hashes(feasibility_sha256=feasibility_sha),
            decision=RunDecision(
                risk_level=risk_level,
                score=score * 100,
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
        artifact = RunArtifact(
            run_id=artifact_id,
            status="OK",
            mode="art_studio_candidate",
            tool_id="art_studio",
            hashes=Hashes(feasibility_sha256=feasibility_sha),
            decision=RunDecision(
                risk_level=risk_level,
                score=score * 100,
                warnings=[],
            ),
            request_summary={"attachment_ids": list(attachment_sha_map.keys())},
            meta={
                "engine_version": ENGINE_VERSION,
                "operator_notes": req.operator_notes,
            },
        )

    persist_run(artifact)

    return BindArtStudioCandidateResponse(
        artifact_id=artifact_id,
        decision=decision,
        feasibility_score=score,
        risk_level=risk_level,
        feasibility_sha256=feasibility_sha,
        attachment_sha256_map=attachment_sha_map,
    )
