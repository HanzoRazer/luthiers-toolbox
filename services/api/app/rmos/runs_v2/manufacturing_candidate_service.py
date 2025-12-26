# services/api/app/rmos/runs_v2/manufacturing_candidate_service.py
"""
Manufacturing Candidate Service.

Provides:
- List candidates for a run
- Approve/reject decisions
- ZIP export for manufacturing
"""

from __future__ import annotations

import io
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from fastapi import HTTPException
from fastapi.responses import StreamingResponse

from app.auth.principal import Principal
from .store import get_run, update_run
from .attachments import get_attachment_path, get_bytes_attachment
from .schemas_manufacturing_ops import (
    CandidateListResponse,
    CandidateListItem,
    CandidateDecisionRequest,
    CandidateDecisionResponse,
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_candidates(run: Any) -> list[Any]:
    """Get manufacturing candidates list from run."""
    return list(getattr(run, "manufacturing_candidates", None) or [])


def _get_attr(obj: Any, key: str, default: Any = None) -> Any:
    """Get attribute from object or dict."""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _set_attr(obj: Any, key: str, value: Any) -> None:
    """Set attribute on object or dict."""
    if isinstance(obj, dict):
        obj[key] = value
    else:
        setattr(obj, key, value)


def list_candidates(run_id: str) -> CandidateListResponse:
    """List all manufacturing candidates for a run."""
    run = get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    candidates = _get_candidates(run)

    items: list[CandidateListItem] = []
    for c in candidates:
        items.append(
            CandidateListItem(
                candidate_id=_get_attr(c, "candidate_id", ""),
                advisory_id=_get_attr(c, "advisory_id", ""),
                status=_get_attr(c, "status", "PROPOSED"),
                label=_get_attr(c, "label"),
                note=_get_attr(c, "note"),
                created_at_utc=_get_attr(c, "created_at_utc", ""),
                created_by=_get_attr(c, "created_by"),
                updated_at_utc=_get_attr(c, "updated_at_utc", ""),
                updated_by=_get_attr(c, "updated_by"),
            )
        )

    # Stable ordering: newest first by updated_at_utc, then by candidate_id
    items.sort(key=lambda x: (x.updated_at_utc or "", x.candidate_id), reverse=True)
    return CandidateListResponse(run_id=run_id, count=len(items), items=items)


def _find_candidate_or_404(run: Any, candidate_id: str) -> Any:
    """Find candidate by ID or raise 404."""
    for c in _get_candidates(run):
        if _get_attr(c, "candidate_id") == candidate_id:
            return c
    raise HTTPException(status_code=404, detail="Candidate not found")


def decide_candidate(
    run_id: str,
    candidate_id: str,
    payload: CandidateDecisionRequest,
    principal: Principal,
) -> CandidateDecisionResponse:
    """Approve or reject a manufacturing candidate."""
    run = get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    cand = _find_candidate_or_404(run, candidate_id)

    decision = payload.decision
    status = "ACCEPTED" if decision == "ACCEPT" else "REJECTED"

    now = _utc_now()
    _set_attr(cand, "status", status)
    if payload.note:
        _set_attr(cand, "note", payload.note)
    _set_attr(cand, "updated_at_utc", now)
    _set_attr(cand, "updated_by", principal.user_id)

    # Persist the updated candidates list
    run.manufacturing_candidates = _get_candidates(run)
    update_run(run)

    return CandidateDecisionResponse(
        run_id=run_id,
        candidate_id=candidate_id,
        advisory_id=_get_attr(cand, "advisory_id", ""),
        status=status,
        updated_at_utc=now,
        updated_by=principal.user_id,
    )


def _infer_file_info(blob_bytes: bytes) -> tuple[str, str]:
    """Infer filename extension and MIME type from blob content."""
    head = blob_bytes[:4096]
    if head.startswith(b"<svg") or b"<svg" in head:
        return ".svg", "image/svg+xml"
    if head.startswith(b"{") or head.startswith(b"["):
        return ".json", "application/json"
    if head.startswith(b"%PDF"):
        return ".pdf", "application/pdf"
    if head[:8] == b"\x89PNG\r\n\x1a\n":
        return ".png", "image/png"
    if head[:3] == b"\xff\xd8\xff":
        return ".jpg", "image/jpeg"
    return ".bin", "application/octet-stream"


def download_candidate_zip(run_id: str, candidate_id: str) -> StreamingResponse:
    """
    Create a ZIP containing the advisory blob and manifest.

    Product-facing export for operators/manufacturing.
    """
    run = get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    cand = _find_candidate_or_404(run, candidate_id)
    advisory_id = _get_attr(cand, "advisory_id", "")
    if not advisory_id:
        raise HTTPException(status_code=400, detail="Candidate missing advisory_id")

    blob_path = get_attachment_path(advisory_id)
    if not blob_path:
        raise HTTPException(status_code=404, detail="Advisory blob not found in CAS")

    blob_bytes = get_bytes_attachment(advisory_id)
    if blob_bytes is None:
        blob_bytes = Path(blob_path).read_bytes()

    ext, mime = _infer_file_info(blob_bytes)
    fname = f"{advisory_id}{ext}"

    manifest = {
        "run_id": run_id,
        "candidate_id": candidate_id,
        "advisory_id": advisory_id,
        "status": _get_attr(cand, "status", "PROPOSED"),
        "label": _get_attr(cand, "label"),
        "note": _get_attr(cand, "note"),
        "mime": mime,
        "created_at_utc": _get_attr(cand, "created_at_utc"),
        "created_by": _get_attr(cand, "created_by"),
        "updated_at_utc": _get_attr(cand, "updated_at_utc"),
        "updated_by": _get_attr(cand, "updated_by"),
    }

    def _stream():
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("manifest.json", json.dumps(manifest, indent=2))
            zf.writestr(f"blob/{fname}", blob_bytes)
        buf.seek(0)
        yield from buf

    out_name = f"candidate_{candidate_id}_{advisory_id[:12]}.zip"
    return StreamingResponse(
        _stream(),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{out_name}"'},
    )
