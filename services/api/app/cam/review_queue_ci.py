"""
Review Queue CI

CAM Dev Order 8E: CI summary for review queue state.

Provides:
  - ReviewQueueCISummary model
  - CI status classification
  - Queue state evaluation

8E invariants:
  - implementation_authorized: always False
  - execution_authorized: always False
  - machine_output_allowed: always False

Core principle:
  CI summary reports review queue state for visibility.
  It does not authorize implementation, execution, or machine output.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional, Tuple
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator

from .review_queue_item import ReviewQueueItem, ReviewStatus, ReviewPriority
from .review_decision_record import ReviewDecisionRecord


ReviewQueueCIStatus = Literal["pass", "warn", "fail"]


class ReviewQueueCISummary(BaseModel):
    """
    Review queue CI summary.

    8E invariants (model-enforced):
      - implementation_authorized: always False
      - execution_authorized: always False
      - machine_output_allowed: always False
    """

    summary_id: str = Field(
        default_factory=lambda: f"rqci-{uuid4().hex[:12]}",
        description="Unique summary identifier"
    )

    total_queue_items: int = Field(
        default=0,
        ge=0,
        description="Total queue items"
    )

    queued_count: int = Field(
        default=0,
        ge=0,
        description="Items in queued status"
    )

    in_review_count: int = Field(
        default=0,
        ge=0,
        description="Items in in_review status"
    )

    needs_more_evidence_count: int = Field(
        default=0,
        ge=0,
        description="Items needing more evidence"
    )

    reviewed_count: int = Field(
        default=0,
        ge=0,
        description="Items that have been reviewed"
    )

    deferred_count: int = Field(
        default=0,
        ge=0,
        description="Items that have been deferred"
    )

    rejected_count: int = Field(
        default=0,
        ge=0,
        description="Items that have been rejected"
    )

    critical_open_count: int = Field(
        default=0,
        ge=0,
        description="Critical priority open items"
    )

    high_open_count: int = Field(
        default=0,
        ge=0,
        description="High priority open items"
    )

    blocking_issue_count: int = Field(
        default=0,
        ge=0,
        description="Total blocking issues across items"
    )

    missing_assignment_count: int = Field(
        default=0,
        ge=0,
        description="Open items without assignment"
    )

    total_decisions: int = Field(
        default=0,
        ge=0,
        description="Total decision records"
    )

    status: ReviewQueueCIStatus = Field(
        default="pass",
        description="CI status: pass, warn, or fail"
    )

    blocking_issues: List[str] = Field(
        default_factory=list,
        description="Blocking issues preventing pass"
    )

    warnings: List[str] = Field(
        default_factory=list,
        description="Warnings causing warn status"
    )

    implementation_authorized: bool = Field(
        default=False,
        description="Always False — 8E does not authorize implementation"
    )

    execution_authorized: bool = Field(
        default=False,
        description="Always False — 8E does not authorize execution"
    )

    machine_output_allowed: bool = Field(
        default=False,
        description="Always False — 8E does not allow machine output"
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp"
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )

    deterministic_summary_hash: str = Field(
        default="",
        description="Deterministic hash of summary state"
    )

    @model_validator(mode="after")
    def enforce_8e_invariants(self) -> "ReviewQueueCISummary":
        """Enforce 8E invariants."""
        if self.implementation_authorized:
            raise ValueError(
                "8E invariant violation: implementation_authorized must be False — "
                "8E does not authorize implementation"
            )
        if self.execution_authorized:
            raise ValueError(
                "8E invariant violation: execution_authorized must be False — "
                "8E does not authorize execution"
            )
        if self.machine_output_allowed:
            raise ValueError(
                "8E invariant violation: machine_output_allowed must be False — "
                "8E does not allow machine output"
            )
        return self

    def compute_hash(self) -> str:
        """Compute deterministic hash of summary state."""
        hash_input = {
            "total_queue_items": self.total_queue_items,
            "queued_count": self.queued_count,
            "in_review_count": self.in_review_count,
            "needs_more_evidence_count": self.needs_more_evidence_count,
            "reviewed_count": self.reviewed_count,
            "deferred_count": self.deferred_count,
            "rejected_count": self.rejected_count,
            "critical_open_count": self.critical_open_count,
            "high_open_count": self.high_open_count,
            "blocking_issue_count": self.blocking_issue_count,
            "missing_assignment_count": self.missing_assignment_count,
            "total_decisions": self.total_decisions,
            "status": self.status,
            "blocking_issues": sorted(self.blocking_issues),
            "warnings": sorted(self.warnings),
        }
        canonical = json.dumps(hash_input, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()


def build_review_queue_ci_hash(summary: ReviewQueueCISummary) -> str:
    """Build deterministic hash for a CI summary."""
    return summary.compute_hash()


def count_by_status(
    items: List[ReviewQueueItem],
) -> Dict[ReviewStatus, int]:
    """Count queue items by status."""
    counts: Dict[ReviewStatus, int] = {
        "queued": 0,
        "in_review": 0,
        "needs_more_evidence": 0,
        "reviewed": 0,
        "deferred": 0,
        "rejected": 0,
    }
    for item in items:
        if item.review_status in counts:
            counts[item.review_status] += 1
    return counts


def count_open_by_priority(
    items: List[ReviewQueueItem],
) -> Dict[ReviewPriority, int]:
    """Count open items by priority."""
    open_statuses = ("queued", "in_review", "needs_more_evidence")
    counts: Dict[ReviewPriority, int] = {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
    }
    for item in items:
        if item.review_status in open_statuses:
            if item.review_priority in counts:
                counts[item.review_priority] += 1
    return counts


def count_blocking_issues(
    items: List[ReviewQueueItem],
) -> int:
    """Count total blocking issues across all items."""
    return sum(len(item.blocking_issues) for item in items)


def count_missing_assignments(
    items: List[ReviewQueueItem],
) -> int:
    """Count open items without assignment."""
    open_statuses = ("queued", "in_review", "needs_more_evidence")
    return sum(
        1 for item in items
        if item.review_status in open_statuses
        and item.assigned_role is None
    )


def detect_authorization_violations(
    items: List[ReviewQueueItem],
) -> List[str]:
    """Detect items with authorization violations."""
    violations: List[str] = []
    for item in items:
        if item.decision_authorized:
            violations.append(f"[{item.queue_item_id}] decision_authorized=True")
        if item.implementation_authorized:
            violations.append(f"[{item.queue_item_id}] implementation_authorized=True")
        if item.execution_authorized:
            violations.append(f"[{item.queue_item_id}] execution_authorized=True")
        if item.machine_output_allowed:
            violations.append(f"[{item.queue_item_id}] machine_output_allowed=True")
    return violations


def classify_review_queue_ci_status(
    critical_open_count: int,
    high_open_count: int,
    missing_assignment_count: int,
    needs_more_evidence_count: int,
    blocking_issue_count: int,
    authorization_violations: List[str],
) -> Tuple[ReviewQueueCIStatus, List[str], List[str]]:
    """
    Classify review queue CI status.

    FAIL conditions:
      - Any authorization violations

    WARN conditions:
      - critical_open_count > 0
      - high_open_count > 0
      - missing_assignment_count > 0
      - needs_more_evidence_count > 0
      - blocking_issue_count > 0

    PASS:
      - No failures, no warnings

    Returns (status, blocking_issues, warnings).
    """
    blocking_issues: List[str] = []
    warnings: List[str] = []

    # FAIL conditions
    if authorization_violations:
        blocking_issues.extend(authorization_violations)

    if blocking_issues:
        return "fail", blocking_issues, warnings

    # WARN conditions
    if critical_open_count > 0:
        warnings.append(f"{critical_open_count} critical priority item(s) open")

    if high_open_count > 0:
        warnings.append(f"{high_open_count} high priority item(s) open")

    if missing_assignment_count > 0:
        warnings.append(f"{missing_assignment_count} open item(s) without assignment")

    if needs_more_evidence_count > 0:
        warnings.append(f"{needs_more_evidence_count} item(s) need more evidence")

    if blocking_issue_count > 0:
        warnings.append(f"{blocking_issue_count} blocking issue(s) across items")

    if warnings:
        return "warn", blocking_issues, warnings

    return "pass", blocking_issues, warnings


def evaluate_review_queue_ci(
    items: List[ReviewQueueItem],
    decisions: List[ReviewDecisionRecord],
) -> ReviewQueueCISummary:
    """
    Evaluate review queue CI state.

    Builds CI summary from current queue state.
    """
    # Count by status
    status_counts = count_by_status(items)

    # Count open by priority
    priority_counts = count_open_by_priority(items)

    # Count blocking issues
    blocking_issue_count = count_blocking_issues(items)

    # Count missing assignments
    missing_assignment_count = count_missing_assignments(items)

    # Detect authorization violations
    auth_violations = detect_authorization_violations(items)

    # Classify status
    status, blocking_issues, warnings = classify_review_queue_ci_status(
        critical_open_count=priority_counts["critical"],
        high_open_count=priority_counts["high"],
        missing_assignment_count=missing_assignment_count,
        needs_more_evidence_count=status_counts["needs_more_evidence"],
        blocking_issue_count=blocking_issue_count,
        authorization_violations=auth_violations,
    )

    summary = ReviewQueueCISummary(
        total_queue_items=len(items),
        queued_count=status_counts["queued"],
        in_review_count=status_counts["in_review"],
        needs_more_evidence_count=status_counts["needs_more_evidence"],
        reviewed_count=status_counts["reviewed"],
        deferred_count=status_counts["deferred"],
        rejected_count=status_counts["rejected"],
        critical_open_count=priority_counts["critical"],
        high_open_count=priority_counts["high"],
        blocking_issue_count=blocking_issue_count,
        missing_assignment_count=missing_assignment_count,
        total_decisions=len(decisions),
        status=status,
        blocking_issues=blocking_issues,
        warnings=warnings,
    )

    summary.deterministic_summary_hash = summary.compute_hash()
    return summary


def get_ci_summary_dict(summary: ReviewQueueCISummary) -> Dict[str, Any]:
    """Get CI summary as dictionary for API response."""
    return {
        "summary_id": summary.summary_id,
        "total_queue_items": summary.total_queue_items,
        "queued_count": summary.queued_count,
        "in_review_count": summary.in_review_count,
        "needs_more_evidence_count": summary.needs_more_evidence_count,
        "reviewed_count": summary.reviewed_count,
        "deferred_count": summary.deferred_count,
        "rejected_count": summary.rejected_count,
        "critical_open_count": summary.critical_open_count,
        "high_open_count": summary.high_open_count,
        "blocking_issue_count": summary.blocking_issue_count,
        "missing_assignment_count": summary.missing_assignment_count,
        "total_decisions": summary.total_decisions,
        "status": summary.status,
        "blocking_issues": summary.blocking_issues,
        "warnings": summary.warnings,
        "implementation_authorized": summary.implementation_authorized,
        "execution_authorized": summary.execution_authorized,
        "machine_output_allowed": summary.machine_output_allowed,
        "created_at": summary.created_at.isoformat(),
    }
