"""
Execution Admission Controller.

Sprint: MRP-5M
Status: PROTOTYPE

Main controller for runtime admission evaluation.
Determines whether certified topology may enter executable runtime flow.

ARCHITECTURAL PRINCIPLE:
    The controller is an ADMISSION AUTHORITY, not a semantic authority.
    It evaluates runtime eligibility, not topology correctness.

    The controller MUST:
    - verify CertifiedTopology integrity
    - verify validation continuity
    - verify deterministic runtime eligibility
    - evaluate runtime policies
    - emit admission result
    - produce admission provenance

    The controller MUST NOT:
    - repair topology
    - reinterpret semantics
    - orchestrate translators
    - mutate geometry
    - infer runtime behavior
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from .contracts import (
    AdmissionDecision,
    AdmissionRejection,
    AdmissionTrace,
    ExecutionAdmissionRequest,
    ExecutionAdmissionResult,
    PolicyEvaluationResult,
    RejectionReason,
    RuntimeExecutionContext,
)
from .exceptions import (
    AdmissionDeniedError,
    IntegrityViolationError,
    InvalidAdmissionRequestError,
    UncertifiedTopologyError,
)
from .integrity import (
    IntegrityVerificationResult,
    verify_all as verify_integrity,
)
from .policies import (
    AdmissionPolicyRegistry,
    PolicySeverity,
    get_default_policy_registry,
)
from .provenance import (
    AdmissionProvenance,
    ProvenanceBuilder,
    get_admission_ledger,
)

if TYPE_CHECKING:
    from ..topology_validation.contracts import CertifiedTopology


class ExecutionAdmissionController:
    """
    Controller for runtime execution admission.

    Evaluates admission requests and produces explicit admission results.
    All decisions are observable and produce provenance.

    Usage:
        controller = ExecutionAdmissionController()
        result = controller.evaluate(request)

        if result.admitted:
            # proceed with execution
            pass
        else:
            # handle rejection
            print(result.rejection.message)
    """

    def __init__(
        self,
        policy_registry: Optional[AdmissionPolicyRegistry] = None,
        record_provenance: bool = True,
    ):
        """
        Initialize the admission controller.

        Args:
            policy_registry: Custom policy registry, or None for defaults
            record_provenance: Whether to record provenance to global ledger
        """
        self._policy_registry = policy_registry or get_default_policy_registry()
        self._record_provenance = record_provenance

    def evaluate(
        self,
        request: ExecutionAdmissionRequest,
    ) -> ExecutionAdmissionResult:
        """
        Evaluate an admission request.

        This is the main entry point for admission evaluation.
        Returns an explicit result, never raises for normal rejection.

        Args:
            request: The admission request to evaluate

        Returns:
            ExecutionAdmissionResult with decision and provenance

        Raises:
            InvalidAdmissionRequestError: If request structure is invalid
        """
        self._validate_request_structure(request)

        provenance_builder = ProvenanceBuilder(request)
        trace = AdmissionTrace(
            request_id=request.request_id,
            trace_id=request.trace_id,
            started_at=datetime.now(timezone.utc).isoformat(),
        )

        # Phase 1: Integrity verification
        integrity_result = self._verify_integrity(request, trace)
        provenance_builder.record_integrity_result(integrity_result)

        if not integrity_result.passed:
            return self._reject_for_integrity(
                request, trace, integrity_result, provenance_builder
            )

        # Phase 2: Policy evaluation
        policy_results = self._evaluate_policies(request, trace)
        provenance_builder.record_policy_results(policy_results)

        blocking_failures = [
            pr for pr in policy_results
            if not pr.passed and pr.severity == PolicySeverity.BLOCKING.value
        ]

        if blocking_failures:
            return self._reject_for_policy(
                request, trace, blocking_failures, provenance_builder
            )

        # Phase 3: Conditional admission check
        warnings = [
            pr for pr in policy_results
            if not pr.passed and pr.severity == PolicySeverity.WARNING.value
        ]

        conditional = (
            len(warnings) > 0
            and request.runtime_context.allow_conditionals
        )

        # Phase 4: Admission
        return self._admit(
            request, trace, warnings, conditional, provenance_builder
        )

    def evaluate_or_raise(
        self,
        request: ExecutionAdmissionRequest,
    ) -> ExecutionAdmissionResult:
        """
        Evaluate and raise AdmissionDeniedError on rejection.

        Convenience method for strict admission mode.
        """
        result = self.evaluate(request)

        if result.rejected:
            raise AdmissionDeniedError(
                message=result.rejection.message if result.rejection else "Admission denied",
                policy_violations=[
                    pv.policy_id for pv in result.rejection.policy_violations
                ] if result.rejection else [],
                details=result.rejection.to_dict() if result.rejection else {},
            )

        return result

    def _validate_request_structure(
        self,
        request: ExecutionAdmissionRequest,
    ) -> None:
        """Validate request structure before evaluation."""
        errors = []

        if request.certified_topology is None:
            errors.append("certified_topology is required")

        if request.runtime_context is None:
            errors.append("runtime_context is required")

        if errors:
            raise InvalidAdmissionRequestError(
                message="Invalid admission request",
                validation_errors=errors,
            )

    def _verify_integrity(
        self,
        request: ExecutionAdmissionRequest,
        trace: AdmissionTrace,
    ) -> IntegrityVerificationResult:
        """Run integrity verification checks."""
        result = verify_integrity(request.certified_topology)

        for check in result.checks:
            trace.add_integrity_check(
                check_name=check.check_name,
                passed=check.passed,
                details=check.details,
            )

        return result

    def _evaluate_policies(
        self,
        request: ExecutionAdmissionRequest,
        trace: AdmissionTrace,
    ) -> List[PolicyEvaluationResult]:
        """Evaluate all policies against the request."""
        results = self._policy_registry.evaluate_all(request)

        for result in results:
            trace.add_policy_evaluation(result)

        return results

    def _reject_for_integrity(
        self,
        request: ExecutionAdmissionRequest,
        trace: AdmissionTrace,
        integrity_result: IntegrityVerificationResult,
        provenance_builder: ProvenanceBuilder,
    ) -> ExecutionAdmissionResult:
        """Create rejection result for integrity failure."""
        reason = self._map_integrity_to_rejection_reason(integrity_result)

        rejection = AdmissionRejection(
            reason=reason,
            message=integrity_result.message,
            integrity_details=integrity_result.to_dict(),
        )

        provenance_builder.record_rejection(rejection)
        provenance = provenance_builder.build()

        if self._record_provenance:
            get_admission_ledger().record(provenance)

        return ExecutionAdmissionResult.reject(
            request_id=request.request_id,
            trace_id=request.trace_id,
            trace=trace,
            rejection=rejection,
        )

    def _reject_for_policy(
        self,
        request: ExecutionAdmissionRequest,
        trace: AdmissionTrace,
        blocking_failures: List[PolicyEvaluationResult],
        provenance_builder: ProvenanceBuilder,
    ) -> ExecutionAdmissionResult:
        """Create rejection result for policy failure."""
        first_failure = blocking_failures[0]
        reason = self._map_policy_to_rejection_reason(first_failure)

        rejection = AdmissionRejection(
            reason=reason,
            message=first_failure.message,
            policy_violations=blocking_failures,
        )

        provenance_builder.record_rejection(rejection)
        provenance = provenance_builder.build()

        if self._record_provenance:
            get_admission_ledger().record(provenance)

        return ExecutionAdmissionResult.reject(
            request_id=request.request_id,
            trace_id=request.trace_id,
            trace=trace,
            rejection=rejection,
        )

    def _admit(
        self,
        request: ExecutionAdmissionRequest,
        trace: AdmissionTrace,
        warnings: List[PolicyEvaluationResult],
        conditional: bool,
        provenance_builder: ProvenanceBuilder,
    ) -> ExecutionAdmissionResult:
        """Create admission result."""
        authorized_adapters = self._determine_authorized_adapters(request)

        result = ExecutionAdmissionResult.admit(
            request_id=request.request_id,
            trace_id=request.trace_id,
            trace=trace,
            authorized_adapters=authorized_adapters,
            warnings=warnings,
            conditional=conditional,
        )

        provenance_builder.record_admission(
            authorized_adapters=authorized_adapters,
            authorization_token=result.authorization_token or "",
            warnings=warnings,
            conditional=conditional,
        )
        provenance = provenance_builder.build()

        if self._record_provenance:
            get_admission_ledger().record(provenance)

        return result

    def _determine_authorized_adapters(
        self,
        request: ExecutionAdmissionRequest,
    ) -> List[str]:
        """Determine which adapters are authorized for this execution."""
        context = request.runtime_context
        available = context.available_adapter_ids

        if context.requested_adapter_id:
            if context.requested_adapter_id in available:
                return [context.requested_adapter_id]
            return []

        if request.requested_adapters:
            return [a for a in request.requested_adapters if a in available]

        return list(available)

    def _map_integrity_to_rejection_reason(
        self,
        result: IntegrityVerificationResult,
    ) -> RejectionReason:
        """Map integrity violation to rejection reason."""
        violation_type = result.violation_type or ""

        if "CERTIFICATION_CHAIN" in violation_type:
            return RejectionReason.UNCERTIFIED_TOPOLOGY
        if "TOPOLOGY_IMMUTABLE" in violation_type:
            return RejectionReason.TOPOLOGY_MUTATED
        if "VALIDATION_SIGNATURE" in violation_type:
            return RejectionReason.SIGNATURE_MISMATCH

        return RejectionReason.INTEGRITY_VIOLATION

    def _map_policy_to_rejection_reason(
        self,
        result: PolicyEvaluationResult,
    ) -> RejectionReason:
        """Map policy failure to rejection reason."""
        policy_id = result.policy_id

        if "uncertified" in policy_id:
            return RejectionReason.UNCERTIFIED_TOPOLOGY
        if "adapter" in policy_id:
            return RejectionReason.ADAPTER_UNAVAILABLE
        if "runtime" in policy_id or "prototype" in policy_id:
            return RejectionReason.RUNTIME_INCOMPATIBLE
        if "signature" in policy_id:
            return RejectionReason.SIGNATURE_MISMATCH

        return RejectionReason.POLICY_VIOLATION


def get_admission_controller(
    policy_registry: Optional[AdmissionPolicyRegistry] = None,
) -> ExecutionAdmissionController:
    """Get an admission controller with optional custom policies."""
    return ExecutionAdmissionController(policy_registry=policy_registry)
