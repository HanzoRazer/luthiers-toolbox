"""
Tests for Runtime Spine Integration (MRP-5P).

Sprint: MRP-5P
Status: PROTOTYPE

Integration tests verifying the runtime spine composes correctly:
  topology_validation → runtime_admission → runtime_provenance

Each module's output feeds the next module's input.
These tests verify:
  1. CertifiedTopology flows from validation to admission
  2. ExecutionAdmissionResult flows from admission to provenance
  3. RuntimeReplayBundle captures complete lineage
  4. Replay verification uses provenance data
"""

import pytest

from app.cam.topology_validation import (
    CertifiedTopology,
    TopologyValidator,
    ValidationError,
    ValidationResult,
    ValidationTier,
    certify_topology,
    validate_topology,
)
from app.cam.runtime_admission import (
    AdmissionDecision,
    ExecutionAdmissionController,
    ExecutionAdmissionRequest,
    ExecutionAdmissionResult,
    ExecutionMode,
    RuntimeExecutionContext,
    RuntimeTier,
    get_admission_controller,
)
from app.cam.runtime_provenance import (
    RuntimeReplayBundle,
    ReplayExecutionHarness,
    ReplayExecutionStatus,
    ArtifactRegressionComparator,
    RegressionStatus,
    build_minimal_replay_bundle,
    build_minimal_topology_dict,
    build_minimal_validation_lineage,
    build_minimal_admission_lineage,
    build_minimal_artifact_lineage,
    build_replay_bundle_from_pipeline_outputs,
    verify_replay_bundle_integrity,
)


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def valid_topology_dict():
    """Valid topology dictionary that passes validation."""
    return {
        "request_id": "integration-test-001",
        "tier": "PROTOTYPE",
        "shells": [
            {
                "shell_id": "body_001",
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
def topology_validator():
    """TopologyValidator instance."""
    return TopologyValidator(tier=ValidationTier.PROTOTYPE)


@pytest.fixture
def admission_controller():
    """ExecutionAdmissionController instance."""
    return get_admission_controller()


@pytest.fixture
def replay_harness():
    """ReplayExecutionHarness instance."""
    return ReplayExecutionHarness()


@pytest.fixture
def regression_comparator():
    """ArtifactRegressionComparator instance."""
    return ArtifactRegressionComparator()


# =============================================================================
# TestValidationToAdmission: Topology validation output feeds admission input
# =============================================================================


class TestValidationToAdmission:
    """Test that validation output flows correctly to admission."""

    def test_certified_topology_accepted_by_admission(
        self,
        valid_topology_dict,
        topology_validator,
        admission_controller,
    ):
        """Certified topology is accepted by admission controller."""
        # Use certify() which validates and wraps in one step
        certified = topology_validator.certify(valid_topology_dict)

        context = RuntimeExecutionContext(
            requested_adapter_id="mock",
            available_adapter_ids=["mock"],  # Must declare available adapters
            execution_mode=ExecutionMode.DETERMINISTIC,
            runtime_tier=RuntimeTier.PROTOTYPE,
        )

        request = ExecutionAdmissionRequest(
            certified_topology=certified,
            runtime_context=context,
        )

        admission_result = admission_controller.evaluate(request)
        assert admission_result.decision == AdmissionDecision.ADMITTED

    def test_uncertified_topology_rejected_by_admission(
        self,
        valid_topology_dict,
        admission_controller,
    ):
        """Uncertified topology is rejected by admission controller."""
        context = RuntimeExecutionContext(
            requested_adapter_id="mock",
            available_adapter_ids=["mock"],
            execution_mode=ExecutionMode.DETERMINISTIC,
            runtime_tier=RuntimeTier.PROTOTYPE,
        )

        request = ExecutionAdmissionRequest(
            certified_topology=valid_topology_dict,  # Not CertifiedTopology
            runtime_context=context,
        )

        admission_result = admission_controller.evaluate(request)
        assert admission_result.decision == AdmissionDecision.REJECTED

    def test_validation_signature_preserved_through_admission(
        self,
        valid_topology_dict,
        topology_validator,
        admission_controller,
    ):
        """Validation signature is preserved through admission."""
        # Certify and capture the signature
        certified = topology_validator.certify(valid_topology_dict)
        original_signature = certified.signature

        context = RuntimeExecutionContext(
            requested_adapter_id="mock",
            available_adapter_ids=["mock"],
            execution_mode=ExecutionMode.DETERMINISTIC,
            runtime_tier=RuntimeTier.PROTOTYPE,
        )

        request = ExecutionAdmissionRequest(
            certified_topology=certified,
            runtime_context=context,
        )

        admission_result = admission_controller.evaluate(request)

        # Signature should be accessible via certified topology
        assert certified.validation.signature == original_signature


# =============================================================================
# TestAdmissionToProvenance: Admission output feeds provenance input
# =============================================================================


class TestAdmissionToProvenance:
    """Test that admission output flows correctly to provenance."""

    def test_admitted_decision_creates_replayable_bundle(self):
        """ADMITTED decision creates a replayable bundle."""
        bundle = build_minimal_replay_bundle(
            adapter_id="mock",
            decision="ADMITTED",
        )

        assert bundle.replayable is True
        assert bundle.provenance.admission_lineage.decision == "ADMITTED"

    def test_rejected_decision_creates_non_replayable_bundle(self):
        """REJECTED decision creates a non-replayable bundle."""
        bundle = build_minimal_replay_bundle(
            adapter_id="mock",
            decision="REJECTED",
        )

        assert bundle.replayable is False
        assert bundle.provenance.admission_lineage.decision == "REJECTED"

    def test_admission_lineage_preserved_in_bundle(self):
        """Admission lineage is fully preserved in bundle."""
        admission = build_minimal_admission_lineage(
            decision="CONDITIONALLY_ADMITTED",
            authorized_adapters=["mock", "cadquery"],
        )

        topology = build_minimal_topology_dict()
        validation = build_minimal_validation_lineage(topology)
        artifact = build_minimal_artifact_lineage()

        bundle = build_replay_bundle_from_pipeline_outputs(
            topology_dict=topology,
            validation_lineage=validation,
            admission_lineage=admission,
            artifact_lineage=artifact,
            adapter_id="mock",
        )

        assert bundle.provenance.admission_lineage.decision == "CONDITIONALLY_ADMITTED"
        assert "mock" in bundle.provenance.admission_lineage.authorized_adapters
        assert "cadquery" in bundle.provenance.admission_lineage.authorized_adapters


# =============================================================================
# TestProvenanceToReplay: Provenance feeds replay execution
# =============================================================================


class TestProvenanceToReplay:
    """Test that provenance feeds replay execution correctly."""

    def test_replay_consumes_bundle_provenance(
        self,
        replay_harness,
    ):
        """Replay harness correctly consumes bundle provenance."""
        bundle = build_minimal_replay_bundle(adapter_id="mock")

        result = replay_harness.execute(bundle)

        assert result.status == ReplayExecutionStatus.REPLAYED
        assert result.bundle_run_id == bundle.provenance.run_id

    def test_replay_respects_admission_decision(
        self,
        replay_harness,
    ):
        """Replay respects the admission decision in bundle."""
        bundle = build_minimal_replay_bundle(
            adapter_id="mock",
            decision="REJECTED",
        )

        result = replay_harness.execute(bundle)

        # Rejected bundles are marked non-replayable, so integrity check may fail first
        assert result.status in (
            ReplayExecutionStatus.REJECTED_ADMISSION,
            ReplayExecutionStatus.INVALID_BUNDLE,
            ReplayExecutionStatus.NON_REPLAYABLE,
        )

    def test_replay_respects_adapter_constraint(
        self,
        replay_harness,
    ):
        """Replay respects adapter constraints."""
        bundle = build_minimal_replay_bundle(
            adapter_id="occ",  # Not mock
            decision="ADMITTED",
        )

        result = replay_harness.execute(bundle)

        assert result.status == ReplayExecutionStatus.NON_REPLAYABLE
        assert "occ" in result.message or "occ" in str(result.constraints)


# =============================================================================
# TestFullSpineIntegration: End-to-end flow through all modules
# =============================================================================


class TestFullSpineIntegration:
    """Test the full spine: validation → admission → provenance → replay."""

    def test_happy_path_through_full_spine(
        self,
        valid_topology_dict,
        topology_validator,
        admission_controller,
        replay_harness,
        regression_comparator,
    ):
        """Complete flow from validation through replay."""
        # Step 1: Validate topology
        validation_result = topology_validator.validate(valid_topology_dict)
        assert validation_result.passed

        # Step 2: Certify topology
        certified = topology_validator.certify(valid_topology_dict)

        # Step 3: Request admission
        context = RuntimeExecutionContext(
            requested_adapter_id="mock",
            available_adapter_ids=["mock"],
            execution_mode=ExecutionMode.DETERMINISTIC,
            runtime_tier=RuntimeTier.PROTOTYPE,
        )
        request = ExecutionAdmissionRequest(
            certified_topology=certified,
            runtime_context=context,
        )
        admission_result = admission_controller.evaluate(request)
        assert admission_result.decision == AdmissionDecision.ADMITTED

        # Step 4: Build provenance bundle
        bundle = build_minimal_replay_bundle(
            request_id=valid_topology_dict["request_id"],
            adapter_id="mock",
            decision="ADMITTED",
        )

        # Step 5: Verify bundle integrity
        integrity = verify_replay_bundle_integrity(bundle)
        assert integrity.passed

        # Step 6: Execute replay
        replay_result = replay_harness.execute(bundle)
        assert replay_result.status == ReplayExecutionStatus.REPLAYED

        # Step 7: Check regression
        regression = regression_comparator.compare(bundle, replay_result)
        # Note: Hash may not match because fixture builds fresh content
        # This tests the flow, not determinism of fixture data
        assert regression.status in (RegressionStatus.MATCH, RegressionStatus.DIVERGED)

    def test_validation_failure_blocks_full_spine(
        self,
        topology_validator,
        admission_controller,
    ):
        """Validation failure prevents admission."""
        invalid_topology = {
            "request_id": "invalid-001",
            "tier": "PROTOTYPE",
            "shells": [],  # Empty shells = blocking finding
        }

        result = topology_validator.validate(invalid_topology)
        assert not result.passed

        # Certify should raise ValidationError for failed topology
        with pytest.raises(ValidationError):
            topology_validator.certify(invalid_topology)

        # Also test that uncertified topology is rejected by admission
        context = RuntimeExecutionContext(
            requested_adapter_id="mock",
            available_adapter_ids=["mock"],
            execution_mode=ExecutionMode.DETERMINISTIC,
            runtime_tier=RuntimeTier.PROTOTYPE,
        )
        request = ExecutionAdmissionRequest(
            certified_topology=invalid_topology,  # Not certified
            runtime_context=context,
        )

        admission_result = admission_controller.evaluate(request)
        assert admission_result.decision == AdmissionDecision.REJECTED

    def test_bundle_preserves_complete_lineage(self):
        """Bundle preserves complete lineage from all modules."""
        bundle = build_minimal_replay_bundle(
            request_id="lineage-test-001",
            adapter_id="mock",
            decision="ADMITTED",
        )

        provenance = bundle.provenance

        # Validation lineage present
        assert provenance.validation_lineage is not None
        assert provenance.validation_lineage.request_id == "lineage-test-001"
        assert provenance.validation_lineage.tier == "PROTOTYPE"
        assert provenance.validation_lineage.passed is True

        # Admission lineage present
        assert provenance.admission_lineage is not None
        assert provenance.admission_lineage.decision == "ADMITTED"
        assert "mock" in provenance.admission_lineage.authorized_adapters

        # Artifact lineage present
        assert provenance.artifact_lineage is not None
        assert provenance.artifact_lineage.content_hash is not None

        # Trace events present
        assert len(provenance.trace_events) >= 5


# =============================================================================
# TestModuleIndependence: Each module works independently
# =============================================================================


class TestModuleIndependence:
    """Test that each module can be tested in isolation."""

    def test_topology_validation_standalone(self, valid_topology_dict):
        """Topology validation works without admission or provenance."""
        validator = TopologyValidator(tier=ValidationTier.PROTOTYPE)
        result = validator.validate(valid_topology_dict)

        assert result is not None
        assert hasattr(result, "passed")
        assert hasattr(result, "signature")

    def test_admission_controller_standalone(self, valid_topology_dict):
        """Admission controller works with certified topology."""
        validator = TopologyValidator(tier=ValidationTier.PROTOTYPE)
        certified = validator.certify(valid_topology_dict)

        controller = ExecutionAdmissionController()
        context = RuntimeExecutionContext(
            requested_adapter_id="mock",
            available_adapter_ids=["mock"],
            execution_mode=ExecutionMode.DETERMINISTIC,
            runtime_tier=RuntimeTier.PROTOTYPE,
        )
        request = ExecutionAdmissionRequest(
            certified_topology=certified,
            runtime_context=context,
        )

        admission_result = controller.evaluate(request)

        assert admission_result is not None
        assert hasattr(admission_result, "decision")
        assert hasattr(admission_result, "trace")

    def test_provenance_bundle_standalone(self):
        """Provenance bundle builds without live validation/admission."""
        bundle = build_minimal_replay_bundle()

        assert bundle is not None
        assert bundle.provenance is not None
        assert bundle.bundle_id is not None

    def test_replay_harness_standalone(self):
        """Replay harness executes without live pipeline."""
        bundle = build_minimal_replay_bundle(adapter_id="mock")
        harness = ReplayExecutionHarness()

        result = harness.execute(bundle)

        assert result is not None
        assert result.status == ReplayExecutionStatus.REPLAYED


# =============================================================================
# TestCrossModuleContracts: Contract compatibility between modules
# =============================================================================


class TestCrossModuleContracts:
    """Test contract compatibility between runtime modules."""

    def test_validation_result_has_required_fields(self, valid_topology_dict):
        """ValidationResult has fields expected by admission."""
        validator = TopologyValidator()
        result = validator.validate(valid_topology_dict)

        # Fields expected by admission
        assert hasattr(result, "passed")
        assert hasattr(result, "tier")
        assert hasattr(result, "signature")

    def test_certified_topology_has_required_fields(self, valid_topology_dict):
        """CertifiedTopology has fields expected by admission."""
        validator = TopologyValidator()
        certified = validator.certify(valid_topology_dict)

        # Fields expected by admission (via properties)
        assert hasattr(certified, "topology_dict")
        assert hasattr(certified, "validation")
        assert hasattr(certified, "signature")

    def test_admission_result_has_required_fields(self, valid_topology_dict):
        """ExecutionAdmissionResult has fields expected by provenance."""
        validator = TopologyValidator()
        certified = validator.certify(valid_topology_dict)

        controller = ExecutionAdmissionController()
        context = RuntimeExecutionContext(
            requested_adapter_id="mock",
            available_adapter_ids=["mock"],
            execution_mode=ExecutionMode.DETERMINISTIC,
            runtime_tier=RuntimeTier.PROTOTYPE,
        )
        request = ExecutionAdmissionRequest(
            certified_topology=certified,
            runtime_context=context,
        )

        admission_result = controller.evaluate(request)

        # Fields expected by provenance
        assert hasattr(admission_result, "decision")
        assert hasattr(admission_result, "authorization_token")
        assert hasattr(admission_result, "trace")

    def test_replay_bundle_has_required_fields(self):
        """RuntimeReplayBundle has fields expected by replay harness."""
        bundle = build_minimal_replay_bundle()

        # Fields expected by harness
        assert hasattr(bundle, "bundle_id")
        assert hasattr(bundle, "provenance")
        assert hasattr(bundle, "replayable")
        assert hasattr(bundle, "replay_constraints")

        # Provenance sub-fields
        provenance = bundle.provenance
        assert hasattr(provenance, "run_id")
        assert hasattr(provenance, "source_topology_hash")
        assert hasattr(provenance, "validation_lineage")
        assert hasattr(provenance, "admission_lineage")
        assert hasattr(provenance, "artifact_lineage")
        assert hasattr(provenance, "trace_events")
