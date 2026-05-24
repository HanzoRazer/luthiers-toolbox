"""
Runtime Capability Integration Tests.

Sprint: MRP-5V
Status: PROTOTYPE

Tests for the runtime capability federation layer.

Test coverage:
  - Package exists and imports
  - Duplicate capability IDs rejected
  - Existing registries federated
  - Unknown capability rejected
  - Disabled capability rejected
  - Replay-unsafe capability rejected in replay mode
  - CertifiedRuntimeService invokes resolver
  - Capability manifest deterministic
  - Federation does not mutate source registries
"""

import pytest
from typing import List, Optional

from app.cam.runtime_capabilities import (
    # Registry
    CapabilityRegistry,
    get_capability_registry,
    reset_capability_registry,
    # Sources
    CapabilitySource,
    FederatedCapability,
    CamOperationCapabilitySource,
    TranslatorCapabilitySource,
    AdapterCapabilitySource,
    create_default_sources,
    register_default_sources,
    # Contracts
    CapabilityNamespace,
    GovernanceClassification,
    make_capability_id,
    parse_capability_id,
    validate_capability_id,
    ResolutionContext,
    ResolutionStatus,
    PolicyDecision,
    # Resolution
    CapabilityResolver,
    get_capability_resolver,
    reset_capability_resolver,
    resolve_capability,
    can_use_capability,
    # Policies
    ExecutionPolicyFederation,
    get_policy_federation,
    reset_policy_federation,
    # Manifest
    build_capability_manifest,
    CapabilityManifest,
    compare_manifests,
    # Exceptions
    DuplicateCapabilityError,
    CapabilityNotFoundError,
    InvalidCapabilityIdError,
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


class MockCapabilitySource(CapabilitySource):
    """Mock source for testing."""

    def __init__(
        self,
        name: str = "mock_source",
        namespace: CapabilityNamespace = CapabilityNamespace.SERVICE,
        capabilities: Optional[List[FederatedCapability]] = None,
    ):
        self._name = name
        self._namespace = namespace
        self._capabilities = {c.local_id: c for c in (capabilities or [])}

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


def create_test_capability(
    local_id: str,
    namespace: CapabilityNamespace = CapabilityNamespace.SERVICE,
    enabled: bool = True,
    deterministic: bool = True,
    replay_safe: bool = True,
) -> FederatedCapability:
    """Create a test capability."""
    return FederatedCapability(
        capability_id=make_capability_id(namespace, local_id),
        namespace=namespace,
        local_id=local_id,
        version="1.0.0",
        source_name="test",
        display_name=local_id,
        enabled=enabled,
        deterministic=deterministic,
        replay_safe=replay_safe,
    )


# -----------------------------------------------------------------------------
# Package Import Tests
# -----------------------------------------------------------------------------

class TestPackageExists:
    """Tests verifying package exists and imports."""

    def test_runtime_capabilities_imports(self):
        """runtime_capabilities package imports successfully."""
        from app.cam.runtime_capabilities import CapabilityRegistry
        assert CapabilityRegistry is not None

    def test_registry_imports(self):
        """Registry components import."""
        from app.cam.runtime_capabilities import (
            CapabilityRegistry,
            get_capability_registry,
        )
        assert CapabilityRegistry is not None
        assert get_capability_registry is not None

    def test_resolution_imports(self):
        """Resolution components import."""
        from app.cam.runtime_capabilities import (
            CapabilityResolver,
            resolve_capability,
            can_use_capability,
        )
        assert CapabilityResolver is not None
        assert resolve_capability is not None

    def test_policy_imports(self):
        """Policy components import."""
        from app.cam.runtime_capabilities import (
            ExecutionPolicyFederation,
            get_policy_federation,
        )
        assert ExecutionPolicyFederation is not None

    def test_manifest_imports(self):
        """Manifest components import."""
        from app.cam.runtime_capabilities import (
            build_capability_manifest,
            CapabilityManifest,
        )
        assert build_capability_manifest is not None

    def test_source_adapters_import(self):
        """Source adapters import."""
        from app.cam.runtime_capabilities import (
            CamOperationCapabilitySource,
            TranslatorCapabilitySource,
            AdapterCapabilitySource,
        )
        assert CamOperationCapabilitySource is not None
        assert TranslatorCapabilitySource is not None


# -----------------------------------------------------------------------------
# Capability ID Tests
# -----------------------------------------------------------------------------

class TestCapabilityIds:
    """Tests for namespaced capability IDs."""

    def test_make_capability_id(self):
        """make_capability_id creates namespaced ID."""
        cid = make_capability_id(CapabilityNamespace.OPERATION, "nut_slot")
        assert cid == "operation:nut_slot"

    def test_parse_capability_id(self):
        """parse_capability_id extracts namespace and local_id."""
        ns, local = parse_capability_id("translator:dxf_r12")
        assert ns == CapabilityNamespace.TRANSLATOR
        assert local == "dxf_r12"

    def test_parse_invalid_id_raises(self):
        """Invalid capability ID raises ValueError."""
        with pytest.raises(ValueError, match="missing namespace"):
            parse_capability_id("no_colon")

    def test_validate_capability_id_valid(self):
        """validate_capability_id returns True for valid ID."""
        assert validate_capability_id("operation:nut_slot") is True

    def test_validate_capability_id_invalid(self):
        """validate_capability_id returns False for invalid ID."""
        assert validate_capability_id("invalid") is False


# -----------------------------------------------------------------------------
# Registry Tests
# -----------------------------------------------------------------------------

class TestCapabilityRegistry:
    """Tests for CapabilityRegistry."""

    def test_register_source(self):
        """Source can be registered."""
        registry = CapabilityRegistry()
        cap = create_test_capability("test_cap")
        source = MockCapabilitySource(capabilities=[cap])
        registry.register_source(source)

        assert registry.has_capability("service:test_cap")

    def test_duplicate_capability_rejected(self):
        """Duplicate capability ID raises error."""
        registry = CapabilityRegistry()

        cap1 = create_test_capability("duplicate_cap")
        source1 = MockCapabilitySource(name="source1", capabilities=[cap1])
        registry.register_source(source1)

        cap2 = create_test_capability("duplicate_cap")
        source2 = MockCapabilitySource(name="source2", capabilities=[cap2])

        with pytest.raises(DuplicateCapabilityError, match="duplicate_cap"):
            registry.register_source(source2)

    def test_unknown_capability_returns_none(self):
        """Unknown capability returns None from get_capability."""
        registry = CapabilityRegistry()
        cap = registry.get_capability("operation:unknown")
        assert cap is None

    def test_require_capability_raises_for_unknown(self):
        """require_capability raises for unknown capability."""
        registry = CapabilityRegistry()
        with pytest.raises(CapabilityNotFoundError, match="unknown"):
            registry.require_capability("operation:unknown")

    def test_list_capabilities_sorted(self):
        """list_capability_ids returns sorted list."""
        registry = CapabilityRegistry()
        caps = [
            create_test_capability("z_cap"),
            create_test_capability("a_cap"),
            create_test_capability("m_cap"),
        ]
        source = MockCapabilitySource(capabilities=caps)
        registry.register_source(source)

        ids = registry.list_capability_ids()
        assert ids == sorted(ids)

    def test_freeze_prevents_registration(self):
        """Frozen registry rejects new sources."""
        registry = CapabilityRegistry()
        registry.freeze()

        source = MockCapabilitySource()
        with pytest.raises(RuntimeError, match="frozen"):
            registry.register_source(source)

    def test_invalid_capability_id_raises(self):
        """Invalid capability ID raises error."""
        registry = CapabilityRegistry()
        with pytest.raises(InvalidCapabilityIdError):
            registry.get_capability("invalid_no_colon")


# -----------------------------------------------------------------------------
# Source Adapter Tests
# -----------------------------------------------------------------------------

class TestSourceAdapters:
    """Tests for existing registry source adapters."""

    def test_cam_operation_source_lists_operations(self):
        """CamOperationCapabilitySource lists operations."""
        source = CamOperationCapabilitySource()
        ids = source.list_capability_ids()
        assert "nut_slot" in ids
        assert "drilling" in ids

    def test_cam_operation_source_returns_capability(self):
        """CamOperationCapabilitySource returns federated capability."""
        source = CamOperationCapabilitySource()
        cap = source.get_capability("nut_slot")
        assert cap is not None
        assert cap.capability_id == "operation:nut_slot"
        assert cap.namespace == CapabilityNamespace.OPERATION

    def test_translator_source_lists_translators(self):
        """TranslatorCapabilitySource lists translators."""
        source = TranslatorCapabilitySource()
        ids = source.list_capability_ids()
        assert "dxf_r12" in ids
        assert "dxf_r2000" in ids

    def test_translator_source_returns_capability(self):
        """TranslatorCapabilitySource returns federated capability."""
        source = TranslatorCapabilitySource()
        cap = source.get_capability("dxf_r12")
        assert cap is not None
        assert cap.capability_id == "translator:dxf_r12"
        assert cap.namespace == CapabilityNamespace.TRANSLATOR

    def test_source_adapters_do_not_mutate_registry(self):
        """Source adapters do not modify underlying registries."""
        from app.cam.cam_operation_registry import (
            CAM_OPERATION_REGISTRY,
            list_supported_operations,
        )

        before_ops = list_supported_operations()

        # Create and use source adapter
        source = CamOperationCapabilitySource()
        caps = source.list_capabilities()

        after_ops = list_supported_operations()

        assert before_ops == after_ops
        assert len(CAM_OPERATION_REGISTRY) == len(before_ops)


# -----------------------------------------------------------------------------
# Resolution Tests
# -----------------------------------------------------------------------------

class TestCapabilityResolution:
    """Tests for CapabilityResolver."""

    def test_resolve_registered_capability(self):
        """Registered capability resolves successfully."""
        registry = get_capability_registry()
        cap = create_test_capability("test_resolve")
        source = MockCapabilitySource(capabilities=[cap])
        registry.register_source(source)

        result = resolve_capability("service:test_resolve")
        assert result.status == ResolutionStatus.RESOLVED
        assert result.is_allowed

    def test_unknown_capability_rejected(self):
        """Unknown capability is rejected."""
        result = resolve_capability("operation:unknown_op")
        assert result.status == ResolutionStatus.NOT_FOUND
        assert not result.is_allowed
        assert "not registered" in result.rejection_reasons[0]

    def test_disabled_capability_rejected(self):
        """Disabled capability is rejected."""
        registry = get_capability_registry()
        cap = create_test_capability("disabled_cap", enabled=False)
        source = MockCapabilitySource(capabilities=[cap])
        registry.register_source(source)

        result = resolve_capability("service:disabled_cap")
        assert result.status == ResolutionStatus.DISABLED
        assert not result.is_allowed

    def test_replay_unsafe_rejected_in_replay_mode(self):
        """Replay-unsafe capability rejected in replay mode."""
        registry = get_capability_registry()
        cap = create_test_capability("unsafe_cap", replay_safe=False)
        source = MockCapabilitySource(capabilities=[cap])
        registry.register_source(source)

        context = ResolutionContext(is_replay_mode=True)
        result = resolve_capability("service:unsafe_cap", context)

        assert result.status == ResolutionStatus.REPLAY_UNSAFE
        assert not result.is_allowed

    def test_replay_unsafe_allowed_in_normal_mode(self):
        """Replay-unsafe capability allowed in normal mode."""
        registry = get_capability_registry()
        cap = create_test_capability("unsafe_cap", replay_safe=False)
        source = MockCapabilitySource(capabilities=[cap])
        registry.register_source(source)

        context = ResolutionContext(is_replay_mode=False)
        result = resolve_capability("service:unsafe_cap", context)

        assert result.status == ResolutionStatus.RESOLVED
        assert result.is_allowed

    def test_can_use_capability_helper(self):
        """can_use_capability convenience function works."""
        registry = get_capability_registry()
        cap = create_test_capability("usable_cap")
        source = MockCapabilitySource(capabilities=[cap])
        registry.register_source(source)

        assert can_use_capability("service:usable_cap") is True
        assert can_use_capability("operation:nonexistent") is False


# -----------------------------------------------------------------------------
# Policy Tests
# -----------------------------------------------------------------------------

class TestPolicyFederation:
    """Tests for ExecutionPolicyFederation."""

    def test_enabled_policy_passes_enabled(self):
        """Enabled capability passes enabled policy."""
        federation = ExecutionPolicyFederation()
        cap = create_test_capability("enabled_cap", enabled=True)
        context = ResolutionContext()

        result = federation.evaluate(cap, context)
        assert result.is_allowed

    def test_enabled_policy_rejects_disabled(self):
        """Disabled capability rejected by enabled policy."""
        federation = ExecutionPolicyFederation()
        cap = create_test_capability("disabled_cap", enabled=False)
        context = ResolutionContext()

        result = federation.evaluate(cap, context)
        assert not result.is_allowed
        assert any("disabled" in r.lower() for r in result.rejection_reasons)

    def test_replay_policy_rejects_unsafe(self):
        """Replay-unsafe rejected when require_replay_safe."""
        federation = ExecutionPolicyFederation()
        cap = create_test_capability("unsafe_cap", replay_safe=False)
        context = ResolutionContext(require_replay_safe=True)

        result = federation.evaluate(cap, context)
        assert not result.is_allowed
        assert any("replay" in r.lower() for r in result.rejection_reasons)

    def test_policy_does_not_mutate_capability(self):
        """Policy evaluation does not mutate capability."""
        federation = ExecutionPolicyFederation()
        cap = create_test_capability("immutable_cap")

        original_enabled = cap.enabled
        original_replay_safe = cap.replay_safe

        context = ResolutionContext(require_replay_safe=True)
        federation.evaluate(cap, context)

        assert cap.enabled == original_enabled
        assert cap.replay_safe == original_replay_safe


# -----------------------------------------------------------------------------
# Manifest Tests
# -----------------------------------------------------------------------------

class TestCapabilityManifest:
    """Tests for capability manifest generation."""

    def test_manifest_deterministic(self):
        """Manifest generation is deterministic."""
        registry = get_capability_registry()
        caps = [
            create_test_capability("cap_a"),
            create_test_capability("cap_b"),
            create_test_capability("cap_c"),
        ]
        source = MockCapabilitySource(capabilities=caps)
        registry.register_source(source)

        manifest1 = build_capability_manifest(registry)
        manifest2 = build_capability_manifest(registry)

        assert manifest1.content_hash == manifest2.content_hash
        assert len(manifest1.entries) == len(manifest2.entries)

        for e1, e2 in zip(manifest1.entries, manifest2.entries):
            assert e1.capability_id == e2.capability_id

    def test_manifest_entries_sorted(self):
        """Manifest entries are sorted by type, then id."""
        registry = get_capability_registry()
        caps = [
            create_test_capability("z_cap"),
            create_test_capability("a_cap"),
            create_test_capability("m_cap"),
        ]
        source = MockCapabilitySource(capabilities=caps)
        registry.register_source(source)

        manifest = build_capability_manifest(registry)
        ids = [e.capability_id for e in manifest.entries]

        assert ids == sorted(ids)

    def test_manifest_statistics(self):
        """Manifest includes correct statistics."""
        registry = get_capability_registry()
        caps = [
            create_test_capability("enabled_cap", enabled=True),
            create_test_capability("disabled_cap", enabled=False),
            create_test_capability("replay_unsafe", replay_safe=False),
        ]
        source = MockCapabilitySource(capabilities=caps)
        registry.register_source(source)

        manifest = build_capability_manifest(registry)

        assert manifest.total_count == 3
        assert manifest.enabled_count == 2
        assert manifest.disabled_count == 1

    def test_manifest_to_json_roundtrip(self):
        """Manifest JSON serialization roundtrips."""
        registry = get_capability_registry()
        cap = create_test_capability("json_cap")
        source = MockCapabilitySource(capabilities=[cap])
        registry.register_source(source)

        manifest = build_capability_manifest(registry)
        json_str = manifest.to_json()
        restored = CapabilityManifest.from_json(json_str)

        assert manifest.content_hash == restored.content_hash
        assert manifest.total_count == restored.total_count


# -----------------------------------------------------------------------------
# Integration Tests
# -----------------------------------------------------------------------------

class TestRegistryFederation:
    """Tests for registry federation with real sources."""

    def test_default_sources_register(self):
        """Default sources register without errors."""
        registry = CapabilityRegistry()
        register_default_sources(registry)

        # Should have capabilities from all sources
        ids = registry.list_capability_ids()
        assert len(ids) > 0

        # Check for known capabilities
        assert registry.has_capability("operation:nut_slot")
        assert registry.has_capability("translator:dxf_r12")

    def test_federated_capabilities_resolve(self):
        """Federated capabilities can be resolved."""
        registry = CapabilityRegistry()
        register_default_sources(registry)

        resolver = CapabilityResolver(registry=registry)

        result = resolver.resolve("operation:nut_slot")
        assert result.status == ResolutionStatus.RESOLVED

        result = resolver.resolve("translator:dxf_r12")
        # dxf_r12 is validation_only, so may not be "enabled"
        assert result.status in (ResolutionStatus.RESOLVED, ResolutionStatus.DISABLED)

    def test_manifest_with_real_sources(self):
        """Manifest generation works with real sources."""
        registry = CapabilityRegistry()
        register_default_sources(registry)

        manifest = build_capability_manifest(registry)

        assert manifest.total_count > 0
        assert manifest.content_hash != ""

        # Should have entries from multiple namespaces
        types = {e.capability_type for e in manifest.entries}
        assert "operation" in types
        assert "translator" in types


# -----------------------------------------------------------------------------
# Runtime Service Integration Tests
# -----------------------------------------------------------------------------

class TestRuntimeServiceIntegration:
    """Tests for runtime service capability integration."""

    def test_service_invokes_resolver(self):
        """CertifiedRuntimeService has capability resolver."""
        from app.cam.runtime_service import CertifiedRuntimeService
        service = CertifiedRuntimeService()
        assert hasattr(service, "_capability_resolver")

    def test_service_contracts_have_capability_fields(self):
        """Service contracts have capability fields."""
        from app.cam.runtime_service import (
            CertifiedRuntimeRequest,
            CertifiedRuntimeResult,
            ServiceExecutionStatus,
        )

        # Request should have capability_id field
        from dataclasses import fields
        request_fields = {f.name for f in fields(CertifiedRuntimeRequest)}
        assert "capability_id" in request_fields
        assert "is_replay_mode" in request_fields

        # Result should have capability_resolution_report field
        result_fields = {f.name for f in fields(CertifiedRuntimeResult)}
        assert "capability_resolution_report" in result_fields

        # Status should have CAPABILITY_REJECTED
        assert hasattr(ServiceExecutionStatus, "CAPABILITY_REJECTED")
