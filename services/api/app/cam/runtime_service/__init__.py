"""
Certified Runtime Service.

Sprint: MRP-5Q/R
Status: PROTOTYPE

The safe internal entrypoint for the governed runtime spine.

Usage:
    from app.cam.runtime_service import (
        CertifiedRuntimeService,
        CertifiedRuntimeRequest,
        CertifiedRuntimeResult,
    )
    from app.cam.topology_validation import certify_topology

    # Certify topology first
    certified = certify_topology(topology_dict)

    # Create request
    request = CertifiedRuntimeRequest(
        certified_topology=certified,
        adapter_id="mock",
    )

    # Execute service
    service = CertifiedRuntimeService()
    result = service.execute(request)

    if result.success:
        print(f"Artifact hash: {result.artifact_hash}")
        print(f"Replay bundle ID: {result.replay_bundle_id}")
    else:
        print(f"Failed: {result.error_message}")

ARCHITECTURAL BOUNDARY:
    This service orchestrates the runtime spine.
    It does NOT:
    - Create topology semantics
    - Certify topology
    - Make admission decisions
    - Record provenance lineage

    It wires together:
    - topology_validation (certification)
    - runtime_admission (gate control)
    - runtime_provenance (lineage recording)

WARNING:
    This is an INTERNAL developer surface.
    It is NOT a public HTTP API.
    It is NOT machine authorization.
"""

# Contracts
from .contracts import (
    ArtifactIntent,
    CertifiedRuntimeRequest,
    CertifiedRuntimeResult,
    ServiceExecutionStatus,
)

# Exceptions
from .exceptions import (
    AdapterUnavailableError,
    AdmissionRejectedError,
    CapabilityResolutionFailedError,
    InvalidRequestError,
    ProvenanceRecordingError,
    RuntimeServiceError,
    TranslationFailedError,
    UncertifiedTopologyError,
)

# Adapters
from .adapters import (
    AdapterExecutionResult,
    AdapterRegistry,
    MockRuntimeAdapter,
    RuntimeAdapter,
    get_adapter,
    get_adapter_registry,
    is_adapter_available,
    list_available_adapters,
)

# Service
from .service import (
    CertifiedRuntimeService,
    execute_certified_runtime,
    get_certified_runtime_service,
)

__all__ = [
    # Contracts
    "ArtifactIntent",
    "CertifiedRuntimeRequest",
    "CertifiedRuntimeResult",
    "ServiceExecutionStatus",
    # Exceptions
    "AdapterUnavailableError",
    "AdmissionRejectedError",
    "CapabilityResolutionFailedError",
    "InvalidRequestError",
    "ProvenanceRecordingError",
    "RuntimeServiceError",
    "TranslationFailedError",
    "UncertifiedTopologyError",
    # Adapters
    "AdapterExecutionResult",
    "AdapterRegistry",
    "MockRuntimeAdapter",
    "RuntimeAdapter",
    "get_adapter",
    "get_adapter_registry",
    "is_adapter_available",
    "list_available_adapters",
    # Service
    "CertifiedRuntimeService",
    "execute_certified_runtime",
    "get_certified_runtime_service",
]
