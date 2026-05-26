"""
Strategy Export Router

CAM Dev Order 7U: HTTP endpoints for strategy/export interoperability.

Provides endpoints for:
  - Compatibility evaluation
  - Review-safe export packaging
  - CI summary

7U invariants:
  - No endpoint authorizes execution
  - No endpoint allows machine output
  - No endpoint invokes serializers
  - No endpoint generates G-code
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.cam.strategy_export_compatibility import (
    StrategyExportCompatibilityEvaluation,
    evaluate_general_export_readiness,
    evaluate_targeted_translator_compatibility,
)
from app.cam.review_safe_export_package import (
    ReviewSafeExportPackage,
    PackageReviewStatus,
    create_review_safe_export_package,
    add_compatibility_evaluation,
    add_strategy_to_package,
    add_geometry_authority_ref,
    update_review_status,
    validate_package_for_review,
)
from app.cam.strategy_export_registry import (
    register_strategy_export_compatibility,
    get_strategy_export_compatibility,
    list_strategy_export_compatibilities,
    list_evaluations_by_workspace,
    list_evaluations_by_strategy,
    register_review_safe_export_package,
    get_review_safe_export_package,
    list_review_safe_export_packages,
    list_packages_by_workspace,
    list_packages_by_strategy,
    list_packages_by_review_status,
    get_ci_summary,
)


router = APIRouter(
    prefix="/api/cam/strategy-export",
    tags=["CAM", "Strategy", "Export", "Compatibility"],
)


class StrategyExportMeta(BaseModel):
    """Metadata for Strategy Export API."""

    version: str = "7U"
    execution_authorized: bool = False
    machine_output_allowed: bool = False
    serializer_invocation_allowed: bool = False
    generates_gcode: bool = False
    description: str = "Strategy/export interoperability contracts — no execution"


@router.get("/", response_model=StrategyExportMeta)
async def get_meta() -> StrategyExportMeta:
    """Get Strategy Export API metadata."""
    return StrategyExportMeta()


class EvaluateCompatibilityRequest(BaseModel):
    """Request to evaluate strategy/export compatibility."""

    workspace_id: Optional[str] = None
    strategy_id: Optional[str] = None
    target_translator_id: Optional[str] = None
    geometry_authority_ref_ids: Optional[List[str]] = None
    modality_id: Optional[str] = None
    review_status: Optional[str] = None
    workspace_status: Optional[str] = None


@router.post("/evaluate", response_model=StrategyExportCompatibilityEvaluation)
async def evaluate_compatibility(
    request: EvaluateCompatibilityRequest,
) -> StrategyExportCompatibilityEvaluation:
    """
    Evaluate strategy/export compatibility.

    If target_translator_id is provided, performs targeted evaluation.
    Otherwise, performs general export readiness evaluation.
    """
    if not request.workspace_id and not request.strategy_id:
        raise HTTPException(
            400,
            "Either workspace_id or strategy_id is required"
        )

    if request.target_translator_id:
        evaluation = evaluate_targeted_translator_compatibility(
            workspace_id=request.workspace_id,
            strategy_id=request.strategy_id,
            target_translator_id=request.target_translator_id,
            geometry_authority_ref_ids=request.geometry_authority_ref_ids,
            modality_id=request.modality_id,
            review_status=request.review_status,
            workspace_status=request.workspace_status,
        )
    else:
        evaluation = evaluate_general_export_readiness(
            workspace_id=request.workspace_id,
            strategy_id=request.strategy_id,
            geometry_authority_ref_ids=request.geometry_authority_ref_ids,
            modality_id=request.modality_id,
            review_status=request.review_status,
            workspace_status=request.workspace_status,
        )

    return register_strategy_export_compatibility(evaluation)


@router.get("/evaluations", response_model=List[StrategyExportCompatibilityEvaluation])
async def list_evaluations() -> List[StrategyExportCompatibilityEvaluation]:
    """List all compatibility evaluations."""
    return list_strategy_export_compatibilities()


@router.get("/evaluations/{evaluation_id}", response_model=StrategyExportCompatibilityEvaluation)
async def get_evaluation(evaluation_id: str) -> StrategyExportCompatibilityEvaluation:
    """Get a specific compatibility evaluation by ID."""
    evaluation = get_strategy_export_compatibility(evaluation_id)
    if not evaluation:
        raise HTTPException(404, f"Evaluation '{evaluation_id}' not found")
    return evaluation


@router.get(
    "/evaluations/by-workspace/{workspace_id}",
    response_model=List[StrategyExportCompatibilityEvaluation],
)
async def get_evaluations_by_workspace(
    workspace_id: str,
) -> List[StrategyExportCompatibilityEvaluation]:
    """List all evaluations for a workspace."""
    return list_evaluations_by_workspace(workspace_id)


@router.get(
    "/evaluations/by-strategy/{strategy_id}",
    response_model=List[StrategyExportCompatibilityEvaluation],
)
async def get_evaluations_by_strategy(
    strategy_id: str,
) -> List[StrategyExportCompatibilityEvaluation]:
    """List all evaluations for a strategy."""
    return list_evaluations_by_strategy(strategy_id)


class CreatePackageRequest(BaseModel):
    """Request to create a review-safe export package."""

    workspace_id: Optional[str] = None
    strategy_id: Optional[str] = None
    geometry_authority_ref_ids: Optional[List[str]] = None
    export_object_id: Optional[str] = None
    translation_artifact_id: Optional[str] = None
    translator_id: Optional[str] = None
    title: str = ""
    description: str = ""


@router.post("/packages", response_model=ReviewSafeExportPackage)
async def create_package(
    request: CreatePackageRequest,
) -> ReviewSafeExportPackage:
    """Create and register a review-safe export package."""
    package = create_review_safe_export_package(
        workspace_id=request.workspace_id,
        strategy_id=request.strategy_id,
        geometry_authority_ref_ids=request.geometry_authority_ref_ids,
        export_object_id=request.export_object_id,
        translation_artifact_id=request.translation_artifact_id,
        translator_id=request.translator_id,
        title=request.title,
        description=request.description,
    )
    return register_review_safe_export_package(package)


@router.get("/packages", response_model=List[ReviewSafeExportPackage])
async def list_packages() -> List[ReviewSafeExportPackage]:
    """List all review-safe export packages."""
    return list_review_safe_export_packages()


@router.get("/packages/{package_id}", response_model=ReviewSafeExportPackage)
async def get_package(package_id: str) -> ReviewSafeExportPackage:
    """Get a specific package by ID."""
    package = get_review_safe_export_package(package_id)
    if not package:
        raise HTTPException(404, f"Package '{package_id}' not found")
    return package


@router.get(
    "/packages/by-workspace/{workspace_id}",
    response_model=List[ReviewSafeExportPackage],
)
async def get_packages_by_workspace(
    workspace_id: str,
) -> List[ReviewSafeExportPackage]:
    """List all packages for a workspace."""
    return list_packages_by_workspace(workspace_id)


@router.get(
    "/packages/by-strategy/{strategy_id}",
    response_model=List[ReviewSafeExportPackage],
)
async def get_packages_by_strategy(
    strategy_id: str,
) -> List[ReviewSafeExportPackage]:
    """List all packages for a strategy."""
    return list_packages_by_strategy(strategy_id)


@router.get(
    "/packages/by-review-status/{review_status}",
    response_model=List[ReviewSafeExportPackage],
)
async def get_packages_by_status(
    review_status: PackageReviewStatus,
) -> List[ReviewSafeExportPackage]:
    """List all packages with a specific review status."""
    return list_packages_by_review_status(review_status)


class AddEvaluationRequest(BaseModel):
    """Request to add an evaluation to a package."""

    evaluation_id: str


@router.post(
    "/packages/{package_id}/evaluations",
    response_model=ReviewSafeExportPackage,
)
async def add_evaluation_to_package(
    package_id: str,
    request: AddEvaluationRequest,
) -> ReviewSafeExportPackage:
    """Add a compatibility evaluation to a package."""
    package = get_review_safe_export_package(package_id)
    if not package:
        raise HTTPException(404, f"Package '{package_id}' not found")

    evaluation = get_strategy_export_compatibility(request.evaluation_id)
    if not evaluation:
        raise HTTPException(404, f"Evaluation '{request.evaluation_id}' not found")

    updated = add_compatibility_evaluation(package, request.evaluation_id)
    return updated


class UpdateReviewStatusRequest(BaseModel):
    """Request to update package review status."""

    review_status: PackageReviewStatus
    reviewer_note: Optional[str] = None


@router.post(
    "/packages/{package_id}/review-status",
    response_model=ReviewSafeExportPackage,
)
async def update_package_review_status(
    package_id: str,
    request: UpdateReviewStatusRequest,
) -> ReviewSafeExportPackage:
    """Update the review status of a package."""
    package = get_review_safe_export_package(package_id)
    if not package:
        raise HTTPException(404, f"Package '{package_id}' not found")

    updated = update_review_status(
        package,
        request.review_status,
        request.reviewer_note,
    )
    return updated


@router.post("/packages/{package_id}/validate")
async def validate_package(package_id: str) -> Dict[str, Any]:
    """Validate that a package is ready for review."""
    package = get_review_safe_export_package(package_id)
    if not package:
        raise HTTPException(404, f"Package '{package_id}' not found")

    is_valid, issues = validate_package_for_review(package)

    return {
        "package_id": package_id,
        "is_valid": is_valid,
        "issues": issues,
        "review_status": package.review_status,
        "blocking_issues": package.blocking_issues,
        "warnings": package.warnings,
    }


@router.get("/ci")
async def get_ci_status() -> Dict[str, Any]:
    """
    Get CI summary for strategy/export compatibility health.

    Returns:
      - total_evaluations
      - total_packages
      - green_count
      - yellow_count
      - red_count
      - package_without_review_count
      - packages_with_blocking_issues
      - packages_approved
      - status: pass|warn|fail

    Status:
      - fail: any RED evaluation or package with blocking issues
      - warn: YELLOW evaluations or packages lacking review
      - pass: all GREEN evaluations and packages are review-safe
    """
    return get_ci_summary()
