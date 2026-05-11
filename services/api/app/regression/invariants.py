"""
Invariant Definitions
=====================

Defines invariants that must hold true for protected system outputs.
Invariants are boolean checks that detect behavioral violations.

MRP-1B: Regression & Behavioral Observability Infrastructure
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from .blueprint_signature import BlueprintOutputSignature


class InvariantSeverity(Enum):
    """Severity level for invariant violations."""
    CRITICAL = "critical"  # Blocks release
    WARNING = "warning"    # Requires review
    INFO = "info"          # Informational only


@dataclass
class InvariantCheck:
    """
    Definition of a single invariant check.
    """
    id: str
    description: str
    severity: InvariantSeverity
    check_fn: Callable[[Any], bool]
    failure_message: str
    system_id: str = ""

    def check(self, signature: Any) -> "InvariantResult":
        """Run the invariant check against a signature."""
        try:
            passed = self.check_fn(signature)
            return InvariantResult(
                invariant_id=self.id,
                passed=passed,
                severity=self.severity,
                message=None if passed else self.failure_message,
            )
        except Exception as e:
            return InvariantResult(
                invariant_id=self.id,
                passed=False,
                severity=InvariantSeverity.CRITICAL,
                message=f"Invariant check error: {e}",
            )


@dataclass
class InvariantResult:
    """Result of a single invariant check."""
    invariant_id: str
    passed: bool
    severity: InvariantSeverity
    message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "invariant_id": self.invariant_id,
            "passed": self.passed,
            "severity": self.severity.value,
            "message": self.message,
        }


# ─── Blueprint Reader Invariants ────────────────────────────────────────────

def _check_dimensions_positive(sig: BlueprintOutputSignature) -> bool:
    """Body dimensions must be positive."""
    return sig.body_width_mm > 0 and sig.body_height_mm > 0


def _check_dimensions_plausible(sig: BlueprintOutputSignature) -> bool:
    """Body dimensions must be within plausible guitar range."""
    # Smallest: ukulele ~150mm, Largest: bass ~600mm
    return (
        100 < sig.body_width_mm < 700 and
        150 < sig.body_height_mm < 800
    )


def _check_aspect_ratio_plausible(sig: BlueprintOutputSignature) -> bool:
    """Body aspect ratio must be plausible for instruments."""
    if sig.body_width_mm <= 0 or sig.body_height_mm <= 0:
        return False
    ratio = sig.body_height_mm / sig.body_width_mm
    # Guitar bodies: roughly 1.0 to 2.0 height/width ratio
    return 0.8 < ratio < 2.5


def _check_dxf_not_empty(sig: BlueprintOutputSignature) -> bool:
    """DXF output must contain entities."""
    return sig.dxf_entity_count > 0


def _check_dxf_entity_count_reasonable(sig: BlueprintOutputSignature) -> bool:
    """DXF entity count must be reasonable (not explosion or empty)."""
    return 10 < sig.dxf_entity_count < 100000


def _check_has_closed_contours(sig: BlueprintOutputSignature) -> bool:
    """DXF should have at least one closed contour for body outline."""
    return sig.dxf_closed_contours > 0


def _check_selection_valid(sig: BlueprintOutputSignature) -> bool:
    """If selection occurred, index must be valid."""
    if sig.candidate_count == 0:
        return True  # No selection needed
    return 0 <= sig.selected_index < sig.candidate_count


def _check_confidence_bounded(sig: BlueprintOutputSignature) -> bool:
    """Confidence values must be in [0, 1] range."""
    return (
        0.0 <= sig.selection_score <= 1.0 and
        0.0 <= sig.recommendation_confidence <= 1.0
    )


def _check_accepted_has_artifacts(sig: BlueprintOutputSignature) -> bool:
    """If recommendation is 'accept', artifacts must be present."""
    if sig.recommendation_action != "accept":
        return True  # Only check accepted results
    return sig.dxf_entity_count > 0 and sig.svg_present


# Define all Blueprint Reader invariants
BLUEPRINT_READER_INVARIANTS: List[InvariantCheck] = [
    InvariantCheck(
        id="BR_INV_001",
        description="Body dimensions must be positive",
        severity=InvariantSeverity.CRITICAL,
        check_fn=_check_dimensions_positive,
        failure_message="Body width or height is zero or negative",
        system_id="BLUEPRINT_READER_MVP",
    ),
    InvariantCheck(
        id="BR_INV_002",
        description="Body dimensions must be plausible for instruments",
        severity=InvariantSeverity.WARNING,
        check_fn=_check_dimensions_plausible,
        failure_message="Body dimensions outside plausible instrument range (100-700mm width, 150-800mm height)",
        system_id="BLUEPRINT_READER_MVP",
    ),
    InvariantCheck(
        id="BR_INV_003",
        description="Body aspect ratio must be plausible",
        severity=InvariantSeverity.WARNING,
        check_fn=_check_aspect_ratio_plausible,
        failure_message="Body aspect ratio outside plausible range (0.8-2.5)",
        system_id="BLUEPRINT_READER_MVP",
    ),
    InvariantCheck(
        id="BR_INV_004",
        description="DXF output must not be empty",
        severity=InvariantSeverity.CRITICAL,
        check_fn=_check_dxf_not_empty,
        failure_message="DXF output contains no entities",
        system_id="BLUEPRINT_READER_MVP",
    ),
    InvariantCheck(
        id="BR_INV_005",
        description="DXF entity count must be reasonable",
        severity=InvariantSeverity.WARNING,
        check_fn=_check_dxf_entity_count_reasonable,
        failure_message="DXF entity count outside reasonable range (10-100000)",
        system_id="BLUEPRINT_READER_MVP",
    ),
    InvariantCheck(
        id="BR_INV_006",
        description="DXF should have closed contours",
        severity=InvariantSeverity.WARNING,
        check_fn=_check_has_closed_contours,
        failure_message="No closed contours detected in DXF output",
        system_id="BLUEPRINT_READER_MVP",
    ),
    InvariantCheck(
        id="BR_INV_007",
        description="Selection index must be valid",
        severity=InvariantSeverity.CRITICAL,
        check_fn=_check_selection_valid,
        failure_message="Selected index out of bounds for candidate count",
        system_id="BLUEPRINT_READER_MVP",
    ),
    InvariantCheck(
        id="BR_INV_008",
        description="Confidence values must be bounded [0, 1]",
        severity=InvariantSeverity.CRITICAL,
        check_fn=_check_confidence_bounded,
        failure_message="Confidence value outside [0, 1] range",
        system_id="BLUEPRINT_READER_MVP",
    ),
    InvariantCheck(
        id="BR_INV_009",
        description="Accepted results must have artifacts",
        severity=InvariantSeverity.CRITICAL,
        check_fn=_check_accepted_has_artifacts,
        failure_message="Recommendation is 'accept' but artifacts are missing",
        system_id="BLUEPRINT_READER_MVP",
    ),
]


@dataclass
class InvariantCheckResults:
    """Results of running all invariants for a system."""
    system_id: str
    total_checks: int
    passed: int
    failed: int
    critical_failures: int
    warning_failures: int
    results: List[InvariantResult] = field(default_factory=list)

    @property
    def all_passed(self) -> bool:
        return self.failed == 0

    @property
    def has_critical_failures(self) -> bool:
        return self.critical_failures > 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "system_id": self.system_id,
            "total_checks": self.total_checks,
            "passed": self.passed,
            "failed": self.failed,
            "critical_failures": self.critical_failures,
            "warning_failures": self.warning_failures,
            "all_passed": self.all_passed,
            "has_critical_failures": self.has_critical_failures,
            "results": [r.to_dict() for r in self.results],
        }


def check_invariants(
    signature: Any,
    invariants: List[InvariantCheck],
    system_id: str = "",
) -> InvariantCheckResults:
    """
    Run all invariant checks against a signature.

    Args:
        signature: The signature to check
        invariants: List of invariant checks to run
        system_id: System identifier for the results

    Returns:
        InvariantCheckResults with all check outcomes
    """
    results = []
    passed = 0
    failed = 0
    critical = 0
    warnings = 0

    for invariant in invariants:
        result = invariant.check(signature)
        results.append(result)

        if result.passed:
            passed += 1
        else:
            failed += 1
            if result.severity == InvariantSeverity.CRITICAL:
                critical += 1
            elif result.severity == InvariantSeverity.WARNING:
                warnings += 1

    return InvariantCheckResults(
        system_id=system_id or invariants[0].system_id if invariants else "",
        total_checks=len(invariants),
        passed=passed,
        failed=failed,
        critical_failures=critical,
        warning_failures=warnings,
        results=results,
    )
