"""
IBG Repository — Governed Repository Change Proposal contracts (PR A).

This package owns repository proposal *automation* — turning governed engineering
evidence into deterministic, reviewable repository change proposals. It is deliberately
homed OUTSIDE ``instrument_geometry/body/ibg/`` (which owns body-geometry evidence) and
OUTSIDE ``governance/`` (which defines constraints, not operational construction).

Constitutional boundary: this package moves IBG from observation to *proposal*, never to
authority. Nothing here promotes evidence, grants canonical authority, mutates a checkout,
commits, pushes, or creates a GitHub PR. PR A adds contracts only — no git, no router,
no filesystem or network I/O.
"""

from __future__ import annotations

from .proposal_target import (
    ProposalTargetBinding,
    ProposalBindingError,
    EvidenceContractError,
    InvalidTargetPathError,
    build_proposal_target_binding,
    normalize_producing_subsystem,
)
from .cbsp21_patch_adapter import (
    CBSP21_SCHEMA,
    REQUIRED_FIELDS,
    CBSP21PacketError,
    CBSP21PatchPacketAdapter,
    build_cbsp21_patch_packet,
    validate_cbsp21_patch_packet,
    canonical_packet_json,
    compute_packet_hash,
)
from .repository_change_proposal import (
    RepositoryChangeProposal,
    RepositoryChangeProposalError,
    PROPOSAL_CONSTITUTIONAL_CLASSIFICATION,
    build_repository_change_proposal,
)
from .repository_review_package import (
    RepositoryProposalReviewPackage,
    RepositoryReviewPackageError,
    build_repository_proposal_review_package,
)

__all__ = [
    "ProposalTargetBinding",
    "ProposalBindingError",
    "EvidenceContractError",
    "InvalidTargetPathError",
    "build_proposal_target_binding",
    "normalize_producing_subsystem",
    "CBSP21_SCHEMA",
    "REQUIRED_FIELDS",
    "CBSP21PacketError",
    "CBSP21PatchPacketAdapter",
    "build_cbsp21_patch_packet",
    "validate_cbsp21_patch_packet",
    "canonical_packet_json",
    "compute_packet_hash",
    "RepositoryChangeProposal",
    "RepositoryChangeProposalError",
    "PROPOSAL_CONSTITUTIONAL_CLASSIFICATION",
    "build_repository_change_proposal",
    "RepositoryProposalReviewPackage",
    "RepositoryReviewPackageError",
    "build_repository_proposal_review_package",
]
