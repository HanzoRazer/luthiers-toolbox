"""
Review Decision Record

CAM Dev Order 8E: Model for review decision records.

Provides:
  - ReviewDecisionRecord model
  - Decision validation
  - Decision-to-status mapping
  - Deterministic hash computation

8E invariants:
  - human_review_recorded: always True
  - implementation_authorized: always False
  - execution_authorized: always False
  - machine_output_allowed: always False

Core principle:
  Decision records capture human review state.
  Decision records do not authorize implementation or execution.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator

from .review_queue_item import ReviewStatus


DecisionType = Literal[
    "acknowledge",
    "request_more_evidence",
    "defer",
    "reject",
    "mark_reviewed",
]


DECISION_TO_STATUS_MAP: Dict[DecisionType, ReviewStatus] = {
    "acknowledge": "in_review",
    "request_more_evidence": "needs_more_evidence",
    "defer": "deferred",
    "reject": "rejected",
    "mark_reviewed": "reviewed",
}


class ReviewDecisionRecord(BaseModel):
    """
    Review decision record.

    Captures human review decisions without authorizing implementation.

    8E invariants (model-enforced):
      - human_review_recorded: always True
      - implementation_authorized: always False
      - execution_authorized: always False
      - machine_output_allowed: always False
    """

    decision_id: str = Field(
        default_factory=lambda: f"rdr-{uuid4().hex[:12]}",
        description="Unique decision identifier"
    )

    queue_item_id: str = Field(
        ...,
        description="Associated queue item ID"
    )

    decision_type: DecisionType = Field(
        ...,
        description="Type of decision"
    )

    decision_rationale: str = Field(
        default="",
        description="Rationale for the decision"
    )

    reviewer_ref: Optional[str] = Field(
        default=None,
        description="Reviewer reference (metadata only)"
    )

    resulting_review_status: ReviewStatus = Field(
        ...,
        description="Review status after this decision"
    )

    human_review_recorded: bool = Field(
        default=True,
        description="Always True — this is a human review record"
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
        description="Decision timestamp"
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )

    deterministic_decision_hash: str = Field(
        default="",
        description="Deterministic hash of decision state"
    )

    @model_validator(mode="after")
    def enforce_8e_invariants(self) -> "ReviewDecisionRecord":
        """Enforce 8E invariants."""
        if not self.human_review_recorded:
            raise ValueError(
                "8E invariant violation: human_review_recorded must be True — "
                "this is a human review record"
            )
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
        """Compute deterministic hash of decision state."""
        hash_input = {
            "queue_item_id": self.queue_item_id,
            "decision_type": self.decision_type,
            "decision_rationale": self.decision_rationale,
            "reviewer_ref": self.reviewer_ref,
            "resulting_review_status": self.resulting_review_status,
        }
        canonical = json.dumps(hash_input, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()


def build_review_decision_hash(decision: ReviewDecisionRecord) -> str:
    """Build deterministic hash for a decision record."""
    return decision.compute_hash()


def get_resulting_status(decision_type: DecisionType) -> ReviewStatus:
    """Get the resulting review status for a decision type."""
    return DECISION_TO_STATUS_MAP[decision_type]


def create_review_decision_record(
    queue_item_id: str,
    decision_type: DecisionType,
    decision_rationale: str = "",
    reviewer_ref: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> ReviewDecisionRecord:
    """Create a review decision record."""
    resulting_status = get_resulting_status(decision_type)

    record = ReviewDecisionRecord(
        queue_item_id=queue_item_id,
        decision_type=decision_type,
        decision_rationale=decision_rationale,
        reviewer_ref=reviewer_ref,
        resulting_review_status=resulting_status,
        metadata=metadata or {},
    )
    record.deterministic_decision_hash = record.compute_hash()
    return record


def validate_review_decision_record(
    record: ReviewDecisionRecord,
) -> tuple[bool, List[str]]:
    """Validate a review decision record."""
    issues: List[str] = []

    if not record.human_review_recorded:
        issues.append("human_review_recorded must be True")

    if record.implementation_authorized:
        issues.append("implementation_authorized must be False")

    if record.execution_authorized:
        issues.append("execution_authorized must be False")

    if record.machine_output_allowed:
        issues.append("machine_output_allowed must be False")

    if not record.queue_item_id:
        issues.append("queue_item_id is required")

    return len(issues) == 0, issues


def get_decision_record_summary(record: ReviewDecisionRecord) -> Dict[str, Any]:
    """Get decision record summary for API response."""
    return {
        "decision_id": record.decision_id,
        "queue_item_id": record.queue_item_id,
        "decision_type": record.decision_type,
        "decision_rationale": record.decision_rationale,
        "reviewer_ref": record.reviewer_ref,
        "resulting_review_status": record.resulting_review_status,
        "human_review_recorded": record.human_review_recorded,
        "implementation_authorized": record.implementation_authorized,
        "execution_authorized": record.execution_authorized,
        "machine_output_allowed": record.machine_output_allowed,
        "created_at": record.created_at.isoformat(),
    }
