"""
Review UX CI Router

CAM Dev Order 8D: REST endpoints for review UX CI enforcement.

Provides:
  - POST /api/cam/review-ux-ci/baselines — register baseline
  - GET /api/cam/review-ux-ci/baselines — list baselines
  - GET /api/cam/review-ux-ci/baselines/{baseline_id} — get baseline
  - GET /api/cam/review-ux-ci/baselines/latest — get latest baseline
  - POST /api/cam/review-ux-ci/check — run CI check
  - GET /api/cam/review-ux-ci/summaries — list CI summaries
  - GET /api/cam/review-ux-ci/summaries/{summary_id} — get CI summary
  - GET /api/cam/review-ux-ci/summaries/latest — get latest summary
  - GET /api/cam/review-ux-ci/report — build CI report
  - GET /api/cam/review-ux-ci/status — get status summary

8D invariants:
  - execution_authorized: always False
  - machine_output_allowed: always False
  - auto_approval_allowed: always False

Core principle:
  Endpoints expose CI enforcement state for human review.
  They do not authorize execution, machine output, or auto-approval.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ...cam.review_ux_baseline import (
    ReviewUXBaseline,
    create_review_ux_baseline,
    get_baseline_summary,
)
from ...cam.review_ux_ci_enforcement import (
    get_ci_enforcement_summary,
)
from ...cam.review_ux_ci_registry import (
    register_review_ux_baseline,
    get_review_ux_baseline,
    get_latest_review_ux_baseline,
    list_review_ux_baselines,
    get_review_ux_baseline_count,
    register_review_ux_ci_summary,
    get_review_ux_ci_summary,
    get_latest_review_ux_ci_summary,
    list_review_ux_ci_summaries,
    get_review_ux_ci_summary_count,
    evaluate_current_review_ux_state,
    run_review_ux_ci_check,
    build_review_ux_ci_report,
    get_review_ux_ci_status_summary,
)


router = APIRouter(prefix="/api/cam/review-ux-ci", tags=["cam", "review-ux-ci"])


# ─────────────────────────────────────────────────────────────────────────────
# Request/Response models
# ─────────────────────────────────────────────────────────────────────────────

class CreateBaselineRequest(BaseModel):
    """Request to create a review UX baseline."""
    baseline_name: str = Field(..., min_length=1, max_length=200)
    required_panel_count: Optional[int] = Field(default=None, ge=0)
    allowed_missing_provenance_count: int = Field(default=0, ge=0)
    allowed_federation_visibility_gap_count: int = Field(default=0, ge=0)
    allowed_fragmented_replay_count: int = Field(default=0, ge=0)
    allowed_review_overload_count: int = Field(default=0, ge=0)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RunCICheckRequest(BaseModel):
    """Request to run CI check."""
    baseline_id: Optional[str] = Field(
        default=None,
        description="Baseline ID to check against (optional, uses latest if not provided)"
    )


class BaselineResponse(BaseModel):
    """Response containing baseline details."""
    success: bool
    baseline_id: str
    baseline_name: str
    message: str
    summary: Dict[str, Any]


class CISummaryResponse(BaseModel):
    """Response containing CI summary details."""
    success: bool
    summary_id: str
    status: str
    message: str
    summary: Dict[str, Any]


class ListBaselinesResponse(BaseModel):
    """Response containing list of baselines."""
    total: int
    baselines: List[Dict[str, Any]]


class ListSummariesResponse(BaseModel):
    """Response containing list of CI summaries."""
    total: int
    summaries: List[Dict[str, Any]]


class CIReportResponse(BaseModel):
    """Response containing CI report."""
    report: Dict[str, Any]


class StatusSummaryResponse(BaseModel):
    """Response containing status summary."""
    status: Dict[str, Any]


# ─────────────────────────────────────────────────────────────────────────────
# Baseline endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/baselines", response_model=BaselineResponse)
async def create_baseline(request: CreateBaselineRequest) -> BaselineResponse:
    """
    Create and register a review UX baseline.

    Baselines define thresholds for CI enforcement.
    """
    baseline = create_review_ux_baseline(
        baseline_name=request.baseline_name,
        required_panel_count=request.required_panel_count,
        allowed_missing_provenance_count=request.allowed_missing_provenance_count,
        allowed_federation_visibility_gap_count=request.allowed_federation_visibility_gap_count,
        allowed_fragmented_replay_count=request.allowed_fragmented_replay_count,
        allowed_review_overload_count=request.allowed_review_overload_count,
        metadata=request.metadata,
    )

    success, error = register_review_ux_baseline(baseline)
    if not success:
        raise HTTPException(status_code=400, detail=error)

    return BaselineResponse(
        success=True,
        baseline_id=baseline.baseline_id,
        baseline_name=baseline.baseline_name,
        message="Baseline registered successfully",
        summary=get_baseline_summary(baseline),
    )


@router.get("/baselines", response_model=ListBaselinesResponse)
async def list_baselines() -> ListBaselinesResponse:
    """List all registered baselines."""
    baselines = list_review_ux_baselines()
    return ListBaselinesResponse(
        total=len(baselines),
        baselines=[get_baseline_summary(b) for b in baselines],
    )


@router.get("/baselines/latest", response_model=BaselineResponse)
async def get_latest_baseline() -> BaselineResponse:
    """Get the most recently registered baseline."""
    baseline = get_latest_review_ux_baseline()
    if not baseline:
        raise HTTPException(status_code=404, detail="No baselines registered")

    return BaselineResponse(
        success=True,
        baseline_id=baseline.baseline_id,
        baseline_name=baseline.baseline_name,
        message="Latest baseline retrieved",
        summary=get_baseline_summary(baseline),
    )


@router.get("/baselines/{baseline_id}", response_model=BaselineResponse)
async def get_baseline(baseline_id: str) -> BaselineResponse:
    """Get a baseline by ID."""
    baseline = get_review_ux_baseline(baseline_id)
    if not baseline:
        raise HTTPException(status_code=404, detail=f"Baseline {baseline_id} not found")

    return BaselineResponse(
        success=True,
        baseline_id=baseline.baseline_id,
        baseline_name=baseline.baseline_name,
        message="Baseline retrieved",
        summary=get_baseline_summary(baseline),
    )


# ─────────────────────────────────────────────────────────────────────────────
# CI check endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/check", response_model=CISummaryResponse)
async def run_ci_check(request: RunCICheckRequest) -> CISummaryResponse:
    """
    Run CI check against current review UX state.

    Optionally specify a baseline to check against.
    If no baseline specified, uses the latest registered baseline.
    If no baseline exists, evaluates without threshold comparison.
    """
    summary, success, error = run_review_ux_ci_check(request.baseline_id)

    if not success:
        raise HTTPException(status_code=400, detail=error)

    return CISummaryResponse(
        success=True,
        summary_id=summary.summary_id,
        status=summary.status,
        message=f"CI check completed with status: {summary.status}",
        summary=get_ci_enforcement_summary(summary),
    )


@router.get("/summaries", response_model=ListSummariesResponse)
async def list_summaries() -> ListSummariesResponse:
    """List all CI enforcement summaries."""
    summaries = list_review_ux_ci_summaries()
    return ListSummariesResponse(
        total=len(summaries),
        summaries=[get_ci_enforcement_summary(s) for s in summaries],
    )


@router.get("/summaries/latest", response_model=CISummaryResponse)
async def get_latest_summary() -> CISummaryResponse:
    """Get the most recent CI enforcement summary."""
    summary = get_latest_review_ux_ci_summary()
    if not summary:
        raise HTTPException(status_code=404, detail="No CI summaries registered")

    return CISummaryResponse(
        success=True,
        summary_id=summary.summary_id,
        status=summary.status,
        message="Latest CI summary retrieved",
        summary=get_ci_enforcement_summary(summary),
    )


@router.get("/summaries/{summary_id}", response_model=CISummaryResponse)
async def get_summary(summary_id: str) -> CISummaryResponse:
    """Get a CI summary by ID."""
    summary = get_review_ux_ci_summary(summary_id)
    if not summary:
        raise HTTPException(status_code=404, detail=f"Summary {summary_id} not found")

    return CISummaryResponse(
        success=True,
        summary_id=summary.summary_id,
        status=summary.status,
        message="CI summary retrieved",
        summary=get_ci_enforcement_summary(summary),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Report endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/report", response_model=CIReportResponse)
async def get_ci_report() -> CIReportResponse:
    """Build and return the full CI report."""
    report = build_review_ux_ci_report()
    return CIReportResponse(report=report)


@router.get("/status", response_model=StatusSummaryResponse)
async def get_status() -> StatusSummaryResponse:
    """Get aggregated status summary."""
    status = get_review_ux_ci_status_summary()
    return StatusSummaryResponse(status=status)
