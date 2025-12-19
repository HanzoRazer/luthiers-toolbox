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
    ListAssetsResponse,
)
from ..advisory_store import get_advisory_store, compute_content_hash
from ..image_providers import (
    GuitarVisionEngine,
    ImageSize,
    ImageQuality,
    ImageProvider,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/advisory", tags=["Advisory Assets"])


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
            "request_id": result.request.request_id,
        },
    )
    
    # Save to store
    store = get_advisory_store()
    store.save_asset(asset, content=image_bytes)
    
    logger.info(
        "advisory_image.generated",
        extra={
            "asset_id": asset.asset_id,
            "provider": asset.provider,
            "generation_time_ms": generation_time_ms,
            "cost_usd": result.actual_cost,
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
    
    store.update_asset(asset)
    
    action = "approved" if req.approved else "rejected"
    logger.info(
        f"advisory_asset.{action}",
        extra={
            "asset_id": asset_id,
            "reviewed_by": req.reviewer,
        }
    )
    
    return AdvisoryAssetOut.from_asset(asset)


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
    
    total_cost = sum(a.cost_usd or 0 for a in all_assets)
    
    by_provider = {}
    for a in all_assets:
        by_provider[a.provider] = by_provider.get(a.provider, 0) + 1
    
    return {
        "total_assets": len(all_assets),
        "pending_review": len(pending),
        "approved": len(approved),
        "rejected": len(rejected),
        "total_cost_usd": round(total_cost, 4),
        "by_provider": by_provider,
    }
