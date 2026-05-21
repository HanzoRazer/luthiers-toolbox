"""
Runtime Admission Controller.

Sprint: MRP-5M
Status: PROTOTYPE
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

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
from .integrity import verify_all
from .policies import AdmissionPolicyRegistry, PolicySeverity, get_default_policy_registry


@dataclass
class AdmissionConfiguration:
    strict_mode: bool = True
    allow_conditional_admission: bool = False
    require_all_policies_pass: bool = True
    log_decisions: bool = True
    record_provenance: bool = True


class ExecutionAdmissionController:
    """
    Controls admission of certified topologies to runtime execution.

    Responsibilities:
    - Verify certification integrity
    - Evaluate admission policies
    - Issue admission decisions
    - Generate admission traces
    """

    def __init__(
        self,
        policy_registry: Optional[AdmissionPolicyRegistry] = None,
        config: Optional[AdmissionConfiguration] = None,
        record_provenance: bool = True,
    ):
        self._policy_registry = policy_registry or get_default_policy_registry()
        if config is None:
            config = AdmissionConfiguration(record_provenance=record_provenance)
        self._config = config

    @property
    def policy_registry(self) -> AdmissionPolicyRegistry:
        return self._policy_registry

    @property
    def config(self) -> AdmissionConfiguration:
        return self._config

    def evaluate(self, request: ExecutionAdmissionRequest) -> ExecutionAdmissionResult:
        """
        Evaluate an admission request and return a decision.

        Steps:
        1. Validate the request
        2. Verify certification integrity
        3. Evaluate admission policies
        4. Issue admission decision
        """
        trace = AdmissionTrace(
            request_id=request.request_id,
            trace_id=request.trace_id,
            started_at=datetime.now(timezone.utc).isoformat(),
        )

        try:
            self._validate_request(request)
        except InvalidAdmissionRequestError as e:
            return self._reject(
                request, trace,
                RejectionReason.UNCERTIFIED_TOPOLOGY,
                e.message,
            )

        integrity_result = verify_all(request.certified_topology)
        for check in integrity_result.checks:
            trace.add_integrity_check(
                check.check_name,
                check.passed,
                {"message": check.message},
            )

        if not integrity_result.passed:
            return self._reject(
                request, trace,
                RejectionReason.INTEGRITY_VIOLATION,
                integrity_result.message,
                integrity_details=integrity_result.to_dict(),
            )

        policy_results = self._policy_registry.evaluate_all(request)
        for result in policy_results:
            trace.add_policy_evaluation(result)

        blocking_failures = [
            r for r in policy_results
            if not r.passed and r.severity == PolicySeverity.BLOCKING.value
        ]
        warnings = [
            r for r in policy_results
            if not r.passed and r.severity == PolicySeverity.WARNING.value
        ]

        if blocking_failures:
            return self._reject(
                request, trace,
                RejectionReason.POLICY_VIOLATION,
                f"Policy violations: {', '.join(f.policy_id for f in blocking_failures)}",
                policy_violations=blocking_failures,
            )

        if warnings and not self._config.allow_conditional_admission:
            return self._admit(request, trace, warnings=warnings, conditional=False)

        if warnings and self._config.allow_conditional_admission:
            if request.runtime_context.allow_conditionals:
                return self._admit(request, trace, warnings=warnings, conditional=True)

        return self._admit(request, trace)

    def _validate_request(self, request: ExecutionAdmissionRequest) -> None:
        """Validate that the request is well-formed."""
        from ..topology_validation.contracts import CertifiedTopology

        if request.certified_topology is None:
            raise InvalidAdmissionRequestError("certified_topology is required")

        if not isinstance(request.certified_topology, CertifiedTopology):
            raise InvalidAdmissionRequestError(
                "Only CertifiedTopology may be submitted for admission"
            )

        if request.runtime_context is None:
            raise InvalidAdmissionRequestError("runtime_context is required")

    def _admit(
        self,
        request: ExecutionAdmissionRequest,
        trace: AdmissionTrace,
        warnings: Optional[List[PolicyEvaluationResult]] = None,
        conditional: bool = False,
    ) -> ExecutionAdmissionResult:
        """Create an admission result."""
        authorized_adapters = self._determine_authorized_adapters(request)

        return ExecutionAdmissionResult.admit(
            request_id=request.request_id,
            trace_id=request.trace_id,
            trace=trace,
            authorized_adapters=authorized_adapters,
            warnings=warnings,
            conditional=conditional,
        )

    def _reject(
        self,
        request: ExecutionAdmissionRequest,
        trace: AdmissionTrace,
        reason: RejectionReason,
        message: str,
        policy_violations: Optional[List[PolicyEvaluationResult]] = None,
        integrity_details: Optional[Dict[str, Any]] = None,
    ) -> ExecutionAdmissionResult:
        """Create a rejection result."""
        rejection = AdmissionRejection(
            reason=reason,
            message=message,
            policy_violations=policy_violations or [],
            integrity_details=integrity_details,
        )

        return ExecutionAdmissionResult.reject(
            request_id=request.request_id,
            trace_id=request.trace_id,
            trace=trace,
            rejection=rejection,
        )

    def _determine_authorized_adapters(
        self, request: ExecutionAdmissionRequest
    ) -> List[str]:
        """Determine which adapters are authorized for this request."""
        context = request.runtime_context
        requested = context.requested_adapter_id
        available = context.available_adapter_ids

        if requested and requested in available:
            return [requested]

        if request.requested_adapters:
            return [a for a in request.requested_adapters if a in available]

        return list(available) if available else []


def get_admission_controller(
    policy_registry: Optional[AdmissionPolicyRegistry] = None,
    config: Optional[AdmissionConfiguration] = None,
) -> ExecutionAdmissionController:
    """Factory function to create an admission controller."""
    return ExecutionAdmissionController(
        policy_registry=policy_registry,
        config=config,
    )
