"""
Review Queue Item

CAM Dev Order 8E: Model for governed review queue items.

Provides:
  - ReviewQueueItem model
  - Queue item validation
  - Deterministic hash computation

8E invariants:
  - human_review_required: always True
  - decision_authorized: always False
  - implementation_authorized: always False
  - execution_authorized: always False
  - machine_output_allowed: always False

Core principle:
  Review routing organizes human decisions.
  Review routing does not make human decisions.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator


ReviewSourceLayer = Literal[
    "manufacturing_cognition",
    "geometry_authority",
    "strategy_export",
    "fixture_topology",
    "manufacturing_replay",
    "federation",
    "review_ux",
    "post_freeze",
]

ReviewPriority = Literal["low", "medium", "high", "critical"]

ReviewStatus = Literal[
    "queued",
    "in_review",
    "needs_more_evidence",
    "reviewed",
    "deferred",
    "rejected",
]


class ReviewQueueItem(BaseModel):
    """
    Review queue item for governed human review routing.

    8E invariants (model-enforced):
      - human_review_required: always True
      - decision_authorized: always False
      - implementation_authorized: always False
      - execution_authorized: always False
      - machine_output_allowed: always False
    """

    queue_item_id: str = Field(
        default_factory=lambda: f"rqi-{uuid4().hex[:12]}",
        description="Unique queue item identifier"
    )

    panel_id: Optional[str] = Field(
        default=None,
        description="Associated review panel ID"
    )

    priority_id: Optional[str] = Field(
        default=None,
        description="Associated attention priority ID"
    )

    provenance_explanation_id: Optional[str] = Field(
        default=None,
        description="Associated provenance explanation ID"
    )

    source_layer: ReviewSourceLayer = Field(
        default="review_ux",
        description="Source layer that generated this review item"
    )

    review_priority: ReviewPriority = Field(
        default="medium",
        description="Review priority level"
    )

    review_status: ReviewStatus = Field(
        default="queued",
        description="Current review status"
    )

    assigned_role: Optional[str] = Field(
        default=None,
        description="Assigned reviewer role (metadata only)"
    )

    review_reason: str = Field(
        default="",
        description="Reason for review"
    )

    blocking_issues: List[str] = Field(
        default_factory=list,
        description="Blocking issues requiring resolution"
    )

    warnings: List[str] = Field(
        default_factory=list,
        description="Warnings for reviewer attention"
    )

    human_review_required: bool = Field(
        default=True,
        description="Always True — 8E requires human review"
    )

    decision_authorized: bool = Field(
        default=False,
        description="Always False — 8E does not authorize decisions"
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

    deterministic_queue_hash: str = Field(
        default="",
        description="Deterministic hash of queue item state"
    )

    @model_validator(mode="after")
    def enforce_8e_invariants(self) -> "ReviewQueueItem":
        """Enforce 8E invariants."""
        if not self.human_review_required:
            raise ValueError(
                "8E invariant violation: human_review_required must be True — "
                "8E requires human review"
            )
        if self.decision_authorized:
            raise ValueError(
                "8E invariant violation: decision_authorized must be False — "
                "8E does not authorize decisions"
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
        """Compute deterministic hash of queue item state."""
        hash_input = {
            "panel_id": self.panel_id,
            "priority_id": self.priority_id,
            "source_layer": self.source_layer,
            "review_priority": self.review_priority,
            "review_status": self.review_status,
            "assigned_role": self.assigned_role,
            "review_reason": self.review_reason,
            "blocking_issues": sorted(self.blocking_issues),
            "warnings": sorted(self.warnings),
        }
        canonical = json.dumps(hash_input, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()


def build_review_queue_hash(item: ReviewQueueItem) -> str:
    """Build deterministic hash for a queue item."""
    return item.compute_hash()


def create_review_queue_item(
    review_reason: str,
    source_layer: ReviewSourceLayer = "review_ux",
    review_priority: ReviewPriority = "medium",
    panel_id: Optional[str] = None,
    priority_id: Optional[str] = None,
    provenance_explanation_id: Optional[str] = None,
    assigned_role: Optional[str] = None,
    blocking_issues: Optional[List[str]] = None,
    warnings: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> ReviewQueueItem:
    """Create a review queue item."""
    item = ReviewQueueItem(
        panel_id=panel_id,
        priority_id=priority_id,
        provenance_explanation_id=provenance_explanation_id,
        source_layer=source_layer,
        review_priority=review_priority,
        assigned_role=assigned_role,
        review_reason=review_reason,
        blocking_issues=blocking_issues or [],
        warnings=warnings or [],
        metadata=metadata or {},
    )
    item.deterministic_queue_hash = item.compute_hash()
    return item


def validate_review_queue_item(
    item: ReviewQueueItem,
) -> tuple[bool, List[str]]:
    """Validate a review queue item."""
    issues: List[str] = []

    if not item.human_review_required:
        issues.append("human_review_required must be True")

    if item.decision_authorized:
        issues.append("decision_authorized must be False")

    if item.implementation_authorized:
        issues.append("implementation_authorized must be False")

    if item.execution_authorized:
        issues.append("execution_authorized must be False")

    if item.machine_output_allowed:
        issues.append("machine_output_allowed must be False")

    if not item.review_reason:
        issues.append("review_reason is required")

    return len(issues) == 0, issues


def get_queue_item_summary(item: ReviewQueueItem) -> Dict[str, Any]:
    """Get queue item summary for API response."""
    return {
        "queue_item_id": item.queue_item_id,
        "panel_id": item.panel_id,
        "priority_id": item.priority_id,
        "source_layer": item.source_layer,
        "review_priority": item.review_priority,
        "review_status": item.review_status,
        "assigned_role": item.assigned_role,
        "review_reason": item.review_reason,
        "blocking_issue_count": len(item.blocking_issues),
        "warning_count": len(item.warnings),
        "human_review_required": item.human_review_required,
        "decision_authorized": item.decision_authorized,
        "implementation_authorized": item.implementation_authorized,
        "execution_authorized": item.execution_authorized,
        "machine_output_allowed": item.machine_output_allowed,
        "created_at": item.created_at.isoformat(),
    }
