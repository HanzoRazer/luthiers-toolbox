"""
Certification Integrity Verification.

Sprint: MRP-5M
Status: PROTOTYPE
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional
import hashlib
import json


@dataclass
class IntegrityCheckResult:
    check_name: str
    passed: bool
    message: str
    expected_value: Optional[str] = None
    actual_value: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
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
    passed: bool
    checks: list
    violation_type: Optional[str] = None
    message: str = ""

    @property
    def failed_checks(self) -> list:
        return [c for c in self.checks if not c.passed]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "checks": [c.to_dict() for c in self.checks],
            "violation_type": self.violation_type,
            "message": self.message,
        }


def compute_topology_hash(topology_dict: Dict[str, Any]) -> str:
    topology_json = json.dumps(topology_dict, sort_keys=True)
    return hashlib.sha256(topology_json.encode()).hexdigest()[:16]


def verify_certification_chain(certified_topology: Any) -> IntegrityCheckResult:
    from ..topology_validation.contracts import CertifiedTopology

    if not isinstance(certified_topology, CertifiedTopology):
        return IntegrityCheckResult(
            check_name="certification_chain",
            passed=False,
            message="Object is not CertifiedTopology",
        )

    if not hasattr(certified_topology, "_certified") or not certified_topology._certified:
        return IntegrityCheckResult(
            check_name="certification_chain",
            passed=False,
            message="CertifiedTopology._certified is False",
        )

    if certified_topology.validation is None:
        return IntegrityCheckResult(
            check_name="certification_chain",
            passed=False,
            message="Validation result is missing",
        )

    if not certified_topology.validation.passed:
        return IntegrityCheckResult(
            check_name="certification_chain",
            passed=False,
            message="Validation result shows failure",
        )

    if certified_topology.signature is None:
        return IntegrityCheckResult(
            check_name="certification_chain",
            passed=False,
            message="Validation signature is missing",
        )

    return IntegrityCheckResult(
        check_name="certification_chain",
        passed=True,
        message="Certification chain is intact",
    )


def verify_validation_signature(certified_topology: Any) -> IntegrityCheckResult:
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

    if not signature.input_hash or not signature.validation_hash:
        return IntegrityCheckResult(
            check_name="validation_signature",
            passed=False,
            message="Signature hashes are empty",
        )

    return IntegrityCheckResult(
        check_name="validation_signature",
        passed=True,
        message="Validation signature is well-formed",
    )


def verify_topology_immutable(certified_topology: Any) -> IntegrityCheckResult:
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
    current_hash = compute_topology_hash(certified_topology.topology_dict)

    if current_hash != expected_hash:
        return IntegrityCheckResult(
            check_name="topology_immutable",
            passed=False,
            message="Topology was mutated after certification",
            expected_value=expected_hash,
            actual_value=current_hash,
        )

    return IntegrityCheckResult(
        check_name="topology_immutable",
        passed=True,
        message="Topology has not been mutated",
    )


def verify_all(certified_topology: Any) -> IntegrityVerificationResult:
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
