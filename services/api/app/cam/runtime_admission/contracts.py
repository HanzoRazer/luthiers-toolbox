"""
Runtime Admission Contracts.

Sprint: MRP-5M
Status: PROTOTYPE

Data contracts for runtime admission control.
These define the request/response structure for admission evaluation.

ARCHITECTURAL PRINCIPLE:
    Certification ≠ Admission
    Certification approves topology correctness.
    Admission authorizes runtime execution.

A certified topology may still be rejected for admission if:
    - runtime context is incompatible,
    - required adapter unavailable,
    - integrity violated after certification,
    - runtime policy prohibits execution.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid


class AdmissionDecision(str, Enum):
    """Decision outcomes for admission evaluation."""

    ADMITTED = "ADMITTED"  # Execution authorized
    REJECTED = "REJECTED"  # Execution denied
    CONDITIONALLY_ADMITTED = "CONDITIONALLY_ADMITTED"  # Admitted with warnings


class RuntimeTier(str, Enum):
    """Runtime execution tiers."""

    PROTOTYPE = "PROTOTYPE"  # Bounded prototype execution
    PRODUCTION = "PRODUCTION"  # Full production execution (future)


class ExecutionMode(str, Enum):
    """Execution mode constraints."""

    DETERMINISTIC = "DETERMINISTIC"  # Reproducible execution required
    BEST_EFFORT = "BEST_EFFORT"  # Allow non-deterministic fallbacks (future)


class RejectionReason(str, Enum):
    """Classification of rejection reasons."""

    UNCERTIFIED_TOPOLOGY = "UNCERTIFIED_TOPOLOGY"
    INTEGRITY_VIOLATION = "INTEGRITY_VIOLATION"
    POLICY_VIOLATION = "POLICY_VIOLATION"
    ADAPTER_UNAVAILABLE = "ADAPTER_UNAVAILABLE"
    RUNTIME_INCOMPATIBLE = "RUNTIME_INCOMPATIBLE"
    SIGNATURE_MISMATCH = "SIGNATURE_MISMATCH"
    TOPOLOGY_MUTATED = "TOPOLOGY_MUTATED"


@dataclass
class RuntimeExecutionContext:
    """
    Context for runtime execution.

    Describes the execution environment and constraints.
    """

    runtime_tier: RuntimeTier = RuntimeTier.PROTOTYPE
    execution_mode: ExecutionMode = ExecutionMode.DETERMINISTIC
    requested_adapter_id: Optional[str] = None
    available_adapter_ids: List[str] = field(default_factory=list)
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    allow_conditionals: bool = False
    environment_label: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "runtime_tier": self.runtime_tier.value,
            "execution_mode": self.execution_mode.value,
            "requested_adapter_id": self.requested_adapter_id,
            "available_adapter_ids": self.available_adapter_ids,
            "request_id": self.request_id,
            "trace_id": self.trace_id,
            "allow_conditionals": self.allow_conditionals,
            "environment_label": self.environment_label,
        }


@dataclass
class ExecutionAdmissionRequest:
    """
    Request for execution admission.

    Wraps CertifiedTopology with runtime context and trace metadata.
    The controller evaluates this request object, not naked topology.
    """

    certified_topology: Any  # CertifiedTopology (Any to avoid circular import)
    runtime_context: RuntimeExecutionContext
    requested_pipeline: Optional[str] = None
    requested_adapters: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.runtime_context is None:
            self.runtime_context = RuntimeExecutionContext()

    @property
    def request_id(self) -> str:
        """Request ID from runtime context."""
        return self.runtime_context.request_id

    @property
    def trace_id(self) -> str:
        """Trace ID from runtime context."""
        return self.runtime_context.trace_id

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "certified_topology": (
                self.certified_topology.to_dict()
                if hasattr(self.certified_topology, "to_dict")
                else str(self.certified_topology)
            ),
            "runtime_context": self.runtime_context.to_dict(),
            "requested_pipeline": self.requested_pipeline,
            "requested_adapters": self.requested_adapters,
            "metadata": self.metadata,
        }


@dataclass
class PolicyEvaluationResult:
    """Result of a single policy evaluation."""

    policy_id: str
    passed: bool
    severity: str  # BLOCKING, WARNING, INFO
    message: str
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "policy_id": self.policy_id,
            "passed": self.passed,
            "severity": self.severity,
            "message": self.message,
            "details": self.details,
        }


@dataclass
class AdmissionRejection:
    """
    Details of an admission rejection.

    First-class artifact for rejection tracking.
    """

    reason: RejectionReason
    message: str
    policy_violations: List[PolicyEvaluationResult] = field(default_factory=list)
    integrity_details: Optional[Dict[str, Any]] = None
    timestamp_iso: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "reason": self.reason.value,
            "message": self.message,
            "policy_violations": [pv.to_dict() for pv in self.policy_violations],
            "integrity_details": self.integrity_details,
            "timestamp_iso": self.timestamp_iso,
        }


@dataclass
class AdmissionTrace:
    """
    Trace of admission evaluation.

    Records the full evaluation path for observability.
    """

    request_id: str
    trace_id: str
    started_at: str
    completed_at: Optional[str] = None
    integrity_checks: List[Dict[str, Any]] = field(default_factory=list)
    policy_evaluations: List[PolicyEvaluationResult] = field(default_factory=list)
    decision_basis: Optional[str] = None

    def add_integrity_check(
        self,
        check_name: str,
        passed: bool,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record an integrity check result."""
        self.integrity_checks.append({
            "check_name": check_name,
            "passed": passed,
            "details": details or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def add_policy_evaluation(self, result: PolicyEvaluationResult) -> None:
        """Record a policy evaluation result."""
        self.policy_evaluations.append(result)

    def complete(self, decision_basis: str) -> None:
        """Mark trace as complete."""
        self.completed_at = datetime.now(timezone.utc).isoformat()
        self.decision_basis = decision_basis

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "request_id": self.request_id,
            "trace_id": self.trace_id,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "integrity_checks": self.integrity_checks,
            "policy_evaluations": [pe.to_dict() for pe in self.policy_evaluations],
            "decision_basis": self.decision_basis,
        }


@dataclass
class ExecutionAdmissionResult:
    """
    Result of execution admission evaluation.

    Explicit artifact — never implicit booleans or hidden flags.
    """

    decision: AdmissionDecision
    request_id: str
    trace_id: str
    trace: AdmissionTrace
    rejection: Optional[AdmissionRejection] = None
    warnings: List[PolicyEvaluationResult] = field(default_factory=list)
    authorized_adapters: List[str] = field(default_factory=list)
    authorization_token: Optional[str] = None
    timestamp_iso: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def admitted(self) -> bool:
        """Check if execution was admitted."""
        return self.decision in (
            AdmissionDecision.ADMITTED,
            AdmissionDecision.CONDITIONALLY_ADMITTED,
        )

    @property
    def rejected(self) -> bool:
        """Check if execution was rejected."""
        return self.decision == AdmissionDecision.REJECTED

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "decision": self.decision.value,
            "admitted": self.admitted,
            "rejected": self.rejected,
            "request_id": self.request_id,
            "trace_id": self.trace_id,
            "trace": self.trace.to_dict(),
            "rejection": self.rejection.to_dict() if self.rejection else None,
            "warnings": [w.to_dict() for w in self.warnings],
            "authorized_adapters": self.authorized_adapters,
            "authorization_token": self.authorization_token,
            "timestamp_iso": self.timestamp_iso,
            "metadata": self.metadata,
        }

    @classmethod
    def admit(
        cls,
        request_id: str,
        trace_id: str,
        trace: AdmissionTrace,
        authorized_adapters: List[str],
        warnings: Optional[List[PolicyEvaluationResult]] = None,
        conditional: bool = False,
    ) -> "ExecutionAdmissionResult":
        """Create an admission result."""
        decision = (
            AdmissionDecision.CONDITIONALLY_ADMITTED
            if conditional
            else AdmissionDecision.ADMITTED
        )
        trace.complete(f"Admitted: {decision.value}")

        return cls(
            decision=decision,
            request_id=request_id,
            trace_id=trace_id,
            trace=trace,
            warnings=warnings or [],
            authorized_adapters=authorized_adapters,
            authorization_token=str(uuid.uuid4()),
        )

    @classmethod
    def reject(
        cls,
        request_id: str,
        trace_id: str,
        trace: AdmissionTrace,
        rejection: AdmissionRejection,
    ) -> "ExecutionAdmissionResult":
        """Create a rejection result."""
        trace.complete(f"Rejected: {rejection.reason.value}")

        return cls(
            decision=AdmissionDecision.REJECTED,
            request_id=request_id,
            trace_id=trace_id,
            trace=trace,
            rejection=rejection,
        )
