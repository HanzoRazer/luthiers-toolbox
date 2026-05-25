"""
Review Safe Fixture Package

CAM Dev Order 7V: Human-review bundle for fixture/topology cognition.

Provides:
  - ReviewSafeFixturePackage model
  - ID-only reference collection
  - Package validation

7V invariants:
  - executable_payload_present: always False
  - execution_authorized: always False
  - machine_output_allowed: always False

Core principle:
  Fixture packages are review artifacts.
  They are not machine jobs or execution plans.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator


PackageReviewStatus = Literal[
    "draft",
    "pending_review",
    "under_review",
    "approved_for_export_review",
    "approved",
    "rejected",
    "deferred",
]


class ReviewSafeFixturePackage(BaseModel):
    """
    Human-review bundle for fixture/topology cognition.

    Collects ID-only references to fixture constraints, topology evaluations,
    and compatibility assessments for human review.

    7V invariants (model-enforced):
      - executable_payload_present: always False
      - execution_authorized: always False
      - machine_output_allowed: always False
    """

    package_id: str = Field(
        default_factory=lambda: f"fix-pkg-{uuid4().hex[:12]}",
        description="Unique package identifier"
    )

    title: str = Field(
        default="",
        description="Human-readable package title"
    )
    description: str = Field(
        default="",
        description="Package description"
    )

    workspace_id: Optional[str] = Field(
        default=None,
        description="Source workspace ID"
    )
    strategy_id: Optional[str] = Field(
        default=None,
        description="Source strategy ID"
    )
    strategy_ids: List[str] = Field(
        default_factory=list,
        description="Additional strategy IDs"
    )

    geometry_authority_ref_ids: List[str] = Field(
        default_factory=list,
        description="Geometry authority reference IDs"
    )

    fixture_constraint_ids: List[str] = Field(
        default_factory=list,
        description="Fixture constraint IDs"
    )

    topology_evaluation_ids: List[str] = Field(
        default_factory=list,
        description="Topology evaluation IDs"
    )

    compatibility_evaluation_ids: List[str] = Field(
        default_factory=list,
        description="Fixture/strategy compatibility evaluation IDs"
    )

    source_fixture_ids: List[str] = Field(
        default_factory=list,
        description="Source golden fixture IDs"
    )

    replay_session_refs: List[str] = Field(
        default_factory=list,
        description="Replay session references (7W linkage)"
    )

    review_status: PackageReviewStatus = Field(
        default="draft",
        description="Current review status"
    )
    reviewer_notes: List[str] = Field(
        default_factory=list,
        description="Notes from reviewers"
    )

    blocking_issues: List[str] = Field(
        default_factory=list,
        description="Issues blocking approval"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Non-blocking warnings"
    )

    topology_risks_present: bool = Field(
        default=False,
        description="Whether topology risks are present"
    )
    fixture_conflicts_present: bool = Field(
        default=False,
        description="Whether fixture conflicts are present"
    )

    executable_payload_present: bool = Field(
        default=False,
        description="Always False — packages do not contain executable payloads"
    )
    execution_authorized: bool = Field(
        default=False,
        description="Always False — 7V does not authorize execution"
    )
    machine_output_allowed: bool = Field(
        default=False,
        description="Always False — 7V does not allow machine output"
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Last update timestamp"
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
    def enforce_7v_invariants(self) -> "ReviewSafeFixturePackage":
        """Enforce 7V invariants."""
        if self.executable_payload_present:
            raise ValueError(
                "7V invariant violation: executable_payload_present must be False — "
                "packages do not contain executable payloads"
            )
        if self.execution_authorized:
            raise ValueError(
                "7V invariant violation: execution_authorized must be False"
            )
        if self.machine_output_allowed:
            raise ValueError(
                "7V invariant violation: machine_output_allowed must be False"
            )
        return self

    def compute_hash(self) -> str:
        """Compute deterministic hash of package state."""
        hash_input = {
            "package_id": self.package_id,
            "workspace_id": self.workspace_id,
            "strategy_id": self.strategy_id,
            "strategy_ids": sorted(self.strategy_ids),
            "geometry_authority_ref_ids": sorted(self.geometry_authority_ref_ids),
            "fixture_constraint_ids": sorted(self.fixture_constraint_ids),
            "topology_evaluation_ids": sorted(self.topology_evaluation_ids),
            "compatibility_evaluation_ids": sorted(self.compatibility_evaluation_ids),
            "review_status": self.review_status,
            "blocking_issues": sorted(self.blocking_issues),
        }
        canonical = json.dumps(hash_input, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()


def create_review_safe_fixture_package(
    workspace_id: Optional[str] = None,
    strategy_id: Optional[str] = None,
    geometry_authority_ref_ids: Optional[List[str]] = None,
    fixture_constraint_ids: Optional[List[str]] = None,
    topology_evaluation_ids: Optional[List[str]] = None,
    compatibility_evaluation_ids: Optional[List[str]] = None,
    title: str = "",
    description: str = "",
) -> ReviewSafeFixturePackage:
    """
    Create a review-safe fixture package.

    Collects references without resolving objects or creating dependencies.
    """
    package = ReviewSafeFixturePackage(
        workspace_id=workspace_id,
        strategy_id=strategy_id,
        geometry_authority_ref_ids=geometry_authority_ref_ids or [],
        fixture_constraint_ids=fixture_constraint_ids or [],
        topology_evaluation_ids=topology_evaluation_ids or [],
        compatibility_evaluation_ids=compatibility_evaluation_ids or [],
        title=title,
        description=description,
    )
    package.deterministic_package_hash = package.compute_hash()
    return package


def add_fixture_constraint_to_package(
    package: ReviewSafeFixturePackage,
    constraint_id: str,
) -> ReviewSafeFixturePackage:
    """Add a fixture constraint to the package."""
    if constraint_id not in package.fixture_constraint_ids:
        package.fixture_constraint_ids.append(constraint_id)
        package.updated_at = datetime.now(timezone.utc)
        package.deterministic_package_hash = package.compute_hash()
    return package


def add_topology_evaluation_to_package(
    package: ReviewSafeFixturePackage,
    evaluation_id: str,
) -> ReviewSafeFixturePackage:
    """Add a topology evaluation to the package."""
    if evaluation_id not in package.topology_evaluation_ids:
        package.topology_evaluation_ids.append(evaluation_id)
        package.updated_at = datetime.now(timezone.utc)
        package.deterministic_package_hash = package.compute_hash()
    return package


def add_compatibility_evaluation_to_package(
    package: ReviewSafeFixturePackage,
    evaluation_id: str,
) -> ReviewSafeFixturePackage:
    """Add a compatibility evaluation to the package."""
    if evaluation_id not in package.compatibility_evaluation_ids:
        package.compatibility_evaluation_ids.append(evaluation_id)
        package.updated_at = datetime.now(timezone.utc)
        package.deterministic_package_hash = package.compute_hash()
    return package


def add_geometry_authority_ref_to_package(
    package: ReviewSafeFixturePackage,
    geometry_authority_ref_id: str,
) -> ReviewSafeFixturePackage:
    """Add a geometry authority reference to the package."""
    if geometry_authority_ref_id not in package.geometry_authority_ref_ids:
        package.geometry_authority_ref_ids.append(geometry_authority_ref_id)
        package.updated_at = datetime.now(timezone.utc)
        package.deterministic_package_hash = package.compute_hash()
    return package


def update_fixture_package_review_status(
    package: ReviewSafeFixturePackage,
    new_status: PackageReviewStatus,
    reviewer_note: Optional[str] = None,
) -> ReviewSafeFixturePackage:
    """Update the review status of the package."""
    package.review_status = new_status
    if reviewer_note:
        package.reviewer_notes.append(reviewer_note)
    package.updated_at = datetime.now(timezone.utc)
    package.deterministic_package_hash = package.compute_hash()
    return package


def add_blocking_issue_to_package(
    package: ReviewSafeFixturePackage,
    issue: str,
) -> ReviewSafeFixturePackage:
    """Add a blocking issue to the package."""
    if issue not in package.blocking_issues:
        package.blocking_issues.append(issue)
        package.updated_at = datetime.now(timezone.utc)
        package.deterministic_package_hash = package.compute_hash()
    return package


def add_warning_to_package(
    package: ReviewSafeFixturePackage,
    warning: str,
) -> ReviewSafeFixturePackage:
    """Add a warning to the package."""
    if warning not in package.warnings:
        package.warnings.append(warning)
        package.updated_at = datetime.now(timezone.utc)
        package.deterministic_package_hash = package.compute_hash()
    return package


def mark_topology_risks_present(
    package: ReviewSafeFixturePackage,
) -> ReviewSafeFixturePackage:
    """Mark that topology risks are present in the package."""
    package.topology_risks_present = True
    package.updated_at = datetime.now(timezone.utc)
    package.deterministic_package_hash = package.compute_hash()
    return package


def mark_fixture_conflicts_present(
    package: ReviewSafeFixturePackage,
) -> ReviewSafeFixturePackage:
    """Mark that fixture conflicts are present in the package."""
    package.fixture_conflicts_present = True
    package.updated_at = datetime.now(timezone.utc)
    package.deterministic_package_hash = package.compute_hash()
    return package


def validate_review_safe_fixture_package(
    package: ReviewSafeFixturePackage,
) -> tuple[bool, List[str]]:
    """
    Validate that a fixture package is ready for review.

    Returns:
        (is_valid, issues)
    """
    issues: List[str] = []

    if package.executable_payload_present:
        issues.append("executable_payload_present must be False")

    if package.execution_authorized:
        issues.append("execution_authorized must be False")

    if package.machine_output_allowed:
        issues.append("machine_output_allowed must be False")

    if not package.workspace_id and not package.strategy_id:
        issues.append("Package must reference a workspace or strategy")

    if not package.fixture_constraint_ids and not package.topology_evaluation_ids:
        issues.append("Package has no fixture constraints or topology evaluations")

    if package.blocking_issues and package.review_status == "approved":
        issues.append("Package has blocking issues but is marked approved")

    return len(issues) == 0, issues


def is_fixture_package_approved(package: ReviewSafeFixturePackage) -> bool:
    """Check if fixture package is approved."""
    return (
        package.review_status in ("approved", "approved_for_export_review") and
        not package.blocking_issues
    )


def build_fixture_package_hash(package: ReviewSafeFixturePackage) -> str:
    """Build deterministic hash for a fixture package."""
    return package.compute_hash()
