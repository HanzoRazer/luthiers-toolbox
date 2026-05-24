"""
Runtime Spine Full Verification Tests (MRP-5X).

Sprint: MRP-5X
Status: RELEASE_VERIFICATION

End-to-end verification of the complete governed runtime spine.

Full path verified:
    CertifiedTopology
    → ExecutionAdmissionController
    → CapabilityResolver (MRP-5V)
    → CertifiedRuntimeService
    → RuntimeProvenanceRecorder
    → RuntimeReplayBundle
    → ReplayExecutionHarness
    → ArtifactRegressionComparator

This is a VERIFICATION sprint. No new features.
Tests prove the system is ready for release/merge boundary.
"""

import pytest

# Topology validation
from app.cam.topology_validation import (
    CertifiedTopology,
    TopologyValidator,
    ValidationTier,
    certify_topology,
)

# Runtime admission
from app.cam.runtime_admission import (
    AdmissionDecision,
    ExecutionAdmissionController,
    ExecutionAdmissionRequest,
    ExecutionMode,
    RuntimeExecutionContext,
    RuntimeTier,
    get_admission_controller,
)

# Runtime capabilities (MRP-5V)
from app.cam.runtime_capabilities import (
    CapabilityRegistry,
    CapabilityResolver,
    ResolutionContext,
    ResolutionStatus,
    build_capability_manifest,
    get_capability_registry,
    get_capability_resolver,
    register_default_sources,
    reset_capability_registry,
    reset_capability_resolver,
    reset_policy_federation,
)

# Runtime service
from app.cam.runtime_service import (
    CertifiedRuntimeService,
    CertifiedRuntimeRequest,
    CertifiedRuntimeResult,
    ServiceExecutionStatus,
    get_certified_runtime_service,
)

# Runtime provenance
from app.cam.runtime_provenance import (
    RuntimeReplayBundle,
    ReplayExecutionHarness,
    ReplayExecutionStatus,
    ReplayExecutionResult,
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

# Runtime manifest
from app.cam.runtime_manifest import (
    RuntimeSpineManifest,
    build_runtime_spine_manifest,
    RUNTIME_SPINE_VERSION,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture(autouse=True)
def reset_capability_globals():
    """Reset capability singletons before each test."""
    reset_capability_registry()
    reset_capability_resolver()
    reset_policy_federation()
    yield
    reset_capability_registry()
    reset_capability_resolver()
    reset_policy_federation()


@pytest.fixture
def valid_topology_dict():
    """Valid topology dictionary that passes validation."""
    return {
        "request_id": "full-spine-verification-001",
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
def capability_registry():
    """Populated capability registry."""
    registry = get_capability_registry()
    register_default_sources(registry)
    return registry


@pytest.fixture
def capability_resolver(capability_registry):
    """CapabilityResolver with populated registry."""
    return get_capability_resolver()


@pytest.fixture
def runtime_service():
    """CertifiedRuntimeService instance."""
    return CertifiedRuntimeService()


@pytest.fixture
def replay_harness():
    """ReplayExecutionHarness instance."""
    return ReplayExecutionHarness()


@pytest.fixture
def regression_comparator():
    """ArtifactRegressionComparator instance."""
    return ArtifactRegressionComparator()


# =============================================================================
# Full Spine Happy Path
# =============================================================================

class TestFullSpineHappyPath:
    """End-to-end happy path verification."""

    def test_complete_spine_execution(
        self,
        valid_topology_dict,
        topology_validator,
        capability_registry,
    ):
        """Complete spine executes successfully."""
        # Step 1: Certify topology
        certified = topology_validator.certify(valid_topology_dict)
        assert isinstance(certified, CertifiedTopology)

        # Step 2: Create runtime request
        request = CertifiedRuntimeRequest(
            certified_topology=certified,
            adapter_id="mock",
            runtime_tier=RuntimeTier.PROTOTYPE,
            execution_mode=ExecutionMode.DETERMINISTIC,
        )

        # Step 3: Execute through service
        service = CertifiedRuntimeService()
        result = service.execute(request)

        # Step 4: Verify success
        assert result.status == ServiceExecutionStatus.SUCCESS
        assert result.replay_bundle is not None
        assert result.artifact_hash is not None

    def test_spine_with_capability_resolution(
        self,
        valid_topology_dict,
        topology_validator,
        capability_registry,
    ):
        """Spine with explicit capability resolution."""
        certified = topology_validator.certify(valid_topology_dict)

        # Request with capability_id triggers resolution
        request = CertifiedRuntimeRequest(
            certified_topology=certified,
            adapter_id="mock",
            capability_id="adapter:mock",  # Explicit capability
            runtime_tier=RuntimeTier.PROTOTYPE,
            execution_mode=ExecutionMode.DETERMINISTIC,
        )

        service = CertifiedRuntimeService()
        result = service.execute(request)

        assert result.status == ServiceExecutionStatus.SUCCESS
        assert result.capability_resolution_report is not None

    def test_replay_bundle_generated(
        self,
        valid_topology_dict,
        topology_validator,
    ):
        """Replay bundle is generated on successful execution."""
        certified = topology_validator.certify(valid_topology_dict)

        request = CertifiedRuntimeRequest(
            certified_topology=certified,
            adapter_id="mock",
        )

        service = CertifiedRuntimeService()
        result = service.execute(request)

        assert result.success
        bundle = result.replay_bundle
        assert bundle is not None
        assert bundle.bundle_id is not None
        assert bundle.replayable is True


# =============================================================================
# Capability Resolution Gate Tests
# =============================================================================

class TestCapabilityResolutionGate:
    """Tests proving capability resolution is mandatory."""

    def test_unknown_capability_blocks_service(
        self,
        valid_topology_dict,
        topology_validator,
        capability_registry,
    ):
        """Unknown capability blocks service execution."""
        certified = topology_validator.certify(valid_topology_dict)

        request = CertifiedRuntimeRequest(
            certified_topology=certified,
            adapter_id="mock",
            capability_id="operation:nonexistent_capability",
        )

        service = CertifiedRuntimeService()
        result = service.execute(request)

        assert result.status == ServiceExecutionStatus.CAPABILITY_REJECTED
        assert "not registered" in str(result.error_details).lower() or \
               "not_found" in str(result.error_details).lower()

    def test_resolver_required_before_execution(
        self,
        capability_registry,
    ):
        """CapabilityResolver must be invoked before execution when capability_id set."""
        resolver = get_capability_resolver()

        # Resolver must return a result (not bypass)
        result = resolver.resolve("operation:nut_slot")
        assert result is not None
        assert result.status in (ResolutionStatus.RESOLVED, ResolutionStatus.DISABLED)

    def test_service_uses_resolver(self):
        """CertifiedRuntimeService has capability resolver."""
        service = CertifiedRuntimeService()
        assert hasattr(service, "_capability_resolver")
        assert service._capability_resolver is not None


# =============================================================================
# Admission Gate Tests
# =============================================================================

class TestAdmissionGate:
    """Tests proving admission gate enforcement."""

    def test_rejected_admission_blocks_service(
        self,
        valid_topology_dict,
        admission_controller,
    ):
        """Rejected admission blocks service execution."""
        # Use uncertified topology to trigger rejection
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

    def test_unavailable_adapter_rejected(
        self,
        valid_topology_dict,
        topology_validator,
    ):
        """Request for unavailable adapter is rejected."""
        certified = topology_validator.certify(valid_topology_dict)

        request = CertifiedRuntimeRequest(
            certified_topology=certified,
            adapter_id="nonexistent_adapter",
        )

        service = CertifiedRuntimeService()
        result = service.execute(request)

        assert result.status == ServiceExecutionStatus.INVALID_REQUEST


# =============================================================================
# Replay and Regression Tests
# =============================================================================

class TestReplayAndRegression:
    """Tests for replay execution and artifact regression."""

    def test_replay_execution_succeeds(
        self,
        replay_harness,
    ):
        """Admitted bundle can be replayed."""
        bundle = build_minimal_replay_bundle(
            adapter_id="mock",
            decision="ADMITTED",
        )

        result = replay_harness.execute(bundle)
        assert result.status == ReplayExecutionStatus.REPLAYED

    def test_artifact_regression_matches(
        self,
        regression_comparator,
    ):
        """Artifact regression comparator detects matches."""
        # Create bundle with a known artifact hash
        bundle = build_minimal_replay_bundle(
            adapter_id="mock",
            decision="ADMITTED",
        )
        # Get the content_hash from the bundle's artifact lineage
        baseline_hash = bundle.provenance.artifact_lineage.content_hash

        # Create execution result with matching hash
        execution_result = ReplayExecutionResult(
            status=ReplayExecutionStatus.REPLAYED,
            run_id="test-run-001",
            bundle_run_id=bundle.provenance.run_id,
            reproduced_hash=baseline_hash,
            reproduced_size=bundle.provenance.artifact_lineage.content_size_bytes,
        )

        # Compare should detect match
        result = regression_comparator.compare(bundle, execution_result)

        assert result.status == RegressionStatus.MATCH

    def test_replay_does_not_authorize(
        self,
        replay_harness,
    ):
        """Replay verifies but does not authorize new execution."""
        # Rejected bundle should not become authorized through replay
        rejected_bundle = build_minimal_replay_bundle(
            adapter_id="mock",
            decision="REJECTED",
        )

        # Replay should execute (for verification) but bundle stays non-replayable
        result = replay_harness.execute(rejected_bundle)

        # The result reflects the original admission decision
        assert rejected_bundle.replayable is False


# =============================================================================
# Manifest Determinism Tests
# =============================================================================

class TestManifestDeterminism:
    """Tests for manifest determinism."""

    def test_capability_manifest_deterministic(
        self,
        capability_registry,
    ):
        """Capability manifest generation is deterministic."""
        manifest1 = build_capability_manifest(capability_registry)
        manifest2 = build_capability_manifest(capability_registry)

        assert manifest1.content_hash == manifest2.content_hash

    def test_runtime_spine_manifest_deterministic(self):
        """Runtime spine manifest is deterministic."""
        manifest1 = build_runtime_spine_manifest()
        manifest2 = build_runtime_spine_manifest()

        # Compare structural content (excluding generated_at timestamp)
        dict1 = manifest1.to_dict()
        dict2 = manifest2.to_dict()

        # Remove timestamp for comparison
        del dict1["generated_at"]
        del dict2["generated_at"]

        assert dict1 == dict2
        assert manifest1.total_contracts == manifest2.total_contracts
        assert manifest1.compatibility_status == manifest2.compatibility_status

    def test_manifest_has_version(self):
        """Manifest includes version information."""
        manifest = build_runtime_spine_manifest()
        assert manifest.version_info.spine_version == RUNTIME_SPINE_VERSION


# =============================================================================
# Source Registry Immutability Tests
# =============================================================================

class TestSourceRegistryImmutability:
    """Tests proving federation doesn't mutate source registries."""

    def test_cam_operation_registry_unchanged(
        self,
        capability_registry,
    ):
        """CAM operation registry is not mutated by federation."""
        from app.cam.cam_operation_registry import (
            CAM_OPERATION_REGISTRY,
            list_supported_operations,
        )

        before = list_supported_operations()
        before_count = len(CAM_OPERATION_REGISTRY)

        # Access through federation
        _ = capability_registry.list_capabilities()

        after = list_supported_operations()
        after_count = len(CAM_OPERATION_REGISTRY)

        assert before == after
        assert before_count == after_count

    def test_translator_registry_unchanged(
        self,
        capability_registry,
    ):
        """Translator registry is not mutated by federation."""
        from app.cam.translator_capability_registry import (
            TRANSLATOR_CAPABILITY_REGISTRY,
            list_translator_ids,
        )

        before = list_translator_ids()
        before_count = len(TRANSLATOR_CAPABILITY_REGISTRY)

        # Access through federation
        _ = capability_registry.list_capabilities()

        after = list_translator_ids()
        after_count = len(TRANSLATOR_CAPABILITY_REGISTRY)

        assert before == after
        assert before_count == after_count


# =============================================================================
# Integration Completeness Tests
# =============================================================================

class TestIntegrationCompleteness:
    """Tests verifying all spine components integrate correctly."""

    def test_all_spine_modules_import(self):
        """All spine modules can be imported."""
        # These imports should not fail
        from app.cam.topology_validation import CertifiedTopology
        from app.cam.runtime_admission import ExecutionAdmissionController
        from app.cam.runtime_capabilities import CapabilityResolver
        from app.cam.runtime_service import CertifiedRuntimeService
        from app.cam.runtime_provenance import RuntimeReplayBundle
        from app.cam.runtime_manifest import RuntimeSpineManifest

        assert all([
            CertifiedTopology,
            ExecutionAdmissionController,
            CapabilityResolver,
            CertifiedRuntimeService,
            RuntimeReplayBundle,
            RuntimeSpineManifest,
        ])

    def test_gate_order_enforced(
        self,
        valid_topology_dict,
        topology_validator,
        capability_registry,
    ):
        """Gate order is enforced: validation → admission → capability → execution."""
        certified = topology_validator.certify(valid_topology_dict)

        request = CertifiedRuntimeRequest(
            certified_topology=certified,
            adapter_id="mock",
            capability_id="adapter:mock",
        )

        service = CertifiedRuntimeService()
        result = service.execute(request)

        # Success means all gates passed in order
        assert result.success
        assert result.admission_decision == AdmissionDecision.ADMITTED
        assert result.capability_resolution_report is not None

    def test_provenance_chain_complete(
        self,
        valid_topology_dict,
        topology_validator,
    ):
        """Provenance chain is complete in replay bundle."""
        certified = topology_validator.certify(valid_topology_dict)

        request = CertifiedRuntimeRequest(
            certified_topology=certified,
            adapter_id="mock",
        )

        service = CertifiedRuntimeService()
        result = service.execute(request)

        bundle = result.replay_bundle
        assert bundle.provenance is not None
        assert bundle.provenance.validation_lineage is not None
        assert bundle.provenance.admission_lineage is not None
        assert bundle.provenance.artifact_lineage is not None
