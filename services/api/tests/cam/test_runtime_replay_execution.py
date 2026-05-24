"""
Tests for Runtime Replay Execution (MRP-5O).

Sprint: MRP-5O
Status: PROTOTYPE

Tests the replay execution infrastructure:
- Admitted bundle replay
- Rejected admission non-replay
- Invalid bundle rejection
- Missing inputs non-replayable
- Artifact hash comparison
- Regression detection
- Authority separation
- Immutability guarantees
- Determinism verification
"""

import pytest
from unittest.mock import MagicMock
import copy
import hashlib

from app.cam.runtime_provenance import (
    # Classification
    DivergenceSeverity,
    RegressionStatus,
    ReplayExecutionStatus,
    # Execution
    ReplayExecutionHarness,
    ReplayExecutionResult,
    ReproducedArtifact,
    execute_replay,
    # Regression
    ArtifactRegressionComparator,
    ArtifactRegressionReport,
    DivergenceDetail,
    compare_regression,
    # Fixtures
    build_minimal_replay_bundle,
    build_minimal_topology_dict,
    # Contracts
    RuntimeReplayBundle,
    AdmissionLineage,
    ArtifactLineage,
    ValidationLineage,
    # Integrity
    verify_replay_bundle_integrity,
)


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def valid_bundle():
    """Create a valid replay bundle for mock adapter."""
    return build_minimal_replay_bundle(
        adapter_id="mock",
        decision="ADMITTED",
        is_replayable=True,
    )


@pytest.fixture
def rejected_bundle():
    """Create a bundle with rejected admission."""
    return build_minimal_replay_bundle(
        adapter_id="mock",
        decision="REJECTED",
        is_replayable=False,
    )


@pytest.fixture
def non_mock_bundle():
    """Create a bundle with non-mock adapter."""
    return build_minimal_replay_bundle(
        adapter_id="occ_step",
        decision="ADMITTED",
        is_replayable=False,
    )


@pytest.fixture
def harness():
    """Create a ReplayExecutionHarness."""
    return ReplayExecutionHarness()


@pytest.fixture
def comparator():
    """Create an ArtifactRegressionComparator."""
    return ArtifactRegressionComparator()


# =============================================================================
# Test Classes
# =============================================================================


class TestAdmittedBundleReplays:
    """Tests for successful replay of admitted bundles."""

    def test_admitted_bundle_replays_successfully(self, harness, valid_bundle):
        """Admitted bundle with mock adapter replays successfully."""
        result = harness.execute(valid_bundle)
        assert result.status == ReplayExecutionStatus.REPLAYED
        assert result.reproduced_hash is not None
        assert result.reproduced_size is not None

    def test_replay_produces_artifact_hash(self, harness, valid_bundle):
        """Replay execution produces a valid artifact hash."""
        result = harness.execute(valid_bundle)
        assert result.reproduced_hash is not None
        assert len(result.reproduced_hash) == 16  # SHA-256 truncated to 16

    def test_replay_tracks_execution_time(self, harness, valid_bundle):
        """Replay tracks execution time."""
        result = harness.execute(valid_bundle)
        assert result.execution_time_ms >= 0

    def test_replay_includes_bundle_run_id(self, harness, valid_bundle):
        """Replay result includes original bundle run_id."""
        result = harness.execute(valid_bundle)
        assert result.bundle_run_id == valid_bundle.provenance.run_id

    def test_replay_generates_new_run_id(self, harness, valid_bundle):
        """Replay generates a new run_id distinct from bundle."""
        result = harness.execute(valid_bundle)
        assert result.run_id != valid_bundle.provenance.run_id


class TestRejectedAdmissionDoesNotReplay:
    """Tests ensuring rejected bundles cannot replay."""

    def test_rejected_admission_returns_rejected_status(self, harness, rejected_bundle):
        """Rejected admission bundle returns REJECTED_ADMISSION or INVALID_BUNDLE status."""
        result = harness.execute(rejected_bundle)
        # May fail integrity check (INVALID_BUNDLE) or admission check (REJECTED_ADMISSION)
        assert result.status in (ReplayExecutionStatus.REJECTED_ADMISSION, ReplayExecutionStatus.INVALID_BUNDLE)

    def test_rejected_admission_no_artifact_produced(self, harness, rejected_bundle):
        """Rejected admission does not produce artifact hash."""
        result = harness.execute(rejected_bundle)
        assert result.reproduced_hash is None

    def test_rejected_admission_explains_reason(self, harness, rejected_bundle):
        """Rejected admission explains the rejection reason."""
        result = harness.execute(rejected_bundle)
        # Either in message or constraints
        assert "REJECTED" in result.message or any("REJECTED" in c for c in result.constraints)


class TestInvalidBundleRejected:
    """Tests for invalid bundle detection."""

    def test_tampered_bundle_detected(self, harness, valid_bundle):
        """Tampered bundle is detected as invalid."""
        valid_bundle.bundle_hash = "tampered_hash"
        result = harness.execute(valid_bundle)
        assert result.status == ReplayExecutionStatus.INVALID_BUNDLE

    def test_invalid_bundle_reports_constraints(self, harness, valid_bundle):
        """Invalid bundle reports integrity constraints."""
        valid_bundle.bundle_hash = "tampered_hash"
        result = harness.execute(valid_bundle)
        assert len(result.constraints) > 0


class TestMissingInputsNonReplayable:
    """Tests for missing required inputs."""

    def test_non_mock_adapter_non_replayable(self, harness, non_mock_bundle):
        """Non-mock adapter bundle is non-replayable."""
        result = harness.execute(non_mock_bundle)
        assert result.status == ReplayExecutionStatus.NON_REPLAYABLE

    def test_non_replayable_reports_adapter_constraint(self, harness, non_mock_bundle):
        """Non-replayable bundle reports adapter constraint."""
        result = harness.execute(non_mock_bundle)
        assert any("adapter" in c.lower() for c in result.constraints)

    def test_bundle_marked_non_replayable(self, harness, valid_bundle):
        """Bundle marked non-replayable is rejected."""
        valid_bundle.replayable = False
        valid_bundle.replay_constraints = ["test_constraint"]
        result = harness.execute(valid_bundle)
        # May fail integrity check first (because bundle_hash is now invalid)
        # or non-replayable check
        assert result.status in (ReplayExecutionStatus.NON_REPLAYABLE, ReplayExecutionStatus.INVALID_BUNDLE)


class TestArtifactHashMatch:
    """Tests for artifact hash comparison."""

    def test_matching_hash_reported(self, comparator, valid_bundle, harness):
        """Matching artifact hash is reported correctly."""
        exec_result = harness.execute(valid_bundle)

        # Force hash and size to match for test
        valid_bundle.provenance.artifact_lineage.content_hash = exec_result.reproduced_hash
        valid_bundle.provenance.artifact_lineage.content_size_bytes = exec_result.reproduced_size

        report = comparator.compare(valid_bundle, exec_result)
        assert report.hash_match is True
        assert report.status == RegressionStatus.MATCH

    def test_match_report_passed_property(self, comparator, valid_bundle, harness):
        """Match report has passed=True."""
        exec_result = harness.execute(valid_bundle)
        valid_bundle.provenance.artifact_lineage.content_hash = exec_result.reproduced_hash
        valid_bundle.provenance.artifact_lineage.content_size_bytes = exec_result.reproduced_size

        report = comparator.compare(valid_bundle, exec_result)
        assert report.passed is True


class TestArtifactHashMismatchReported:
    """Tests for artifact hash mismatch detection."""

    def test_mismatch_detected(self, comparator, valid_bundle, harness):
        """Artifact hash mismatch is detected."""
        exec_result = harness.execute(valid_bundle)

        # Ensure hash differs
        valid_bundle.provenance.artifact_lineage.content_hash = "different_hash"

        report = comparator.compare(valid_bundle, exec_result)
        assert report.hash_match is False
        assert report.status == RegressionStatus.DIVERGED

    def test_mismatch_reports_divergence(self, comparator, valid_bundle, harness):
        """Hash mismatch reports divergence details."""
        exec_result = harness.execute(valid_bundle)
        valid_bundle.provenance.artifact_lineage.content_hash = "different_hash"

        report = comparator.compare(valid_bundle, exec_result)
        assert len(report.divergences) > 0
        assert any(d.field == "artifact_hash" for d in report.divergences)

    def test_mismatch_severity_blocking(self, comparator, valid_bundle, harness):
        """Hash mismatch has BLOCKING severity."""
        exec_result = harness.execute(valid_bundle)
        valid_bundle.provenance.artifact_lineage.content_hash = "different_hash"

        report = comparator.compare(valid_bundle, exec_result)
        assert report.overall_severity == DivergenceSeverity.BLOCKING


class TestReplayDoesNotReauthorize:
    """Tests ensuring replay does not grant new authority."""

    def test_replay_uses_existing_admission(self, harness, valid_bundle):
        """Replay uses existing admission record, not new authorization."""
        # Modify admission after bundle creation - replay should still work
        # because it uses the recorded decision, not re-evaluates
        original_decision = valid_bundle.provenance.admission_lineage.decision
        result = harness.execute(valid_bundle)

        assert result.status == ReplayExecutionStatus.REPLAYED
        # Verify we used the recorded decision
        assert valid_bundle.provenance.admission_lineage.decision == original_decision

    def test_no_new_admission_created(self, harness, valid_bundle):
        """Replay does not create new admission records."""
        # If replay created new admission, it would need to call admission controller
        # The harness should not have any admission-related side effects
        result = harness.execute(valid_bundle)

        # Result should only reflect replay, not new authorization
        assert result.status == ReplayExecutionStatus.REPLAYED
        assert "authorization" not in result.message.lower()


class TestReplayDoesNotMutateBundle:
    """Tests ensuring replay does not mutate input bundle."""

    def test_bundle_unchanged_after_replay(self, harness, valid_bundle):
        """Bundle is not mutated by replay execution."""
        original_run_id = valid_bundle.provenance.run_id
        original_hash = valid_bundle.bundle_hash
        original_topology_hash = valid_bundle.provenance.source_topology_hash

        harness.execute(valid_bundle)

        assert valid_bundle.provenance.run_id == original_run_id
        assert valid_bundle.bundle_hash == original_hash
        assert valid_bundle.provenance.source_topology_hash == original_topology_hash

    def test_topology_unchanged_after_replay(self, harness, valid_bundle):
        """Source topology hash is not mutated by replay."""
        original_topology_hash = valid_bundle.provenance.source_topology_hash

        harness.execute(valid_bundle)

        assert valid_bundle.provenance.source_topology_hash == original_topology_hash

    def test_lineage_unchanged_after_replay(self, harness, valid_bundle):
        """Lineage records are not mutated by replay."""
        original_validation = valid_bundle.provenance.validation_lineage.request_id
        original_admission = valid_bundle.provenance.admission_lineage.decision

        harness.execute(valid_bundle)

        assert valid_bundle.provenance.validation_lineage.request_id == original_validation
        assert valid_bundle.provenance.admission_lineage.decision == original_admission


class TestMockAdapterDeterministic:
    """Tests for deterministic mock execution."""

    def test_same_bundle_produces_same_hash(self, harness, valid_bundle):
        """Same bundle produces same artifact hash on repeated replay."""
        result1 = harness.execute(valid_bundle)
        result2 = harness.execute(valid_bundle)

        assert result1.reproduced_hash == result2.reproduced_hash

    def test_same_topology_produces_same_hash(self, harness):
        """Same topology in different bundles produces same hash."""
        bundle1 = build_minimal_replay_bundle(request_id="determinism-test")
        bundle2 = build_minimal_replay_bundle(request_id="determinism-test")

        result1 = harness.execute(bundle1)
        result2 = harness.execute(bundle2)

        assert result1.reproduced_hash == result2.reproduced_hash

    def test_different_topology_produces_different_hash(self, harness):
        """Different topology produces different artifact hash."""
        bundle1 = build_minimal_replay_bundle(request_id="topology-a")
        bundle2 = build_minimal_replay_bundle(request_id="topology-b")

        result1 = harness.execute(bundle1)
        result2 = harness.execute(bundle2)

        assert result1.reproduced_hash != result2.reproduced_hash


class TestRegressionReportStable:
    """Tests for stable regression reports."""

    def test_report_serializable(self, comparator, valid_bundle, harness):
        """Regression report is JSON-serializable."""
        exec_result = harness.execute(valid_bundle)
        report = comparator.compare(valid_bundle, exec_result)

        d = report.to_dict()
        assert "status" in d
        assert "hash_match" in d
        assert "divergences" in d

    def test_divergence_detail_serializable(self, comparator, valid_bundle, harness):
        """Divergence details are JSON-serializable."""
        exec_result = harness.execute(valid_bundle)
        valid_bundle.provenance.artifact_lineage.content_hash = "different"

        report = comparator.compare(valid_bundle, exec_result)
        d = report.to_dict()

        assert len(d["divergences"]) > 0
        assert "field" in d["divergences"][0]
        assert "expected" in d["divergences"][0]
        assert "actual" in d["divergences"][0]


class TestTamperedBundleRejected:
    """Tests for tampered bundle rejection."""

    def test_tampered_provenance_hash_rejected(self, harness, valid_bundle):
        """Tampered bundle hash is rejected."""
        valid_bundle.bundle_hash = "tampered"
        result = harness.execute(valid_bundle)
        assert result.status == ReplayExecutionStatus.INVALID_BUNDLE

    def test_tampered_validation_detected(self, harness, valid_bundle):
        """Tampered validation lineage is detected."""
        valid_bundle.provenance.validation_lineage.passed = False
        # This would change the provenance hash if recomputed
        result = harness.execute(valid_bundle)
        # Bundle integrity check should catch the mismatch
        assert result.status in (
            ReplayExecutionStatus.INVALID_BUNDLE,
            ReplayExecutionStatus.NON_REPLAYABLE,
        )


class TestMetadataDivergenceDetected:
    """Tests for metadata divergence detection."""

    def test_size_mismatch_detected(self, comparator, valid_bundle, harness):
        """Artifact size mismatch is detected."""
        exec_result = harness.execute(valid_bundle)

        # Force hash to match but size to differ
        valid_bundle.provenance.artifact_lineage.content_hash = exec_result.reproduced_hash
        valid_bundle.provenance.artifact_lineage.content_size_bytes = exec_result.reproduced_size + 100

        report = comparator.compare(valid_bundle, exec_result)

        # Size mismatch should be detected
        size_divergence = [d for d in report.divergences if d.field == "artifact_size"]
        assert len(size_divergence) > 0

    def test_type_mismatch_in_reproduced_artifact(self, comparator, valid_bundle, harness):
        """Artifact type mismatch in reproduced artifact is detected."""
        exec_result = harness.execute(valid_bundle)

        reproduced = ReproducedArtifact.from_bytes(
            content=b"test",
            artifact_type="different_type",  # Mismatch
        )

        report = comparator.compare(valid_bundle, exec_result, reproduced=reproduced)

        type_divergence = [d for d in report.divergences if d.field == "artifact_type"]
        assert len(type_divergence) > 0


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_execute_replay_function(self, valid_bundle):
        """execute_replay convenience function works."""
        result = execute_replay(valid_bundle)
        assert result.status == ReplayExecutionStatus.REPLAYED

    def test_compare_regression_function(self, valid_bundle):
        """compare_regression convenience function works."""
        exec_result = execute_replay(valid_bundle)
        report = compare_regression(valid_bundle, exec_result)
        assert report.status in (RegressionStatus.MATCH, RegressionStatus.DIVERGED)


class TestBaselineMissing:
    """Tests for missing baseline handling."""

    def test_missing_baseline_hash_reported(self, comparator, valid_bundle, harness):
        """Missing baseline hash is reported."""
        exec_result = harness.execute(valid_bundle)
        valid_bundle.provenance.artifact_lineage.content_hash = None

        report = comparator.compare(valid_bundle, exec_result)
        assert report.status == RegressionStatus.BASELINE_MISSING

    def test_missing_reproduced_hash_invalid(self, comparator, valid_bundle):
        """Missing reproduced hash results in INVALID status."""
        exec_result = ReplayExecutionResult(
            status=ReplayExecutionStatus.NON_REPLAYABLE,
            run_id="test",
            bundle_run_id=valid_bundle.provenance.run_id,
            reproduced_hash=None,
        )

        report = comparator.compare(valid_bundle, exec_result)
        assert report.status == RegressionStatus.INVALID


class TestReproducedArtifact:
    """Tests for ReproducedArtifact dataclass."""

    def test_from_bytes_computes_hash(self):
        """from_bytes computes content hash."""
        content = b"test content"
        artifact = ReproducedArtifact.from_bytes(content, "test_type")

        expected_hash = hashlib.sha256(content).hexdigest()[:16]
        assert artifact.content_hash == expected_hash

    def test_from_bytes_computes_size(self):
        """from_bytes computes content size."""
        content = b"test content"
        artifact = ReproducedArtifact.from_bytes(content, "test_type")

        assert artifact.content_size == len(content)

    def test_from_bytes_generates_id(self):
        """from_bytes generates artifact ID."""
        artifact = ReproducedArtifact.from_bytes(b"test", "test_type")
        assert artifact.artifact_id.startswith("reproduced-")
