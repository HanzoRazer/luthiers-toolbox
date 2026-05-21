"""
Runtime Admission Control.

Sprint: MRP-5M
Status: PROTOTYPE

Provides admission control for certified topologies entering runtime execution.
"""

from .contracts import (
    AdmissionDecision,
    AdmissionRejection,
    AdmissionTrace,
    ExecutionAdmissionRequest,
    ExecutionAdmissionResult,
    ExecutionMode,
    PolicyEvaluationResult,
    RejectionReason,
    RuntimeExecutionContext,
    RuntimeTier,
)
from .controller import (
    AdmissionConfiguration,
    ExecutionAdmissionController,
    get_admission_controller,
)
from .exceptions import (
    AdmissionDeniedError,
    AdmissionError,
    IntegrityViolationError,
    InvalidAdmissionRequestError,
    PolicyViolationError,
    UncertifiedTopologyError,
)
from .integrity import (
    IntegrityCheckResult,
    IntegrityVerificationResult,
    compute_topology_hash,
    verify_all,
    verify_certification_chain,
    verify_topology_immutable,
    verify_validation_signature,
)
from .policies import (
    AdapterAvailablePolicy,
    AdmissionPolicy,
    AdmissionPolicyRegistry,
    DeterministicOnlyPolicy,
    NoUncertifiedExecutionPolicy,
    PolicyResult,
    PolicySeverity,
    PrototypeRuntimeOnlyPolicy,
    SignatureIntegrityPolicy,
    ValidationRequiredPolicy,
    get_default_policy_registry,
)

__all__ = [
    # Contracts
    "AdmissionDecision",
    "AdmissionRejection",
    "AdmissionTrace",
    "ExecutionAdmissionRequest",
    "ExecutionAdmissionResult",
    "ExecutionMode",
    "PolicyEvaluationResult",
    "RejectionReason",
    "RuntimeExecutionContext",
    "RuntimeTier",
    # Controller
    "AdmissionConfiguration",
    "ExecutionAdmissionController",
    "get_admission_controller",
    # Exceptions
    "AdmissionDeniedError",
    "AdmissionError",
    "IntegrityViolationError",
    "InvalidAdmissionRequestError",
    "PolicyViolationError",
    "UncertifiedTopologyError",
    # Integrity
    "IntegrityCheckResult",
    "IntegrityVerificationResult",
    "compute_topology_hash",
    "verify_all",
    "verify_certification_chain",
    "verify_topology_immutable",
    "verify_validation_signature",
    # Policies
    "AdapterAvailablePolicy",
    "AdmissionPolicy",
    "AdmissionPolicyRegistry",
    "DeterministicOnlyPolicy",
    "NoUncertifiedExecutionPolicy",
    "PolicyResult",
    "PolicySeverity",
    "PrototypeRuntimeOnlyPolicy",
    "SignatureIntegrityPolicy",
    "ValidationRequiredPolicy",
    "get_default_policy_registry",
]
