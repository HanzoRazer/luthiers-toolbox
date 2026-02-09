"""Advisory Asset Schemas (Neutral Zone)"""
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
    """AI-generated content that requires human review before use."""
    
    asset_id: str = Field(default_factory=lambda: f"adv_{uuid4().hex[:12]}")
    asset_type: AdvisoryAssetType
    created_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Source tracking
    source: Literal["ai_graphics", "ai_analysis", "ai_suggestion"] = "ai_graphics"
    provider: str  # dalle3, sdxl, stub
    model: str     # dall-e-3, sd-xl-base-1.0
    
    # Request correlation (ties into global request tracking)
    request_id: Optional[str] = None  # From middleware/header
    provider_request_id: Optional[str] = None  # From AI provider response
    
    # Content
    prompt: str
    prompt_hash: Optional[str] = None  # For duplicate detection
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
    
    # Review request tracking
    review_request_id: Optional[str] = None  # Request ID when reviewed
    
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
    prompt_hash: Optional[str] = None
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
    
    # Request correlation
    request_id: Optional[str] = None
    provider_request_id: Optional[str] = None
    review_request_id: Optional[str] = None

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
            prompt_hash=asset.prompt_hash,
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
            request_id=asset.request_id,
            provider_request_id=asset.provider_request_id,
            review_request_id=asset.review_request_id,
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
    
    # Optional: attach to a run when approving
    run_id: Optional[str] = None  # If provided and approved, attach to this run


class AttachToRunRequest(BaseModel):
    """Request to attach an approved advisory to a run."""
    asset_id: str
    run_id: str
    kind: str = "advisory"  # advisory, explanation, note


class AttachToRunResponse(BaseModel):
    """Response from attaching advisory to run."""
    success: bool
    asset_id: str
    run_id: str
    advisory_ref_created: bool
    message: str


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


class BudgetConfig(BaseModel):
    """Budget configuration for cost tracking."""
    daily_limit_usd: Optional[float] = Field(default=None, ge=0)
    weekly_limit_usd: Optional[float] = Field(default=None, ge=0)
    monthly_limit_usd: Optional[float] = Field(default=None, ge=0)
    total_limit_usd: Optional[float] = Field(default=None, ge=0)
    alert_threshold_pct: float = Field(default=80.0, ge=0, le=100)  # Alert at X% of limit


class BudgetStatus(BaseModel):
    """Current budget status."""
    # Spending totals
    spent_today_usd: float
    spent_this_week_usd: float
    spent_this_month_usd: float
    spent_total_usd: float
    
    # Limits (None = no limit)
    daily_limit_usd: Optional[float] = None
    weekly_limit_usd: Optional[float] = None
    monthly_limit_usd: Optional[float] = None
    total_limit_usd: Optional[float] = None
    
    # Remaining
    daily_remaining_usd: Optional[float] = None
    weekly_remaining_usd: Optional[float] = None
    monthly_remaining_usd: Optional[float] = None
    total_remaining_usd: Optional[float] = None
    
    # Status
    daily_exceeded: bool = False
    weekly_exceeded: bool = False
    monthly_exceeded: bool = False
    total_exceeded: bool = False
    any_limit_exceeded: bool = False
    
    # Alerts
    alerts: List[str] = []


class BatchEstimateRequest(BaseModel):
    """Request for batch generation cost estimate."""
    prompts: List[str] = Field(..., min_length=1, max_length=100)
    provider: Optional[str] = None
    quality: str = "standard"
    size: str = "1024x1024"


class BatchEstimateResponse(BaseModel):
    """Response with batch generation cost estimate."""
    num_images: int
    provider: str
    quality: str
    cost_per_image: float
    total_cost: float
    budget_status: BudgetStatus
    can_afford: bool
    warning: Optional[str] = None


# =========================================================================
# Features 12–21 extracted to schemas_features.py (WP-3)
# Re-export for backward compatibility
# =========================================================================
from .schemas_features import (  # noqa: E402
    StylePreset as StylePreset,
    NegativePromptEntry as NegativePromptEntry,
    PromptTemplate as PromptTemplate,
    AssetSearchRequest as AssetSearchRequest,
    AssetSearchResponse as AssetSearchResponse,
    ExportFormat as ExportFormat,
    ExportFilterRequest as ExportFilterRequest,
    ExportResult as ExportResult,
    SimilarityMatch as SimilarityMatch,
    DuplicateCheckRequest as DuplicateCheckRequest,
    DuplicateCheckResponse as DuplicateCheckResponse,
    RequestRecord as RequestRecord,
    PromptHistoryEntry as PromptHistoryEntry,
    PromptHistoryResponse as PromptHistoryResponse,
)
