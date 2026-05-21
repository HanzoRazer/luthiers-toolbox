"""
Runtime Provenance Recorder.

Sprint: MRP-5N
Status: PROTOTYPE

Records runtime artifact provenance from pipeline execution.
Captures validation, admission, translator, adapter, and artifact lineage.

ARCHITECTURAL PRINCIPLE:
    The recorder captures.
    The recorder does not:
    - mutate topology,
    - reinterpret validation,
    - reinterpret admission,
    - infer missing data.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TYPE_CHECKING
import uuid

from .contracts import (
    AdmissionLineage,
    ArtifactLineage,
    RuntimeArtifactProvenance,
    RuntimeReplayBundle,
    RuntimeTraceEvent,
    TraceEventType,
    ValidationLineage,
)
from .exceptions import ProvenanceRecordingError
from .serialization import stable_hash_bytes, stable_hash_model

if TYPE_CHECKING:
    from ..topology_validation.contracts import CertifiedTopology
    from ..runtime_admission.contracts import ExecutionAdmissionResult


class RuntimeProvenanceRecorder:
    """
    Records runtime artifact provenance.

    Accepts explicit inputs and produces a RuntimeReplayBundle.
    Does not require full pipeline orchestration.

    Usage:
        recorder = RuntimeProvenanceRecorder()
        bundle = recorder.record(
            certified_topology=certified,
            admission_result=admission_result,
            artifact=artifact,
            translator_id="step_acoustic",
            adapter_id="mock",
        )
    """

    def __init__(self):
        self._sequence_counter = 0

    def record(
        self,
        certified_topology: Any,  # CertifiedTopology
        admission_result: Any,  # ExecutionAdmissionResult
        artifact: Any,  # RuntimeArtifact or compatible
        translator_id: str,
        adapter_id: str,
        trace_events: Optional[List[RuntimeTraceEvent]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> RuntimeReplayBundle:
        """
        Record provenance and create a replay bundle.

        Args:
            certified_topology: The certified topology that was executed
            admission_result: The admission result authorizing execution
            artifact: The produced artifact
            translator_id: ID of translator used
            adapter_id: ID of adapter used
            trace_events: Optional pre-recorded trace events
            metadata: Optional additional metadata

        Returns:
            RuntimeReplayBundle containing complete provenance

        Raises:
            ProvenanceRecordingError: If required inputs are missing
        """
        self._validate_inputs(
            certified_topology, admission_result, artifact, translator_id, adapter_id
        )

        run_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()

        validation_lineage = self._extract_validation_lineage(certified_topology)
        admission_lineage = self._extract_admission_lineage(admission_result)
        artifact_lineage = self._extract_artifact_lineage(artifact)

        if trace_events is None:
            trace_events = self._generate_trace_events(
                validation_lineage, admission_lineage, artifact_lineage
            )

        source_topology_id = self._extract_topology_id(certified_topology)
        source_topology_hash = self._extract_topology_hash(certified_topology)

        provenance = RuntimeArtifactProvenance(
            run_id=run_id,
            source_topology_id=source_topology_id,
            source_topology_hash=source_topology_hash,
            validation_lineage=validation_lineage,
            admission_lineage=admission_lineage,
            artifact_lineage=artifact_lineage,
            translator_id=translator_id,
            adapter_id=adapter_id,
            trace_events=trace_events,
            created_at=created_at,
        )

        replayable, constraints = self._assess_replayability(
            certified_topology, admission_result, artifact, adapter_id
        )

        bundle = RuntimeReplayBundle(
            bundle_id=str(uuid.uuid4()),
            provenance=provenance,
            replayable=replayable,
            replay_constraints=constraints,
        )

        return bundle

    def _validate_inputs(
        self,
        certified_topology: Any,
        admission_result: Any,
        artifact: Any,
        translator_id: str,
        adapter_id: str,
    ) -> None:
        """Validate required inputs are present."""
        missing = []

        if certified_topology is None:
            missing.append("certified_topology")

        if admission_result is None:
            missing.append("admission_result")

        if artifact is None:
            missing.append("artifact")

        if not translator_id:
            missing.append("translator_id")

        if not adapter_id:
            missing.append("adapter_id")

        if missing:
            raise ProvenanceRecordingError(
                message=f"Missing required inputs: {', '.join(missing)}",
                missing_fields=missing,
            )

    def _extract_validation_lineage(self, certified_topology: Any) -> ValidationLineage:
        """Extract validation lineage from certified topology."""
        validation = getattr(certified_topology, "validation", None)
        signature = getattr(certified_topology, "signature", None)

        request_id = "unknown"
        tier = "PROTOTYPE"
        passed = False
        input_hash = ""
        validation_hash = ""
        blocking_count = 0
        major_count = 0

        if validation:
            request_id = getattr(validation, "request_id", "unknown")
            tier_val = getattr(validation, "tier", None)
            tier = tier_val.value if hasattr(tier_val, "value") else str(tier_val or "PROTOTYPE")
            passed = getattr(validation, "passed", False)
            blocking_count = getattr(validation, "blocking_count", 0)
            major_count = getattr(validation, "major_count", 0)

        if signature:
            input_hash = getattr(signature, "input_hash", "")
            validation_hash = getattr(signature, "validation_hash", "")

        return ValidationLineage(
            request_id=request_id,
            tier=tier,
            passed=passed,
            signature_input_hash=input_hash,
            signature_validation_hash=validation_hash,
            blocking_count=blocking_count,
            major_count=major_count,
        )

    def _extract_admission_lineage(self, admission_result: Any) -> AdmissionLineage:
        """Extract admission lineage from admission result."""
        admission_id = str(uuid.uuid4())
        decision = "UNKNOWN"
        authorization_token = None
        runtime_tier = "PROTOTYPE"
        execution_mode = "DETERMINISTIC"
        authorized_adapters = []

        if hasattr(admission_result, "trace"):
            trace = admission_result.trace
            if hasattr(trace, "request_id"):
                admission_id = trace.request_id

        if hasattr(admission_result, "decision"):
            decision_val = admission_result.decision
            decision = decision_val.value if hasattr(decision_val, "value") else str(decision_val)

        if hasattr(admission_result, "authorization_token"):
            authorization_token = admission_result.authorization_token

        if hasattr(admission_result, "authorized_adapters"):
            authorized_adapters = list(admission_result.authorized_adapters)

        return AdmissionLineage(
            admission_id=admission_id,
            decision=decision,
            authorization_token=authorization_token,
            runtime_tier=runtime_tier,
            execution_mode=execution_mode,
            authorized_adapters=authorized_adapters,
        )

    def _extract_artifact_lineage(self, artifact: Any) -> ArtifactLineage:
        """Extract artifact lineage from artifact."""
        artifact_id = str(uuid.uuid4())
        artifact_type = "unknown"
        content_hash = ""
        content_size = 0
        metadata = {}

        if hasattr(artifact, "artifact_id"):
            artifact_id = artifact.artifact_id
        elif hasattr(artifact, "id"):
            artifact_id = str(artifact.id)

        if hasattr(artifact, "artifact_type"):
            artifact_type = artifact.artifact_type
        elif hasattr(artifact, "output_class"):
            artifact_type = artifact.output_class

        content_bytes = None
        if hasattr(artifact, "content_bytes"):
            content_bytes = artifact.content_bytes
        elif hasattr(artifact, "content"):
            content = artifact.content
            if isinstance(content, bytes):
                content_bytes = content
            elif isinstance(content, str):
                content_bytes = content.encode("utf-8")

        if content_bytes:
            content_hash = stable_hash_bytes(content_bytes)
            content_size = len(content_bytes)

        if hasattr(artifact, "metadata"):
            metadata = dict(artifact.metadata) if artifact.metadata else {}
        elif hasattr(artifact, "to_provenance_dict"):
            prov_dict = artifact.to_provenance_dict()
            metadata = prov_dict.get("metadata", {})

        return ArtifactLineage(
            artifact_id=artifact_id,
            artifact_type=artifact_type,
            content_hash=content_hash,
            content_size_bytes=content_size,
            metadata=metadata,
        )

    def _extract_topology_id(self, certified_topology: Any) -> str:
        """Extract topology ID from certified topology."""
        if hasattr(certified_topology, "request_id"):
            return certified_topology.request_id
        if hasattr(certified_topology, "topology_dict"):
            return certified_topology.topology_dict.get("request_id", "unknown")
        return "unknown"

    def _extract_topology_hash(self, certified_topology: Any) -> str:
        """Extract topology hash from certified topology."""
        if hasattr(certified_topology, "signature"):
            sig = certified_topology.signature
            if hasattr(sig, "input_hash"):
                return sig.input_hash
        if hasattr(certified_topology, "topology_dict"):
            return stable_hash_model(certified_topology.topology_dict)[:16]
        return ""

    def _generate_trace_events(
        self,
        validation_lineage: ValidationLineage,
        admission_lineage: AdmissionLineage,
        artifact_lineage: ArtifactLineage,
    ) -> List[RuntimeTraceEvent]:
        """Generate trace events for the pipeline."""
        events = []
        self._sequence_counter = 0

        events.append(self._create_event(
            TraceEventType.VALIDATION_CERTIFIED,
            {
                "request_id": validation_lineage.request_id,
                "tier": validation_lineage.tier,
                "passed": validation_lineage.passed,
            },
        ))

        events.append(self._create_event(
            TraceEventType.ADMISSION_COMPLETED,
            {
                "admission_id": admission_lineage.admission_id,
                "decision": admission_lineage.decision,
            },
        ))

        events.append(self._create_event(
            TraceEventType.TRANSLATION_COMPLETED,
            {"artifact_type": artifact_lineage.artifact_type},
        ))

        events.append(self._create_event(
            TraceEventType.ADAPTER_COMPLETED,
            {},
        ))

        events.append(self._create_event(
            TraceEventType.ARTIFACT_RECORDED,
            {
                "artifact_id": artifact_lineage.artifact_id,
                "content_hash": artifact_lineage.content_hash[:16] if artifact_lineage.content_hash else "",
            },
        ))

        return events

    def _create_event(
        self,
        event_type: TraceEventType,
        details: Dict[str, Any],
    ) -> RuntimeTraceEvent:
        """Create a trace event with sequence number."""
        self._sequence_counter += 1
        return RuntimeTraceEvent.create(
            event_type=event_type,
            details=details,
            sequence_number=self._sequence_counter,
        )

    def _assess_replayability(
        self,
        certified_topology: Any,
        admission_result: Any,
        artifact: Any,
        adapter_id: str,
    ) -> tuple:
        """Assess whether the run is replayable."""
        constraints = []

        if adapter_id != "mock":
            constraints.append(f"Non-mock adapter '{adapter_id}' - real kernel replay not supported")

        if not hasattr(certified_topology, "topology_dict"):
            constraints.append("Topology dict not preserved")

        if not hasattr(admission_result, "authorization_token"):
            constraints.append("Authorization token not preserved")

        replayable = len(constraints) == 0

        return replayable, constraints


def create_replay_bundle(
    certified_topology: Any,
    admission_result: Any,
    artifact: Any,
    translator_id: str,
    adapter_id: str,
    trace_events: Optional[List[RuntimeTraceEvent]] = None,
) -> RuntimeReplayBundle:
    """
    Convenience function to create a replay bundle.

    Equivalent to:
        RuntimeProvenanceRecorder().record(...)
    """
    recorder = RuntimeProvenanceRecorder()
    return recorder.record(
        certified_topology=certified_topology,
        admission_result=admission_result,
        artifact=artifact,
        translator_id=translator_id,
        adapter_id=adapter_id,
        trace_events=trace_events,
    )
