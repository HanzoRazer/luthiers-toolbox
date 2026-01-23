# services/api/app/vision/schemas.py
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

ProviderName = Literal["openai", "stub"]


class VisionGenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    provider: ProviderName = Field("openai")
    model: Optional[str] = Field(None, description="Provider model name (optional)")
    size: str = Field("1024x1024", description="e.g. 1024x1024")
    quality: str = Field("standard", description="e.g. standard|hd (provider dependent)")
    num_images: int = Field(1, ge=1, le=8)
    meta: Optional[Dict[str, Any]] = Field(None, description="Optional caller metadata")


class VisionAsset(BaseModel):
    sha256: str = Field(..., description="CAS sha256 of the stored image bytes")
    url: str = Field(..., description="Browser-loadable URL for the asset bytes (proxied by API)")
    mime: str = Field(..., description="MIME type")
    filename: str = Field(..., description="Best-effort filename for UI download")
    size_bytes: int = Field(..., description="Byte size")
    provider: str = Field(..., description="Provider name")
    model: str = Field(..., description="Model used")
    revised_prompt: Optional[str] = None
    request_id: str = Field("", description="X-Request-Id header value (if available)")


class VisionGenerateResponse(BaseModel):
    assets: List[VisionAsset]
    request_id: str = Field("", description="X-Request-Id header value (if available)")


class VisionPromptPreviewRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    style: Optional[str] = Field(None, description="Photography style (optional)")
    include_variations: bool = Field(False, description="Reserved for future use")


class VisionPromptPreviewResponse(BaseModel):
    raw_prompt: str
    engineered_prompt: str
    photography_style: Optional[str] = None


class VisionVocabularyResponse(BaseModel):
    vocabulary: Dict[str, List[str]]
