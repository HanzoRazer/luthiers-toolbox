"""
Federated Review Package

CAM Dev Order 7X: Review-safe cross-domain cognition bundle.

Provides:
  - FederatedReviewPackage model
  - Cross-domain review bundling
  - Package validation
  - Hash computation

7X invariants:
  - immutable: always True
  - execution_authorized: always False
  - machine_output_allowed: always False

Core principle:
  Review packages preserve cross-domain cognition.
  They do not authorize execution or mutate ontologies.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator

from .federated_semantic_reference import FederatedDomainType


class FederatedReviewPackage(BaseModel):
    """
    Review-safe cross-domain cognition bundle.

    Bundles federation references, continuity records, and replay packages
    for immutable cross-domain review.

    7X invariants (model-enforced):
      - immutable: always True
      - execution_authorized: always False
      - machine_output_allowed: always False
    """

    package_id: str = Field(
        default_factory=lambda: f"frp-{uuid4().hex[:12]}",
        description="Unique package identifier"
    )

    participating_domains: List[FederatedDomainType] = Field(
        default_factory=list,
        description="Domains participating in this package"
    )

    federation_ref_ids: List[str] = Field(
        default_factory=list,
        description="Federation reference IDs included in package"
    )

    continuity_record_ids: List[str] = Field(
        default_factory=list,
        description="Continuity record IDs included in package"
    )

    replay_package_refs: List[str] = Field(
        default_factory=list,
        description="Replay package reference IDs"
    )

    provenance_refs: List[str] = Field(
        default_factory=list,
        description="Provenance reference chain"
    )

    review_summary: str = Field(
        default="",
        description="Human-readable review summary"
    )

    warnings: List[str] = Field(
        default_factory=list,
        description="Non-blocking warnings"
    )
    blocking_issues: List[str] = Field(
        default_factory=list,
        description="Issues blocking package validity"
    )

    immutable: bool = Field(
        default=True,
        description="Always True — federated packages are immutable"
    )

    execution_authorized: bool = Field(
        default=False,
        description="Always False — 7X does not authorize execution"
    )
    machine_output_allowed: bool = Field(
        default=False,
        description="Always False — 7X does not allow machine output"
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp"
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )

    deterministic_package_hash: str = Field(
        default="",
        description="Deterministic hash of package state"
    )

    @model_validator(mode="after")
    def enforce_7x_invariants(self) -> "FederatedReviewPackage":
        """Enforce 7X invariants."""
        if not self.immutable:
            raise ValueError(
                "7X invariant violation: immutable must be True — "
                "federated packages are immutable"
            )
        if self.execution_authorized:
            raise ValueError(
                "7X invariant violation: execution_authorized must be False — "
                "7X does not authorize execution"
            )
        if self.machine_output_allowed:
            raise ValueError(
                "7X invariant violation: machine_output_allowed must be False — "
                "7X does not allow machine output"
            )
        return self

    def compute_hash(self) -> str:
        """Compute deterministic hash of package state."""
        hash_input = {
            "participating_domains": sorted(self.participating_domains),
            "federation_ref_ids": sorted(self.federation_ref_ids),
            "continuity_record_ids": sorted(self.continuity_record_ids),
            "replay_package_refs": sorted(self.replay_package_refs),
            "provenance_refs": sorted(self.provenance_refs),
            "review_summary": self.review_summary,
            "warnings": sorted(self.warnings),
            "blocking_issues": sorted(self.blocking_issues),
        }
        canonical = json.dumps(hash_input, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()


def create_federated_review_package(
    participating_domains: List[FederatedDomainType],
    federation_ref_ids: List[str] | None = None,
    continuity_record_ids: List[str] | None = None,
    replay_package_refs: List[str] | None = None,
    provenance_refs: List[str] | None = None,
    review_summary: str = "",
) -> FederatedReviewPackage:
    """
    Create a federated review package.

    Bundles federation state for immutable cross-domain review.
    """
    package = FederatedReviewPackage(
        participating_domains=participating_domains,
        federation_ref_ids=federation_ref_ids or [],
        continuity_record_ids=continuity_record_ids or [],
        replay_package_refs=replay_package_refs or [],
        provenance_refs=provenance_refs or [],
        review_summary=review_summary,
    )

    # Warn if no federation refs or continuity records
    if not package.federation_ref_ids and not package.continuity_record_ids:
        package.warnings.append(
            "Package has no federation refs or continuity records"
        )

    package.deterministic_package_hash = package.compute_hash()
    return package


def validate_federated_review_package(
    package: FederatedReviewPackage,
) -> Tuple[bool, List[str]]:
    """
    Validate that a federated review package is well-formed.

    Returns:
        (is_valid, issues)
    """
    issues: List[str] = []

    if not package.immutable:
        issues.append("immutable must be True")

    if package.execution_authorized:
        issues.append("execution_authorized must be False")

    if package.machine_output_allowed:
        issues.append("machine_output_allowed must be False")

    if not package.participating_domains:
        issues.append("No participating domains specified")

    if not package.federation_ref_ids and not package.continuity_record_ids:
        issues.append("Package has no federation refs or continuity records")

    if package.blocking_issues:
        issues.append(f"Package has {len(package.blocking_issues)} blocking issues")

    return len(issues) == 0, issues


def is_package_valid_for_review(package: FederatedReviewPackage) -> bool:
    """Check if package is valid for review."""
    is_valid, _ = validate_federated_review_package(package)
    return is_valid


def build_federated_package_hash(package: FederatedReviewPackage) -> str:
    """Build deterministic hash for a federated package."""
    return package.compute_hash()


def add_federation_ref(
    package: FederatedReviewPackage,
    federation_ref_id: str,
) -> FederatedReviewPackage:
    """Add a federation reference to the package."""
    if federation_ref_id not in package.federation_ref_ids:
        package.federation_ref_ids.append(federation_ref_id)
        package.deterministic_package_hash = package.compute_hash()
    return package


def add_continuity_record(
    package: FederatedReviewPackage,
    continuity_record_id: str,
) -> FederatedReviewPackage:
    """Add a continuity record to the package."""
    if continuity_record_id not in package.continuity_record_ids:
        package.continuity_record_ids.append(continuity_record_id)
        package.deterministic_package_hash = package.compute_hash()
    return package


def add_replay_package_ref(
    package: FederatedReviewPackage,
    replay_package_ref: str,
) -> FederatedReviewPackage:
    """Add a replay package reference."""
    if replay_package_ref not in package.replay_package_refs:
        package.replay_package_refs.append(replay_package_ref)
        package.deterministic_package_hash = package.compute_hash()
    return package


def add_provenance_ref(
    package: FederatedReviewPackage,
    provenance_ref: str,
) -> FederatedReviewPackage:
    """Add a provenance reference."""
    if provenance_ref not in package.provenance_refs:
        package.provenance_refs.append(provenance_ref)
        package.deterministic_package_hash = package.compute_hash()
    return package


def add_participating_domain(
    package: FederatedReviewPackage,
    domain: FederatedDomainType,
) -> FederatedReviewPackage:
    """Add a participating domain."""
    if domain not in package.participating_domains:
        package.participating_domains.append(domain)
        package.deterministic_package_hash = package.compute_hash()
    return package


def add_warning(
    package: FederatedReviewPackage,
    warning: str,
) -> FederatedReviewPackage:
    """Add a warning to the package."""
    if warning not in package.warnings:
        package.warnings.append(warning)
        package.deterministic_package_hash = package.compute_hash()
    return package


def add_blocking_issue(
    package: FederatedReviewPackage,
    issue: str,
) -> FederatedReviewPackage:
    """Add a blocking issue to the package."""
    if issue not in package.blocking_issues:
        package.blocking_issues.append(issue)
        package.deterministic_package_hash = package.compute_hash()
    return package


def update_review_summary(
    package: FederatedReviewPackage,
    review_summary: str,
) -> FederatedReviewPackage:
    """Update the review summary."""
    package.review_summary = review_summary
    package.deterministic_package_hash = package.compute_hash()
    return package


def get_package_summary(package: FederatedReviewPackage) -> Dict[str, Any]:
    """Get a summary of the federated review package."""
    return {
        "package_id": package.package_id,
        "participating_domain_count": len(package.participating_domains),
        "participating_domains": package.participating_domains,
        "federation_ref_count": len(package.federation_ref_ids),
        "continuity_record_count": len(package.continuity_record_ids),
        "replay_package_ref_count": len(package.replay_package_refs),
        "provenance_ref_count": len(package.provenance_refs),
        "immutable": package.immutable,
        "warning_count": len(package.warnings),
        "blocking_issue_count": len(package.blocking_issues),
    }
