"""
Review Enforcement — Constitutional Runtime Foundation
======================================================

DEV ORDER 1D: IBG Constitutional Intake Foundation

Enforces human review requirements for semantic objects.
Machine systems may suggest, rank, evaluate, and constrain,
but may NOT ratify, canonize, or silently clear review requirements.

Key principle:
    review_required may NOT be machine-cleared without:
    - explicit authority transition
    - provenance update
    - review lineage entry

Author: Constitutional Runtime Foundation
Date: 2026-05-18
Sprint: DEV ORDER 1D
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class ReviewDecision(str, Enum):
    """Possible review decisions."""
    PENDING = "pending"
    APPROVE = "approve"
    REJECT = "reject"
    DEFER = "defer"
    REQUEST_CHANGES = "request_changes"


class ReviewBypassAttemptError(Exception):
    """Raised when machine code attempts to bypass review requirements."""

    def __init__(self, attempted_action: str, actor: str):
        self.attempted_action = attempted_action
        self.actor = actor
        super().__init__(
            f"Review bypass attempt: {attempted_action} by {actor}. "
            "Machine code cannot clear review requirements."
        )


class ReviewIncompleteError(Exception):
    """Raised when an operation requires completed review but review is pending."""

    def __init__(self, operation: str):
        self.operation = operation
        super().__init__(
            f"Operation '{operation}' requires completed human review"
        )


@dataclass
class ReviewRecord:
    """
    Record of a single human review action.

    Captures who reviewed, what decision was made, and any notes.
    """
    reviewer_id: str
    decision: ReviewDecision
    timestamp: datetime
    notes: Optional[str] = None
    review_context: Optional[Dict[str, Any]] = None

    def is_human(self) -> bool:
        """Check if reviewer is human (not machine)."""
        return not self.reviewer_id.startswith("system:")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "reviewer_id": self.reviewer_id,
            "decision": self.decision.value,
            "timestamp": self.timestamp.isoformat(),
            "notes": self.notes,
            "review_context": self.review_context,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReviewRecord":
        """Create from dictionary."""
        return cls(
            reviewer_id=data["reviewer_id"],
            decision=ReviewDecision(data["decision"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            notes=data.get("notes"),
            review_context=data.get("review_context"),
        )


@dataclass
class ReviewEnforcement:
    """
    Enforces review requirements with protected state.

    Once review_required is set to True by machine code, it cannot
    be cleared by machine code. Only explicit human review can
    transition the state.

    Attributes:
        _review_required: Internal review flag (protected)
        _review_required_set_by: Who set the review requirement
        _review_required_reason: Why review is required
        _review_completed: Whether review has been completed
        _review_decision: Final review decision
        review_history: History of all review actions
    """
    _review_required: bool = field(default=True, repr=False)
    _review_required_set_by: str = field(default="system:default", repr=False)
    _review_required_reason: str = field(default="Default: all candidates require review", repr=False)
    _review_completed: bool = field(default=False, repr=False)
    _review_decision: ReviewDecision = field(default=ReviewDecision.PENDING, repr=False)
    _bypass_attempt_count: int = field(default=0, repr=False)
    review_history: List[ReviewRecord] = field(default_factory=list)

    @property
    def review_required(self) -> bool:
        """Read-only access to review_required flag."""
        return self._review_required

    @property
    def review_completed(self) -> bool:
        """Read-only access to review_completed flag."""
        return self._review_completed

    @property
    def review_decision(self) -> ReviewDecision:
        """Read-only access to review decision."""
        return self._review_decision

    @property
    def bypass_attempt_count(self) -> int:
        """Number of bypass attempts detected."""
        return self._bypass_attempt_count

    def set_review_required(
        self,
        required: bool,
        actor: str,
        reason: str,
    ) -> None:
        """
        Set review requirement.

        Machine code can set review_required to True.
        Machine code CANNOT set review_required to False.
        Only human actors can clear the review requirement.

        Args:
            required: Whether review is required
            actor: Who is setting this (must start with "human:" for False)
            reason: Why this change is being made

        Raises:
            ReviewBypassAttemptError: If machine attempts to clear requirement
        """
        if self._review_required and not required:
            # Attempting to clear review requirement
            if not actor.startswith("human:"):
                self._bypass_attempt_count += 1
                raise ReviewBypassAttemptError(
                    "clear review_required flag",
                    actor
                )

        self._review_required = required
        self._review_required_set_by = actor
        self._review_required_reason = reason

    def record_review(
        self,
        reviewer_id: str,
        decision: ReviewDecision,
        notes: Optional[str] = None,
        review_context: Optional[Dict[str, Any]] = None,
    ) -> ReviewRecord:
        """
        Record a review action.

        Only human reviewers can approve or reject.
        System actors can only defer or request changes.

        Args:
            reviewer_id: ID of the reviewer
            decision: Review decision
            notes: Optional notes
            review_context: Optional context about what was reviewed

        Returns:
            The created review record

        Raises:
            ReviewBypassAttemptError: If system actor tries to approve/reject
        """
        # Check if system is trying to approve/reject
        if reviewer_id.startswith("system:"):
            if decision in {ReviewDecision.APPROVE, ReviewDecision.REJECT}:
                self._bypass_attempt_count += 1
                raise ReviewBypassAttemptError(
                    f"issue {decision.value} decision",
                    reviewer_id
                )

        record = ReviewRecord(
            reviewer_id=reviewer_id,
            decision=decision,
            timestamp=datetime.now(timezone.utc),
            notes=notes,
            review_context=review_context,
        )

        self.review_history.append(record)

        # Update state based on decision
        if decision in {ReviewDecision.APPROVE, ReviewDecision.REJECT}:
            self._review_completed = True
            self._review_decision = decision

            # If approved by human, review is no longer required
            if decision == ReviewDecision.APPROVE:
                self._review_required = False
                self._review_required_set_by = reviewer_id
                self._review_required_reason = "Cleared by human approval"

        return record

    def require_completed_review(self, operation: str) -> None:
        """
        Assert that review has been completed before proceeding.

        Args:
            operation: Description of what operation requires review

        Raises:
            ReviewIncompleteError: If review is not completed
        """
        if not self._review_completed:
            raise ReviewIncompleteError(operation)

    def require_approval(self, operation: str) -> None:
        """
        Assert that review has been completed with APPROVE decision.

        Args:
            operation: Description of what operation requires approval

        Raises:
            ReviewIncompleteError: If review is not completed or not approved
        """
        if not self._review_completed:
            raise ReviewIncompleteError(operation)

        if self._review_decision != ReviewDecision.APPROVE:
            raise ReviewIncompleteError(
                f"{operation} (review completed but decision was {self._review_decision.value})"
            )

    def get_latest_review(self) -> Optional[ReviewRecord]:
        """Get the most recent review record."""
        if self.review_history:
            return self.review_history[-1]
        return None

    def get_human_reviews(self) -> List[ReviewRecord]:
        """Get all reviews by human reviewers."""
        return [r for r in self.review_history if r.is_human()]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "review_required": self._review_required,
            "review_required_set_by": self._review_required_set_by,
            "review_required_reason": self._review_required_reason,
            "review_completed": self._review_completed,
            "review_decision": self._review_decision.value,
            "bypass_attempt_count": self._bypass_attempt_count,
            "review_history": [r.to_dict() for r in self.review_history],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReviewEnforcement":
        """Create from dictionary."""
        enforcement = cls()
        enforcement._review_required = data.get("review_required", True)
        enforcement._review_required_set_by = data.get("review_required_set_by", "system:default")
        enforcement._review_required_reason = data.get("review_required_reason", "")
        enforcement._review_completed = data.get("review_completed", False)
        enforcement._review_decision = ReviewDecision(data.get("review_decision", "pending"))
        enforcement._bypass_attempt_count = data.get("bypass_attempt_count", 0)
        enforcement.review_history = [
            ReviewRecord.from_dict(r)
            for r in data.get("review_history", [])
        ]
        return enforcement


def create_default_review_enforcement() -> ReviewEnforcement:
    """
    Create default review enforcement requiring human review.

    All semantic candidates start with review required.
    """
    return ReviewEnforcement()


def create_pre_approved_review_enforcement(
    approver_id: str,
    reason: str,
) -> ReviewEnforcement:
    """
    Create review enforcement for pre-approved items.

    Use only for items that have already been human-reviewed
    through another channel.

    Args:
        approver_id: Human reviewer who approved (must start with "human:")
        reason: Reason for pre-approval

    Returns:
        ReviewEnforcement with review already completed

    Raises:
        ValueError: If approver_id is not a human actor
    """
    if not approver_id.startswith("human:"):
        raise ValueError(
            f"Pre-approval requires human actor, got: {approver_id}"
        )

    enforcement = ReviewEnforcement()
    enforcement._review_required = False
    enforcement._review_required_set_by = approver_id
    enforcement._review_required_reason = f"Pre-approved: {reason}"
    enforcement._review_completed = True
    enforcement._review_decision = ReviewDecision.APPROVE

    enforcement.review_history.append(ReviewRecord(
        reviewer_id=approver_id,
        decision=ReviewDecision.APPROVE,
        timestamp=datetime.now(timezone.utc),
        notes=f"Pre-approved: {reason}",
    ))

    return enforcement
