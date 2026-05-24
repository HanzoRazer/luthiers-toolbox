"""
Review UX CI Enforcement

CAM Dev Order 8D: CI enforcement for review UX contracts.

Provides:
  - ReviewUXCIEnforcementSummary model
  - CI status classification
  - Baseline comparison
  - Counting helpers (pure functions)

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
from typing import Any, Dict, List, Literal, Optional, Tuple
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator

from .review_ux_baseline import ReviewUXBaseline
from .manufacturing_review_panel import ManufacturingReviewPanel
from .provenance_explanation import ProvenanceExplanationArtifact
from .review_attention_priority import ReviewAttentionPriority


ReviewUXCIStatus = Literal["pass", "warn", "fail"]


class ReviewUXCIEnforcementSummary(BaseModel):
    """
    Review UX CI enforcement summary.

    Records review UX state for CI evaluation against baseline.

    8D invariants (model-enforced):
      - execution_authorized: always False
      - machine_output_allowed: always False
      - auto_approval_allowed: always False
    """

    summary_id: str = Field(
        default_factory=lambda: f"ruxci-{uuid4().hex[:12]}",
        description="Unique summary identifier"
    )

    baseline_id: Optional[str] = Field(
        default=None,
        description="Baseline ID used for comparison (if any)"
    )

    panel_count: int = Field(
        default=0,
        ge=0,
        description="Total review panels"
    )

    missing_provenance_count: int = Field(
        default=0,
        ge=0,
        description="Panels missing provenance"
    )

    federation_visibility_gap_count: int = Field(
        default=0,
        ge=0,
        description="Panels with federation visibility gaps"
    )

    fragmented_replay_count: int = Field(
        default=0,
        ge=0,
        description="Panels with fragmented replay"
    )

    review_overload_count: int = Field(
        default=0,
        ge=0,
        description="Panels in review overload"
    )

    baseline_exceeded: bool = Field(
        default=False,
        description="Whether baseline thresholds were exceeded"
    )

    exceeded_fields: List[str] = Field(
        default_factory=list,
        description="Fields that exceeded baseline thresholds"
    )

    status: ReviewUXCIStatus = Field(
        default="pass",
        description="CI status: pass, warn, or fail"
    )

    blocking_issues: List[str] = Field(
        default_factory=list,
        description="Specific blocking issues"
    )

    warnings: List[str] = Field(
        default_factory=list,
        description="Specific warnings"
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

    deterministic_summary_hash: str = Field(
        default="",
        description="Deterministic hash of summary state"
    )

    @model_validator(mode="after")
    def enforce_8d_invariants(self) -> "ReviewUXCIEnforcementSummary":
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
        """Compute deterministic hash of summary state."""
        hash_input = {
            "baseline_id": self.baseline_id,
            "panel_count": self.panel_count,
            "missing_provenance_count": self.missing_provenance_count,
            "federation_visibility_gap_count": self.federation_visibility_gap_count,
            "fragmented_replay_count": self.fragmented_replay_count,
            "review_overload_count": self.review_overload_count,
            "baseline_exceeded": self.baseline_exceeded,
            "exceeded_fields": sorted(self.exceeded_fields),
            "status": self.status,
            "blocking_issues": sorted(self.blocking_issues),
            "warnings": sorted(self.warnings),
        }
        canonical = json.dumps(hash_input, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()


# ─────────────────────────────────────────────────────────────────────────────
# Pure counting helpers (accept collections, no registry coupling)
# ─────────────────────────────────────────────────────────────────────────────

def count_missing_provenance(
    panels: List[ManufacturingReviewPanel],
    explanations: List[ProvenanceExplanationArtifact],
) -> int:
    """
    Count artifacts missing provenance explanations.

    For each panel, check if each context_artifact_id has a matching explanation.
    """
    explained_ids = {e.artifact_id for e in explanations}
    count = 0
    for panel in panels:
        for artifact_id in panel.context_artifact_ids:
            if artifact_id not in explained_ids:
                count += 1
    return count


def count_federation_visibility_gaps(
    panels: List[ManufacturingReviewPanel],
) -> int:
    """Count panels with federation_visible=False."""
    return sum(1 for p in panels if not p.federation_visible)


def count_fragmented_replay(
    panels: List[ManufacturingReviewPanel],
) -> int:
    """Count panels with replay_complete=False."""
    return sum(1 for p in panels if not p.replay_complete)


def count_review_overload(
    priorities: List[ReviewAttentionPriority],
    threshold: float = 0.85,
) -> int:
    """
    Count priorities with aggregate_attention_score >= threshold.

    Default threshold is 0.85 (critical level).
    """
    return sum(
        1 for p in priorities
        if p.aggregate_attention_score >= threshold
    )


# ─────────────────────────────────────────────────────────────────────────────
# Baseline comparison
# ─────────────────────────────────────────────────────────────────────────────

def compare_review_ux_to_baseline(
    missing_provenance_count: int,
    federation_visibility_gap_count: int,
    fragmented_replay_count: int,
    review_overload_count: int,
    panel_count: int,
    baseline: Optional[ReviewUXBaseline],
) -> Dict[str, Any]:
    """
    Compare review UX state to baseline.

    Returns dict with:
      - baseline_exceeded: bool
      - exceeded_fields: List[str]
      - comparison_details: Dict
    """
    if baseline is None:
        return {
            "baseline_exceeded": False,
            "exceeded_fields": [],
            "comparison_details": {"no_baseline": True},
        }

    exceeded_fields: List[str] = []

    # Check required panel count
    if baseline.required_panel_count is not None:
        if panel_count < baseline.required_panel_count:
            exceeded_fields.append("panel_count")

    # Check thresholds
    if missing_provenance_count > baseline.allowed_missing_provenance_count:
        exceeded_fields.append("missing_provenance")

    if federation_visibility_gap_count > baseline.allowed_federation_visibility_gap_count:
        exceeded_fields.append("federation_visibility_gap")

    if fragmented_replay_count > baseline.allowed_fragmented_replay_count:
        exceeded_fields.append("fragmented_replay")

    if review_overload_count > baseline.allowed_review_overload_count:
        exceeded_fields.append("review_overload")

    return {
        "baseline_exceeded": len(exceeded_fields) > 0,
        "exceeded_fields": exceeded_fields,
        "comparison_details": {
            "panel_count": panel_count,
            "required_panel_count": baseline.required_panel_count,
            "missing_provenance_count": missing_provenance_count,
            "allowed_missing_provenance_count": baseline.allowed_missing_provenance_count,
            "federation_visibility_gap_count": federation_visibility_gap_count,
            "allowed_federation_visibility_gap_count": baseline.allowed_federation_visibility_gap_count,
            "fragmented_replay_count": fragmented_replay_count,
            "allowed_fragmented_replay_count": baseline.allowed_fragmented_replay_count,
            "review_overload_count": review_overload_count,
            "allowed_review_overload_count": baseline.allowed_review_overload_count,
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# CI status classification
# ─────────────────────────────────────────────────────────────────────────────

def classify_review_ux_ci_status(
    missing_provenance_count: int,
    federation_visibility_gap_count: int,
    fragmented_replay_count: int,
    review_overload_count: int,
    baseline_exceeded: bool,
    exceeded_fields: List[str],
) -> Tuple[ReviewUXCIStatus, List[str], List[str]]:
    """
    Classify review UX CI status.

    FAIL conditions:
      - baseline_exceeded = True
      - review_overload_count > 0

    WARN conditions:
      - missing_provenance_count > 0 (without exceeding baseline)
      - federation_visibility_gap_count > 0 (without exceeding baseline)
      - fragmented_replay_count > 0 (without exceeding baseline)

    PASS:
      - No FAIL or WARN conditions

    Returns (status, blocking_issues, warnings).
    """
    blocking_issues: List[str] = []
    warnings: List[str] = []

    # FAIL conditions
    if baseline_exceeded:
        blocking_issues.append(f"Baseline thresholds exceeded: {', '.join(exceeded_fields)}")

    if review_overload_count > 0:
        blocking_issues.append(f"Review overload detected: {review_overload_count} panel(s)")

    if blocking_issues:
        return "fail", blocking_issues, warnings

    # WARN conditions
    if missing_provenance_count > 0:
        warnings.append(f"Missing provenance: {missing_provenance_count} artifact(s)")

    if federation_visibility_gap_count > 0:
        warnings.append(f"Federation visibility gaps: {federation_visibility_gap_count} panel(s)")

    if fragmented_replay_count > 0:
        warnings.append(f"Fragmented replay: {fragmented_replay_count} panel(s)")

    if warnings:
        return "warn", blocking_issues, warnings

    return "pass", blocking_issues, warnings


def evaluate_review_ux_against_baseline(
    panels: List[ManufacturingReviewPanel],
    explanations: List[ProvenanceExplanationArtifact],
    priorities: List[ReviewAttentionPriority],
    baseline: Optional[ReviewUXBaseline] = None,
) -> ReviewUXCIEnforcementSummary:
    """
    Evaluate review UX state against baseline.

    Builds CI summary from current 8C artifacts.
    """
    # Count
    panel_count = len(panels)
    missing_provenance = count_missing_provenance(panels, explanations)
    federation_gaps = count_federation_visibility_gaps(panels)
    fragmented_replay = count_fragmented_replay(panels)
    review_overload = count_review_overload(priorities)

    # Compare to baseline
    comparison = compare_review_ux_to_baseline(
        missing_provenance_count=missing_provenance,
        federation_visibility_gap_count=federation_gaps,
        fragmented_replay_count=fragmented_replay,
        review_overload_count=review_overload,
        panel_count=panel_count,
        baseline=baseline,
    )

    baseline_exceeded = comparison["baseline_exceeded"]
    exceeded_fields = comparison["exceeded_fields"]

    # Classify status
    status, blocking_issues, warnings = classify_review_ux_ci_status(
        missing_provenance_count=missing_provenance,
        federation_visibility_gap_count=federation_gaps,
        fragmented_replay_count=fragmented_replay,
        review_overload_count=review_overload,
        baseline_exceeded=baseline_exceeded,
        exceeded_fields=exceeded_fields,
    )

    summary = ReviewUXCIEnforcementSummary(
        baseline_id=baseline.baseline_id if baseline else None,
        panel_count=panel_count,
        missing_provenance_count=missing_provenance,
        federation_visibility_gap_count=federation_gaps,
        fragmented_replay_count=fragmented_replay,
        review_overload_count=review_overload,
        baseline_exceeded=baseline_exceeded,
        exceeded_fields=exceeded_fields,
        status=status,
        blocking_issues=blocking_issues,
        warnings=warnings,
    )

    summary.deterministic_summary_hash = summary.compute_hash()
    return summary


def get_ci_enforcement_summary(summary: ReviewUXCIEnforcementSummary) -> Dict[str, Any]:
    """Get CI summary as dictionary for API response."""
    return {
        "summary_id": summary.summary_id,
        "baseline_id": summary.baseline_id,
        "panel_count": summary.panel_count,
        "missing_provenance_count": summary.missing_provenance_count,
        "federation_visibility_gap_count": summary.federation_visibility_gap_count,
        "fragmented_replay_count": summary.fragmented_replay_count,
        "review_overload_count": summary.review_overload_count,
        "baseline_exceeded": summary.baseline_exceeded,
        "exceeded_fields": summary.exceeded_fields,
        "status": summary.status,
        "blocking_issues": summary.blocking_issues,
        "warnings": summary.warnings,
        "execution_authorized": summary.execution_authorized,
        "machine_output_allowed": summary.machine_output_allowed,
        "auto_approval_allowed": summary.auto_approval_allowed,
        "created_at": summary.created_at.isoformat(),
    }


def get_status_message(summary: ReviewUXCIEnforcementSummary) -> str:
    """Get human-readable status message."""
    if summary.status == "pass":
        return "Review UX CI passed — all checks clean"
    elif summary.status == "warn":
        return f"Review UX CI warning: {len(summary.warnings)} warning(s)"
    else:
        return f"Review UX CI failed: {'; '.join(summary.blocking_issues) or 'see blocking issues'}"
