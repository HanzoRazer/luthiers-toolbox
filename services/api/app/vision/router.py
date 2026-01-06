# services/api/app/vision/router.py
"""
Vision Producer Plane - Canonical API for AI Image Generation

This module provides the producer plane for the hybrid architecture:
- Generates assets via AI providers
- Writes to CAS (Content-Addressed Storage)
- Returns sha256 as the authoritative identity

The Ledger Plane (RMOS) handles attach/review/promote governance.
"""
from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.ai.transport import get_image_client
from app.rmos.runs_v2.attachments import put_bytes_attachment
from app.vision.schemas import VisionAsset, VisionGenerateRequest, VisionGenerateResponse

router = APIRouter(prefix="/api/vision", tags=["Vision"])


class ProvidersResponse(BaseModel):
    providers: List[Dict[str, Any]]


def _extract_request_id(req: Request) -> str:
    return req.headers.get("x-request-id") or ""


def _format_to_mime(fmt: str) -> str:
    """Convert format string to MIME type."""
    mapping = {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "webp": "image/webp",
    }
    return mapping.get(fmt.lower(), "image/png")


def _filename(provider: str, model: str, size: str, fmt: str, i: int) -> str:
    ext = f".{fmt}" if fmt else ".png"
    safe_model = (model or "model").replace("/", "_").replace(" ", "_")
    return f"vision_{provider}_{safe_model}_{size}_{i+1}{ext}"


def _blob_download_url(sha256: str) -> str:
    """Return browser-loadable URL for CAS blob (same-origin, no auth required)."""
    return f"/api/advisory/blobs/{sha256}/download"


@router.get("/providers", response_model=ProvidersResponse)
def list_providers() -> ProvidersResponse:
    """List available AI image providers and their configuration status."""
    providers = []
    for name in ("openai", "stub"):
        try:
            c = get_image_client(provider=name)
            configured = bool(getattr(c, "is_configured", True))
        except Exception:
            configured = False
        providers.append({"name": name, "configured": configured})
    return ProvidersResponse(providers=providers)


@router.post("/generate", response_model=VisionGenerateResponse)
def generate(req: Request, payload: VisionGenerateRequest) -> VisionGenerateResponse:
    """
    Generate images via AI provider and store in CAS.

    Returns assets with sha256 identity for subsequent RMOS attachment.
    """
    request_id = _extract_request_id(req)

    try:
        client = get_image_client(provider=payload.provider)
    except Exception as e:
        raise HTTPException(status_code=409, detail=f"AI_PROVIDER_NOT_CONFIGURED: {payload.provider}") from e

    if getattr(client, "is_configured", True) is False:
        raise HTTPException(status_code=409, detail=f"AI_PROVIDER_NOT_CONFIGURED: {payload.provider}")

    assets: List[VisionAsset] = []

    for i in range(payload.num_images):
        try:
            # Use the canonical .generate() method from ImageClient
            response = client.generate(
                prompt=payload.prompt,
                model=payload.model,
                size=payload.size,
                quality=payload.quality,
            )
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"AI_PROVIDER_UNAVAILABLE: {str(e)}") from e

        # Extract from ImageResponse dataclass
        img_bytes = response.image_bytes
        fmt = response.format or "png"
        mime = _format_to_mime(fmt)
        model_used = response.model or payload.model or ""
        revised_prompt = response.revised_prompt

        # CAS store via canonical RMOS attachments module (content-addressed)
        try:
            attachment, _storage_path = put_bytes_attachment(
                img_bytes,
                kind="advisory",
                mime=mime,
                filename=_filename(payload.provider, model_used, payload.size, fmt, i),
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"CAS_WRITE_FAILED: {str(e)}") from e

        assets.append(
            VisionAsset(
                sha256=attachment.sha256,
                url=_blob_download_url(attachment.sha256),
                mime=attachment.mime,
                filename=attachment.filename,
                size_bytes=attachment.size_bytes,
                provider=str(payload.provider),
                model=model_used,
                revised_prompt=revised_prompt,
                request_id=request_id,
            )
        )

    return VisionGenerateResponse(assets=assets, request_id=request_id)
