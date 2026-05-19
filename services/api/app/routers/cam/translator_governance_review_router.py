"""
Translator Governance Review Router

CAM Dev Order 7J: REST endpoints for governance review readiness matrix.

Endpoints:
  POST /api/cam/translators/governance-review/evaluate   - Evaluate review readiness
  GET  /api/cam/translators/governance-review            - List review matrices
  GET  /api/cam/translators/governance-review/{id}       - Get review matrix
  GET  /api/cam/translators/governance-review/by-translator/{id} - By translator

7J invariants:
  - All responses have execution_authorized=false
  - All responses have machine_output_allowed=false
  - No mutation endpoints
  - No approval endpoints

Guardrail:
  7J determines review readiness only. It does not create approval
  authority, execution authority, or mutation authority.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.cam.translator_governance_review_matrix import (
    TranslatorGovernanceReviewMatrix,
    GovernanceReviewMatrixSummary,
    CANONICAL_ESCALATION_LAYERS,
    SCORING_WEIGHTS,
    GATE_THRESHOLDS,
    evaluate_governance_review_readiness,
    evaluate_governance_review_readiness_by_dossier_id,
    get_review_matrix,
    list_review_matrices,
    list_review_matrices_for_translator,
    to_summary,
    ReviewMatrixEvaluationError,
)


router = APIRouter(tags=["Translator Governance Review"])


# -----------------------------------------------------------------------------
# Request Models
# -----------------------------------------------------------------------------

class ReviewEvaluateRequest(BaseModel):
    """Request model for evaluating governance review readiness."""

    dossier_id: str = Field(..., description="Dossier ID to evaluate")
    persist_to_rmos: bool = Field(
        default=False,
        description="Whether to persist to RMOS"
    )


# -----------------------------------------------------------------------------
# Response Models
# -----------------------------------------------------------------------------

class ReviewPolicyInfo(BaseModel):
    """Information about review matrix policy configuration."""

    canonical_escalation_layers: List[str] = Field(
        default_factory=lambda: CANONICAL_ESCALATION_LAYERS.copy()
    )
    scoring_weights: Dict[str, int] = Field(
        default_factory=lambda: SCORING_WEIGHTS.copy()
    )
    gate_thresholds: Dict[str, int] = Field(
        default_factory=lambda: GATE_THRESHOLDS.copy()
    )
    eligibility_rules: List[str] = Field(
        default_factory=lambda: [
            "review_gate != red",
            "blocker_count == 0",
            "execution_authorized == false",
            "machine_output_allowed == false",
        ]
    )

    # 7J invariants
    execution_authorized: bool = False
    machine_output_allowed: bool = False


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------

@router.post(
    "/translators/governance-review/evaluate",
    response_model=TranslatorGovernanceReviewMatrix,
    summary="Evaluate governance review readiness",
    description="Evaluate governance review readiness from a dossier.",
)
async def evaluate_review_readiness(
    request: ReviewEvaluateRequest,
) -> TranslatorGovernanceReviewMatrix:
    """
    Evaluate governance review readiness.

    Takes a dossier ID and produces a deterministic review matrix.

    Guardrail:
      7J determines review readiness only. It does not create approval
      authority, execution authority, or mutation authority.
    """
    try:
        matrix = evaluate_governance_review_readiness_by_dossier_id(
            dossier_id=request.dossier_id,
            persist_to_rmos=request.persist_to_rmos,
        )
        return matrix
    except ReviewMatrixEvaluationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/translators/governance-review",
    response_model=List[GovernanceReviewMatrixSummary],
    summary="List governance review matrices",
    description="List all governance review matrices.",
)
async def list_reviews(
    translator_id: Optional[str] = None,
) -> List[GovernanceReviewMatrixSummary]:
    """List governance review matrices, optionally filtered by translator."""
    if translator_id:
        matrices = list_review_matrices_for_translator(translator_id)
    else:
        matrices = list_review_matrices()
    return [to_summary(m) for m in matrices]


@router.get(
    "/translators/governance-review/policy",
    response_model=ReviewPolicyInfo,
    summary="Get review policy",
    description="Get the current review matrix policy configuration.",
)
async def get_review_policy() -> ReviewPolicyInfo:
    """Get review policy information."""
    return ReviewPolicyInfo()


@router.get(
    "/translators/governance-review/by-translator/{translator_id}",
    response_model=List[TranslatorGovernanceReviewMatrix],
    summary="Get review matrices by translator",
    description="Get all governance review matrices for a specific translator.",
)
async def get_reviews_by_translator(
    translator_id: str,
) -> List[TranslatorGovernanceReviewMatrix]:
    """Get all governance review matrices for a translator."""
    return list_review_matrices_for_translator(translator_id)


@router.get(
    "/translators/governance-review/{review_matrix_id}",
    response_model=TranslatorGovernanceReviewMatrix,
    summary="Get governance review matrix",
    description="Get a specific governance review matrix by ID.",
)
async def get_review(review_matrix_id: str) -> TranslatorGovernanceReviewMatrix:
    """Get governance review matrix by ID."""
    matrix = get_review_matrix(review_matrix_id)

    if matrix is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Governance review matrix not found: {review_matrix_id}",
        )

    return matrix
