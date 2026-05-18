"""
Confidence Declaration — Constitutional Runtime Foundation
==========================================================

DEV ORDER 1D: IBG Constitutional Intake Foundation

Defines confidence semantics for semantic objects in the IBG intake pipeline.
Confidence declarations separate signal quality from authority legitimacy.

Key principle:
    Confidence = 0.95 does NOT mean:
    - "this is correct"
    - "this is canonical"
    - "this is approved"
    - "this can skip review"

    Confidence values must not be conflated with ontological truth.

Author: Constitutional Runtime Foundation
Date: 2026-05-18
Sprint: DEV ORDER 1D
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class ConfidenceType(str, Enum):
    """
    Types of confidence measurements.

    Each type has different semantics and interpretation.
    They must NOT be conflated.
    """

    EPISTEMIC = "epistemic"
    STATISTICAL = "statistical"
    HEURISTIC = "heuristic"
    HUMAN_ASSESSED = "human_assessed"
    COMPOSITE = "composite"
    UNKNOWN = "unknown"


# Standard non-implications for confidence values
STANDARD_NON_IMPLICATIONS: List[str] = [
    "correctness",
    "canonicity",
    "approval",
    "review bypass",
    "ontological truth",
    "authority legitimacy",
    "production readiness",
    "IBG memory eligibility",
]


@dataclass
class ConfidenceDeclaration:
    """
    Typed confidence declaration with explicit semantics.

    Separates:
        - signal quality (how good is the measurement?)
        - semantic confidence (how confident is the interpretation?)
        - authority legitimacy (does this have governance authority?)
        - human ratification (has a human approved this?)

    Attributes:
        value: Confidence value (0.0-1.0)
        confidence_type: Type of confidence measurement
        origin: What produced this confidence value
        interpretation: What this value actually means
        does_not_imply: Explicit list of non-implications
        timestamp: When this confidence was measured
        metadata: Additional context
    """
    value: float
    confidence_type: ConfidenceType
    origin: str
    interpretation: str
    does_not_imply: List[str] = field(default_factory=lambda: list(STANDARD_NON_IMPLICATIONS))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate confidence value is in range."""
        if not 0.0 <= self.value <= 1.0:
            raise ValueError(f"Confidence value must be 0.0-1.0, got {self.value}")

    def implies_correctness(self) -> bool:
        """
        Confidence NEVER implies correctness.

        This method always returns False as a constitutional safeguard.
        """
        return False

    def implies_canonicity(self) -> bool:
        """
        Confidence NEVER implies canonicity.

        This method always returns False as a constitutional safeguard.
        """
        return False

    def implies_review_bypass(self) -> bool:
        """
        Confidence NEVER implies review can be bypassed.

        This method always returns False as a constitutional safeguard.
        """
        return False

    def implies_ibg_eligibility(self) -> bool:
        """
        Confidence NEVER implies IBG memory eligibility.

        This method always returns False as a constitutional safeguard.
        """
        return False

    def is_human_assessed(self) -> bool:
        """Check if this confidence was assessed by a human."""
        return self.confidence_type == ConfidenceType.HUMAN_ASSESSED

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "value": self.value,
            "confidence_type": self.confidence_type.value,
            "origin": self.origin,
            "interpretation": self.interpretation,
            "does_not_imply": self.does_not_imply,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConfidenceDeclaration":
        """Create from dictionary."""
        return cls(
            value=data["value"],
            confidence_type=ConfidenceType(data["confidence_type"]),
            origin=data["origin"],
            interpretation=data["interpretation"],
            does_not_imply=data.get("does_not_imply", list(STANDARD_NON_IMPLICATIONS)),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {}),
        )


def create_statistical_confidence(
    value: float,
    origin: str,
    interpretation: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> ConfidenceDeclaration:
    """
    Create a statistical confidence declaration.

    Use for model outputs, scoring algorithms, probability estimates.

    Args:
        value: Confidence value (0.0-1.0)
        origin: What produced this (e.g., "contour_scorer.compute_score")
        interpretation: What this means (e.g., "probability of body contour match")
        metadata: Additional context

    Returns:
        ConfidenceDeclaration with STATISTICAL type
    """
    return ConfidenceDeclaration(
        value=value,
        confidence_type=ConfidenceType.STATISTICAL,
        origin=origin,
        interpretation=interpretation,
        metadata=metadata or {},
    )


def create_heuristic_confidence(
    value: float,
    origin: str,
    interpretation: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> ConfidenceDeclaration:
    """
    Create a heuristic confidence declaration.

    Use for rule-based estimates, threshold comparisons, qualitative judgments.

    Args:
        value: Confidence value (0.0-1.0)
        origin: What produced this (e.g., "gap_closure_heuristic")
        interpretation: What this means (e.g., "estimated gap closure quality")
        metadata: Additional context

    Returns:
        ConfidenceDeclaration with HEURISTIC type
    """
    return ConfidenceDeclaration(
        value=value,
        confidence_type=ConfidenceType.HEURISTIC,
        origin=origin,
        interpretation=interpretation,
        metadata=metadata or {},
    )


def create_epistemic_confidence(
    value: float,
    origin: str,
    interpretation: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> ConfidenceDeclaration:
    """
    Create an epistemic confidence declaration.

    Use for knowledge quality, evidence completeness, information sufficiency.

    Args:
        value: Confidence value (0.0-1.0)
        origin: What produced this (e.g., "evidence_completeness_check")
        interpretation: What this means (e.g., "how much evidence is available")
        metadata: Additional context

    Returns:
        ConfidenceDeclaration with EPISTEMIC type
    """
    return ConfidenceDeclaration(
        value=value,
        confidence_type=ConfidenceType.EPISTEMIC,
        origin=origin,
        interpretation=interpretation,
        metadata=metadata or {},
    )


def create_human_confidence(
    value: float,
    reviewer_id: str,
    interpretation: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> ConfidenceDeclaration:
    """
    Create a human-assessed confidence declaration.

    Use for human review judgments, manual assessments.

    Args:
        value: Confidence value (0.0-1.0)
        reviewer_id: ID of the human reviewer
        interpretation: What this means
        metadata: Additional context

    Returns:
        ConfidenceDeclaration with HUMAN_ASSESSED type
    """
    return ConfidenceDeclaration(
        value=value,
        confidence_type=ConfidenceType.HUMAN_ASSESSED,
        origin=f"human:{reviewer_id}",
        interpretation=interpretation,
        metadata=metadata or {},
    )


def create_unknown_confidence() -> ConfidenceDeclaration:
    """
    Create an unknown/unspecified confidence declaration.

    Use when confidence is not yet determined or cannot be measured.

    Returns:
        ConfidenceDeclaration with UNKNOWN type and 0.0 value
    """
    return ConfidenceDeclaration(
        value=0.0,
        confidence_type=ConfidenceType.UNKNOWN,
        origin="unspecified",
        interpretation="Confidence not yet determined",
    )


@dataclass
class CompositeConfidence:
    """
    Composite confidence from multiple sources.

    Used when confidence is derived from multiple measurements
    of different types.

    Attributes:
        components: Individual confidence declarations
        aggregation_method: How components were combined
        final_value: Aggregated confidence value
        final_type: Type assigned to the composite
    """
    components: List[ConfidenceDeclaration]
    aggregation_method: str
    final_value: float
    final_type: ConfidenceType = ConfidenceType.COMPOSITE

    def to_declaration(self) -> ConfidenceDeclaration:
        """Convert to a single ConfidenceDeclaration."""
        return ConfidenceDeclaration(
            value=self.final_value,
            confidence_type=self.final_type,
            origin=f"composite:{self.aggregation_method}",
            interpretation=f"Composite confidence from {len(self.components)} sources",
            metadata={
                "components": [c.to_dict() for c in self.components],
                "aggregation_method": self.aggregation_method,
            },
        )


def aggregate_confidence_min(
    declarations: List[ConfidenceDeclaration],
) -> CompositeConfidence:
    """
    Aggregate confidence using minimum (conservative).

    Args:
        declarations: List of confidence declarations

    Returns:
        CompositeConfidence with min value
    """
    if not declarations:
        return CompositeConfidence(
            components=[],
            aggregation_method="min",
            final_value=0.0,
        )

    return CompositeConfidence(
        components=declarations,
        aggregation_method="min",
        final_value=min(d.value for d in declarations),
    )


def aggregate_confidence_weighted(
    declarations: List[ConfidenceDeclaration],
    weights: Optional[List[float]] = None,
) -> CompositeConfidence:
    """
    Aggregate confidence using weighted average.

    Args:
        declarations: List of confidence declarations
        weights: Optional weights (defaults to equal weights)

    Returns:
        CompositeConfidence with weighted average value
    """
    if not declarations:
        return CompositeConfidence(
            components=[],
            aggregation_method="weighted_average",
            final_value=0.0,
        )

    if weights is None:
        weights = [1.0 / len(declarations)] * len(declarations)

    if len(weights) != len(declarations):
        raise ValueError("Weights must match declarations count")

    total_weight = sum(weights)
    if total_weight == 0:
        return CompositeConfidence(
            components=declarations,
            aggregation_method="weighted_average",
            final_value=0.0,
        )

    weighted_sum = sum(d.value * w for d, w in zip(declarations, weights))
    final_value = weighted_sum / total_weight

    return CompositeConfidence(
        components=declarations,
        aggregation_method="weighted_average",
        final_value=final_value,
    )


class ConfidenceMisrepresentationError(Exception):
    """Raised when confidence is misused or misinterpreted."""

    def __init__(self, attempted_implication: str):
        self.attempted_implication = attempted_implication
        super().__init__(
            f"Confidence misrepresentation: cannot imply {attempted_implication}. "
            "Confidence values do not convey authority or correctness."
        )
