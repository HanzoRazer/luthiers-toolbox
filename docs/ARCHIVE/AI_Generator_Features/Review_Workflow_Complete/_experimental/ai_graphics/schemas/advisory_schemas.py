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


class RejectionReason(str, Enum):
    """Standard rejection reasons for review workflow."""
    POOR_QUALITY = "poor_quality"
    WRONG_STYLE = "wrong_style"
    ANATOMICALLY_INCORRECT = "anatomically_incorrect"
    WRONG_GUITAR_TYPE = "wrong_guitar_type"
    WRONG_FINISH = "wrong_finish"
    WRONG_HARDWARE = "wrong_hardware"
    ARTIFACTS = "artifacts"
    LIGHTING_ISSUES = "lighting_issues"
    COMPOSITION = "composition"
    NOT_PHOTOREALISTIC = "not_photorealistic"
    DUPLICATE = "duplicate"
    OTHER = "other"


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
    rejection_reason: Optional[str] = None  # RejectionReason value if rejected
    rating: Optional[int] = Field(default=None, ge=1, le=5)  # Quality rating 1-5
    is_favorite: bool = False  # Bookmarked for later, separate from approval
    
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
    revised_prompt: Optional[str] = None  # DALL-E's rewritten version
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
    review_note: Optional[str] = None
    rejection_reason: Optional[str] = None
    rating: Optional[int] = None
    is_favorite: bool = False

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
            revised_prompt=asset.meta.get("revised_prompt") if asset.meta else None,
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
            review_note=asset.review_note,
            rejection_reason=asset.rejection_reason,
            rating=asset.rating,
            is_favorite=asset.is_favorite,
        )


# Request/Response models for API
class GenerateImageRequest(BaseModel):
    """Request for advisory image generation."""
    prompt: str
    size: str = "1024x1024"
    quality: str = "standard"
    photo_style: str = "product"
    provider: Optional[str] = None
    user_id: Optional[str] = None      # For prompt history tracking
    session_id: Optional[str] = None   # For prompt history tracking


class GenerateImageResponse(BaseModel):
    """Response from advisory image generation."""
    asset: AdvisoryAssetOut
    message: str = "Image generated. Requires human review before workflow use."


class ReviewAssetRequest(BaseModel):
    """Request to review an asset."""
    approved: bool
    reviewer: str
    note: Optional[str] = None
    rejection_reason: Optional[str] = None  # Required if approved=False, use RejectionReason values
    rating: Optional[int] = Field(default=None, ge=1, le=5)  # Quality rating 1-5


class BulkReviewItem(BaseModel):
    """Single item in a bulk review request."""
    asset_id: str
    approved: bool
    rejection_reason: Optional[str] = None
    rating: Optional[int] = Field(default=None, ge=1, le=5)


class BulkReviewRequest(BaseModel):
    """Request to review multiple assets at once."""
    items: List[BulkReviewItem]
    reviewer: str
    note: Optional[str] = None  # Applies to all items


class BulkReviewResponse(BaseModel):
    """Response from bulk review operation."""
    success_count: int
    error_count: int
    results: List[dict]  # Per-item results


class ListAssetsResponse(BaseModel):
    """Response for listing assets."""
    assets: List[AdvisoryAssetOut]
    total: int
    pending_review: int


class CostEstimateRequest(BaseModel):
    """Request for cost estimate before generation."""
    num_images: int = Field(default=1, ge=1, le=10)
    size: str = "1024x1024"
    quality: str = "standard"


class ProviderCostEstimate(BaseModel):
    """Cost estimate for a single provider."""
    provider: str
    available: bool
    cost_per_image: float
    total_cost: float
    quality_level: str
    notes: Optional[str] = None


class CostComparisonResponse(BaseModel):
    """Response comparing costs across providers."""
    estimates: List[ProviderCostEstimate]
    cheapest: str
    best_quality: str
    recommended: str
    num_images: int
    quality: str


class PromptHistoryEntry(BaseModel):
    """Record of a prompt used in generation."""
    prompt_id: str = Field(default_factory=lambda: f"pmt_{uuid4().hex[:12]}")
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    
    # The prompts
    user_prompt: str
    engineered_prompt: Optional[str] = None
    revised_prompt: Optional[str] = None  # What DALL-E actually used
    
    # Context
    provider: str
    model: str
    photo_style: str = "product"
    quality: str = "standard"
    size: str = "1024x1024"
    
    # Result
    asset_id: Optional[str] = None  # Link to generated asset
    success: bool = True
    
    # Timestamps
    created_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Reuse tracking
    times_reused: int = 0
    is_template: bool = False  # User marked as reusable template
    template_name: Optional[str] = None


class PromptHistoryResponse(BaseModel):
    """Response for prompt history queries."""
    prompts: List[PromptHistoryEntry]
    total: int
    user_id: Optional[str] = None
    session_id: Optional[str] = None
