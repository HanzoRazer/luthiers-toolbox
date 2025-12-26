from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Optional, List
from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel

from .persist_glue import (
    ATTACHMENTS_ROOT_DEFAULT,
    load_run_artifact,
)
from .signed_urls import sign_attachment

router = APIRouter(prefix="/api/rmos/acoustics", tags=["rmos", "acoustics"])

_SHA_RE = re.compile(r"^[a-f0-9]{64}$")


def _attachments_root() -> Path:
    return Path(
        os.getenv("RMOS_RUN_ATTACHMENTS_DIR", ATTACHMENTS_ROOT_DEFAULT)
    ).expanduser().resolve()


def _sanitize_ext_from_relpath(relpath: str) -> str:
    if not relpath:
        return ""
    suffix = Path(relpath).suffix
    if "/" in suffix or "\\" in suffix or len(suffix) > 16:
        return ""
    return suffix


def _client_ip(req: Request) -> str:
    return (req.client.host if req.client else "") or ""


class RunAttachmentOut(BaseModel):
    sha256: str
    relpath: str
    kind: Optional[str] = None
    bytes: Optional[int] = None
    mime: Optional[str] = None
    signed_url: Optional[str] = None
    signed_exp: Optional[int] = None


class RunAttachmentsResponse(BaseModel):
    run_id: str
    count: int
    attachments: List[RunAttachmentOut]


@router.get("/runs/{run_id}/attachments", response_model=RunAttachmentsResponse)
def list_run_attachments(
    request: Request,
    run_id: str,
    signed: int = Query(default=0, description="Include signed URLs"),
    ttl: Optional[int] = Query(default=None, description="TTL for signed URLs"),
):
    """
    Lists attachments for a run.
    Optionally emits signed URLs (HMAC + expiry) with no path disclosure.
    """
    run = load_run_artifact(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    root = _attachments_root()
    out: List[RunAttachmentOut] = []

    for a in run.attachments:
        sha = a.sha256.lower().strip()
        if not _SHA_RE.match(sha):
            continue

        ext = _sanitize_ext_from_relpath(a.relpath or "")
        blob = root / sha[:2] / sha[2:4] / f"{sha}{ext}"

        size = None
        if blob.exists():
            try:
                size = blob.stat().st_size
            except Exception:
                pass

        entry = RunAttachmentOut(
            sha256=sha,
            relpath=a.relpath,
            kind=getattr(a, "kind", None),
            bytes=size,
            mime=getattr(a, "mime", None),
        )

        if signed == 1:
            token = sign_attachment(
                sha256=sha,
                ext=ext,
                download=1,
                ttl_seconds=ttl,
                client_ip=_client_ip(request),
            )
            qs = urlencode(token.to_query())
            entry.signed_url = (
                f"/api/rmos/acoustics/attachments/{sha}/signed-download?{qs}"
            )
            entry.signed_exp = token.exp

        out.append(entry)

    return RunAttachmentsResponse(
        run_id=run_id,
        count=len(out),
        attachments=out,
    )
