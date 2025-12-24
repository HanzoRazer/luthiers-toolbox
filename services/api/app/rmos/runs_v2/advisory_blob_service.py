"""
RMOS Advisory Blob Service - Bundles:
- RMOS_ADVISORY_BLOB_BROWSER_V1
- RMOS_ADVISORY_BLOB_MIME_FILENAME_INFERENCE_V1
- RMOS_SVG_PREVIEW_SAFETY_GATE_V1

Run-scoped advisory blob operations:
- Authority: run.advisory_inputs[*].advisory_id is the authoritative CAS key list
- Download/preview/zip: only for sha256 values present in that list
- Includes mime sniffing, filename inference, and SVG preview safety checks
"""

from __future__ import annotations

import os
import tempfile
import zipfile
import mimetypes
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, Response

from .store import get_run
from .attachments import get_attachment_path, get_bytes_attachment
from .advisory_blob_schemas import AdvisoryBlobRef, SvgPreviewStatusResponse


# =============================================================================
# HELPERS: Run / Authorization
# =============================================================================

def _run_or_404(run_id: str):
    """Load run or raise 404."""
    run = get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


def _authorized_advisory_ids(run: Any) -> List[str]:
    """
    HEAD truth: run.advisory_inputs[*].advisory_id is the authoritative CAS key list.
    """
    refs = getattr(run, "advisory_inputs", None) or []
    out: List[str] = []
    for r in refs:
        adv_id = getattr(r, "advisory_id", None)
        if isinstance(adv_id, str) and adv_id:
            out.append(adv_id)
    return out


def _find_ref(run: Any, sha256: str) -> Optional[Any]:
    """Find an advisory ref by sha256."""
    refs = getattr(run, "advisory_inputs", None) or []
    for r in refs:
        if getattr(r, "advisory_id", None) == sha256:
            return r
    return None


def _assert_authorized(run: Any, sha256: str) -> Any:
    """Assert sha256 is authorized (linked to run) or raise 404."""
    ref = _find_ref(run, sha256)
    if ref is None:
        raise HTTPException(status_code=404, detail="Advisory blob not linked to this run")
    return ref


def _resolve_blob_path(sha256: str) -> str:
    """
    Advisory blobs are CAS by sha256. Resolve via attachments CAS path.
    If your advisory blob store diverges physically later, swap this function only.
    """
    path = get_attachment_path(sha256)
    if not path:
        raise HTTPException(status_code=404, detail="Blob not found for advisory_id (CAS missing)")
    return path


# =============================================================================
# HELPERS: Mime Sniffing + Filename Inference
# =============================================================================

def _read_head_bytes(sha256: str, max_bytes: int = 4096) -> bytes:
    """
    Read first N bytes of a CAS blob for sniffing.
    Uses get_bytes_attachment when available; otherwise reads from resolved path.
    """
    b = get_bytes_attachment(sha256)
    if b is not None:
        return b[:max_bytes]

    path = get_attachment_path(sha256)
    if not path:
        return b""
    try:
        with open(path, "rb") as f:
            return f.read(max_bytes)
    except Exception:
        return b""


def _sniff_mime(sha256: str, fallback_filename: Optional[str] = None) -> str:
    """
    High-signal, low-dependency sniffing:
    - SVG: starts with '<' + contains '<svg'
    - JSON: starts with '{' or '['
    - Otherwise: guess from filename extension if available
    - Else: octet-stream
    """
    head = _read_head_bytes(sha256, 4096).lstrip()
    if not head:
        # no bytes available; fall back to filename guessing
        if fallback_filename:
            mt, _ = mimetypes.guess_type(fallback_filename)
            return mt or "application/octet-stream"
        return "application/octet-stream"

    # SVG sniff
    if head.startswith(b"<") and b"<svg" in head.lower():
        return "image/svg+xml"

    # JSON sniff
    if head.startswith(b"{") or head.startswith(b"["):
        return "application/json"

    # Filename-based guess (last resort)
    if fallback_filename:
        mt, _ = mimetypes.guess_type(fallback_filename)
        if mt:
            return mt

    return "application/octet-stream"


def _default_extension_for_mime(mime: str) -> str:
    """Get default file extension for a mime type."""
    m = (mime or "").lower()
    if m == "image/svg+xml":
        return ".svg"
    if m == "application/json":
        return ".json"
    # attempt standard mappings
    ext = mimetypes.guess_extension(m) or ""
    return ext if ext.startswith(".") else ""


def _infer_filename(sha256: str, kind: Optional[str], mime: str) -> str:
    """
    Stable human-friendly filename for downloads/zip when ref.filename missing.
    """
    ext = _default_extension_for_mime(mime)
    k = (kind or "").strip().lower()

    base = sha256[:12]
    if k:
        # kind helps operator context
        return f"{k}_{base}{ext or '.bin'}"
    return f"{base}{ext or '.bin'}"


def _normalize_ref_fields(run_ref: Any, sha256: str) -> Dict[str, Optional[str]]:
    """
    Produces robust kind/title/mime/filename for UI + headers.
    Does not mutate stored data; it's presentation-level normalization.
    """
    kind = getattr(run_ref, "kind", None)
    title = getattr(run_ref, "title", None)
    filename = getattr(run_ref, "filename", None)
    mime = getattr(run_ref, "mime", None)

    # If filename exists but mime doesn't, guess mime from filename first
    if filename and not mime:
        guessed, _ = mimetypes.guess_type(filename)
        mime = guessed

    # Sniff mime if still missing/empty
    if not mime:
        mime = _sniff_mime(sha256, fallback_filename=filename)

    # Infer filename if missing
    if not filename:
        filename = _infer_filename(sha256, kind, mime)

    return {
        "kind": kind,
        "title": title,
        "mime": mime,
        "filename": filename,
    }


# =============================================================================
# HELPERS: SVG Preview Safety
# =============================================================================

def _svg_preview_is_safe(svg_bytes: bytes) -> Tuple[bool, str, Optional[str]]:
    """
    Preview-only safety gate.
    - Blocks <script> and <foreignObject> to prevent scriptable/HTML content in inline preview.
    - Blocks <image> to avoid embedded/external image payloads in preview.
    Download remains allowed regardless.

    Returns: (is_safe, reason_if_blocked, blocked_by_tag)
    """
    try:
        text = svg_bytes.decode("utf-8", errors="strict")
    except Exception:
        return (False, "SVG preview requires UTF-8 SVG content", "encoding")

    lower = text.lower()

    if "<script" in lower:
        return (False, "SVG preview blocked: <script> detected", "script")
    if "foreignobject" in lower:
        return (False, "SVG preview blocked: <foreignObject> detected", "foreignObject")
    if "<image" in lower:
        return (False, "SVG preview blocked: <image> detected", "image")

    return (True, "", None)


# =============================================================================
# SERVICE FUNCTIONS
# =============================================================================

def list_advisory_blobs(run_id: str) -> List[AdvisoryBlobRef]:
    """
    List all advisory blobs linked to a run.
    Source of truth: run.advisory_inputs[*].advisory_id
    """
    run = _run_or_404(run_id)
    refs = getattr(run, "advisory_inputs", None) or []

    items: List[AdvisoryBlobRef] = []
    for r in refs:
        advisory_id = getattr(r, "advisory_id", None)
        if not advisory_id:
            continue

        norm = _normalize_ref_fields(r, advisory_id)

        items.append(
            AdvisoryBlobRef(
                advisory_id=advisory_id,
                kind=norm["kind"],
                title=norm["title"],
                mime=norm["mime"],
                filename=norm["filename"],
            )
        )
    return items


def download_advisory_blob(run_id: str, sha256: str) -> FileResponse:
    """
    Download an advisory blob by sha256.
    Only allowed if sha256 is linked to this run's advisory_inputs.
    """
    run = _run_or_404(run_id)
    ref = _assert_authorized(run, sha256)

    path = _resolve_blob_path(sha256)

    norm = _normalize_ref_fields(ref, sha256)
    filename = norm["filename"] or f"{sha256}"
    mime = norm["mime"] or "application/octet-stream"

    return FileResponse(path=path, media_type=mime, filename=filename)


def preview_svg(run_id: str, sha256: str) -> Response:
    """
    Inline SVG preview (artifact-authorized).
    - Only for blobs linked to the run.
    - Only if mime is SVG-ish.
    - Applies safety gate (blocks script/foreignObject/image).
    - Returns SVG bytes as image/svg+xml (safe for <img> or <object> embed).
    """
    run = _run_or_404(run_id)
    ref = _assert_authorized(run, sha256)

    norm = _normalize_ref_fields(ref, sha256)
    mime = (norm["mime"] or "").lower()
    if mime not in ("image/svg+xml", "image/svg", "text/svg+xml"):
        raise HTTPException(status_code=415, detail=f"Not SVG (mime={norm['mime']})")

    b = get_bytes_attachment(sha256)
    if b is None:
        path = _resolve_blob_path(sha256)
        b = Path(path).read_bytes()

    # Preview-only safety gate (download endpoint remains unchanged)
    ok, reason, blocked_by = _svg_preview_is_safe(b)
    if not ok:
        raise HTTPException(status_code=415, detail=reason)

    return Response(content=b, media_type="image/svg+xml")


def check_svg_preview_status(run_id: str, sha256: str) -> SvgPreviewStatusResponse:
    """
    Check if SVG preview is available and safe.
    Returns status response instead of raising exception.
    Useful for UI to show friendly message.
    """
    run = _run_or_404(run_id)
    ref = _find_ref(run, sha256)

    if ref is None:
        return SvgPreviewStatusResponse(
            run_id=run_id,
            advisory_id=sha256,
            ok=False,
            reason="Advisory blob not linked to this run",
            action="none",
        )

    norm = _normalize_ref_fields(ref, sha256)
    mime = (norm["mime"] or "").lower()

    if mime not in ("image/svg+xml", "image/svg", "text/svg+xml"):
        return SvgPreviewStatusResponse(
            run_id=run_id,
            advisory_id=sha256,
            ok=False,
            mime=norm["mime"],
            reason=f"Not SVG (mime={norm['mime']})",
            blocked_by="not_svg",
            action="download",
        )

    b = get_bytes_attachment(sha256)
    if b is None:
        try:
            path = _resolve_blob_path(sha256)
            b = Path(path).read_bytes()
        except HTTPException:
            return SvgPreviewStatusResponse(
                run_id=run_id,
                advisory_id=sha256,
                ok=False,
                mime=norm["mime"],
                reason="Blob not found in CAS",
                action="none",
            )

    ok, reason, blocked_by = _svg_preview_is_safe(b)

    return SvgPreviewStatusResponse(
        run_id=run_id,
        advisory_id=sha256,
        ok=ok,
        mime=norm["mime"],
        reason=reason if not ok else None,
        blocked_by=blocked_by,
        action="preview" if ok else "download",
    )


def download_all_zip(run_id: str, background: BackgroundTasks) -> FileResponse:
    """
    Creates a zip containing all advisory blobs linked to the run.
    Authorization is run-scoped: only linked advisory_inputs are included.
    Uses a temp file and deletes it after response is sent.
    """
    run = _run_or_404(run_id)
    ids = _authorized_advisory_ids(run)
    if not ids:
        raise HTTPException(status_code=404, detail="No advisory blobs linked to this run")

    # Create temp zip
    fd, zip_path = tempfile.mkstemp(prefix=f"run_{run_id}_advisory_", suffix=".zip")
    os.close(fd)

    try:
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for sha in ids:
                path = _resolve_blob_path(sha)

                ref = _find_ref(run, sha)
                if ref:
                    norm = _normalize_ref_fields(ref, sha)
                else:
                    norm = {
                        "kind": "advisory",
                        "mime": _sniff_mime(sha),
                        "filename": _infer_filename(sha, "advisory", _sniff_mime(sha)),
                        "title": None,
                    }

                kind = (norm["kind"] or "advisory").strip() or "advisory"
                filename = norm["filename"] or f"{sha[:12]}.bin"

                zip_name = f"{kind}/{sha[:12]}_{filename}"
                zf.write(path, arcname=zip_name)

    except HTTPException:
        # clean temp zip before re-raising
        try:
            os.remove(zip_path)
        except Exception:
            pass
        raise
    except Exception as e:
        try:
            os.remove(zip_path)
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"Failed to build zip: {e}")

    # Delete after response
    background.add_task(lambda p=zip_path: os.path.exists(p) and os.remove(p))

    return FileResponse(
        path=zip_path,
        media_type="application/zip",
        filename=f"run_{run_id}_advisory_blobs.zip",
    )
