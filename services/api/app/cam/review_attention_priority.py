"""
Review Attention Priority

CAM Dev Order 8C: Model for review attention priority scoring.

Provides:
  - ReviewAttentionPriority model
  - Attention score calculation
  - Priority classification

8C invariants:
  - auto_approval_allowed: always False

Core principle:
  Priority scoring helps humans focus review effort.
  It does not authorize auto-approval.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator


ReviewPriorityLevel = Literal["critical", "high", "medium", "low"]


class ReviewAttentionPriority(BaseModel):
    """
    Review attention priority for a panel.

    Scores range from 0.0 to 1.0:
      - critical: >= 0.85
      - high: >= 0.65
      - medium: >= 0.35
      - low: < 0.35

    8C invariants (model-enforced):
      - auto_approval_allowed: always False
    """

    priority_id: str = Field(
        default_factory=lambda: f"rap-{uuid4().hex[:12]}",
        description="Unique priority identifier"
    )

    panel_id: str = Field(
        default="",
        description="Associated panel ID"
    )

    aggregate_attention_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Aggregate attention score (0.0-1.0)"
    )

    component_scores: Dict[str, float] = Field(
        default_factory=dict,
        description="Individual component scores"
    )

    priority_level: ReviewPriorityLevel = Field(
        default="low",
        description="Classified priority level"
    )

    auto_approval_allowed: bool = Field(
        default=False,
        description="Always False — 8C does not allow auto-approval"
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp"
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )

    deterministic_priority_hash: str = Field(
        default="",
        description="Deterministic hash of priority state"
    )

    @model_validator(mode="after")
    def enforce_8c_invariants(self) -> "ReviewAttentionPriority":
        """Enforce 8C invariants."""
        if self.auto_approval_allowed:
            raise ValueError(
                "8C invariant violation: auto_approval_allowed must be False — "
                "8C does not allow auto-approval"
            )
        return self

    def compute_hash(self) -> str:
        """Compute deterministic hash of priority state."""
        hash_input = {
            "panel_id": self.panel_id,
            "aggregate_attention_score": self.aggregate_attention_score,
            "priority_level": self.priority_level,
        }
        canonical = json.dumps(hash_input, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()


def calculate_attention_score(component_scores: Dict[str, float]) -> float:
    """
    Calculate aggregate attention score from components.

    Uses max aggregation: aggregate = max(component_scores)
    """
    if not component_scores:
        return 0.0
    return max(component_scores.values())


def classify_review_priority(score: float) -> ReviewPriorityLevel:
    """
    Classify review priority from score.

    Thresholds:
      - critical: >= 0.85
      - high: >= 0.65
      - medium: >= 0.35
      - low: < 0.35
    """
    if score >= 0.85:
        return "critical"
    elif score >= 0.65:
        return "high"
    elif score >= 0.35:
        return "medium"
    else:
        return "low"


def create_review_attention_priority(
    panel_id: str,
    component_scores: Optional[Dict[str, float]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> ReviewAttentionPriority:
    """Create a review attention priority."""
    scores = component_scores or {}
    aggregate = calculate_attention_score(scores)
    level = classify_review_priority(aggregate)

    priority = ReviewAttentionPriority(
        panel_id=panel_id,
        aggregate_attention_score=aggregate,
        component_scores=scores,
        priority_level=level,
        metadata=metadata or {},
    )
    priority.deterministic_priority_hash = priority.compute_hash()
    return priority


def validate_review_attention_priority(
    priority: ReviewAttentionPriority,
) -> tuple[bool, List[str]]:
    """Validate a review attention priority."""
    issues: List[str] = []

    if priority.auto_approval_allowed:
        issues.append("auto_approval_allowed must be False")

    if priority.aggregate_attention_score < 0.0 or priority.aggregate_attention_score > 1.0:
        issues.append("aggregate_attention_score must be between 0.0 and 1.0")

    return len(issues) == 0, issues


def get_priority_summary(priority: ReviewAttentionPriority) -> Dict[str, Any]:
    """Get priority summary for API response."""
    return {
        "priority_id": priority.priority_id,
        "panel_id": priority.panel_id,
        "aggregate_attention_score": priority.aggregate_attention_score,
        "priority_level": priority.priority_level,
        "component_count": len(priority.component_scores),
        "auto_approval_allowed": priority.auto_approval_allowed,
        "created_at": priority.created_at.isoformat(),
    }
