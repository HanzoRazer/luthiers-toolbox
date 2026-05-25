"""
Confidence Envelope V1 — Cross-Repository Semantic Compatibility Layer
=======================================================================

GOVERNED INTEROPERABILITY NORMALIZATION SPRINT: 2026-05-24

This module provides a cross-repo semantic compatibility layer that wraps
confidence values from multiple source systems WITHOUT replacing them.

Design principles:
    - Interoperability before unification
    - Preserves source system semantics (TypedConfidenceV1, ConfidenceDeclaration)
    - Constrains rank_score misinterpretation
    - Always non-authoritative at runtime
    - Human review always required

Cross-repo mapping:
    tap_tone_pi    → TypedConfidenceV1 (ADR-0012 epistemic taxonomy)
    luthiers       → ConfidenceDeclaration (confidence_type enum)
    CAM-Assist     → Authority blocks (execution_authority_claim)
    vectorizer     → R_AND_D_EXCLUDED (HEURISTIC/PREDICTED default)

Constitutional invariant: ConfidenceEnvelopeV1 NEVER authorizes execution.

Author: Governed Interoperability Normalization Sprint
Date: 2026-05-24
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union

from .confidence_declaration import (
    ConfidenceDeclaration,
    ConfidenceType,
    STANDARD_NON_IMPLICATIONS,
)


class SemanticDomain(str, Enum):
    """
    Semantic domains per tap_tone ADR-0010 orthogonal domains.

    Four domains with different authority characteristics:
        MEASUREMENT: Context-dependent legitimacy (sensor capture, governed DXF)
        ADVISORY: May prioritize attention only, no truth establishment
        INTERPRETIVE: Model-dependent, no truth establishment
        OPERATOR: Final for human decisions
    """
    MEASUREMENT = "measurement"
    ADVISORY = "advisory"
    INTERPRETIVE = "interpretive"
    OPERATOR = "operator"


class EpistemicStatus(str, Enum):
    """
    Epistemic status taxonomy aligned with tap_tone ADR-0012.

    Each status has different authority implications for cross-repo exchange.
    """
    OBSERVED = "observed"
    DERIVED = "derived"
    ESTIMATED = "estimated"
    PREDICTED = "predicted"
    HEURISTIC = "heuristic"
    OPERATOR_ANNOTATED = "operator_annotated"
    EXTERNALLY_SOURCED = "externally_sourced"
    UNKNOWN = "unknown"


class SourceSystem(str, Enum):
    """
    Source systems in the multi-repo architecture.

    Each system has its own confidence vocabulary that this envelope normalizes.
    """
    TAP_TONE_PI = "tap_tone_pi"
    LUTHIERS_TOOLBOX = "luthiers_toolbox"
    CAM_ASSIST_BLUEPRINT = "cam_assist_blueprint"
    VECTORIZER_SANDBOX = "vectorizer_sandbox"
    EXTERNAL = "external"
    UNKNOWN = "unknown"


CROSS_REPO_NON_IMPLICATIONS: List[str] = [
    *STANDARD_NON_IMPLICATIONS,
    "execution authorization",
    "machine output legitimacy",
    "automatic routing approval",
    "semantic consensus",
    "constitutional override",
    "governance bypass",
    "cross-repo authority propagation",
]


@dataclass
class ConfidenceEnvelopeV1:
    """
    Cross-repository semantic compatibility layer for confidence values.

    This envelope WRAPS confidence values from source systems to enable
    cross-repo interoperability. It does NOT replace the source system's
    native confidence representation.

    Key invariants:
        - runtime_authoritative is ALWAYS False
        - review_required is ALWAYS True
        - execution_authorized is ALWAYS False
        - implies_* methods ALWAYS return False

    Usage:
        # Wrap a luthiers ConfidenceDeclaration
        envelope = ConfidenceEnvelopeV1.from_confidence_declaration(decl)

        # Wrap a tap_tone TypedConfidenceV1 (via dict representation)
        envelope = ConfidenceEnvelopeV1.from_typed_confidence_dict(typed_conf_dict)

        # Wrap a raw rank_score with constrained semantics
        envelope = ConfidenceEnvelopeV1.from_rank_score(score, context)

    Attributes:
        domain: Semantic domain per ADR-0010 orthogonal domains
        source_system: Which repo/system produced this confidence
        semantic_scope: What this confidence actually measures
        confidence_type: Mapped confidence type from source system
        confidence_value: The numeric confidence value (0.0-1.0)
        epistemic_status: Optional epistemic status per ADR-0012
        evidence_basis: What evidence supports this confidence
        review_required: ALWAYS True — constitutional invariant
        non_implications: Explicit list of what this does NOT imply
        runtime_authoritative: ALWAYS False — constitutional invariant
        execution_authorized: ALWAYS False — constitutional invariant
        source_representation: Original confidence object serialized
        created_at: When this envelope was created
        metadata: Additional cross-repo context
    """
    domain: SemanticDomain
    source_system: SourceSystem
    semantic_scope: str
    confidence_type: ConfidenceType
    confidence_value: float
    epistemic_status: Optional[EpistemicStatus] = None
    evidence_basis: str = ""
    review_required: Literal[True] = True
    non_implications: List[str] = field(
        default_factory=lambda: list(CROSS_REPO_NON_IMPLICATIONS)
    )
    runtime_authoritative: Literal[False] = False
    execution_authorized: Literal[False] = False
    source_representation: Optional[Dict[str, Any]] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate constitutional invariants."""
        if self.runtime_authoritative is not False:
            raise ValueError(
                "Constitutional invariant violation: runtime_authoritative must be False"
            )
        if self.review_required is not True:
            raise ValueError(
                "Constitutional invariant violation: review_required must be True"
            )
        if self.execution_authorized is not False:
            raise ValueError(
                "Constitutional invariant violation: execution_authorized must be False"
            )
        if not 0.0 <= self.confidence_value <= 1.0:
            raise ValueError(
                f"Confidence value must be 0.0-1.0, got {self.confidence_value}"
            )

    def implies_correctness(self) -> Literal[False]:
        """Confidence envelopes NEVER imply correctness."""
        return False

    def implies_canonicity(self) -> Literal[False]:
        """Confidence envelopes NEVER imply canonicity."""
        return False

    def implies_review_bypass(self) -> Literal[False]:
        """Confidence envelopes NEVER imply review can be bypassed."""
        return False

    def implies_execution_authority(self) -> Literal[False]:
        """Confidence envelopes NEVER imply execution authority."""
        return False

    def implies_governance_bypass(self) -> Literal[False]:
        """Confidence envelopes NEVER imply governance bypass."""
        return False

    def implies_cross_repo_authority(self) -> Literal[False]:
        """Confidence envelopes NEVER propagate authority across repositories."""
        return False

    def is_production_authoritative(self) -> Literal[False]:
        """Envelopes are NEVER production authoritative — interoperability layer only."""
        return False

    def requires_human_review(self) -> Literal[True]:
        """Envelopes ALWAYS require human review before any downstream action."""
        return True

    def get_epistemic_posture(self) -> EpistemicStatus:
        """
        Get the epistemic posture for cross-repo exchange.

        If epistemic_status is explicitly set, use that.
        Otherwise, infer from confidence_type and source_system.
        """
        if self.epistemic_status is not None:
            return self.epistemic_status

        # Infer from confidence type and source
        if self.confidence_type == ConfidenceType.HUMAN_ASSESSED:
            return EpistemicStatus.OPERATOR_ANNOTATED
        if self.source_system == SourceSystem.VECTORIZER_SANDBOX:
            return EpistemicStatus.PREDICTED
        if self.confidence_type == ConfidenceType.HEURISTIC:
            return EpistemicStatus.HEURISTIC
        if self.confidence_type == ConfidenceType.STATISTICAL:
            return EpistemicStatus.ESTIMATED

        return EpistemicStatus.UNKNOWN

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "envelope_version": "v1",
            "domain": self.domain.value,
            "source_system": self.source_system.value,
            "semantic_scope": self.semantic_scope,
            "confidence_type": self.confidence_type.value,
            "confidence_value": self.confidence_value,
            "epistemic_status": (
                self.epistemic_status.value if self.epistemic_status else None
            ),
            "evidence_basis": self.evidence_basis,
            "review_required": self.review_required,
            "non_implications": self.non_implications,
            "runtime_authoritative": self.runtime_authoritative,
            "execution_authorized": self.execution_authorized,
            "source_representation": self.source_representation,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
            "epistemic_posture": self.get_epistemic_posture().value,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConfidenceEnvelopeV1":
        """Create from dictionary."""
        return cls(
            domain=SemanticDomain(data["domain"]),
            source_system=SourceSystem(data["source_system"]),
            semantic_scope=data["semantic_scope"],
            confidence_type=ConfidenceType(data["confidence_type"]),
            confidence_value=data["confidence_value"],
            epistemic_status=(
                EpistemicStatus(data["epistemic_status"])
                if data.get("epistemic_status")
                else None
            ),
            evidence_basis=data.get("evidence_basis", ""),
            non_implications=data.get(
                "non_implications", list(CROSS_REPO_NON_IMPLICATIONS)
            ),
            source_representation=data.get("source_representation"),
            created_at=datetime.fromisoformat(data["created_at"]),
            metadata=data.get("metadata", {}),
        )

    @classmethod
    def from_confidence_declaration(
        cls,
        declaration: ConfidenceDeclaration,
        domain: SemanticDomain = SemanticDomain.ADVISORY,
        epistemic_status: Optional[EpistemicStatus] = None,
    ) -> "ConfidenceEnvelopeV1":
        """
        Wrap a luthiers-toolbox ConfidenceDeclaration.

        Args:
            declaration: The ConfidenceDeclaration to wrap
            domain: Semantic domain for this confidence
            epistemic_status: Optional explicit epistemic status

        Returns:
            ConfidenceEnvelopeV1 wrapping the declaration
        """
        return cls(
            domain=domain,
            source_system=SourceSystem.LUTHIERS_TOOLBOX,
            semantic_scope=declaration.interpretation,
            confidence_type=declaration.confidence_type,
            confidence_value=declaration.value,
            epistemic_status=epistemic_status,
            evidence_basis=declaration.origin,
            non_implications=list(declaration.does_not_imply) + [
                "cross-repo authority propagation",
                "execution authorization",
            ],
            source_representation=declaration.to_dict(),
            metadata=declaration.metadata,
        )

    @classmethod
    def from_typed_confidence_dict(
        cls,
        typed_conf: Dict[str, Any],
        domain: Optional[SemanticDomain] = None,
    ) -> "ConfidenceEnvelopeV1":
        """
        Wrap a tap_tone_pi TypedConfidenceV1 (via dict representation).

        TypedConfidenceV1 schema expected:
            {
                "domain": str,
                "value": float,
                "source": str,
                "epistemic_status": str (optional),
                ...
            }

        Args:
            typed_conf: Dictionary representation of TypedConfidenceV1
            domain: Override domain (defaults to mapping from typed_conf["domain"])

        Returns:
            ConfidenceEnvelopeV1 wrapping the TypedConfidenceV1
        """
        tap_tone_domain = typed_conf.get("domain", "advisory")
        domain_map = {
            "measurement": SemanticDomain.MEASUREMENT,
            "advisory": SemanticDomain.ADVISORY,
            "interpretive": SemanticDomain.INTERPRETIVE,
            "operator": SemanticDomain.OPERATOR,
        }
        resolved_domain = domain or domain_map.get(
            tap_tone_domain, SemanticDomain.ADVISORY
        )

        epistemic_str = typed_conf.get("epistemic_status")
        epistemic_status = None
        if epistemic_str:
            try:
                epistemic_status = EpistemicStatus(epistemic_str.lower())
            except ValueError:
                epistemic_status = EpistemicStatus.UNKNOWN

        conf_type_str = typed_conf.get("confidence_type", "heuristic")
        try:
            conf_type = ConfidenceType(conf_type_str)
        except ValueError:
            conf_type = ConfidenceType.UNKNOWN

        return cls(
            domain=resolved_domain,
            source_system=SourceSystem.TAP_TONE_PI,
            semantic_scope=typed_conf.get("source", "tap_tone typed confidence"),
            confidence_type=conf_type,
            confidence_value=typed_conf.get("value", 0.0),
            epistemic_status=epistemic_status,
            evidence_basis=typed_conf.get("source", ""),
            source_representation=typed_conf,
        )

    @classmethod
    def from_rank_score(
        cls,
        score: float,
        context: str,
        source_system: SourceSystem = SourceSystem.LUTHIERS_TOOLBOX,
    ) -> "ConfidenceEnvelopeV1":
        """
        Wrap a rank_score with constrained semantics.

        rank_score values are HEURISTIC sort keys that do NOT imply:
            - correctness
            - approval
            - execution authority
            - review bypass

        Args:
            score: The rank_score value (0.0-1.0)
            context: What this rank_score measures
            source_system: Source of the rank_score

        Returns:
            ConfidenceEnvelopeV1 with HEURISTIC type and constrained semantics
        """
        return cls(
            domain=SemanticDomain.ADVISORY,
            source_system=source_system,
            semantic_scope=f"rank_score: {context}",
            confidence_type=ConfidenceType.HEURISTIC,
            confidence_value=score,
            epistemic_status=EpistemicStatus.HEURISTIC,
            evidence_basis="composite ranking algorithm",
            non_implications=list(CROSS_REPO_NON_IMPLICATIONS) + [
                "rank implies approval",
                "high score implies correctness",
                "sort order implies authority",
            ],
            metadata={"wrapped_type": "rank_score", "context": context},
        )

    @classmethod
    def from_vectorizer_output(
        cls,
        confidence_value: float,
        description: str,
        workflow_id: Optional[str] = None,
    ) -> "ConfidenceEnvelopeV1":
        """
        Wrap vectorizer-sandbox output with R_AND_D_EXCLUDED posture.

        Vectorizer outputs default to PREDICTED/HEURISTIC epistemic posture
        and must not feed production spine without graduation.

        Args:
            confidence_value: The confidence value
            description: What this confidence measures
            workflow_id: Optional workflow identifier

        Returns:
            ConfidenceEnvelopeV1 with R_AND_D_EXCLUDED posture
        """
        return cls(
            domain=SemanticDomain.INTERPRETIVE,
            source_system=SourceSystem.VECTORIZER_SANDBOX,
            semantic_scope=description,
            confidence_type=ConfidenceType.HEURISTIC,
            confidence_value=confidence_value,
            epistemic_status=EpistemicStatus.PREDICTED,
            evidence_basis="vectorizer research pipeline",
            non_implications=list(CROSS_REPO_NON_IMPLICATIONS) + [
                "production readiness",
                "spine integration approval",
                "lifecycle graduation",
            ],
            metadata={
                "lifecycle_class": "R_AND_D_EXCLUDED",
                "workflow_id": workflow_id,
            },
        )


def create_advisory_envelope(
    value: float,
    scope: str,
    source: SourceSystem,
    evidence: str = "",
) -> ConfidenceEnvelopeV1:
    """
    Create an advisory confidence envelope.

    Use for attention-prioritization signals that do NOT establish truth.

    Args:
        value: Confidence value (0.0-1.0)
        scope: What this confidence measures
        source: Source system
        evidence: Evidence basis

    Returns:
        ConfidenceEnvelopeV1 with ADVISORY domain
    """
    return ConfidenceEnvelopeV1(
        domain=SemanticDomain.ADVISORY,
        source_system=source,
        semantic_scope=scope,
        confidence_type=ConfidenceType.HEURISTIC,
        confidence_value=value,
        epistemic_status=EpistemicStatus.HEURISTIC,
        evidence_basis=evidence,
    )


def create_interpretive_envelope(
    value: float,
    scope: str,
    source: SourceSystem,
    evidence: str = "",
) -> ConfidenceEnvelopeV1:
    """
    Create an interpretive confidence envelope.

    Use for model-dependent interpretations that do NOT establish truth.

    Args:
        value: Confidence value (0.0-1.0)
        scope: What this confidence measures
        source: Source system
        evidence: Evidence basis

    Returns:
        ConfidenceEnvelopeV1 with INTERPRETIVE domain
    """
    return ConfidenceEnvelopeV1(
        domain=SemanticDomain.INTERPRETIVE,
        source_system=source,
        semantic_scope=scope,
        confidence_type=ConfidenceType.STATISTICAL,
        confidence_value=value,
        epistemic_status=EpistemicStatus.ESTIMATED,
        evidence_basis=evidence,
    )


class ConfidenceEnvelopeIntegrityError(Exception):
    """Raised when confidence envelope integrity is compromised."""

    def __init__(self, violation: str):
        self.violation = violation
        super().__init__(
            f"Confidence envelope integrity violation: {violation}. "
            "Envelopes must maintain constitutional invariants."
        )
