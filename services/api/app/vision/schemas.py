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


# ---------------------------------------------------------------------------
# Segmentation Schemas
# ---------------------------------------------------------------------------

GuitarCategory = Literal["auto", "acoustic", "electric"]
OutputFormat = Literal["json", "dxf", "svg", "all"]


# NOTE: SegmentRequest removed 2026-02-26 (dead code - endpoint uses Form() params)


class SegmentResponse(BaseModel):
    """Response from guitar body segmentation."""
    ok: bool = Field(..., description="Whether segmentation succeeded")
    polygon: List[List[float]] = Field(default_factory=list, description="Body outline as [[x,y], ...] in mm")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="AI confidence score")
    guitar_type: str = Field("unknown", description="Detected guitar type")
    point_count: int = Field(0, description="Number of points in polygon")
    target_width_mm: float = Field(0.0, description="Scaled width in mm")
    target_height_mm: float = Field(0.0, description="Scaled height in mm")
    notes: str = Field("", description="AI observations")
    error: Optional[str] = Field(None, description="Error message if failed")
    # Asset references (if output_format includes dxf/svg)
    dxf_sha256: Optional[str] = Field(None, description="SHA256 of DXF file in CAS")
    dxf_url: Optional[str] = Field(None, description="Download URL for DXF")
    svg_sha256: Optional[str] = Field(None, description="SHA256 of SVG file in CAS")
    svg_url: Optional[str] = Field(None, description="Download URL for SVG")


# NOTE: PhotoToGcodeRequest removed 2026-02-26 (dead code - endpoint uses Form() params)


class PhotoToGcodeResponse(BaseModel):
    """Response from photo-to-gcode pipeline."""
    ok: bool
    # Segmentation results
    confidence: float = 0.0
    guitar_type: str = "unknown"
    polygon_points: int = 0
    # Assets
    svg_preview_url: Optional[str] = None
    dxf_url: Optional[str] = None
    gcode_url: Optional[str] = None
    # CAM stats
    cam_stats: Optional[Dict[str, Any]] = None
    # Error
    error: Optional[str] = None
