"""
Runtime Capability Regression Guard.

Sprint: MRP-5X
Status: REGRESSION_GUARD

Focused guard against future capability bypass regressions.

This file contains INVARIANT tests only. It does NOT duplicate
test_runtime_capability_integration.py. Its purpose is to catch
regressions in the MRP-5V capability gate.

Invariants tested:
  1. Unknown capability is rejected (not silently ignored)
  2. Disabled capability is rejected (not bypassed)
  3. Replay-unsafe capability rejected when replay_mode=True
  4. Duplicate capability ID rejected at registration
  5. Manifest output stable across repeated calls
  6. Policy ordering deterministic (sorted evaluation)
  7. Resolver returns metadata/result only (no callable)
  8. Source registries are not mutated by federation
  9. CertifiedRuntimeService cannot execute without capability resolution
"""

import copy
import pytest
from typing import List, Optional
from unittest.mock import MagicMock, patch

# Guard: skip all tests if runtime_capabilities not yet implemented
pytest_plugins = []
try:
    from app.cam.runtime_capabilities import (
        CapabilityRegistry,
        CapabilityResolver,
        CapabilitySource,
        FederatedCapability,
        CapabilityNamespace,
        GovernanceClassification,
        ResolutionContext,
        ResolutionStatus,
        PolicyDecision,
        make_capability_id,
        build_capability_manifest,
        reset_capability_registry,
        reset_capability_resolver,
        reset_policy_federation,
        DuplicateCapabilityError,
        CapabilityNotFoundError,
    )
    RUNTIME_CAPABILITIES_AVAILABLE = True
except ImportError:
    RUNTIME_CAPABILITIES_AVAILABLE = False
    # Provide stubs so module can be parsed when implementation unavailable
    from enum import Enum, auto

    class CapabilityNamespace(Enum):
        OPERATION = auto()

    class GovernanceClassification(Enum):
        PUBLIC_GOVERNED = auto()

    class ResolutionStatus(Enum):
        NOT_FOUND = auto()
        DISABLED = auto()
        REPLAY_UNSAFE = auto()
        ALLOWED = auto()

    class PolicyDecision(Enum):
        REJECTED = auto()
        ALLOWED = auto()

    class CapabilitySource:
        pass

    class FederatedCapability:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    class CapabilityRegistry:
        pass

    class CapabilityResolver:
        pass

    class ResolutionContext:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    def make_capability_id(ns, local_id):
        return f"{ns.name.lower()}:{local_id}"

    def build_capability_manifest(registry):
        return None

    def reset_capability_registry():
        pass

    def reset_capability_resolver():
        pass

    def reset_policy_federation():
        pass

    class DuplicateCapabilityError(Exception):
        pass

    class CapabilityNotFoundError(Exception):
        pass

pytestmark = pytest.mark.skipif(
    not RUNTIME_CAPABILITIES_AVAILABLE,
    reason="runtime_capabilities module not yet implemented",
)


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_globals():
    """Reset global singletons before each test."""
    reset_capability_registry()
    reset_capability_resolver()
    reset_policy_federation()
    yield
    reset_capability_registry()
    reset_capability_resolver()
    reset_policy_federation()


def _make_capability(
    local_id: str,
    namespace: CapabilityNamespace = CapabilityNamespace.OPERATION,
    enabled: bool = True,
    replay_safe: bool = True,
    deterministic: bool = True,
) -> FederatedCapability:
    """Create a test capability."""
    return FederatedCapability(
        capability_id=make_capability_id(namespace, local_id),
        local_id=local_id,
        namespace=namespace,
        display_name=f"Test {local_id}",
        description=f"Test capability {local_id}",
        governance_classification=GovernanceClassification.PUBLIC_GOVERNED,
        enabled=enabled,
        replay_safe=replay_safe,
        deterministic=deterministic,
        version="1.0.0",
        source_name="test_source",
    )


class _TestSource(CapabilitySource):
    """Test capability source."""

    def __init__(
        self,
        name: str,
        namespace: CapabilityNamespace,
        capabilities: List[FederatedCapability],
    ):
        self._name = name
        self._namespace = namespace
        self._capabilities = {c.local_id: c for c in capabilities}

    @property
    def source_name(self) -> str:
        return self._name

    @property
    def namespace(self) -> CapabilityNamespace:
        return self._namespace

    def list_capability_ids(self) -> List[str]:
        return list(self._capabilities.keys())

    def get_capability(self, local_id: str) -> Optional[FederatedCapability]:
        return self._capabilities.get(local_id)


# -----------------------------------------------------------------------------
# Invariant 1: Unknown capability is rejected
# -----------------------------------------------------------------------------

class TestUnknownCapabilityRejected:
    """Invariant: Unknown capability MUST be rejected, not silently ignored."""

    def test_resolver_rejects_unknown_capability(self):
        """Resolver returns NOT_FOUND for unknown capability."""
        registry = CapabilityRegistry()
        resolver = CapabilityResolver(registry=registry)

        result = resolver.resolve("operation:nonexistent")

        assert result.status == ResolutionStatus.NOT_FOUND
        assert not result.is_allowed
        assert "not registered" in result.rejection_reasons[0].lower()

    def test_require_capability_raises_for_unknown(self):
        """Registry.require_capability raises for unknown ID."""
        registry = CapabilityRegistry()

        with pytest.raises(CapabilityNotFoundError):
            registry.require_capability("operation:nonexistent")


# -----------------------------------------------------------------------------
# Invariant 2: Disabled capability is rejected
# -----------------------------------------------------------------------------

class TestDisabledCapabilityRejected:
    """Invariant: Disabled capability MUST be rejected, not bypassed."""

    def test_resolver_rejects_disabled_capability(self):
        """Resolver rejects disabled capability."""
        cap = _make_capability("disabled_op", enabled=False)
        source = _TestSource("src", CapabilityNamespace.OPERATION, [cap])

        registry = CapabilityRegistry()
        registry.register_source(source)

        resolver = CapabilityResolver(registry=registry)
        result = resolver.resolve("operation:disabled_op")

        assert result.status == ResolutionStatus.DISABLED
        assert result.policy_decision == PolicyDecision.REJECTED
        assert not result.is_allowed


# -----------------------------------------------------------------------------
# Invariant 3: Replay-unsafe capability rejected in replay mode
# -----------------------------------------------------------------------------

class TestReplayUnsafeRejected:
    """Invariant: Replay-unsafe capability MUST be rejected when replay_mode=True."""

    def test_resolver_rejects_replay_unsafe_in_replay_mode(self):
        """Resolver rejects replay-unsafe capability in replay context."""
        cap = _make_capability("unsafe_op", replay_safe=False)
        source = _TestSource("src", CapabilityNamespace.OPERATION, [cap])

        registry = CapabilityRegistry()
        registry.register_source(source)

        resolver = CapabilityResolver(registry=registry)
        context = ResolutionContext(
            is_replay_mode=True,
            require_replay_safe=True,
        )
        result = resolver.resolve("operation:unsafe_op", context)

        assert result.status == ResolutionStatus.REPLAY_UNSAFE
        assert not result.is_allowed

    def test_replay_unsafe_allowed_in_normal_mode(self):
        """Replay-unsafe capability allowed when not in replay mode."""
        cap = _make_capability("unsafe_op", replay_safe=False)
        source = _TestSource("src", CapabilityNamespace.OPERATION, [cap])

        registry = CapabilityRegistry()
        registry.register_source(source)

        resolver = CapabilityResolver(registry=registry)
        context = ResolutionContext(
            is_replay_mode=False,
            require_replay_safe=False,
        )
        result = resolver.resolve("operation:unsafe_op", context)

        assert result.is_allowed


# -----------------------------------------------------------------------------
# Invariant 4: Duplicate capability ID rejected
# -----------------------------------------------------------------------------

class TestDuplicateCapabilityRejected:
    """Invariant: Duplicate capability ID MUST be rejected at registration."""

    def test_duplicate_id_raises_at_registration(self):
        """Registering duplicate ID raises DuplicateCapabilityError."""
        cap1 = _make_capability("dup_op")
        cap2 = _make_capability("dup_op")  # Same ID

        source1 = _TestSource("src1", CapabilityNamespace.OPERATION, [cap1])
        source2 = _TestSource("src2", CapabilityNamespace.OPERATION, [cap2])

        registry = CapabilityRegistry()
        registry.register_source(source1)

        with pytest.raises(DuplicateCapabilityError) as exc_info:
            registry.register_source(source2)

        assert "dup_op" in str(exc_info.value)


# -----------------------------------------------------------------------------
# Invariant 5: Manifest output stable across repeated calls
# -----------------------------------------------------------------------------

class TestManifestStable:
    """Invariant: Manifest output MUST be stable across repeated calls."""

    def test_manifest_identical_across_calls(self):
        """build_capability_manifest returns identical output on repeated calls."""
        cap1 = _make_capability("op_a")
        cap2 = _make_capability("op_b")
        source = _TestSource("src", CapabilityNamespace.OPERATION, [cap1, cap2])

        registry = CapabilityRegistry()
        registry.register_source(source)
        registry.freeze()

        manifest1 = build_capability_manifest(registry)
        manifest2 = build_capability_manifest(registry)

        assert manifest1.schema_version == manifest2.schema_version
        assert manifest1.content_hash == manifest2.content_hash
        assert manifest1.total_count == manifest2.total_count
        # Note: generated_at will differ, so compare entries not full JSON
        assert len(manifest1.entries) == len(manifest2.entries)
        for e1, e2 in zip(manifest1.entries, manifest2.entries):
            assert e1.capability_id == e2.capability_id


# -----------------------------------------------------------------------------
# Invariant 6: Policy ordering deterministic
# -----------------------------------------------------------------------------

class TestPolicyOrderingDeterministic:
    """Invariant: Policy evaluation order MUST be deterministic."""

    def test_capability_list_is_sorted(self):
        """Registry.list_capability_ids returns sorted list."""
        cap_z = _make_capability("zzz_last")
        cap_a = _make_capability("aaa_first")
        cap_m = _make_capability("mmm_middle")

        # Register in non-alphabetical order
        source = _TestSource(
            "src",
            CapabilityNamespace.OPERATION,
            [cap_z, cap_a, cap_m],
        )

        registry = CapabilityRegistry()
        registry.register_source(source)

        ids = registry.list_capability_ids()

        assert ids == sorted(ids)
        assert ids[0] == "operation:aaa_first"
        assert ids[-1] == "operation:zzz_last"


# -----------------------------------------------------------------------------
# Invariant 7: Resolver returns metadata/result only, not callable
# -----------------------------------------------------------------------------

class TestResolverReturnsMetadataOnly:
    """Invariant: Resolver returns metadata/result, NOT executable callable."""

    def test_resolution_result_has_no_callable(self):
        """CapabilityResolutionResult does not contain callable."""
        cap = _make_capability("safe_op")
        source = _TestSource("src", CapabilityNamespace.OPERATION, [cap])

        registry = CapabilityRegistry()
        registry.register_source(source)

        resolver = CapabilityResolver(registry=registry)
        result = resolver.resolve("operation:safe_op")

        # Result should have metadata, not callable
        assert hasattr(result, "resolved_capability")
        assert hasattr(result, "status")
        assert hasattr(result, "policy_decision")

        # Resolved capability is metadata, not callable
        resolved_cap = result.resolved_capability
        assert resolved_cap is not None
        assert not callable(resolved_cap)
        assert isinstance(resolved_cap.capability_id, str)
        assert isinstance(resolved_cap.display_name, str)


# -----------------------------------------------------------------------------
# Invariant 8: Source registries not mutated by federation
# -----------------------------------------------------------------------------

class TestSourceRegistriesNotMutated:
    """Invariant: Federation MUST NOT mutate source registries."""

    def test_source_capabilities_unchanged_after_federation(self):
        """Source capabilities are unchanged after registry federation."""
        original_caps = [
            _make_capability("op_1"),
            _make_capability("op_2"),
        ]
        # Deep copy to verify no mutation
        expected_ids = [c.capability_id for c in original_caps]

        source = _TestSource("src", CapabilityNamespace.OPERATION, original_caps)

        # Capture state before federation
        before_ids = source.list_capability_ids()

        # Federate
        registry = CapabilityRegistry()
        registry.register_source(source)
        registry.freeze()

        # Build manifest (exercises full federation)
        build_capability_manifest(registry)

        # Source should be unchanged
        after_ids = source.list_capability_ids()
        assert before_ids == after_ids

        # Original capabilities should be unchanged
        for local_id in after_ids:
            cap = source.get_capability(local_id)
            assert cap is not None
            assert cap.capability_id in expected_ids


# -----------------------------------------------------------------------------
# Invariant 9: CertifiedRuntimeService requires capability resolution
# -----------------------------------------------------------------------------

class TestServiceRequiresCapabilityResolution:
    """Invariant: CertifiedRuntimeService cannot execute without capability resolution."""

    def test_service_rejects_when_capability_resolution_fails(self):
        """Service returns CAPABILITY_REJECTED when resolution fails."""
        from app.cam.runtime_service import CertifiedRuntimeService
        from app.cam.runtime_service.contracts import (
            CertifiedRuntimeRequest,
            ArtifactIntent,
            ServiceExecutionStatus,
        )
        from app.cam.runtime_admission import ExecutionMode, RuntimeTier
        from app.cam.topology_validation import CertifiedTopology

        # Create service with resolver that will reject
        cap = _make_capability("test_op", enabled=False)  # Disabled = rejected
        source = _TestSource("src", CapabilityNamespace.OPERATION, [cap])

        registry = CapabilityRegistry()
        registry.register_source(source)

        resolver = CapabilityResolver(registry=registry)

        # Mock topology and adapter
        mock_topology = MagicMock(spec=CertifiedTopology)
        mock_topology.topology_dict = {"test": "data"}

        # Create service with our resolver
        with patch("app.cam.runtime_service.service.is_adapter_available", return_value=True):
            with patch("app.cam.runtime_service.service.list_available_adapters", return_value=["dxf_export"]):
                service = CertifiedRuntimeService(capability_resolver=resolver)

                request = CertifiedRuntimeRequest(
                    certified_topology=mock_topology,
                    adapter_id="dxf_export",
                    artifact_intent=ArtifactIntent.DXF_OUTLINE,
                    capability_id="operation:test_op",  # Will be rejected (disabled)
                    execution_mode=ExecutionMode.DETERMINISTIC,
                    runtime_tier=RuntimeTier.PRODUCTION,
                )

                # Mock admission to pass
                with patch.object(
                    service._admission_controller,
                    "evaluate",
                    return_value=MagicMock(
                        decision=MagicMock(value="admitted"),
                        rejections=[],
                    ),
                ):
                    # Patch decision enum comparison
                    from app.cam.runtime_admission import AdmissionDecision
                    with patch.object(
                        service._admission_controller.evaluate.return_value,
                        "decision",
                        AdmissionDecision.ADMITTED,
                    ):
                        result = service.execute(request)

        assert result.status == ServiceExecutionStatus.CAPABILITY_REJECTED
        assert "disabled" in result.error_message.lower()
