from __future__ import annotations

import io
import json
import os
import re
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Dict, Any
from urllib.parse import urlencode
import hashlib

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from .persist_glue import ATTACHMENTS_ROOT_DEFAULT, load_run_artifact
from .signed_urls import sign_attachment

router = APIRouter(prefix="/api/rmos/acoustics", tags=["rmos", "acoustics"])

_SHA_RE = re.compile(r"^[a-f0-9]{64}$")


def _attachments_root() -> Path:
    return Path(os.getenv("RMOS_RUN_ATTACHMENTS_DIR", ATTACHMENTS_ROOT_DEFAULT)).expanduser().resolve()


def _client_ip(req: Request) -> str:
    return (req.client.host if req.client else "") or ""


def _sanitize_ext_from_relpath(relpath: str) -> str:
    if not relpath:
        return ""
    rel = relpath.replace("\\", "/")
    name = rel.split("/")[-1]
    suffix = Path(name).suffix
    if "/" in suffix or "\\" in suffix or len(suffix) > 16:
        return ""
    return suffix


def _max_zip_items() -> int:
    v = os.getenv("RMOS_ACOUSTICS_ZIP_MAX_ITEMS", "").strip()
    if not v:
        return 200
    try:
        return max(1, int(v))
    except Exception:
        return 200


def _max_zip_total_input_bytes() -> int:
    v = os.getenv("RMOS_ACOUSTICS_ZIP_MAX_TOTAL_INPUT_BYTES", "").strip()
    if not v:
        return 500 * 1024 * 1024  # 500MB
    try:
        return max(1, int(v))
    except Exception:
        return 500 * 1024 * 1024


def _max_zip_output_bytes() -> int:
    v = os.getenv("RMOS_ACOUSTICS_ZIP_MAX_OUTPUT_BYTES", "").strip()
    if not v:
        return 500 * 1024 * 1024  # 500MB
    try:
        return max(1, int(v))
    except Exception:
        return 500 * 1024 * 1024


def _safe_zip_member_name(relpath: str, sha256: str) -> str:
    """
    Prevent zip-slip; keep member names purely relative, no traversal.
    If relpath is missing/odd, fall back to sha256.
    """
    rel = (relpath or "").replace("\\", "/").strip()
    rel = rel.lstrip("/")
    # Drop any path components that are traversal
    parts = [p for p in rel.split("/") if p not in ("", ".", "..")]
    name = "/".join(parts)
    if not name:
        name = sha256
    return name


def _ensure_blob_exists(root: Path, sha: str, ext: str) -> Path:
    """
    For zip export, we require ext be known (from relpath suffix).
    """
    blob = root / sha[:2] / sha[2:4] / f"{sha}{ext}"
    if not blob.exists():
        raise FileNotFoundError(str(sha))
    return blob


def _store_blob_content_addressed(root: Path, tmp_file: Path, ext: str) -> tuple[str, Path, int]:
    """
    Hash tmp_file, then move into sharded store as {sha}{ext}.
    Returns (sha256, final_path, bytes).
    """
    h = hashlib.sha256()
    size = 0
    with tmp_file.open("rb") as f:
        while True:
            b = f.read(1024 * 1024)
            if not b:
                break
            h.update(b)
            size += len(b)
    sha = h.hexdigest()

    shard = root / sha[:2] / sha[2:4]
    shard.mkdir(parents=True, exist_ok=True)
    final_path = shard / f"{sha}{ext}"

    # Dedup: if already exists, just delete tmp
    if final_path.exists():
        try:
            tmp_file.unlink(missing_ok=True)  # py3.11+
        except Exception:
            pass
        return sha, final_path, int(final_path.stat().st_size)

    # Atomic move
    tmp_file.replace(final_path)
    return sha, final_path, size


class ZipExportRequest(BaseModel):
    sha256s: Optional[List[str]] = Field(
        default=None,
        description="Subset to include. If omitted/empty -> include all attachments in run (up to max items).",
    )
    zip_name: Optional[str] = Field(
        default="acoustics_attachments.zip",
        description="Download filename hint (no server path).",
    )
    ttl_seconds: Optional[int] = Field(default=None, description="Signed URL TTL")
    include_manifest: bool = Field(default=True, description="Include a manifest.json inside the zip")


class ZipExportResponse(BaseModel):
    run_id: str
    requested: int
    included: int

    zip_sha256: str
    bytes: int
    mime: str

    signed_url: str
    signed_exp: int

    filename: str


@router.post("/runs/{run_id}/attachments/zip", response_model=ZipExportResponse)
def export_run_attachments_zip(
    request: Request,
    run_id: str,
    body: ZipExportRequest,
):
    run = load_run_artifact(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    # Build attachment lookup by sha
    att_by_sha: Dict[str, Any] = {}
    for a in run.attachments:
        sha = (getattr(a, "sha256", "") or "").lower().strip()
        if _SHA_RE.match(sha):
            att_by_sha[sha] = a

    if not att_by_sha:
        raise HTTPException(status_code=404, detail="Run has no attachments")

    # Determine requested set
    wanted: List[str]
    if body.sha256s:
        wanted = [(s or "").lower().strip() for s in body.sha256s]
    else:
        wanted = list(att_by_sha.keys())

    # De-dupe while preserving order
    seen = set()
    wanted = [s for s in wanted if s and (s not in seen and not seen.add(s))]

    max_items = _max_zip_items()
    if len(wanted) > max_items:
        raise HTTPException(
            status_code=413,
            detail=f"Too many items requested ({len(wanted)}). Max is {max_items}. "
                   f"Set RMOS_ACOUSTICS_ZIP_MAX_ITEMS to adjust.",
        )

    root = _attachments_root()
    max_input = _max_zip_total_input_bytes()
    max_output = _max_zip_output_bytes()

    # Resolve blobs and enforce total input cap
    blobs: List[tuple[str, str, Path, int, str]] = []
    total_in = 0

    for sha in wanted:
        if not _SHA_RE.match(sha):
            continue
        a = att_by_sha.get(sha)
        if a is None:
            continue

        relpath = getattr(a, "relpath", "") or ""
        ext = _sanitize_ext_from_relpath(relpath)
        if not ext:
            continue

        try:
            blob = _ensure_blob_exists(root, sha, ext)
        except FileNotFoundError:
            continue

        try:
            sz = int(blob.stat().st_size)
        except Exception:
            continue

        total_in += sz
        if total_in > max_input:
            raise HTTPException(
                status_code=413,
                detail=f"Total input exceeds limit ({max_input} bytes). "
                       f"Set RMOS_ACOUSTICS_ZIP_MAX_TOTAL_INPUT_BYTES to adjust.",
            )

        member = _safe_zip_member_name(relpath, sha)
        mime = getattr(a, "mime", "") or ""
        blobs.append((sha, member, blob, sz, mime))

    if not blobs:
        raise HTTPException(status_code=404, detail="No eligible attachments found to zip")

    # Create zip in a temp file under attachments root (or system temp if desired)
    tmp_dir = root / ".tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(prefix="acoustics_zip_", suffix=".zip", dir=str(tmp_dir), delete=False) as tf:
        tmp_zip_path = Path(tf.name)

    included = 0
    manifest_entries = []

    try:
        with zipfile.ZipFile(str(tmp_zip_path), mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            # Add files
            for sha, member, blob, sz, mime in blobs:
                zf.write(str(blob), arcname=member)
                included += 1
                manifest_entries.append({
                    "sha256": sha,
                    "member": member,
                    "bytes": sz,
                    "mime": mime or None,
                })

            # Optional manifest inside zip
            if body.include_manifest:
                man = {
                    "manifest_version": 1,
                    "run_id": run_id,
                    "included": included,
                    "files": manifest_entries,
                }
                zf.writestr("manifest.json", json.dumps(man, indent=2, sort_keys=True))

        # Enforce output size cap
        out_size = int(tmp_zip_path.stat().st_size)
        if out_size > max_output:
            raise HTTPException(
                status_code=413,
                detail=f"ZIP output exceeds limit ({max_output} bytes). "
                       f"Set RMOS_ACOUSTICS_ZIP_MAX_OUTPUT_BYTES to adjust.",
            )

        # Store ZIP in content-addressed store
        zip_sha, final_path, final_bytes = _store_blob_content_addressed(root, tmp_zip_path, ".zip")

        # Sign URL for download
        token = sign_attachment(
            sha256=zip_sha,
            ext=".zip",
            download=1,
            ttl_seconds=body.ttl_seconds,
            client_ip=_client_ip(request),
        )
        qs = urlencode(token.to_query())
        signed_url = f"/api/rmos/acoustics/attachments/{zip_sha}/signed-download?{qs}"

        filename = (body.zip_name or "acoustics_attachments.zip").strip()
        # avoid weird header injection; keep it simple
        if len(filename) > 128:
            filename = "acoustics_attachments.zip"
        filename = filename.replace("\n", "").replace("\r", "")

        return ZipExportResponse(
            run_id=run_id,
            requested=len(wanted),
            included=included,
            zip_sha256=zip_sha,
            bytes=int(final_bytes),
            mime="application/zip",
            signed_url=signed_url,
            signed_exp=token.exp,
            filename=filename,
        )

    finally:
        # tmp_zip_path is either moved into store or still exists; clean up if present
        try:
            if tmp_zip_path.exists():
                tmp_zip_path.unlink()
        except Exception:
            pass
