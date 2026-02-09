"""RMOS Acoustics Router - Read-only advisory surface."""
from __future__ import annotations

import base64
import os
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import FileResponse

from .store import RunStoreV2
from .attachments import resolve_attachment_path
from .signed_urls import make_signed_query, verify_attachment_request, Scope
from .attachment_meta import AttachmentMetaIndex, AttachmentRecentIndex
from .acoustics_helpers import enrich_with_urls, apply_cursor_pagination
from .acoustics_schemas import (
    AttachmentMetaPublic,
    AttachmentMetaIndexEntry,
    AttachmentMetaBrowseOut,
    AttachmentMetaFacetsOut,
    AttachmentMetaRecentOut,
    RunAttachmentsListOut,
    AttachmentExistsOut,
    SignedUrlMintOut,
    RunAdvisoriesListOut,
    AdvisorySummary,
    IndexRebuildOut,
    RunSummary,
    RunsBrowseOut,
    RunDetailOut,
)

router = APIRouter()

# -----
# Dependencies
# -----

def require_auth() -> None:
    """Placeholder for auth gating."""
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
    """If a valid signed URL is present, allow without normal auth."""
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

# -----
# Endpoints
# -----

# --- Runs Browse (Session/Run-centric Library) ---

@router.get("/runs", response_model=RunsBrowseOut)
def browse_runs(
    limit: int = Query( default=20, ge=1, le=100, description="Max runs to return (1..100)" ),
    cursor: Optional[str] = Query( default=None, description="Pagination cursor (created_at_utc|run_id from previous response)" ),
    session_id: Optional[str] = Query( default=None, description="Filter by session_id (exact match)" ),
    batch_label: Optional[str] = Query( default=None, description="Filter by batch_label (exact match)" ),
    include_urls: bool = Query( default=False, description="Include attachment URLs in viewer_pack entries" ),
    _auth: None = Depends(require_auth),
    store: RunStoreV2 = Depends(get_store),
) -> RunsBrowseOut:
    """Browse runs with pagination."""
    # Fetch more than needed for filtering
    fetch_limit = limit * 4 + 50

    runs = store.list_runs(limit=fetch_limit)

    # Sort by created_at_utc descending
    def _sort_key(r):
        ts = r.created_at_utc.isoformat() if hasattr(r.created_at_utc, "isoformat") else str(r.created_at_utc)
        return (ts, r.run_id)

    runs = sorted(runs, key=_sort_key, reverse=True)

    # Cursor pagination: skip entries until we pass the cursor
    if cursor:
        try:
            cursor_ts, cursor_rid = cursor.split("|", 1)
            found_cursor = False
            filtered = []
            for r in runs:
                ts = r.created_at_utc.isoformat() if hasattr(r.created_at_utc, "isoformat") else str(r.created_at_utc)
                if found_cursor:
                    filtered.append(r)
                elif ts == cursor_ts and r.run_id == cursor_rid:
                    found_cursor = True
                elif ts < cursor_ts:
                    # Older than cursor, include
                    filtered.append(r)
            runs = filtered
        except (ValueError, TypeError, AttributeError):  # WP-1: narrowed from except Exception
            pass  # Invalid cursor, ignore

    # Filter by session_id
    want_session = session_id.strip() if session_id and session_id.strip() else None
    if want_session:
        runs = [r for r in runs if (r.meta.get("session_id") or r.workflow_session_id) == want_session]

    # Filter by batch_label
    want_batch = batch_label.strip() if batch_label and batch_label.strip() else None
    if want_batch:
        runs = [r for r in runs if r.meta.get("batch_label") == want_batch]

    # Take page
    page = runs[:limit]

    # Build next_cursor
    next_cursor = None
    if len(runs) > limit and page:
        last = page[-1]
        ts = last.created_at_utc.isoformat() if hasattr(last.created_at_utc, "isoformat") else str(last.created_at_utc)
        next_cursor = f"{ts}|{last.run_id}"

    # Build summaries
    summaries = []
    for r in page:
        attachments = r.attachments or []
        kinds = list(set(a.kind for a in attachments if a.kind))
        viewer_packs = [a for a in attachments if a.kind == "viewer_pack"]
        primary_vp = viewer_packs[0].sha256 if viewer_packs else None

        summaries.append(RunSummary(
            run_id=r.run_id,
            created_at_utc=r.created_at_utc.isoformat() if hasattr(r.created_at_utc, "isoformat") else str(r.created_at_utc),
            mode=r.mode,
            status=r.status,
            session_id=r.meta.get("session_id") or r.workflow_session_id,
            batch_label=r.meta.get("batch_label"),
            event_type=r.event_type,
            attachment_count=len(attachments),
            viewer_pack_count=len(viewer_packs),
            kinds_present=sorted(kinds),
            primary_viewer_pack_sha256=primary_vp,
        ))

    return RunsBrowseOut(
        count=len(summaries),
        limit=limit,
        session_id_filter=want_session,
        batch_label_filter=want_batch,
        next_cursor=next_cursor,
        runs=summaries,
    )

@router.get("/runs/{run_id}", response_model=RunDetailOut)
def get_run_detail(
    run_id: str,
    include_urls: bool = Query( default=True, description="Include attachment_url for each attachment" ),
    _auth: None = Depends(require_auth),
    store: RunStoreV2 = Depends(get_store),
) -> RunDetailOut:
    """
    Get detailed run metadata + attachments.

    Returns full run context with attachment list.
    """
    artifact = store.get(run_id)
    if not artifact:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")

    attachments_raw = artifact.attachments or []

    # Build attachment list
    attachment_list = []
    for a in attachments_raw:
        pub = AttachmentMetaPublic(
            sha256=a.sha256,
            kind=a.kind,
            mime=a.mime,
            filename=a.filename,
            size_bytes=a.size_bytes,
            created_at_utc=a.created_at_utc,
        )
        if include_urls:
            pub.download_url = f"/api/rmos/acoustics/attachments/{a.sha256}"
        attachment_list.append(pub)

    return RunDetailOut(
        run_id=artifact.run_id,
        created_at_utc=artifact.created_at_utc.isoformat() if hasattr(artifact.created_at_utc, "isoformat") else str(artifact.created_at_utc),
        mode=artifact.mode,
        status=artifact.status,
        tool_id=artifact.tool_id,
        session_id=artifact.meta.get("session_id") or artifact.workflow_session_id,
        batch_label=artifact.meta.get("batch_label"),
        event_type=artifact.event_type,
        request_summary=artifact.request_summary,
        meta=artifact.meta,
        attachment_count=len(attachment_list),
        attachments=attachment_list,
    )

@router.get("/runs/{run_id}/advisories", response_model=RunAdvisoriesListOut)
def list_run_advisories(
    run_id: str,
    _auth: None = Depends(require_auth),
    store: RunStoreV2 = Depends(get_store),
) -> RunAdvisoriesListOut:
    """List advisory summaries for a run."""
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
    """Resolve advisory_id -> lookup entry (includes sha256 + run_id + metadata)."""
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
    """Stream an attachment blob by sha256 from the content-addressed store."""
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
    """HEAD metadata for an attachment blob."""
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
    """Mint a temporary signed URL for downloading/streaming an attachment."""
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
    """Return attachments for a run with inline bytes (base64), plus mime/kind."""
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
                except OSError:  # WP-1: narrowed from except Exception
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
                    except OSError:  # WP-1: narrowed from except Exception
                        item["omitted_reason"] = "read_failed"

        out_items.append(AttachmentMetaPublic(**item))

    return RunAttachmentsListOut(
        run_id=run_id,
        count=len(out_items),
        include_bytes=include_bytes,
        max_inline_bytes=int(max_inline_bytes),
        attachments=out_items,
    )

# -----
# Attachment Index endpoints (facets, browse, recent, exists, rebuild)
# Extracted to acoustics_index_routes.py — included as sub-router below
# -----
from .acoustics_index_routes import router as _index_router  # noqa: E402

router.include_router(_index_router)

# Re-export for backward compatibility
from .acoustics_index_routes import (rebuild_attachment_meta_index, attachment_meta_exists, attachment_meta_facets, get_attachment_meta_from_index, list_attachment_meta_from_index, attachment_meta_recent)  # noqa: E402, F401
