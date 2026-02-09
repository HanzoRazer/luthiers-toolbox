"""
Acoustics attachment-index endpoints (facets, browse, recent, exists, rebuild).

Extracted from acoustics_router.py during WP-3 decomposition.
"""
from __future__ import annotations

import os
from collections import Counter
from typing import Any, Dict, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from .store import RunStoreV2
from .attachments import resolve_attachment_path
from .attachment_meta import AttachmentMetaIndex, AttachmentRecentIndex
from .acoustics_helpers import enrich_with_urls, apply_cursor_pagination
from .acoustics_schemas import (
    AttachmentMetaIndexEntry,
    AttachmentMetaBrowseOut,
    AttachmentMetaFacetsOut,
    AttachmentMetaRecentOut,
    AttachmentExistsOut,
    IndexRebuildOut,
)


router = APIRouter()


# -------------------------
# Dependencies (same contract as parent router)
# -------------------------


def require_auth() -> None:
    """Placeholder for auth gating."""
    return None


def get_store() -> RunStoreV2:
    return RunStoreV2()


# -------------------------
# Index Endpoints
# -------------------------


@router.post("/index/rebuild_attachment_meta", response_model=IndexRebuildOut)
def rebuild_attachment_meta_index(
    _auth: None = Depends(require_auth),
    store: RunStoreV2 = Depends(get_store),
) -> IndexRebuildOut:
    """Rebuild global sha256->meta index by scanning authoritative run artifacts on disk."""
    idx = AttachmentMetaIndex(store.root)
    stats = idx.rebuild_from_run_artifacts()

    # Also rebuild the recency index for fast "recent" endpoint
    recent_idx = AttachmentRecentIndex(store.root)
    recent_stats = recent_idx.rebuild_from_meta_index(idx)

    return IndexRebuildOut(ok=True, **stats)


@router.get("/index/attachment_meta/{sha256}/exists", response_model=AttachmentExistsOut)
def attachment_meta_exists(
    sha256: str,
    _auth: None = Depends(require_auth),
    store: RunStoreV2 = Depends(get_store),
) -> AttachmentExistsOut:
    """H7.2.2.1: Check both index presence and blob presence for an attachment."""
    idx = AttachmentMetaIndex(store.root)
    meta = idx.get(sha256)
    in_index = meta is not None

    p = resolve_attachment_path(sha256)
    in_store = p.exists()

    size_bytes = None
    if in_store:
        try:
            size_bytes = int(p.stat().st_size)
        except OSError:  # WP-1: narrowed from except Exception
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


# NOTE: facets/recent routes MUST be defined BEFORE /{sha256} to prevent FastAPI
# from matching "facets" or "recent" as sha256 values (path parameter matching)
@router.get("/index/attachment_meta/facets", response_model=AttachmentMetaFacetsOut)
def attachment_meta_facets(
    kind_prefix: Optional[str] = Query(
        default=None,
        description="Filter to kinds starting with this prefix"
    ),
    mime_prefix: Optional[str] = Query(
        default=None,
        description="Filter to MIME types starting with this prefix"
    ),
    size_buckets: bool = Query(
        default=True,
        description="Include size bucket counts"
    ),
    _auth: None = Depends(require_auth),
    store: RunStoreV2 = Depends(get_store),
) -> AttachmentMetaFacetsOut:
    """Facet counts for attachment meta index."""
    idx = AttachmentMetaIndex(store.root)
    entries = list(idx.list_all())

    # Apply filters (optional)
    if kind_prefix:
        entries = [e for e in entries if (e.get("kind") or "").startswith(kind_prefix)]
    if mime_prefix:
        entries = [e for e in entries if (e.get("mime") or "").startswith(mime_prefix)]

    total = len(entries)

    # Counts by kind
    kind_counts = Counter((e.get("kind") or "unknown") for e in entries)

    # MIME prefix grouping (first token + '/')
    def _mime_group(m: str) -> str:
        if not m:
            return "unknown"
        if "/" in m:
            return m.split("/", 1)[0] + "/"
        return m

    mime_prefix_counts = Counter(_mime_group(e.get("mime") or "") for e in entries)
    mime_exact_counts = Counter((e.get("mime") or "unknown") for e in entries)

    # Size buckets
    bucket_counts: Counter = Counter()
    if size_buckets:
        for e in entries:
            n = int(e.get("size_bytes") or 0)
            if n < 100_000:
                bucket_counts["lt_100kb"] += 1
            elif n < 1_000_000:
                bucket_counts["100kb_1mb"] += 1
            elif n < 20_000_000:
                bucket_counts["1mb_20mb"] += 1
            else:
                bucket_counts["ge_20mb"] += 1

    return AttachmentMetaFacetsOut(
        total=total,
        kinds=[{"kind": k, "count": c} for k, c in kind_counts.most_common()],
        mime_prefixes=[{"mime_prefix": k, "count": c} for k, c in mime_prefix_counts.most_common()],
        mime_exact=[{"mime": k, "count": c} for k, c in mime_exact_counts.most_common()],
        size_buckets=[{"bucket": k, "count": c} for k, c in bucket_counts.items()] if size_buckets else [],
        note="Counts computed from _attachment_meta.json. No paths disclosed.",
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


@router.get("/index/attachment_meta", response_model=AttachmentMetaBrowseOut)
def list_attachment_meta_from_index(
    *,
    kind: Optional[str] = Query(
        default=None,
        description="Exact match on attachment kind (e.g., spectrum_csv, audio_raw, manifest)"
    ),
    mime_prefix: Optional[str] = Query(
        default=None,
        description="Prefix match on MIME (e.g., image/, audio/, application/json)"
    ),
    limit: int = Query(
        default=200,
        ge=1,
        le=1000,
        description="Max rows to return (1..1000)"
    ),
    cursor: Optional[str] = Query(
        default=None,
        min_length=64,
        max_length=64,
        description="Pagination cursor: the last sha256 from a previous response. Returns results AFTER this item."
    ),
    include_urls: bool = Query(
        default=False,
        description="If true, include attachment_url pointing to /api/rmos/acoustics/attachments/{sha256}"
    ),
    signed_urls: bool = Query(
        default=False,
        description="If true, include signed query params (sig/expires) in attachment_url. Requires server secret."
    ),
    url_ttl_s: int = Query(
        default=300,
        ge=30,
        le=3600,
        description="TTL in seconds for signed URLs (default 300). Ignored when signed_urls=false."
    ),
    url_scope: str = Query(
        default="download",
        pattern="^(download|head)$",
        description="Signed URL scope: 'download' (GET) or 'head' (HEAD metadata only)."
    ),
    _auth: None = Depends(require_auth),
    store: RunStoreV2 = Depends(get_store),
) -> AttachmentMetaBrowseOut:
    """Browse the global sha256->meta index (no run_id required, no path disclosure)."""
    idx = AttachmentMetaIndex(store.root)
    items = idx.list_all()

    total_in_index = len(items)

    # Normalize filters
    want_kind = kind.strip() if isinstance(kind, str) and kind.strip() else None
    want_mime_prefix = mime_prefix.strip() if isinstance(mime_prefix, str) and mime_prefix.strip() else None

    # Filter entries
    if want_kind is not None:
        items = [it for it in items if it.get("kind") == want_kind]
    if want_mime_prefix is not None:
        items = [it for it in items if (it.get("mime") or "").startswith(want_mime_prefix)]

    # Sort by last_seen_at_utc descending (newest first), then by sha256 for stability
    def sort_key(m: Dict[str, Any]) -> tuple:
        return (m.get("last_seen_at_utc") or m.get("created_at_utc") or "", m.get("sha256") or "")

    items.sort(key=sort_key, reverse=True)

    # Cursor pagination
    page, next_cursor = apply_cursor_pagination(items, cursor=cursor, limit=limit)

    # URL enrichment (optional)
    enrich_with_urls(
        page,
        include_urls=include_urls,
        signed_urls=signed_urls,
        url_ttl_s=url_ttl_s,
        url_scope=url_scope,
    )

    # Convert to typed entries
    entries = [AttachmentMetaIndexEntry(**m) for m in page]

    return AttachmentMetaBrowseOut(
        count=len(entries),
        total_in_index=total_in_index,
        limit=limit,
        kind_filter=want_kind,
        mime_prefix_filter=want_mime_prefix,
        next_cursor=next_cursor,
        entries=entries,
    )


# NOTE: /recent route MUST also be defined BEFORE /{sha256} - it's already in the
# correct position relative to /facets above, but we add this note for clarity.
@router.get("/index/attachment_meta/recent", response_model=AttachmentMetaRecentOut)
def attachment_meta_recent(
    kind: Optional[str] = Query(
        default=None,
        description="Exact match on attachment kind (e.g., audio_raw, plot_png)"
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=200,
        description="Max entries to return (1..200)"
    ),
    cursor: Optional[str] = Query(
        default=None,
        min_length=64,
        max_length=64,
        description="Pagination cursor: the last sha256 from a previous response"
    ),
    include_urls: bool = Query(
        default=False,
        description="Include attachment_url pointing to /api/rmos/acoustics/attachments/{sha256}"
    ),
    signed_urls: bool = Query(
        default=False,
        description="Include signed URLs (requires include_urls=True implicitly)"
    ),
    url_ttl_s: int = Query(
        default=300,
        ge=60,
        le=86400,
        description="TTL for signed URLs in seconds (60..86400)"
    ),
    url_scope: Literal["download", "head"] = Query(
        default="download",
        description="Scope for signed URLs"
    ),
    _auth: None = Depends(require_auth),
    store: RunStoreV2 = Depends(get_store),
) -> AttachmentMetaRecentOut:
    """Recent attachments from precomputed recency index."""
    recent_idx = AttachmentRecentIndex(store.root)
    entries = recent_idx.list_entries()

    # Filter by kind (exact match)
    want_kind = kind.strip() if isinstance(kind, str) and kind.strip() else None
    if want_kind is not None:
        entries = [e for e in entries if e.get("kind") == want_kind]

    # Cursor pagination
    page, next_cursor = apply_cursor_pagination(entries, cursor=cursor, limit=limit)

    # URL enrichment (optional)
    enrich_with_urls(
        page,
        include_urls=include_urls,
        signed_urls=signed_urls,
        url_ttl_s=url_ttl_s,
        url_scope=url_scope,
    )

    # Convert to typed entries
    out_entries = [AttachmentMetaIndexEntry(**e) for e in page]

    return AttachmentMetaRecentOut(
        count=len(out_entries),
        limit=limit,
        kind_filter=want_kind,
        next_cursor=next_cursor,
        entries=out_entries,
    )
