"""
Vision Service - AI Image Generation Orchestration

Cross-domain orchestration between Guitar Vision Engine and Advisory Assets.
Lives in services/ because it bridges AI sandbox with governance layer.

Architecture Layer: ORCHESTRATION (Layer 5)
See: docs/governance/ARCHITECTURE_INVARIANTS.md

This service:
- Coordinates vision generation with advisory asset creation
- Bridges AI-generated images to the review workflow
- Provides audit trail via request_id correlation
- Does NOT contain image generation logic (delegates to ai_graphics/)

Usage:
    from app.services.vision_service import (
        generate_and_store,
        get_vocabulary,
        list_providers,
    )
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from uuid import uuid4

# AI Sandbox imports (generation lives there)
from .._experimental.ai_graphics.image_providers import (
    GuitarVisionEngine,
    ImageProvider,
    ImageSize,
    ImageQuality,
    ImageGenerationResult,
    PROVIDER_COSTS,
)
from .._experimental.ai_graphics.prompt_engine import (
    engineer_guitar_prompt,
    parse_guitar_request,
    GuitarPrompt,
    BODY_SHAPES,
    FINISHES,
    WOODS,
    HARDWARE,
    INLAYS,
    PHOTOGRAPHY_STYLES,
)
from .._experimental.ai_graphics.advisory_store import AdvisoryAssetStore
from .._experimental.ai_graphics.schemas.advisory_schemas import (
    AdvisoryAsset,
    AdvisoryAssetType,
)

# Hashing for content addressing
from ..rmos.runs_v2.hashing import sha256_text


# =============================================================================
# Singleton Engine
# =============================================================================

_engine: Optional[GuitarVisionEngine] = None
_advisory_store: Optional[AdvisoryAssetStore] = None


def _get_engine() -> GuitarVisionEngine:
    """Get or create the engine singleton."""
    global _engine
    if _engine is None:
        _engine = GuitarVisionEngine()
    return _engine


def _get_advisory_store() -> AdvisoryAssetStore:
    """Get or create the advisory store singleton."""
    global _advisory_store
    if _advisory_store is None:
        _advisory_store = AdvisoryAssetStore()
    return _advisory_store


# =============================================================================
# Generation Workflows
# =============================================================================

def generate_and_store(
    *,
    prompt: str,
    num_images: int = 1,
    size: str = "1024x1024",
    quality: str = "standard",
    photo_style: Optional[str] = None,
    provider: Optional[str] = None,
    prefer_quality: bool = False,
    prefer_cost: bool = False,
    request_id: Optional[str] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate guitar image(s) and store as AdvisoryAssets.

    This is the primary entry point for vision generation with full
    governance integration. Each generated image becomes an AdvisoryAsset
    that requires review before workflow attachment.

    Args:
        prompt: Natural language description of the guitar
        num_images: Number of images to generate (1-4)
        size: Image size (512x512, 1024x1024, etc.)
        quality: Quality level (draft, standard, hd)
        photo_style: Photography style override
        provider: Force specific provider (dalle3, sdxl, stub)
        prefer_quality: Prefer quality over cost
        prefer_cost: Prefer cost over quality
        request_id: Correlation ID for audit trail
        user_id: User identifier for tracking
        session_id: Session identifier for tracking

    Returns:
        Dict with:
        - success: bool
        - request_id: str
        - assets: List[AdvisoryAsset] (created assets)
        - engineered_prompt: str
        - provider_used: str
        - total_cost: float
        - error: Optional[str]
    """
    import time
    start = time.time()

    # Generate request_id if not provided
    if request_id is None:
        request_id = f"vis_{uuid4().hex[:12]}"

    engine = _get_engine()
    store = _get_advisory_store()

    # Map string values to enums
    size_map = {
        "512x512": ImageSize.SQUARE_SM,
        "768x768": ImageSize.SQUARE_MD,
        "1024x1024": ImageSize.SQUARE_LG,
        "768x1024": ImageSize.PORTRAIT,
        "1024x768": ImageSize.LANDSCAPE,
        "1792x1024": ImageSize.WIDE,
        "1024x1792": ImageSize.TALL,
    }

    quality_map = {
        "draft": ImageQuality.DRAFT,
        "standard": ImageQuality.STANDARD,
        "hd": ImageQuality.HD,
    }

    provider_map = {
        "dalle3": ImageProvider.DALLE3,
        "sdxl": ImageProvider.SDXL,
        "guitar_lora": ImageProvider.GUITAR_LORA,
        "stub": ImageProvider.STUB,
    }

    # Engineer the prompt first
    guitar_prompt = engineer_guitar_prompt(
        prompt,
        photo_style=photo_style,
    )
    parsed = guitar_prompt.parsed_request

    try:
        # Generate images
        result = engine.generate(
            user_prompt=prompt,
            num_images=num_images,
            size=size_map.get(size, ImageSize.SQUARE_LG),
            quality=quality_map.get(quality, ImageQuality.STANDARD),
            photo_style=photo_style,
            prefer_quality=prefer_quality,
            prefer_cost=prefer_cost,
            force_provider=provider_map.get(provider) if provider else None,
        )

        if not result.success:
            return {
                "success": False,
                "request_id": request_id,
                "assets": [],
                "engineered_prompt": guitar_prompt.positive_prompt,
                "provider_used": "none",
                "total_cost": 0.0,
                "error": result.error,
            }

        # Create AdvisoryAsset for each generated image
        created_assets = []
        for img in result.images:
            # Compute content hash
            content_hash = sha256_text(img.base64_data or img.url or img.image_id)

            asset = AdvisoryAsset(
                asset_type=AdvisoryAssetType.IMAGE,
                source="ai_graphics",
                provider=img.provider.value,
                model=_get_model_name(img.provider),
                request_id=request_id,
                provider_request_id=img.image_id,
                prompt=prompt,
                prompt_hash=sha256_text(prompt),
                content_hash=content_hash,
                content_uri=img.url,
                image_width=_parse_size(size)[0],
                image_height=_parse_size(size)[1],
                image_format="png",
                generation_time_ms=int(img.generation_time_ms),
                cost_usd=result.actual_cost / len(result.images),
                meta={
                    "engineered_prompt": guitar_prompt.positive_prompt,
                    "negative_prompt": guitar_prompt.negative_prompt,
                    "detected_category": parsed.category.value,
                    "detected_body_shape": parsed.body_shape,
                    "detected_finish": parsed.finish,
                    "parse_confidence": parsed.confidence,
                    "quality": quality,
                    "photo_style": photo_style,
                    "user_id": user_id,
                    "session_id": session_id,
                },
            )

            # Store the asset
            store.put(asset)
            created_assets.append(asset)

        elapsed_ms = (time.time() - start) * 1000

        return {
            "success": True,
            "request_id": request_id,
            "assets": [_asset_to_dict(a) for a in created_assets],
            "engineered_prompt": guitar_prompt.positive_prompt,
            "negative_prompt": guitar_prompt.negative_prompt,
            "detected_category": parsed.category.value,
            "detected_body_shape": parsed.body_shape,
            "detected_finish": parsed.finish,
            "provider_used": result.request.provider.value,
            "total_cost": result.actual_cost,
            "total_time_ms": elapsed_ms,
            "error": None,
        }

    except Exception as e:
        return {
            "success": False,
            "request_id": request_id,
            "assets": [],
            "engineered_prompt": guitar_prompt.positive_prompt,
            "provider_used": "none",
            "total_cost": 0.0,
            "error": str(e),
        }


def engineer_prompt_only(
    *,
    prompt: str,
    photo_style: Optional[str] = None,
    model_target: str = "general",
) -> Dict[str, Any]:
    """
    Engineer a prompt without generating an image.

    Useful for previewing prompts before generation.

    Args:
        prompt: Natural language description
        photo_style: Photography style
        model_target: Optimize for (general, dalle, sdxl)

    Returns:
        Dict with positive_prompt, negative_prompt, parsed details
    """
    guitar_prompt = engineer_guitar_prompt(
        prompt,
        photo_style=photo_style,
        model_target=model_target,
    )
    parsed = guitar_prompt.parsed_request

    return {
        "user_input": prompt,
        "positive_prompt": guitar_prompt.positive_prompt,
        "negative_prompt": guitar_prompt.negative_prompt,
        "category": parsed.category.value,
        "body_shape": parsed.body_shape,
        "body_shape_expanded": parsed.body_shape_expanded,
        "finish": parsed.finish,
        "finish_expanded": parsed.finish_expanded,
        "woods": parsed.woods,
        "hardware": parsed.hardware,
        "inlays": parsed.inlays,
        "custom_terms": parsed.custom_terms,
        "confidence": parsed.confidence,
    }


# =============================================================================
# Provider & Vocabulary
# =============================================================================

def list_providers() -> Dict[str, Any]:
    """
    List available image generation providers.

    Returns:
        Dict with providers list, default provider, routing status
    """
    engine = _get_engine()
    available = engine.router.get_available_providers()

    provider_info = {
        ImageProvider.DALLE3: {
            "name": "DALL-E 3",
            "description": "OpenAI DALL-E 3 - High quality, general purpose",
        },
        ImageProvider.SDXL: {
            "name": "Stable Diffusion XL",
            "description": "Self-hosted, cost-effective",
        },
        ImageProvider.GUITAR_LORA: {
            "name": "Guitar LoRA",
            "description": "Fine-tuned guitar specialist",
        },
        ImageProvider.STUB: {
            "name": "Stub",
            "description": "Testing without real generation",
        },
    }

    providers = []
    for provider_id in [ImageProvider.DALLE3, ImageProvider.SDXL,
                        ImageProvider.GUITAR_LORA, ImageProvider.STUB]:
        costs = PROVIDER_COSTS.get(provider_id, {})
        info = provider_info.get(provider_id, {})
        providers.append({
            "id": provider_id.value,
            "name": info.get("name", provider_id.value),
            "available": provider_id in available,
            "costs": {q.value: c for q, c in costs.items()},
            "description": info.get("description", ""),
        })

    # Determine default
    if ImageProvider.GUITAR_LORA in available:
        default = "guitar_lora"
    elif ImageProvider.DALLE3 in available:
        default = "dalle3"
    elif ImageProvider.SDXL in available:
        default = "sdxl"
    else:
        default = "stub"

    return {
        "providers": providers,
        "default_provider": default,
        "routing_enabled": True,
    }


def get_vocabulary() -> Dict[str, Any]:
    """
    Get vocabulary for UI dropdowns.

    Returns organized lists of body shapes, finishes, woods, etc.
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

    # Organize finishes
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

    return {
        "body_shapes": body_shapes_by_cat,
        "finishes": finishes_by_type,
        "woods": list(WOODS.keys()),
        "hardware": list(HARDWARE.keys()),
        "inlays": list(INLAYS.keys()),
        "photo_styles": list(PHOTOGRAPHY_STYLES.keys()),
    }


# =============================================================================
# Feedback (Teaching Loop)
# =============================================================================

def record_feedback(
    *,
    asset_id: str,
    selected: bool,
    rating: Optional[int] = None,
    reviewer: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Record user feedback on a generated image.

    Feeds the teacher-student learning loop for provider routing.

    Args:
        asset_id: The advisory asset ID
        selected: Whether this image was selected as best
        rating: Optional 1-5 rating
        reviewer: Who provided the feedback

    Returns:
        Dict with success status and message
    """
    store = _get_advisory_store()
    engine = _get_engine()

    try:
        asset = store.get(asset_id)
        if asset is None:
            return {
                "success": False,
                "message": f"Asset {asset_id} not found",
            }

        # Update engine router scores
        engine.router.record_feedback(
            category=asset.meta.get("detected_category", "unknown"),
            provider=ImageProvider(asset.provider),
            was_selected=selected,
            rating=rating,
        )

        return {
            "success": True,
            "message": f"Feedback recorded for {asset_id}",
            "provider_scores_updated": True,
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to record feedback: {e}",
        }


# =============================================================================
# Helpers
# =============================================================================

def _get_model_name(provider: ImageProvider) -> str:
    """Get model name for a provider."""
    model_names = {
        ImageProvider.DALLE3: "dall-e-3",
        ImageProvider.SDXL: "sd-xl-base-1.0",
        ImageProvider.GUITAR_LORA: "guitar-lora-v1",
        ImageProvider.STUB: "stub",
    }
    return model_names.get(provider, "unknown")


def _parse_size(size: str) -> tuple:
    """Parse size string to (width, height)."""
    try:
        w, h = size.split("x")
        return int(w), int(h)
    except Exception:
        return 1024, 1024


def _asset_to_dict(asset: AdvisoryAsset) -> Dict[str, Any]:
    """Convert AdvisoryAsset to dict for API response."""
    return {
        "asset_id": asset.asset_id,
        "asset_type": asset.asset_type.value,
        "created_at_utc": asset.created_at_utc.isoformat(),
        "provider": asset.provider,
        "model": asset.model,
        "prompt": asset.prompt,
        "content_hash": asset.content_hash,
        "content_uri": asset.content_uri,
        "image_width": asset.image_width,
        "image_height": asset.image_height,
        "generation_time_ms": asset.generation_time_ms,
        "cost_usd": asset.cost_usd,
        "reviewed": asset.reviewed,
        "approved_for_workflow": asset.approved_for_workflow,
        "request_id": asset.request_id,
    }
