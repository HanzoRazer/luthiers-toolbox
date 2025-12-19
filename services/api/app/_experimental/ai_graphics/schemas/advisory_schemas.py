"""
Advisory Asset Schemas

AI-generated content that requires human review before workflow integration.
These assets live in the ADVISORY ZONE and cannot directly create run artifacts.

Integrates with existing:
- image_providers.py (AiImageResult, GuitarVisionEngine)
- image_transport.py (OpenAIImageTransport)
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class AdvisoryAssetType(str, Enum):
    """Types of AI-generated advisory content."""
    IMAGE = "image"
    SUGGESTION = "suggestion"
    ANALYSIS = "analysis"
    PATTERN = "pattern"


class AdvisoryAsset(BaseModel):
    """
    AI-generated content that requires human review before use.
    
    GOVERNANCE: AI produces AdvisoryAsset, not RunArtifact.
    Human review required before workflow integration.
    """
    
    asset_id: str = Field(default_factory=lambda: f"adv_{uuid4().hex[:12]}")
    asset_type: AdvisoryAssetType
    created_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Source tracking
    source: Literal["ai_graphics", "ai_analysis", "ai_suggestion"] = "ai_graphics"
    provider: str  # dalle3, sdxl, stub
    model: str     # dall-e-3, sd-xl-base-1.0
    
    # Content
    prompt: str
    content_hash: str
    content_uri: Optional[str] = None
    content_size_bytes: Optional[int] = None
    
    # Image-specific
    image_width: Optional[int] = None
    image_height: Optional[int] = None
    image_format: Optional[str] = None
    
    # Suggestion-specific
    suggestion_data: Optional[Dict[str, Any]] = None
    
    # Metadata
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    warnings: List[str] = Field(default_factory=list)
    generation_time_ms: Optional[int] = None
    cost_usd: Optional[float] = None
    
    # Governance state
    reviewed: bool = False
    approved_for_workflow: bool = False
    reviewed_by: Optional[str] = None
    reviewed_at_utc: Optional[datetime] = None
    review_note: Optional[str] = None
    
    meta: Dict[str, Any] = Field(default_factory=dict)


class AdvisoryAssetRef(BaseModel):
    """Lightweight reference for linking to runs."""
    asset_id: str
    asset_type: AdvisoryAssetType
    attached_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    attached_by: str
    was_reviewed: bool = False
    was_approved: bool = False


class AdvisoryAssetOut(BaseModel):
    """API response model."""
    asset_id: str
    asset_type: str
    created_at_utc: str
    source: str
    provider: str
    model: str
    prompt: str
    content_hash: str
    content_uri: Optional[str] = None
    confidence: Optional[float] = None
    warnings: List[str] = []
    generation_time_ms: Optional[int] = None
    cost_usd: Optional[float] = None
    reviewed: bool
    approved_for_workflow: bool
    reviewed_by: Optional[str] = None
    reviewed_at_utc: Optional[str] = None

    @classmethod
    def from_asset(cls, asset: AdvisoryAsset) -> "AdvisoryAssetOut":
        return cls(
            asset_id=asset.asset_id,
            asset_type=asset.asset_type.value,
            created_at_utc=asset.created_at_utc.isoformat(),
            source=asset.source,
            provider=asset.provider,
            model=asset.model,
            prompt=asset.prompt,
            content_hash=asset.content_hash,
            content_uri=asset.content_uri,
            confidence=asset.confidence,
            warnings=asset.warnings,
            generation_time_ms=asset.generation_time_ms,
            cost_usd=asset.cost_usd,
            reviewed=asset.reviewed,
            approved_for_workflow=asset.approved_for_workflow,
            reviewed_by=asset.reviewed_by,
            reviewed_at_utc=asset.reviewed_at_utc.isoformat() if asset.reviewed_at_utc else None,
        )


# Request/Response models for API
class GenerateImageRequest(BaseModel):
    """Request for advisory image generation."""
    prompt: str
    size: str = "1024x1024"
    quality: str = "standard"
    photo_style: str = "product"
    provider: Optional[str] = None


class GenerateImageResponse(BaseModel):
    """Response from advisory image generation."""
    asset: AdvisoryAssetOut
    message: str = "Image generated. Requires human review before workflow use."


class ReviewAssetRequest(BaseModel):
    """Request to review an asset."""
    approved: bool
    reviewer: str
    note: Optional[str] = None


class ListAssetsResponse(BaseModel):
    """Response for listing assets."""
    assets: List[AdvisoryAssetOut]
    total: int
    pending_review: int
