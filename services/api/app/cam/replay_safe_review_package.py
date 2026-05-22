"""
Replay Safe Review Package

CAM Dev Order 7W: Immutable observational replay package.

Provides:
  - ReplaySafeReviewPackage model
  - Review-safe cognition continuity bundle
  - Package validation
  - Hash computation

7W invariants:
  - immutable: always True
  - execution_authorized: always False
  - machine_output_allowed: always False
  - replay_execution_present: always False

Core principle:
  Replay packages preserve review continuity.
  They do not authorize execution or replay machine behavior.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator


ReplayContinuityState = Literal[
    "complete",
    "partial",
    "fragmented",
    "invalid",
]


class ReplaySafeReviewPackage(BaseModel):
    """
    Immutable observational replay package.

    Bundles replay session, observations, and timeline
    for review-safe cognition continuity.

    7W invariants (model-enforced):
      - immutable: always True
      - execution_authorized: always False
      - machine_output_allowed: always False
      - replay_execution_present: always False
    """

    package_id: str = Field(
        default_factory=lambda: f"rsrp-{uuid4().hex[:12]}",
        description="Unique package identifier"
    )

    replay_session_id: str = Field(
        ...,
        description="Source replay session ID"
    )

    observation_ids: List[str] = Field(
        default_factory=list,
        description="Observation IDs included in package"
    )

    timeline_id: Optional[str] = Field(
        default=None,
        description="Associated timeline ID"
    )

    provenance_refs: List[str] = Field(
        default_factory=list,
        description="Provenance reference chain"
    )

    # 7X: Optional cross-domain continuity linkage
    cross_domain_continuity_refs: List[str] = Field(
        default_factory=list,
        description="Linked cross-domain continuity record IDs (7X)"
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
        description="Issues blocking package approval"
    )

    continuity_state: ReplayContinuityState = Field(
        default="partial",
        description="Package continuity state"
    )

    immutable: bool = Field(
        default=True,
        description="Always True — replay packages are immutable"
    )

    execution_authorized: bool = Field(
        default=False,
        description="Always False — 7W does not authorize execution"
    )
    machine_output_allowed: bool = Field(
        default=False,
        description="Always False — 7W does not allow machine output"
    )
    replay_execution_present: bool = Field(
        default=False,
        description="Always False — 7W does not replay execution"
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
    def enforce_7w_invariants(self) -> "ReplaySafeReviewPackage":
        """Enforce 7W invariants."""
        if not self.immutable:
            raise ValueError(
                "7W invariant violation: immutable must be True — "
                "replay packages are immutable"
            )
        if self.execution_authorized:
            raise ValueError(
                "7W invariant violation: execution_authorized must be False"
            )
        if self.machine_output_allowed:
            raise ValueError(
                "7W invariant violation: machine_output_allowed must be False"
            )
        if self.replay_execution_present:
            raise ValueError(
                "7W invariant violation: replay_execution_present must be False"
            )
        return self

    def compute_hash(self) -> str:
        """Compute deterministic hash of package state."""
        hash_input = {
            "package_id": self.package_id,
            "replay_session_id": self.replay_session_id,
            "observation_ids": sorted(self.observation_ids),
            "timeline_id": self.timeline_id,
            "provenance_refs": sorted(self.provenance_refs),
            "review_summary": self.review_summary,
            "warnings": sorted(self.warnings),
            "blocking_issues": sorted(self.blocking_issues),
            "continuity_state": self.continuity_state,
        }
        canonical = json.dumps(hash_input, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()


def create_replay_safe_review_package(
    replay_session_id: str,
    observation_ids: Optional[List[str]] = None,
    timeline_id: Optional[str] = None,
    provenance_refs: Optional[List[str]] = None,
    review_summary: str = "",
) -> ReplaySafeReviewPackage:
    """
    Create a replay-safe review package.

    Bundles replay session references for immutable review continuity.
    """
    package = ReplaySafeReviewPackage(
        replay_session_id=replay_session_id,
        observation_ids=observation_ids or [],
        timeline_id=timeline_id,
        provenance_refs=provenance_refs or [],
        review_summary=review_summary,
    )
    package.deterministic_package_hash = package.compute_hash()
    return package


def add_observation_to_package(
    package: ReplaySafeReviewPackage,
    observation_id: str,
) -> ReplaySafeReviewPackage:
    """Add an observation to the package."""
    if observation_id not in package.observation_ids:
        package.observation_ids.append(observation_id)
        package.deterministic_package_hash = package.compute_hash()
    return package


def add_provenance_ref_to_package(
    package: ReplaySafeReviewPackage,
    provenance_ref: str,
) -> ReplaySafeReviewPackage:
    """Add a provenance reference to the package."""
    if provenance_ref not in package.provenance_refs:
        package.provenance_refs.append(provenance_ref)
        package.deterministic_package_hash = package.compute_hash()
    return package


def add_warning_to_package(
    package: ReplaySafeReviewPackage,
    warning: str,
) -> ReplaySafeReviewPackage:
    """Add a warning to the package."""
    if warning not in package.warnings:
        package.warnings.append(warning)
        package.deterministic_package_hash = package.compute_hash()
    return package


def add_blocking_issue_to_package(
    package: ReplaySafeReviewPackage,
    issue: str,
) -> ReplaySafeReviewPackage:
    """Add a blocking issue to the package."""
    if issue not in package.blocking_issues:
        package.blocking_issues.append(issue)
        package.deterministic_package_hash = package.compute_hash()
    return package


def set_timeline_for_package(
    package: ReplaySafeReviewPackage,
    timeline_id: str,
) -> ReplaySafeReviewPackage:
    """Set the timeline for the package."""
    package.timeline_id = timeline_id
    package.deterministic_package_hash = package.compute_hash()
    return package


def update_review_summary(
    package: ReplaySafeReviewPackage,
    review_summary: str,
) -> ReplaySafeReviewPackage:
    """Update the review summary."""
    package.review_summary = review_summary
    package.deterministic_package_hash = package.compute_hash()
    return package


def update_continuity_state(
    package: ReplaySafeReviewPackage,
    new_state: ReplayContinuityState,
) -> ReplaySafeReviewPackage:
    """Update the package continuity state."""
    package.continuity_state = new_state
    package.deterministic_package_hash = package.compute_hash()
    return package


def validate_replay_safe_review_package(
    package: ReplaySafeReviewPackage,
) -> tuple[bool, List[str]]:
    """
    Validate that a replay package is well-formed.

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

    if package.replay_execution_present:
        issues.append("replay_execution_present must be False")

    if not package.replay_session_id:
        issues.append("Package must reference a replay session")

    if not package.observation_ids:
        issues.append("Package has no observations")

    if package.blocking_issues and package.continuity_state == "complete":
        issues.append("Package has blocking issues but is marked complete")

    return len(issues) == 0, issues


def is_package_complete(package: ReplaySafeReviewPackage) -> bool:
    """Check if package is complete."""
    return (
        package.continuity_state == "complete" and
        not package.blocking_issues and
        len(package.observation_ids) > 0
    )


def is_package_valid_for_review(package: ReplaySafeReviewPackage) -> bool:
    """Check if package is valid for review."""
    is_valid, _ = validate_replay_safe_review_package(package)
    return is_valid


def build_replay_package_hash(package: ReplaySafeReviewPackage) -> str:
    """Build deterministic hash for a replay package."""
    return package.compute_hash()


def get_package_summary(package: ReplaySafeReviewPackage) -> Dict[str, Any]:
    """Get a summary of the package."""
    return {
        "package_id": package.package_id,
        "replay_session_id": package.replay_session_id,
        "observation_count": len(package.observation_ids),
        "has_timeline": package.timeline_id is not None,
        "provenance_ref_count": len(package.provenance_refs),
        "warning_count": len(package.warnings),
        "blocking_issue_count": len(package.blocking_issues),
        "continuity_state": package.continuity_state,
        "immutable": package.immutable,
    }
