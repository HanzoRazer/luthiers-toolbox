"""
RMOS Acoustics Router - Read-only advisory surface.

Provides three endpoints:
1. List advisories for a run (from _index.json rollup)
2. Resolve advisory_id to its blob pointer (from _advisory_lookup.json)
3. Stream attachment blob by sha256 (no path disclosure)

This router does NOT:
- Compute advisories
- Modify runs
- Interpret acoustics logic
- Expose filesystem paths in JSON payloads
"""
from __future__ import annotations

import base64
import os
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import FileResponse

from .store import RunStoreV2
from .attachments import resolve_attachment_path
from .signed_urls import make_signed_query, verify_attachment_request, Scope
from .attachment_meta import AttachmentMetaIndex
from .acoustics_schemas import (
    AttachmentMetaPublic,
    RunAttachmentsListOut,
    AttachmentExistsOut,
    SignedUrlMintOut,
    RunAdvisoriesListOut,
    AdvisorySummary,
    IndexRebuildOut,
)


router = APIRouter()


# -------------------------
# Dependencies
# -------------------------


def require_auth() -> None:
    """
    Placeholder for auth gating.

    Replace this with your real dependency, e.g.
      from app.auth import require_user
      def require_auth(user=Depends(require_user)): ...
    """
    return None


def get_store() -> RunStoreV2:
    """
    Store accessor.

    If you already instantiate a singleton store elsewhere, swap this to return it.
    """
    return RunStoreV2()


def _signed_urls_enabled() -> bool:
    """If secret is set, signed URLs feature is enabled."""
    return bool(os.getenv("RMOS_SIGNED_URL_SECRET", "").strip())


def require_auth_or_signed(
    request: Request,
    sha256: str,
    download: bool = False,
    filename: Optional[str] = None,
) -> None:
    """
    If a valid signed URL is present, allow without normal auth.
    Otherwise require normal auth.

    Signed query params:
      ?expires=...&sig=...&download=...&filename=...
    """
    qp = request.query_params
    exp = qp.get("expires")
    sig = qp.get("sig")

    if exp and sig and _signed_urls_enabled():
        ok = verify_attachment_request(
            method=request.method,
            path=request.url.path,  # includes /api/rmos/acoustics prefix
            sha256=sha256,
            expires=int(exp),
            sig=str(sig),
            download=bool(download),
            filename=filename,
        )
        if ok:
            return None
        raise HTTPException(status_code=403, detail="invalid or expired signed URL")

    # Fallback to normal auth (placeholder)
    require_auth()
    return None


# -------------------------
# Endpoints
# -------------------------


@router.get("/runs/{run_id}/advisories", response_model=RunAdvisoriesListOut)
def list_run_advisories(
    run_id: str,
    _auth: None = Depends(require_auth),
    store: RunStoreV2 = Depends(get_store),
) -> RunAdvisoriesListOut:
    """
    List advisory summaries for a run.

    Source: run-local rollup inside _index.json (meta["advisories"]).
    Does NOT read advisory blobs.
    """
    advisories = store.list_run_advisories(run_id)
    return RunAdvisoriesListOut(
        run_id=run_id,
        count=len(advisories),
        advisories=[AdvisorySummary(**a) if isinstance(a, dict) else a for a in advisories],
    )


@router.get("/advisories/{advisory_id}")
def resolve_advisory(
    advisory_id: str,
    _auth: None = Depends(require_auth),
    store: RunStoreV2 = Depends(get_store),
) -> Dict[str, Any]:
    """
    Resolve advisory_id -> lookup entry (includes sha256 + run_id + metadata).
    Source: _advisory_lookup.json

    This does NOT stream the blob; it returns the pointer for the client
    to call /attachments/{sha256} (or for server-side to fetch).
    """
    entry = store.resolve_advisory(advisory_id)
    if not entry:
        raise HTTPException(status_code=404, detail="advisory_id not found")
    return entry


@router.get("/attachments/{sha256}")
def get_attachment_by_sha256(
    sha256: str,
    request: Request,
    _auth: None = Depends(lambda: None),  # auth handled below
    *,
    download: bool = False,
    filename: Optional[str] = None,
) -> FileResponse:
    """
    Stream an attachment blob by sha256 from the content-addressed store.

    - DOES NOT return shard paths in JSON.
    - Streams file bytes (FileResponse).
    - Supports signed URLs (no auth required if valid signature present).
    - Optional:
        ?download=true -> content-disposition attachment
        ?filename=... -> override filename for the browser
        ?expires=...&sig=... -> signed URL params (bypasses normal auth)
    """
    # Allow either normal auth or valid signed URL
    require_auth_or_signed(request, sha256, download=download, filename=filename)

    p = resolve_attachment_path(sha256)
    if not p.exists():
        raise HTTPException(status_code=404, detail="attachment not found")

    # Best-effort name: caller can override with ?filename=
    display_name = filename or p.name
    headers = {}
    if download:
        headers["Content-Disposition"] = f'attachment; filename="{display_name}"'

    return FileResponse(
        path=str(p),
        media_type="application/octet-stream",
        filename=display_name,
        headers=headers,
    )


@router.head("/attachments/{sha256}")
def head_attachment_metadata(
    sha256: str,
    request: Request,
    _auth: None = Depends(lambda: None),  # auth handled below (signed OR normal)
    store: RunStoreV2 = Depends(get_store),
    *,
    # Optional: give us a run_id so we can resolve kind/mime/filename from the RunArtifact
    run_id: Optional[str] = None,
) -> Response:
    """
    HEAD metadata for an attachment blob.

    Returns headers:
      - Content-Length
      - Content-Type (best-effort)
      - X-RMOS-Attachment-SHA256
      - X-RMOS-Attachment-Kind (if resolvable)
      - X-RMOS-Attachment-Filename (if resolvable)
      - X-RMOS-Attachment-Created-At (if resolvable)

    Signed URL compatible (method=HEAD).
    No shard path disclosure.
    """
    # Allow either normal auth or valid signed URL
    require_auth_or_signed(request, sha256)

    p = resolve_attachment_path(sha256)
    if not p.exists():
        raise HTTPException(status_code=404, detail="attachment not found")

    # Always true from store (authoritative)
    size_bytes = int(p.stat().st_size)

    # Best-effort resolved fields
    kind = None
    mime = "application/octet-stream"
    filename = None
    created_at = None

    if run_id:
        # Resolve from specific run's attachment record
        art = store.get(run_id)
        if art is not None:
            atts = getattr(art, "attachments", None) or []
            for a in atts:
                if getattr(a, "sha256", None) == sha256:
                    kind = getattr(a, "kind", None) or kind
                    mime = getattr(a, "mime", None) or mime
                    filename = getattr(a, "filename", None) or filename
                    created_at = getattr(a, "created_at_utc", None) or created_at
                    # Prefer store-reported size if present
                    sb = getattr(a, "size_bytes", None)
                    if isinstance(sb, int) and sb >= 0:
                        size_bytes = sb
                    break
    else:
        # Fallback: resolve from global attachment meta index
        meta_index = AttachmentMetaIndex(store.root)
        meta = meta_index.get(sha256)
        if meta:
            kind = meta.get("kind") or kind
            mime = meta.get("mime") or mime
            filename = meta.get("filename") or filename
            created_at = meta.get("created_at_utc") or created_at
            sb = meta.get("size_bytes")
            if isinstance(sb, int) and sb > 0:
                size_bytes = sb

    headers = {
        "Content-Length": str(size_bytes),
        "Content-Type": mime,
        "X-RMOS-Attachment-SHA256": sha256,
    }
    if kind:
        headers["X-RMOS-Attachment-Kind"] = str(kind)
    if filename:
        headers["X-RMOS-Attachment-Filename"] = str(filename)
    if created_at:
        headers["X-RMOS-Attachment-Created-At"] = str(created_at)

    # HEAD must return no body
    return Response(status_code=200, headers=headers)


@router.post("/attachments/{sha256}/signed_url", response_model=SignedUrlMintOut)
def mint_signed_attachment_url(
    sha256: str,
    request: Request,
    _auth: None = Depends(require_auth),
    *,
    ttl_seconds: int = 300,
    download: bool = False,
    filename: Optional[str] = None,
    method: str = "GET",  # "GET" or "HEAD"
    scope: Scope = "download",
) -> SignedUrlMintOut:
    """
    Mint a temporary signed URL for downloading/streaming an attachment.

    Frontend calls this (auth-gated), receives a signed URL usable without cookies/secrets.

    Query params:
      - ttl_seconds: URL validity duration (default 300 = 5 minutes)
      - download: include Content-Disposition attachment header
      - filename: override filename for browser download
      - method: HTTP method to sign ("GET" or "HEAD")
      - scope: Token scope ("download" or "head"). Download tokens work for HEAD too.
    """
    if not _signed_urls_enabled():
        raise HTTPException(status_code=503, detail="signed URLs not enabled")

    method_u = method.upper().strip()
    if method_u not in {"GET", "HEAD"}:
        raise HTTPException(status_code=400, detail="method must be GET or HEAD")

    # The path that will be requested later (strip /signed_url suffix)
    attachment_path = request.url.path.rsplit("/signed_url", 1)[0]

    # Signed query for the specified method
    params = make_signed_query(
        method=method_u,
        path=attachment_path,
        sha256=sha256,
        ttl_seconds=int(ttl_seconds),
        scope=scope,
        download=download,
        filename=filename,
    )

    # Build query string
    q = f"expires={params.expires}&sig={params.sig}&scope={params.scope}"
    if download:
        q += "&download=true"
    if filename:
        q += f"&filename={filename}"

    return SignedUrlMintOut(
        sha256=sha256,
        method=method_u,
        scope=scope,
        expires=params.expires,
        signed_url=f"{attachment_path}?{q}",
    )


@router.get("/runs/{run_id}/attachments", response_model=RunAttachmentsListOut)
def list_run_attachments_with_bytes(
    run_id: str,
    _auth: None = Depends(require_auth),
    store: RunStoreV2 = Depends(get_store),
    *,
    # Optional filters
    kinds: Optional[str] = None,  # comma-separated filter: "manifest,analysis,advisory.v1.json"
    # Safety controls
    include_bytes: bool = True,
    max_inline_bytes: int = 2_000_000,  # 2 MB default (override per call if needed)
    include_urls: bool = True,
) -> RunAttachmentsListOut:
    """
    Return attachments for a run with inline bytes (base64), plus mime/kind.

    - No shard path disclosure.
    - Inline bytes are guarded by max_inline_bytes.
    - If file is too large, data is omitted with omitted_reason.

    Query params:
      - kinds: comma-separated list of attachment kinds to include
      - include_bytes: false -> metadata only (still one call)
      - max_inline_bytes: override inline size limit (server still enforces)
      - include_urls: true -> adds download_url per attachment
    """
    artifact = store.get(run_id)
    if artifact is None:
        raise HTTPException(status_code=404, detail="run_id not found")

    # Pull attachments from RunArtifact (defensive: don't assume field always exists)
    attachments = getattr(artifact, "attachments", None) or []

    # Parse kinds filter
    kinds_set = None
    if kinds:
        kinds_set = {k.strip() for k in kinds.split(",") if k.strip()}

    out_items = []
    for a in attachments:
        # 'a' is expected to be RunAttachment (Pydantic model)
        kind = getattr(a, "kind", None)
        if kinds_set is not None and kind not in kinds_set:
            continue

        sha256 = getattr(a, "sha256", None)
        if not sha256:
            continue

        item = {
            "sha256": sha256,
            "kind": kind,
            "mime": getattr(a, "mime", None),
            "filename": getattr(a, "filename", None),
            "size_bytes": getattr(a, "size_bytes", None),
            "created_at_utc": getattr(a, "created_at_utc", None),
            "data_b64": None,
            "omitted_reason": None,
            "download_url": f"/api/rmos/acoustics/attachments/{sha256}" if include_urls else None,
        }

        if include_bytes:
            p = resolve_attachment_path(sha256)
            if not p.exists():
                item["omitted_reason"] = "missing_in_store"
            else:
                # Prefer store-reported size, but verify on disk
                try:
                    st_size = int(p.stat().st_size)
                except Exception:
                    st_size = None

                if st_size is not None and st_size > int(max_inline_bytes):
                    item["omitted_reason"] = f"too_large_for_inline>{int(max_inline_bytes)}"
                else:
                    try:
                        raw = p.read_bytes()
                        if len(raw) > int(max_inline_bytes):
                            item["omitted_reason"] = f"too_large_for_inline>{int(max_inline_bytes)}"
                        else:
                            item["data_b64"] = base64.b64encode(raw).decode("ascii")
                    except Exception:
                        item["omitted_reason"] = "read_failed"

        out_items.append(AttachmentMetaPublic(**item))

    return RunAttachmentsListOut(
        run_id=run_id,
        count=len(out_items),
        include_bytes=include_bytes,
        max_inline_bytes=int(max_inline_bytes),
        attachments=out_items,
    )


@router.post("/index/rebuild_attachment_meta", response_model=IndexRebuildOut)
def rebuild_attachment_meta_index(
    _auth: None = Depends(require_auth),
    store: RunStoreV2 = Depends(get_store),
) -> IndexRebuildOut:
    """
    Rebuild global sha256->meta index by scanning authoritative run artifacts on disk.

    Writes: {runs_root}/_attachment_meta.json

    This operation:
    - Scans date-partitioned run artifacts (source of truth)
    - Rebuilds _attachment_meta.json atomically (temp -> replace)
    - No path disclosure to clients
    - Auth-gated
    """
    idx = AttachmentMetaIndex(store.root)
    stats = idx.rebuild_from_run_artifacts()
    return IndexRebuildOut(ok=True, **stats)


@router.get("/index/attachment_meta/{sha256}/exists", response_model=AttachmentExistsOut)
def attachment_meta_exists(
    sha256: str,
    _auth: None = Depends(require_auth),
    store: RunStoreV2 = Depends(get_store),
) -> AttachmentExistsOut:
    """
    H7.2.2.1: Check both index presence and blob presence for an attachment.

    Returns:
      - in_index: true if sha256 exists in _attachment_meta.json
      - in_store: true if blob exists in content-addressed attachments store
      - size_bytes: file size if in_store is true
      - index_* fields: metadata from index when in_index=True

    No shard path disclosure.
    """
    idx = AttachmentMetaIndex(store.root)
    meta = idx.get(sha256)
    in_index = meta is not None

    p = resolve_attachment_path(sha256)
    in_store = p.exists()

    size_bytes = None
    if in_store:
        try:
            size_bytes = int(p.stat().st_size)
        except Exception:
            size_bytes = None

    # Extended fields when in_index
    index_kind = meta.get("kind") if meta else None
    index_mime = meta.get("mime") if meta else None
    index_filename = meta.get("filename") if meta else None
    index_size_bytes = meta.get("size_bytes") if meta else None

    return AttachmentExistsOut(
        sha256=sha256.lower().strip(),
        in_index=in_index,
        in_store=in_store,
        size_bytes=size_bytes,
        index_kind=index_kind,
        index_mime=index_mime,
        index_filename=index_filename,
        index_size_bytes=index_size_bytes,
    )


@router.get("/index/attachment_meta/{sha256}")
def get_attachment_meta_from_index(
    sha256: str,
    _auth: None = Depends(require_auth),
    store: RunStoreV2 = Depends(get_store),
) -> Dict[str, Any]:
    """Query the global sha256→meta index directly (no paths).

    Returns the index row for the given sha256 if present.
    """
    idx = AttachmentMetaIndex(store.root)
    meta = idx.get(sha256)
    if meta is None:
        raise HTTPException(status_code=404, detail="sha256 not found in attachment meta index")
    return {"sha256": sha256.lower().strip(), **meta}
