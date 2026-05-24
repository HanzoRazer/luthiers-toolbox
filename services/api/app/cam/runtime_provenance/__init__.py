"""
Runtime Provenance and Replay.

Sprint: MRP-5N
Status: PROTOTYPE

Provides runtime artifact provenance and replay verification.
Preserves executable lineage across the certified runtime pipeline.

ARCHITECTURAL PRINCIPLE:
    Every artifact must answer:
    - What produced me?
    - From what certified topology?
    - Under what validation result?
    - Under what admission decision?
    - Using what translator?
    - Using what adapter?
    - With what deterministic signature?
    - Can this run be replayed?

Usage:
    from app.cam.runtime_provenance import (
        RuntimeProvenanceRecorder,
        RuntimeReplayEngine,
        RuntimeReplayBundle,
    )

    # Record provenance
    recorder = RuntimeProvenanceRecorder()
    bundle = recorder.record(
        certified_topology=certified,
        admission_result=admission_result,
        artifact=artifact,
        translator_id="step_acoustic",
        adapter_id="mock",
    )

    # Verify bundle
    engine = RuntimeReplayEngine()
    result = engine.verify(bundle)

    if result.passed:
        print("Bundle verified successfully")
    else:
        print(f"Verification failed: {result.message}")

    # Serialize for storage
    json_str = bundle.to_json()

    # Load from storage
    loaded_bundle = RuntimeReplayBundle.from_json(json_str)
"""

# Contracts
from .contracts import (
    AdmissionLineage,
    ArtifactLineage,
    ReplayStatus,
    ReplayVerificationResult,
    RuntimeArtifact,
    RuntimeArtifactProvenance,
    RuntimeReplayBundle,
    RuntimeTraceEvent,
    TraceEventType,
    ValidationLineage,
)

# Exceptions
from .exceptions import (
    BundleSerializationError,
    IntegrityError,
    NonReplayableError,
    ProvenanceError,
    ProvenanceRecordingError,
    ReplayError,
)

# Integrity
from .integrity import (
    BundleIntegrityResult,
    IntegrityCheckResult,
    verify_admission_signature,
    verify_artifact_hash,
    verify_bundle_hash,
    verify_or_raise,
    verify_provenance_hash,
    verify_replay_bundle_integrity,
    verify_trace_order,
    verify_validation_signature,
)

# Recorder
from .recorder import (
    RuntimeProvenanceRecorder,
    create_replay_bundle,
)

# Replay
from .replay import (
    RuntimeReplayEngine,
    get_bundle_summary,
    verify_bundle,
)

# Classification (MRP-5O)
from .classification import (
    DivergenceSeverity,
    RegressionStatus,
    ReplayExecutionStatus,
)

# Execution (MRP-5O)
from .execution import (
    ReplayExecutionHarness,
    ReplayExecutionResult,
    ReproducedArtifact,
    execute_replay,
)

# Regression (MRP-5O)
from .regression import (
    ArtifactRegressionComparator,
    ArtifactRegressionReport,
    DivergenceDetail,
    compare_regression,
)

# Fixtures (MRP-5O)
from .fixtures import (
    build_minimal_admission_lineage,
    build_minimal_artifact_lineage,
    build_minimal_replay_bundle,
    build_minimal_topology_dict,
    build_minimal_trace_events,
    build_minimal_validation_lineage,
    build_replay_bundle_from_pipeline_outputs,
)

# Serialization
from .serialization import (
    stable_dict_from_object,
    stable_hash_bytes,
    stable_hash_model,
    stable_hash_short,
    stable_hash_string,
    stable_json_dumps,
    stable_json_loads,
    verify_hash_match,
)

__all__ = [
    # Contracts
    "AdmissionLineage",
    "ArtifactLineage",
    "ReplayStatus",
    "ReplayVerificationResult",
    "RuntimeArtifact",
    "RuntimeArtifactProvenance",
    "RuntimeReplayBundle",
    "RuntimeTraceEvent",
    "TraceEventType",
    "ValidationLineage",
    # Exceptions
    "BundleSerializationError",
    "IntegrityError",
    "NonReplayableError",
    "ProvenanceError",
    "ProvenanceRecordingError",
    "ReplayError",
    # Integrity
    "BundleIntegrityResult",
    "IntegrityCheckResult",
    "verify_admission_signature",
    "verify_artifact_hash",
    "verify_bundle_hash",
    "verify_or_raise",
    "verify_provenance_hash",
    "verify_replay_bundle_integrity",
    "verify_trace_order",
    "verify_validation_signature",
    # Recorder
    "RuntimeProvenanceRecorder",
    "create_replay_bundle",
    # Replay
    "RuntimeReplayEngine",
    "get_bundle_summary",
    "verify_bundle",
    # Classification (MRP-5O)
    "DivergenceSeverity",
    "RegressionStatus",
    "ReplayExecutionStatus",
    # Execution (MRP-5O)
    "ReplayExecutionHarness",
    "ReplayExecutionResult",
    "ReproducedArtifact",
    "execute_replay",
    # Regression (MRP-5O)
    "ArtifactRegressionComparator",
    "ArtifactRegressionReport",
    "DivergenceDetail",
    "compare_regression",
    # Fixtures (MRP-5O)
    "build_minimal_admission_lineage",
    "build_minimal_artifact_lineage",
    "build_minimal_replay_bundle",
    "build_minimal_topology_dict",
    "build_minimal_trace_events",
    "build_minimal_validation_lineage",
    "build_replay_bundle_from_pipeline_outputs",
    # Serialization
    "stable_dict_from_object",
    "stable_hash_bytes",
    "stable_hash_model",
    "stable_hash_short",
    "stable_hash_string",
    "stable_json_dumps",
    "stable_json_loads",
    "verify_hash_match",
]
