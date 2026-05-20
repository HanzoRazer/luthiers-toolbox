"""
Certification Integrity Verification.

Sprint: MRP-5M
Status: PROTOTYPE

Verifies integrity of certified topology before admission.
Detects tampering, mutation, or corruption after certification.

ARCHITECTURAL PRINCIPLE:
    Integrity verification is SEPARATE from policy evaluation.
    Integrity checks detect corruption.
    Policies evaluate eligibility.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, TYPE_CHECKING
import hashlib
import json

from .exceptions import IntegrityViolationError

if TYPE_CHECKING:
    from ..topology_validation.contracts import CertifiedTopology


@dataclass
class IntegrityCheckResult:
    """Result of an integrity check."""

    check_name: str
    passed: bool
    message: str
    expected_value: Optional[str] = None
    actual_value: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {
            "check_name": self.check_name,
            "passed": self.passed,
            "message": self.message,
            "details": self.details,
        }
        if self.expected_value:
            result["expected_value"] = self.expected_value
        if self.actual_value:
            result["actual_value"] = self.actual_value
        return result


@dataclass
class IntegrityVerificationResult:
    """Complete result of all integrity checks."""

    passed: bool
    checks: list  # List[IntegrityCheckResult]
    violation_type: Optional[str] = None
    message: str = ""

    @property
    def failed_checks(self) -> list:
        """Get list of failed checks."""
        return [c for c in self.checks if not c.passed]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "passed": self.passed,
            "checks": [c.to_dict() for c in self.checks],
            "violation_type": self.violation_type,
            "message": self.message,
            "failed_check_count": len(self.failed_checks),
        }


def compute_topology_hash(topology_dict: Dict[str, Any]) -> str:
    """
    Compute deterministic hash of topology dictionary.

    Uses same algorithm as ValidationSignature.compute().
    """
    topology_json = json.dumps(topology_dict, sort_keys=True)
    return hashlib.sha256(topology_json.encode()).hexdigest()[:16]


def verify_certification_chain(certified_topology: "CertifiedTopology") -> IntegrityCheckResult:
    """
    Verify the certification chain is intact.

    Checks that:
    - CertifiedTopology has required attributes
    - Validation result exists and passed
    - Signature exists
    """
    from ..topology_validation.contracts import CertifiedTopology

    if not isinstance(certified_topology, CertifiedTopology):
        return IntegrityCheckResult(
            check_name="certification_chain",
            passed=False,
            message="Object is not CertifiedTopology",
            details={"actual_type": type(certified_topology).__name__},
        )

    if not hasattr(certified_topology, "_certified"):
        return IntegrityCheckResult(
            check_name="certification_chain",
            passed=False,
            message="CertifiedTopology missing _certified flag",
        )

    if not certified_topology._certified:
        return IntegrityCheckResult(
            check_name="certification_chain",
            passed=False,
            message="CertifiedTopology._certified is False",
        )

    validation = certified_topology.validation
    if validation is None:
        return IntegrityCheckResult(
            check_name="certification_chain",
            passed=False,
            message="Validation result is missing",
        )

    if not validation.passed:
        return IntegrityCheckResult(
            check_name="certification_chain",
            passed=False,
            message="Validation result shows failure",
            details={"validation_passed": validation.passed},
        )

    signature = certified_topology.signature
    if signature is None:
        return IntegrityCheckResult(
            check_name="certification_chain",
            passed=False,
            message="Validation signature is missing",
        )

    return IntegrityCheckResult(
        check_name="certification_chain",
        passed=True,
        message="Certification chain is intact",
        details={
            "validation_tier": validation.tier.value,
            "request_id": validation.request_id,
        },
    )


def verify_validation_signature(certified_topology: "CertifiedTopology") -> IntegrityCheckResult:
    """
    Verify the validation signature is well-formed.

    Checks that:
    - Signature has input_hash
    - Signature has validation_hash
    - Hashes are non-empty
    """
    from ..topology_validation.contracts import CertifiedTopology

    if not isinstance(certified_topology, CertifiedTopology):
        return IntegrityCheckResult(
            check_name="validation_signature",
            passed=False,
            message="Object is not CertifiedTopology",
        )

    signature = certified_topology.signature
    if signature is None:
        return IntegrityCheckResult(
            check_name="validation_signature",
            passed=False,
            message="Signature is missing",
        )

    if not signature.input_hash:
        return IntegrityCheckResult(
            check_name="validation_signature",
            passed=False,
            message="Signature input_hash is empty",
        )

    if not signature.validation_hash:
        return IntegrityCheckResult(
            check_name="validation_signature",
            passed=False,
            message="Signature validation_hash is empty",
        )

    return IntegrityCheckResult(
        check_name="validation_signature",
        passed=True,
        message="Validation signature is well-formed",
        details={
            "input_hash_length": len(signature.input_hash),
            "validation_hash_length": len(signature.validation_hash),
        },
    )


def verify_topology_immutable(certified_topology: "CertifiedTopology") -> IntegrityCheckResult:
    """
    Verify topology has not been mutated after certification.

    Recomputes the topology hash and compares to the signature's input_hash.
    If they differ, topology was modified after certification.
    """
    from ..topology_validation.contracts import CertifiedTopology

    if not isinstance(certified_topology, CertifiedTopology):
        return IntegrityCheckResult(
            check_name="topology_immutable",
            passed=False,
            message="Object is not CertifiedTopology",
        )

    signature = certified_topology.signature
    if signature is None:
        return IntegrityCheckResult(
            check_name="topology_immutable",
            passed=False,
            message="Cannot verify immutability: signature missing",
        )

    expected_hash = signature.input_hash
    topology_dict = certified_topology.topology_dict

    try:
        current_hash = compute_topology_hash(topology_dict)
    except Exception as e:
        return IntegrityCheckResult(
            check_name="topology_immutable",
            passed=False,
            message=f"Failed to compute topology hash: {e}",
        )

    if current_hash != expected_hash:
        return IntegrityCheckResult(
            check_name="topology_immutable",
            passed=False,
            message="Topology was mutated after certification",
            expected_value=expected_hash,
            actual_value=current_hash,
            details={
                "hash_mismatch": True,
                "expected": expected_hash,
                "actual": current_hash,
            },
        )

    return IntegrityCheckResult(
        check_name="topology_immutable",
        passed=True,
        message="Topology has not been mutated",
        details={
            "hash": current_hash,
            "verified": True,
        },
    )


def verify_all(certified_topology: "CertifiedTopology") -> IntegrityVerificationResult:
    """
    Run all integrity checks on a certified topology.

    Returns comprehensive result with all check outcomes.
    """
    checks = [
        verify_certification_chain(certified_topology),
        verify_validation_signature(certified_topology),
        verify_topology_immutable(certified_topology),
    ]

    failed = [c for c in checks if not c.passed]
    passed = len(failed) == 0

    violation_type = None
    message = "All integrity checks passed"

    if not passed:
        first_failure = failed[0]
        violation_type = first_failure.check_name.upper()
        message = first_failure.message

    return IntegrityVerificationResult(
        passed=passed,
        checks=checks,
        violation_type=violation_type,
        message=message,
    )


def verify_or_raise(certified_topology: "CertifiedTopology") -> IntegrityVerificationResult:
    """
    Run all integrity checks and raise on failure.

    Convenience function for strict verification mode.
    """
    result = verify_all(certified_topology)

    if not result.passed:
        failed = result.failed_checks[0]
        raise IntegrityViolationError(
            message=failed.message,
            violation_type=result.violation_type or "UNKNOWN",
            expected_hash=failed.expected_value,
            actual_hash=failed.actual_value,
            details={"checks": [c.to_dict() for c in result.checks]},
        )

    return result
