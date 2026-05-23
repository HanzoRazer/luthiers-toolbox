"""
Release Readiness Evaluation

CAM Dev Order 7Z: Release readiness evaluation for governance freezes.

Provides:
  - ReleaseReadinessEvaluation model
  - Readiness classification (ready/not_ready/blocked)
  - Evaluation criteria assessment

7Z invariants:
  - human_review_required: always True
  - auto_release_authorized: always False
  - release_authorized: always False
  - execution_authorized: always False
  - machine_output_allowed: always False

Core principle:
  Readiness evaluations assess whether a freeze is ready for review.
  They do not authorize release or execution.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional, Tuple
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator

from .governance_baseline_freeze import GovernanceBaselineFreeze
from .federation_ci_registry import get_latest_federation_ci_summary


ReleaseReadinessStatus = Literal["ready", "not_ready", "blocked"]


class ReleaseReadinessEvaluation(BaseModel):
    """
    Release readiness evaluation for a governance freeze.

    Assesses whether a freeze meets readiness criteria.

    7Z invariants (model-enforced):
      - human_review_required: always True
      - auto_release_authorized: always False
      - release_authorized: always False
      - execution_authorized: always False
      - machine_output_allowed: always False
    """

    evaluation_id: str = Field(
        default_factory=lambda: f"rre-{uuid4().hex[:12]}",
        description="Unique evaluation identifier"
    )

    freeze_id: str = Field(
        ...,
        description="Freeze ID being evaluated"
    )

    readiness_status: ReleaseReadinessStatus = Field(
        default="not_ready",
        description="Readiness status"
    )

    ci_passed: bool = Field(
        default=False,
        description="Whether CI passed at evaluation time"
    )
    no_blocking_issues: bool = Field(
        default=False,
        description="Whether there are no blocking issues"
    )
    warnings_within_threshold: bool = Field(
        default=True,
        description="Whether warnings are within acceptable threshold"
    )
    baseline_aligned: bool = Field(
        default=False,
        description="Whether aligned with baseline expectations"
    )
    human_review_completed: bool = Field(
        default=False,
        description="Whether human review has been completed"
    )

    blocking_reasons: List[str] = Field(
        default_factory=list,
        description="Reasons preventing readiness"
    )
    recommendations: List[str] = Field(
        default_factory=list,
        description="Recommendations for achieving readiness"
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

    evaluated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Evaluation timestamp"
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )

    deterministic_evaluation_hash: str = Field(
        default="",
        description="Deterministic hash of evaluation state"
    )

    @model_validator(mode="after")
    def enforce_7z_invariants(self) -> "ReleaseReadinessEvaluation":
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
        """Compute deterministic hash of evaluation state."""
        hash_input = {
            "freeze_id": self.freeze_id,
            "readiness_status": self.readiness_status,
            "ci_passed": self.ci_passed,
            "no_blocking_issues": self.no_blocking_issues,
            "warnings_within_threshold": self.warnings_within_threshold,
            "baseline_aligned": self.baseline_aligned,
            "human_review_completed": self.human_review_completed,
            "blocking_reasons": sorted(self.blocking_reasons),
            "recommendations": sorted(self.recommendations),
        }
        canonical = json.dumps(hash_input, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()


def classify_readiness_status(
    ci_passed: bool,
    no_blocking_issues: bool,
    warnings_within_threshold: bool,
    baseline_aligned: bool,
    human_review_completed: bool,
) -> ReleaseReadinessStatus:
    """
    Classify release readiness status.

    BLOCKED: Any blocking issues or CI failure
    NOT_READY: Missing human review or baseline alignment
    READY: All criteria met
    """
    if not ci_passed:
        return "blocked"
    if not no_blocking_issues:
        return "blocked"
    if not warnings_within_threshold:
        return "not_ready"
    if not baseline_aligned:
        return "not_ready"
    if not human_review_completed:
        return "not_ready"

    return "ready"


def evaluate_freeze_readiness(
    freeze: GovernanceBaselineFreeze,
    warning_threshold: int = 0,
) -> ReleaseReadinessEvaluation:
    """
    Evaluate release readiness for a governance freeze.

    Assesses:
      - CI status at freeze time
      - Blocking issues
      - Warning count vs threshold
      - Baseline alignment
      - Human review status
    """
    blocking_reasons: List[str] = []
    recommendations: List[str] = []

    # Check CI status
    ci_passed = freeze.ci_status_at_freeze == "pass"
    if not ci_passed:
        if freeze.ci_status_at_freeze == "fail":
            blocking_reasons.append("CI status is FAIL")
        elif freeze.ci_status_at_freeze == "warn":
            recommendations.append("CI status is WARN — review warnings")
        else:
            recommendations.append("CI status unknown — run evaluation")

    # Check blocking issues
    no_blocking_issues = freeze.blocking_issue_count == 0
    if not no_blocking_issues:
        blocking_reasons.append(f"{freeze.blocking_issue_count} blocking issue(s)")

    # Check warnings
    warnings_within_threshold = freeze.warning_count <= warning_threshold
    if not warnings_within_threshold:
        recommendations.append(
            f"{freeze.warning_count} warning(s) exceeds threshold of {warning_threshold}"
        )

    # Check baseline alignment
    baseline_aligned = freeze.baseline_id is not None
    if not baseline_aligned:
        recommendations.append("No baseline specified — consider setting baseline")

    # Human review status (from freeze status)
    human_review_completed = freeze.status in ("reviewed", "approved")
    if not human_review_completed:
        recommendations.append("Human review not completed")

    # Classify status
    readiness_status = classify_readiness_status(
        ci_passed=ci_passed,
        no_blocking_issues=no_blocking_issues,
        warnings_within_threshold=warnings_within_threshold,
        baseline_aligned=baseline_aligned,
        human_review_completed=human_review_completed,
    )

    evaluation = ReleaseReadinessEvaluation(
        freeze_id=freeze.freeze_id,
        readiness_status=readiness_status,
        ci_passed=ci_passed,
        no_blocking_issues=no_blocking_issues,
        warnings_within_threshold=warnings_within_threshold,
        baseline_aligned=baseline_aligned,
        human_review_completed=human_review_completed,
        blocking_reasons=blocking_reasons,
        recommendations=recommendations,
    )
    evaluation.deterministic_evaluation_hash = evaluation.compute_hash()
    return evaluation


def build_readiness_evaluation_from_ci(
    freeze: GovernanceBaselineFreeze,
    warning_threshold: int = 0,
) -> ReleaseReadinessEvaluation:
    """
    Build readiness evaluation using latest CI summary.

    Gets current CI state and evaluates freeze readiness.
    """
    latest_summary = get_latest_federation_ci_summary()

    if latest_summary:
        # Update freeze with latest CI info (for evaluation only, not mutating)
        ci_status = latest_summary.status
        blocking_count = latest_summary.blocking_issue_count
        warning_count = latest_summary.warning_count
    else:
        ci_status = freeze.ci_status_at_freeze
        blocking_count = freeze.blocking_issue_count
        warning_count = freeze.warning_count

    blocking_reasons: List[str] = []
    recommendations: List[str] = []

    ci_passed = ci_status == "pass"
    if not ci_passed:
        if ci_status == "fail":
            blocking_reasons.append("CI status is FAIL")
        elif ci_status == "warn":
            recommendations.append("CI status is WARN — review warnings")

    no_blocking_issues = blocking_count == 0
    if not no_blocking_issues:
        blocking_reasons.append(f"{blocking_count} blocking issue(s)")

    warnings_within_threshold = warning_count <= warning_threshold
    if not warnings_within_threshold:
        recommendations.append(
            f"{warning_count} warning(s) exceeds threshold of {warning_threshold}"
        )

    baseline_aligned = freeze.baseline_id is not None
    if not baseline_aligned:
        recommendations.append("No baseline specified")

    human_review_completed = freeze.status in ("reviewed", "approved")
    if not human_review_completed:
        recommendations.append("Human review not completed")

    readiness_status = classify_readiness_status(
        ci_passed=ci_passed,
        no_blocking_issues=no_blocking_issues,
        warnings_within_threshold=warnings_within_threshold,
        baseline_aligned=baseline_aligned,
        human_review_completed=human_review_completed,
    )

    evaluation = ReleaseReadinessEvaluation(
        freeze_id=freeze.freeze_id,
        readiness_status=readiness_status,
        ci_passed=ci_passed,
        no_blocking_issues=no_blocking_issues,
        warnings_within_threshold=warnings_within_threshold,
        baseline_aligned=baseline_aligned,
        human_review_completed=human_review_completed,
        blocking_reasons=blocking_reasons,
        recommendations=recommendations,
    )
    evaluation.deterministic_evaluation_hash = evaluation.compute_hash()
    return evaluation


def get_readiness_status_message(evaluation: ReleaseReadinessEvaluation) -> str:
    """Get human-readable status message for evaluation."""
    if evaluation.readiness_status == "ready":
        return "Release readiness: READY for human review"
    elif evaluation.readiness_status == "blocked":
        reasons = "; ".join(evaluation.blocking_reasons) or "see blocking reasons"
        return f"Release readiness: BLOCKED — {reasons}"
    else:
        recs = "; ".join(evaluation.recommendations[:2]) or "see recommendations"
        return f"Release readiness: NOT READY — {recs}"


def get_evaluation_summary_dict(
    evaluation: ReleaseReadinessEvaluation,
) -> Dict[str, Any]:
    """Get evaluation as dictionary for API response."""
    return {
        "evaluation_id": evaluation.evaluation_id,
        "freeze_id": evaluation.freeze_id,
        "readiness_status": evaluation.readiness_status,
        "ci_passed": evaluation.ci_passed,
        "no_blocking_issues": evaluation.no_blocking_issues,
        "warnings_within_threshold": evaluation.warnings_within_threshold,
        "baseline_aligned": evaluation.baseline_aligned,
        "human_review_completed": evaluation.human_review_completed,
        "blocking_reasons": evaluation.blocking_reasons,
        "recommendations": evaluation.recommendations,
        "status_message": get_readiness_status_message(evaluation),
        "human_review_required": evaluation.human_review_required,
        "release_authorized": evaluation.release_authorized,
    }
