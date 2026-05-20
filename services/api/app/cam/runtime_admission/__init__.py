"""
Runtime Admission Control.

Sprint: MRP-5M
Status: PROTOTYPE

Provides runtime admission control for the topology execution pipeline.
Ensures only certified, valid topology enters executable runtime flow.

ARCHITECTURAL PRINCIPLE:
    Certification ≠ Admission

    Certification (MRP-5I): topology correctness approved
    Admission (MRP-5M): runtime execution authorized

    A certified topology may still be rejected for admission if:
    - runtime context is incompatible
    - required adapter unavailable
    - integrity violated after certification
    - runtime policy prohibits execution

Usage:
    from app.cam.runtime_admission import (
        ExecutionAdmissionController,
        ExecutionAdmissionRequest,
        RuntimeExecutionContext,
    )

    # Create request
    context = RuntimeExecutionContext(
        available_adapter_ids=["mock"],
    )
    request = ExecutionAdmissionRequest(
        certified_topology=certified,
        runtime_context=context,
    )

    # Evaluate admission
    controller = ExecutionAdmissionController()
    result = controller.evaluate(request)

    if result.admitted:
        print(f"Admitted with adapters: {result.authorized_adapters}")
    else:
        print(f"Rejected: {result.rejection.message}")
"""

# Contracts
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

# Controller
from .controller import (
    ExecutionAdmissionController,
    get_admission_controller,
)

# Exceptions
from .exceptions import (
    AdmissionDeniedError,
    AdmissionError,
    IntegrityViolationError,
    InvalidAdmissionRequestError,
    PolicyViolationError,
    UncertifiedTopologyError,
)

# Integrity
from .integrity import (
    IntegrityCheckResult,
    IntegrityVerificationResult,
    compute_topology_hash,
    verify_all,
    verify_certification_chain,
    verify_or_raise,
    verify_topology_immutable,
    verify_validation_signature,
)

# Policies
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

# Provenance
from .provenance import (
    AdmissionLedger,
    AdmissionProvenance,
    ProvenanceBuilder,
    get_admission_ledger,
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
    "verify_or_raise",
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
    # Provenance
    "AdmissionLedger",
    "AdmissionProvenance",
    "ProvenanceBuilder",
    "get_admission_ledger",
]
