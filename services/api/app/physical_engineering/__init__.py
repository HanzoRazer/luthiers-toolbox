"""Fail-closed advisory screening of untrusted physical-engineering proposals.

Geometry on a proposal is an untrusted claim until PEP-MESH-SEAM-003.
"""
from app.physical_engineering.errors import (
    EvidenceDigestMismatch,
    EvidenceNotFound,
    EvidenceResolutionError,
    SnapshotIntegrityError,
    ValidatorConfigurationError,
)
from app.physical_engineering.evidence import (
    EvidenceResolver,
    InMemoryEvidenceResolver,
    ResolvedEvidence,
)
from app.physical_engineering.policy import ValidationPolicyV1
from app.physical_engineering.proposal_v1 import (
    VALIDATOR_VERSION,
    ActionType,
    AuthorityClass,
    EvidenceRef,
    GeometryRegion,
    PhysicalEngineeringProposalV1,
    PhysicalEngineeringValidationV1,
    ProposedChange,
    ValidationResult,
    to_json,
    validate_proposal,
)
from app.physical_engineering.snapshot import (
    FrozenValidationSnapshotV1,
    build_validation_snapshot,
    replay_validation_snapshot,
)

__all__ = [
    "VALIDATOR_VERSION",
    "ActionType",
    "AuthorityClass",
    "EvidenceDigestMismatch",
    "EvidenceNotFound",
    "EvidenceRef",
    "EvidenceResolutionError",
    "EvidenceResolver",
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
    "build_validation_snapshot",
    "replay_validation_snapshot",
    "to_json",
    "validate_proposal",
]
