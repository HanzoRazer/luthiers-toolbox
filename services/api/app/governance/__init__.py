"""
Governance utilities (canonical contracts).

This package provides:

Endpoint Governance:
- endpoint registry: authoritative status of API routes
- endpoint_meta decorator: annotate endpoints with governance intent
- middleware: runtime visibility (warnings) when legacy/shadow endpoints are hit

Constitutional Runtime Foundation (DEV ORDER 1D):
- authority_state: Authority state enum and transition logic
- provenance_record: Provenance tracking for semantic objects
- confidence_declaration: Typed confidence with explicit semantics
- review_enforcement: Human review requirement protection

Cross-Repository Interoperability (Governed Interoperability Normalization):
- confidence_envelope: ConfidenceEnvelopeV1 cross-repo semantic compatibility layer
- provenance_attachment: ProvenanceAttachmentDraft for IBG ratification substrate
- authority_metadata: AuthorityMetadata for cross-repo normalization

Contract-like governance models currently live flat under app/governance
pending package normalization.
"""

from .authority_state import (
    AuthorityState,
    AuthorityStateContainer,
    AuthorityStateTransition,
    AuthorityTransitionError,
    ForbiddenTransitionError,
    AUTHORITY_LEVELS,
    VALID_TRANSITIONS,
    FORBIDDEN_TRANSITIONS,
    compare_authority,
    requires_human_review,
    can_populate_ibg_memory,
)

from .provenance_record import (
    ProvenanceRecord,
    TransformationRecord,
    TransformationStage,
    ProvenanceMissingError,
    ProvenanceIntegrityError,
    create_source_provenance,
    create_derived_provenance,
)

from .confidence_declaration import (
    ConfidenceDeclaration,
    ConfidenceType,
    CompositeConfidence,
    ConfidenceMisrepresentationError,
    create_statistical_confidence,
    create_heuristic_confidence,
    create_epistemic_confidence,
    create_human_confidence,
    create_unknown_confidence,
    aggregate_confidence_min,
    aggregate_confidence_weighted,
)

from .review_enforcement import (
    ReviewEnforcement,
    ReviewRecord,
    ReviewDecision,
    ReviewBypassAttemptError,
    ReviewIncompleteError,
    create_default_review_enforcement,
    create_pre_approved_review_enforcement,
)

from .confidence_envelope import (
    ConfidenceEnvelopeV1,
    SemanticDomain,
    EpistemicStatus,
    SourceSystem,
    CROSS_REPO_NON_IMPLICATIONS,
    ConfidenceEnvelopeIntegrityError,
    create_advisory_envelope,
    create_interpretive_envelope,
)

from .provenance_attachment import (
    ProvenanceAttachmentDraft,
    ProvenanceAttachmentStatus,
    NON_EXPORTABLE_STATUSES,
    IBG_DEFAULT_STATUS,
    ProvenanceAttachmentDraftError,
    ProvenanceRatificationNotAuthorizedError,
    create_ibg_provenance_draft,
)

from .authority_metadata import (
    AuthorityMetadata,
    ReviewState,
    LifecycleState,
    SourceRepo,
    AuthorityMetadataError,
    create_luthiers_authority_metadata,
    create_vectorizer_authority_metadata,
    create_ibg_authority_metadata,
)

__all__ = [
    # Authority State
    "AuthorityState",
    "AuthorityStateContainer",
    "AuthorityStateTransition",
    "AuthorityTransitionError",
    "ForbiddenTransitionError",
    "AUTHORITY_LEVELS",
    "VALID_TRANSITIONS",
    "FORBIDDEN_TRANSITIONS",
    "compare_authority",
    "requires_human_review",
    "can_populate_ibg_memory",
    # Provenance
    "ProvenanceRecord",
    "TransformationRecord",
    "TransformationStage",
    "ProvenanceMissingError",
    "ProvenanceIntegrityError",
    "create_source_provenance",
    "create_derived_provenance",
    # Confidence
    "ConfidenceDeclaration",
    "ConfidenceType",
    "CompositeConfidence",
    "ConfidenceMisrepresentationError",
    "create_statistical_confidence",
    "create_heuristic_confidence",
    "create_epistemic_confidence",
    "create_human_confidence",
    "create_unknown_confidence",
    "aggregate_confidence_min",
    "aggregate_confidence_weighted",
    # Review
    "ReviewEnforcement",
    "ReviewRecord",
    "ReviewDecision",
    "ReviewBypassAttemptError",
    "ReviewIncompleteError",
    "create_default_review_enforcement",
    "create_pre_approved_review_enforcement",
    # Confidence Envelope (Cross-Repo Interoperability)
    "ConfidenceEnvelopeV1",
    "SemanticDomain",
    "EpistemicStatus",
    "SourceSystem",
    "CROSS_REPO_NON_IMPLICATIONS",
    "ConfidenceEnvelopeIntegrityError",
    "create_advisory_envelope",
    "create_interpretive_envelope",
    # Provenance Attachment (IBG Ratification Substrate)
    "ProvenanceAttachmentDraft",
    "ProvenanceAttachmentStatus",
    "NON_EXPORTABLE_STATUSES",
    "IBG_DEFAULT_STATUS",
    "ProvenanceAttachmentDraftError",
    "ProvenanceRatificationNotAuthorizedError",
    "create_ibg_provenance_draft",
    # Authority Metadata (Cross-Repo Normalization)
    "AuthorityMetadata",
    "ReviewState",
    "LifecycleState",
    "SourceRepo",
    "AuthorityMetadataError",
    "create_luthiers_authority_metadata",
    "create_vectorizer_authority_metadata",
    "create_ibg_authority_metadata",
]
