"""
Teaching Loop Routes

API endpoints for exporting approved Advisory Assets to LoRA training format.

Flow:
1. DALL-E generates → AdvisoryAsset
2. Human reviews → approves
3. POST /api/teaching/export → training dataset
4. Kohya trains → Guitar LoRA
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..services.teaching_loop import (
    TeachingLoopExporter,
    ExportConfig,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/teaching", tags=["Teaching Loop", "Training"])


# =============================================================================
# SCHEMAS
# =============================================================================

class ExportRequest(BaseModel):
    """Request to export approved assets to training format."""
    output_dir: str = "./guitar_training_dataset"
    trigger_word: str = "guitar_photo"
    min_confidence: float = 0.0
    overwrite: bool = False


class ExportResponse(BaseModel):
    """Response from export operation."""
    success: bool
    total_approved: int
    exported_count: int
    skipped_count: int
    error_count: int
    output_dir: str
    message: str


class StatsResponse(BaseModel):
    """Statistics about approved assets and exports."""
    approved_count: int
    existing_images: int
    existing_captions: int
    by_provider: dict
    by_category: dict
    output_dir: str
    ready_to_train: bool


# =============================================================================
# ROUTES
# =============================================================================

@router.post("/export", response_model=ExportResponse)
def export_to_training(req: ExportRequest) -> ExportResponse:
    """
    Export all approved Advisory Assets to LoRA training format.

    Creates:
    - images/*.png - Training images
    - images/*.txt - Captions for each image
    - metadata.jsonl - Full metadata
    - export_log.json - Export report
    """
    config = ExportConfig(
        output_dir=Path(req.output_dir),
        trigger_word=req.trigger_word,
        min_confidence=req.min_confidence,
        overwrite_existing=req.overwrite,
    )

    exporter = TeachingLoopExporter(config)

    try:
        report = exporter.export_all()
    except Exception as e:
        logger.error(f"Export failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "EXPORT_FAILED", "message": str(e)}
        )

    success = report.exported_count > 0 or report.total_approved == 0

    if report.total_approved == 0:
        message = "No approved assets to export. Approve some images first."
    elif report.exported_count == 0:
        message = f"All {report.total_approved} approved assets already exported."
    else:
        message = f"Exported {report.exported_count} images to training dataset."

    return ExportResponse(
        success=success,
        total_approved=report.total_approved,
        exported_count=report.exported_count,
        skipped_count=report.skipped_count,
        error_count=report.error_count,
        output_dir=str(config.output_dir),
        message=message,
    )


@router.get("/stats", response_model=StatsResponse)
def get_stats(
    output_dir: str = Query(default="./guitar_training_dataset"),
) -> StatsResponse:
    """Get statistics about approved assets and existing exports."""

    config = ExportConfig(output_dir=Path(output_dir))
    exporter = TeachingLoopExporter(config)

    stats = exporter.get_stats()

    # Ready to train if we have at least 10 images
    ready = stats["existing_images"] >= 10

    return StatsResponse(
        approved_count=stats["approved_count"],
        existing_images=stats["existing_images"],
        existing_captions=stats["existing_captions"],
        by_provider=stats["by_provider"],
        by_category=stats["by_category"],
        output_dir=stats["output_dir"],
        ready_to_train=ready,
    )


@router.get("/ready")
def check_ready(
    output_dir: str = Query(default="./guitar_training_dataset"),
    min_images: int = Query(default=10),
):
    """Check if enough training data is ready."""

    config = ExportConfig(output_dir=Path(output_dir))
    exporter = TeachingLoopExporter(config)

    stats = exporter.get_stats()

    ready = stats["existing_images"] >= min_images

    return {
        "ready": ready,
        "images_available": stats["existing_images"],
        "images_required": min_images,
        "approved_pending_export": stats["approved_count"] - stats["existing_images"],
        "next_step": (
            "Run Kohya training" if ready
            else f"Need {min_images - stats['existing_images']} more approved images"
        ),
    }


@router.get("/workflow")
def get_workflow():
    """Get the teaching loop workflow status and next steps."""

    from ..advisory_store import get_advisory_store
    from ..schemas.advisory_schemas import AdvisoryAssetType

    store = get_advisory_store()

    # Count assets by state
    all_images = store.list_assets(asset_type=AdvisoryAssetType.IMAGE, limit=10000)
    pending = [a for a in all_images if not a.reviewed]
    approved = [a for a in all_images if a.approved_for_workflow]
    rejected = [a for a in all_images if a.reviewed and not a.approved_for_workflow]

    # Determine current stage
    if len(all_images) == 0:
        stage = "generate"
        next_step = "POST /api/advisory/generate/image to create images"
    elif len(pending) > 0:
        stage = "review"
        next_step = f"Review {len(pending)} pending images at POST /api/advisory/assets/{{id}}/review"
    elif len(approved) < 10:
        stage = "generate_more"
        next_step = f"Generate more images ({len(approved)}/10 minimum for training)"
    else:
        stage = "export"
        next_step = "POST /api/teaching/export to create training dataset"

    return {
        "stage": stage,
        "next_step": next_step,
        "counts": {
            "total_generated": len(all_images),
            "pending_review": len(pending),
            "approved": len(approved),
            "rejected": len(rejected),
        },
        "workflow": [
            {"step": 1, "name": "Generate", "action": "POST /api/advisory/generate/image"},
            {"step": 2, "name": "Review", "action": "POST /api/advisory/assets/{id}/review"},
            {"step": 3, "name": "Export", "action": "POST /api/teaching/export"},
            {"step": 4, "name": "Train", "action": "Run Kohya with exported dataset"},
        ],
    }
