from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel

from .persist_glue import ATTACHMENTS_ROOT_DEFAULT

router = APIRouter(prefix="/api/rmos/acoustics", tags=["rmos", "acoustics"])

_SHA_RE = re.compile(r"^[a-f0-9]{64}$")


def _attachments_root() -> Path:
    return Path(
        os.getenv("RMOS_RUN_ATTACHMENTS_DIR", ATTACHMENTS_ROOT_DEFAULT)
    ).expanduser().resolve()


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


class AttachmentResolveResponse(BaseModel):
    sha256: str
    exists: bool
    bytes: Optional[int] = None
    ext: Optional[str] = None
    mime: Optional[str] = None


@router.get("/attachments/{sha256}", response_model=AttachmentResolveResponse)
def resolve_attachment(
    sha256: str,
    ext: Optional[str] = Query(default=None),
    download: int = Query(default=0),
):
    """
    Resolve a content-addressed attachment in the sharded store.
    - If download=0 (default): returns metadata (exists/bytes/mime)
    - If download=1: streams bytes via FileResponse
    """
    sha256 = sha256.lower().strip()
    if not _SHA_RE.match(sha256):
        raise HTTPException(status_code=400, detail="Invalid sha256")

    root = _attachments_root()
    ext_s = _sanitize_ext(ext)
    blob = _resolve_blob(root, sha256, ext_s)

    if blob is None:
        return AttachmentResolveResponse(
            sha256=sha256,
            exists=False,
        )

    if download == 1:
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
