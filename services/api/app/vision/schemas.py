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


class SegmentRequest(BaseModel):
    """Request for guitar body segmentation."""
    target_width_mm: float = Field(400.0, ge=50.0, le=1000.0, description="Target body width in mm")
    simplify_tolerance_mm: float = Field(1.0, ge=0.0, le=10.0, description="Simplification tolerance in mm")
    guitar_category: GuitarCategory = Field("auto", description="Guitar type hint for better detection")
    output_format: OutputFormat = Field("json", description="Output format(s)")


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


class PhotoToGcodeRequest(BaseModel):
    """Request for photo-to-gcode pipeline."""
    target_width_mm: float = Field(400.0, ge=50.0, le=1000.0, description="Target body width in mm")
    simplify_tolerance_mm: float = Field(1.0, ge=0.0, le=10.0, description="Simplification tolerance")
    guitar_category: GuitarCategory = Field("auto", description="Guitar type hint")
    # CAM parameters
    tool_diameter_mm: float = Field(6.0, ge=1.0, le=25.0, description="Tool diameter in mm")
    stepover: float = Field(0.45, ge=0.2, le=0.8, description="Stepover as fraction of tool diameter")
    stepdown_mm: float = Field(2.0, ge=0.5, le=10.0, description="Stepdown per pass in mm")
    feed_rate_mm_min: float = Field(1200.0, ge=100.0, le=5000.0, description="Feed rate mm/min")
    post_processor: str = Field("GRBL", description="Post processor: GRBL, Mach4, LinuxCNC")


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
