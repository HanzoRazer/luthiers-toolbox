"""
Runtime Admission Policies.

Sprint: MRP-5M
Status: PROTOTYPE

Policy framework for runtime admission control.
Policies evaluate whether a certified topology should be
admitted for runtime execution.

ARCHITECTURAL PRINCIPLE:
    Policies evaluate runtime eligibility only.
    They do NOT:
    - reinterpret topology semantics,
    - modify validation,
    - repair geometry,
    - or mutate lifecycle classification.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from .contracts import (
    ExecutionAdmissionRequest,
    ExecutionMode,
    PolicyEvaluationResult,
    RuntimeTier,
)

if TYPE_CHECKING:
    from ..topology_validation.contracts import CertifiedTopology


class PolicySeverity(str, Enum):
    """Severity of policy violations."""

    BLOCKING = "BLOCKING"  # Admission denied
    WARNING = "WARNING"  # Admission allowed with warning
    INFO = "INFO"  # Informational, does not affect admission


@dataclass
class PolicyResult:
    """Result of a policy evaluation."""

    passed: bool
    severity: PolicySeverity
    message: str
    details: Dict[str, Any] = field(default_factory=dict)

    def to_evaluation_result(self, policy_id: str) -> PolicyEvaluationResult:
        """Convert to PolicyEvaluationResult."""
        return PolicyEvaluationResult(
            policy_id=policy_id,
            passed=self.passed,
            severity=self.severity.value,
            message=self.message,
            details=self.details,
        )


class AdmissionPolicy(ABC):
    """
    Base class for admission policies.

    Each policy evaluates a specific admission criterion.
    Policies must be stateless and deterministic.
    """

    @property
    @abstractmethod
    def policy_id(self) -> str:
        """Unique identifier for this policy."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of what this policy checks."""
        ...

    @property
    def severity(self) -> PolicySeverity:
        """Default severity when this policy fails."""
        return PolicySeverity.BLOCKING

    @abstractmethod
    def evaluate(self, request: ExecutionAdmissionRequest) -> PolicyResult:
        """
        Evaluate the policy against an admission request.

        Args:
            request: The admission request to evaluate

        Returns:
            PolicyResult indicating pass/fail and details
        """
        ...


class NoUncertifiedExecutionPolicy(AdmissionPolicy):
    """
    Constitutional policy: only certified topology may execute.

    This is the foundational admission policy. Without certification,
    topology cannot enter the runtime pipeline.
    """

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
                details={
                    "actual_type": type(topology).__name__,
                    "expected_type": "CertifiedTopology",
                },
            )

        if not hasattr(topology, "_certified") or not topology._certified:
            return PolicyResult(
                passed=False,
                severity=PolicySeverity.BLOCKING,
                message="Topology certification flag is not set",
            )

        return PolicyResult(
            passed=True,
            severity=PolicySeverity.INFO,
            message="Topology is certified",
        )


class DeterministicOnlyPolicy(AdmissionPolicy):
    """
    Policy: only deterministic execution allowed in prototype runtime.

    Ensures reproducible execution for prototype tier.
    """

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
                    details={
                        "runtime_tier": context.runtime_tier.value,
                        "execution_mode": context.execution_mode.value,
                        "required_mode": ExecutionMode.DETERMINISTIC.value,
                    },
                )

        return PolicyResult(
            passed=True,
            severity=PolicySeverity.INFO,
            message="Execution mode is compatible with runtime tier",
        )


class AdapterAvailablePolicy(AdmissionPolicy):
    """
    Policy: requested adapter must be available.

    If a specific adapter is requested, it must be in the
    available adapters list.
    """

    @property
    def policy_id(self) -> str:
        return "adapter_available"

    @property
    def description(self) -> str:
        return "Ensures requested adapter is available in runtime context"

    def evaluate(self, request: ExecutionAdmissionRequest) -> PolicyResult:
        context = request.runtime_context
        requested = context.requested_adapter_id
        available = context.available_adapter_ids

        if requested is None:
            return PolicyResult(
                passed=True,
                severity=PolicySeverity.INFO,
                message="No specific adapter requested",
            )

        if not available:
            return PolicyResult(
                passed=False,
                severity=PolicySeverity.BLOCKING,
                message="No adapters available in runtime context",
                details={
                    "requested_adapter": requested,
                    "available_adapters": [],
                },
            )

        if requested not in available:
            return PolicyResult(
                passed=False,
                severity=PolicySeverity.BLOCKING,
                message=f"Requested adapter '{requested}' is not available",
                details={
                    "requested_adapter": requested,
                    "available_adapters": available,
                },
            )

        return PolicyResult(
            passed=True,
            severity=PolicySeverity.INFO,
            message=f"Adapter '{requested}' is available",
        )


class SignatureIntegrityPolicy(AdmissionPolicy):
    """
    Policy: certification signature must be intact.

    Verifies that the validation signature exists and is well-formed.
    Actual hash verification is done by integrity module.
    """

    @property
    def policy_id(self) -> str:
        return "signature_integrity"

    @property
    def description(self) -> str:
        return "Ensures certification signature is present and well-formed"

    def evaluate(self, request: ExecutionAdmissionRequest) -> PolicyResult:
        from ..topology_validation.contracts import CertifiedTopology

        topology = request.certified_topology

        if not isinstance(topology, CertifiedTopology):
            return PolicyResult(
                passed=False,
                severity=PolicySeverity.BLOCKING,
                message="Cannot verify signature: not CertifiedTopology",
            )

        signature = topology.signature
        if signature is None:
            return PolicyResult(
                passed=False,
                severity=PolicySeverity.BLOCKING,
                message="Certification signature is missing",
            )

        if not signature.input_hash or not signature.validation_hash:
            return PolicyResult(
                passed=False,
                severity=PolicySeverity.BLOCKING,
                message="Certification signature is incomplete",
                details={
                    "has_input_hash": bool(signature.input_hash),
                    "has_validation_hash": bool(signature.validation_hash),
                },
            )

        return PolicyResult(
            passed=True,
            severity=PolicySeverity.INFO,
            message="Certification signature is present and well-formed",
            details={
                "input_hash": signature.input_hash[:8] + "...",
                "validation_hash": signature.validation_hash[:8] + "...",
            },
        )


class PrototypeRuntimeOnlyPolicy(AdmissionPolicy):
    """
    Policy: only prototype runtime is currently supported.

    Production runtime is a future capability.
    """

    @property
    def policy_id(self) -> str:
        return "prototype_runtime_only"

    @property
    def description(self) -> str:
        return "Ensures runtime tier is PROTOTYPE (production not yet supported)"

    @property
    def severity(self) -> PolicySeverity:
        return PolicySeverity.BLOCKING

    def evaluate(self, request: ExecutionAdmissionRequest) -> PolicyResult:
        context = request.runtime_context

        if context.runtime_tier != RuntimeTier.PROTOTYPE:
            return PolicyResult(
                passed=False,
                severity=PolicySeverity.BLOCKING,
                message="Only PROTOTYPE runtime tier is currently supported",
                details={
                    "requested_tier": context.runtime_tier.value,
                    "supported_tiers": [RuntimeTier.PROTOTYPE.value],
                },
            )

        return PolicyResult(
            passed=True,
            severity=PolicySeverity.INFO,
            message="Runtime tier is PROTOTYPE",
        )


class ValidationRequiredPolicy(AdmissionPolicy):
    """
    Policy: topology must have passed validation.

    Enforces the certification chain — only validated topology
    may be admitted for execution.
    """

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
            return PolicyResult(
                passed=False,
                severity=PolicySeverity.BLOCKING,
                message="Cannot verify validation: not CertifiedTopology",
            )

        validation = topology.validation
        if validation is None:
            return PolicyResult(
                passed=False,
                severity=PolicySeverity.BLOCKING,
                message="Validation result is missing",
            )

        if not validation.passed:
            return PolicyResult(
                passed=False,
                severity=PolicySeverity.BLOCKING,
                message="Topology validation did not pass",
                details={
                    "validation_passed": validation.passed,
                    "blocking_count": validation.blocking_count,
                },
            )

        return PolicyResult(
            passed=True,
            severity=PolicySeverity.INFO,
            message="Topology validation passed",
            details={
                "tier": validation.tier.value,
                "request_id": validation.request_id,
            },
        )


class AdmissionPolicyRegistry:
    """
    Registry of admission policies.

    Maintains the ordered list of policies to evaluate.
    Does NOT make semantic decisions — just executes policies.
    """

    def __init__(self, policies: Optional[List[AdmissionPolicy]] = None):
        """
        Initialize with optional policy list.

        If no policies provided, uses default policy set.
        """
        if policies is not None:
            self._policies = list(policies)
        else:
            self._policies = self._default_policies()

    def _default_policies(self) -> List[AdmissionPolicy]:
        """Return the default policy set."""
        return [
            NoUncertifiedExecutionPolicy(),
            ValidationRequiredPolicy(),
            SignatureIntegrityPolicy(),
            PrototypeRuntimeOnlyPolicy(),
            DeterministicOnlyPolicy(),
            AdapterAvailablePolicy(),
        ]

    def add(self, policy: AdmissionPolicy) -> None:
        """Add a policy to the registry."""
        self._policies.append(policy)

    def remove(self, policy_id: str) -> bool:
        """Remove a policy by ID. Returns True if removed."""
        for i, p in enumerate(self._policies):
            if p.policy_id == policy_id:
                self._policies.pop(i)
                return True
        return False

    def get(self, policy_id: str) -> Optional[AdmissionPolicy]:
        """Get a policy by ID."""
        for p in self._policies:
            if p.policy_id == policy_id:
                return p
        return None

    def list_policies(self) -> List[str]:
        """List all policy IDs."""
        return [p.policy_id for p in self._policies]

    def evaluate_all(
        self, request: ExecutionAdmissionRequest
    ) -> List[PolicyEvaluationResult]:
        """
        Evaluate all policies against a request.

        Returns all evaluation results, not just failures.
        """
        results = []
        for policy in self._policies:
            result = policy.evaluate(request)
            results.append(result.to_evaluation_result(policy.policy_id))
        return results

    def evaluate_until_blocking(
        self, request: ExecutionAdmissionRequest
    ) -> List[PolicyEvaluationResult]:
        """
        Evaluate policies until a BLOCKING failure is encountered.

        This is the typical evaluation mode — stop on first blocking failure.
        """
        results = []
        for policy in self._policies:
            result = policy.evaluate(request)
            eval_result = result.to_evaluation_result(policy.policy_id)
            results.append(eval_result)

            if not result.passed and result.severity == PolicySeverity.BLOCKING:
                break

        return results


def get_default_policy_registry() -> AdmissionPolicyRegistry:
    """Get a registry with default policies."""
    return AdmissionPolicyRegistry()
