"""
Runtime Admission Policies.

Sprint: MRP-5M
Status: PROTOTYPE
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from .contracts import ExecutionAdmissionRequest, ExecutionMode, PolicyEvaluationResult, RuntimeTier


class PolicySeverity(str, Enum):
    BLOCKING = "BLOCKING"
    WARNING = "WARNING"
    INFO = "INFO"


@dataclass
class PolicyResult:
    passed: bool
    severity: PolicySeverity
    message: str
    details: Dict[str, Any] = field(default_factory=dict)

    def to_evaluation_result(self, policy_id: str) -> PolicyEvaluationResult:
        return PolicyEvaluationResult(
            policy_id=policy_id,
            passed=self.passed,
            severity=self.severity.value,
            message=self.message,
            details=self.details,
        )


class AdmissionPolicy(ABC):
    @property
    @abstractmethod
    def policy_id(self) -> str:
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        ...

    @property
    def severity(self) -> PolicySeverity:
        return PolicySeverity.BLOCKING

    @abstractmethod
    def evaluate(self, request: ExecutionAdmissionRequest) -> PolicyResult:
        ...


class NoUncertifiedExecutionPolicy(AdmissionPolicy):
    @property
    def policy_id(self) -> str:
        return "no_uncertified_execution"

    @property
    def description(self) -> str:
        return "Ensures only CertifiedTopology is submitted for admission"

    def evaluate(self, request: ExecutionAdmissionRequest) -> PolicyResult:
        from ..topology_validation.contracts import CertifiedTopology

        topology = request.certified_topology
        if not isinstance(topology, CertifiedTopology):
            return PolicyResult(
                passed=False,
                severity=PolicySeverity.BLOCKING,
                message="Topology is not CertifiedTopology",
            )

        if not hasattr(topology, "_certified") or not topology._certified:
            return PolicyResult(
                passed=False,
                severity=PolicySeverity.BLOCKING,
                message="Topology certification flag is not set",
            )

        return PolicyResult(passed=True, severity=PolicySeverity.INFO, message="Topology is certified")


class DeterministicOnlyPolicy(AdmissionPolicy):
    @property
    def policy_id(self) -> str:
        return "deterministic_only"

    @property
    def description(self) -> str:
        return "Ensures execution mode is deterministic for prototype runtime"

    def evaluate(self, request: ExecutionAdmissionRequest) -> PolicyResult:
        context = request.runtime_context
        if context.runtime_tier == RuntimeTier.PROTOTYPE:
            if context.execution_mode != ExecutionMode.DETERMINISTIC:
                return PolicyResult(
                    passed=False,
                    severity=PolicySeverity.BLOCKING,
                    message="Prototype runtime requires deterministic execution",
                )
        return PolicyResult(passed=True, severity=PolicySeverity.INFO, message="Execution mode compatible")


class AdapterAvailablePolicy(AdmissionPolicy):
    @property
    def policy_id(self) -> str:
        return "adapter_available"

    @property
    def description(self) -> str:
        return "Ensures requested adapter is available"

    def evaluate(self, request: ExecutionAdmissionRequest) -> PolicyResult:
        context = request.runtime_context
        requested = context.requested_adapter_id
        available = context.available_adapter_ids

        if requested is None:
            return PolicyResult(passed=True, severity=PolicySeverity.INFO, message="No specific adapter requested")

        if not available:
            return PolicyResult(
                passed=False,
                severity=PolicySeverity.BLOCKING,
                message="No adapters available",
            )

        if requested not in available:
            return PolicyResult(
                passed=False,
                severity=PolicySeverity.BLOCKING,
                message=f"Requested adapter '{requested}' is not available",
            )

        return PolicyResult(passed=True, severity=PolicySeverity.INFO, message=f"Adapter '{requested}' is available")


class SignatureIntegrityPolicy(AdmissionPolicy):
    @property
    def policy_id(self) -> str:
        return "signature_integrity"

    @property
    def description(self) -> str:
        return "Ensures certification signature is present"

    def evaluate(self, request: ExecutionAdmissionRequest) -> PolicyResult:
        from ..topology_validation.contracts import CertifiedTopology

        topology = request.certified_topology
        if not isinstance(topology, CertifiedTopology):
            return PolicyResult(passed=False, severity=PolicySeverity.BLOCKING, message="Not CertifiedTopology")

        signature = topology.signature
        if signature is None:
            return PolicyResult(passed=False, severity=PolicySeverity.BLOCKING, message="Signature is missing")

        if not signature.input_hash or not signature.validation_hash:
            return PolicyResult(passed=False, severity=PolicySeverity.BLOCKING, message="Signature incomplete")

        return PolicyResult(passed=True, severity=PolicySeverity.INFO, message="Signature is valid")


class PrototypeRuntimeOnlyPolicy(AdmissionPolicy):
    @property
    def policy_id(self) -> str:
        return "prototype_runtime_only"

    @property
    def description(self) -> str:
        return "Ensures runtime tier is PROTOTYPE"

    def evaluate(self, request: ExecutionAdmissionRequest) -> PolicyResult:
        context = request.runtime_context
        if context.runtime_tier != RuntimeTier.PROTOTYPE:
            return PolicyResult(
                passed=False,
                severity=PolicySeverity.BLOCKING,
                message="Only PROTOTYPE runtime tier is currently supported",
            )
        return PolicyResult(passed=True, severity=PolicySeverity.INFO, message="Runtime tier is PROTOTYPE")


class ValidationRequiredPolicy(AdmissionPolicy):
    @property
    def policy_id(self) -> str:
        return "validation_required"

    @property
    def description(self) -> str:
        return "Ensures topology has passed validation"

    def evaluate(self, request: ExecutionAdmissionRequest) -> PolicyResult:
        from ..topology_validation.contracts import CertifiedTopology

        topology = request.certified_topology
        if not isinstance(topology, CertifiedTopology):
            return PolicyResult(passed=False, severity=PolicySeverity.BLOCKING, message="Not CertifiedTopology")

        validation = topology.validation
        if validation is None:
            return PolicyResult(passed=False, severity=PolicySeverity.BLOCKING, message="Validation result missing")

        if not validation.passed:
            return PolicyResult(passed=False, severity=PolicySeverity.BLOCKING, message="Validation did not pass")

        return PolicyResult(passed=True, severity=PolicySeverity.INFO, message="Validation passed")


class AdmissionPolicyRegistry:
    def __init__(self, policies: Optional[List[AdmissionPolicy]] = None):
        if policies is not None:
            self._policies = list(policies)
        else:
            self._policies = self._default_policies()

    def _default_policies(self) -> List[AdmissionPolicy]:
        return [
            NoUncertifiedExecutionPolicy(),
            ValidationRequiredPolicy(),
            SignatureIntegrityPolicy(),
            PrototypeRuntimeOnlyPolicy(),
            DeterministicOnlyPolicy(),
            AdapterAvailablePolicy(),
        ]

    def add(self, policy: AdmissionPolicy) -> None:
        self._policies.append(policy)

    def remove(self, policy_id: str) -> bool:
        for i, p in enumerate(self._policies):
            if p.policy_id == policy_id:
                self._policies.pop(i)
                return True
        return False

    def get(self, policy_id: str) -> Optional[AdmissionPolicy]:
        for p in self._policies:
            if p.policy_id == policy_id:
                return p
        return None

    def list_policies(self) -> List[str]:
        return [p.policy_id for p in self._policies]

    def evaluate_all(self, request: ExecutionAdmissionRequest) -> List[PolicyEvaluationResult]:
        results = []
        for policy in self._policies:
            result = policy.evaluate(request)
            results.append(result.to_evaluation_result(policy.policy_id))
        return results


def get_default_policy_registry() -> AdmissionPolicyRegistry:
    return AdmissionPolicyRegistry()
