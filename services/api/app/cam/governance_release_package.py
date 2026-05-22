"""
Governance Release Package

CAM Dev Order 7Z: Release packages bundling freeze and evaluation.

Provides:
  - GovernanceReleasePackage model
  - Package creation from freeze and evaluation
  - Hash computation for integrity

7Z invariants:
  - human_review_required: always True
  - auto_release_authorized: always False
  - release_authorized: always False
  - execution_authorized: always False
  - machine_output_allowed: always False

Core principle:
  Release packages bundle freeze and evaluation for human review.
  They do not authorize release or execution.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator

from .governance_baseline_freeze import GovernanceBaselineFreeze
from .release_readiness_evaluation import ReleaseReadinessEvaluation


class GovernanceReleasePackage(BaseModel):
    """
    Governance release package bundling freeze and evaluation.

    Provides complete context for human review.

    7Z invariants (model-enforced):
      - human_review_required: always True
      - auto_release_authorized: always False
      - release_authorized: always False
      - execution_authorized: always False
      - machine_output_allowed: always False
    """

    package_id: str = Field(
        default_factory=lambda: f"grp-{uuid4().hex[:12]}",
        description="Unique package identifier"
    )

    package_name: str = Field(
        ...,
        description="Human-readable package name"
    )

    freeze_id: str = Field(
        ...,
        description="Freeze ID included in package"
    )

    evaluation_id: Optional[str] = Field(
        default=None,
        description="Evaluation ID included in package"
    )

    readiness_status: str = Field(
        default="not_ready",
        description="Readiness status from evaluation"
    )

    baseline_id: Optional[str] = Field(
        default=None,
        description="Baseline ID from freeze"
    )

    ci_summary_id: Optional[str] = Field(
        default=None,
        description="CI summary ID from freeze"
    )

    ci_status: Optional[str] = Field(
        default=None,
        description="CI status (pass/warn/fail)"
    )

    blocking_issue_count: int = Field(
        default=0,
        description="Blocking issues"
    )
    warning_count: int = Field(
        default=0,
        description="Warnings"
    )

    blocking_reasons: List[str] = Field(
        default_factory=list,
        description="Blocking reasons from evaluation"
    )
    recommendations: List[str] = Field(
        default_factory=list,
        description="Recommendations from evaluation"
    )

    review_notes: List[str] = Field(
        default_factory=list,
        description="Notes for reviewers"
    )

    human_review_required: bool = Field(
        default=True,
        description="Always True — 7Z requires human review"
    )
    auto_release_authorized: bool = Field(
        default=False,
        description="Always False — 7Z does not authorize auto-release"
    )
    release_authorized: bool = Field(
        default=False,
        description="Always False — 7Z does not authorize release"
    )
    execution_authorized: bool = Field(
        default=False,
        description="Always False — 7Z does not authorize execution"
    )
    machine_output_allowed: bool = Field(
        default=False,
        description="Always False — 7Z does not allow machine output"
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Package creation timestamp"
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
    def enforce_7z_invariants(self) -> "GovernanceReleasePackage":
        """Enforce 7Z invariants."""
        if not self.human_review_required:
            raise ValueError(
                "7Z invariant violation: human_review_required must be True — "
                "7Z always requires human review"
            )
        if self.auto_release_authorized:
            raise ValueError(
                "7Z invariant violation: auto_release_authorized must be False — "
                "7Z does not authorize auto-release"
            )
        if self.release_authorized:
            raise ValueError(
                "7Z invariant violation: release_authorized must be False — "
                "7Z does not authorize release"
            )
        if self.execution_authorized:
            raise ValueError(
                "7Z invariant violation: execution_authorized must be False — "
                "7Z does not authorize execution"
            )
        if self.machine_output_allowed:
            raise ValueError(
                "7Z invariant violation: machine_output_allowed must be False — "
                "7Z does not allow machine output"
            )
        return self

    def compute_hash(self) -> str:
        """Compute deterministic hash of package state."""
        hash_input = {
            "package_name": self.package_name,
            "freeze_id": self.freeze_id,
            "evaluation_id": self.evaluation_id,
            "readiness_status": self.readiness_status,
            "baseline_id": self.baseline_id,
            "ci_summary_id": self.ci_summary_id,
            "ci_status": self.ci_status,
            "blocking_issue_count": self.blocking_issue_count,
            "warning_count": self.warning_count,
            "blocking_reasons": sorted(self.blocking_reasons),
            "recommendations": sorted(self.recommendations),
        }
        canonical = json.dumps(hash_input, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()


def create_governance_release_package(
    package_name: str,
    freeze: GovernanceBaselineFreeze,
    evaluation: Optional[ReleaseReadinessEvaluation] = None,
) -> GovernanceReleasePackage:
    """
    Create a governance release package from freeze and evaluation.

    Bundles freeze and evaluation for human review.
    """
    package = GovernanceReleasePackage(
        package_name=package_name,
        freeze_id=freeze.freeze_id,
        evaluation_id=evaluation.evaluation_id if evaluation else None,
        readiness_status=evaluation.readiness_status if evaluation else "not_ready",
        baseline_id=freeze.baseline_id,
        ci_summary_id=freeze.ci_summary_id,
        ci_status=freeze.ci_status_at_freeze,
        blocking_issue_count=freeze.blocking_issue_count,
        warning_count=freeze.warning_count,
        blocking_reasons=evaluation.blocking_reasons if evaluation else [],
        recommendations=evaluation.recommendations if evaluation else [],
    )
    package.deterministic_package_hash = package.compute_hash()
    return package


def build_package_from_freeze(
    package_name: str,
    freeze: GovernanceBaselineFreeze,
) -> GovernanceReleasePackage:
    """
    Build a release package from freeze only (no evaluation).

    Used when evaluation hasn't been run yet.
    """
    return create_governance_release_package(
        package_name=package_name,
        freeze=freeze,
        evaluation=None,
    )


def get_package_summary(package: GovernanceReleasePackage) -> Dict[str, Any]:
    """Get a summary of the package."""
    return {
        "package_id": package.package_id,
        "package_name": package.package_name,
        "freeze_id": package.freeze_id,
        "evaluation_id": package.evaluation_id,
        "readiness_status": package.readiness_status,
        "baseline_id": package.baseline_id,
        "ci_status": package.ci_status,
        "blocking_issue_count": package.blocking_issue_count,
        "warning_count": package.warning_count,
        "human_review_required": package.human_review_required,
        "release_authorized": package.release_authorized,
    }


def get_package_review_context(package: GovernanceReleasePackage) -> Dict[str, Any]:
    """Get full review context for a package."""
    return {
        "package_id": package.package_id,
        "package_name": package.package_name,
        "freeze_id": package.freeze_id,
        "evaluation_id": package.evaluation_id,
        "readiness_status": package.readiness_status,
        "baseline_id": package.baseline_id,
        "ci_summary_id": package.ci_summary_id,
        "ci_status": package.ci_status,
        "blocking_issue_count": package.blocking_issue_count,
        "warning_count": package.warning_count,
        "blocking_reasons": package.blocking_reasons,
        "recommendations": package.recommendations,
        "review_notes": package.review_notes,
        "human_review_required": package.human_review_required,
        "auto_release_authorized": package.auto_release_authorized,
        "release_authorized": package.release_authorized,
        "execution_authorized": package.execution_authorized,
        "machine_output_allowed": package.machine_output_allowed,
        "created_at": package.created_at.isoformat(),
        "deterministic_package_hash": package.deterministic_package_hash,
    }
