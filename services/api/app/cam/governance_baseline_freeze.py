"""
Governance Baseline Freeze

CAM Dev Order 7Z: Governance baseline freeze for release readiness.

Provides:
  - GovernanceBaselineFreeze model
  - Freeze state management
  - Hash computation for integrity

7Z invariants:
  - human_review_required: always True
  - auto_release_authorized: always False
  - release_authorized: always False
  - execution_authorized: always False
  - machine_output_allowed: always False

Core principle:
  Governance freezes capture point-in-time governance state for review.
  They do not authorize release or execution.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional, Tuple
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator


GovernanceFreezeStatus = Literal["pending", "reviewed", "approved", "rejected"]


class GovernanceBaselineFreeze(BaseModel):
    """
    Governance baseline freeze for release readiness evaluation.

    Captures point-in-time governance state for human review.

    7Z invariants (model-enforced):
      - human_review_required: always True
      - auto_release_authorized: always False
      - release_authorized: always False
      - execution_authorized: always False
      - machine_output_allowed: always False
    """

    freeze_id: str = Field(
        default_factory=lambda: f"gbf-{uuid4().hex[:12]}",
        description="Unique freeze identifier"
    )

    freeze_name: str = Field(
        ...,
        description="Human-readable freeze name"
    )

    baseline_id: Optional[str] = Field(
        default=None,
        description="7Y baseline ID used for this freeze"
    )

    ci_summary_id: Optional[str] = Field(
        default=None,
        description="7Y CI summary ID at freeze time"
    )

    ci_status_at_freeze: Optional[str] = Field(
        default=None,
        description="CI status at freeze time (pass/warn/fail)"
    )

    federation_ref_count_at_freeze: int = Field(
        default=0,
        description="Federation ref count at freeze time"
    )
    continuity_record_count_at_freeze: int = Field(
        default=0,
        description="Continuity record count at freeze time"
    )
    package_count_at_freeze: int = Field(
        default=0,
        description="Federated package count at freeze time"
    )

    blocking_issue_count: int = Field(
        default=0,
        description="Blocking issues at freeze time"
    )
    warning_count: int = Field(
        default=0,
        description="Warnings at freeze time"
    )

    status: GovernanceFreezeStatus = Field(
        default="pending",
        description="Current freeze status"
    )

    reviewer_notes: List[str] = Field(
        default_factory=list,
        description="Notes from human reviewers"
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
        description="Freeze creation timestamp"
    )

    reviewed_at: Optional[datetime] = Field(
        default=None,
        description="Review timestamp"
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )

    deterministic_freeze_hash: str = Field(
        default="",
        description="Deterministic hash of freeze state"
    )

    @model_validator(mode="after")
    def enforce_7z_invariants(self) -> "GovernanceBaselineFreeze":
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
        """Compute deterministic hash of freeze state."""
        hash_input = {
            "freeze_name": self.freeze_name,
            "baseline_id": self.baseline_id,
            "ci_summary_id": self.ci_summary_id,
            "ci_status_at_freeze": self.ci_status_at_freeze,
            "federation_ref_count_at_freeze": self.federation_ref_count_at_freeze,
            "continuity_record_count_at_freeze": self.continuity_record_count_at_freeze,
            "package_count_at_freeze": self.package_count_at_freeze,
            "blocking_issue_count": self.blocking_issue_count,
            "warning_count": self.warning_count,
            "status": self.status,
        }
        canonical = json.dumps(hash_input, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()


def create_governance_baseline_freeze(
    freeze_name: str,
    baseline_id: Optional[str] = None,
    ci_summary_id: Optional[str] = None,
    ci_status_at_freeze: Optional[str] = None,
    federation_ref_count_at_freeze: int = 0,
    continuity_record_count_at_freeze: int = 0,
    package_count_at_freeze: int = 0,
    blocking_issue_count: int = 0,
    warning_count: int = 0,
) -> GovernanceBaselineFreeze:
    """
    Create a governance baseline freeze.

    Freezes capture point-in-time governance state.
    """
    freeze = GovernanceBaselineFreeze(
        freeze_name=freeze_name,
        baseline_id=baseline_id,
        ci_summary_id=ci_summary_id,
        ci_status_at_freeze=ci_status_at_freeze,
        federation_ref_count_at_freeze=federation_ref_count_at_freeze,
        continuity_record_count_at_freeze=continuity_record_count_at_freeze,
        package_count_at_freeze=package_count_at_freeze,
        blocking_issue_count=blocking_issue_count,
        warning_count=warning_count,
    )
    freeze.deterministic_freeze_hash = freeze.compute_hash()
    return freeze


def validate_governance_baseline_freeze(
    freeze: GovernanceBaselineFreeze,
) -> Tuple[bool, List[str]]:
    """
    Validate that a freeze is well-formed.

    Returns:
        (is_valid, issues)
    """
    issues: List[str] = []

    if not freeze.human_review_required:
        issues.append("human_review_required must be True")

    if freeze.auto_release_authorized:
        issues.append("auto_release_authorized must be False")

    if freeze.release_authorized:
        issues.append("release_authorized must be False")

    if freeze.execution_authorized:
        issues.append("execution_authorized must be False")

    if freeze.machine_output_allowed:
        issues.append("machine_output_allowed must be False")

    if not freeze.freeze_name:
        issues.append("freeze_name is required")

    if freeze.blocking_issue_count < 0:
        issues.append("blocking_issue_count cannot be negative")

    if freeze.warning_count < 0:
        issues.append("warning_count cannot be negative")

    return len(issues) == 0, issues


def is_freeze_valid(freeze: GovernanceBaselineFreeze) -> bool:
    """Check if freeze is valid."""
    is_valid, _ = validate_governance_baseline_freeze(freeze)
    return is_valid


def build_freeze_hash(freeze: GovernanceBaselineFreeze) -> str:
    """Build deterministic hash for a freeze."""
    return freeze.compute_hash()


def get_freeze_summary(freeze: GovernanceBaselineFreeze) -> Dict[str, Any]:
    """Get a summary of the freeze."""
    return {
        "freeze_id": freeze.freeze_id,
        "freeze_name": freeze.freeze_name,
        "baseline_id": freeze.baseline_id,
        "ci_summary_id": freeze.ci_summary_id,
        "ci_status_at_freeze": freeze.ci_status_at_freeze,
        "federation_ref_count_at_freeze": freeze.federation_ref_count_at_freeze,
        "continuity_record_count_at_freeze": freeze.continuity_record_count_at_freeze,
        "package_count_at_freeze": freeze.package_count_at_freeze,
        "blocking_issue_count": freeze.blocking_issue_count,
        "warning_count": freeze.warning_count,
        "status": freeze.status,
        "human_review_required": freeze.human_review_required,
    }
