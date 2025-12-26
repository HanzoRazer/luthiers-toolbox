from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from .persist_glue import ATTACHMENTS_ROOT_DEFAULT


router = APIRouter(prefix="/api/rmos/acoustics", tags=["rmos", "acoustics"])


_SHA_RE = re.compile(r"^[a-f0-9]{64}$")


def _get_attachments_root() -> Path:
    return Path(os.getenv("RMOS_RUN_ATTACHMENTS_DIR", ATTACHMENTS_ROOT_DEFAULT)).expanduser().resolve()


def _sharded_path(root: Path, sha256_hex: str, ext: str) -> Path:
    shard1 = sha256_hex[:2]
    shard2 = sha256_hex[2:4]
    return root / shard1 / shard2 / f"{sha256_hex}{ext}"


def _sanitize_ext(ext: Optional[str]) -> str:
    """
    Accept: None, "", ".wav", ".json", ".csv", ".png", etc.
    Reject weird ext like path separators.
    """
    if not ext:
        return ""
    ext = ext.strip()
    if ext == ".":
        return ""
    if "/" in ext or "\\" in ext:
        raise HTTPException(status_code=400, detail="Invalid ext.")
    if not ext.startswith("."):
        # allow "wav" style too
        ext = "." + ext
    # keep it short/sane
    if len(ext) > 16:
        raise HTTPException(status_code=400, detail="Invalid ext.")
    return ext


class AttachmentResolveResponse(BaseModel):
    sha256: str
    exists: bool
    path: Optional[str] = None
    bytes: Optional[int] = None
    ext: Optional[str] = None
    mime: Optional[str] = None


def _guess_mime(ext: str) -> Optional[str]:
    e = ext.lower()
    if e == ".wav":
        return "audio/wav"
    if e == ".json":
        return "application/json"
    if e == ".csv":
        return "text/csv"
    if e == ".png":
        return "image/png"
    if e in (".jpg", ".jpeg"):
        return "image/jpeg"
    if e == ".txt":
        return "text/plain"
    return None


@router.get("/attachments/{sha256}", response_model=AttachmentResolveResponse)
def resolve_attachment(
    sha256: str,
    ext: Optional[str] = Query(default=None, description="Optional file extension hint, e.g. .wav"),
    download: int = Query(default=0, description="Set 1 to stream the file contents"),
) -> AttachmentResolveResponse:
    """
    Resolve a content-addressed attachment in the sharded store.
    - If download=0 (default): returns metadata (exists/path/bytes)
    - If download=1: streams bytes via FileResponse (still returns JSON model? no; will return file)
    """
    sha256 = sha256.lower().strip()
    if not _SHA_RE.match(sha256):
        raise HTTPException(status_code=400, detail="Invalid sha256 (expected 64 lowercase hex).")

    root = _get_attachments_root()
    root.mkdir(parents=True, exist_ok=True)

    ext_s = _sanitize_ext(ext)
    mime = _guess_mime(ext_s) if ext_s else None

    # If ext specified, check that exact file
    if ext_s:
        p = _sharded_path(root, sha256, ext_s)
        if not p.exists():
            # not found
            return AttachmentResolveResponse(sha256=sha256, exists=False, ext=ext_s, mime=mime)
        if download == 1:
            return FileResponse(
                path=str(p),
                media_type=mime or "application/octet-stream",
                filename=p.name,
            )
        st = p.stat()
        return AttachmentResolveResponse(
            sha256=sha256,
            exists=True,
            path=str(p),
            bytes=int(st.st_size),
            ext=ext_s,
            mime=mime,
        )

    # If ext not specified, try to find any matching file by scanning known common extensions.
    # (We avoid scanning the whole store; only check the shard directory.)
    shard_dir = root / sha256[:2] / sha256[2:4]
    if not shard_dir.exists():
        return AttachmentResolveResponse(sha256=sha256, exists=False)

    # Common extensions (add more if you use them)
    candidates = [".json", ".wav", ".csv", ".png", ".jpg", ".jpeg", ".txt", ".nc", ".gcode", ".dxf"]
    found: Optional[Path] = None
    found_ext: str = ""
    for e in candidates:
        p = shard_dir / f"{sha256}{e}"
        if p.exists():
            found = p
            found_ext = e
            break

    # Also consider "no extension" file
    if found is None:
        p0 = shard_dir / sha256
        if p0.exists():
            found = p0
            found_ext = ""

    if found is None:
        return AttachmentResolveResponse(sha256=sha256, exists=False)

    if download == 1:
        return FileResponse(
            path=str(found),
            media_type=_guess_mime(found_ext) or "application/octet-stream",
            filename=found.name,
        )

    st = found.stat()
    return AttachmentResolveResponse(
        sha256=sha256,
        exists=True,
        path=str(found),
        bytes=int(st.st_size),
        ext=found_ext or None,
        mime=_guess_mime(found_ext),
    )
