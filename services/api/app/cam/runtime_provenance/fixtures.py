"""
Replay Fixture Helpers.

Sprint: MRP-5O
Status: PROTOTYPE

Provides deterministic fixture builders for replay bundles.
Used by scripts and utilities for testing and verification.

NOTE: Test-only fixtures (tampered bundles, edge cases) belong in tests/.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import hashlib
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
from .serialization import stable_hash_string, stable_json_dumps


def build_minimal_topology_dict(
    request_id: Optional[str] = None,
    shell_count: int = 1,
) -> Dict[str, Any]:
    """
    Build a minimal valid topology dictionary.

    Args:
        request_id: Optional request ID (auto-generated if None)
        shell_count: Number of shells to include

    Returns:
        Minimal topology dictionary suitable for validation
    """
    req_id = request_id or f"fixture-{uuid.uuid4()}"

    shells = []
    for i in range(shell_count):
        shells.append({
            "shell_id": f"shell_{i+1:03d}",
            "shell_type": "flat_extrusion",
            "component_name": f"component_{i+1}",
            "is_closed": True,
            "is_manifold": True,
            "surface_count": 6,
            "edge_count": 12,
            "vertex_count": 8,
            "continuity": [],
        })

    return {
        "request_id": req_id,
        "tier": "PROTOTYPE",
        "shells": shells,
    }


def build_minimal_validation_lineage(
    topology_dict: Dict[str, Any],
    passed: bool = True,
) -> ValidationLineage:
    """
    Build a minimal validation lineage.

    Args:
        topology_dict: The source topology
        passed: Whether validation passed

    Returns:
        ValidationLineage for the topology
    """
    input_hash = stable_hash_string(stable_json_dumps(topology_dict))
    validation_hash = stable_hash_string(f"{input_hash}-validated")

    return ValidationLineage(
        request_id=topology_dict.get("request_id", "unknown"),
        tier="PROTOTYPE",
        passed=passed,
        signature_input_hash=input_hash,
        signature_validation_hash=validation_hash,
        blocking_count=0 if passed else 1,
        major_count=0,
    )


def build_minimal_admission_lineage(
    decision: str = "ADMITTED",
    authorized_adapters: Optional[List[str]] = None,
) -> AdmissionLineage:
    """
    Build a minimal admission lineage.

    Args:
        decision: Admission decision (ADMITTED, REJECTED, CONDITIONALLY_ADMITTED)
        authorized_adapters: List of authorized adapter IDs

    Returns:
        AdmissionLineage
    """
    return AdmissionLineage(
        admission_id=str(uuid.uuid4()),
        decision=decision,
        authorization_token=str(uuid.uuid4()) if decision != "REJECTED" else None,
        runtime_tier="PROTOTYPE",
        execution_mode="DETERMINISTIC",
        authorized_adapters=authorized_adapters or ["mock"],
    )


def build_minimal_artifact_lineage(
    artifact_type: str = "step_acoustic",
    adapter_id: str = "mock",
    content: Optional[bytes] = None,
) -> ArtifactLineage:
    """
    Build a minimal artifact lineage.

    Args:
        artifact_type: Type of artifact
        adapter_id: Adapter that produced the artifact
        content: Optional content bytes for hash computation

    Returns:
        ArtifactLineage
    """
    if content is None:
        content = b"MOCK_ARTIFACT_CONTENT"

    content_hash = hashlib.sha256(content).hexdigest()[:16]

    return ArtifactLineage(
        artifact_id=str(uuid.uuid4()),
        artifact_type=artifact_type,
        content_hash=content_hash,
        content_size_bytes=len(content),
        metadata={"format": "STEP", "version": "1.0", "adapter_id": adapter_id},
    )


def build_minimal_trace_events() -> List[RuntimeTraceEvent]:
    """
    Build minimal trace events for a complete pipeline run.

    Returns:
        List of trace events in correct order (all 5 required events)
    """
    base_time = datetime.now(timezone.utc)

    return [
        RuntimeTraceEvent(
            event_type=TraceEventType.VALIDATION_CERTIFIED,
            timestamp_iso=base_time.isoformat(),
            sequence_number=1,
            details={"tier": "PROTOTYPE"},
        ),
        RuntimeTraceEvent(
            event_type=TraceEventType.ADMISSION_COMPLETED,
            timestamp_iso=base_time.isoformat(),
            sequence_number=2,
            details={"decision": "ADMITTED"},
        ),
        RuntimeTraceEvent(
            event_type=TraceEventType.TRANSLATION_COMPLETED,
            timestamp_iso=base_time.isoformat(),
            sequence_number=3,
            details={"translator_id": "step_acoustic"},
        ),
        RuntimeTraceEvent(
            event_type=TraceEventType.ADAPTER_COMPLETED,
            timestamp_iso=base_time.isoformat(),
            sequence_number=4,
            details={"adapter_id": "mock"},
        ),
        RuntimeTraceEvent(
            event_type=TraceEventType.ARTIFACT_RECORDED,
            timestamp_iso=base_time.isoformat(),
            sequence_number=5,
            details={"artifact_type": "step_acoustic"},
        ),
    ]


def build_minimal_replay_bundle(
    request_id: Optional[str] = None,
    adapter_id: str = "mock",
    decision: str = "ADMITTED",
    is_replayable: bool = True,
) -> RuntimeReplayBundle:
    """
    Build a minimal valid replay bundle for testing.

    Args:
        request_id: Optional request ID
        adapter_id: Adapter ID (use "mock" for replayable bundles)
        decision: Admission decision
        is_replayable: Whether bundle should be marked replayable

    Returns:
        Complete RuntimeReplayBundle
    """
    topology = build_minimal_topology_dict(request_id=request_id)
    validation = build_minimal_validation_lineage(topology)
    admission = build_minimal_admission_lineage(decision=decision)
    artifact = build_minimal_artifact_lineage(adapter_id=adapter_id)
    trace = build_minimal_trace_events()

    run_id = str(uuid.uuid4())
    topology_hash = stable_hash_string(stable_json_dumps(topology))

    replay_constraints = []
    if adapter_id != "mock":
        replay_constraints.append(f"adapter_id={adapter_id} not supported for mock replay")
        is_replayable = False
    if decision == "REJECTED":
        replay_constraints.append("admission decision is REJECTED")
        is_replayable = False

    provenance = RuntimeArtifactProvenance(
        run_id=run_id,
        source_topology_id=topology.get("request_id", "unknown"),
        source_topology_hash=topology_hash,
        validation_lineage=validation,
        admission_lineage=admission,
        artifact_lineage=artifact,
        translator_id=artifact.artifact_type,
        adapter_id=adapter_id,
        trace_events=trace,
        created_at=datetime.now(timezone.utc).isoformat(),
    )

    return RuntimeReplayBundle(
        bundle_id=str(uuid.uuid4()),
        provenance=provenance,
        replayable=is_replayable,
        replay_constraints=replay_constraints,
    )


def build_replay_bundle_from_pipeline_outputs(
    topology_dict: Dict[str, Any],
    validation_lineage: ValidationLineage,
    admission_lineage: AdmissionLineage,
    artifact_lineage: ArtifactLineage,
    adapter_id: str = "mock",
    trace_events: Optional[List[RuntimeTraceEvent]] = None,
) -> RuntimeReplayBundle:
    """
    Build a replay bundle from actual pipeline outputs.

    Args:
        topology_dict: Source topology dictionary
        validation_lineage: Validation result lineage
        admission_lineage: Admission decision lineage
        artifact_lineage: Artifact metadata lineage
        adapter_id: Adapter ID
        trace_events: Optional trace events (defaults to minimal set)

    Returns:
        RuntimeReplayBundle assembled from pipeline outputs
    """
    run_id = str(uuid.uuid4())

    if trace_events is None:
        trace_events = build_minimal_trace_events()

    topology_hash = stable_hash_string(stable_json_dumps(topology_dict))

    is_replayable = (
        adapter_id == "mock"
        and admission_lineage.decision in ("ADMITTED", "CONDITIONALLY_ADMITTED")
    )

    replay_constraints = []
    if adapter_id != "mock":
        replay_constraints.append(
            f"adapter_id={adapter_id} not supported for mock replay"
        )
    if admission_lineage.decision == "REJECTED":
        replay_constraints.append("admission decision is REJECTED")

    provenance = RuntimeArtifactProvenance(
        run_id=run_id,
        source_topology_id=topology_dict.get("request_id", "unknown"),
        source_topology_hash=topology_hash,
        validation_lineage=validation_lineage,
        admission_lineage=admission_lineage,
        artifact_lineage=artifact_lineage,
        translator_id=artifact_lineage.artifact_type,
        adapter_id=adapter_id,
        trace_events=trace_events,
        created_at=datetime.now(timezone.utc).isoformat(),
    )

    return RuntimeReplayBundle(
        bundle_id=str(uuid.uuid4()),
        provenance=provenance,
        replayable=is_replayable,
        replay_constraints=replay_constraints,
    )
