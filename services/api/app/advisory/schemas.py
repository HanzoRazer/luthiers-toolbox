"""
Advisory Asset Schemas (Neutral Zone)

AI-generated content that requires human review before workflow integration.
These assets live in the ADVISORY ZONE and cannot directly create run artifacts.

This module is the NEUTRAL ZONE for advisory schemas.
Both AI sandbox and RMOS code may import from here.
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


class StylePreset(BaseModel):
    """Predefined style preset for one-click configuration."""
    preset_id: str
    name: str
    description: str
    photo_style: str
    quality: str
    lighting: str
    background: str
    mood: str
    prompt_suffix: str  # Added to user prompt
    negative_prompt: str
    recommended_for: List[str]  # e.g., ["electric", "acoustic"]


class NegativePromptEntry(BaseModel):
    """Entry in the negative prompt library."""
    entry_id: str = Field(default_factory=lambda: f"neg_{uuid4().hex[:8]}")
    name: str
    category: str  # general, anatomy, quality, style
    prompt: str
    description: Optional[str] = None
    severity: str = "recommended"  # required, recommended, optional


class PromptTemplate(BaseModel):
    """Saved prompt template for reuse."""
    template_id: str = Field(default_factory=lambda: f"tpl_{uuid4().hex[:8]}")
    name: str
    description: Optional[str] = None
    
    # The template content
    prompt_template: str  # Can include {placeholders}
    photo_style: str = "product"
    quality: str = "standard"
    size: str = "1024x1024"
    negative_prompt: Optional[str] = None
    
    # Metadata
    created_by: Optional[str] = None
    created_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    times_used: int = 0
    
    # Placeholders that can be filled
    placeholders: List[str] = Field(default_factory=list)  # e.g., ["body_shape", "finish"]
    
    # Tags for organization
    tags: List[str] = Field(default_factory=list)


# =============================================================================
# SEARCH & FILTER (Features 15-17)
# =============================================================================

class AssetSearchRequest(BaseModel):
    """Request for searching/filtering assets."""
    # Text search
    prompt_query: Optional[str] = None  # Search in prompt text
    
    # Filters
    body_shapes: Optional[List[str]] = None  # les_paul, strat, dreadnought, etc.
    finishes: Optional[List[str]] = None  # sunburst, natural, cherry, etc.
    categories: Optional[List[str]] = None  # electric, acoustic, bass, classical
    providers: Optional[List[str]] = None  # dalle3, sdxl, etc.
    
    # Review status
    reviewed: Optional[bool] = None
    approved: Optional[bool] = None
    favorites_only: bool = False
    
    # Rating filter
    min_rating: Optional[int] = Field(default=None, ge=1, le=5)
    max_rating: Optional[int] = Field(default=None, ge=1, le=5)
    
    # Cost filter
    min_cost: Optional[float] = None
    max_cost: Optional[float] = None
    
    # Date filter
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    
    # Sorting
    sort_by: str = "created_at"  # created_at, confidence, cost, rating
    sort_order: str = "desc"  # asc, desc
    
    # Pagination
    limit: int = Field(default=50, ge=1, le=500)
    offset: int = Field(default=0, ge=0)


class AssetSearchResponse(BaseModel):
    """Response from asset search."""
    assets: List[AdvisoryAssetOut]
    total: int
    limit: int
    offset: int
    has_more: bool


# =============================================================================
# EXPORT (Features 18-19)
# =============================================================================

class ExportFormat(str, Enum):
    """Supported export formats."""
    LORA = "lora"  # Standard LoRA training format
    EVERYDREAM = "everydream"  # EveryDream2 format
    DREAMBOOTH = "dreambooth"  # DreamBooth format
    KOHYA = "kohya"  # Kohya_ss format


class ExportFilterRequest(BaseModel):
    """Request for filtered export."""
    # Include filters (same as search)
    body_shapes: Optional[List[str]] = None
    finishes: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    providers: Optional[List[str]] = None
    
    # Must be approved for training
    approved_only: bool = True
    favorites_only: bool = False
    
    # Rating filter
    min_rating: Optional[int] = Field(default=None, ge=1, le=5)
    
    # Format options
    format: ExportFormat = ExportFormat.LORA
    trigger_word: str = "guitar_photo"
    
    # Output options
    include_captions: bool = True
    include_metadata: bool = True
    
    # Limit
    max_images: Optional[int] = Field(default=None, ge=1, le=1000)


class ExportResult(BaseModel):
    """Result from export operation."""
    format: str
    num_images: int
    output_dir: str
    files_created: List[str]
    config_file: Optional[str] = None
    total_size_bytes: int
    trigger_word: str
    filters_applied: Dict[str, Any]


# =============================================================================
# DUPLICATE DETECTION (Feature 20)
# =============================================================================

class SimilarityMatch(BaseModel):
    """A potential duplicate/similar asset."""
    asset_id: str
    similarity_score: float  # 0.0 to 1.0
    match_type: str  # exact, near_duplicate, similar
    prompt: str
    asset_url: Optional[str] = None


class DuplicateCheckRequest(BaseModel):
    """Request to check for duplicates before generating."""
    prompt: str
    threshold: float = Field(default=0.8, ge=0.0, le=1.0)  # Similarity threshold
    check_exact: bool = True  # Check for exact prompt matches
    check_similar: bool = True  # Check for semantically similar prompts
    max_results: int = Field(default=5, ge=1, le=20)


class DuplicateCheckResponse(BaseModel):
    """Response from duplicate check."""
    has_duplicates: bool
    has_similar: bool
    exact_matches: List[SimilarityMatch]
    similar_matches: List[SimilarityMatch]
    recommendation: str  # proceed, review_existing, skip
    prompt_hash: str


# =============================================================================
# REQUEST TRACKING (Feature 21)
# =============================================================================

class RequestRecord(BaseModel):
    """Record of a generation or review request for correlation."""
    record_id: str = Field(default_factory=lambda: f"req_{uuid4().hex[:12]}")
    
    # Global correlation
    request_id: str  # From middleware/header
    provider_request_id: Optional[str] = None  # From AI provider response
    
    # What happened
    action: str  # generate, review, export, search
    endpoint: str
    
    # Context
    asset_id: Optional[str] = None
    prompt: Optional[str] = None
    provider: Optional[str] = None
    
    # Timing
    created_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    duration_ms: Optional[int] = None
    
    # Result
    success: bool = True
    error: Optional[str] = None
    
    # Metadata
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    meta: Dict[str, Any] = Field(default_factory=dict)


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
