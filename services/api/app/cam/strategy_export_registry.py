"""
Strategy Export Registry

CAM Dev Order 7U: In-memory registry for strategy/export compatibility.

Provides:
  - Evaluation registration and lookup
  - Package registration and lookup
  - CI summary generation
  - Adapter functions for translator capability registry

7U invariants:
  - No registered evaluation may authorize execution
  - No registered package may authorize machine output
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from app.cam.strategy_export_compatibility import (
    StrategyExportCompatibilityEvaluation,
    evaluate_strategy_export_compatibility,
)
from app.cam.review_safe_export_package import (
    ReviewSafeExportPackage,
    validate_package_for_review,
)


STRATEGY_EXPORT_COMPATIBILITY_INDEX: Dict[str, StrategyExportCompatibilityEvaluation] = {}

REVIEW_SAFE_EXPORT_PACKAGE_INDEX: Dict[str, ReviewSafeExportPackage] = {}

EVALUATIONS_BY_WORKSPACE_INDEX: Dict[str, List[str]] = {}
EVALUATIONS_BY_STRATEGY_INDEX: Dict[str, List[str]] = {}
PACKAGES_BY_WORKSPACE_INDEX: Dict[str, List[str]] = {}
PACKAGES_BY_STRATEGY_INDEX: Dict[str, List[str]] = {}


def register_strategy_export_compatibility(
    evaluation: StrategyExportCompatibilityEvaluation,
) -> StrategyExportCompatibilityEvaluation:
    """
    Register a strategy export compatibility evaluation.

    Args:
        evaluation: Evaluation to register

    Returns:
        The registered evaluation
    """
    evaluation.deterministic_evaluation_hash = evaluation.compute_hash()

    STRATEGY_EXPORT_COMPATIBILITY_INDEX[evaluation.evaluation_id] = evaluation

    if evaluation.workspace_id:
        if evaluation.workspace_id not in EVALUATIONS_BY_WORKSPACE_INDEX:
            EVALUATIONS_BY_WORKSPACE_INDEX[evaluation.workspace_id] = []
        if evaluation.evaluation_id not in EVALUATIONS_BY_WORKSPACE_INDEX[evaluation.workspace_id]:
            EVALUATIONS_BY_WORKSPACE_INDEX[evaluation.workspace_id].append(evaluation.evaluation_id)

    if evaluation.strategy_id:
        if evaluation.strategy_id not in EVALUATIONS_BY_STRATEGY_INDEX:
            EVALUATIONS_BY_STRATEGY_INDEX[evaluation.strategy_id] = []
        if evaluation.evaluation_id not in EVALUATIONS_BY_STRATEGY_INDEX[evaluation.strategy_id]:
            EVALUATIONS_BY_STRATEGY_INDEX[evaluation.strategy_id].append(evaluation.evaluation_id)

    return evaluation


def get_strategy_export_compatibility(
    evaluation_id: str,
) -> Optional[StrategyExportCompatibilityEvaluation]:
    """Get a compatibility evaluation by ID."""
    return STRATEGY_EXPORT_COMPATIBILITY_INDEX.get(evaluation_id)


def list_strategy_export_compatibilities() -> List[StrategyExportCompatibilityEvaluation]:
    """List all registered compatibility evaluations."""
    return list(STRATEGY_EXPORT_COMPATIBILITY_INDEX.values())


def list_evaluations_by_workspace(
    workspace_id: str,
) -> List[StrategyExportCompatibilityEvaluation]:
    """List all evaluations for a workspace."""
    eval_ids = EVALUATIONS_BY_WORKSPACE_INDEX.get(workspace_id, [])
    return [
        STRATEGY_EXPORT_COMPATIBILITY_INDEX[eid]
        for eid in eval_ids
        if eid in STRATEGY_EXPORT_COMPATIBILITY_INDEX
    ]


def list_evaluations_by_strategy(
    strategy_id: str,
) -> List[StrategyExportCompatibilityEvaluation]:
    """List all evaluations for a strategy."""
    eval_ids = EVALUATIONS_BY_STRATEGY_INDEX.get(strategy_id, [])
    return [
        STRATEGY_EXPORT_COMPATIBILITY_INDEX[eid]
        for eid in eval_ids
        if eid in STRATEGY_EXPORT_COMPATIBILITY_INDEX
    ]


def register_review_safe_export_package(
    package: ReviewSafeExportPackage,
) -> ReviewSafeExportPackage:
    """
    Register a review-safe export package.

    Args:
        package: Package to register

    Returns:
        The registered package
    """
    package.deterministic_package_hash = package.compute_hash()

    REVIEW_SAFE_EXPORT_PACKAGE_INDEX[package.package_id] = package

    if package.workspace_id:
        if package.workspace_id not in PACKAGES_BY_WORKSPACE_INDEX:
            PACKAGES_BY_WORKSPACE_INDEX[package.workspace_id] = []
        if package.package_id not in PACKAGES_BY_WORKSPACE_INDEX[package.workspace_id]:
            PACKAGES_BY_WORKSPACE_INDEX[package.workspace_id].append(package.package_id)

    if package.strategy_id:
        if package.strategy_id not in PACKAGES_BY_STRATEGY_INDEX:
            PACKAGES_BY_STRATEGY_INDEX[package.strategy_id] = []
        if package.package_id not in PACKAGES_BY_STRATEGY_INDEX[package.strategy_id]:
            PACKAGES_BY_STRATEGY_INDEX[package.strategy_id].append(package.package_id)

    return package


def get_review_safe_export_package(
    package_id: str,
) -> Optional[ReviewSafeExportPackage]:
    """Get a review-safe export package by ID."""
    return REVIEW_SAFE_EXPORT_PACKAGE_INDEX.get(package_id)


def list_review_safe_export_packages() -> List[ReviewSafeExportPackage]:
    """List all registered review-safe export packages."""
    return list(REVIEW_SAFE_EXPORT_PACKAGE_INDEX.values())


def list_packages_by_workspace(
    workspace_id: str,
) -> List[ReviewSafeExportPackage]:
    """List all packages for a workspace."""
    pkg_ids = PACKAGES_BY_WORKSPACE_INDEX.get(workspace_id, [])
    return [
        REVIEW_SAFE_EXPORT_PACKAGE_INDEX[pid]
        for pid in pkg_ids
        if pid in REVIEW_SAFE_EXPORT_PACKAGE_INDEX
    ]


def list_packages_by_strategy(
    strategy_id: str,
) -> List[ReviewSafeExportPackage]:
    """List all packages for a strategy."""
    pkg_ids = PACKAGES_BY_STRATEGY_INDEX.get(strategy_id, [])
    return [
        REVIEW_SAFE_EXPORT_PACKAGE_INDEX[pid]
        for pid in pkg_ids
        if pid in REVIEW_SAFE_EXPORT_PACKAGE_INDEX
    ]


def list_packages_by_review_status(
    review_status: str,
) -> List[ReviewSafeExportPackage]:
    """List all packages with a specific review status."""
    return [
        pkg for pkg in REVIEW_SAFE_EXPORT_PACKAGE_INDEX.values()
        if pkg.review_status == review_status
    ]


def get_packages_without_review() -> List[ReviewSafeExportPackage]:
    """Get packages that have not been reviewed."""
    return [
        pkg for pkg in REVIEW_SAFE_EXPORT_PACKAGE_INDEX.values()
        if pkg.review_status in ("draft", "pending_review")
    ]


CIStatus = Literal["pass", "warn", "fail"]


class StrategyExportCISummary(Dict[str, Any]):
    """CI summary for strategy/export compatibility health."""

    pass


def get_ci_summary() -> StrategyExportCISummary:
    """
    Generate CI summary for strategy/export compatibility health.

    Returns summary with:
      - total_evaluations
      - total_packages
      - red_count
      - yellow_count
      - green_count
      - package_without_review_count
      - packages_with_blocking_issues
      - status: pass|warn|fail

    Status:
      - fail: any RED evaluation or package with blocking issues
      - warn: YELLOW evaluations or packages lacking review
      - pass: all GREEN evaluations and packages are review-safe
    """
    total_evaluations = len(STRATEGY_EXPORT_COMPATIBILITY_INDEX)
    total_packages = len(REVIEW_SAFE_EXPORT_PACKAGE_INDEX)

    green_count = 0
    yellow_count = 0
    red_count = 0

    for evaluation in STRATEGY_EXPORT_COMPATIBILITY_INDEX.values():
        if evaluation.gate == "green":
            green_count += 1
        elif evaluation.gate == "yellow":
            yellow_count += 1
        elif evaluation.gate == "red":
            red_count += 1

    packages_without_review = get_packages_without_review()
    package_without_review_count = len(packages_without_review)

    packages_with_blocking_issues = [
        pkg for pkg in REVIEW_SAFE_EXPORT_PACKAGE_INDEX.values()
        if pkg.blocking_issues
    ]
    packages_with_blocking_issues_count = len(packages_with_blocking_issues)

    packages_approved = [
        pkg for pkg in REVIEW_SAFE_EXPORT_PACKAGE_INDEX.values()
        if pkg.review_status == "approved"
    ]
    packages_approved_count = len(packages_approved)

    status: CIStatus
    if red_count > 0 or packages_with_blocking_issues_count > 0:
        status = "fail"
    elif yellow_count > 0 or package_without_review_count > 0:
        status = "warn"
    else:
        status = "pass"

    evaluations_by_gate = {
        "green": green_count,
        "yellow": yellow_count,
        "red": red_count,
    }

    packages_by_review_status: Dict[str, int] = {}
    for pkg in REVIEW_SAFE_EXPORT_PACKAGE_INDEX.values():
        status_key = pkg.review_status
        packages_by_review_status[status_key] = packages_by_review_status.get(status_key, 0) + 1

    return StrategyExportCISummary(
        total_evaluations=total_evaluations,
        total_packages=total_packages,
        green_count=green_count,
        yellow_count=yellow_count,
        red_count=red_count,
        package_without_review_count=package_without_review_count,
        packages_with_blocking_issues=packages_with_blocking_issues_count,
        packages_approved=packages_approved_count,
        evaluations_by_gate=evaluations_by_gate,
        packages_by_review_status=packages_by_review_status,
        status=status,
    )


def clear_strategy_export_indexes() -> None:
    """Clear all indexes (for testing)."""
    STRATEGY_EXPORT_COMPATIBILITY_INDEX.clear()
    REVIEW_SAFE_EXPORT_PACKAGE_INDEX.clear()
    EVALUATIONS_BY_WORKSPACE_INDEX.clear()
    EVALUATIONS_BY_STRATEGY_INDEX.clear()
    PACKAGES_BY_WORKSPACE_INDEX.clear()
    PACKAGES_BY_STRATEGY_INDEX.clear()


def get_translator_capability_for_export(
    translator_id: str,
) -> Optional[Dict[str, Any]]:
    """
    Adapter function to query existing translator capability registry.

    Returns translator capability if found, None otherwise.
    """
    try:
        from app.cam.translator_capability_registry import (
            get_translator_capability,
        )
        return get_translator_capability(translator_id)
    except ImportError:
        return None
    except Exception:
        return None


def evaluate_translator_capability_compatibility(
    translator_id: str,
    modality_id: Optional[str] = None,
) -> tuple[bool, Optional[str]]:
    """
    Adapter function to evaluate translator capability compatibility.

    Args:
        translator_id: Translator to check
        modality_id: Optional modality to verify compatibility

    Returns:
        (is_compatible, error_message)
    """
    capability = get_translator_capability_for_export(translator_id)

    if not capability:
        return True, None

    if modality_id and "supported_modalities" in capability:
        if modality_id not in capability["supported_modalities"]:
            return False, f"Translator does not support modality '{modality_id}'"

    return True, None


def check_translator_quarantine_status(
    translator_id: str,
) -> tuple[bool, Optional[str]]:
    """
    Adapter function to check translator quarantine status.

    Args:
        translator_id: Translator to check

    Returns:
        (is_quarantined, reason)
    """
    try:
        from app.cam.translator_execution_quarantine import (
            is_translator_quarantined,
            get_quarantine_reason,
        )
        is_quarantined = is_translator_quarantined(translator_id)
        if is_quarantined:
            reason = get_quarantine_reason(translator_id)
            return True, reason
        return False, None
    except ImportError:
        return False, None
    except Exception:
        return False, None
