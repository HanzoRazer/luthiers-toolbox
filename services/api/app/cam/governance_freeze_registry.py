"""
Governance Freeze Registry

CAM Dev Order 7Z: Registry for governance freezes, evaluations, and packages.

Provides:
  - In-memory freeze registry
  - In-memory evaluation registry
  - In-memory package registry
  - Registration helpers
  - Query helpers

7Z invariants:
  - human_review_required: always True
  - auto_release_authorized: always False
  - release_authorized: always False
  - execution_authorized: always False
  - machine_output_allowed: always False

Core principle:
  Registry tracks freezes, evaluations, and packages.
  It does not authorize release or execution.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from .governance_baseline_freeze import (
    GovernanceBaselineFreeze,
    validate_governance_baseline_freeze,
)
from .release_readiness_evaluation import ReleaseReadinessEvaluation
from .governance_release_package import GovernanceReleasePackage


# ─────────────────────────────────────────────────────────────────────────────
# In-memory indexes
# ─────────────────────────────────────────────────────────────────────────────

GOVERNANCE_FREEZE_INDEX: Dict[str, GovernanceBaselineFreeze] = {}
RELEASE_EVALUATION_INDEX: Dict[str, ReleaseReadinessEvaluation] = {}
GOVERNANCE_PACKAGE_INDEX: Dict[str, GovernanceReleasePackage] = {}

# Track order for latest retrieval
_GOVERNANCE_FREEZE_ORDER: List[str] = []
_RELEASE_EVALUATION_ORDER: List[str] = []
_GOVERNANCE_PACKAGE_ORDER: List[str] = []


# ─────────────────────────────────────────────────────────────────────────────
# Freeze registration
# ─────────────────────────────────────────────────────────────────────────────

def register_governance_freeze(
    freeze: GovernanceBaselineFreeze,
) -> Tuple[bool, Optional[str]]:
    """
    Register a governance baseline freeze.

    Returns (success, error_message).
    """
    # Validate freeze
    is_valid, issues = validate_governance_baseline_freeze(freeze)
    if not is_valid:
        return False, f"Validation failed: {'; '.join(issues)}"

    # Check for duplicate
    if freeze.freeze_id in GOVERNANCE_FREEZE_INDEX:
        return False, f"Freeze {freeze.freeze_id} already exists"

    # Recompute hash before registration
    freeze.deterministic_freeze_hash = freeze.compute_hash()

    GOVERNANCE_FREEZE_INDEX[freeze.freeze_id] = freeze
    _GOVERNANCE_FREEZE_ORDER.append(freeze.freeze_id)
    return True, None


def get_governance_freeze(
    freeze_id: str,
) -> Optional[GovernanceBaselineFreeze]:
    """Get a governance freeze by ID."""
    return GOVERNANCE_FREEZE_INDEX.get(freeze_id)


def get_latest_governance_freeze() -> Optional[GovernanceBaselineFreeze]:
    """Get the most recently registered freeze."""
    if not _GOVERNANCE_FREEZE_ORDER:
        return None
    latest_id = _GOVERNANCE_FREEZE_ORDER[-1]
    return GOVERNANCE_FREEZE_INDEX.get(latest_id)


def list_governance_freezes() -> List[GovernanceBaselineFreeze]:
    """List all governance freezes in registration order."""
    return [
        GOVERNANCE_FREEZE_INDEX[fid]
        for fid in _GOVERNANCE_FREEZE_ORDER
        if fid in GOVERNANCE_FREEZE_INDEX
    ]


def list_governance_freezes_by_status(
    status: str,
) -> List[GovernanceBaselineFreeze]:
    """List freezes filtered by status."""
    return [
        freeze for freeze in GOVERNANCE_FREEZE_INDEX.values()
        if freeze.status == status
    ]


def get_freeze_by_name(
    freeze_name: str,
) -> Optional[GovernanceBaselineFreeze]:
    """Get a freeze by name (returns first match)."""
    for freeze in GOVERNANCE_FREEZE_INDEX.values():
        if freeze.freeze_name == freeze_name:
            return freeze
    return None


def update_freeze_status(
    freeze_id: str,
    new_status: str,
    reviewer_note: Optional[str] = None,
) -> Tuple[bool, Optional[str]]:
    """
    Update a freeze's status.

    Valid transitions:
      - pending -> reviewed
      - reviewed -> approved
      - reviewed -> rejected

    Returns (success, error_message).
    """
    freeze = GOVERNANCE_FREEZE_INDEX.get(freeze_id)
    if not freeze:
        return False, f"Freeze {freeze_id} not found"

    valid_transitions = {
        "pending": ["reviewed"],
        "reviewed": ["approved", "rejected"],
        "approved": [],
        "rejected": [],
    }

    if new_status not in valid_transitions.get(freeze.status, []):
        return False, f"Invalid status transition from {freeze.status} to {new_status}"

    freeze.status = new_status
    if reviewer_note:
        freeze.reviewer_notes.append(reviewer_note)

    from datetime import datetime, timezone
    freeze.reviewed_at = datetime.now(timezone.utc)

    # Recompute hash after status change
    freeze.deterministic_freeze_hash = freeze.compute_hash()

    return True, None


# ─────────────────────────────────────────────────────────────────────────────
# Evaluation registration
# ─────────────────────────────────────────────────────────────────────────────

def register_release_evaluation(
    evaluation: ReleaseReadinessEvaluation,
) -> Tuple[bool, Optional[str]]:
    """
    Register a release readiness evaluation.

    Returns (success, error_message).
    """
    # Validate 7Z invariants
    if not evaluation.human_review_required:
        return False, "human_review_required must be True"
    if evaluation.auto_release_authorized:
        return False, "auto_release_authorized must be False"
    if evaluation.release_authorized:
        return False, "release_authorized must be False"
    if evaluation.execution_authorized:
        return False, "execution_authorized must be False"
    if evaluation.machine_output_allowed:
        return False, "machine_output_allowed must be False"

    # Recompute hash before registration
    evaluation.deterministic_evaluation_hash = evaluation.compute_hash()

    RELEASE_EVALUATION_INDEX[evaluation.evaluation_id] = evaluation
    _RELEASE_EVALUATION_ORDER.append(evaluation.evaluation_id)
    return True, None


def get_release_evaluation(
    evaluation_id: str,
) -> Optional[ReleaseReadinessEvaluation]:
    """Get a release evaluation by ID."""
    return RELEASE_EVALUATION_INDEX.get(evaluation_id)


def get_latest_release_evaluation() -> Optional[ReleaseReadinessEvaluation]:
    """Get the most recently registered evaluation."""
    if not _RELEASE_EVALUATION_ORDER:
        return None
    latest_id = _RELEASE_EVALUATION_ORDER[-1]
    return RELEASE_EVALUATION_INDEX.get(latest_id)


def list_release_evaluations() -> List[ReleaseReadinessEvaluation]:
    """List all release evaluations in registration order."""
    return [
        RELEASE_EVALUATION_INDEX[eid]
        for eid in _RELEASE_EVALUATION_ORDER
        if eid in RELEASE_EVALUATION_INDEX
    ]


def list_evaluations_for_freeze(
    freeze_id: str,
) -> List[ReleaseReadinessEvaluation]:
    """List all evaluations for a specific freeze."""
    return [
        evaluation for evaluation in RELEASE_EVALUATION_INDEX.values()
        if evaluation.freeze_id == freeze_id
    ]


def list_evaluations_by_status(
    status: str,
) -> List[ReleaseReadinessEvaluation]:
    """List evaluations filtered by readiness status."""
    return [
        evaluation for evaluation in RELEASE_EVALUATION_INDEX.values()
        if evaluation.readiness_status == status
    ]


# ─────────────────────────────────────────────────────────────────────────────
# Package registration
# ─────────────────────────────────────────────────────────────────────────────

def register_governance_package(
    package: GovernanceReleasePackage,
) -> Tuple[bool, Optional[str]]:
    """
    Register a governance release package.

    Returns (success, error_message).
    """
    # Validate 7Z invariants
    if not package.human_review_required:
        return False, "human_review_required must be True"
    if package.auto_release_authorized:
        return False, "auto_release_authorized must be False"
    if package.release_authorized:
        return False, "release_authorized must be False"
    if package.execution_authorized:
        return False, "execution_authorized must be False"
    if package.machine_output_allowed:
        return False, "machine_output_allowed must be False"

    # Recompute hash before registration
    package.deterministic_package_hash = package.compute_hash()

    GOVERNANCE_PACKAGE_INDEX[package.package_id] = package
    _GOVERNANCE_PACKAGE_ORDER.append(package.package_id)
    return True, None


def get_governance_package(
    package_id: str,
) -> Optional[GovernanceReleasePackage]:
    """Get a governance package by ID."""
    return GOVERNANCE_PACKAGE_INDEX.get(package_id)


def get_latest_governance_package() -> Optional[GovernanceReleasePackage]:
    """Get the most recently registered package."""
    if not _GOVERNANCE_PACKAGE_ORDER:
        return None
    latest_id = _GOVERNANCE_PACKAGE_ORDER[-1]
    return GOVERNANCE_PACKAGE_INDEX.get(latest_id)


def list_governance_packages() -> List[GovernanceReleasePackage]:
    """List all governance packages in registration order."""
    return [
        GOVERNANCE_PACKAGE_INDEX[pid]
        for pid in _GOVERNANCE_PACKAGE_ORDER
        if pid in GOVERNANCE_PACKAGE_INDEX
    ]


def list_packages_for_freeze(
    freeze_id: str,
) -> List[GovernanceReleasePackage]:
    """List all packages for a specific freeze."""
    return [
        package for package in GOVERNANCE_PACKAGE_INDEX.values()
        if package.freeze_id == freeze_id
    ]


def list_packages_by_readiness(
    readiness_status: str,
) -> List[GovernanceReleasePackage]:
    """List packages filtered by readiness status."""
    return [
        package for package in GOVERNANCE_PACKAGE_INDEX.values()
        if package.readiness_status == readiness_status
    ]


# ─────────────────────────────────────────────────────────────────────────────
# Query helpers
# ─────────────────────────────────────────────────────────────────────────────

def get_governance_freeze_count() -> int:
    """Get count of registered freezes."""
    return len(GOVERNANCE_FREEZE_INDEX)


def get_release_evaluation_count() -> int:
    """Get count of registered evaluations."""
    return len(RELEASE_EVALUATION_INDEX)


def get_governance_package_count() -> int:
    """Get count of registered packages."""
    return len(GOVERNANCE_PACKAGE_INDEX)


def get_ready_evaluation_count() -> int:
    """Get count of evaluations with ready status."""
    return len([e for e in RELEASE_EVALUATION_INDEX.values() if e.readiness_status == "ready"])


def get_blocked_evaluation_count() -> int:
    """Get count of evaluations with blocked status."""
    return len([e for e in RELEASE_EVALUATION_INDEX.values() if e.readiness_status == "blocked"])


def get_pending_freeze_count() -> int:
    """Get count of pending freezes."""
    return len([f for f in GOVERNANCE_FREEZE_INDEX.values() if f.status == "pending"])


def get_reviewed_freeze_count() -> int:
    """Get count of reviewed freezes."""
    return len([f for f in GOVERNANCE_FREEZE_INDEX.values() if f.status == "reviewed"])


def get_governance_status_summary() -> Dict[str, Any]:
    """Get aggregated governance status summary."""
    freezes = list(GOVERNANCE_FREEZE_INDEX.values())
    evaluations = list(RELEASE_EVALUATION_INDEX.values())
    packages = list(GOVERNANCE_PACKAGE_INDEX.values())

    latest_freeze = get_latest_governance_freeze()
    latest_evaluation = get_latest_release_evaluation()
    latest_package = get_latest_governance_package()

    return {
        "total_freezes": len(freezes),
        "pending_freezes": len([f for f in freezes if f.status == "pending"]),
        "reviewed_freezes": len([f for f in freezes if f.status == "reviewed"]),
        "approved_freezes": len([f for f in freezes if f.status == "approved"]),
        "rejected_freezes": len([f for f in freezes if f.status == "rejected"]),
        "total_evaluations": len(evaluations),
        "ready_evaluations": len([e for e in evaluations if e.readiness_status == "ready"]),
        "not_ready_evaluations": len([e for e in evaluations if e.readiness_status == "not_ready"]),
        "blocked_evaluations": len([e for e in evaluations if e.readiness_status == "blocked"]),
        "total_packages": len(packages),
        "latest_freeze_id": latest_freeze.freeze_id if latest_freeze else None,
        "latest_freeze_status": latest_freeze.status if latest_freeze else None,
        "latest_evaluation_id": latest_evaluation.evaluation_id if latest_evaluation else None,
        "latest_evaluation_status": latest_evaluation.readiness_status if latest_evaluation else None,
        "latest_package_id": latest_package.package_id if latest_package else None,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Test helpers
# ─────────────────────────────────────────────────────────────────────────────

def clear_governance_freeze_indexes_for_tests() -> None:
    """Clear all governance freeze indexes for test isolation."""
    GOVERNANCE_FREEZE_INDEX.clear()
    RELEASE_EVALUATION_INDEX.clear()
    GOVERNANCE_PACKAGE_INDEX.clear()
    _GOVERNANCE_FREEZE_ORDER.clear()
    _RELEASE_EVALUATION_ORDER.clear()
    _GOVERNANCE_PACKAGE_ORDER.clear()


def get_governance_freeze_index_counts() -> Dict[str, int]:
    """Get counts of all governance freeze indexes."""
    return {
        "freezes": len(GOVERNANCE_FREEZE_INDEX),
        "evaluations": len(RELEASE_EVALUATION_INDEX),
        "packages": len(GOVERNANCE_PACKAGE_INDEX),
    }
