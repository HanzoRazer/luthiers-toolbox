"""
Tests for Runtime Spine Contracts and Manifest.

Sprint: MRP-5T
Tests: versioning, contracts, compatibility, manifest building
"""

import json
import pytest

from app.cam.runtime_manifest import (
    # Contracts
    ContractClassification,
    CompatibilityLevel,
    RuntimeContractEntry,
    RuntimeVersionInfo,
    RuntimeSpineManifest,
    RuntimeCompatibilityReport,
    # Versioning
    RUNTIME_SPINE_VERSION,
    REPLAY_BUNDLE_SCHEMA_VERSION,
    MANIFEST_SCHEMA_VERSION,
    CONTRACT_FREEZE_DATE,
    CONTRACT_FREEZE_SPRINT,
    parse_version,
    is_compatible,
    get_version_info,
    # Manifest
    RuntimeSpineManifestBuilder,
    build_runtime_spine_manifest,
    manifest_to_json,
    manifest_from_json,
    compute_manifest_hash,
    # Compatibility
    ContractDiff,
    compare_contracts,
    compare_manifests,
    assert_compatible,
    check_contract_stability,
    # Exceptions
    RuntimeManifestError,
    VersionMismatchError,
    ContractBreakError,
    ManifestBuildError,
    ContractNotFoundError,
    InvalidContractError,
)


class TestVersioning:
    """Tests for versioning module."""

    def test_version_constants_exist(self):
        """Version constants should be defined."""
        assert RUNTIME_SPINE_VERSION is not None
        assert REPLAY_BUNDLE_SCHEMA_VERSION is not None
        assert MANIFEST_SCHEMA_VERSION is not None
        assert CONTRACT_FREEZE_DATE is not None
        assert CONTRACT_FREEZE_SPRINT is not None

    def test_parse_version_simple(self):
        """parse_version should handle simple versions."""
        assert parse_version("0.1.0") == (0, 1, 0)
        assert parse_version("1.0.0") == (1, 0, 0)
        assert parse_version("2.3.4") == (2, 3, 4)

    def test_parse_version_two_parts(self):
        """parse_version should handle two-part versions."""
        assert parse_version("1.0") == (1, 0)

    def test_is_compatible_same_version(self):
        """Same version should be compatible."""
        assert is_compatible("0.1.0", "0.1.0") is True

    def test_is_compatible_higher_minor(self):
        """Higher minor version should be compatible."""
        assert is_compatible("0.2.0", "0.1.0") is True
        assert is_compatible("1.5.0", "1.3.0") is True

    def test_is_compatible_lower_minor_incompatible(self):
        """Lower minor version should be incompatible."""
        assert is_compatible("0.1.0", "0.2.0") is False

    def test_is_compatible_different_major_incompatible(self):
        """Different major version should be incompatible."""
        assert is_compatible("1.0.0", "0.1.0") is False
        assert is_compatible("0.1.0", "1.0.0") is False

    def test_get_version_info(self):
        """get_version_info should return all version fields."""
        info = get_version_info()
        assert "runtime_spine_version" in info
        assert "replay_bundle_schema_version" in info
        assert "manifest_schema_version" in info
        assert "contract_freeze_date" in info
        assert "contract_freeze_sprint" in info


class TestContractEnums:
    """Tests for contract enums."""

    def test_contract_classification_values(self):
        """ContractClassification should have expected values."""
        assert ContractClassification.PUBLIC_GOVERNED.value == "PUBLIC_GOVERNED"
        assert ContractClassification.DEVELOPER_EXPERIMENTAL.value == "DEVELOPER_EXPERIMENTAL"
        assert ContractClassification.INTERNAL_ONLY.value == "INTERNAL_ONLY"

    def test_compatibility_level_values(self):
        """CompatibilityLevel should have expected values."""
        assert CompatibilityLevel.COMPATIBLE.value == "COMPATIBLE"
        assert CompatibilityLevel.MINOR_BREAK.value == "MINOR_BREAK"
        assert CompatibilityLevel.MAJOR_BREAK.value == "MAJOR_BREAK"


class TestRuntimeContractEntry:
    """Tests for RuntimeContractEntry."""

    def test_create_entry(self):
        """Should create contract entry with defaults."""
        entry = RuntimeContractEntry(
            contract_name="TestContract",
            module_path="app.cam.test",
            classification=ContractClassification.PUBLIC_GOVERNED,
        )
        assert entry.contract_name == "TestContract"
        assert entry.module_path == "app.cam.test"
        assert entry.classification == ContractClassification.PUBLIC_GOVERNED
        assert entry.version == RUNTIME_SPINE_VERSION
        assert entry.compatibility_level == CompatibilityLevel.COMPATIBLE
        assert entry.deprecated is False
        assert entry.deterministic is True
        assert entry.replay_safe is True

    def test_entry_to_dict(self):
        """Should serialize to dict."""
        entry = RuntimeContractEntry(
            contract_name="TestContract",
            module_path="app.cam.test",
            classification=ContractClassification.PUBLIC_GOVERNED,
            description="Test description",
        )
        d = entry.to_dict()
        assert d["contract_name"] == "TestContract"
        assert d["module_path"] == "app.cam.test"
        assert d["classification"] == "PUBLIC_GOVERNED"
        assert d["description"] == "Test description"


class TestRuntimeVersionInfo:
    """Tests for RuntimeVersionInfo."""

    def test_create_version_info(self):
        """Should create version info with defaults."""
        info = RuntimeVersionInfo()
        assert info.spine_version == RUNTIME_SPINE_VERSION
        assert info.replay_schema_version == REPLAY_BUNDLE_SCHEMA_VERSION
        assert info.manifest_schema_version == MANIFEST_SCHEMA_VERSION
        assert info.freeze_date == CONTRACT_FREEZE_DATE

    def test_version_info_to_dict(self):
        """Should serialize to dict."""
        info = RuntimeVersionInfo()
        d = info.to_dict()
        assert "spine_version" in d
        assert "replay_schema_version" in d
        assert "manifest_schema_version" in d
        assert "freeze_date" in d


class TestRuntimeSpineManifestBuilder:
    """Tests for RuntimeSpineManifestBuilder."""

    def test_build_empty_fails(self):
        """Building with no contracts should fail."""
        builder = RuntimeSpineManifestBuilder()
        with pytest.raises(ManifestBuildError):
            builder.build()

    def test_add_governed_contract(self):
        """Should add governed contract."""
        builder = RuntimeSpineManifestBuilder()
        builder.add_governed_contract(
            contract_name="TestContract",
            module_path="app.cam.test",
        )
        manifest = builder.build()
        assert len(manifest.governed_contracts) == 1
        assert manifest.governed_contracts[0].contract_name == "TestContract"
        assert manifest.governed_contracts[0].classification == ContractClassification.PUBLIC_GOVERNED

    def test_add_developer_api(self):
        """Should add developer API."""
        builder = RuntimeSpineManifestBuilder()
        builder.add_developer_api(
            contract_name="test_function",
            module_path="app.cam.test",
        )
        manifest = builder.build()
        assert len(manifest.developer_apis) == 1
        assert manifest.developer_apis[0].classification == ContractClassification.DEVELOPER_EXPERIMENTAL

    def test_add_internal_contract(self):
        """Should add internal contract."""
        builder = RuntimeSpineManifestBuilder()
        builder.add_internal_contract(
            contract_name="InternalHelper",
            module_path="app.cam.test",
        )
        manifest = builder.build()
        assert len(manifest.internal_contracts) == 1
        assert manifest.internal_contracts[0].classification == ContractClassification.INTERNAL_ONLY

    def test_duplicate_name_rejected(self):
        """Duplicate contract names should be rejected."""
        builder = RuntimeSpineManifestBuilder()
        builder.add_governed_contract("TestContract", "app.cam.test")
        with pytest.raises(InvalidContractError):
            builder.add_developer_api("TestContract", "app.cam.other")

    def test_empty_module_path_rejected(self):
        """Empty module path should be rejected."""
        builder = RuntimeSpineManifestBuilder()
        with pytest.raises(InvalidContractError):
            builder.add_governed_contract("TestContract", "")

    def test_fluent_interface(self):
        """Builder should support fluent interface."""
        manifest = (
            RuntimeSpineManifestBuilder()
            .add_governed_contract("Contract1", "app.cam.a")
            .add_developer_api("api_func", "app.cam.b")
            .add_internal_contract("Internal1", "app.cam.c")
            .build()
        )
        assert manifest.total_contracts == 3

    def test_clear_builder(self):
        """clear() should remove all contracts."""
        builder = RuntimeSpineManifestBuilder()
        builder.add_governed_contract("Test", "app.cam.test")
        builder.clear()
        with pytest.raises(ManifestBuildError):
            builder.build()


class TestRuntimeSpineManifest:
    """Tests for RuntimeSpineManifest."""

    def test_total_contracts(self):
        """total_contracts should sum all lists."""
        manifest = (
            RuntimeSpineManifestBuilder()
            .add_governed_contract("C1", "app.a")
            .add_governed_contract("C2", "app.b")
            .add_developer_api("api1", "app.c")
            .add_internal_contract("I1", "app.d")
            .build()
        )
        assert manifest.total_contracts == 4

    def test_compatibility_status_stable(self):
        """Should be STABLE_PROTOTYPE when no deprecations."""
        manifest = (
            RuntimeSpineManifestBuilder()
            .add_governed_contract("C1", "app.a")
            .build()
        )
        assert manifest.compatibility_status == "STABLE_PROTOTYPE"

    def test_compatibility_status_with_deprecation(self):
        """Should be DEPRECATIONS_PENDING with deprecated contract."""
        builder = RuntimeSpineManifestBuilder()
        builder.add_governed_contract(
            "DeprecatedContract",
            "app.old",
            deprecated=True,
            deprecation_note="Use NewContract instead",
        )
        manifest = builder.build()
        assert manifest.compatibility_status == "DEPRECATIONS_PENDING"

    def test_manifest_to_dict(self):
        """Should serialize manifest to dict."""
        manifest = (
            RuntimeSpineManifestBuilder()
            .add_governed_contract("C1", "app.a", description="Contract 1")
            .build()
        )
        d = manifest.to_dict()
        assert "version_info" in d
        assert "governed_contracts" in d
        assert "developer_apis" in d
        assert "internal_contracts" in d
        assert "total_contracts" in d
        assert "compatibility_status" in d
        assert "generated_at" in d
        assert "generator_sprint" in d


class TestManifestSerialization:
    """Tests for manifest JSON serialization."""

    def test_manifest_to_json(self):
        """Should serialize to JSON string."""
        manifest = (
            RuntimeSpineManifestBuilder()
            .add_governed_contract("C1", "app.a")
            .build()
        )
        json_str = manifest_to_json(manifest)
        assert isinstance(json_str, str)
        parsed = json.loads(json_str)
        assert parsed["total_contracts"] == 1

    def test_manifest_roundtrip(self):
        """Should roundtrip through JSON."""
        original = (
            RuntimeSpineManifestBuilder()
            .add_governed_contract("Contract1", "app.cam.a", description="Test")
            .add_developer_api("api_func", "app.cam.b")
            .add_internal_contract("Internal1", "app.cam.c")
            .build()
        )
        json_str = manifest_to_json(original)
        restored = manifest_from_json(json_str)

        assert restored.total_contracts == original.total_contracts
        assert len(restored.governed_contracts) == len(original.governed_contracts)
        assert restored.governed_contracts[0].contract_name == "Contract1"
        assert restored.version_info.spine_version == original.version_info.spine_version

    def test_compute_manifest_hash_deterministic(self):
        """Hash should be deterministic for same content."""
        manifest1 = (
            RuntimeSpineManifestBuilder()
            .add_governed_contract("C1", "app.a")
            .build()
        )
        manifest2 = (
            RuntimeSpineManifestBuilder()
            .add_governed_contract("C1", "app.a")
            .build()
        )
        assert compute_manifest_hash(manifest1) == compute_manifest_hash(manifest2)

    def test_compute_manifest_hash_different_content(self):
        """Hash should differ for different content."""
        manifest1 = (
            RuntimeSpineManifestBuilder()
            .add_governed_contract("C1", "app.a")
            .build()
        )
        manifest2 = (
            RuntimeSpineManifestBuilder()
            .add_governed_contract("C2", "app.b")
            .build()
        )
        assert compute_manifest_hash(manifest1) != compute_manifest_hash(manifest2)


class TestContractComparison:
    """Tests for contract comparison."""

    def test_compare_unchanged_contracts(self):
        """Identical contracts should be UNCHANGED."""
        c1 = RuntimeContractEntry(
            contract_name="Test",
            module_path="app.cam.test",
            classification=ContractClassification.PUBLIC_GOVERNED,
        )
        c2 = RuntimeContractEntry(
            contract_name="Test",
            module_path="app.cam.test",
            classification=ContractClassification.PUBLIC_GOVERNED,
        )
        diff = compare_contracts(c1, c2)
        assert diff.change_type == "UNCHANGED"
        assert diff.breaking is False

    def test_compare_deprecated_contract(self):
        """Deprecation should be detected."""
        c1 = RuntimeContractEntry(
            contract_name="Test",
            module_path="app.cam.test",
            classification=ContractClassification.PUBLIC_GOVERNED,
        )
        c2 = RuntimeContractEntry(
            contract_name="Test",
            module_path="app.cam.test",
            classification=ContractClassification.PUBLIC_GOVERNED,
            deprecated=True,
            deprecation_note="Use other",
        )
        diff = compare_contracts(c1, c2)
        assert diff.change_type == "MODIFIED"
        assert "deprecated" in diff.details.lower()

    def test_compare_lost_determinism_breaking(self):
        """Lost determinism should be breaking."""
        c1 = RuntimeContractEntry(
            contract_name="Test",
            module_path="app.cam.test",
            classification=ContractClassification.PUBLIC_GOVERNED,
            deterministic=True,
        )
        c2 = RuntimeContractEntry(
            contract_name="Test",
            module_path="app.cam.test",
            classification=ContractClassification.PUBLIC_GOVERNED,
            deterministic=False,
        )
        diff = compare_contracts(c1, c2)
        assert diff.breaking is True
        assert "determinism" in diff.details.lower()

    def test_compare_classification_downgrade_breaking(self):
        """Downgrade from PUBLIC_GOVERNED should be breaking."""
        c1 = RuntimeContractEntry(
            contract_name="Test",
            module_path="app.cam.test",
            classification=ContractClassification.PUBLIC_GOVERNED,
        )
        c2 = RuntimeContractEntry(
            contract_name="Test",
            module_path="app.cam.test",
            classification=ContractClassification.INTERNAL_ONLY,
        )
        diff = compare_contracts(c1, c2)
        assert diff.breaking is True


class TestManifestComparison:
    """Tests for manifest comparison."""

    def test_compare_identical_manifests(self):
        """Identical manifests should be compatible."""
        manifest = (
            RuntimeSpineManifestBuilder()
            .add_governed_contract("C1", "app.a")
            .build()
        )
        report = compare_manifests(manifest, manifest)
        assert report.compatible is True
        assert report.overall_level == CompatibilityLevel.COMPATIBLE
        assert len(report.breaking_changes) == 0

    def test_compare_manifest_with_additions(self):
        """Additions should be compatible."""
        m1 = (
            RuntimeSpineManifestBuilder()
            .add_governed_contract("C1", "app.a")
            .build()
        )
        m2 = (
            RuntimeSpineManifestBuilder()
            .add_governed_contract("C1", "app.a")
            .add_governed_contract("C2", "app.b")
            .build()
        )
        report = compare_manifests(m1, m2)
        assert report.compatible is True
        assert "C2" in report.additions

    def test_compare_manifest_with_removal_breaking(self):
        """Removing governed contract should be breaking."""
        m1 = (
            RuntimeSpineManifestBuilder()
            .add_governed_contract("C1", "app.a")
            .add_governed_contract("C2", "app.b")
            .build()
        )
        m2 = (
            RuntimeSpineManifestBuilder()
            .add_governed_contract("C1", "app.a")
            .build()
        )
        report = compare_manifests(m1, m2)
        assert report.compatible is False
        assert report.overall_level == CompatibilityLevel.MAJOR_BREAK
        assert any("C2" in bc for bc in report.breaking_changes)


class TestAssertCompatible:
    """Tests for assert_compatible helper."""

    def test_assert_compatible_passes(self):
        """Should pass for compatible versions."""
        assert assert_compatible("0.1.0", "0.1.0") is True

    def test_assert_compatible_raises(self):
        """Should raise for incompatible versions."""
        with pytest.raises(VersionMismatchError) as exc_info:
            assert_compatible("0.1.0", "1.0.0")
        assert exc_info.value.current == "0.1.0"
        assert exc_info.value.required == "1.0.0"

    def test_assert_compatible_no_raise(self):
        """Should return False when raise_on_incompatible=False."""
        result = assert_compatible("0.1.0", "1.0.0", raise_on_incompatible=False)
        assert result is False


class TestCheckContractStability:
    """Tests for check_contract_stability."""

    def test_stable_contract(self):
        """Stable contract should have no violations."""
        contract = RuntimeContractEntry(
            contract_name="Stable",
            module_path="app.cam.test",
            classification=ContractClassification.PUBLIC_GOVERNED,
            deterministic=True,
            replay_safe=True,
        )
        violations = check_contract_stability(contract)
        assert len(violations) == 0

    def test_non_deterministic_violation(self):
        """Non-deterministic contract should have violation."""
        contract = RuntimeContractEntry(
            contract_name="NonDet",
            module_path="app.cam.test",
            classification=ContractClassification.PUBLIC_GOVERNED,
            deterministic=False,
        )
        violations = check_contract_stability(contract)
        assert len(violations) == 1
        assert "deterministic" in violations[0]

    def test_deprecated_violation(self):
        """Deprecated contract should have violation."""
        contract = RuntimeContractEntry(
            contract_name="Old",
            module_path="app.cam.test",
            classification=ContractClassification.PUBLIC_GOVERNED,
            deprecated=True,
            deprecation_note="Use New instead",
        )
        violations = check_contract_stability(contract)
        assert any("deprecated" in v for v in violations)


class TestBuildRuntimeSpineManifest:
    """Tests for build_runtime_spine_manifest."""

    def test_builds_complete_manifest(self):
        """Should build manifest with all spine contracts."""
        manifest = build_runtime_spine_manifest()

        assert manifest.total_contracts > 0
        assert len(manifest.governed_contracts) > 0
        assert len(manifest.developer_apis) > 0

        # Check for key contracts
        governed_names = [c.contract_name for c in manifest.governed_contracts]
        assert "CertifiedTopology" in governed_names
        assert "ExecutionAdmissionController" in governed_names
        assert "RuntimeReplayBundle" in governed_names
        assert "CertifiedRuntimeService" in governed_names

    def test_manifest_version_info(self):
        """Manifest should have correct version info."""
        manifest = build_runtime_spine_manifest()
        assert manifest.version_info.spine_version == RUNTIME_SPINE_VERSION
        assert manifest.generator_sprint == CONTRACT_FREEZE_SPRINT


class TestExceptions:
    """Tests for manifest exceptions."""

    def test_version_mismatch_error(self):
        """VersionMismatchError should store versions."""
        err = VersionMismatchError("0.1.0", "1.0.0")
        assert err.current == "0.1.0"
        assert err.required == "1.0.0"

    def test_contract_break_error(self):
        """ContractBreakError should store details."""
        err = ContractBreakError("TestContract", ["change1", "change2"])
        assert err.contract_name == "TestContract"
        assert len(err.breaking_changes) == 2

    def test_contract_not_found_error(self):
        """ContractNotFoundError should store name."""
        err = ContractNotFoundError("Missing")
        assert err.contract_name == "Missing"

    def test_invalid_contract_error(self):
        """InvalidContractError should store details."""
        err = InvalidContractError("Bad", "No module")
        assert err.contract_name == "Bad"
        assert err.reason == "No module"
