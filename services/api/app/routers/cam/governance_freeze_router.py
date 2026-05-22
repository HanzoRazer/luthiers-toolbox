"""
Governance Freeze Router

CAM Dev Order 7Z: Governance baseline freeze and release readiness endpoints.

Provides:
  - Freeze CRUD
  - Release readiness evaluation endpoint
  - Package creation endpoint
  - Status endpoint

7Z invariants:
  - All endpoints require human review
  - No auto-release authorization
  - No release authorization
  - No execution authorization
  - No machine output

Core principle:
  Router exposes governance freezes for human review.
  It does not authorize release or execution.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.cam.governance_baseline_freeze import (
    GovernanceBaselineFreeze,
    create_governance_baseline_freeze,
    get_freeze_summary,
)
from app.cam.release_readiness_evaluation import (
    ReleaseReadinessEvaluation,
    evaluate_freeze_readiness,
    build_readiness_evaluation_from_ci,
    get_readiness_status_message,
    get_evaluation_summary_dict,
)
from app.cam.governance_release_package import (
    GovernanceReleasePackage,
    create_governance_release_package,
    get_package_summary,
    get_package_review_context,
)
from app.cam.governance_freeze_registry import (
    register_governance_freeze,
    get_governance_freeze,
    get_latest_governance_freeze,
    list_governance_freezes,
    list_governance_freezes_by_status,
    update_freeze_status,
    register_release_evaluation,
    get_release_evaluation,
    get_latest_release_evaluation,
    list_release_evaluations,
    list_evaluations_for_freeze,
    register_governance_package,
    get_governance_package,
    get_latest_governance_package,
    list_governance_packages,
    get_governance_status_summary,
)
from app.cam.federation_ci_registry import (
    get_federation_drift_baseline,
    get_latest_federation_ci_summary,
)


router = APIRouter(prefix="/api/cam/governance-freeze", tags=["CAM", "Governance", "Release"])


# ─────────────────────────────────────────────────────────────────────────────
# Request/Response models
# ─────────────────────────────────────────────────────────────────────────────

class CreateFreezeRequest(BaseModel):
    """Request to create a governance baseline freeze."""
    freeze_name: str
    baseline_id: Optional[str] = None
    ci_summary_id: Optional[str] = None


class FreezeResponse(BaseModel):
    """Response containing a freeze."""
    freeze_id: str
    freeze_name: str
    baseline_id: Optional[str]
    ci_summary_id: Optional[str]
    ci_status_at_freeze: Optional[str]
    federation_ref_count_at_freeze: int
    continuity_record_count_at_freeze: int
    package_count_at_freeze: int
    blocking_issue_count: int
    warning_count: int
    status: str
    human_review_required: bool
    release_authorized: bool
    deterministic_freeze_hash: str


class EvaluateRequest(BaseModel):
    """Request to evaluate freeze readiness."""
    freeze_id: str
    warning_threshold: int = Field(default=0)


class EvaluationResponse(BaseModel):
    """Response containing a readiness evaluation."""
    evaluation_id: str
    freeze_id: str
    readiness_status: str
    ci_passed: bool
    no_blocking_issues: bool
    warnings_within_threshold: bool
    baseline_aligned: bool
    human_review_completed: bool
    blocking_reasons: List[str]
    recommendations: List[str]
    status_message: str
    human_review_required: bool
    release_authorized: bool
    deterministic_evaluation_hash: str


class CreatePackageRequest(BaseModel):
    """Request to create a governance release package."""
    package_name: str
    freeze_id: str
    evaluation_id: Optional[str] = None


class PackageResponse(BaseModel):
    """Response containing a release package."""
    package_id: str
    package_name: str
    freeze_id: str
    evaluation_id: Optional[str]
    readiness_status: str
    baseline_id: Optional[str]
    ci_status: Optional[str]
    blocking_issue_count: int
    warning_count: int
    blocking_reasons: List[str]
    recommendations: List[str]
    human_review_required: bool
    release_authorized: bool
    deterministic_package_hash: str


class UpdateStatusRequest(BaseModel):
    """Request to update freeze status."""
    new_status: str
    reviewer_note: Optional[str] = None


class GovernanceStatusResponse(BaseModel):
    """Aggregated governance status response."""
    total_freezes: int
    pending_freezes: int
    reviewed_freezes: int
    approved_freezes: int
    rejected_freezes: int
    total_evaluations: int
    ready_evaluations: int
    not_ready_evaluations: int
    blocked_evaluations: int
    total_packages: int
    latest_freeze_id: Optional[str]
    latest_freeze_status: Optional[str]
    latest_evaluation_id: Optional[str]
    latest_evaluation_status: Optional[str]
    latest_package_id: Optional[str]


# ─────────────────────────────────────────────────────────────────────────────
# Freeze endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/freezes", response_model=FreezeResponse)
def create_freeze(request: CreateFreezeRequest) -> FreezeResponse:
    """
    Create a governance baseline freeze.

    Captures point-in-time governance state for human review.
    """
    # Get baseline and CI summary if specified
    baseline = None
    if request.baseline_id:
        baseline = get_federation_drift_baseline(request.baseline_id)
        if not baseline:
            raise HTTPException(
                status_code=404,
                detail=f"Baseline {request.baseline_id} not found"
            )

    # Get latest CI summary for freeze state
    ci_summary = None
    if request.ci_summary_id:
        from app.cam.federation_ci_registry import get_federation_ci_summary
        ci_summary = get_federation_ci_summary(request.ci_summary_id)
        if not ci_summary:
            raise HTTPException(
                status_code=404,
                detail=f"CI summary {request.ci_summary_id} not found"
            )
    else:
        ci_summary = get_latest_federation_ci_summary()

    freeze = create_governance_baseline_freeze(
        freeze_name=request.freeze_name,
        baseline_id=request.baseline_id,
        ci_summary_id=ci_summary.summary_id if ci_summary else None,
        ci_status_at_freeze=ci_summary.status if ci_summary else None,
        federation_ref_count_at_freeze=ci_summary.total_federation_refs if ci_summary else 0,
        continuity_record_count_at_freeze=ci_summary.total_continuity_records if ci_summary else 0,
        package_count_at_freeze=ci_summary.total_federated_packages if ci_summary else 0,
        blocking_issue_count=ci_summary.blocking_issue_count if ci_summary else 0,
        warning_count=ci_summary.warning_count if ci_summary else 0,
    )

    success, error = register_governance_freeze(freeze)
    if not success:
        raise HTTPException(status_code=400, detail=error)

    return FreezeResponse(
        freeze_id=freeze.freeze_id,
        freeze_name=freeze.freeze_name,
        baseline_id=freeze.baseline_id,
        ci_summary_id=freeze.ci_summary_id,
        ci_status_at_freeze=freeze.ci_status_at_freeze,
        federation_ref_count_at_freeze=freeze.federation_ref_count_at_freeze,
        continuity_record_count_at_freeze=freeze.continuity_record_count_at_freeze,
        package_count_at_freeze=freeze.package_count_at_freeze,
        blocking_issue_count=freeze.blocking_issue_count,
        warning_count=freeze.warning_count,
        status=freeze.status,
        human_review_required=freeze.human_review_required,
        release_authorized=freeze.release_authorized,
        deterministic_freeze_hash=freeze.deterministic_freeze_hash,
    )


@router.get("/freezes", response_model=List[Dict[str, Any]])
def list_freezes() -> List[Dict[str, Any]]:
    """List all governance freezes."""
    freezes = list_governance_freezes()
    return [get_freeze_summary(f) for f in freezes]


@router.get("/freezes/latest", response_model=FreezeResponse)
def get_latest_freeze() -> FreezeResponse:
    """Get the most recent governance freeze."""
    freeze = get_latest_governance_freeze()
    if not freeze:
        raise HTTPException(status_code=404, detail="No freezes registered")

    return FreezeResponse(
        freeze_id=freeze.freeze_id,
        freeze_name=freeze.freeze_name,
        baseline_id=freeze.baseline_id,
        ci_summary_id=freeze.ci_summary_id,
        ci_status_at_freeze=freeze.ci_status_at_freeze,
        federation_ref_count_at_freeze=freeze.federation_ref_count_at_freeze,
        continuity_record_count_at_freeze=freeze.continuity_record_count_at_freeze,
        package_count_at_freeze=freeze.package_count_at_freeze,
        blocking_issue_count=freeze.blocking_issue_count,
        warning_count=freeze.warning_count,
        status=freeze.status,
        human_review_required=freeze.human_review_required,
        release_authorized=freeze.release_authorized,
        deterministic_freeze_hash=freeze.deterministic_freeze_hash,
    )


@router.get("/freezes/{freeze_id}", response_model=FreezeResponse)
def get_freeze(freeze_id: str) -> FreezeResponse:
    """Get a governance freeze by ID."""
    freeze = get_governance_freeze(freeze_id)
    if not freeze:
        raise HTTPException(status_code=404, detail=f"Freeze {freeze_id} not found")

    return FreezeResponse(
        freeze_id=freeze.freeze_id,
        freeze_name=freeze.freeze_name,
        baseline_id=freeze.baseline_id,
        ci_summary_id=freeze.ci_summary_id,
        ci_status_at_freeze=freeze.ci_status_at_freeze,
        federation_ref_count_at_freeze=freeze.federation_ref_count_at_freeze,
        continuity_record_count_at_freeze=freeze.continuity_record_count_at_freeze,
        package_count_at_freeze=freeze.package_count_at_freeze,
        blocking_issue_count=freeze.blocking_issue_count,
        warning_count=freeze.warning_count,
        status=freeze.status,
        human_review_required=freeze.human_review_required,
        release_authorized=freeze.release_authorized,
        deterministic_freeze_hash=freeze.deterministic_freeze_hash,
    )


@router.patch("/freezes/{freeze_id}/status", response_model=FreezeResponse)
def update_status(freeze_id: str, request: UpdateStatusRequest) -> FreezeResponse:
    """
    Update a freeze's status.

    Valid transitions:
      - pending -> reviewed
      - reviewed -> approved
      - reviewed -> rejected
    """
    success, error = update_freeze_status(
        freeze_id=freeze_id,
        new_status=request.new_status,
        reviewer_note=request.reviewer_note,
    )
    if not success:
        raise HTTPException(status_code=400, detail=error)

    freeze = get_governance_freeze(freeze_id)
    return FreezeResponse(
        freeze_id=freeze.freeze_id,
        freeze_name=freeze.freeze_name,
        baseline_id=freeze.baseline_id,
        ci_summary_id=freeze.ci_summary_id,
        ci_status_at_freeze=freeze.ci_status_at_freeze,
        federation_ref_count_at_freeze=freeze.federation_ref_count_at_freeze,
        continuity_record_count_at_freeze=freeze.continuity_record_count_at_freeze,
        package_count_at_freeze=freeze.package_count_at_freeze,
        blocking_issue_count=freeze.blocking_issue_count,
        warning_count=freeze.warning_count,
        status=freeze.status,
        human_review_required=freeze.human_review_required,
        release_authorized=freeze.release_authorized,
        deterministic_freeze_hash=freeze.deterministic_freeze_hash,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Evaluation endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/evaluate", response_model=EvaluationResponse)
def evaluate_readiness(request: EvaluateRequest) -> EvaluationResponse:
    """
    Evaluate release readiness for a freeze.

    Assesses CI status, blocking issues, warnings, and baseline alignment.
    """
    freeze = get_governance_freeze(request.freeze_id)
    if not freeze:
        raise HTTPException(
            status_code=404,
            detail=f"Freeze {request.freeze_id} not found"
        )

    evaluation = evaluate_freeze_readiness(
        freeze=freeze,
        warning_threshold=request.warning_threshold,
    )

    success, error = register_release_evaluation(evaluation)
    if not success:
        raise HTTPException(status_code=400, detail=error)

    return EvaluationResponse(
        evaluation_id=evaluation.evaluation_id,
        freeze_id=evaluation.freeze_id,
        readiness_status=evaluation.readiness_status,
        ci_passed=evaluation.ci_passed,
        no_blocking_issues=evaluation.no_blocking_issues,
        warnings_within_threshold=evaluation.warnings_within_threshold,
        baseline_aligned=evaluation.baseline_aligned,
        human_review_completed=evaluation.human_review_completed,
        blocking_reasons=evaluation.blocking_reasons,
        recommendations=evaluation.recommendations,
        status_message=get_readiness_status_message(evaluation),
        human_review_required=evaluation.human_review_required,
        release_authorized=evaluation.release_authorized,
        deterministic_evaluation_hash=evaluation.deterministic_evaluation_hash,
    )


@router.get("/evaluations/latest", response_model=EvaluationResponse)
def get_latest_evaluation() -> EvaluationResponse:
    """Get the most recent release evaluation."""
    evaluation = get_latest_release_evaluation()
    if not evaluation:
        raise HTTPException(status_code=404, detail="No evaluations registered")

    return EvaluationResponse(
        evaluation_id=evaluation.evaluation_id,
        freeze_id=evaluation.freeze_id,
        readiness_status=evaluation.readiness_status,
        ci_passed=evaluation.ci_passed,
        no_blocking_issues=evaluation.no_blocking_issues,
        warnings_within_threshold=evaluation.warnings_within_threshold,
        baseline_aligned=evaluation.baseline_aligned,
        human_review_completed=evaluation.human_review_completed,
        blocking_reasons=evaluation.blocking_reasons,
        recommendations=evaluation.recommendations,
        status_message=get_readiness_status_message(evaluation),
        human_review_required=evaluation.human_review_required,
        release_authorized=evaluation.release_authorized,
        deterministic_evaluation_hash=evaluation.deterministic_evaluation_hash,
    )


@router.get("/evaluations", response_model=List[Dict[str, Any]])
def list_evaluations() -> List[Dict[str, Any]]:
    """List all release evaluations."""
    evaluations = list_release_evaluations()
    return [get_evaluation_summary_dict(e) for e in evaluations]


@router.get("/evaluations/{evaluation_id}", response_model=EvaluationResponse)
def get_evaluation(evaluation_id: str) -> EvaluationResponse:
    """Get a specific evaluation by ID."""
    evaluation = get_release_evaluation(evaluation_id)
    if not evaluation:
        raise HTTPException(status_code=404, detail=f"Evaluation {evaluation_id} not found")

    return EvaluationResponse(
        evaluation_id=evaluation.evaluation_id,
        freeze_id=evaluation.freeze_id,
        readiness_status=evaluation.readiness_status,
        ci_passed=evaluation.ci_passed,
        no_blocking_issues=evaluation.no_blocking_issues,
        warnings_within_threshold=evaluation.warnings_within_threshold,
        baseline_aligned=evaluation.baseline_aligned,
        human_review_completed=evaluation.human_review_completed,
        blocking_reasons=evaluation.blocking_reasons,
        recommendations=evaluation.recommendations,
        status_message=get_readiness_status_message(evaluation),
        human_review_required=evaluation.human_review_required,
        release_authorized=evaluation.release_authorized,
        deterministic_evaluation_hash=evaluation.deterministic_evaluation_hash,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Package endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/packages", response_model=PackageResponse)
def create_package(request: CreatePackageRequest) -> PackageResponse:
    """
    Create a governance release package.

    Bundles freeze and evaluation for human review.
    """
    freeze = get_governance_freeze(request.freeze_id)
    if not freeze:
        raise HTTPException(
            status_code=404,
            detail=f"Freeze {request.freeze_id} not found"
        )

    evaluation = None
    if request.evaluation_id:
        evaluation = get_release_evaluation(request.evaluation_id)
        if not evaluation:
            raise HTTPException(
                status_code=404,
                detail=f"Evaluation {request.evaluation_id} not found"
            )

    package = create_governance_release_package(
        package_name=request.package_name,
        freeze=freeze,
        evaluation=evaluation,
    )

    success, error = register_governance_package(package)
    if not success:
        raise HTTPException(status_code=400, detail=error)

    return PackageResponse(
        package_id=package.package_id,
        package_name=package.package_name,
        freeze_id=package.freeze_id,
        evaluation_id=package.evaluation_id,
        readiness_status=package.readiness_status,
        baseline_id=package.baseline_id,
        ci_status=package.ci_status,
        blocking_issue_count=package.blocking_issue_count,
        warning_count=package.warning_count,
        blocking_reasons=package.blocking_reasons,
        recommendations=package.recommendations,
        human_review_required=package.human_review_required,
        release_authorized=package.release_authorized,
        deterministic_package_hash=package.deterministic_package_hash,
    )


@router.get("/packages/latest", response_model=PackageResponse)
def get_latest_package() -> PackageResponse:
    """Get the most recent governance package."""
    package = get_latest_governance_package()
    if not package:
        raise HTTPException(status_code=404, detail="No packages registered")

    return PackageResponse(
        package_id=package.package_id,
        package_name=package.package_name,
        freeze_id=package.freeze_id,
        evaluation_id=package.evaluation_id,
        readiness_status=package.readiness_status,
        baseline_id=package.baseline_id,
        ci_status=package.ci_status,
        blocking_issue_count=package.blocking_issue_count,
        warning_count=package.warning_count,
        blocking_reasons=package.blocking_reasons,
        recommendations=package.recommendations,
        human_review_required=package.human_review_required,
        release_authorized=package.release_authorized,
        deterministic_package_hash=package.deterministic_package_hash,
    )


@router.get("/packages", response_model=List[Dict[str, Any]])
def list_packages() -> List[Dict[str, Any]]:
    """List all governance packages."""
    packages = list_governance_packages()
    return [get_package_summary(p) for p in packages]


@router.get("/packages/{package_id}", response_model=Dict[str, Any])
def get_package(package_id: str) -> Dict[str, Any]:
    """Get a specific package by ID with full review context."""
    package = get_governance_package(package_id)
    if not package:
        raise HTTPException(status_code=404, detail=f"Package {package_id} not found")

    return get_package_review_context(package)


# ─────────────────────────────────────────────────────────────────────────────
# Status endpoint
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/status", response_model=GovernanceStatusResponse)
def get_status() -> GovernanceStatusResponse:
    """Get aggregated governance status summary."""
    status = get_governance_status_summary()
    return GovernanceStatusResponse(**status)
