"""
Translator Readiness Matrix Router

CAM Dev Order 7G: REST endpoints for translator readiness evaluation.

Endpoints:
  GET  /api/cam/translators/readiness              - List all evaluations
  GET  /api/cam/translators/readiness/{translator_id} - Get evaluation for translator
  POST /api/cam/translators/readiness/evaluate     - Evaluate translator readiness
  GET  /api/cam/translators/readiness/requirements/{level} - Get promotion requirements
  GET  /api/cam/translators/readiness/levels       - List readiness levels

7G invariants:
  - All responses have execution_ready=false
  - All responses have promotion_authorized=false
  - No DXF, G-code, or machine output
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.cam.translator_readiness_matrix import (
    ReadinessLevel,
    TranslatorReadinessEvaluation,
    TranslatorReadinessEvaluationSummary,
    PROMOTION_REQUIREMENTS,
    MATURITY_TO_READINESS,
    evaluate_translator_readiness,
    get_readiness_evaluation,
    list_readiness_evaluations,
    get_promotion_requirements,
    get_next_promotion_level,
    can_promote,
)
from app.cam.translation_artifact import TranslationArtifact


router = APIRouter(prefix="/translators/readiness", tags=["Translator Readiness"])


# -----------------------------------------------------------------------------
# Request Models
# -----------------------------------------------------------------------------

class ReadinessEvaluationRequest(BaseModel):
    """Request model for readiness evaluation."""

    translator_id: str = Field(..., description="Translator identifier")
    target_level: Optional[ReadinessLevel] = Field(
        default=None,
        description="Target promotion level to evaluate"
    )
    artifact: Optional[TranslationArtifact] = Field(
        default=None,
        description="Optional artifact for authorization/provenance integration"
    )


class PromotionCheckRequest(BaseModel):
    """Request model for promotion eligibility check."""

    translator_id: str = Field(..., description="Translator identifier")
    target_level: Optional[ReadinessLevel] = Field(
        default=None,
        description="Target promotion level (defaults to next level)"
    )


# -----------------------------------------------------------------------------
# Response Models
# -----------------------------------------------------------------------------

class ReadinessLevelInfo(BaseModel):
    """Information about a readiness level."""

    level: ReadinessLevel
    description: str
    required_maturity: str
    min_test_fixtures: int
    requires_governance_approval: bool


class PromotionCheckResponse(BaseModel):
    """Response for promotion eligibility check."""

    translator_id: str
    can_promote: bool
    target_level: Optional[ReadinessLevel]
    blockers: List[str]

    # 7G invariants
    promotion_authorized: bool = Field(
        default=False,
        description="Always false — promotion requires human approval"
    )


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------

@router.get(
    "",
    response_model=List[TranslatorReadinessEvaluationSummary],
    summary="List readiness evaluations",
    description="List all translator readiness evaluations in the index.",
)
async def list_evaluations(
    translator_id: Optional[str] = None,
) -> List[TranslatorReadinessEvaluationSummary]:
    """List readiness evaluations, optionally filtered by translator."""
    evaluations = list_readiness_evaluations(translator_id=translator_id)
    return [e.to_summary() for e in evaluations]


@router.get(
    "/levels",
    response_model=List[ReadinessLevelInfo],
    summary="List readiness levels",
    description="List all readiness levels with their requirements.",
)
async def list_levels() -> List[ReadinessLevelInfo]:
    """List all readiness levels."""
    descriptions = {
        "experimental": "Unstable prototype. May change without notice.",
        "governed_experimental": "Regression-tracked experimental translator.",
        "stable_candidate": "Deterministic and externally validated.",
        "production": "Full production approval.",
    }

    levels = []
    for level, requirements in PROMOTION_REQUIREMENTS.items():
        levels.append(ReadinessLevelInfo(
            level=level,
            description=descriptions.get(level, ""),
            required_maturity=requirements.get("required_maturity", "unknown"),
            min_test_fixtures=requirements.get("min_test_fixtures", 0),
            requires_governance_approval=requirements.get("requires_governance_approval", False),
        ))
    return levels


@router.get(
    "/requirements/{level}",
    response_model=Dict[str, Any],
    summary="Get promotion requirements",
    description="Get requirements for a specific readiness level.",
)
async def get_level_requirements(level: ReadinessLevel) -> Dict[str, Any]:
    """Get promotion requirements for a target level."""
    requirements = get_promotion_requirements(level)
    if not requirements:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Requirements not found for level: {level}",
        )
    return {
        "level": level,
        "requirements": requirements,
        "next_level": get_next_promotion_level(level),
    }


@router.get(
    "/maturity-mapping",
    response_model=Dict[str, str],
    summary="Get maturity to readiness mapping",
    description="Get the mapping from translator maturity to readiness level.",
)
async def get_maturity_mapping() -> Dict[str, str]:
    """Get maturity to readiness level mapping."""
    return {k: v for k, v in MATURITY_TO_READINESS.items()}


@router.get(
    "/{translator_id}",
    response_model=TranslatorReadinessEvaluation,
    summary="Get translator readiness",
    description="Get the most recent readiness evaluation for a translator.",
)
async def get_translator_readiness(translator_id: str) -> TranslatorReadinessEvaluation:
    """Get readiness evaluation for a specific translator."""
    # First check if we have a cached evaluation
    evaluation = get_readiness_evaluation(translator_id)

    if evaluation is None:
        # Generate a fresh evaluation
        evaluation = evaluate_translator_readiness(translator_id=translator_id)

    return evaluation


@router.post(
    "/evaluate",
    response_model=TranslatorReadinessEvaluation,
    summary="Evaluate translator readiness",
    description="Evaluate translator readiness with optional target level and artifact.",
)
async def evaluate_readiness(
    request: ReadinessEvaluationRequest,
) -> TranslatorReadinessEvaluation:
    """
    Evaluate translator readiness.

    This is READINESS EVALUATION, not execution authorization.
    No DXF. No G-code. No machine output.
    """
    evaluation = evaluate_translator_readiness(
        translator_id=request.translator_id,
        target_level=request.target_level,
        artifact=request.artifact,
    )
    return evaluation


@router.post(
    "/can-promote",
    response_model=PromotionCheckResponse,
    summary="Check promotion eligibility",
    description="Quick check whether a translator can be promoted.",
)
async def check_promotion_eligibility(
    request: PromotionCheckRequest,
) -> PromotionCheckResponse:
    """
    Check whether translator is eligible for promotion.

    Note: Eligibility is not authorization. Actual promotion
    requires human approval.
    """
    eligible, blockers = can_promote(
        translator_id=request.translator_id,
        target_level=request.target_level,
    )

    # Determine actual target level if not specified
    if request.target_level:
        target = request.target_level
    else:
        # Get current level and derive next
        eval_result = evaluate_translator_readiness(request.translator_id)
        target = get_next_promotion_level(eval_result.current_level)

    return PromotionCheckResponse(
        translator_id=request.translator_id,
        can_promote=eligible,
        target_level=target,
        blockers=blockers,
        promotion_authorized=False,
    )
