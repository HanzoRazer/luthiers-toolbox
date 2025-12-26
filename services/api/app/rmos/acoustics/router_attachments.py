from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Optional
from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException, Query, Header, Request
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel

from .persist_glue import ATTACHMENTS_ROOT_DEFAULT
from .signed_urls import sign_attachment, verify_attachment

router = APIRouter(prefix="/api/rmos/acoustics", tags=["rmos", "acoustics"])

_SHA_RE = re.compile(r"^[a-f0-9]{64}$")


def _attachments_root() -> Path:
    return Path(os.getenv("RMOS_RUN_ATTACHMENTS_DIR", ATTACHMENTS_ROOT_DEFAULT)).expanduser().resolve()


def _sanitize_ext(ext: Optional[str]) -> str:
    if not ext:
        return ""
    ext = ext.strip()
    if "/" in ext or "\\" in ext:
        raise HTTPException(status_code=400, detail="Invalid ext")
    if not ext.startswith("."):
        ext = "." + ext
    if len(ext) > 16:
        raise HTTPException(status_code=400, detail="Invalid ext")
    return ext


def _guess_mime(ext: str) -> Optional[str]:
    return {
        ".wav": "audio/wav",
        ".json": "application/json",
        ".csv": "text/csv",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".txt": "text/plain",
        ".dxf": "image/vnd.dxf",
        ".nc": "text/plain",
        ".gcode": "text/plain",
    }.get(ext.lower())


def _resolve_blob(root: Path, sha: str, ext_hint: str) -> Optional[Path]:
    shard = root / sha[:2] / sha[2:4]
    if not shard.exists():
        return None

    if ext_hint:
        p = shard / f"{sha}{ext_hint}"
        if p.exists():
            return p

    for e in [".json", ".wav", ".csv", ".png", ".jpg", ".jpeg", ".txt", ".nc", ".gcode", ".dxf"]:
        p = shard / f"{sha}{e}"
        if p.exists():
            return p

    p0 = shard / sha
    return p0 if p0.exists() else None


def _max_attachment_bytes() -> int:
    v = os.getenv("RMOS_MAX_ATTACHMENT_BYTES", "").strip()
    if not v:
        return 104857600  # 100MB default
    try:
        return int(v)
    except Exception:
        return 104857600


def _require_stream_token(x_rmos_stream_token: Optional[str]) -> None:
    token = os.getenv("RMOS_ACOUSTICS_STREAM_TOKEN", "").strip()
    if not token:
        return  # dev/default: no gate
    if (x_rmos_stream_token or "").strip() != token:
        raise HTTPException(status_code=401, detail="Streaming requires X-RMOS-Stream-Token")


def _enforce_size_limit(blob: Path) -> None:
    limit = _max_attachment_bytes()
    try:
        size = blob.stat().st_size
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Attachment not found")
    if size > limit:
        raise HTTPException(status_code=413, detail=f"Attachment exceeds size limit ({limit} bytes)")


def _client_ip(req: Request) -> str:
    # If you're behind a reverse proxy, you can adjust this later.
    # Keep simple and explicit for now.
    return (req.client.host if req.client else "") or ""


class AttachmentResolveResponse(BaseModel):
    sha256: str
    exists: bool
    bytes: Optional[int] = None
    ext: Optional[str] = None
    mime: Optional[str] = None


class SignedUrlResponse(BaseModel):
    sha256: str
    exp: int
    url: str


@router.head("/attachments/{sha256}")
def head_attachment(
    sha256: str,
    ext: Optional[str] = Query(default=None),
) -> Response:
    """
    HEAD request to get attachment metadata via headers only.
    Returns X-RMOS-Exists, X-RMOS-Bytes, X-RMOS-Ext, X-RMOS-Mime.
    """
    sha256 = sha256.lower().strip()
    if not _SHA_RE.match(sha256):
        raise HTTPException(status_code=400, detail="Invalid sha256")

    root = _attachments_root()
    ext_s = _sanitize_ext(ext)
    blob = _resolve_blob(root, sha256, ext_s)

    if blob is None:
        return Response(status_code=404, headers={"X-RMOS-Exists": "0"})

    st = blob.stat()
    mime = _guess_mime(blob.suffix)
    headers = {
        "X-RMOS-Exists": "1",
        "X-RMOS-Bytes": str(int(st.st_size)),
        "X-RMOS-Ext": blob.suffix or "",
        "X-RMOS-Mime": mime or "",
    }
    return Response(status_code=200, headers=headers)


@router.get("/attachments/{sha256}", response_model=AttachmentResolveResponse)
def resolve_attachment(
    sha256: str,
    ext: Optional[str] = Query(default=None),
    download: int = Query(default=0),
    x_rmos_stream_token: Optional[str] = Header(default=None, alias="X-RMOS-Stream-Token"),
):
    """
    Resolve a content-addressed attachment in the sharded store.
    - If download=0 (default): returns metadata (exists/bytes/mime)
    - If download=1: streams bytes via FileResponse (auth-gated if RMOS_ACOUSTICS_STREAM_TOKEN set)
    """
    sha256 = sha256.lower().strip()
    if not _SHA_RE.match(sha256):
        raise HTTPException(status_code=400, detail="Invalid sha256")

    root = _attachments_root()
    ext_s = _sanitize_ext(ext)
    blob = _resolve_blob(root, sha256, ext_s)

    if blob is None:
        return AttachmentResolveResponse(sha256=sha256, exists=False)

    if download == 1:
        # Header-gated streaming (legacy mode)
        _require_stream_token(x_rmos_stream_token)
        _enforce_size_limit(blob)
        return FileResponse(
            path=str(blob),
            media_type=_guess_mime(blob.suffix) or "application/octet-stream",
            filename=blob.name,
        )

    st = blob.stat()
    return AttachmentResolveResponse(
        sha256=sha256,
        exists=True,
        bytes=int(st.st_size),
        ext=blob.suffix or None,
        mime=_guess_mime(blob.suffix),
    )


@router.get("/attachments/{sha256}/signed", response_model=SignedUrlResponse)
def create_signed_url(
    request: Request,
    sha256: str,
    ext: str = Query(..., description="Required extension, e.g. .wav"),
    ttl_seconds: Optional[int] = Query(default=None, description="Optional TTL override"),
) -> SignedUrlResponse:
    """
    Returns a signed URL for streaming/downloading a blob without requiring auth headers in the browser.
    Requires RMOS_ACOUSTICS_SIGNING_SECRET to be set.
    """
    sha256 = sha256.lower().strip()
    if not _SHA_RE.match(sha256):
        raise HTTPException(status_code=400, detail="Invalid sha256")

    ext_s = _sanitize_ext(ext)
    if not ext_s:
        raise HTTPException(status_code=400, detail="ext is required")

    # Ensure it exists before issuing a signed URL
    root = _attachments_root()
    blob = _resolve_blob(root, sha256, ext_s)
    if blob is None:
        raise HTTPException(status_code=404, detail="Attachment not found")

    token = sign_attachment(
        sha256=sha256,
        ext=ext_s,
        download=1,
        ttl_seconds=ttl_seconds,
        client_ip=_client_ip(request),
    )

    # Build URL (relative). Frontend can prefix with API base.
    q = urlencode(token.to_query())
    url = f"/api/rmos/acoustics/attachments/{sha256}/signed-download?{q}"
    return SignedUrlResponse(sha256=sha256, exp=token.exp, url=url)


@router.get("/attachments/{sha256}/signed-download")
def signed_download(
    request: Request,
    sha256: str,
    exp: int = Query(...),
    ext: str = Query(...),
    dl: int = Query(default=1),
    ip: str = Query(default=""),
    sig: str = Query(...),
):
    """
    Streams the blob if signature is valid and not expired.
    This bypasses X-RMOS-Stream-Token (signature is the gate).
    """
    sha256 = sha256.lower().strip()
    if not _SHA_RE.match(sha256):
        raise HTTPException(status_code=400, detail="Invalid sha256")

    ext_s = _sanitize_ext(ext)
    if not ext_s:
        raise HTTPException(status_code=400, detail="Invalid ext")

    try:
        verify_attachment(
            sha256=sha256,
            exp=int(exp),
            ext=ext_s,
            download=int(dl),
            ip=ip or "",
            sig=sig,
            client_ip=_client_ip(request),
        )
    except ValueError as e:
        # Avoid leaking details; give stable error codes.
        reason = str(e)
        if reason == "expired":
            raise HTTPException(status_code=401, detail="Signed URL expired")
        raise HTTPException(status_code=401, detail="Invalid signed URL")

    root = _attachments_root()
    blob = _resolve_blob(root, sha256, ext_s)
    if blob is None:
        raise HTTPException(status_code=404, detail="Attachment not found")

    _enforce_size_limit(blob)

    return FileResponse(
        path=str(blob),
        media_type=_guess_mime(blob.suffix) or "application/octet-stream",
        filename=blob.name,
    )
