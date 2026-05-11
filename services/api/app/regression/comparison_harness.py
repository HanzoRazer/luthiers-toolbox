"""
Baseline Comparison Harness
===========================

Utilities for loading, saving, and comparing regression baselines.
Provides the framework for comparing current outputs against stored baselines.

MRP-1B: Regression & Behavioral Observability Infrastructure
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, TypeVar

from .signature_schema import (
    RegressionSignature,
    SignatureComparison,
    ComparisonResult,
)
from .blueprint_signature import BlueprintOutputSignature
from .invariants import (
    InvariantCheck,
    InvariantCheckResults,
    BLUEPRINT_READER_INVARIANTS,
    check_invariants,
)


# Type variable for signature classes
T = TypeVar("T", bound=RegressionSignature)


# Default baseline directory (relative to tests/regression_corpus/)
DEFAULT_BASELINE_DIR = Path(__file__).parent.parent.parent.parent.parent / "tests" / "regression_corpus" / "baselines"


@dataclass
class BaselineComparison:
    """
    Complete comparison result between current output and baseline.
    """
    # Identity
    artifact_id: str
    system_id: str
    baseline_path: Optional[str] = None

    # Comparison result
    comparison_result: ComparisonResult = ComparisonResult.BASELINE_MISSING
    signature_comparison: Optional[SignatureComparison] = None

    # Invariant results
    invariant_results: Optional[InvariantCheckResults] = None

    # Summary
    is_acceptable: bool = False
    blocking_issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    # Timestamps
    compared_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "artifact_id": self.artifact_id,
            "system_id": self.system_id,
            "baseline_path": self.baseline_path,
            "comparison_result": self.comparison_result.value,
            "signature_comparison": (
                self.signature_comparison.to_dict()
                if self.signature_comparison else None
            ),
            "invariant_results": (
                self.invariant_results.to_dict()
                if self.invariant_results else None
            ),
            "is_acceptable": self.is_acceptable,
            "blocking_issues": self.blocking_issues,
            "warnings": self.warnings,
            "compared_at": self.compared_at,
        }


def _get_baseline_path(
    artifact_id: str,
    system_id: str,
    baseline_dir: Optional[Path] = None,
) -> Path:
    """Get the baseline file path for an artifact."""
    base_dir = baseline_dir or DEFAULT_BASELINE_DIR
    return base_dir / system_id.lower() / f"{artifact_id}.json"


def load_baseline(
    artifact_id: str,
    system_id: str,
    signature_class: Type[T] = RegressionSignature,
    baseline_dir: Optional[Path] = None,
) -> Optional[T]:
    """
    Load a baseline signature from disk.

    Args:
        artifact_id: Identifier for the artifact
        system_id: System identifier (e.g., "BLUEPRINT_READER_MVP")
        signature_class: Class to deserialize into
        baseline_dir: Optional custom baseline directory

    Returns:
        Loaded signature, or None if baseline doesn't exist
    """
    path = _get_baseline_path(artifact_id, system_id, baseline_dir)

    if not path.exists():
        return None

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return signature_class.from_dict(data)


def save_baseline(
    signature: RegressionSignature,
    baseline_dir: Optional[Path] = None,
    overwrite: bool = False,
) -> Path:
    """
    Save a signature as a baseline.

    Args:
        signature: The signature to save
        baseline_dir: Optional custom baseline directory
        overwrite: If True, overwrite existing baseline

    Returns:
        Path where baseline was saved

    Raises:
        FileExistsError: If baseline exists and overwrite=False
    """
    path = _get_baseline_path(
        signature.artifact_id,
        signature.system_id,
        baseline_dir,
    )

    if path.exists() and not overwrite:
        raise FileExistsError(f"Baseline already exists: {path}")

    # Ensure directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(signature.to_dict(), f, indent=2)

    return path


def _compare_signatures(
    baseline: RegressionSignature,
    current: RegressionSignature,
    dimension_tolerance_pct: float = 5.0,
    count_tolerance_pct: float = 10.0,
) -> SignatureComparison:
    """
    Compare two signatures and detect drift.
    """
    comparison = SignatureComparison(
        result=ComparisonResult.MATCH,
        baseline_id=baseline.artifact_id,
        current_id=current.artifact_id,
    )

    warnings = []
    blocking = []

    # Compare dimensions
    for key in baseline.dimensions:
        base_val = baseline.dimensions[key]
        curr_val = current.dimensions.get(key, 0.0)
        delta = curr_val - base_val

        comparison.dimension_deltas[key] = delta

        if base_val != 0:
            drift_pct = abs(delta) / abs(base_val) * 100
            comparison.dimension_drift_pct[key] = drift_pct

            if drift_pct > dimension_tolerance_pct:
                warnings.append(f"Dimension '{key}' drifted {drift_pct:.1f}%")

    # Compare counts
    for key in baseline.counts:
        base_val = baseline.counts[key]
        curr_val = current.counts.get(key, 0)
        delta = curr_val - base_val

        comparison.count_deltas[key] = delta

        if base_val != 0 and abs(delta) / base_val * 100 > count_tolerance_pct:
            warnings.append(f"Count '{key}' changed by {delta}")

    # Compare flags
    for key in baseline.flags:
        base_val = baseline.flags[key]
        curr_val = current.flags.get(key, False)

        if base_val != curr_val:
            comparison.flag_changes[key] = (base_val, curr_val)
            warnings.append(f"Flag '{key}' changed: {base_val} -> {curr_val}")

    # Determine result
    if warnings:
        comparison.result = ComparisonResult.DRIFT
        comparison.is_acceptable = True  # Drift is warning-level
    if blocking:
        comparison.result = ComparisonResult.REGRESSION
        comparison.is_acceptable = False

    comparison.warnings = warnings
    comparison.blocking_issues = blocking

    return comparison


def compare_to_baseline(
    current: RegressionSignature,
    invariants: Optional[List[InvariantCheck]] = None,
    baseline_dir: Optional[Path] = None,
    dimension_tolerance_pct: float = 5.0,
    count_tolerance_pct: float = 10.0,
) -> BaselineComparison:
    """
    Compare a current signature against its stored baseline.

    Args:
        current: The current signature to compare
        invariants: Optional list of invariants to check
        baseline_dir: Optional custom baseline directory
        dimension_tolerance_pct: Tolerance for dimension drift
        count_tolerance_pct: Tolerance for count changes

    Returns:
        BaselineComparison with full comparison results
    """
    result = BaselineComparison(
        artifact_id=current.artifact_id,
        system_id=current.system_id,
    )

    # Determine signature class
    if isinstance(current, BlueprintOutputSignature):
        signature_class = BlueprintOutputSignature
        default_invariants = BLUEPRINT_READER_INVARIANTS
    else:
        signature_class = RegressionSignature
        default_invariants = []

    # Load baseline
    baseline_path = _get_baseline_path(
        current.artifact_id,
        current.system_id,
        baseline_dir,
    )
    result.baseline_path = str(baseline_path)

    baseline = load_baseline(
        current.artifact_id,
        current.system_id,
        signature_class,
        baseline_dir,
    )

    # Run invariant checks
    inv_checks = invariants if invariants is not None else default_invariants
    if inv_checks:
        result.invariant_results = check_invariants(
            current,
            inv_checks,
            current.system_id,
        )

        if result.invariant_results.has_critical_failures:
            result.blocking_issues.append("Critical invariant failures detected")

        if result.invariant_results.warning_failures > 0:
            result.warnings.append(
                f"{result.invariant_results.warning_failures} invariant warnings"
            )

    # Compare to baseline if available
    if baseline is None:
        result.comparison_result = ComparisonResult.BASELINE_MISSING
        result.warnings.append("No baseline found for comparison")
    else:
        sig_comparison = _compare_signatures(
            baseline,
            current,
            dimension_tolerance_pct,
            count_tolerance_pct,
        )
        result.signature_comparison = sig_comparison
        result.comparison_result = sig_comparison.result
        result.warnings.extend(sig_comparison.warnings)
        result.blocking_issues.extend(sig_comparison.blocking_issues)

    # Determine overall acceptability
    result.is_acceptable = (
        len(result.blocking_issues) == 0 and
        (result.invariant_results is None or
         not result.invariant_results.has_critical_failures)
    )

    return result
