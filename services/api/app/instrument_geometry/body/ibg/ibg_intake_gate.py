"""
IBG Intake Gate — Constitutional Semantic Intake Enforcement
============================================================

DEV ORDER 1D: IBG Constitutional Intake Foundation

The IBG Intake Gate prevents unauthorized semantic objects from entering:
- IBG memory
- Semantic persistence
- Downstream CAD authority
- Canonical morphology registries

Key principle:
    No BodyIsolationResult may populate IBG memory until:
    - provenance is present
    - topology integrity is adequate
    - human review state is explicit
    - authority state is sufficient

Author: Constitutional Runtime Foundation
Date: 2026-05-18
Sprint: DEV ORDER 1D
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from app.governance import (
    AuthorityState,
    ProvenanceRecord,
    ReviewDecision,
    can_populate_ibg_memory,
)

from .body_evidence_candidate import BodyEvidenceCandidate


class IntakeRejectionReason(str, Enum):
    """Reasons for intake rejection."""
    AUTHORITY_INSUFFICIENT = "authority_insufficient"
    PROVENANCE_MISSING = "provenance_missing"
    PROVENANCE_INCOMPLETE = "provenance_incomplete"
    REVIEW_REQUIRED = "review_required"
    REVIEW_NOT_APPROVED = "review_not_approved"
    CONFIDENCE_UNDECLARED = "confidence_undeclared"
    REVIEW_BYPASS_DETECTED = "review_bypass_detected"
    TOPOLOGY_INTEGRITY_DEGRADED = "topology_integrity_degraded"
    CANDIDATE_REJECTED = "candidate_rejected"


class IBGIntakeRejectionError(Exception):
    """Raised when intake is rejected."""

    def __init__(
        self,
        reason: IntakeRejectionReason,
        details: str,
        candidate_id: Optional[str] = None,
    ):
        self.reason = reason
        self.details = details
        self.candidate_id = candidate_id
        super().__init__(
            f"IBG intake rejected [{reason.value}]: {details}"
        )


@dataclass
class IntakeValidationResult:
    """
    Result of intake validation.

    Attributes:
        is_valid: Whether the candidate passed all gates
        candidate_id: ID of the candidate validated
        rejections: List of rejection reasons (empty if valid)
        warnings: List of non-blocking warnings
        validated_at: Timestamp of validation
        gate_results: Detailed results per gate
    """
    is_valid: bool
    candidate_id: str
    rejections: List[IntakeRejectionReason] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    validated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    gate_results: Dict[str, bool] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "is_valid": self.is_valid,
            "candidate_id": self.candidate_id,
            "rejections": [r.value for r in self.rejections],
            "warnings": self.warnings,
            "validated_at": self.validated_at.isoformat(),
            "gate_results": self.gate_results,
        }


@dataclass
class IBGIntakeGateConfig:
    """
    Configuration for the IBG Intake Gate.

    Attributes:
        minimum_authority: Minimum authority state required
        require_provenance: Whether provenance is required
        require_complete_lineage: Whether complete lineage is required
        require_human_review: Whether human review is required
        minimum_topology_integrity: Minimum topology integrity score
        allow_bypass_attempts: How many bypass attempts are tolerated (0 = none)
    """
    minimum_authority: AuthorityState = AuthorityState.HUMAN_REVIEWED
    require_provenance: bool = True
    require_complete_lineage: bool = True
    require_human_review: bool = True
    minimum_topology_integrity: float = 0.5
    allow_bypass_attempts: int = 0


class IBGIntakeGate:
    """
    Constitutional gate for IBG memory intake.

    Validates candidates against governance requirements before
    allowing intake to IBG memory or downstream systems.

    Usage:
        gate = IBGIntakeGate()
        result = gate.validate(candidate)
        if result.is_valid:
            # Safe to proceed with intake
            pass
        else:
            # Handle rejections
            for reason in result.rejections:
                print(f"Rejected: {reason.value}")
    """

    def __init__(self, config: Optional[IBGIntakeGateConfig] = None):
        """Initialize the gate with optional configuration."""
        self.config = config or IBGIntakeGateConfig()

    def validate(
        self,
        candidate: BodyEvidenceCandidate,
    ) -> IntakeValidationResult:
        """
        Validate a candidate for IBG intake.

        Runs all gates and returns a comprehensive result.

        Args:
            candidate: The candidate to validate

        Returns:
            IntakeValidationResult with all gate results
        """
        rejections: List[IntakeRejectionReason] = []
        warnings: List[str] = []
        gate_results: Dict[str, bool] = {}

        # Gate 1: Authority state
        authority_ok = self._check_authority(candidate)
        gate_results["authority"] = authority_ok
        if not authority_ok:
            rejections.append(IntakeRejectionReason.AUTHORITY_INSUFFICIENT)

        # Gate 2: Provenance presence
        if self.config.require_provenance:
            provenance_ok = self._check_provenance_presence(candidate)
            gate_results["provenance_presence"] = provenance_ok
            if not provenance_ok:
                rejections.append(IntakeRejectionReason.PROVENANCE_MISSING)

        # Gate 3: Provenance completeness
        if self.config.require_complete_lineage and candidate.has_provenance():
            lineage_ok = self._check_provenance_completeness(candidate)
            gate_results["provenance_completeness"] = lineage_ok
            if not lineage_ok:
                rejections.append(IntakeRejectionReason.PROVENANCE_INCOMPLETE)

        # Gate 4: Review status
        if self.config.require_human_review:
            review_ok = self._check_review_status(candidate)
            gate_results["review_status"] = review_ok
            if not review_ok:
                if candidate.review_required and not candidate.review_completed:
                    rejections.append(IntakeRejectionReason.REVIEW_REQUIRED)
                elif candidate.review_completed and candidate.review.review_decision != ReviewDecision.APPROVE:
                    rejections.append(IntakeRejectionReason.REVIEW_NOT_APPROVED)

        # Gate 5: Confidence declaration
        confidence_ok = self._check_confidence(candidate)
        gate_results["confidence"] = confidence_ok
        if not confidence_ok:
            rejections.append(IntakeRejectionReason.CONFIDENCE_UNDECLARED)

        # Gate 6: Review bypass detection
        bypass_ok = self._check_bypass_attempts(candidate)
        gate_results["bypass_detection"] = bypass_ok
        if not bypass_ok:
            rejections.append(IntakeRejectionReason.REVIEW_BYPASS_DETECTED)

        # Gate 7: Topology integrity
        if candidate.has_provenance():
            integrity_ok = self._check_topology_integrity(candidate)
            gate_results["topology_integrity"] = integrity_ok
            if not integrity_ok:
                rejections.append(IntakeRejectionReason.TOPOLOGY_INTEGRITY_DEGRADED)
                if candidate.provenance:
                    for note in candidate.provenance.topology_degradation_notes:
                        warnings.append(f"Topology degradation: {note}")

        # Gate 8: Rejection status
        rejection_ok = self._check_rejection_status(candidate)
        gate_results["rejection_status"] = rejection_ok
        if not rejection_ok:
            rejections.append(IntakeRejectionReason.CANDIDATE_REJECTED)

        return IntakeValidationResult(
            is_valid=len(rejections) == 0,
            candidate_id=candidate.candidate_id,
            rejections=rejections,
            warnings=warnings,
            gate_results=gate_results,
        )

    def validate_or_raise(
        self,
        candidate: BodyEvidenceCandidate,
    ) -> IntakeValidationResult:
        """
        Validate a candidate and raise on rejection.

        Args:
            candidate: The candidate to validate

        Returns:
            IntakeValidationResult (only if valid)

        Raises:
            IBGIntakeRejectionError: If any gate fails
        """
        result = self.validate(candidate)

        if not result.is_valid and result.rejections:
            first_rejection = result.rejections[0]
            raise IBGIntakeRejectionError(
                reason=first_rejection,
                details=f"Failed gates: {[r.value for r in result.rejections]}",
                candidate_id=candidate.candidate_id,
            )

        return result

    def _check_authority(self, candidate: BodyEvidenceCandidate) -> bool:
        """Check if authority state meets minimum."""
        return can_populate_ibg_memory(candidate.authority_state)

    def _check_provenance_presence(self, candidate: BodyEvidenceCandidate) -> bool:
        """Check if provenance is present."""
        return candidate.has_provenance()

    def _check_provenance_completeness(self, candidate: BodyEvidenceCandidate) -> bool:
        """Check if provenance has complete lineage."""
        return candidate.has_complete_lineage()

    def _check_review_status(self, candidate: BodyEvidenceCandidate) -> bool:
        """Check if review is completed with approval."""
        if not candidate.review_completed:
            return False
        return candidate.review.review_decision == ReviewDecision.APPROVE

    def _check_confidence(self, candidate: BodyEvidenceCandidate) -> bool:
        """Check if confidence is properly declared."""
        from app.governance import ConfidenceType
        return candidate.confidence.confidence_type != ConfidenceType.UNKNOWN

    def _check_bypass_attempts(self, candidate: BodyEvidenceCandidate) -> bool:
        """Check if bypass attempts exceed threshold."""
        return candidate.review.bypass_attempt_count <= self.config.allow_bypass_attempts

    def _check_topology_integrity(self, candidate: BodyEvidenceCandidate) -> bool:
        """Check if topology integrity meets minimum."""
        if candidate.provenance is None:
            return True  # Can't check without provenance
        return candidate.provenance.topology_integrity_score >= self.config.minimum_topology_integrity

    def _check_rejection_status(self, candidate: BodyEvidenceCandidate) -> bool:
        """Check if candidate has been rejected."""
        return candidate.authority_state != AuthorityState.REJECTED


def create_default_intake_gate() -> IBGIntakeGate:
    """
    Create the default IBG Intake Gate with standard configuration.

    Default requirements:
    - Authority >= HUMAN_REVIEWED
    - Provenance required with complete lineage
    - Human review required with APPROVE decision
    - Minimum topology integrity 0.5
    - Zero bypass attempts tolerated

    Returns:
        IBGIntakeGate with default configuration
    """
    return IBGIntakeGate()


def create_strict_intake_gate() -> IBGIntakeGate:
    """
    Create a strict IBG Intake Gate for production use.

    Stricter requirements:
    - Authority >= APPROVED_FOR_GENERATION
    - Higher topology integrity threshold (0.7)

    Returns:
        IBGIntakeGate with strict configuration
    """
    return IBGIntakeGate(IBGIntakeGateConfig(
        minimum_authority=AuthorityState.APPROVED_FOR_GENERATION,
        minimum_topology_integrity=0.7,
    ))


def create_permissive_intake_gate() -> IBGIntakeGate:
    """
    Create a permissive IBG Intake Gate for development/testing.

    WARNING: This gate is more permissive and should NOT be used
    in production. It still requires provenance and review.

    Relaxed requirements:
    - Authority >= HUMAN_REVIEWED (unchanged)
    - Lower topology integrity threshold (0.3)
    - Some bypass attempts tolerated

    Returns:
        IBGIntakeGate with permissive configuration
    """
    return IBGIntakeGate(IBGIntakeGateConfig(
        minimum_topology_integrity=0.3,
        allow_bypass_attempts=2,
    ))
