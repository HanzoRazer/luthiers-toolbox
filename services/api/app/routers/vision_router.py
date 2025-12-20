"""
Vision Router - AI Guitar Image Generation API

HTTP wrapper for Guitar Vision service. Delegates all logic to
services/vision_service.py following the router-service pattern.

Architecture Layer: ROUTER (Layer 6)
See: docs/governance/ARCHITECTURE_INVARIANTS.md

This router:
- Handles HTTP request/response
- Validates input via Pydantic models
- Delegates to vision_service.py (no business logic here)
- Returns structured responses

Endpoints:
    POST /vision/generate     - Generate and store as AdvisoryAsset
    POST /vision/prompt       - Engineer prompt only (no generation)
    POST /vision/feedback     - Record user selection (teaching loop)
    GET  /vision/providers    - List available providers
    GET  /vision/vocabulary   - Get vocabulary for UI dropdowns
    GET  /vision/health       - Health check
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, Field


# Import service layer
from ..services.vision_service import (
    generate_and_store,
    engineer_prompt_only,
    list_providers,
    get_vocabulary,
    record_feedback,
)


router = APIRouter(prefix="/vision", tags=["Guitar Vision"])


# =============================================================================
# REQUEST/RESPONSE SCHEMAS
# =============================================================================

class ImageSizeEnum(str, Enum):
    """Available image sizes."""
    SQUARE_SM = "512x512"
    SQUARE_MD = "768x768"
    SQUARE_LG = "1024x1024"
    PORTRAIT = "768x1024"
    LANDSCAPE = "1024x768"
    WIDE = "1792x1024"
    TALL = "1024x1792"


class ImageQualityEnum(str, Enum):
    """Quality levels."""
    DRAFT = "draft"
    STANDARD = "standard"
    HD = "hd"


class ProviderEnum(str, Enum):
    """Available providers."""
    DALLE3 = "dalle3"
    SDXL = "sdxl"
    GUITAR_LORA = "guitar_lora"
    STUB = "stub"
    AUTO = "auto"


class PhotoStyleEnum(str, Enum):
    """Photography styles."""
    PRODUCT = "product"
    DRAMATIC = "dramatic"
    LIFESTYLE = "lifestyle"
    STUDIO = "studio"
    VINTAGE = "vintage"
    HERO = "hero"
    FLOATING = "floating"
    ARTISTIC = "artistic"
    CATALOG = "catalog"
    PLAYER = "player"


# --- Generate Request/Response ---

class GenerateRequest(BaseModel):
    """Request to generate guitar image(s)."""
    prompt: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="Natural language description of the guitar",
    )
    num_images: int = Field(default=1, ge=1, le=4)
    size: ImageSizeEnum = Field(default=ImageSizeEnum.SQUARE_LG)
    quality: ImageQualityEnum = Field(default=ImageQualityEnum.STANDARD)
    provider: ProviderEnum = Field(default=ProviderEnum.AUTO)
    photo_style: Optional[PhotoStyleEnum] = None
    prefer_quality: bool = False
    prefer_cost: bool = False


class GeneratedAssetResponse(BaseModel):
    """Single generated asset in response."""
    asset_id: str
    content_uri: Optional[str] = None
    content_hash: str
    provider: str
    generation_time_ms: int
    reviewed: bool = False
    approved_for_workflow: bool = False


class GenerateResponse(BaseModel):
    """Response from image generation."""
    success: bool
    request_id: str
    assets: List[GeneratedAssetResponse] = Field(default_factory=list)
    engineered_prompt: str
    negative_prompt: Optional[str] = None
    detected_category: Optional[str] = None
    detected_body_shape: Optional[str] = None
    detected_finish: Optional[str] = None
    provider_used: str
    total_cost: float
    total_time_ms: Optional[float] = None
    error: Optional[str] = None


# --- Prompt Request/Response ---

class PromptRequest(BaseModel):
    """Request to engineer prompt only."""
    prompt: str = Field(..., min_length=3, max_length=500)
    photo_style: Optional[PhotoStyleEnum] = None
    model_target: str = Field(default="general")


class PromptResponse(BaseModel):
    """Engineered prompt response."""
    user_input: str
    positive_prompt: str
    negative_prompt: str
    category: str
    body_shape: Optional[str] = None
    finish: Optional[str] = None
    confidence: float


# --- Feedback Request/Response ---

class FeedbackRequest(BaseModel):
    """Record user feedback."""
    asset_id: str
    selected: bool = True
    rating: Optional[int] = Field(default=None, ge=1, le=5)


class FeedbackResponse(BaseModel):
    """Feedback response."""
    success: bool
    message: str


# --- Health Response ---

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: str
    providers_available: int


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/generate", response_model=GenerateResponse)
async def generate_image(
    request: GenerateRequest,
    x_request_id: Optional[str] = Header(None, alias="X-Request-ID"),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
):
    """
    Generate guitar image(s) from natural language prompt.

    Images are stored as AdvisoryAssets requiring review before
    workflow integration. Returns asset IDs for tracking.

    Examples:
        - "emerald green les paul with gold hardware"
        - "sunburst dreadnought acoustic with abalone rosette"
        - "black telecaster maple fretboard"
    """
    result = generate_and_store(
        prompt=request.prompt.strip(),
        num_images=request.num_images,
        size=request.size.value,
        quality=request.quality.value,
        photo_style=request.photo_style.value if request.photo_style else None,
        provider=request.provider.value if request.provider != ProviderEnum.AUTO else None,
        prefer_quality=request.prefer_quality,
        prefer_cost=request.prefer_cost,
        request_id=x_request_id,
        user_id=x_user_id,
        session_id=x_session_id,
    )

    # Map assets to response format
    assets = [
        GeneratedAssetResponse(
            asset_id=a["asset_id"],
            content_uri=a.get("content_uri"),
            content_hash=a["content_hash"],
            provider=a["provider"],
            generation_time_ms=a.get("generation_time_ms", 0),
            reviewed=a.get("reviewed", False),
            approved_for_workflow=a.get("approved_for_workflow", False),
        )
        for a in result.get("assets", [])
    ]

    return GenerateResponse(
        success=result["success"],
        request_id=result["request_id"],
        assets=assets,
        engineered_prompt=result.get("engineered_prompt", ""),
        negative_prompt=result.get("negative_prompt"),
        detected_category=result.get("detected_category"),
        detected_body_shape=result.get("detected_body_shape"),
        detected_finish=result.get("detected_finish"),
        provider_used=result.get("provider_used", "none"),
        total_cost=result.get("total_cost", 0.0),
        total_time_ms=result.get("total_time_ms"),
        error=result.get("error"),
    )


@router.post("/prompt", response_model=PromptResponse)
async def engineer_prompt(request: PromptRequest):
    """
    Engineer a prompt without generating an image.

    Useful for previewing what the prompt will look like
    and understanding how the parser interprets input.
    """
    result = engineer_prompt_only(
        prompt=request.prompt.strip(),
        photo_style=request.photo_style.value if request.photo_style else None,
        model_target=request.model_target,
    )

    return PromptResponse(
        user_input=result["user_input"],
        positive_prompt=result["positive_prompt"],
        negative_prompt=result["negative_prompt"],
        category=result["category"],
        body_shape=result.get("body_shape"),
        finish=result.get("finish"),
        confidence=result["confidence"],
    )


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    request: FeedbackRequest,
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
):
    """
    Record user selection for teaching loop.

    Feedback improves provider routing over time:
    - If DALL-E images are consistently chosen, LoRA needs more training
    - If LoRA wins for certain categories, route those to save costs
    """
    result = record_feedback(
        asset_id=request.asset_id,
        selected=request.selected,
        rating=request.rating,
        reviewer=x_user_id,
    )

    return FeedbackResponse(
        success=result["success"],
        message=result["message"],
    )


@router.get("/providers")
async def get_providers():
    """
    List available image generation providers.

    Shows which providers are configured, their costs, and availability.
    """
    return list_providers()


@router.get("/vocabulary")
async def get_vocab():
    """
    Get vocabulary for UI dropdowns.

    Returns categorized lists of body shapes, finishes, woods,
    hardware, inlays, and photo styles.
    """
    return get_vocabulary()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    providers = list_providers()
    available_count = sum(1 for p in providers["providers"] if p["available"])

    return HealthResponse(
        status="healthy" if available_count > 0 else "degraded",
        timestamp=datetime.utcnow().isoformat(),
        providers_available=available_count,
    )
