"""
Review UX Baseline

CAM Dev Order 8D: Baseline model for review UX CI enforcement.

Provides:
  - ReviewUXBaseline model
  - Baseline hash computation
  - Threshold definitions

8D invariants:
  - execution_authorized: always False
  - machine_output_allowed: always False
  - auto_approval_allowed: always False

Core principle:
  Review UX is governance-critical only if its completeness is measurable.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator


class ReviewUXBaseline(BaseModel):
    """
    Review UX baseline for CI enforcement.

    Defines expected state and allowed thresholds for review UX artifacts.

    8D invariants (model-enforced):
      - execution_authorized: always False
      - machine_output_allowed: always False
      - auto_approval_allowed: always False
    """

    baseline_id: str = Field(
        default_factory=lambda: f"ruxb-{uuid4().hex[:12]}",
        description="Unique baseline identifier"
    )

    baseline_name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Baseline name"
    )

    required_panel_count: Optional[int] = Field(
        default=None,
        ge=0,
        description="Required number of review panels (None = not checked)"
    )

    allowed_missing_provenance_count: int = Field(
        default=0,
        ge=0,
        description="Allowed count of panels missing provenance"
    )

    allowed_federation_visibility_gap_count: int = Field(
        default=0,
        ge=0,
        description="Allowed count of federation visibility gaps"
    )

    allowed_fragmented_replay_count: int = Field(
        default=0,
        ge=0,
        description="Allowed count of fragmented replay panels"
    )

    allowed_review_overload_count: int = Field(
        default=0,
        ge=0,
        description="Allowed count of review overload panels"
    )

    execution_authorized: bool = Field(
        default=False,
        description="Always False — 8D does not authorize execution"
    )

    machine_output_allowed: bool = Field(
        default=False,
        description="Always False — 8D does not allow machine output"
    )

    auto_approval_allowed: bool = Field(
        default=False,
        description="Always False — 8D does not allow auto-approval"
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp"
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )

    deterministic_baseline_hash: str = Field(
        default="",
        description="Deterministic hash of baseline state"
    )

    @model_validator(mode="after")
    def enforce_8d_invariants(self) -> "ReviewUXBaseline":
        """Enforce 8D invariants."""
        if self.execution_authorized:
            raise ValueError(
                "8D invariant violation: execution_authorized must be False — "
                "8D does not authorize execution"
            )
        if self.machine_output_allowed:
            raise ValueError(
                "8D invariant violation: machine_output_allowed must be False — "
                "8D does not allow machine output"
            )
        if self.auto_approval_allowed:
            raise ValueError(
                "8D invariant violation: auto_approval_allowed must be False — "
                "8D does not allow auto-approval"
            )
        return self

    def compute_hash(self) -> str:
        """Compute deterministic hash of baseline state."""
        hash_input = {
            "baseline_name": self.baseline_name,
            "required_panel_count": self.required_panel_count,
            "allowed_missing_provenance_count": self.allowed_missing_provenance_count,
            "allowed_federation_visibility_gap_count": self.allowed_federation_visibility_gap_count,
            "allowed_fragmented_replay_count": self.allowed_fragmented_replay_count,
            "allowed_review_overload_count": self.allowed_review_overload_count,
        }
        canonical = json.dumps(hash_input, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()


def build_review_ux_baseline_hash(baseline: ReviewUXBaseline) -> str:
    """Build deterministic hash for a baseline."""
    return baseline.compute_hash()


def create_review_ux_baseline(
    baseline_name: str,
    required_panel_count: Optional[int] = None,
    allowed_missing_provenance_count: int = 0,
    allowed_federation_visibility_gap_count: int = 0,
    allowed_fragmented_replay_count: int = 0,
    allowed_review_overload_count: int = 0,
    metadata: Optional[Dict[str, Any]] = None,
) -> ReviewUXBaseline:
    """
    Create a review UX baseline.

    All baselines start with execution/machine_output/auto_approval = False.
    """
    baseline = ReviewUXBaseline(
        baseline_name=baseline_name,
        required_panel_count=required_panel_count,
        allowed_missing_provenance_count=allowed_missing_provenance_count,
        allowed_federation_visibility_gap_count=allowed_federation_visibility_gap_count,
        allowed_fragmented_replay_count=allowed_fragmented_replay_count,
        allowed_review_overload_count=allowed_review_overload_count,
        metadata=metadata or {},
    )

    baseline.deterministic_baseline_hash = baseline.compute_hash()
    return baseline


def validate_review_ux_baseline(
    baseline: ReviewUXBaseline,
) -> tuple[bool, List[str]]:
    """
    Validate a review UX baseline.

    Returns (is_valid, issues).
    """
    issues: List[str] = []

    if not baseline.baseline_name:
        issues.append("Missing baseline_name")

    if baseline.execution_authorized:
        issues.append("execution_authorized must be False")

    if baseline.machine_output_allowed:
        issues.append("machine_output_allowed must be False")

    if baseline.auto_approval_allowed:
        issues.append("auto_approval_allowed must be False")

    return len(issues) == 0, issues


def get_baseline_summary(baseline: ReviewUXBaseline) -> Dict[str, Any]:
    """Get baseline summary for API response."""
    return {
        "baseline_id": baseline.baseline_id,
        "baseline_name": baseline.baseline_name,
        "required_panel_count": baseline.required_panel_count,
        "allowed_missing_provenance_count": baseline.allowed_missing_provenance_count,
        "allowed_federation_visibility_gap_count": baseline.allowed_federation_visibility_gap_count,
        "allowed_fragmented_replay_count": baseline.allowed_fragmented_replay_count,
        "allowed_review_overload_count": baseline.allowed_review_overload_count,
        "execution_authorized": baseline.execution_authorized,
        "machine_output_allowed": baseline.machine_output_allowed,
        "auto_approval_allowed": baseline.auto_approval_allowed,
        "created_at": baseline.created_at.isoformat(),
    }
