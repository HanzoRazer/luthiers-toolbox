"""
Tests for Runtime Provenance and Replay (MRP-5N).

Sprint: MRP-5N
Status: PROTOTYPE

Tests the runtime provenance infrastructure:
- Provenance bundle creation
- Validation signature preservation
- Admission decision preservation
- Artifact hash stability
- Trace order determinism
- Replay bundle integrity
- Tampering detection
- Stable JSON hashing
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock
import json

from app.cam.topology_validation.contracts import (
    CertifiedTopology,
    ValidationResult,
    ValidationSignature,
    ValidationTier,
)
from app.cam.topology_validation.validators import TopologyValidator
from app.cam.runtime_admission import (
    ExecutionAdmissionController,
    ExecutionAdmissionRequest,
    RuntimeExecutionContext,
)
from app.cam.runtime_provenance import (
    # Contracts
    AdmissionLineage,
    ArtifactLineage,
    ReplayStatus,
    ReplayVerificationResult,
    RuntimeArtifactProvenance,
    RuntimeReplayBundle,
    RuntimeTraceEvent,
    TraceEventType,
    ValidationLineage,
    # Exceptions
    IntegrityError,
    NonReplayableError,
    ProvenanceRecordingError,
    ReplayError,
    # Integrity
    verify_admission_signature,
    verify_artifact_hash,
    verify_bundle_hash,
    verify_provenance_hash,
    verify_replay_bundle_integrity,
    verify_trace_order,
    verify_validation_signature,
    # Recorder
    RuntimeProvenanceRecorder,
    create_replay_bundle,
    # Replay
    RuntimeReplayEngine,
    get_bundle_summary,
    verify_bundle,
    # Serialization
    stable_hash_bytes,
    stable_hash_model,
    stable_hash_string,
    stable_json_dumps,
    stable_json_loads,
    verify_hash_match,
)


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def valid_topology_dict():
    """Valid topology dictionary."""
    return {
        "request_id": "test-prov-001",
        "tier": "PROTOTYPE",
        "shells": [
            {
                "shell_id": "shell_body_001",
                "shell_type": "flat_extrusion",
                "component_name": "body",
                "is_closed": True,
                "is_manifold": True,
                "surface_count": 6,
                "edge_count": 12,
                "vertex_count": 8,
                "continuity": [],
            }
        ],
    }


@pytest.fixture
def certified_topology(valid_topology_dict):
    """Create a valid CertifiedTopology."""
    validator = TopologyValidator(tier=ValidationTier.PROTOTYPE)
    return validator.certify(valid_topology_dict)


@pytest.fixture
def admission_result(certified_topology):
    """Create an admission result."""
    context = RuntimeExecutionContext(
        available_adapter_ids=["mock"],
    )
    request = ExecutionAdmissionRequest(
        certified_topology=certified_topology,
        runtime_context=context,
    )
    controller = ExecutionAdmissionController(record_provenance=False)
    return controller.evaluate(request)


@pytest.fixture
def mock_artifact():
    """Create a mock artifact."""
    artifact = MagicMock()
    artifact.artifact_id = "artifact-test-001"
    artifact.artifact_type = "step_acoustic"
    artifact.content_bytes = b"ISO-10303-21; TEST STEP CONTENT"
    artifact.metadata = {"format": "STEP", "version": "1.0"}
    artifact.to_provenance_dict = MagicMock(return_value={
        "artifact_id": "artifact-test-001",
        "artifact_type": "step_acoustic",
        "metadata": {"format": "STEP"},
    })
    return artifact


@pytest.fixture
def replay_bundle(certified_topology, admission_result, mock_artifact):
    """Create a replay bundle."""
    recorder = RuntimeProvenanceRecorder()
    return recorder.record(
        certified_topology=certified_topology,
        admission_result=admission_result,
        artifact=mock_artifact,
        translator_id="step_acoustic",
        adapter_id="mock",
    )


# =============================================================================
# Test: Provenance Bundle Created
# =============================================================================


class TestProvenanceBundleCreated:
    """Tests for provenance bundle creation."""

    def test_bundle_created_successfully(self, replay_bundle):
        """Bundle should be created successfully."""
        assert replay_bundle is not None
        assert replay_bundle.bundle_id is not None
        assert replay_bundle.provenance is not None

    def test_bundle_has_run_id(self, replay_bundle):
        """Bundle should have a run ID."""
        assert replay_bundle.provenance.run_id is not None
        assert len(replay_bundle.provenance.run_id) > 0

    def test_bundle_has_source_topology(self, replay_bundle):
        """Bundle should have source topology info."""
        assert replay_bundle.provenance.source_topology_id is not None
        assert replay_bundle.provenance.source_topology_hash is not None

    def test_bundle_has_lineage(self, replay_bundle):
        """Bundle should have all lineage records."""
        assert replay_bundle.provenance.validation_lineage is not None
        assert replay_bundle.provenance.admission_lineage is not None
        assert replay_bundle.provenance.artifact_lineage is not None

    def test_bundle_is_replayable_for_mock(self, replay_bundle):
        """Bundle with mock adapter should be replayable."""
        assert replay_bundle.replayable is True
        assert len(replay_bundle.replay_constraints) == 0


# =============================================================================
# Test: Validation Signature Preserved
# =============================================================================


class TestValidationSignaturePreserved:
    """Tests for validation signature preservation."""

    def test_validation_request_id_preserved(self, replay_bundle, valid_topology_dict):
        """Validation request ID should be preserved."""
        validation = replay_bundle.provenance.validation_lineage
        assert validation.request_id == valid_topology_dict["request_id"]

    def test_validation_tier_preserved(self, replay_bundle):
        """Validation tier should be preserved."""
        validation = replay_bundle.provenance.validation_lineage
        assert validation.tier == "PROTOTYPE"

    def test_validation_passed_preserved(self, replay_bundle):
        """Validation passed status should be preserved."""
        validation = replay_bundle.provenance.validation_lineage
        assert validation.passed is True

    def test_validation_hashes_preserved(self, replay_bundle):
        """Validation signature hashes should be preserved."""
        validation = replay_bundle.provenance.validation_lineage
        assert validation.signature_input_hash is not None
        assert validation.signature_validation_hash is not None
        assert len(validation.signature_input_hash) > 0
        assert len(validation.signature_validation_hash) > 0


# =============================================================================
# Test: Admission Decision Preserved
# =============================================================================


class TestAdmissionDecisionPreserved:
    """Tests for admission decision preservation."""

    def test_admission_id_preserved(self, replay_bundle):
        """Admission ID should be preserved."""
        admission = replay_bundle.provenance.admission_lineage
        assert admission.admission_id is not None

    def test_admission_decision_preserved(self, replay_bundle):
        """Admission decision should be preserved."""
        admission = replay_bundle.provenance.admission_lineage
        assert admission.decision == "ADMITTED"

    def test_authorized_adapters_preserved(self, replay_bundle):
        """Authorized adapters should be preserved."""
        admission = replay_bundle.provenance.admission_lineage
        assert "mock" in admission.authorized_adapters


# =============================================================================
# Test: Artifact Hash Stable
# =============================================================================


class TestArtifactHashStable:
    """Tests for artifact hash stability."""

    def test_artifact_hash_computed(self, replay_bundle):
        """Artifact hash should be computed."""
        artifact = replay_bundle.provenance.artifact_lineage
        assert artifact.content_hash is not None
        assert len(artifact.content_hash) > 0

    def test_artifact_hash_is_deterministic(self, mock_artifact):
        """Same content should produce same hash."""
        content = mock_artifact.content_bytes
        hash1 = stable_hash_bytes(content)
        hash2 = stable_hash_bytes(content)
        assert hash1 == hash2

    def test_artifact_size_preserved(self, replay_bundle, mock_artifact):
        """Artifact size should be preserved."""
        artifact = replay_bundle.provenance.artifact_lineage
        assert artifact.content_size_bytes == len(mock_artifact.content_bytes)


# =============================================================================
# Test: Trace Order Deterministic
# =============================================================================


class TestTraceOrderDeterministic:
    """Tests for trace order determinism."""

    def test_trace_events_exist(self, replay_bundle):
        """Trace events should exist."""
        events = replay_bundle.provenance.trace_events
        assert len(events) >= 5

    def test_trace_order_correct(self, replay_bundle):
        """Trace events should be in correct order."""
        events = replay_bundle.provenance.trace_events
        expected_order = [
            TraceEventType.VALIDATION_CERTIFIED,
            TraceEventType.ADMISSION_COMPLETED,
            TraceEventType.TRANSLATION_COMPLETED,
            TraceEventType.ADAPTER_COMPLETED,
            TraceEventType.ARTIFACT_RECORDED,
        ]
        for i, expected in enumerate(expected_order):
            assert events[i].event_type == expected

    def test_sequence_numbers_monotonic(self, replay_bundle):
        """Sequence numbers should be monotonically increasing."""
        events = replay_bundle.provenance.trace_events
        seq_nums = [e.sequence_number for e in events]
        assert seq_nums == sorted(seq_nums)
        assert len(set(seq_nums)) == len(seq_nums)  # All unique


# =============================================================================
# Test: Replay Bundle Integrity
# =============================================================================


class TestReplayBundleIntegrity:
    """Tests for replay bundle integrity."""

    def test_bundle_integrity_passes(self, replay_bundle):
        """Bundle integrity check should pass."""
        result = verify_replay_bundle_integrity(replay_bundle)
        assert result.passed

    def test_all_integrity_checks_pass(self, replay_bundle):
        """All integrity checks should pass."""
        result = verify_replay_bundle_integrity(replay_bundle)
        assert len(result.failed_checks) == 0
        assert len(result.passed_checks) >= 5

    def test_replay_verification_passes(self, replay_bundle):
        """Replay verification should pass."""
        result = verify_bundle(replay_bundle)
        assert result.passed
        assert result.status == ReplayStatus.VERIFIED


# =============================================================================
# Test: Tampered Artifact Hash Rejected
# =============================================================================


class TestTamperedArtifactHashRejected:
    """Tests for tampered artifact hash rejection."""

    def test_tampered_artifact_hash_detected(self):
        """Tampered artifact content should be detected."""
        original = b"original content"
        original_hash = stable_hash_bytes(original)

        tampered = b"tampered content"
        result = verify_artifact_hash(tampered, original_hash)

        assert not result.passed
        assert "mismatch" in result.message.lower()

    def test_verify_hash_match_works(self):
        """verify_hash_match should detect tampering."""
        content = b"test content"
        correct_hash = stable_hash_bytes(content)

        assert verify_hash_match(content, correct_hash) is True
        assert verify_hash_match(b"different", correct_hash) is False


# =============================================================================
# Test: Tampered Validation Signature Rejected
# =============================================================================


class TestTamperedValidationSignatureRejected:
    """Tests for tampered validation signature rejection."""

    def test_missing_validation_hash_detected(self):
        """Missing validation hash should be detected."""
        lineage = ValidationLineage(
            request_id="test",
            tier="PROTOTYPE",
            passed=True,
            signature_input_hash="abc123",
            signature_validation_hash="",  # Empty!
        )
        provenance = MagicMock()
        provenance.validation_lineage = lineage

        result = verify_validation_signature(provenance)
        assert not result.passed

    def test_failed_validation_detected(self):
        """Failed validation should be detected."""
        lineage = ValidationLineage(
            request_id="test",
            tier="PROTOTYPE",
            passed=False,  # Failed!
            signature_input_hash="abc123",
            signature_validation_hash="def456",
        )
        provenance = MagicMock()
        provenance.validation_lineage = lineage

        result = verify_validation_signature(provenance)
        assert not result.passed


# =============================================================================
# Test: Replay Does Not Re-Authorize
# =============================================================================


class TestReplayDoesNotReauthorize:
    """Tests that replay does not grant execution authority."""

    def test_replay_only_verifies(self, replay_bundle):
        """Replay should only verify, not authorize."""
        engine = RuntimeReplayEngine()
        result = engine.verify(replay_bundle)

        assert result.status == ReplayStatus.VERIFIED
        assert "authorization" not in str(result.to_dict()).lower() or "token" not in str(result.to_dict()).lower()

    def test_non_replayable_bundle_reported(self, certified_topology, admission_result, mock_artifact):
        """Non-replayable bundle should be reported, not repaired."""
        recorder = RuntimeProvenanceRecorder()
        bundle = recorder.record(
            certified_topology=certified_topology,
            admission_result=admission_result,
            artifact=mock_artifact,
            translator_id="step_acoustic",
            adapter_id="occ",  # Non-mock adapter
        )

        assert not bundle.replayable
        assert len(bundle.replay_constraints) > 0

        engine = RuntimeReplayEngine()
        result = engine.verify(bundle, verify_replayable=True)
        assert result.status == ReplayStatus.NON_REPLAYABLE


# =============================================================================
# Test: Replay Does Not Mutate Topology
# =============================================================================


class TestReplayDoesNotMutateTopology:
    """Tests that replay does not mutate topology."""

    def test_bundle_content_unchanged_after_verify(self, replay_bundle):
        """Bundle content should be unchanged after verification."""
        original_hash = replay_bundle.provenance.provenance_hash

        engine = RuntimeReplayEngine()
        engine.verify(replay_bundle)

        assert replay_bundle.provenance.provenance_hash == original_hash

    def test_topology_hash_preserved(self, replay_bundle, certified_topology):
        """Topology hash should be preserved in bundle."""
        expected_hash = certified_topology.signature.input_hash
        actual_hash = replay_bundle.provenance.source_topology_hash
        assert actual_hash == expected_hash


# =============================================================================
# Test: Stable JSON Hashing Consistent
# =============================================================================


class TestStableJsonHashingConsistent:
    """Tests for stable JSON hashing consistency."""

    def test_stable_json_dumps_deterministic(self):
        """stable_json_dumps should be deterministic."""
        data = {"z": 1, "a": 2, "m": [3, 1, 2]}
        json1 = stable_json_dumps(data)
        json2 = stable_json_dumps(data)
        assert json1 == json2

    def test_stable_json_sorted_keys(self):
        """stable_json_dumps should sort keys."""
        data = {"z": 1, "a": 2}
        result = stable_json_dumps(data)
        assert result.index('"a"') < result.index('"z"')

    def test_stable_hash_model_deterministic(self):
        """stable_hash_model should be deterministic."""
        data = {"key": "value", "number": 42}
        hash1 = stable_hash_model(data)
        hash2 = stable_hash_model(data)
        assert hash1 == hash2

    def test_stable_hash_different_for_different_content(self):
        """Different content should produce different hashes."""
        hash1 = stable_hash_model({"a": 1})
        hash2 = stable_hash_model({"a": 2})
        assert hash1 != hash2


# =============================================================================
# Test: Replay Result Reports Constraints
# =============================================================================


class TestReplayResultReportsConstraints:
    """Tests for constraint reporting in replay results."""

    def test_non_replayable_reports_constraints(self, certified_topology, admission_result, mock_artifact):
        """Non-replayable bundle should report constraints."""
        recorder = RuntimeProvenanceRecorder()
        bundle = recorder.record(
            certified_topology=certified_topology,
            admission_result=admission_result,
            artifact=mock_artifact,
            translator_id="step_acoustic",
            adapter_id="cadquery",  # Non-mock
        )

        engine = RuntimeReplayEngine()
        result = engine.verify(bundle, verify_replayable=True)

        assert result.status == ReplayStatus.NON_REPLAYABLE
        assert len(result.constraints) > 0

    def test_verification_result_serializable(self, replay_bundle):
        """Verification result should be serializable."""
        engine = RuntimeReplayEngine()
        result = engine.verify(replay_bundle)

        result_dict = result.to_dict()
        json_str = json.dumps(result_dict)
        assert len(json_str) > 0


# =============================================================================
# Test: Bundle Serialization
# =============================================================================


class TestBundleSerialization:
    """Tests for bundle serialization/deserialization."""

    def test_bundle_to_json(self, replay_bundle):
        """Bundle should serialize to JSON."""
        json_str = replay_bundle.to_json()
        assert len(json_str) > 0
        assert "bundle_id" in json_str

    def test_bundle_from_json(self, replay_bundle):
        """Bundle should deserialize from JSON."""
        json_str = replay_bundle.to_json()
        loaded = RuntimeReplayBundle.from_json(json_str)

        assert loaded.bundle_id == replay_bundle.bundle_id
        assert loaded.provenance.run_id == replay_bundle.provenance.run_id

    def test_roundtrip_preserves_integrity(self, replay_bundle):
        """Serialization roundtrip should preserve integrity."""
        json_str = replay_bundle.to_json()
        loaded = RuntimeReplayBundle.from_json(json_str)

        result = verify_replay_bundle_integrity(loaded)
        assert result.passed


# =============================================================================
# Test: Recording Errors
# =============================================================================


class TestRecordingErrors:
    """Tests for recording error handling."""

    def test_missing_topology_raises_error(self, admission_result, mock_artifact):
        """Missing topology should raise error."""
        recorder = RuntimeProvenanceRecorder()

        with pytest.raises(ProvenanceRecordingError) as exc:
            recorder.record(
                certified_topology=None,
                admission_result=admission_result,
                artifact=mock_artifact,
                translator_id="step_acoustic",
                adapter_id="mock",
            )

        assert "certified_topology" in exc.value.missing_fields

    def test_missing_artifact_raises_error(self, certified_topology, admission_result):
        """Missing artifact should raise error."""
        recorder = RuntimeProvenanceRecorder()

        with pytest.raises(ProvenanceRecordingError) as exc:
            recorder.record(
                certified_topology=certified_topology,
                admission_result=admission_result,
                artifact=None,
                translator_id="step_acoustic",
                adapter_id="mock",
            )

        assert "artifact" in exc.value.missing_fields


# =============================================================================
# Test: Bundle Summary
# =============================================================================


class TestBundleSummary:
    """Tests for bundle summary functionality."""

    def test_summary_includes_key_fields(self, replay_bundle):
        """Summary should include key fields."""
        summary = get_bundle_summary(replay_bundle)

        assert "bundle_id" in summary
        assert "run_id" in summary
        assert "source" in summary
        assert "validation" in summary
        assert "admission" in summary
        assert "artifact" in summary
        assert "trace" in summary

    def test_summary_readable(self, replay_bundle):
        """Summary should be human-readable."""
        summary = get_bundle_summary(replay_bundle)

        assert summary["replayable"] is True
        assert summary["validation"]["passed"] is True
        assert summary["admission"]["decision"] == "ADMITTED"


# =============================================================================
# Test: Strict Mode
# =============================================================================


class TestStrictMode:
    """Tests for strict verification mode."""

    def test_strict_mode_raises_on_failure(self, certified_topology, admission_result, mock_artifact):
        """Strict mode should raise on verification failure."""
        recorder = RuntimeProvenanceRecorder()
        bundle = recorder.record(
            certified_topology=certified_topology,
            admission_result=admission_result,
            artifact=mock_artifact,
            translator_id="step_acoustic",
            adapter_id="occ",  # Non-mock
        )

        engine = RuntimeReplayEngine(strict=True)

        with pytest.raises(NonReplayableError):
            engine.verify(bundle, verify_replayable=True)

    def test_strict_mode_returns_on_success(self, replay_bundle):
        """Strict mode should return on success."""
        engine = RuntimeReplayEngine(strict=True)
        result = engine.verify(replay_bundle)

        assert result.passed
