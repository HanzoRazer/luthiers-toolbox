#!/usr/bin/env python3
"""
REFERENCE ONLY - DO NOT IMPORT IN PRODUCTION

This file is preserved for standalone testing and reference.
Production implementation: app/routers/vision_router.py
Service layer: app/services/vision_service.py

Key differences from production:
- Production creates AdvisoryAssets (audit trail)
- Production uses request_id correlation
- Production delegates to services/ layer

See: docs/governance/AI_SANDBOX_HANDOFF.md

---

Guitar Vision Engine — FastAPI Routes (LEGACY)

REST endpoints for the frontend sandbox to generate guitar images.

Endpoints:
    POST /api/vision/generate         - Generate guitar image(s)
    POST /api/vision/prompt           - Engineer prompt only (no generation)
    POST /api/vision/feedback         - Record user selection (teaching loop)
    GET  /api/vision/providers        - List available providers
    GET  /api/vision/vocabulary       - Get vocabulary for UI dropdowns
    GET  /api/vision/health           - Health check

Author: Luthier's ToolBox
Date: December 16, 2025
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field, field_validator

# Local imports
try:
    from ..prompt_engine import (
        engineer_guitar_prompt,
        parse_guitar_request,
        get_prompt_variations,
        GuitarPrompt,
        ParsedGuitarRequest,
        GuitarCategory,
        BODY_SHAPES,
        FINISHES,
        WOODS,
        HARDWARE,
        INLAYS,
        PHOTOGRAPHY_STYLES,
    )
    from ..image_providers import (
        GuitarVisionEngine,
        ImageProvider,
        ImageSize,
        ImageQuality,
        ImageGenerationResult,
        GeneratedImage,
        PROVIDER_COSTS,
    )
except ImportError:
    # Direct imports for standalone testing
    from prompt_engine import (
        engineer_guitar_prompt,
        parse_guitar_request,
        get_prompt_variations,
        GuitarPrompt,
        ParsedGuitarRequest,
        GuitarCategory,
        BODY_SHAPES,
        FINISHES,
        WOODS,
        HARDWARE,
        INLAYS,
        PHOTOGRAPHY_STYLES,
    )
    from image_providers import (
        GuitarVisionEngine,
        ImageProvider,
        ImageSize,
        ImageQuality,
        ImageGenerationResult,
        GeneratedImage,
        PROVIDER_COSTS,
    )


# =============================================================================
# ROUTER SETUP
# =============================================================================

router = APIRouter(prefix="/vision", tags=["Guitar Vision"])

# Singleton engine instance
_engine: Optional[GuitarVisionEngine] = None


def get_engine() -> GuitarVisionEngine:
    """Get or create the engine singleton."""
    global _engine
    if _engine is None:
        _engine = GuitarVisionEngine()
    return _engine


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
    AUTO = "auto"  # Let router decide


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


# --- Generation Request ---

class GenerateRequest(BaseModel):
    """Request to generate guitar image(s)."""
    
    # Required
    prompt: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="Natural language description of the guitar",
        examples=["emerald green les paul with gold hardware"],
    )
    
    # Generation options
    num_images: int = Field(
        default=1,
        ge=1,
        le=4,
        description="Number of images to generate (1-4)",
    )
    size: ImageSizeEnum = Field(
        default=ImageSizeEnum.SQUARE_LG,
        description="Output image size",
    )
    quality: ImageQualityEnum = Field(
        default=ImageQualityEnum.STANDARD,
        description="Image quality level",
    )
    
    # Provider control
    provider: ProviderEnum = Field(
        default=ProviderEnum.AUTO,
        description="Which provider to use (auto = let router decide)",
    )
    prefer_quality: bool = Field(
        default=False,
        description="Prefer higher quality over cost",
    )
    prefer_cost: bool = Field(
        default=False,
        description="Prefer lower cost over quality",
    )
    
    # Style options
    photo_style: Optional[PhotoStyleEnum] = Field(
        default=None,
        description="Photography style (optional, auto-detected from prompt)",
    )
    
    # Advanced
    seed: Optional[int] = Field(
        default=None,
        description="Random seed for reproducibility (provider-dependent)",
    )
    
    @field_validator("prompt")
    @classmethod
    def validate_prompt(cls, v: str) -> str:
        """Clean up prompt."""
        return v.strip()


class GeneratedImageResponse(BaseModel):
    """Single generated image in response."""
    image_id: str
    url: Optional[str] = None
    base64_data: Optional[str] = None
    provider: str
    generation_time_ms: float
    seed_used: Optional[int] = None


class GenerateResponse(BaseModel):
    """Response from image generation."""
    success: bool
    request_id: str
    
    # Results
    images: List[GeneratedImageResponse] = Field(default_factory=list)
    
    # Prompt info
    user_prompt: str
    engineered_prompt: str
    negative_prompt: str
    
    # Parsing info
    detected_category: str
    detected_body_shape: Optional[str] = None
    detected_finish: Optional[str] = None
    parse_confidence: float
    
    # Cost & timing
    provider_used: str
    routing_reason: str
    estimated_cost: float
    actual_cost: float
    total_time_ms: float
    
    # Error (if failed)
    error: Optional[str] = None


# --- Prompt Engineering Request ---

class PromptRequest(BaseModel):
    """Request to engineer a prompt without generating."""
    prompt: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="Natural language description",
    )
    photo_style: Optional[PhotoStyleEnum] = None
    model_target: str = Field(
        default="general",
        description="Optimize for: general, dalle, sdxl, midjourney",
    )
    include_variations: bool = Field(
        default=False,
        description="Include prompt variations for different styles",
    )


class PromptResponse(BaseModel):
    """Engineered prompt response."""
    user_input: str
    
    # Main prompt
    positive_prompt: str
    negative_prompt: str
    
    # Parsed details
    category: str
    body_shape: Optional[str] = None
    body_shape_expanded: Optional[str] = None
    finish: Optional[str] = None
    finish_expanded: Optional[str] = None
    woods: List[str] = Field(default_factory=list)
    hardware: List[str] = Field(default_factory=list)
    inlays: List[str] = Field(default_factory=list)
    custom_terms: List[str] = Field(default_factory=list)
    confidence: float
    
    # Variations (if requested)
    variations: List[Dict[str, str]] = Field(default_factory=list)


# --- Feedback Request ---

class FeedbackRequest(BaseModel):
    """Record user selection for teaching loop."""
    request_id: str = Field(..., description="The generation request ID")
    selected_image_id: str = Field(..., description="ID of image user selected as best")
    rating: Optional[int] = Field(
        default=None,
        ge=1,
        le=5,
        description="Optional 1-5 rating",
    )


class FeedbackResponse(BaseModel):
    """Feedback recording response."""
    success: bool
    message: str
    provider_scores_updated: bool = False


# --- Provider Info ---

class ProviderInfo(BaseModel):
    """Information about a provider."""
    id: str
    name: str
    available: bool
    costs: Dict[str, float]
    description: str


class ProvidersResponse(BaseModel):
    """List of available providers."""
    providers: List[ProviderInfo]
    default_provider: str
    routing_enabled: bool = True


# --- Vocabulary ---

class VocabularyResponse(BaseModel):
    """Vocabulary for UI dropdowns."""
    body_shapes: Dict[str, List[str]]  # category -> shapes
    finishes: Dict[str, List[str]]  # type -> finishes
    woods: Dict[str, List[str]]  # category -> woods
    hardware: Dict[str, List[str]]  # type -> options
    inlays: Dict[str, List[str]]  # type -> options
    photo_styles: List[str]


# --- Health ---

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    engine_ready: bool
    available_providers: List[str]
    timestamp: str


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/generate", response_model=GenerateResponse)
async def generate_image(request: GenerateRequest) -> GenerateResponse:
    """
    Generate guitar image(s) from natural language prompt.
    
    The prompt is first engineered using guitar-specific vocabulary,
    then routed to the best available provider.
    
    Examples:
        - "emerald green les paul with gold hardware"
        - "sunburst dreadnought acoustic with abalone rosette"
        - "black telecaster maple fretboard"
    """
    import time
    start = time.time()
    
    engine = get_engine()
    
    # Map enums to internal types
    size_map = {
        ImageSizeEnum.SQUARE_SM: ImageSize.SQUARE_SM,
        ImageSizeEnum.SQUARE_MD: ImageSize.SQUARE_MD,
        ImageSizeEnum.SQUARE_LG: ImageSize.SQUARE_LG,
        ImageSizeEnum.PORTRAIT: ImageSize.PORTRAIT,
        ImageSizeEnum.LANDSCAPE: ImageSize.LANDSCAPE,
        ImageSizeEnum.WIDE: ImageSize.WIDE,
        ImageSizeEnum.TALL: ImageSize.TALL,
    }
    
    quality_map = {
        ImageQualityEnum.DRAFT: ImageQuality.DRAFT,
        ImageQualityEnum.STANDARD: ImageQuality.STANDARD,
        ImageQualityEnum.HD: ImageQuality.HD,
    }
    
    provider_map = {
        ProviderEnum.DALLE3: ImageProvider.DALLE3,
        ProviderEnum.SDXL: ImageProvider.SDXL,
        ProviderEnum.GUITAR_LORA: ImageProvider.GUITAR_LORA,
        ProviderEnum.STUB: ImageProvider.STUB,
        ProviderEnum.AUTO: None,  # Let router decide
    }
    
    # Engineer prompt first for response
    guitar_prompt = engineer_guitar_prompt(
        request.prompt,
        photo_style=request.photo_style.value if request.photo_style else None,
    )
    parsed = guitar_prompt.parsed_request
    
    # Generate
    try:
        result = engine.generate(
            user_prompt=request.prompt,
            num_images=request.num_images,
            size=size_map.get(request.size, ImageSize.SQUARE_LG),
            quality=quality_map.get(request.quality, ImageQuality.STANDARD),
            photo_style=request.photo_style.value if request.photo_style else None,
            prefer_quality=request.prefer_quality,
            prefer_cost=request.prefer_cost,
            force_provider=provider_map.get(request.provider),
        )
        
        # Build response
        images = [
            GeneratedImageResponse(
                image_id=img.image_id,
                url=img.url,
                base64_data=img.base64_data,
                provider=img.provider.value,
                generation_time_ms=img.generation_time_ms,
                seed_used=img.seed_used,
            )
            for img in result.images
        ]
        
        elapsed_ms = (time.time() - start) * 1000
        
        return GenerateResponse(
            success=result.success,
            request_id=result.request.request_id,
            images=images,
            user_prompt=request.prompt,
            engineered_prompt=guitar_prompt.positive_prompt,
            negative_prompt=guitar_prompt.negative_prompt,
            detected_category=parsed.category.value,
            detected_body_shape=parsed.body_shape,
            detected_finish=parsed.finish,
            parse_confidence=parsed.confidence,
            provider_used=result.request.provider.value,
            routing_reason="User forced" if request.provider != ProviderEnum.AUTO else "Auto-routed",
            estimated_cost=result.request.estimated_cost(),
            actual_cost=result.actual_cost,
            total_time_ms=elapsed_ms,
            error=result.error,
        )
        
    except Exception as e:
        elapsed_ms = (time.time() - start) * 1000
        return GenerateResponse(
            success=False,
            request_id="error",
            images=[],
            user_prompt=request.prompt,
            engineered_prompt=guitar_prompt.positive_prompt,
            negative_prompt=guitar_prompt.negative_prompt,
            detected_category=parsed.category.value,
            detected_body_shape=parsed.body_shape,
            detected_finish=parsed.finish,
            parse_confidence=parsed.confidence,
            provider_used="none",
            routing_reason="Failed before routing",
            estimated_cost=0.0,
            actual_cost=0.0,
            total_time_ms=elapsed_ms,
            error=str(e),
        )


@router.post("/prompt", response_model=PromptResponse)
async def engineer_prompt(request: PromptRequest) -> PromptResponse:
    """
    Engineer a prompt without generating an image.
    
    Useful for:
    - Previewing what the prompt will look like
    - Understanding how the parser interprets input
    - Getting variations for different photo styles
    """
    guitar_prompt = engineer_guitar_prompt(
        request.prompt,
        photo_style=request.photo_style.value if request.photo_style else None,
        model_target=request.model_target,
    )
    parsed = guitar_prompt.parsed_request
    
    # Get variations if requested
    variations = []
    if request.include_variations:
        var_prompts = get_prompt_variations(request.prompt, count=4)
        variations = [
            {
                "style": vp.model_hints.get("style", "unknown"),
                "positive_prompt": vp.positive_prompt,
            }
            for vp in var_prompts
        ]
    
    return PromptResponse(
        user_input=request.prompt,
        positive_prompt=guitar_prompt.positive_prompt,
        negative_prompt=guitar_prompt.negative_prompt,
        category=parsed.category.value,
        body_shape=parsed.body_shape,
        body_shape_expanded=parsed.body_shape_expanded,
        finish=parsed.finish,
        finish_expanded=parsed.finish_expanded,
        woods=parsed.woods,
        hardware=parsed.hardware,
        inlays=parsed.inlays,
        custom_terms=parsed.custom_terms,
        confidence=parsed.confidence,
        variations=variations,
    )


@router.post("/feedback", response_model=FeedbackResponse)
async def record_feedback(request: FeedbackRequest) -> FeedbackResponse:
    """
    Record which image the user selected as best.
    
    This feeds the teacher-student learning loop:
    - If DALL-E images are consistently chosen over LoRA, we know LoRA needs more training
    - If LoRA wins for certain categories, we route those to LoRA to save costs
    """
    engine = get_engine()
    
    # Find the result in recent logs
    # (In production, this would look up by request_id in a database)
    
    # For now, just record the feedback
    try:
        # This would normally look up the result and call engine.record_selection()
        # Simplified for now:
        engine.router.record_feedback(
            category="unknown",  # Would come from stored result
            provider=ImageProvider.STUB,  # Would come from stored result
            was_selected=True,
            rating=request.rating,
        )
        
        return FeedbackResponse(
            success=True,
            message=f"Recorded selection of {request.selected_image_id}",
            provider_scores_updated=True,
        )
    except Exception as e:
        return FeedbackResponse(
            success=False,
            message=f"Failed to record feedback: {e}",
            provider_scores_updated=False,
        )


@router.get("/providers", response_model=ProvidersResponse)
async def list_providers() -> ProvidersResponse:
    """
    List available image generation providers.
    
    Shows which providers are configured and their costs.
    """
    engine = get_engine()
    available = engine.router.get_available_providers()
    
    provider_descriptions = {
        ImageProvider.DALLE3: "OpenAI DALL-E 3 - High quality, general purpose",
        ImageProvider.SDXL: "Stable Diffusion XL - Self-hosted, cost-effective",
        ImageProvider.GUITAR_LORA: "Guitar LoRA - Fine-tuned guitar specialist",
        ImageProvider.STUB: "Stub - Testing without real generation",
    }
    
    providers = []
    for provider_id in ImageProvider:
        if provider_id == ImageProvider.MIDJOURNEY:
            continue  # Skip unimplemented
            
        costs = PROVIDER_COSTS.get(provider_id, {})
        providers.append(ProviderInfo(
            id=provider_id.value,
            name=provider_id.value.upper().replace("_", " "),
            available=provider_id in available,
            costs={q.value: c for q, c in costs.items()},
            description=provider_descriptions.get(provider_id, ""),
        ))
    
    # Determine default
    if ImageProvider.GUITAR_LORA in available:
        default = "guitar_lora"
    elif ImageProvider.DALLE3 in available:
        default = "dalle3"
    elif ImageProvider.SDXL in available:
        default = "sdxl"
    else:
        default = "stub"
    
    return ProvidersResponse(
        providers=providers,
        default_provider=default,
        routing_enabled=True,
    )


@router.get("/vocabulary", response_model=VocabularyResponse)
async def get_vocabulary() -> VocabularyResponse:
    """
    Get vocabulary for UI dropdowns.
    
    Returns categorized lists of:
    - Body shapes (by guitar type)
    - Finishes (by type)
    - Woods (by usage)
    - Hardware options
    - Inlay options
    - Photo styles
    """
    # Organize body shapes by category
    body_shapes_by_cat: Dict[str, List[str]] = {
        "acoustic": [],
        "electric": [],
        "classical": [],
        "bass": [],
    }
    for shape, category in BODY_SHAPES.items():
        body_shapes_by_cat[category.value].append(shape)
    
    # Organize finishes by type
    finishes_by_type: Dict[str, List[str]] = {
        "solid": [],
        "burst": [],
        "transparent": [],
        "metallic": [],
        "figured": [],
        "special": [],
    }
    for finish in FINISHES.keys():
        if "burst" in finish:
            finishes_by_type["burst"].append(finish)
        elif any(t in finish for t in ["trans", "emerald", "amber", "wine", "ocean"]):
            finishes_by_type["transparent"].append(finish)
        elif any(t in finish for t in ["gold", "silver", "champagne", "gunmetal"]):
            finishes_by_type["metallic"].append(finish)
        elif any(t in finish for t in ["quilted", "flame", "figured", "spalted", "burl"]):
            finishes_by_type["figured"].append(finish)
        elif any(t in finish for t in ["relic", "aged", "satin", "matte", "nitro"]):
            finishes_by_type["special"].append(finish)
        else:
            finishes_by_type["solid"].append(finish)
    
    # Organize woods by usage
    woods_by_usage: Dict[str, List[str]] = {
        "tops": [],
        "back_sides": [],
        "necks": [],
        "fretboards": [],
    }
    for wood in WOODS.keys():
        if "fretboard" in wood:
            woods_by_usage["fretboards"].append(wood)
        elif "neck" in wood:
            woods_by_usage["necks"].append(wood)
        elif "top" in wood or wood in ["spruce", "sitka", "engelmann", "adirondack", "cedar", "redwood"]:
            woods_by_usage["tops"].append(wood)
        else:
            woods_by_usage["back_sides"].append(wood)
    
    # Organize hardware
    hardware_by_type: Dict[str, List[str]] = {
        "colors": [],
        "tuners": [],
        "bridges": [],
        "pickups": [],
    }
    for hw in HARDWARE.keys():
        if any(t in hw for t in ["chrome", "gold", "black", "nickel", "aged", "relic"]) and "tuner" not in hw:
            hardware_by_type["colors"].append(hw)
        elif "tuner" in hw or hw in ["grover", "kluson"]:
            hardware_by_type["tuners"].append(hw)
        elif any(t in hw for t in ["bridge", "tom", "wraparound", "floyd", "bigsby", "hardtail", "tremolo"]):
            hardware_by_type["bridges"].append(hw)
        else:
            hardware_by_type["pickups"].append(hw)
    
    # Organize inlays
    inlays_by_type: Dict[str, List[str]] = {
        "fretboard": [],
        "rosette": [],
        "binding": [],
    }
    for inlay in INLAYS.keys():
        if any(t in inlay for t in ["rosette", "herringbone", "mosaic", "rope"]) and "inlay" not in inlay:
            inlays_by_type["rosette"].append(inlay)
        elif "binding" in inlay:
            inlays_by_type["binding"].append(inlay)
        else:
            inlays_by_type["fretboard"].append(inlay)
    
    return VocabularyResponse(
        body_shapes=body_shapes_by_cat,
        finishes=finishes_by_type,
        woods=woods_by_usage,
        hardware=hardware_by_type,
        inlays=inlays_by_type,
        photo_styles=list(PHOTOGRAPHY_STYLES.keys()),
    )


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.
    
    Returns engine status and available providers.
    """
    try:
        engine = get_engine()
        available = engine.router.get_available_providers()
        
        return HealthResponse(
            status="healthy",
            engine_ready=True,
            available_providers=[p.value for p in available],
            timestamp=datetime.utcnow().isoformat(),
        )
    except Exception as e:
        return HealthResponse(
            status=f"unhealthy: {e}",
            engine_ready=False,
            available_providers=[],
            timestamp=datetime.utcnow().isoformat(),
        )


# =============================================================================
# STANDALONE APP (for testing)
# =============================================================================

def create_app():
    """Create FastAPI app for standalone testing."""
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    
    app = FastAPI(
        title="Guitar Vision Engine",
        description="AI-powered guitar image generation",
        version="1.0.0",
    )
    
    # CORS for frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Mount router
    app.include_router(router, prefix="/api")
    
    @app.get("/")
    async def root():
        return {
            "service": "Guitar Vision Engine",
            "version": "1.0.0",
            "docs": "/docs",
            "endpoints": {
                "generate": "POST /api/vision/generate",
                "prompt": "POST /api/vision/prompt",
                "feedback": "POST /api/vision/feedback",
                "providers": "GET /api/vision/providers",
                "vocabulary": "GET /api/vision/vocabulary",
                "health": "GET /api/vision/health",
            }
        }
    
    return app


if __name__ == "__main__":
    import uvicorn
    
    app = create_app()
    print("=" * 60)
    print("🎸 GUITAR VISION ENGINE — API Server")
    print("=" * 60)
    print("\nEndpoints:")
    print("  POST /api/vision/generate    - Generate images")
    print("  POST /api/vision/prompt      - Engineer prompt only")
    print("  POST /api/vision/feedback    - Record user selection")
    print("  GET  /api/vision/providers   - List providers")
    print("  GET  /api/vision/vocabulary  - Get vocabulary")
    print("  GET  /api/vision/health      - Health check")
    print("\nDocs: http://localhost:8100/docs")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=8100)
