"""
Body Evidence Candidate — Constitutional Semantic Intake Object
===============================================================

DEV ORDER 1D: IBG Constitutional Intake Foundation

BodyEvidenceCandidate is a constitutional wrapper around BodyEvidence
that carries provenance, authority state, confidence declaration,
and review enforcement.

This transforms plain semantic containers into constitutional
semantic intake objects that cannot silently become canonical.

Key principle:
    IBG semantic discovery is permitted.
    IBG ontology authority is NOT permitted.

Author: Constitutional Runtime Foundation
Date: 2026-05-18
Sprint: DEV ORDER 1D
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from app.governance import (
    AuthorityState,
    AuthorityStateContainer,
    ProvenanceRecord,
    TransformationStage,
    ConfidenceDeclaration,
    ConfidenceType,
    ReviewEnforcement,
    ReviewDecision,
    create_source_provenance,
    create_derived_provenance,
    create_heuristic_confidence,
    create_default_review_enforcement,
)

from .body_grid.body_grid_schema import BodyEvidence


class BodyEvidenceCandidateError(Exception):
    """Base exception for BodyEvidenceCandidate errors."""
    pass


class CandidateNotApprovedError(BodyEvidenceCandidateError):
    """Raised when attempting to use an unapproved candidate."""

    def __init__(self, operation: str, current_state: AuthorityState):
        self.operation = operation
        self.current_state = current_state
        super().__init__(
            f"Cannot {operation}: candidate authority is {current_state.value}, "
            "requires human_reviewed or approved_for_generation"
        )


class ProvenanceRequiredError(BodyEvidenceCandidateError):
    """Raised when provenance is required but missing."""

    def __init__(self, operation: str):
        self.operation = operation
        super().__init__(
            f"Cannot {operation}: provenance record is required"
        )


@dataclass
class BodyEvidenceCandidate:
    """
    Constitutional wrapper around BodyEvidence.

    Carries all governance metadata required for IBG intake:
    - provenance (lineage and transformation history)
    - authority state (trust level)
    - confidence declaration (typed confidence)
    - review enforcement (human review requirement)

    Default state:
        authority_state = sandbox_experimental
        review_required = True
        approved_for_ibg_memory = False

    Attributes:
        candidate_id: Unique identifier for this candidate
        evidence: The wrapped BodyEvidence
        authority: Authority state container
        provenance: Provenance record (REQUIRED for IBG intake)
        confidence: Confidence declaration
        review: Review enforcement
        created_at: When this candidate was created
        metadata: Additional metadata
    """
    candidate_id: str
    evidence: BodyEvidence
    authority: AuthorityStateContainer = field(
        default_factory=lambda: AuthorityStateContainer(
            current_state=AuthorityState.SANDBOX_EXPERIMENTAL
        )
    )
    provenance: Optional[ProvenanceRecord] = None
    confidence: ConfidenceDeclaration = field(
        default_factory=lambda: ConfidenceDeclaration(
            value=0.0,
            confidence_type=ConfidenceType.UNKNOWN,
            origin="unspecified",
            interpretation="Confidence not yet determined",
        )
    )
    review: ReviewEnforcement = field(default_factory=create_default_review_enforcement)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Constitutional flags (read-only properties)
    @property
    def review_required(self) -> bool:
        """Whether human review is required."""
        return self.review.review_required

    @property
    def review_completed(self) -> bool:
        """Whether review has been completed."""
        return self.review.review_completed

    @property
    def approved_for_ibg_memory(self) -> bool:
        """
        Whether this candidate is approved for IBG memory population.

        Requires:
        - Authority state >= human_reviewed
        - Provenance present with complete lineage
        - Review completed with APPROVE decision
        """
        if self.authority.current_state not in {
            AuthorityState.HUMAN_REVIEWED,
            AuthorityState.APPROVED_FOR_GENERATION,
        }:
            return False

        if self.provenance is None or not self.provenance.has_complete_lineage():
            return False

        if not self.review.review_completed:
            return False

        if self.review.review_decision != ReviewDecision.APPROVE:
            return False

        return True

    @property
    def authority_state(self) -> AuthorityState:
        """Current authority state."""
        return self.authority.current_state

    def has_provenance(self) -> bool:
        """Check if provenance is present."""
        return self.provenance is not None

    def has_complete_lineage(self) -> bool:
        """Check if provenance has complete lineage."""
        if self.provenance is None:
            return False
        return self.provenance.has_complete_lineage()

    def require_provenance(self, operation: str) -> ProvenanceRecord:
        """
        Assert that provenance is present.

        Args:
            operation: Description of operation requiring provenance

        Returns:
            The provenance record

        Raises:
            ProvenanceRequiredError: If provenance is missing
        """
        if self.provenance is None:
            raise ProvenanceRequiredError(operation)
        return self.provenance

    def require_approval(self, operation: str) -> None:
        """
        Assert that this candidate is approved for the given operation.

        Args:
            operation: Description of operation

        Raises:
            CandidateNotApprovedError: If not approved
        """
        if not self.approved_for_ibg_memory:
            raise CandidateNotApprovedError(operation, self.authority_state)

    def transition_authority(
        self,
        to_state: AuthorityState,
        actor: str,
        reason: str,
    ) -> None:
        """
        Transition authority state with provenance update.

        Args:
            to_state: Target authority state
            actor: Who/what is performing the transition
            reason: Why the transition is happening
        """
        transition = self.authority.transition(to_state, actor, reason)

        # Update provenance if present
        if self.provenance is not None:
            self.provenance.add_transformation(
                stage=TransformationStage.HUMAN_REVIEW if to_state == AuthorityState.HUMAN_REVIEWED
                    else TransformationStage.GENERATION_APPROVAL if to_state == AuthorityState.APPROVED_FOR_GENERATION
                    else TransformationStage.SEMANTIC_CLASSIFICATION,
                method="transition_authority",
                params={
                    "from_state": transition.from_state.value,
                    "to_state": transition.to_state.value,
                    "reason": reason,
                },
                actor=actor,
            )

    def record_review(
        self,
        reviewer_id: str,
        decision: ReviewDecision,
        notes: Optional[str] = None,
    ) -> None:
        """
        Record a human review decision.

        If approved, transitions authority to HUMAN_REVIEWED.

        Args:
            reviewer_id: ID of the reviewer
            decision: Review decision
            notes: Optional notes
        """
        self.review.record_review(reviewer_id, decision, notes)

        # If approved by human, transition authority
        if decision == ReviewDecision.APPROVE and reviewer_id.startswith("human:"):
            if self.authority.can_transition_to(AuthorityState.HUMAN_REVIEWED):
                self.transition_authority(
                    AuthorityState.HUMAN_REVIEWED,
                    reviewer_id,
                    f"Approved via human review: {notes or 'no notes'}",
                )

    def set_confidence(
        self,
        value: float,
        confidence_type: ConfidenceType,
        origin: str,
        interpretation: str,
    ) -> None:
        """
        Set confidence declaration.

        Args:
            value: Confidence value (0.0-1.0)
            confidence_type: Type of confidence
            origin: What produced this confidence
            interpretation: What this value means
        """
        self.confidence = ConfidenceDeclaration(
            value=value,
            confidence_type=confidence_type,
            origin=origin,
            interpretation=interpretation,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "candidate_id": self.candidate_id,
            "evidence": {
                "outline_points": self.evidence.outline_points,
                "source_type": self.evidence.source_type.value,
                "has_landmarks": self.evidence.has_landmarks(),
                "has_contours": self.evidence.has_contours(),
            },
            "authority": self.authority.to_dict(),
            "provenance": self.provenance.to_dict() if self.provenance else None,
            "confidence": self.confidence.to_dict(),
            "review": self.review.to_dict(),
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
            # Constitutional flags
            "review_required": self.review_required,
            "review_completed": self.review_completed,
            "approved_for_ibg_memory": self.approved_for_ibg_memory,
            "authority_state": self.authority_state.value,
        }


def create_candidate_from_evidence(
    evidence: BodyEvidence,
    source_artifact: str,
    extraction_method: str,
    extraction_params: Optional[Dict[str, Any]] = None,
    confidence_value: float = 0.5,
    confidence_origin: str = "body_isolation",
) -> BodyEvidenceCandidate:
    """
    Create a BodyEvidenceCandidate from BodyEvidence.

    Creates provenance and sets initial authority state to ADVISORY_CANDIDATE.

    Args:
        evidence: The body evidence
        source_artifact: Path or ID of the source (e.g., DXF file path)
        extraction_method: Method used to extract (e.g., "body_isolation_stage")
        extraction_params: Parameters used in extraction
        confidence_value: Initial confidence value
        confidence_origin: What produced the confidence

    Returns:
        BodyEvidenceCandidate with provenance and advisory authority
    """
    candidate_id = f"bec_{uuid.uuid4().hex[:12]}"

    # Create provenance
    provenance = create_source_provenance(
        object_id=candidate_id,
        object_type="BodyEvidenceCandidate",
        source_artifact=source_artifact,
    )

    # Add extraction transformation
    provenance.add_transformation(
        stage=TransformationStage.BODY_ISOLATION,
        method=extraction_method,
        params=extraction_params or {},
        actor="system:body_isolation",
    )

    # Create confidence declaration
    confidence = create_heuristic_confidence(
        value=confidence_value,
        origin=confidence_origin,
        interpretation="Heuristic confidence from body isolation scoring",
    )

    # Create candidate with ADVISORY_CANDIDATE authority
    authority = AuthorityStateContainer(
        current_state=AuthorityState.SANDBOX_EXPERIMENTAL
    )

    # Transition to advisory candidate
    authority.transition(
        AuthorityState.ADVISORY_CANDIDATE,
        "system:create_candidate_from_evidence",
        "Created as advisory candidate from body isolation",
    )

    return BodyEvidenceCandidate(
        candidate_id=candidate_id,
        evidence=evidence,
        authority=authority,
        provenance=provenance,
        confidence=confidence,
    )


def create_derived_candidate(
    parent: BodyEvidenceCandidate,
    new_evidence: BodyEvidence,
    transformation_method: str,
    transformation_params: Optional[Dict[str, Any]] = None,
) -> BodyEvidenceCandidate:
    """
    Create a derived BodyEvidenceCandidate from a parent.

    Preserves lineage from parent and records transformation.

    Args:
        parent: Parent candidate
        new_evidence: The new evidence
        transformation_method: Method used for transformation
        transformation_params: Parameters used

    Returns:
        New BodyEvidenceCandidate with derived provenance

    Raises:
        ProvenanceRequiredError: If parent has no provenance
    """
    parent_provenance = parent.require_provenance("create derived candidate")

    candidate_id = f"bec_{uuid.uuid4().hex[:12]}"

    # Create derived provenance
    provenance = create_derived_provenance(
        object_id=candidate_id,
        object_type="BodyEvidenceCandidate",
        parent_provenance=parent_provenance,
        transformation_stage=TransformationStage.MORPHOLOGY_ANALYSIS,
        transformation_method=transformation_method,
        transformation_params=transformation_params,
        actor="system:create_derived_candidate",
    )

    # Start as sandbox experimental (authority does not transfer)
    authority = AuthorityStateContainer(
        current_state=AuthorityState.SANDBOX_EXPERIMENTAL
    )

    return BodyEvidenceCandidate(
        candidate_id=candidate_id,
        evidence=new_evidence,
        authority=authority,
        provenance=provenance,
        confidence=parent.confidence,  # Inherit confidence initially
    )
