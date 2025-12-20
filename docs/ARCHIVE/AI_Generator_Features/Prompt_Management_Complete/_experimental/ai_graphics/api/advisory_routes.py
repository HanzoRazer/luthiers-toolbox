"""
Advisory Routes

API endpoints for AI-generated advisory assets.
Connects existing GuitarVisionEngine to AdvisoryAssetStore.

Flow:
1. Request comes in
2. GuitarVisionEngine generates image (existing)
3. Result stored as AdvisoryAsset (new)
4. Human reviews before workflow use
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

from ..schemas.advisory_schemas import (
    AdvisoryAsset,
    AdvisoryAssetType,
    AdvisoryAssetOut,
    GenerateImageRequest,
    GenerateImageResponse,
    ReviewAssetRequest,
    BulkReviewItem,
    BulkReviewRequest,
    BulkReviewResponse,
    ListAssetsResponse,
    RejectionReason,
    CostEstimateRequest,
    ProviderCostEstimate,
    CostComparisonResponse,
    PromptHistoryEntry,
    PromptHistoryResponse,
    BudgetConfig,
    BudgetStatus,
    BatchEstimateRequest,
    BatchEstimateResponse,
    StylePreset,
    NegativePromptEntry,
    PromptTemplate,
)
from ..advisory_store import (
    get_advisory_store,
    get_prompt_history_store,
    get_budget_tracker,
    compute_content_hash,
)
from ..image_providers import (
    GuitarVisionEngine,
    ImageSize,
    ImageQuality,
    ImageProvider,
    PROVIDER_COSTS,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/advisory", tags=["Advisory Assets"])


# =============================================================================
# STYLE PRESETS (Feature 13)
# =============================================================================

STYLE_PRESETS = {
    "vintage": StylePreset(
        preset_id="vintage",
        name="Vintage",
        description="Classic, warm tones with aged wood aesthetic",
        photo_style="vintage",
        quality="standard",
        lighting="warm tungsten",
        background="aged wood workshop",
        mood="nostalgic, classic",
        prompt_suffix="vintage photography style, warm color grading, aged patina, classic aesthetic, film grain",
        negative_prompt="modern, futuristic, neon, digital, sterile",
        recommended_for=["electric", "acoustic", "classical"],
    ),
    "modern": StylePreset(
        preset_id="modern",
        name="Modern",
        description="Clean, contemporary look with sharp details",
        photo_style="modern",
        quality="hd",
        lighting="clean studio LED",
        background="minimal white or dark gradient",
        mood="sleek, professional",
        prompt_suffix="modern photography, clean lines, sharp focus, contemporary aesthetic, minimalist",
        negative_prompt="vintage, aged, worn, rustic, grainy",
        recommended_for=["electric", "bass"],
    ),
    "studio": StylePreset(
        preset_id="studio",
        name="Studio Product",
        description="Professional product photography for catalogs",
        photo_style="product",
        quality="hd",
        lighting="three-point studio lighting",
        background="seamless white or black",
        mood="commercial, professional",
        prompt_suffix="professional product photography, studio lighting, commercial quality, catalog shot, perfectly lit",
        negative_prompt="casual, amateur, outdoor, natural light only, shadows",
        recommended_for=["electric", "acoustic", "bass", "classical"],
    ),
    "lifestyle": StylePreset(
        preset_id="lifestyle",
        name="Lifestyle",
        description="Guitar in natural environment, storytelling",
        photo_style="lifestyle",
        quality="standard",
        lighting="natural daylight",
        background="music room, stage, or outdoor setting",
        mood="authentic, lived-in",
        prompt_suffix="lifestyle photography, natural setting, authentic moment, environmental portrait, storytelling",
        negative_prompt="sterile, studio, white background, isolated",
        recommended_for=["acoustic", "classical", "electric"],
    ),
    "dramatic": StylePreset(
        preset_id="dramatic",
        name="Dramatic",
        description="High contrast, moody lighting for impact",
        photo_style="dramatic",
        quality="hd",
        lighting="dramatic side lighting, chiaroscuro",
        background="dark, smoky, or spotlight",
        mood="intense, powerful",
        prompt_suffix="dramatic lighting, high contrast, moody atmosphere, cinematic, bold shadows",
        negative_prompt="flat lighting, bright, cheerful, soft, pastel",
        recommended_for=["electric", "bass"],
    ),
    "artistic": StylePreset(
        preset_id="artistic",
        name="Artistic",
        description="Creative, fine art photography approach",
        photo_style="artistic",
        quality="hd",
        lighting="creative mixed lighting",
        background="abstract or textured",
        mood="creative, expressive",
        prompt_suffix="fine art photography, creative composition, artistic interpretation, gallery quality",
        negative_prompt="commercial, standard, boring, conventional",
        recommended_for=["acoustic", "classical"],
    ),
}


# =============================================================================
# NEGATIVE PROMPT LIBRARY (Feature 14)
# =============================================================================

NEGATIVE_PROMPTS = {
    # General quality issues
    "quality_basic": NegativePromptEntry(
        entry_id="quality_basic",
        name="Basic Quality",
        category="quality",
        prompt="blurry, low quality, low resolution, pixelated, jpeg artifacts, compression artifacts",
        description="Prevents basic image quality issues",
        severity="required",
    ),
    "quality_advanced": NegativePromptEntry(
        entry_id="quality_advanced",
        name="Advanced Quality",
        category="quality",
        prompt="overexposed, underexposed, chromatic aberration, lens flare, motion blur, out of focus",
        description="Prevents advanced photography issues",
        severity="recommended",
    ),
    
    # Guitar anatomy issues
    "anatomy_strings": NegativePromptEntry(
        entry_id="anatomy_strings",
        name="String Anatomy",
        category="anatomy",
        prompt="wrong number of strings, extra strings, missing strings, floating strings, disconnected strings",
        description="Ensures correct string count and placement",
        severity="required",
    ),
    "anatomy_frets": NegativePromptEntry(
        entry_id="anatomy_frets",
        name="Fret Anatomy",
        category="anatomy",
        prompt="uneven frets, missing frets, crooked frets, frets wrong angle, bent frets",
        description="Ensures correct fret appearance",
        severity="required",
    ),
    "anatomy_proportions": NegativePromptEntry(
        entry_id="anatomy_proportions",
        name="Body Proportions",
        category="anatomy",
        prompt="wrong proportions, distorted body, asymmetric body, warped neck, bent headstock",
        description="Ensures correct guitar proportions",
        severity="required",
    ),
    "anatomy_hardware": NegativePromptEntry(
        entry_id="anatomy_hardware",
        name="Hardware Anatomy",
        category="anatomy",
        prompt="floating tuners, disconnected bridge, missing pickups, wrong pickup count, inverted hardware",
        description="Ensures correct hardware placement",
        severity="required",
    ),
    
    # Style issues
    "style_cartoon": NegativePromptEntry(
        entry_id="style_cartoon",
        name="Anti-Cartoon",
        category="style",
        prompt="cartoon, anime, illustration, drawing, sketch, painted, artistic rendering, 3d render",
        description="Prevents non-photorealistic styles",
        severity="recommended",
    ),
    "style_watermark": NegativePromptEntry(
        entry_id="style_watermark",
        name="Anti-Watermark",
        category="style",
        prompt="watermark, text, logo, signature, copyright, stamp, overlay",
        description="Prevents unwanted text and marks",
        severity="required",
    ),
    
    # Composition issues
    "composition_crop": NegativePromptEntry(
        entry_id="composition_crop",
        name="Cropping Issues",
        category="composition",
        prompt="cropped, cut off, partial guitar, missing headstock, missing body",
        description="Ensures complete guitar in frame",
        severity="recommended",
    ),
    "composition_background": NegativePromptEntry(
        entry_id="composition_background",
        name="Background Issues",
        category="composition",
        prompt="cluttered background, distracting elements, busy background, multiple guitars",
        description="Ensures clean background",
        severity="optional",
    ),
}


# Pre-built negative prompt combinations
NEGATIVE_PROMPT_SETS = {
    "essential": [
        "quality_basic", "anatomy_strings", "anatomy_proportions", "style_watermark"
    ],
    "recommended": [
        "quality_basic", "quality_advanced", "anatomy_strings", "anatomy_frets",
        "anatomy_proportions", "anatomy_hardware", "style_watermark", "style_cartoon"
    ],
    "maximum": list(NEGATIVE_PROMPTS.keys()),
}


def build_negative_prompt(preset: str = "recommended") -> str:
    """Build a negative prompt from a preset."""
    entry_ids = NEGATIVE_PROMPT_SETS.get(preset, NEGATIVE_PROMPT_SETS["recommended"])
    prompts = [NEGATIVE_PROMPTS[eid].prompt for eid in entry_ids if eid in NEGATIVE_PROMPTS]
    return ", ".join(prompts)


# =============================================================================
# PROMPT TEMPLATES STORE (Feature 12)
# =============================================================================

_templates: dict = {}


def get_template(template_id: str) -> Optional[PromptTemplate]:
    """Get a template by ID."""
    return _templates.get(template_id)


def save_template(template: PromptTemplate) -> str:
    """Save a template."""
    _templates[template.template_id] = template
    return template.template_id


def list_templates(tags: Optional[list] = None, limit: int = 50) -> list:
    """List templates, optionally filtered by tags."""
    templates = list(_templates.values())
    if tags:
        templates = [t for t in templates if any(tag in t.tags for tag in tags)]
    return sorted(templates, key=lambda t: t.times_used, reverse=True)[:limit]


def delete_template(template_id: str) -> bool:
    """Delete a template."""
    if template_id in _templates:
        del _templates[template_id]
        return True
    return False


# =============================================================================
# GENERATE
# =============================================================================

@router.post("/generate/image", response_model=GenerateImageResponse)
def generate_advisory_image(req: GenerateImageRequest) -> GenerateImageResponse:
    """
    Generate an image and store as advisory asset.
    
    GOVERNANCE: Image is NOT approved by default.
    Human review required before workflow integration.
    """
    start_time = time.perf_counter()
    
    # Map request to engine params
    size_map = {
        "1024x1024": ImageSize.SQUARE_LG,
        "1792x1024": ImageSize.LANDSCAPE,
        "1024x1792": ImageSize.PORTRAIT,
    }
    quality_map = {
        "draft": ImageQuality.DRAFT,
        "standard": ImageQuality.STANDARD,
        "hd": ImageQuality.HD,
    }
    
    img_size = size_map.get(req.size, ImageSize.SQUARE_LG)
    img_quality = quality_map.get(req.quality, ImageQuality.STANDARD)
    
    force_provider = None
    if req.provider:
        try:
            force_provider = ImageProvider(req.provider)
        except ValueError:
            pass
    
    # Generate using existing engine
    engine = GuitarVisionEngine()
    result = engine.generate(
        user_prompt=req.prompt,
        num_images=1,
        size=img_size,
        quality=img_quality,
        photo_style=req.photo_style,
        force_provider=force_provider,
    )
    
    if not result.success or not result.images:
        raise HTTPException(
            status_code=500,
            detail={"error": "GENERATION_FAILED", "message": result.error or "Unknown error"}
        )
    
    generated = result.images[0]
    generation_time_ms = int((time.perf_counter() - start_time) * 1000)
    
    # Extract image bytes from result
    image_bytes: Optional[bytes] = None
    content_hash = ""
    
    if generated._result and generated._result.image_bytes:
        image_bytes = generated._result.image_bytes
        content_hash = compute_content_hash(image_bytes)
    elif generated.base64_data:
        import base64
        image_bytes = base64.b64decode(generated.base64_data)
        content_hash = compute_content_hash(image_bytes)
    
    if not content_hash:
        import hashlib
        content_hash = hashlib.sha256(req.prompt.encode()).hexdigest()
    
    # Parse dimensions
    width, height = 1024, 1024
    if "x" in req.size:
        width, height = map(int, req.size.split("x"))
    
    # Create advisory asset
    asset = AdvisoryAsset(
        asset_type=AdvisoryAssetType.IMAGE,
        source="ai_graphics",
        provider=result.request.provider.value,
        model="dall-e-3" if result.request.provider == ImageProvider.DALLE3 else result.request.provider.value,
        prompt=req.prompt,
        content_hash=content_hash,
        image_width=width,
        image_height=height,
        image_format="png",
        generation_time_ms=generation_time_ms,
        cost_usd=result.actual_cost,
        # GOVERNANCE: Not approved by default
        reviewed=False,
        approved_for_workflow=False,
        meta={
            "photo_style": req.photo_style,
            "quality": req.quality,
            "engineered_prompt": result.request.engineered_prompt,
            "revised_prompt": generated.revised_prompt,  # DALL-E's rewritten version
            "request_id": result.request.request_id,
        },
    )
    
    # Save to store
    store = get_advisory_store()
    store.save_asset(asset, content=image_bytes)
    
    # Save to prompt history
    prompt_store = get_prompt_history_store()
    prompt_entry = PromptHistoryEntry(
        user_id=req.user_id if hasattr(req, 'user_id') else None,
        session_id=req.session_id if hasattr(req, 'session_id') else None,
        user_prompt=req.prompt,
        engineered_prompt=result.request.engineered_prompt,
        revised_prompt=generated.revised_prompt,
        provider=asset.provider,
        model=asset.model,
        photo_style=req.photo_style,
        quality=req.quality,
        size=req.size,
        asset_id=asset.asset_id,
        success=True,
    )
    prompt_store.save_prompt(prompt_entry)
    
    logger.info(
        "advisory_image.generated",
        extra={
            "asset_id": asset.asset_id,
            "provider": asset.provider,
            "generation_time_ms": generation_time_ms,
            "cost_usd": result.actual_cost,
            "prompt_id": prompt_entry.prompt_id,
        }
    )
    
    return GenerateImageResponse(
        asset=AdvisoryAssetOut.from_asset(asset),
        message="Image generated. Requires human review before workflow use.",
    )


# =============================================================================
# READ
# =============================================================================

@router.get("/assets", response_model=ListAssetsResponse)
def list_assets(
    asset_type: Optional[str] = Query(default=None),
    reviewed: Optional[bool] = Query(default=None),
    approved: Optional[bool] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> ListAssetsResponse:
    """List advisory assets with optional filters."""
    store = get_advisory_store()
    
    type_enum = None
    if asset_type:
        try:
            type_enum = AdvisoryAssetType(asset_type)
        except ValueError:
            pass
    
    assets = store.list_assets(
        asset_type=type_enum,
        reviewed=reviewed,
        approved=approved,
        limit=limit,
    )
    
    pending = store.count_pending_review()
    
    return ListAssetsResponse(
        assets=[AdvisoryAssetOut.from_asset(a) for a in assets],
        total=len(assets),
        pending_review=pending,
    )


@router.get("/assets/{asset_id}", response_model=AdvisoryAssetOut)
def get_asset(asset_id: str) -> AdvisoryAssetOut:
    """Get a specific advisory asset."""
    store = get_advisory_store()
    asset = store.get_asset(asset_id)
    
    if asset is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "ASSET_NOT_FOUND", "asset_id": asset_id}
        )
    
    return AdvisoryAssetOut.from_asset(asset)


@router.get("/assets/{asset_id}/content")
def get_asset_content(asset_id: str) -> Response:
    """Get the binary content of an advisory asset."""
    store = get_advisory_store()
    asset = store.get_asset(asset_id)
    
    if asset is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "ASSET_NOT_FOUND", "asset_id": asset_id}
        )
    
    content = store.get_asset_content(asset)
    if content is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "CONTENT_NOT_FOUND", "asset_id": asset_id}
        )
    
    media_type = f"image/{asset.image_format}" if asset.image_format else "application/octet-stream"
    
    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": f"inline; filename={asset_id}.{asset.image_format or 'bin'}"
        }
    )


# =============================================================================
# REVIEW
# =============================================================================

@router.post("/assets/{asset_id}/review", response_model=AdvisoryAssetOut)
def review_asset(asset_id: str, req: ReviewAssetRequest) -> AdvisoryAssetOut:
    """
    Review an advisory asset.
    
    GOVERNANCE: Only humans call this endpoint.
    Sets approved_for_workflow based on review.
    
    If rejecting (approved=False), rejection_reason should be provided.
    Valid rejection reasons: poor_quality, wrong_style, anatomically_incorrect,
    wrong_guitar_type, wrong_finish, wrong_hardware, artifacts, lighting_issues,
    composition, not_photorealistic, duplicate, other
    """
    store = get_advisory_store()
    asset = store.get_asset(asset_id)
    
    if asset is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "ASSET_NOT_FOUND", "asset_id": asset_id}
        )
    
    asset.reviewed = True
    asset.approved_for_workflow = req.approved
    asset.reviewed_by = req.reviewer
    asset.reviewed_at_utc = datetime.now(timezone.utc)
    asset.review_note = req.note
    asset.rating = req.rating
    
    # Set rejection reason only if rejecting
    if not req.approved:
        asset.rejection_reason = req.rejection_reason or "other"
    else:
        asset.rejection_reason = None
    
    store.update_asset(asset)
    
    action = "approved" if req.approved else "rejected"
    logger.info(
        f"advisory_asset.{action}",
        extra={
            "asset_id": asset_id,
            "reviewed_by": req.reviewer,
            "rejection_reason": asset.rejection_reason,
            "rating": asset.rating,
        }
    )
    
    return AdvisoryAssetOut.from_asset(asset)


@router.post("/assets/{asset_id}/favorite", response_model=AdvisoryAssetOut)
def toggle_favorite(
    asset_id: str,
    favorite: bool = Query(..., description="Set favorite status"),
) -> AdvisoryAssetOut:
    """
    Toggle favorite/bookmark status for an asset.
    
    Favorites are separate from approval - you can bookmark
    an image for later review without approving it for workflow.
    """
    store = get_advisory_store()
    asset = store.get_asset(asset_id)
    
    if asset is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "ASSET_NOT_FOUND", "asset_id": asset_id}
        )
    
    asset.is_favorite = favorite
    store.update_asset(asset)
    
    action = "favorited" if favorite else "unfavorited"
    logger.info(
        f"advisory_asset.{action}",
        extra={"asset_id": asset_id}
    )
    
    return AdvisoryAssetOut.from_asset(asset)


@router.post("/review/bulk", response_model=BulkReviewResponse)
def bulk_review(req: BulkReviewRequest) -> BulkReviewResponse:
    """
    Review multiple assets in a single request.
    
    Efficient for batch approval/rejection of generated images.
    Each item can have its own approval status, rejection reason, and rating.
    """
    store = get_advisory_store()
    
    results = []
    success_count = 0
    error_count = 0
    
    for item in req.items:
        try:
            asset = store.get_asset(item.asset_id)
            
            if asset is None:
                results.append({
                    "asset_id": item.asset_id,
                    "success": False,
                    "error": "ASSET_NOT_FOUND",
                })
                error_count += 1
                continue
            
            # Apply review
            asset.reviewed = True
            asset.approved_for_workflow = item.approved
            asset.reviewed_by = req.reviewer
            asset.reviewed_at_utc = datetime.now(timezone.utc)
            asset.review_note = req.note
            asset.rating = item.rating
            
            if not item.approved:
                asset.rejection_reason = item.rejection_reason or "other"
            else:
                asset.rejection_reason = None
            
            store.update_asset(asset)
            
            results.append({
                "asset_id": item.asset_id,
                "success": True,
                "approved": item.approved,
            })
            success_count += 1
            
        except Exception as e:
            results.append({
                "asset_id": item.asset_id,
                "success": False,
                "error": str(e),
            })
            error_count += 1
    
    logger.info(
        "advisory_asset.bulk_review",
        extra={
            "reviewed_by": req.reviewer,
            "success_count": success_count,
            "error_count": error_count,
            "total_items": len(req.items),
        }
    )
    
    return BulkReviewResponse(
        success_count=success_count,
        error_count=error_count,
        results=results,
    )


@router.get("/favorites", response_model=ListAssetsResponse)
def list_favorites(
    limit: int = Query(default=50, ge=1, le=200),
) -> ListAssetsResponse:
    """List favorited/bookmarked assets."""
    store = get_advisory_store()
    
    # Get all assets and filter for favorites
    all_assets = store.list_assets(limit=1000)
    favorites = [a for a in all_assets if a.is_favorite][:limit]
    pending = len([a for a in favorites if not a.reviewed])
    
    return ListAssetsResponse(
        assets=[AdvisoryAssetOut.from_asset(a) for a in favorites],
        total=len(favorites),
        pending_review=pending,
    )


@router.get("/pending", response_model=ListAssetsResponse)
def list_pending_review(
    limit: int = Query(default=50, ge=1, le=200),
) -> ListAssetsResponse:
    """List assets pending human review."""
    store = get_advisory_store()
    
    assets = store.list_assets(reviewed=False, limit=limit)
    pending = len(assets)
    
    return ListAssetsResponse(
        assets=[AdvisoryAssetOut.from_asset(a) for a in assets],
        total=len(assets),
        pending_review=pending,
    )


# =============================================================================
# STATS
# =============================================================================

@router.get("/stats")
def get_stats():
    """Get advisory system statistics."""
    store = get_advisory_store()
    
    all_assets = store.list_assets(limit=1000)
    pending = [a for a in all_assets if not a.reviewed]
    approved = [a for a in all_assets if a.approved_for_workflow]
    rejected = [a for a in all_assets if a.reviewed and not a.approved_for_workflow]
    favorites = [a for a in all_assets if a.is_favorite]
    
    total_cost = sum(a.cost_usd or 0 for a in all_assets)
    
    by_provider = {}
    for a in all_assets:
        by_provider[a.provider] = by_provider.get(a.provider, 0) + 1
    
    # Rejection reason breakdown
    by_rejection_reason = {}
    for a in rejected:
        reason = a.rejection_reason or "unspecified"
        by_rejection_reason[reason] = by_rejection_reason.get(reason, 0) + 1
    
    # Rating breakdown
    rated_assets = [a for a in all_assets if a.rating is not None]
    avg_rating = sum(a.rating for a in rated_assets) / len(rated_assets) if rated_assets else None
    by_rating = {}
    for a in rated_assets:
        by_rating[a.rating] = by_rating.get(a.rating, 0) + 1
    
    return {
        "total_assets": len(all_assets),
        "pending_review": len(pending),
        "approved": len(approved),
        "rejected": len(rejected),
        "favorites": len(favorites),
        "total_cost_usd": round(total_cost, 4),
        "by_provider": by_provider,
        "by_rejection_reason": by_rejection_reason,
        "ratings": {
            "average": round(avg_rating, 2) if avg_rating else None,
            "count": len(rated_assets),
            "distribution": by_rating,
        },
    }


# =============================================================================
# COST COMPARISON
# =============================================================================

@router.post("/estimate", response_model=CostComparisonResponse)
def estimate_costs(req: CostEstimateRequest) -> CostComparisonResponse:
    """
    Get cost estimates across all providers before generating.
    
    Compare DALL-E 3, SDXL, SD1.5, and Guitar LoRA costs
    to make informed decisions before spending money.
    """
    # Map quality string to enum
    quality_map = {
        "draft": ImageQuality.DRAFT,
        "standard": ImageQuality.STANDARD,
        "hd": ImageQuality.HD,
        "ultra": ImageQuality.ULTRA,
    }
    quality = quality_map.get(req.quality.lower(), ImageQuality.STANDARD)
    
    # Get engine for availability check
    engine = GuitarVisionEngine()
    available_providers = {p["id"]: p["available"] for p in engine.available_providers()}
    
    estimates = []
    cheapest_cost = float("inf")
    cheapest_provider = None
    
    # Provider metadata
    provider_notes = {
        ImageProvider.DALLE3: "Best quality, highest cost. Photorealistic results.",
        ImageProvider.SDXL: "Good quality, moderate cost. Fast generation.",
        ImageProvider.SD15: "Basic quality, lowest cost. Good for drafts.",
        ImageProvider.GUITAR_LORA: "Guitar-specialized. Requires trained model.",
        ImageProvider.STUB: "Testing only. No actual generation.",
    }
    
    for provider in ImageProvider:
        if provider == ImageProvider.STUB:
            continue  # Skip stub in estimates
            
        provider_costs = PROVIDER_COSTS.get(provider, {})
        cost_per_image = provider_costs.get(quality, 0.04)
        total_cost = cost_per_image * req.num_images
        
        is_available = available_providers.get(provider.value, False)
        
        estimates.append(ProviderCostEstimate(
            provider=provider.value,
            available=is_available,
            cost_per_image=cost_per_image,
            total_cost=round(total_cost, 4),
            quality_level=quality.value,
            notes=provider_notes.get(provider),
        ))
        
        if is_available and total_cost < cheapest_cost:
            cheapest_cost = total_cost
            cheapest_provider = provider.value
    
    # Sort by cost
    estimates.sort(key=lambda e: e.total_cost)
    
    # Determine recommendations
    best_quality = "dalle3"  # DALL-E 3 is always best quality
    
    # Recommended based on quality setting
    if quality == ImageQuality.DRAFT:
        recommended = cheapest_provider or "sd15"
    elif quality in (ImageQuality.HD, ImageQuality.ULTRA):
        recommended = "dalle3"
    else:
        # Standard: balance cost and quality
        recommended = "sdxl" if available_providers.get("sdxl") else "dalle3"
    
    return CostComparisonResponse(
        estimates=estimates,
        cheapest=cheapest_provider or "sd15",
        best_quality=best_quality,
        recommended=recommended,
        num_images=req.num_images,
        quality=req.quality,
    )


# =============================================================================
# BUDGET TRACKING
# =============================================================================

@router.get("/budget/status", response_model=BudgetStatus)
def get_budget_status() -> BudgetStatus:
    """
    Get current budget status.
    
    Shows spending totals (today, week, month, total) and
    remaining budget against configured limits.
    """
    tracker = get_budget_tracker()
    store = get_advisory_store()
    return tracker.get_status(store)


@router.get("/budget/config", response_model=BudgetConfig)
def get_budget_config() -> BudgetConfig:
    """Get current budget configuration."""
    tracker = get_budget_tracker()
    return tracker.get_config()


@router.post("/budget/config", response_model=BudgetConfig)
def set_budget_config(config: BudgetConfig) -> BudgetConfig:
    """
    Set budget limits.
    
    Configure daily, weekly, monthly, and/or total spending limits.
    Set to null to remove a limit.
    """
    tracker = get_budget_tracker()
    tracker.set_config(config)
    
    logger.info(
        "budget.config_updated",
        extra={
            "daily_limit": config.daily_limit_usd,
            "weekly_limit": config.weekly_limit_usd,
            "monthly_limit": config.monthly_limit_usd,
            "total_limit": config.total_limit_usd,
        }
    )
    
    return config


@router.post("/estimate/batch", response_model=BatchEstimateResponse)
def estimate_batch_cost(req: BatchEstimateRequest) -> BatchEstimateResponse:
    """
    Get cost estimate for batch generation.
    
    Estimates total cost for generating multiple images and
    checks if it fits within budget limits.
    """
    # Map quality string to enum
    quality_map = {
        "draft": ImageQuality.DRAFT,
        "standard": ImageQuality.STANDARD,
        "hd": ImageQuality.HD,
        "ultra": ImageQuality.ULTRA,
    }
    quality = quality_map.get(req.quality.lower(), ImageQuality.STANDARD)
    
    # Determine provider
    if req.provider:
        try:
            provider = ImageProvider(req.provider)
        except ValueError:
            provider = ImageProvider.DALLE3
    else:
        provider = ImageProvider.DALLE3
    
    # Calculate cost
    provider_costs = PROVIDER_COSTS.get(provider, {})
    cost_per_image = provider_costs.get(quality, 0.04)
    total_cost = cost_per_image * len(req.prompts)
    
    # Check budget
    tracker = get_budget_tracker()
    store = get_advisory_store()
    budget_status = tracker.get_status(store)
    can_afford, warnings = tracker.can_afford(total_cost, store)
    
    warning_msg = "; ".join(warnings) if warnings else None
    
    return BatchEstimateResponse(
        num_images=len(req.prompts),
        provider=provider.value,
        quality=req.quality,
        cost_per_image=cost_per_image,
        total_cost=round(total_cost, 4),
        budget_status=budget_status,
        can_afford=can_afford,
        warning=warning_msg,
    )


@router.get("/budget/spending")
def get_spending_breakdown():
    """
    Get detailed spending breakdown by provider and time period.
    """
    store = get_advisory_store()
    tracker = get_budget_tracker()
    
    all_assets = store.list_assets(limit=10000)
    
    # By provider
    by_provider = {}
    for asset in all_assets:
        provider = asset.provider
        cost = asset.cost_usd or 0
        if provider not in by_provider:
            by_provider[provider] = {"count": 0, "cost": 0.0}
        by_provider[provider]["count"] += 1
        by_provider[provider]["cost"] += cost
    
    # Round costs
    for provider in by_provider:
        by_provider[provider]["cost"] = round(by_provider[provider]["cost"], 4)
    
    status = tracker.get_status(store)
    
    return {
        "by_provider": by_provider,
        "totals": {
            "today": status.spent_today_usd,
            "this_week": status.spent_this_week_usd,
            "this_month": status.spent_this_month_usd,
            "all_time": status.spent_total_usd,
        },
        "limits": {
            "daily": status.daily_limit_usd,
            "weekly": status.weekly_limit_usd,
            "monthly": status.monthly_limit_usd,
            "total": status.total_limit_usd,
        },
        "alerts": status.alerts,
    }


@router.get("/rejection-reasons")
def list_rejection_reasons():
    """
    List valid rejection reasons for the review endpoint.
    
    Use these values in the rejection_reason field when rejecting an asset.
    """
    return {
        "reasons": [
            {"value": r.value, "label": r.value.replace("_", " ").title()}
            for r in RejectionReason
        ],
        "usage": "POST /api/advisory/assets/{id}/review with rejection_reason field",
    }


# =============================================================================
# PROMPT HISTORY
# =============================================================================

@router.get("/prompts", response_model=PromptHistoryResponse)
def list_prompts(
    user_id: Optional[str] = Query(default=None),
    session_id: Optional[str] = Query(default=None),
    templates_only: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=200),
) -> PromptHistoryResponse:
    """
    List prompt history.
    
    Filter by user_id, session_id, or get all recent prompts.
    Use templates_only=true to get only saved templates.
    """
    store = get_prompt_history_store()
    
    if user_id:
        prompts = store.list_by_user(user_id, limit=limit, templates_only=templates_only)
    elif session_id:
        prompts = store.list_by_session(session_id, limit=limit)
    else:
        prompts = store.list_recent(limit=limit)
    
    return PromptHistoryResponse(
        prompts=prompts,
        total=len(prompts),
        user_id=user_id,
        session_id=session_id,
    )


@router.get("/prompts/{prompt_id}")
def get_prompt(prompt_id: str):
    """Get a specific prompt by ID."""
    store = get_prompt_history_store()
    entry = store.get_prompt(prompt_id)
    
    if entry is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "PROMPT_NOT_FOUND", "prompt_id": prompt_id}
        )
    
    return entry


@router.post("/prompts/{prompt_id}/template")
def save_as_template(
    prompt_id: str,
    template_name: str = Query(..., min_length=1, max_length=100),
):
    """
    Save a prompt as a reusable template.
    
    Templates can be retrieved with templates_only=true in list endpoint.
    """
    store = get_prompt_history_store()
    entry = store.mark_as_template(prompt_id, template_name)
    
    if entry is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "PROMPT_NOT_FOUND", "prompt_id": prompt_id}
        )
    
    return {
        "success": True,
        "prompt_id": prompt_id,
        "template_name": template_name,
        "message": "Prompt saved as template",
    }


@router.post("/prompts/{prompt_id}/reuse")
def reuse_prompt(prompt_id: str):
    """
    Reuse a prompt from history.
    
    Returns the prompt details ready for re-generation.
    Also increments the reuse counter.
    """
    store = get_prompt_history_store()
    entry = store.increment_reuse(prompt_id)
    
    if entry is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "PROMPT_NOT_FOUND", "prompt_id": prompt_id}
        )
    
    return {
        "prompt": entry.user_prompt,
        "photo_style": entry.photo_style,
        "quality": entry.quality,
        "size": entry.size,
        "provider": entry.provider,
        "times_reused": entry.times_reused,
        "original_asset_id": entry.asset_id,
    }


@router.get("/prompts/search/{query}")
def search_prompts(
    query: str,
    limit: int = Query(default=20, ge=1, le=100),
):
    """
    Search prompt history by text.
    
    Searches user prompts for matching text.
    """
    store = get_prompt_history_store()
    results = store.search_prompts(query, limit=limit)
    
    return {
        "query": query,
        "results": results,
        "total": len(results),
    }


@router.get("/prompts/templates/list")
def list_prompt_templates_from_history(
    user_id: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
):
    """
    List saved prompt templates from history.
    
    Templates are prompts marked for reuse.
    """
    store = get_prompt_history_store()
    
    if user_id:
        prompts = store.list_by_user(user_id, limit=limit, templates_only=True)
    else:
        # Get recent and filter for templates
        all_recent = store.list_recent(limit=500)
        prompts = [p for p in all_recent if p.is_template][:limit]
    
    return {
        "templates": prompts,
        "total": len(prompts),
    }


# =============================================================================
# STYLE PRESETS (Feature 13)
# =============================================================================

@router.get("/presets/styles")
def get_style_presets():
    """
    Get all available style presets.
    
    Use these for one-click style configuration:
    - vintage: Classic, warm tones
    - modern: Clean, contemporary
    - studio: Professional product photography
    - lifestyle: Natural environment
    - dramatic: High contrast, moody
    - artistic: Fine art approach
    """
    return {
        "presets": list(STYLE_PRESETS.values()),
        "total": len(STYLE_PRESETS),
    }


@router.get("/presets/styles/{preset_id}")
def get_style_preset(preset_id: str):
    """Get a specific style preset by ID."""
    preset = STYLE_PRESETS.get(preset_id)
    if preset is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "PRESET_NOT_FOUND", "preset_id": preset_id}
        )
    return preset


@router.post("/generate/with-preset")
def generate_with_preset(
    prompt: str = Query(..., min_length=1),
    preset_id: str = Query(...),
    provider: Optional[str] = Query(default=None),
    user_id: Optional[str] = Query(default=None),
    session_id: Optional[str] = Query(default=None),
):
    """
    Generate an image using a style preset.
    
    Combines user prompt with preset's style configuration.
    """
    preset = STYLE_PRESETS.get(preset_id)
    if preset is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "PRESET_NOT_FOUND", "preset_id": preset_id}
        )
    
    # Build enhanced prompt
    enhanced_prompt = f"{prompt}, {preset.prompt_suffix}"
    
    # Create generate request
    req = GenerateImageRequest(
        prompt=enhanced_prompt,
        quality=preset.quality,
        photo_style=preset.photo_style,
        provider=provider,
        user_id=user_id,
        session_id=session_id,
    )
    
    # Call existing generate endpoint
    return generate_advisory_image(req)


# =============================================================================
# NEGATIVE PROMPTS (Feature 14)
# =============================================================================

@router.get("/negative-prompts")
def get_negative_prompts():
    """
    Get the guitar-specific negative prompt library.
    
    Categories:
    - quality: Prevent image quality issues
    - anatomy: Prevent guitar anatomy errors
    - style: Prevent unwanted artistic styles
    - composition: Prevent framing issues
    """
    return {
        "prompts": list(NEGATIVE_PROMPTS.values()),
        "total": len(NEGATIVE_PROMPTS),
        "by_category": {
            "quality": [p for p in NEGATIVE_PROMPTS.values() if p.category == "quality"],
            "anatomy": [p for p in NEGATIVE_PROMPTS.values() if p.category == "anatomy"],
            "style": [p for p in NEGATIVE_PROMPTS.values() if p.category == "style"],
            "composition": [p for p in NEGATIVE_PROMPTS.values() if p.category == "composition"],
        },
    }


@router.get("/negative-prompts/sets")
def get_negative_prompt_sets():
    """
    Get pre-built negative prompt combinations.
    
    Sets:
    - essential: Minimum required (4 prompts)
    - recommended: Standard set (8 prompts)
    - maximum: All available prompts
    """
    return {
        "sets": {
            name: {
                "entries": ids,
                "built_prompt": build_negative_prompt(name),
            }
            for name, ids in NEGATIVE_PROMPT_SETS.items()
        },
    }


@router.get("/negative-prompts/build/{set_name}")
def build_negative_prompt_endpoint(set_name: str):
    """
    Build a negative prompt string from a preset.
    
    Returns a comma-separated string ready to use.
    """
    if set_name not in NEGATIVE_PROMPT_SETS:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "SET_NOT_FOUND",
                "set_name": set_name,
                "available": list(NEGATIVE_PROMPT_SETS.keys()),
            }
        )
    
    return {
        "set_name": set_name,
        "prompt": build_negative_prompt(set_name),
        "entry_count": len(NEGATIVE_PROMPT_SETS[set_name]),
    }


# =============================================================================
# PROMPT TEMPLATES (Feature 12 - Enhanced)
# =============================================================================

@router.post("/templates")
def create_template(
    name: str = Query(..., min_length=1, max_length=100),
    prompt_template: str = Query(..., min_length=1),
    description: Optional[str] = Query(default=None),
    photo_style: str = Query(default="product"),
    quality: str = Query(default="standard"),
    negative_prompt: Optional[str] = Query(default=None),
    tags: Optional[str] = Query(default=None, description="Comma-separated tags"),
    created_by: Optional[str] = Query(default=None),
):
    """
    Create a new prompt template.
    
    Templates can include {placeholders} that get filled at generation time.
    Example: "{finish} {body_shape} with {hardware} hardware"
    """
    import re
    
    # Extract placeholders from template
    placeholders = re.findall(r'\{(\w+)\}', prompt_template)
    
    # Parse tags
    tag_list = [t.strip() for t in tags.split(",")] if tags else []
    
    template = PromptTemplate(
        name=name,
        description=description,
        prompt_template=prompt_template,
        photo_style=photo_style,
        quality=quality,
        negative_prompt=negative_prompt or build_negative_prompt("recommended"),
        created_by=created_by,
        placeholders=placeholders,
        tags=tag_list,
    )
    
    save_template(template)
    
    return {
        "success": True,
        "template": template,
    }


@router.get("/templates")
def list_all_templates(
    tags: Optional[str] = Query(default=None, description="Comma-separated tags to filter"),
    limit: int = Query(default=50, ge=1, le=100),
):
    """List all saved prompt templates."""
    tag_list = [t.strip() for t in tags.split(",")] if tags else None
    templates = list_templates(tags=tag_list, limit=limit)
    
    return {
        "templates": templates,
        "total": len(templates),
    }


@router.get("/templates/{template_id}")
def get_template_endpoint(template_id: str):
    """Get a specific template by ID."""
    template = get_template(template_id)
    if template is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "TEMPLATE_NOT_FOUND", "template_id": template_id}
        )
    return template


@router.delete("/templates/{template_id}")
def delete_template_endpoint(template_id: str):
    """Delete a template."""
    if not delete_template(template_id):
        raise HTTPException(
            status_code=404,
            detail={"error": "TEMPLATE_NOT_FOUND", "template_id": template_id}
        )
    return {"success": True, "deleted": template_id}


@router.post("/templates/{template_id}/generate")
def generate_from_template(
    template_id: str,
    provider: Optional[str] = Query(default=None),
    user_id: Optional[str] = Query(default=None),
    session_id: Optional[str] = Query(default=None),
    **placeholders,
):
    """
    Generate an image using a template.
    
    Fill placeholders via query params:
    /templates/tpl_abc123/generate?body_shape=les%20paul&finish=sunburst
    """
    template = get_template(template_id)
    if template is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "TEMPLATE_NOT_FOUND", "template_id": template_id}
        )
    
    # Fill placeholders
    prompt = template.prompt_template
    for key, value in placeholders.items():
        prompt = prompt.replace(f"{{{key}}}", str(value))
    
    # Check for unfilled placeholders
    import re
    unfilled = re.findall(r'\{(\w+)\}', prompt)
    if unfilled:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "MISSING_PLACEHOLDERS",
                "unfilled": unfilled,
                "message": f"Missing values for: {', '.join(unfilled)}",
            }
        )
    
    # Increment usage counter
    template.times_used += 1
    save_template(template)
    
    # Generate
    req = GenerateImageRequest(
        prompt=prompt,
        quality=template.quality,
        photo_style=template.photo_style,
        provider=provider,
        user_id=user_id,
        session_id=session_id,
    )
    
    return generate_advisory_image(req)
