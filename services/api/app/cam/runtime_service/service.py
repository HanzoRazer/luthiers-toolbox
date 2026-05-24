"""
Certified Runtime Service.

Sprint: MRP-5Q/R + MRP-5V
Status: PROTOTYPE

The safe internal entrypoint for the governed runtime spine.

Orchestrates:
    CertifiedTopology
    -> ExecutionAdmissionController
    -> CapabilityResolver (MRP-5V)
    -> Adapter execution
    -> RuntimeProvenanceRecorder
    -> RuntimeReplayBundle

ARCHITECTURAL PRINCIPLE:
    This service orchestrates. It does not:
    - Create topology semantics (that's topology_builder)
    - Certify topology (that's topology_validation)
    - Make admission decisions (that's runtime_admission)
    - Resolve capability eligibility (that's runtime_capabilities)
    - Record lineage (that's runtime_provenance)

    It wires these together with proper gate ordering.
"""

import time
from typing import Optional

from app.cam.topology_validation import CertifiedTopology
from app.cam.runtime_capabilities import (
    CapabilityResolver,
    CapabilityResolutionResult,
    ResolutionContext,
    ResolutionStatus,
    get_capability_resolver,
)
from app.cam.runtime_admission import (
    AdmissionDecision,
    ExecutionAdmissionController,
    ExecutionAdmissionRequest,
    ExecutionMode,
    RuntimeExecutionContext,
    RuntimeTier,
    get_admission_controller,
)
from app.cam.runtime_provenance import (
    RuntimeReplayBundle,
    build_replay_bundle_from_pipeline_outputs,
    build_minimal_validation_lineage,
    build_minimal_admission_lineage,
    build_minimal_artifact_lineage,
    build_minimal_trace_events,
    stable_json_dumps,
    stable_hash_string,
)

from .adapters import (
    AdapterRegistry,
    get_adapter_registry,
    get_adapter,
    is_adapter_available,
    list_available_adapters,
)
from .contracts import (
    ArtifactIntent,
    CertifiedRuntimeRequest,
    CertifiedRuntimeResult,
    ServiceExecutionStatus,
)
from .exceptions import (
    AdapterUnavailableError,
    AdmissionRejectedError,
    CapabilityResolutionFailedError,
    InvalidRequestError,
    ProvenanceRecordingError,
    RuntimeServiceError,
    UncertifiedTopologyError,
)


class CertifiedRuntimeService:
    """
    Safe internal entrypoint for governed runtime execution.

    Gate order (MRP-5V):
    1. Request validation
    2. Certification check
    3. Admission control
    4. Capability resolution (MRP-5V)
    5. Adapter execution
    6. Provenance recording
    7. Bundle creation

    Misuse rejection:
    - Raw topology: INVALID_REQUEST
    - Uncertified topology: INVALID_REQUEST (TypeError in request)
    - Unavailable adapter: INVALID_REQUEST
    - Admission rejected: ADMISSION_REJECTED
    - Capability rejected: CAPABILITY_REJECTED (MRP-5V)
    - Fabricated certification: caught by admission integrity checks
    """

    def __init__(
        self,
        admission_controller: Optional[ExecutionAdmissionController] = None,
        adapter_registry: Optional[AdapterRegistry] = None,
        capability_resolver: Optional[CapabilityResolver] = None,
    ):
        self._admission_controller = admission_controller or get_admission_controller()
        self._adapter_registry = adapter_registry or get_adapter_registry()
        self._capability_resolver = capability_resolver or get_capability_resolver()
        self._execution_count = 0

    def execute(self, request: CertifiedRuntimeRequest) -> CertifiedRuntimeResult:
        """
        Execute the certified runtime pipeline.

        Args:
            request: Certified runtime request with topology and context

        Returns:
            CertifiedRuntimeResult with status, artifact info, and replay bundle
        """
        start_time = time.perf_counter()

        try:
            self._validate_request(request)

            admission_result = self._run_admission(request)

            if admission_result.decision != AdmissionDecision.ADMITTED:
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                return CertifiedRuntimeResult.failure_result(
                    request_id=request.request_id,
                    status=ServiceExecutionStatus.ADMISSION_REJECTED,
                    error_message=f"Admission rejected: {admission_result.decision.value}",
                    admission_decision=admission_result.decision,
                    error_details={
                        "rejections": [
                            r.to_dict() for r in (admission_result.rejections or [])
                        ]
                    },
                    execution_time_ms=elapsed_ms,
                )

            # MRP-5V: Capability resolution gate
            capability_result = self._run_capability_resolution(request)
            if capability_result is not None and not capability_result.is_allowed:
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                return CertifiedRuntimeResult.failure_result(
                    request_id=request.request_id,
                    status=ServiceExecutionStatus.CAPABILITY_REJECTED,
                    error_message=f"Capability resolution failed: {capability_result.status.value}",
                    admission_decision=admission_result.decision,
                    error_details={
                        "capability_id": capability_result.requested_capability_id,
                        "rejection_reasons": capability_result.rejection_reasons,
                        "resolution_report": capability_result.to_dict(),
                    },
                    execution_time_ms=elapsed_ms,
                )

            adapter_result = self._run_adapter(request)

            replay_bundle = self._record_provenance(
                request=request,
                admission_decision=admission_result.decision,
                artifact_id=adapter_result.artifact_id,
                artifact_hash=adapter_result.artifact_hash,
                artifact_size=adapter_result.artifact_size,
                artifact_type=adapter_result.artifact_type,
            )

            elapsed_ms = (time.perf_counter() - start_time) * 1000
            self._execution_count += 1

            return CertifiedRuntimeResult.success_result(
                request_id=request.request_id,
                admission_decision=admission_result.decision,
                artifact_id=adapter_result.artifact_id,
                artifact_hash=adapter_result.artifact_hash,
                artifact_size_bytes=adapter_result.artifact_size,
                replay_bundle=replay_bundle,
                execution_time_ms=elapsed_ms,
                capability_resolution_report=(
                    capability_result.to_dict() if capability_result else None
                ),
            )

        except RuntimeServiceError as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            return CertifiedRuntimeResult.failure_result(
                request_id=request.request_id,
                status=ServiceExecutionStatus.INVALID_REQUEST,
                error_message=e.message,
                error_details=e.details,
                execution_time_ms=elapsed_ms,
            )

        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            return CertifiedRuntimeResult.failure_result(
                request_id=request.request_id,
                status=ServiceExecutionStatus.ADAPTER_FAILED,
                error_message=str(e),
                error_details={"exception_type": type(e).__name__},
                execution_time_ms=elapsed_ms,
            )

    def _validate_request(self, request: CertifiedRuntimeRequest) -> None:
        """Validate request before processing."""
        if not isinstance(request.certified_topology, CertifiedTopology):
            raise UncertifiedTopologyError(
                f"Expected CertifiedTopology, got {type(request.certified_topology).__name__}"
            )

        if not is_adapter_available(request.adapter_id):
            raise AdapterUnavailableError(
                request.adapter_id,
                list_available_adapters(),
            )

    def _run_admission(self, request: CertifiedRuntimeRequest):
        """Run admission control."""
        context = RuntimeExecutionContext(
            requested_adapter_id=request.adapter_id,
            available_adapter_ids=list_available_adapters(),
            execution_mode=request.execution_mode,
            runtime_tier=request.runtime_tier,
            request_id=request.request_id,
            trace_id=request.trace_id,
        )

        admission_request = ExecutionAdmissionRequest(
            certified_topology=request.certified_topology,
            runtime_context=context,
        )

        return self._admission_controller.evaluate(admission_request)

    def _run_capability_resolution(
        self,
        request: CertifiedRuntimeRequest,
    ) -> Optional[CapabilityResolutionResult]:
        """
        Run capability resolution (MRP-5V).

        If request.capability_id is set, resolves the capability
        through the registry and policy federation.

        Args:
            request: Runtime request

        Returns:
            CapabilityResolutionResult if capability_id specified,
            None otherwise (backward compatibility)
        """
        if not request.capability_id:
            # No capability specified — skip resolution (backward compat)
            return None

        context = ResolutionContext(
            is_replay_mode=request.is_replay_mode,
            require_deterministic=(
                request.execution_mode == ExecutionMode.DETERMINISTIC
            ),
            require_replay_safe=request.is_replay_mode,
            request_id=request.request_id,
            trace_id=request.trace_id,
        )

        return self._capability_resolver.resolve(request.capability_id, context)

    def _run_adapter(self, request: CertifiedRuntimeRequest):
        """Run adapter execution."""
        adapter = get_adapter(request.adapter_id)
        if adapter is None:
            raise AdapterUnavailableError(
                request.adapter_id,
                list_available_adapters(),
            )

        topology_dict = request.certified_topology.topology_dict
        topology_hash = stable_hash_string(stable_json_dumps(topology_dict))

        return adapter.execute(
            topology_hash=topology_hash,
            artifact_intent=request.artifact_intent.value,
            metadata={
                "request_id": request.request_id,
                "trace_id": request.trace_id,
            },
        )

    def _record_provenance(
        self,
        request: CertifiedRuntimeRequest,
        admission_decision: AdmissionDecision,
        artifact_id: str,
        artifact_hash: str,
        artifact_size: int,
        artifact_type: str,
    ) -> RuntimeReplayBundle:
        """Record provenance and create replay bundle."""
        topology_dict = request.certified_topology.topology_dict

        validation_lineage = build_minimal_validation_lineage(
            topology_dict=topology_dict,
            passed=True,
        )

        admission_lineage = build_minimal_admission_lineage(
            decision=admission_decision.value,
            authorized_adapters=[request.adapter_id],
        )

        artifact_lineage = build_minimal_artifact_lineage(
            artifact_type=artifact_type,
            adapter_id=request.adapter_id,
            content=artifact_hash.encode("utf-8"),  # Use hash as content proxy
        )
        artifact_lineage.artifact_id = artifact_id
        artifact_lineage.content_hash = artifact_hash
        artifact_lineage.content_size_bytes = artifact_size

        return build_replay_bundle_from_pipeline_outputs(
            topology_dict=topology_dict,
            validation_lineage=validation_lineage,
            admission_lineage=admission_lineage,
            artifact_lineage=artifact_lineage,
            adapter_id=request.adapter_id,
        )

    @property
    def execution_count(self) -> int:
        """Number of successful executions."""
        return self._execution_count


_global_service: Optional[CertifiedRuntimeService] = None


def get_certified_runtime_service() -> CertifiedRuntimeService:
    """Get the global certified runtime service instance."""
    global _global_service
    if _global_service is None:
        _global_service = CertifiedRuntimeService()
    return _global_service


def execute_certified_runtime(
    request: CertifiedRuntimeRequest,
) -> CertifiedRuntimeResult:
    """Convenience function to execute certified runtime."""
    return get_certified_runtime_service().execute(request)
