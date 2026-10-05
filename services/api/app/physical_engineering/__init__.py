"""Fail-closed advisory screening of untrusted physical-engineering proposals.

Geometry on a proposal is an untrusted claim until PEP-MESH-SEAM-003.
"""
from app.physical_engineering.errors import (
    EvidenceDigestMismatch,
    EvidenceNotFound,
    SnapshotIntegrityError,
    ValidatorConfigurationError,
)
from app.physical_engineering.evidence import (
    EvidenceRef,
    EvidenceResolver,
    FixtureArtifact,
    InMemoryEvidenceResolver,
    ResolvedEvidence,
    is_finite_number,
    text_token,
)
from app.physical_engineering.policy import ValidationPolicyV1
from app.physical_engineering.proposal_v1 import (
    CONTRADICTION_RULE_VERSION,
    VALIDATOR_VERSION,
    ActionType,
    AuthorityClass,
    GeometryRegion,
    PhysicalEngineeringProposalV1,
    PhysicalEngineeringValidationV1,
    ProposedChange,
    ValidationResult,
    capture_snapshot,
    replay_validation,
    to_json,
    validate_proposal,
)
from app.physical_engineering.snapshot import FrozenValidationSnapshotV1

__all__ = [
    "CONTRADICTION_RULE_VERSION",
    "VALIDATOR_VERSION",
    "ActionType",
    "AuthorityClass",
    "EvidenceDigestMismatch",
    "EvidenceNotFound",
    "EvidenceRef",
    "EvidenceResolver",
    "FixtureArtifact",
    "FrozenValidationSnapshotV1",
    "GeometryRegion",
    "InMemoryEvidenceResolver",
    "PhysicalEngineeringProposalV1",
    "PhysicalEngineeringValidationV1",
    "ProposedChange",
    "ResolvedEvidence",
    "SnapshotIntegrityError",
    "ValidationPolicyV1",
    "ValidationResult",
    "ValidatorConfigurationError",
    "capture_snapshot",
    "is_finite_number",
    "text_token",
    "replay_validation",
    "to_json",
    "validate_proposal",
]
