# services/api/app/advisory/blob_router.py
"""
Advisory Blob Download Endpoint

Serves CAS-stored image bytes for browser-loadable <img src="..."> tags.
This endpoint requires no auth and returns raw image bytes.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

from app.rmos.runs_v2.attachments import get_bytes_attachment

router = APIRouter(prefix="/api/advisory/blobs", tags=["Advisory", "Blobs"])


def _detect_mime(data: bytes) -> str:
    """Detect MIME type from magic bytes."""
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if data[:2] == b"\xff\xd8":
        return "image/jpeg"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    return "application/octet-stream"


@router.get("/{sha256}/download")
def download_blob(
    sha256: str,
    mime: Optional[str] = Query(None, description="Optional MIME type hint"),
) -> Response:
    """
    Download raw bytes of a CAS-stored advisory asset.

    This endpoint is used by <img src="..."> tags to render AI-generated images.
    Returns the raw image bytes with appropriate MIME type.
    """
    # Read bytes from CAS
    data = get_bytes_attachment(sha256)
    if data is None:
        raise HTTPException(status_code=404, detail="BLOB_NOT_FOUND")

    # Detect or use provided mime
    content_type = mime or _detect_mime(data)

    return Response(
        content=data,
        media_type=content_type,
        headers={
            "Cache-Control": "public, max-age=31536000, immutable",  # CAS content is immutable
            "Content-Disposition": f'inline; filename="{sha256[:12]}.png"',
        }
    )
