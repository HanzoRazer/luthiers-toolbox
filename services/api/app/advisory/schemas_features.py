"""Advisory Feature Schemas — search, export, duplicate detection, templates & tracking.

Extracted from schemas.py (WP-3).
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from .schemas import AdvisoryAssetOut, BudgetStatus


# =============================================================================
# STYLE / TEMPLATES (Features 12-14)
# =============================================================================

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
