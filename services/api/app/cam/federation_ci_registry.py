"""
Federation CI Registry

CAM Dev Order 7Y: Federation baseline and CI summary indexes.

Provides:
  - In-memory baseline registry
  - In-memory CI summary history
  - Registration helpers
  - Latest summary retrieval

7Y invariants:
  - Baselines are immutable
  - CI summaries are historical records
  - No mutation of federation state

Core principle:
  Registry tracks baselines and CI evaluation history.
  It does not repair drift or mutate state.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from .federation_drift_baseline import (
    FederationDriftBaseline,
    validate_federation_drift_baseline,
)
from .federation_ci_enforcement import (
    FederationCIEnforcementSummary,
)


# ─────────────────────────────────────────────────────────────────────────────
# In-memory indexes
# ─────────────────────────────────────────────────────────────────────────────

FEDERATION_DRIFT_BASELINE_INDEX: Dict[str, FederationDriftBaseline] = {}
FEDERATION_CI_SUMMARY_INDEX: Dict[str, FederationCIEnforcementSummary] = {}

# Track summary order for latest retrieval
_FEDERATION_CI_SUMMARY_ORDER: List[str] = []


# ─────────────────────────────────────────────────────────────────────────────
# Baseline registration
# ─────────────────────────────────────────────────────────────────────────────

def register_federation_drift_baseline(
    baseline: FederationDriftBaseline,
) -> Tuple[bool, Optional[str]]:
    """
    Register a federation drift baseline.

    Baselines are immutable once registered.
    Returns (success, error_message).
    """
    # Validate baseline
    is_valid, issues = validate_federation_drift_baseline(baseline)
    if not is_valid:
        return False, f"Validation failed: {'; '.join(issues)}"

    # Check for duplicate
    if baseline.baseline_id in FEDERATION_DRIFT_BASELINE_INDEX:
        return False, f"Baseline {baseline.baseline_id} already exists — baselines are immutable"

    # Recompute hash before registration
    baseline.deterministic_baseline_hash = baseline.compute_hash()

    FEDERATION_DRIFT_BASELINE_INDEX[baseline.baseline_id] = baseline
    return True, None


def get_federation_drift_baseline(
    baseline_id: str,
) -> Optional[FederationDriftBaseline]:
    """Get a federation drift baseline by ID."""
    return FEDERATION_DRIFT_BASELINE_INDEX.get(baseline_id)


def list_federation_drift_baselines() -> List[FederationDriftBaseline]:
    """List all federation drift baselines."""
    return list(FEDERATION_DRIFT_BASELINE_INDEX.values())


def get_baseline_by_name(
    baseline_name: str,
) -> Optional[FederationDriftBaseline]:
    """Get a baseline by name (returns first match)."""
    for baseline in FEDERATION_DRIFT_BASELINE_INDEX.values():
        if baseline.baseline_name == baseline_name:
            return baseline
    return None


# ─────────────────────────────────────────────────────────────────────────────
# CI Summary registration
# ─────────────────────────────────────────────────────────────────────────────

def register_federation_ci_summary(
    summary: FederationCIEnforcementSummary,
) -> Tuple[bool, Optional[str]]:
    """
    Register a federation CI enforcement summary.

    Summaries are historical records.
    Returns (success, error_message).
    """
    # Basic validation
    if summary.execution_authorized:
        return False, "execution_authorized must be False"
    if summary.machine_output_allowed:
        return False, "machine_output_allowed must be False"

    # Recompute hash before registration
    summary.deterministic_summary_hash = summary.compute_hash()

    FEDERATION_CI_SUMMARY_INDEX[summary.summary_id] = summary
    _FEDERATION_CI_SUMMARY_ORDER.append(summary.summary_id)
    return True, None


def get_federation_ci_summary(
    summary_id: str,
) -> Optional[FederationCIEnforcementSummary]:
    """Get a federation CI summary by ID."""
    return FEDERATION_CI_SUMMARY_INDEX.get(summary_id)


def get_latest_federation_ci_summary() -> Optional[FederationCIEnforcementSummary]:
    """Get the most recently registered CI summary."""
    if not _FEDERATION_CI_SUMMARY_ORDER:
        return None
    latest_id = _FEDERATION_CI_SUMMARY_ORDER[-1]
    return FEDERATION_CI_SUMMARY_INDEX.get(latest_id)


def list_federation_ci_summaries() -> List[FederationCIEnforcementSummary]:
    """List all federation CI summaries in registration order."""
    return [
        FEDERATION_CI_SUMMARY_INDEX[sid]
        for sid in _FEDERATION_CI_SUMMARY_ORDER
        if sid in FEDERATION_CI_SUMMARY_INDEX
    ]


def list_federation_ci_summaries_by_status(
    status: str,
) -> List[FederationCIEnforcementSummary]:
    """List CI summaries filtered by status."""
    return [
        summary for summary in FEDERATION_CI_SUMMARY_INDEX.values()
        if summary.status == status
    ]


def list_summaries_for_baseline(
    baseline_id: str,
) -> List[FederationCIEnforcementSummary]:
    """List all CI summaries that used a specific baseline."""
    return [
        summary for summary in FEDERATION_CI_SUMMARY_INDEX.values()
        if summary.baseline_id == baseline_id
    ]


# ─────────────────────────────────────────────────────────────────────────────
# Query helpers
# ─────────────────────────────────────────────────────────────────────────────

def get_baseline_count() -> int:
    """Get count of registered baselines."""
    return len(FEDERATION_DRIFT_BASELINE_INDEX)


def get_ci_summary_count() -> int:
    """Get count of registered CI summaries."""
    return len(FEDERATION_CI_SUMMARY_INDEX)


def get_passing_summary_count() -> int:
    """Get count of passing CI summaries."""
    return len([s for s in FEDERATION_CI_SUMMARY_INDEX.values() if s.status == "pass"])


def get_failing_summary_count() -> int:
    """Get count of failing CI summaries."""
    return len([s for s in FEDERATION_CI_SUMMARY_INDEX.values() if s.status == "fail"])


def get_warning_summary_count() -> int:
    """Get count of warning CI summaries."""
    return len([s for s in FEDERATION_CI_SUMMARY_INDEX.values() if s.status == "warn"])


def get_ci_status_summary() -> Dict[str, Any]:
    """Get aggregated CI status summary."""
    summaries = list(FEDERATION_CI_SUMMARY_INDEX.values())
    latest = get_latest_federation_ci_summary()

    return {
        "total_baselines": len(FEDERATION_DRIFT_BASELINE_INDEX),
        "total_summaries": len(summaries),
        "passing_count": len([s for s in summaries if s.status == "pass"]),
        "warning_count": len([s for s in summaries if s.status == "warn"]),
        "failing_count": len([s for s in summaries if s.status == "fail"]),
        "latest_status": latest.status if latest else None,
        "latest_summary_id": latest.summary_id if latest else None,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Test helpers
# ─────────────────────────────────────────────────────────────────────────────

def clear_federation_ci_indexes_for_tests() -> None:
    """Clear all federation CI indexes for test isolation."""
    FEDERATION_DRIFT_BASELINE_INDEX.clear()
    FEDERATION_CI_SUMMARY_INDEX.clear()
    _FEDERATION_CI_SUMMARY_ORDER.clear()


def get_federation_ci_index_counts() -> Dict[str, int]:
    """Get counts of all federation CI indexes."""
    return {
        "baselines": len(FEDERATION_DRIFT_BASELINE_INDEX),
        "summaries": len(FEDERATION_CI_SUMMARY_INDEX),
    }
