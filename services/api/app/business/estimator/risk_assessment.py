"""
Risk Assessment Module — Confidence and risk factor evaluation.

Extracted from estimator_service.py for single-responsibility.
"""
from typing import List

from .schemas import (
    EstimateRequest,
    RiskFactor,
    BuilderExperience,
    FinishType,
    FretboardInlay,
    NeckComplexity,
)


# Confidence thresholds
CONFIDENCE_HIGH_THRESHOLD = 1.15   # Total multiplier < 1.15 = high confidence
CONFIDENCE_LOW_THRESHOLD = 1.40    # Total multiplier > 1.40 = low confidence


def assess_confidence(
    combined_multiplier: float,
    request: EstimateRequest,
) -> str:
    """
    Assess estimate confidence level.

    Args:
        combined_multiplier: Combined complexity * experience factor
        request: Original estimate request

    Returns:
        Confidence level: "high", "medium", or "low"
    """
    if combined_multiplier < CONFIDENCE_HIGH_THRESHOLD:
        return "high"
    elif combined_multiplier > CONFIDENCE_LOW_THRESHOLD:
        return "low"
    else:
        return "medium"


def identify_risks(
    request: EstimateRequest,
    combined_multiplier: float,
) -> List[RiskFactor]:
    """
    Identify risk factors affecting estimate.

    Args:
        request: Original estimate request
        combined_multiplier: Combined complexity * experience factor

    Returns:
        List of identified risk factors
    """
    risks = []

    # Beginner builder risk
    if request.builder_experience == BuilderExperience.BEGINNER:
        risks.append(RiskFactor(
            factor="Beginner Experience",
            impact="high",
            description="First-time builders may take 2-3x longer than estimated",
        ))

    # High complexity risk
    if combined_multiplier > 1.5:
        risks.append(RiskFactor(
            factor="High Complexity",
            impact="medium",
            description="Multiple complex features increase variability",
        ))

    # French polish risk
    if request.complexity.finish == FinishType.SHELLAC_FRENCH_POLISH:
        risks.append(RiskFactor(
            factor="French Polish Finish",
            impact="medium",
            description="French polish is highly skill-dependent; time varies widely",
        ))

    # Custom inlay risk
    if request.complexity.fretboard_inlay == FretboardInlay.CUSTOM:
        risks.append(RiskFactor(
            factor="Custom Inlay",
            impact="medium",
            description="Custom inlay design and execution time varies significantly",
        ))

    # Multi-scale risk
    if NeckComplexity.MULTI_SCALE in request.complexity.neck:
        risks.append(RiskFactor(
            factor="Multi-Scale Frets",
            impact="medium",
            description="Fan fret layout requires precise calculation and execution",
        ))

    # Large batch risk
    if request.quantity > 6:
        risks.append(RiskFactor(
            factor="Large Batch",
            impact="low",
            description="Learning curve projections less certain for batches >6",
        ))

    return risks


def get_range_factor(confidence_level: str) -> float:
    """
    Get estimate range factor based on confidence.

    Args:
        confidence_level: "high", "medium", or "low"

    Returns:
        Range factor (e.g., 0.10 for ±10%)
    """
    return {
        "high": 0.10,    # ±10%
        "medium": 0.20,  # ±20%
        "low": 0.35,     # ±35%
    }.get(confidence_level, 0.25)
