from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Optional, List, Dict, Any
from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

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
    # Normalize slashes (relpath should be logical, not a filesystem path)
    rel = relpath.replace("\\", "/")
    name = rel.split("/")[-1]
    suffix = Path(name).suffix
    if "/" in suffix or "\\" in suffix or len(suffix) > 16:
        return ""
    return suffix


def _client_ip(req: Request) -> str:
    return (req.client.host if req.client else "") or ""


def _max_batch_items() -> int:
    v = os.getenv("RMOS_ACOUSTICS_SIGNED_BATCH_MAX_ITEMS", "").strip()
    if not v:
        return 200
    try:
        return max(1, int(v))
    except Exception:
        return 200


def _normalize_kind_list(xs: Optional[List[str]]) -> Optional[set[str]]:
    if not xs:
        return None
    out = set()
    for x in xs:
        if not x:
            continue
        s = str(x).strip()
        if not s:
            continue
        if len(s) > 80:
            continue
        out.add(s)
    return out if out else None


def _normalize_prefix_list(xs: Optional[List[str]]) -> Optional[list[str]]:
    if not xs:
        return None
    out: list[str] = []
    for x in xs:
        if not x:
            continue
        s = str(x).strip()
        if not s:
            continue
        if len(s) > 80:
            continue
        out.append(s)
    return out if out else None


def _kind_allowed(kind: Optional[str], include: Optional[set[str]], exclude: Optional[set[str]], prefixes: Optional[list[str]]) -> bool:
    k = (kind or "").strip()
    if exclude and k in exclude:
        return False
    if include is not None:
        return k in include
    if prefixes:
        return any(k.startswith(p) for p in prefixes)
    return True


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
        sha = (a.sha256 or "").lower().strip()
        if not _SHA_RE.match(sha):
            continue

        ext = _sanitize_ext_from_relpath(a.relpath or "")
        blob = root / sha[:2] / sha[2:4] / f"{sha}{ext}"

        size = None
        if blob.exists():
            try:
                size = int(blob.stat().st_size)
            except Exception:
                size = None

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
            entry.signed_url = f"/api/rmos/acoustics/attachments/{sha}/signed-download?{qs}"
            entry.signed_exp = token.exp

        out.append(entry)

    return RunAttachmentsResponse(run_id=run_id, count=len(out), attachments=out)


# ----------------------------
# NEW: Bulk signed-batch
# ----------------------------

class SignedBatchRequest(BaseModel):
    """
    If sha256s is omitted or empty, signs ALL attachments in the run (up to max items),
    after applying kind filters (if provided).
    """
    sha256s: Optional[List[str]] = Field(default=None, description="Subset of attachment sha256s to sign")
    ttl_seconds: Optional[int] = Field(default=None, description="TTL for signed URLs (seconds)")
    include_metadata: bool = Field(default=True, description="Include relpath/kind/bytes/mime in response")

    include_kinds: Optional[List[str]] = Field(default=None, description="If provided, include only attachments whose kind is in this set")
    exclude_kinds: Optional[List[str]] = Field(default=None, description="If provided, exclude attachments whose kind is in this set")
    kind_prefixes: Optional[List[str]] = Field(default=None, description="Optional: include attachments whose kind starts with any prefix")


class SignedBatchItem(BaseModel):
    sha256: str
    relpath: Optional[str] = None
    kind: Optional[str] = None
    bytes: Optional[int] = None
    mime: Optional[str] = None

    signed_url: Optional[str] = None
    signed_exp: Optional[int] = None

    ok: bool = True
    error: Optional[str] = None


class SignedBatchResponse(BaseModel):
    run_id: str
    requested: int
    signed: int

    included_sha256s: List[str] = []

    skipped_filtered: int = 0
    skipped_invalid_sha: int = 0
    skipped_not_in_run: int = 0
    skipped_missing_ext: int = 0
    skipped_blob_missing: int = 0

    items: List[SignedBatchItem]


@router.post("/runs/{run_id}/attachments/signed-batch", response_model=SignedBatchResponse)
def signed_batch(
    request: Request,
    run_id: str,
    body: SignedBatchRequest,
):
    """
    Bulk pre-sign attachments for a run.
    Returns one signed URL per requested attachment.

    This is frontend-safe (no secrets) and avoids per-attachment round trips.
    """
    run = load_run_artifact(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    # Build lookup from run attachments
    att_by_sha: Dict[str, Any] = {}
    for a in run.attachments:
        sha = (getattr(a, "sha256", "") or "").lower().strip()
        if _SHA_RE.match(sha):
            att_by_sha[sha] = a

    if not att_by_sha:
        return SignedBatchResponse(run_id=run_id, requested=0, signed=0, items=[])

    # Normalize kind filters
    include_kinds = _normalize_kind_list(body.include_kinds)
    exclude_kinds = _normalize_kind_list(body.exclude_kinds)
    kind_prefixes = _normalize_prefix_list(body.kind_prefixes)

    # If both include_kinds and kind_prefixes are provided, include_kinds wins.
    if include_kinds is not None:
        kind_prefixes = None

    # Determine target set
    wanted: List[str]
    if body.sha256s:
        wanted = [(s or "").lower().strip() for s in body.sha256s]
    else:
        wanted = list(att_by_sha.keys())

    # De-dupe while preserving order
    seen = set()
    wanted = [s for s in wanted if s and (s not in seen and not seen.add(s))]

    max_items = _max_batch_items()
    if len(wanted) > max_items:
        raise HTTPException(
            status_code=413,
            detail=f"Too many items requested ({len(wanted)}). Max is {max_items}. "
                   f"Set RMOS_ACOUSTICS_SIGNED_BATCH_MAX_ITEMS to adjust.",
        )

    root = _attachments_root()
    client_ip = _client_ip(request)

    items: List[SignedBatchItem] = []
    included_sha256s: list[str] = []
    signed_count = 0

    skipped_filtered = 0
    skipped_invalid_sha = 0
    skipped_not_in_run = 0
    skipped_missing_ext = 0
    skipped_blob_missing = 0

    for sha in wanted:
        if not _SHA_RE.match(sha):
            skipped_invalid_sha += 1
            continue

        a = att_by_sha.get(sha)
        if a is None:
            skipped_not_in_run += 1
            continue

        kind = getattr(a, "kind", None)
        if not _kind_allowed(kind, include_kinds, exclude_kinds, kind_prefixes):
            skipped_filtered += 1
            continue

        relpath = getattr(a, "relpath", None) or ""
        ext = _sanitize_ext_from_relpath(relpath)
        if not ext:
            skipped_missing_ext += 1
            continue

        # Ensure blob exists before signing (avoid issuing dead links)
        blob = root / sha[:2] / sha[2:4] / f"{sha}{ext}"
        if not blob.exists():
            skipped_blob_missing += 1
            continue

        token = sign_attachment(
            sha256=sha,
            ext=ext,
            download=1,
            ttl_seconds=body.ttl_seconds,
            client_ip=client_ip,
        )
        qs = urlencode(token.to_query())
        signed_url = f"/api/rmos/acoustics/attachments/{sha}/signed-download?{qs}"

        st_size = None
        try:
            st_size = int(blob.stat().st_size)
        except Exception:
            st_size = None

        item = SignedBatchItem(
            sha256=sha,
            signed_url=signed_url,
            signed_exp=token.exp,
            ok=True,
            error=None,
        )

        if body.include_metadata:
            item.relpath = relpath
            item.kind = kind
            item.bytes = st_size
            item.mime = getattr(a, "mime", None)

        items.append(item)
        included_sha256s.append(sha)
        signed_count += 1

    return SignedBatchResponse(
        run_id=run_id,
        requested=len(wanted),
        signed=signed_count,
        included_sha256s=included_sha256s,
        skipped_filtered=skipped_filtered,
        skipped_invalid_sha=skipped_invalid_sha,
        skipped_not_in_run=skipped_not_in_run,
        skipped_missing_ext=skipped_missing_ext,
        skipped_blob_missing=skipped_blob_missing,
        items=items,
    )
