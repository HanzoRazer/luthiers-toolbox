"""
Review UX CI Registry

CAM Dev Order 8D: Registry for review UX baselines and CI enforcement summaries.

Provides:
  - In-memory baseline registry
  - In-memory CI summary registry
  - Registration helpers
  - Query helpers
  - CI status aggregation

8D invariants:
  - execution_authorized: always False
  - machine_output_allowed: always False
  - auto_approval_allowed: always False

Core principle:
  Registry tracks baselines and enforcement state for human review.
  It does not authorize execution, machine output, or auto-approval.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from .review_ux_baseline import (
    ReviewUXBaseline,
    validate_review_ux_baseline,
    get_baseline_summary,
)
from .review_ux_ci_enforcement import (
    ReviewUXCIEnforcementSummary,
    ReviewUXCIStatus,
    evaluate_review_ux_against_baseline,
    get_ci_enforcement_summary,
)
from .review_ux_registry import (
    list_review_panels,
    list_provenance_explanations,
    list_review_attention_priorities,
)


# ─────────────────────────────────────────────────────────────────────────────
# In-memory indexes
# ─────────────────────────────────────────────────────────────────────────────

REVIEW_UX_BASELINE_INDEX: Dict[str, ReviewUXBaseline] = {}
REVIEW_UX_CI_SUMMARY_INDEX: Dict[str, ReviewUXCIEnforcementSummary] = {}

_REVIEW_UX_BASELINE_ORDER: List[str] = []
_REVIEW_UX_CI_SUMMARY_ORDER: List[str] = []


# ─────────────────────────────────────────────────────────────────────────────
# Baseline registration
# ─────────────────────────────────────────────────────────────────────────────

def register_review_ux_baseline(
    baseline: ReviewUXBaseline,
) -> Tuple[bool, Optional[str]]:
    """
    Register a review UX baseline.

    Returns (success, error_message).
    """
    is_valid, issues = validate_review_ux_baseline(baseline)
    if not is_valid:
        return False, f"Validation failed: {'; '.join(issues)}"

    if baseline.baseline_id in REVIEW_UX_BASELINE_INDEX:
        return False, f"Baseline {baseline.baseline_id} already exists"

    baseline.deterministic_baseline_hash = baseline.compute_hash()

    REVIEW_UX_BASELINE_INDEX[baseline.baseline_id] = baseline
    _REVIEW_UX_BASELINE_ORDER.append(baseline.baseline_id)
    return True, None


def get_review_ux_baseline(
    baseline_id: str,
) -> Optional[ReviewUXBaseline]:
    """Get a baseline by ID."""
    return REVIEW_UX_BASELINE_INDEX.get(baseline_id)


def get_latest_review_ux_baseline() -> Optional[ReviewUXBaseline]:
    """Get the most recently registered baseline."""
    if not _REVIEW_UX_BASELINE_ORDER:
        return None
    latest_id = _REVIEW_UX_BASELINE_ORDER[-1]
    return REVIEW_UX_BASELINE_INDEX.get(latest_id)


def list_review_ux_baselines() -> List[ReviewUXBaseline]:
    """List all baselines in registration order."""
    return [
        REVIEW_UX_BASELINE_INDEX[bid]
        for bid in _REVIEW_UX_BASELINE_ORDER
        if bid in REVIEW_UX_BASELINE_INDEX
    ]


def get_review_ux_baseline_count() -> int:
    """Get total baseline count."""
    return len(REVIEW_UX_BASELINE_INDEX)


# ─────────────────────────────────────────────────────────────────────────────
# CI summary registration
# ─────────────────────────────────────────────────────────────────────────────

def register_review_ux_ci_summary(
    summary: ReviewUXCIEnforcementSummary,
) -> Tuple[bool, Optional[str]]:
    """
    Register a CI enforcement summary.

    Returns (success, error_message).
    """
    if summary.execution_authorized:
        return False, "execution_authorized must be False"
    if summary.machine_output_allowed:
        return False, "machine_output_allowed must be False"
    if summary.auto_approval_allowed:
        return False, "auto_approval_allowed must be False"

    if summary.summary_id in REVIEW_UX_CI_SUMMARY_INDEX:
        return False, f"Summary {summary.summary_id} already exists"

    summary.deterministic_summary_hash = summary.compute_hash()

    REVIEW_UX_CI_SUMMARY_INDEX[summary.summary_id] = summary
    _REVIEW_UX_CI_SUMMARY_ORDER.append(summary.summary_id)
    return True, None


def get_review_ux_ci_summary(
    summary_id: str,
) -> Optional[ReviewUXCIEnforcementSummary]:
    """Get a CI summary by ID."""
    return REVIEW_UX_CI_SUMMARY_INDEX.get(summary_id)


def get_latest_review_ux_ci_summary() -> Optional[ReviewUXCIEnforcementSummary]:
    """Get the most recent CI summary."""
    if not _REVIEW_UX_CI_SUMMARY_ORDER:
        return None
    latest_id = _REVIEW_UX_CI_SUMMARY_ORDER[-1]
    return REVIEW_UX_CI_SUMMARY_INDEX.get(latest_id)


def list_review_ux_ci_summaries() -> List[ReviewUXCIEnforcementSummary]:
    """List all CI summaries in registration order."""
    return [
        REVIEW_UX_CI_SUMMARY_INDEX[sid]
        for sid in _REVIEW_UX_CI_SUMMARY_ORDER
        if sid in REVIEW_UX_CI_SUMMARY_INDEX
    ]


def list_ci_summaries_by_status(
    status: ReviewUXCIStatus,
) -> List[ReviewUXCIEnforcementSummary]:
    """List CI summaries by status."""
    return [
        s for s in list_review_ux_ci_summaries()
        if s.status == status
    ]


def get_review_ux_ci_summary_count() -> int:
    """Get total CI summary count."""
    return len(REVIEW_UX_CI_SUMMARY_INDEX)


# ─────────────────────────────────────────────────────────────────────────────
# CI enforcement evaluation
# ─────────────────────────────────────────────────────────────────────────────

def evaluate_current_review_ux_state(
    baseline: Optional[ReviewUXBaseline] = None,
) -> ReviewUXCIEnforcementSummary:
    """
    Evaluate current review UX state against optional baseline.

    Reads from 8C registries:
      - list_review_panels()
      - list_provenance_explanations()
      - list_review_attention_priorities()

    If no baseline provided, uses latest registered baseline.
    If no baseline exists, evaluates without threshold comparison.
    """
    panels = list_review_panels()
    explanations = list_provenance_explanations()
    priorities = list_review_attention_priorities()

    if baseline is None:
        baseline = get_latest_review_ux_baseline()

    summary = evaluate_review_ux_against_baseline(
        panels=panels,
        explanations=explanations,
        priorities=priorities,
        baseline=baseline,
    )

    return summary


def run_review_ux_ci_check(
    baseline_id: Optional[str] = None,
) -> Tuple[ReviewUXCIEnforcementSummary, bool, Optional[str]]:
    """
    Run CI check and register the result.

    Returns (summary, success, error_message).
    """
    baseline = None
    if baseline_id:
        baseline = get_review_ux_baseline(baseline_id)
        if not baseline:
            return None, False, f"Baseline {baseline_id} not found"

    summary = evaluate_current_review_ux_state(baseline)

    success, error = register_review_ux_ci_summary(summary)
    if not success:
        return summary, False, error

    return summary, True, None


# ─────────────────────────────────────────────────────────────────────────────
# CI status aggregation
# ─────────────────────────────────────────────────────────────────────────────

def build_review_ux_ci_report() -> Dict[str, Any]:
    """
    Build CI report for review UX state.

    Returns report object with:
      - total_baselines
      - total_ci_summaries
      - pass_count
      - warn_count
      - fail_count
      - latest_status
      - latest_blocking_issue_count
      - latest_warning_count
      - status: pass|warn|fail
      - blocking_issues
      - warnings
    """
    baselines = list_review_ux_baselines()
    summaries = list_review_ux_ci_summaries()

    pass_count = sum(1 for s in summaries if s.status == "pass")
    warn_count = sum(1 for s in summaries if s.status == "warn")
    fail_count = sum(1 for s in summaries if s.status == "fail")

    latest = get_latest_review_ux_ci_summary()

    blocking_issues: List[str] = []
    warnings: List[str] = []

    if latest:
        if latest.status == "fail":
            blocking_issues.append(
                f"Latest CI check failed: {len(latest.blocking_issues)} blocking issue(s)"
            )
        if latest.baseline_exceeded:
            blocking_issues.append("Baseline thresholds exceeded")

        if latest.status == "warn":
            warnings.append(
                f"Latest CI check has warnings: {len(latest.warnings)} warning(s)"
            )

    if fail_count > 0:
        blocking_issues.append(f"{fail_count} CI check(s) with FAIL status")

    if warn_count > 0:
        warnings.append(f"{warn_count} CI check(s) with WARN status")

    # Determine overall status
    status: ReviewUXCIStatus
    if blocking_issues:
        status = "fail"
    elif warnings:
        status = "warn"
    else:
        status = "pass"

    return {
        "total_baselines": len(baselines),
        "total_ci_summaries": len(summaries),
        "pass_count": pass_count,
        "warn_count": warn_count,
        "fail_count": fail_count,
        "latest_status": latest.status if latest else None,
        "latest_blocking_issue_count": len(latest.blocking_issues) if latest else 0,
        "latest_warning_count": len(latest.warnings) if latest else 0,
        "status": status,
        "blocking_issues": blocking_issues,
        "warnings": warnings,
    }


def get_review_ux_ci_status_summary() -> Dict[str, Any]:
    """Get aggregated status summary."""
    baselines = list_review_ux_baselines()
    summaries = list_review_ux_ci_summaries()

    latest_baseline = get_latest_review_ux_baseline()
    latest_summary = get_latest_review_ux_ci_summary()

    return {
        "total_baselines": len(baselines),
        "total_ci_summaries": len(summaries),
        "pass_count": sum(1 for s in summaries if s.status == "pass"),
        "warn_count": sum(1 for s in summaries if s.status == "warn"),
        "fail_count": sum(1 for s in summaries if s.status == "fail"),
        "latest_baseline_id": latest_baseline.baseline_id if latest_baseline else None,
        "latest_baseline_name": latest_baseline.baseline_name if latest_baseline else None,
        "latest_summary_id": latest_summary.summary_id if latest_summary else None,
        "latest_summary_status": latest_summary.status if latest_summary else None,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Test helpers
# ─────────────────────────────────────────────────────────────────────────────

def clear_review_ux_ci_indexes_for_tests() -> None:
    """Clear all indexes for testing."""
    REVIEW_UX_BASELINE_INDEX.clear()
    REVIEW_UX_CI_SUMMARY_INDEX.clear()
    _REVIEW_UX_BASELINE_ORDER.clear()
    _REVIEW_UX_CI_SUMMARY_ORDER.clear()


def get_review_ux_ci_index_counts() -> Dict[str, int]:
    """Get index counts for debugging."""
    return {
        "baselines": len(REVIEW_UX_BASELINE_INDEX),
        "ci_summaries": len(REVIEW_UX_CI_SUMMARY_INDEX),
        "baseline_order": len(_REVIEW_UX_BASELINE_ORDER),
        "ci_summary_order": len(_REVIEW_UX_CI_SUMMARY_ORDER),
    }
