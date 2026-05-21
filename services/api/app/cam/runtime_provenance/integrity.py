"""
Provenance Integrity Verification.

Sprint: MRP-5N
Status: PROTOTYPE

Verifies integrity of provenance records and replay bundles.
Detects tampering, corruption, or missing data.

ARCHITECTURAL PRINCIPLE:
    Integrity verification is deterministic.
    It observes, it does not repair.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .contracts import (
    RuntimeArtifactProvenance,
    RuntimeReplayBundle,
    RuntimeTraceEvent,
    TraceEventType,
)
from .exceptions import IntegrityError
from .serialization import stable_hash_model, verify_hash_match


@dataclass
class IntegrityCheckResult:
    """Result of a single integrity check."""

    check_name: str
    passed: bool
    message: str
    expected: Optional[str] = None
    actual: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {
            "check_name": self.check_name,
            "passed": self.passed,
            "message": self.message,
            "details": self.details,
        }
        if self.expected:
            result["expected"] = self.expected
        if self.actual:
            result["actual"] = self.actual
        return result


@dataclass
class BundleIntegrityResult:
    """Result of complete bundle integrity verification."""

    passed: bool
    bundle_id: str
    checks: List[IntegrityCheckResult] = field(default_factory=list)
    message: str = ""

    @property
    def failed_checks(self) -> List[IntegrityCheckResult]:
        """Get list of failed checks."""
        return [c for c in self.checks if not c.passed]

    @property
    def passed_checks(self) -> List[IntegrityCheckResult]:
        """Get list of passed checks."""
        return [c for c in self.checks if c.passed]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "passed": self.passed,
            "bundle_id": self.bundle_id,
            "checks": [c.to_dict() for c in self.checks],
            "message": self.message,
            "passed_count": len(self.passed_checks),
            "failed_count": len(self.failed_checks),
        }


def verify_artifact_hash(
    content_bytes: bytes,
    expected_hash: str,
) -> IntegrityCheckResult:
    """
    Verify artifact content matches expected hash.

    Args:
        content_bytes: Artifact content
        expected_hash: Expected hash from provenance

    Returns:
        IntegrityCheckResult
    """
    if not expected_hash:
        return IntegrityCheckResult(
            check_name="artifact_hash",
            passed=False,
            message="Expected hash is empty",
        )

    matches = verify_hash_match(content_bytes, expected_hash)

    if matches:
        return IntegrityCheckResult(
            check_name="artifact_hash",
            passed=True,
            message="Artifact hash matches",
            expected=expected_hash[:16] + "...",
        )

    from .serialization import stable_hash_bytes
    actual = stable_hash_bytes(content_bytes)

    return IntegrityCheckResult(
        check_name="artifact_hash",
        passed=False,
        message="Artifact hash mismatch",
        expected=expected_hash[:16] + "...",
        actual=actual[:16] + "...",
    )


def verify_validation_signature(
    provenance: RuntimeArtifactProvenance,
) -> IntegrityCheckResult:
    """
    Verify validation signature is present and well-formed.

    Args:
        provenance: Provenance record to verify

    Returns:
        IntegrityCheckResult
    """
    validation = provenance.validation_lineage

    if not validation.signature_input_hash:
        return IntegrityCheckResult(
            check_name="validation_signature",
            passed=False,
            message="Validation input hash is empty",
        )

    if not validation.signature_validation_hash:
        return IntegrityCheckResult(
            check_name="validation_signature",
            passed=False,
            message="Validation hash is empty",
        )

    if not validation.passed:
        return IntegrityCheckResult(
            check_name="validation_signature",
            passed=False,
            message="Validation did not pass",
            details={"validation_passed": validation.passed},
        )

    return IntegrityCheckResult(
        check_name="validation_signature",
        passed=True,
        message="Validation signature is valid",
        details={
            "input_hash": validation.signature_input_hash[:8] + "...",
            "validation_hash": validation.signature_validation_hash[:8] + "...",
        },
    )


def verify_admission_signature(
    provenance: RuntimeArtifactProvenance,
) -> IntegrityCheckResult:
    """
    Verify admission decision is recorded.

    Args:
        provenance: Provenance record to verify

    Returns:
        IntegrityCheckResult
    """
    admission = provenance.admission_lineage

    if not admission.admission_id:
        return IntegrityCheckResult(
            check_name="admission_signature",
            passed=False,
            message="Admission ID is empty",
        )

    if admission.decision not in ("ADMITTED", "CONDITIONALLY_ADMITTED"):
        return IntegrityCheckResult(
            check_name="admission_signature",
            passed=False,
            message=f"Admission decision is not admitted: {admission.decision}",
            details={"decision": admission.decision},
        )

    return IntegrityCheckResult(
        check_name="admission_signature",
        passed=True,
        message="Admission signature is valid",
        details={
            "admission_id": admission.admission_id[:8] + "..." if len(admission.admission_id) > 8 else admission.admission_id,
            "decision": admission.decision,
        },
    )


def verify_trace_order(
    provenance: RuntimeArtifactProvenance,
) -> IntegrityCheckResult:
    """
    Verify trace events are in correct order.

    Args:
        provenance: Provenance record to verify

    Returns:
        IntegrityCheckResult
    """
    events = provenance.trace_events

    if not events:
        return IntegrityCheckResult(
            check_name="trace_order",
            passed=False,
            message="No trace events recorded",
        )

    expected_order = [
        TraceEventType.VALIDATION_CERTIFIED,
        TraceEventType.ADMISSION_COMPLETED,
        TraceEventType.TRANSLATION_COMPLETED,
        TraceEventType.ADAPTER_COMPLETED,
        TraceEventType.ARTIFACT_RECORDED,
    ]

    actual_types = [e.event_type for e in events]

    for i, expected_type in enumerate(expected_order):
        if i >= len(actual_types):
            return IntegrityCheckResult(
                check_name="trace_order",
                passed=False,
                message=f"Missing expected event: {expected_type.value}",
                details={
                    "expected_next": expected_type.value,
                    "actual_count": len(actual_types),
                },
            )
        if actual_types[i] != expected_type:
            return IntegrityCheckResult(
                check_name="trace_order",
                passed=False,
                message=f"Event order mismatch at position {i}",
                expected=expected_type.value,
                actual=actual_types[i].value,
            )

    sequence_numbers = [e.sequence_number for e in events]
    if sequence_numbers != sorted(sequence_numbers):
        return IntegrityCheckResult(
            check_name="trace_order",
            passed=False,
            message="Sequence numbers are not monotonically increasing",
            details={"sequence_numbers": sequence_numbers},
        )

    return IntegrityCheckResult(
        check_name="trace_order",
        passed=True,
        message="Trace order is valid",
        details={"event_count": len(events)},
    )


def verify_provenance_hash(
    provenance: RuntimeArtifactProvenance,
) -> IntegrityCheckResult:
    """
    Verify provenance hash matches content.

    Args:
        provenance: Provenance record to verify

    Returns:
        IntegrityCheckResult
    """
    if not provenance.provenance_hash:
        return IntegrityCheckResult(
            check_name="provenance_hash",
            passed=False,
            message="Provenance hash is empty",
        )

    content = {
        "run_id": provenance.run_id,
        "source_topology_id": provenance.source_topology_id,
        "source_topology_hash": provenance.source_topology_hash,
        "validation_lineage": provenance.validation_lineage.to_dict(),
        "admission_lineage": provenance.admission_lineage.to_dict(),
        "artifact_lineage": provenance.artifact_lineage.to_dict(),
        "translator_id": provenance.translator_id,
        "adapter_id": provenance.adapter_id,
    }
    expected_hash = stable_hash_model(content)[:32]

    if provenance.provenance_hash != expected_hash:
        return IntegrityCheckResult(
            check_name="provenance_hash",
            passed=False,
            message="Provenance hash mismatch - content may have been tampered",
            expected=expected_hash[:16] + "...",
            actual=provenance.provenance_hash[:16] + "...",
        )

    return IntegrityCheckResult(
        check_name="provenance_hash",
        passed=True,
        message="Provenance hash is valid",
    )


def verify_bundle_hash(
    bundle: RuntimeReplayBundle,
) -> IntegrityCheckResult:
    """
    Verify bundle hash matches content.

    Args:
        bundle: Replay bundle to verify

    Returns:
        IntegrityCheckResult
    """
    if not bundle.bundle_hash:
        return IntegrityCheckResult(
            check_name="bundle_hash",
            passed=False,
            message="Bundle hash is empty",
        )

    content = {
        "bundle_id": bundle.bundle_id,
        "provenance": bundle.provenance.to_dict(),
        "replayable": bundle.replayable,
        "replay_constraints": bundle.replay_constraints,
        "version": bundle.version,
    }
    expected_hash = stable_hash_model(content)[:32]

    if bundle.bundle_hash != expected_hash:
        return IntegrityCheckResult(
            check_name="bundle_hash",
            passed=False,
            message="Bundle hash mismatch - bundle may have been tampered",
            expected=expected_hash[:16] + "...",
            actual=bundle.bundle_hash[:16] + "...",
        )

    return IntegrityCheckResult(
        check_name="bundle_hash",
        passed=True,
        message="Bundle hash is valid",
    )


def verify_replay_bundle_integrity(
    bundle: RuntimeReplayBundle,
) -> BundleIntegrityResult:
    """
    Run all integrity checks on a replay bundle.

    Args:
        bundle: Replay bundle to verify

    Returns:
        BundleIntegrityResult with all check outcomes
    """
    checks = [
        verify_validation_signature(bundle.provenance),
        verify_admission_signature(bundle.provenance),
        verify_trace_order(bundle.provenance),
        verify_provenance_hash(bundle.provenance),
        verify_bundle_hash(bundle),
    ]

    failed = [c for c in checks if not c.passed]
    passed = len(failed) == 0

    message = "All integrity checks passed" if passed else f"{len(failed)} check(s) failed"

    return BundleIntegrityResult(
        passed=passed,
        bundle_id=bundle.bundle_id,
        checks=checks,
        message=message,
    )


def verify_or_raise(bundle: RuntimeReplayBundle) -> BundleIntegrityResult:
    """
    Run all integrity checks and raise on failure.

    Convenience function for strict verification mode.
    """
    result = verify_replay_bundle_integrity(bundle)

    if not result.passed:
        first_failure = result.failed_checks[0]
        raise IntegrityError(
            message=first_failure.message,
            check_name=first_failure.check_name,
            expected_value=first_failure.expected,
            actual_value=first_failure.actual,
            details={"all_checks": [c.to_dict() for c in result.checks]},
        )

    return result
