"""
Federation CI Router

CAM Dev Order 7Y: Federation CI drift baseline endpoints.

Provides:
  - Baseline CRUD
  - CI evaluation endpoint
  - Latest summary retrieval
  - CI status endpoint

7Y invariants:
  - All endpoints are observational only
  - No execution authorization
  - No machine output
  - Baselines are immutable

Core principle:
  Router exposes federation drift baselines and CI enforcement.
  It does not repair drift or mutate federation state.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.cam.federation_drift_baseline import (
    FederationDriftBaseline,
    create_federation_drift_baseline,
    get_baseline_summary,
)
from app.cam.federation_ci_enforcement import (
    FederationCIEnforcementSummary,
    build_federation_ci_summary,
    evaluate_against_baseline,
    get_enforcement_summary_dict,
    get_summary_status_message,
)
from app.cam.federation_ci_registry import (
    register_federation_drift_baseline,
    get_federation_drift_baseline,
    list_federation_drift_baselines,
    register_federation_ci_summary,
    get_federation_ci_summary,
    get_latest_federation_ci_summary,
    list_federation_ci_summaries,
    get_ci_status_summary,
)


router = APIRouter(prefix="/api/cam/federation-ci", tags=["CAM", "Federation", "CI"])


# ─────────────────────────────────────────────────────────────────────────────
# Request/Response models
# ─────────────────────────────────────────────────────────────────────────────

class CreateBaselineRequest(BaseModel):
    """Request to create a federation drift baseline."""
    baseline_name: str
    expected_federation_ref_count: Optional[int] = None
    expected_continuity_record_count: Optional[int] = None
    expected_package_count: Optional[int] = None
    allowed_warning_count: int = Field(default=0)
    allowed_fragmented_federation_count: int = Field(default=0)


class BaselineResponse(BaseModel):
    """Response containing a baseline."""
    baseline_id: str
    baseline_name: str
    expected_federation_ref_count: Optional[int]
    expected_continuity_record_count: Optional[int]
    expected_package_count: Optional[int]
    allowed_warning_count: int
    allowed_fragmented_federation_count: int
    authority_override_allowed: bool
    ontology_mutation_allowed: bool
    deterministic_baseline_hash: str


class EvaluateRequest(BaseModel):
    """Request to evaluate federation against baseline."""
    baseline_id: Optional[str] = None


class CISummaryResponse(BaseModel):
    """Response containing a CI enforcement summary."""
    summary_id: str
    baseline_id: Optional[str]
    total_federation_refs: int
    total_continuity_records: int
    total_federated_packages: int
    authority_override_count: int
    ontology_mutation_attempt_count: int
    fragmented_federation_count: int
    invalid_continuity_count: int
    warning_count: int
    blocking_issue_count: int
    baseline_mismatch_detected: bool
    status: str
    blocking_issues: List[str]
    warnings: List[str]
    status_message: str
    deterministic_summary_hash: str


class CIStatusResponse(BaseModel):
    """Aggregated CI status response."""
    total_baselines: int
    total_summaries: int
    passing_count: int
    warning_count: int
    failing_count: int
    latest_status: Optional[str]
    latest_summary_id: Optional[str]


# ─────────────────────────────────────────────────────────────────────────────
# Baseline endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/baselines", response_model=BaselineResponse)
def create_baseline(request: CreateBaselineRequest) -> BaselineResponse:
    """
    Create a federation drift baseline.

    Baselines are immutable once registered.
    """
    baseline = create_federation_drift_baseline(
        baseline_name=request.baseline_name,
        expected_federation_ref_count=request.expected_federation_ref_count,
        expected_continuity_record_count=request.expected_continuity_record_count,
        expected_package_count=request.expected_package_count,
        allowed_warning_count=request.allowed_warning_count,
        allowed_fragmented_federation_count=request.allowed_fragmented_federation_count,
    )

    success, error = register_federation_drift_baseline(baseline)
    if not success:
        raise HTTPException(status_code=400, detail=error)

    return BaselineResponse(
        baseline_id=baseline.baseline_id,
        baseline_name=baseline.baseline_name,
        expected_federation_ref_count=baseline.expected_federation_ref_count,
        expected_continuity_record_count=baseline.expected_continuity_record_count,
        expected_package_count=baseline.expected_package_count,
        allowed_warning_count=baseline.allowed_warning_count,
        allowed_fragmented_federation_count=baseline.allowed_fragmented_federation_count,
        authority_override_allowed=baseline.authority_override_allowed,
        ontology_mutation_allowed=baseline.ontology_mutation_allowed,
        deterministic_baseline_hash=baseline.deterministic_baseline_hash,
    )


@router.get("/baselines", response_model=List[Dict[str, Any]])
def list_baselines() -> List[Dict[str, Any]]:
    """List all federation drift baselines."""
    baselines = list_federation_drift_baselines()
    return [get_baseline_summary(b) for b in baselines]


@router.get("/baselines/{baseline_id}", response_model=BaselineResponse)
def get_baseline(baseline_id: str) -> BaselineResponse:
    """Get a federation drift baseline by ID."""
    baseline = get_federation_drift_baseline(baseline_id)
    if not baseline:
        raise HTTPException(status_code=404, detail=f"Baseline {baseline_id} not found")

    return BaselineResponse(
        baseline_id=baseline.baseline_id,
        baseline_name=baseline.baseline_name,
        expected_federation_ref_count=baseline.expected_federation_ref_count,
        expected_continuity_record_count=baseline.expected_continuity_record_count,
        expected_package_count=baseline.expected_package_count,
        allowed_warning_count=baseline.allowed_warning_count,
        allowed_fragmented_federation_count=baseline.allowed_fragmented_federation_count,
        authority_override_allowed=baseline.authority_override_allowed,
        ontology_mutation_allowed=baseline.ontology_mutation_allowed,
        deterministic_baseline_hash=baseline.deterministic_baseline_hash,
    )


# ─────────────────────────────────────────────────────────────────────────────
# CI evaluation endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/evaluate", response_model=CISummaryResponse)
def evaluate_federation(request: EvaluateRequest) -> CISummaryResponse:
    """
    Evaluate current federation state.

    Optionally compare against a baseline.
    Registers the summary in history.
    """
    baseline = None
    if request.baseline_id:
        baseline = get_federation_drift_baseline(request.baseline_id)
        if not baseline:
            raise HTTPException(
                status_code=404,
                detail=f"Baseline {request.baseline_id} not found"
            )

    summary = build_federation_ci_summary(baseline=baseline)

    # Register in history
    success, error = register_federation_ci_summary(summary)
    if not success:
        raise HTTPException(status_code=400, detail=error)

    return CISummaryResponse(
        summary_id=summary.summary_id,
        baseline_id=summary.baseline_id,
        total_federation_refs=summary.total_federation_refs,
        total_continuity_records=summary.total_continuity_records,
        total_federated_packages=summary.total_federated_packages,
        authority_override_count=summary.authority_override_count,
        ontology_mutation_attempt_count=summary.ontology_mutation_attempt_count,
        fragmented_federation_count=summary.fragmented_federation_count,
        invalid_continuity_count=summary.invalid_continuity_count,
        warning_count=summary.warning_count,
        blocking_issue_count=summary.blocking_issue_count,
        baseline_mismatch_detected=summary.baseline_mismatch_detected,
        status=summary.status,
        blocking_issues=summary.blocking_issues,
        warnings=summary.warnings,
        status_message=get_summary_status_message(summary),
        deterministic_summary_hash=summary.deterministic_summary_hash,
    )


@router.get("/summary/latest", response_model=CISummaryResponse)
def get_latest_summary() -> CISummaryResponse:
    """Get the most recent CI enforcement summary."""
    summary = get_latest_federation_ci_summary()
    if not summary:
        raise HTTPException(status_code=404, detail="No CI summaries registered")

    return CISummaryResponse(
        summary_id=summary.summary_id,
        baseline_id=summary.baseline_id,
        total_federation_refs=summary.total_federation_refs,
        total_continuity_records=summary.total_continuity_records,
        total_federated_packages=summary.total_federated_packages,
        authority_override_count=summary.authority_override_count,
        ontology_mutation_attempt_count=summary.ontology_mutation_attempt_count,
        fragmented_federation_count=summary.fragmented_federation_count,
        invalid_continuity_count=summary.invalid_continuity_count,
        warning_count=summary.warning_count,
        blocking_issue_count=summary.blocking_issue_count,
        baseline_mismatch_detected=summary.baseline_mismatch_detected,
        status=summary.status,
        blocking_issues=summary.blocking_issues,
        warnings=summary.warnings,
        status_message=get_summary_status_message(summary),
        deterministic_summary_hash=summary.deterministic_summary_hash,
    )


@router.get("/status", response_model=CIStatusResponse)
def get_ci_status() -> CIStatusResponse:
    """Get aggregated CI status summary."""
    status = get_ci_status_summary()
    return CIStatusResponse(**status)


@router.get("/summaries", response_model=List[Dict[str, Any]])
def list_summaries() -> List[Dict[str, Any]]:
    """List all CI summaries (brief format)."""
    summaries = list_federation_ci_summaries()
    return [
        {
            "summary_id": s.summary_id,
            "baseline_id": s.baseline_id,
            "status": s.status,
            "total_federation_refs": s.total_federation_refs,
            "baseline_mismatch_detected": s.baseline_mismatch_detected,
            "created_at": s.created_at.isoformat(),
        }
        for s in summaries
    ]


@router.get("/summaries/{summary_id}", response_model=CISummaryResponse)
def get_summary(summary_id: str) -> CISummaryResponse:
    """Get a specific CI summary by ID."""
    summary = get_federation_ci_summary(summary_id)
    if not summary:
        raise HTTPException(status_code=404, detail=f"Summary {summary_id} not found")

    return CISummaryResponse(
        summary_id=summary.summary_id,
        baseline_id=summary.baseline_id,
        total_federation_refs=summary.total_federation_refs,
        total_continuity_records=summary.total_continuity_records,
        total_federated_packages=summary.total_federated_packages,
        authority_override_count=summary.authority_override_count,
        ontology_mutation_attempt_count=summary.ontology_mutation_attempt_count,
        fragmented_federation_count=summary.fragmented_federation_count,
        invalid_continuity_count=summary.invalid_continuity_count,
        warning_count=summary.warning_count,
        blocking_issue_count=summary.blocking_issue_count,
        baseline_mismatch_detected=summary.baseline_mismatch_detected,
        status=summary.status,
        blocking_issues=summary.blocking_issues,
        warnings=summary.warnings,
        status_message=get_summary_status_message(summary),
        deterministic_summary_hash=summary.deterministic_summary_hash,
    )
