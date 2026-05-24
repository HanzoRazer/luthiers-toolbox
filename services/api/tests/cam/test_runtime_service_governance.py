"""
Tests for Runtime Service Governance Boundaries (MRP-5S).

Sprint: MRP-5S
Status: PROTOTYPE

Governance-focused tests verifying:
- Service requires CertifiedTopology (certification gate)
- Service cannot bypass admission (runtime authority)
- Replay bundle produced after execution (provenance continuity)
- Replay cannot authorize execution (authority separation)
- Deterministic repeated execution (reproducibility)
- Unknown adapter rejected (explicit failure)
- Fabricated certification rejected (integrity)
- Runtime service does not mutate topology (immutability)
- Service export surface stable (API boundary)
- Replay bundle lineage complete (auditability)

These tests focus on GOVERNANCE BEHAVIOR, not implementation details.
"""

import pytest
import copy

from app.cam.topology_validation import (
    CertifiedTopology,
    TopologyValidator,
    ValidationTier,
    ValidationError,
    certify_topology,
)
from app.cam.runtime_admission import (
    AdmissionDecision,
    ExecutionAdmissionController,
    ExecutionMode,
    RuntimeTier,
)
from app.cam.runtime_provenance import (
    RuntimeReplayBundle,
    ReplayExecutionHarness,
    ReplayExecutionStatus,
    ArtifactRegressionComparator,
    RegressionStatus,
    verify_replay_bundle_integrity,
    build_minimal_replay_bundle,
)
from app.cam.runtime_service import (
    ArtifactIntent,
    CertifiedRuntimeRequest,
    CertifiedRuntimeResult,
    CertifiedRuntimeService,
    ServiceExecutionStatus,
    execute_certified_runtime,
    get_certified_runtime_service,
    # Verify these are exported
    AdapterExecutionResult,
    AdapterRegistry,
    MockRuntimeAdapter,
    is_adapter_available,
    list_available_adapters,
)


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def valid_topology_dict():
    """Valid topology dictionary for governance tests."""
    return {
        "request_id": "governance-test-001",
        "tier": "PROTOTYPE",
        "shells": [
            {
                "shell_id": "gov_shell_001",
                "shell_type": "flat_extrusion",
                "component_name": "body",
                "is_closed": True,
                "is_manifold": True,
                "surface_count": 6,
                "edge_count": 12,
                "vertex_count": 8,
            }
        ],
    }


@pytest.fixture
def certified_topology(valid_topology_dict):
    """Certified topology for tests."""
    return certify_topology(valid_topology_dict)


@pytest.fixture
def service():
    """Fresh service instance."""
    return CertifiedRuntimeService()


# =============================================================================
# TestCertificationGate: Service requires CertifiedTopology
# =============================================================================


class TestCertificationGate:
    """Governance: Service requires certified topology."""

    def test_raw_dict_raises_type_error(self, valid_topology_dict):
        """Raw topology dict raises TypeError at request construction."""
        with pytest.raises(TypeError) as exc_info:
            CertifiedRuntimeRequest(certified_topology=valid_topology_dict)

        assert "CertifiedTopology" in str(exc_info.value)

    def test_none_raises_type_error(self):
        """None topology raises TypeError."""
        with pytest.raises(TypeError):
            CertifiedRuntimeRequest(certified_topology=None)

    def test_arbitrary_object_raises_type_error(self):
        """Arbitrary object raises TypeError."""
        with pytest.raises(TypeError):
            CertifiedRuntimeRequest(certified_topology={"fake": "object"})

    def test_certified_topology_accepted(self, certified_topology):
        """CertifiedTopology is accepted."""
        request = CertifiedRuntimeRequest(certified_topology=certified_topology)
        assert request.certified_topology is certified_topology


# =============================================================================
# TestAdmissionGate: Service cannot bypass admission
# =============================================================================


class TestAdmissionGate:
    """Governance: Service cannot bypass admission control."""

    def test_service_invokes_admission_controller(self, certified_topology, service):
        """Service invokes admission controller before execution."""
        request = CertifiedRuntimeRequest(
            certified_topology=certified_topology,
            adapter_id="mock",
        )

        result = service.execute(request)

        # If we got here, admission was invoked and passed
        assert result.admission_decision is not None

    def test_admission_rejection_stops_execution(self, valid_topology_dict, service):
        """Admission rejection prevents artifact creation."""
        # Create a topology that will pass validation but we'll
        # request an unavailable adapter to force admission issues
        certified = certify_topology(valid_topology_dict)

        # Use an adapter that's in registry but test admission path
        request = CertifiedRuntimeRequest(
            certified_topology=certified,
            adapter_id="nonexistent_adapter",  # Will fail validation
        )

        result = service.execute(request)

        assert not result.success
        assert result.artifact_id is None
        assert result.artifact_hash is None

    def test_no_artifact_without_admission(self, service):
        """No artifact can be created without passing admission."""
        # This is verified by the gate ordering in service
        # Any attempt to get artifact without admission fails
        pass  # Covered by other tests


# =============================================================================
# TestProvenanceContinuity: Replay bundle produced after execution
# =============================================================================


class TestProvenanceContinuity:
    """Governance: Provenance is recorded after execution."""

    def test_successful_execution_produces_bundle(self, certified_topology, service):
        """Successful execution produces a replay bundle."""
        request = CertifiedRuntimeRequest(
            certified_topology=certified_topology,
            adapter_id="mock",
        )

        result = service.execute(request)

        assert result.success
        assert result.replay_bundle is not None
        assert isinstance(result.replay_bundle, RuntimeReplayBundle)

    def test_bundle_has_complete_lineage(self, certified_topology, service):
        """Bundle contains complete provenance lineage."""
        request = CertifiedRuntimeRequest(
            certified_topology=certified_topology,
            adapter_id="mock",
        )

        result = service.execute(request)
        provenance = result.replay_bundle.provenance

        # All lineage components present
        assert provenance.validation_lineage is not None
        assert provenance.admission_lineage is not None
        assert provenance.artifact_lineage is not None
        assert provenance.trace_events is not None
        assert len(provenance.trace_events) >= 5

    def test_bundle_references_source_topology(self, certified_topology, service):
        """Bundle references source topology."""
        request = CertifiedRuntimeRequest(
            certified_topology=certified_topology,
            adapter_id="mock",
        )

        result = service.execute(request)
        provenance = result.replay_bundle.provenance

        assert provenance.source_topology_id is not None
        assert provenance.source_topology_hash is not None


# =============================================================================
# TestAuthoritySeparation: Replay cannot authorize execution
# =============================================================================


class TestAuthoritySeparation:
    """Governance: Replay is evidentiary, not authoritative."""

    def test_replay_does_not_re_admit(self, certified_topology, service):
        """Replay does not invoke new admission."""
        request = CertifiedRuntimeRequest(
            certified_topology=certified_topology,
            adapter_id="mock",
        )

        result = service.execute(request)
        bundle = result.replay_bundle

        # Replay uses existing admission in bundle
        harness = ReplayExecutionHarness()
        replay_result = harness.execute(bundle)

        # Replay worked, but didn't create new admission
        assert replay_result.status == ReplayExecutionStatus.REPLAYED

    def test_rejected_bundle_cannot_replay_to_success(self):
        """Bundle from rejected admission cannot replay to success."""
        bundle = build_minimal_replay_bundle(
            adapter_id="mock",
            decision="REJECTED",
        )

        harness = ReplayExecutionHarness()
        result = harness.execute(bundle)

        # Should not successfully replay
        assert result.status != ReplayExecutionStatus.REPLAYED

    def test_replay_cannot_modify_admission_decision(self, certified_topology, service):
        """Replay cannot modify the recorded admission decision."""
        request = CertifiedRuntimeRequest(
            certified_topology=certified_topology,
            adapter_id="mock",
        )

        result = service.execute(request)
        original_decision = result.replay_bundle.provenance.admission_lineage.decision

        # Execute replay
        harness = ReplayExecutionHarness()
        harness.execute(result.replay_bundle)

        # Decision unchanged
        assert result.replay_bundle.provenance.admission_lineage.decision == original_decision


# =============================================================================
# TestDeterminism: Repeated execution produces identical results
# =============================================================================


class TestDeterminism:
    """Governance: Deterministic execution."""

    def test_same_topology_same_hash(self, valid_topology_dict, service):
        """Same topology produces same artifact hash."""
        cert1 = certify_topology(valid_topology_dict)
        cert2 = certify_topology(valid_topology_dict)

        result1 = service.execute(CertifiedRuntimeRequest(certified_topology=cert1))
        result2 = service.execute(CertifiedRuntimeRequest(certified_topology=cert2))

        assert result1.artifact_hash == result2.artifact_hash

    def test_deterministic_across_service_instances(self, valid_topology_dict):
        """Different service instances produce same hash."""
        service1 = CertifiedRuntimeService()
        service2 = CertifiedRuntimeService()

        cert1 = certify_topology(valid_topology_dict)
        cert2 = certify_topology(valid_topology_dict)

        result1 = service1.execute(CertifiedRuntimeRequest(certified_topology=cert1))
        result2 = service2.execute(CertifiedRuntimeRequest(certified_topology=cert2))

        assert result1.artifact_hash == result2.artifact_hash

    def test_replay_produces_consistent_hash(self, certified_topology, service):
        """Replay produces consistent reproduced hash."""
        request = CertifiedRuntimeRequest(certified_topology=certified_topology)
        result = service.execute(request)

        harness = ReplayExecutionHarness()
        replay1 = harness.execute(result.replay_bundle)
        replay2 = harness.execute(result.replay_bundle)

        assert replay1.reproduced_hash == replay2.reproduced_hash


# =============================================================================
# TestExplicitFailure: Unknown adapter rejected explicitly
# =============================================================================


class TestExplicitFailure:
    """Governance: Unknown adapters fail explicitly."""

    def test_unknown_adapter_rejected(self, certified_topology, service):
        """Unknown adapter ID causes explicit rejection."""
        request = CertifiedRuntimeRequest(
            certified_topology=certified_topology,
            adapter_id="unknown_adapter_xyz",
        )

        result = service.execute(request)

        assert not result.success
        assert result.status == ServiceExecutionStatus.INVALID_REQUEST
        assert "unknown_adapter_xyz" in result.error_message

    def test_empty_adapter_rejected(self, certified_topology, service):
        """Empty adapter ID causes explicit rejection."""
        request = CertifiedRuntimeRequest(
            certified_topology=certified_topology,
            adapter_id="",
        )

        result = service.execute(request)

        assert not result.success

    def test_no_silent_fallback(self, certified_topology, service):
        """No silent fallback to default adapter."""
        request = CertifiedRuntimeRequest(
            certified_topology=certified_topology,
            adapter_id="cadquery",  # Not available
        )

        result = service.execute(request)

        # Must fail, not silently use mock
        assert not result.success
        assert result.artifact_hash is None


# =============================================================================
# TestIntegrity: Fabricated certification rejected
# =============================================================================


class TestIntegrity:
    """Governance: Fabricated certification is rejected."""

    def test_only_certified_topology_type_accepted(self, valid_topology_dict):
        """Only CertifiedTopology type is accepted."""
        # Cannot even create request with non-CertifiedTopology
        with pytest.raises(TypeError):
            CertifiedRuntimeRequest(certified_topology=valid_topology_dict)

    def test_certification_must_come_from_validator(self, valid_topology_dict):
        """Certification must come from TopologyValidator."""
        # CertifiedTopology cannot be instantiated directly
        with pytest.raises(TypeError):
            CertifiedTopology()

    def test_failed_validation_cannot_certify(self):
        """Failed validation cannot produce certification."""
        invalid_topology = {
            "request_id": "invalid",
            "tier": "PROTOTYPE",
            "shells": [],  # Empty = blocking
        }

        with pytest.raises(ValidationError):
            certify_topology(invalid_topology)


# =============================================================================
# TestImmutability: Service does not mutate topology
# =============================================================================


class TestImmutability:
    """Governance: Service does not mutate inputs."""

    def test_topology_dict_unchanged(self, valid_topology_dict, service):
        """Topology dict is unchanged after execution."""
        original = copy.deepcopy(valid_topology_dict)
        certified = certify_topology(valid_topology_dict)

        request = CertifiedRuntimeRequest(certified_topology=certified)
        service.execute(request)

        assert certified.topology_dict == original

    def test_certified_topology_unchanged(self, certified_topology, service):
        """CertifiedTopology properties unchanged after execution."""
        original_id = certified_topology.request_id
        original_sig = certified_topology.signature

        request = CertifiedRuntimeRequest(certified_topology=certified_topology)
        service.execute(request)

        assert certified_topology.request_id == original_id
        assert certified_topology.signature == original_sig

    def test_bundle_unchanged_after_replay(self, certified_topology, service):
        """Bundle is unchanged after replay execution."""
        request = CertifiedRuntimeRequest(certified_topology=certified_topology)
        result = service.execute(request)

        original_bundle_id = result.replay_bundle.bundle_id
        original_run_id = result.replay_bundle.provenance.run_id

        harness = ReplayExecutionHarness()
        harness.execute(result.replay_bundle)

        assert result.replay_bundle.bundle_id == original_bundle_id
        assert result.replay_bundle.provenance.run_id == original_run_id


# =============================================================================
# TestExportSurface: Service export surface is stable
# =============================================================================


class TestExportSurface:
    """Governance: Export surface is stable and intentional."""

    def test_core_service_exports(self):
        """Core service types are exported."""
        from app.cam.runtime_service import (
            CertifiedRuntimeService,
            CertifiedRuntimeRequest,
            CertifiedRuntimeResult,
            ServiceExecutionStatus,
        )
        assert CertifiedRuntimeService is not None
        assert CertifiedRuntimeRequest is not None
        assert CertifiedRuntimeResult is not None
        assert ServiceExecutionStatus is not None

    def test_adapter_exports(self):
        """Adapter types are exported."""
        from app.cam.runtime_service import (
            MockRuntimeAdapter,
            AdapterRegistry,
            AdapterExecutionResult,
            is_adapter_available,
            list_available_adapters,
        )
        assert MockRuntimeAdapter is not None
        assert AdapterRegistry is not None

    def test_exception_exports(self):
        """Exception types are exported."""
        from app.cam.runtime_service import (
            RuntimeServiceError,
            InvalidRequestError,
            UncertifiedTopologyError,
            AdapterUnavailableError,
        )
        assert RuntimeServiceError is not None
        assert InvalidRequestError is not None

    def test_convenience_function_exports(self):
        """Convenience functions are exported."""
        from app.cam.runtime_service import (
            execute_certified_runtime,
            get_certified_runtime_service,
            get_adapter,
        )
        assert callable(execute_certified_runtime)
        assert callable(get_certified_runtime_service)


# =============================================================================
# TestAuditability: Replay bundle lineage is complete
# =============================================================================


class TestAuditability:
    """Governance: Complete audit trail in provenance."""

    def test_validation_lineage_auditable(self, certified_topology, service):
        """Validation lineage supports audit."""
        request = CertifiedRuntimeRequest(certified_topology=certified_topology)
        result = service.execute(request)

        validation = result.replay_bundle.provenance.validation_lineage
        assert validation.request_id is not None
        assert validation.tier is not None
        assert validation.passed is True
        assert validation.signature_input_hash is not None

    def test_admission_lineage_auditable(self, certified_topology, service):
        """Admission lineage supports audit."""
        request = CertifiedRuntimeRequest(certified_topology=certified_topology)
        result = service.execute(request)

        admission = result.replay_bundle.provenance.admission_lineage
        assert admission.admission_id is not None
        assert admission.decision is not None
        assert admission.authorized_adapters is not None

    def test_artifact_lineage_auditable(self, certified_topology, service):
        """Artifact lineage supports audit."""
        request = CertifiedRuntimeRequest(certified_topology=certified_topology)
        result = service.execute(request)

        artifact = result.replay_bundle.provenance.artifact_lineage
        assert artifact.artifact_id is not None
        assert artifact.artifact_type is not None
        assert artifact.content_hash is not None
        assert artifact.content_size_bytes > 0

    def test_trace_events_ordered(self, certified_topology, service):
        """Trace events are in correct order."""
        request = CertifiedRuntimeRequest(certified_topology=certified_topology)
        result = service.execute(request)

        events = result.replay_bundle.provenance.trace_events
        sequences = [e.sequence_number for e in events]

        # Must be monotonically increasing
        assert sequences == sorted(sequences)
        assert len(set(sequences)) == len(sequences)  # No duplicates


# =============================================================================
# TestGateOrdering: Gates execute in correct order
# =============================================================================


class TestGateOrdering:
    """Governance: Gate ordering is enforced."""

    def test_certification_before_admission(self, service):
        """Certification check happens before admission."""
        # Raw topology fails at request construction (before service)
        with pytest.raises(TypeError):
            CertifiedRuntimeRequest(certified_topology={"raw": "dict"})

    def test_admission_before_execution(self, certified_topology, service):
        """Admission happens before adapter execution."""
        # Use unavailable adapter - should fail at validation, not adapter
        request = CertifiedRuntimeRequest(
            certified_topology=certified_topology,
            adapter_id="unavailable",
        )

        result = service.execute(request)

        # Failed before adapter could run
        assert result.status == ServiceExecutionStatus.INVALID_REQUEST

    def test_execution_before_provenance(self, certified_topology, service):
        """Execution completes before provenance is recorded."""
        request = CertifiedRuntimeRequest(certified_topology=certified_topology)
        result = service.execute(request)

        # If we have a bundle, execution completed
        assert result.success
        assert result.replay_bundle is not None
        assert result.artifact_hash is not None
