"""
Runtime Manifest Package.

Sprint: MRP-5T
Status: FROZEN

Provides runtime spine manifest building, versioning, and compatibility checking.

Governed Exports:
    - RuntimeSpineManifest: Complete manifest of runtime spine contracts
    - RuntimeContractEntry: Single contract entry
    - RuntimeVersionInfo: Version information for the runtime spine
    - RuntimeCompatibilityReport: Comparison report between manifests

Developer APIs:
    - RuntimeSpineManifestBuilder: Builder for manifests
    - build_runtime_spine_manifest: Build complete manifest
    - compare_manifests: Compare two manifests
    - assert_compatible: Check version compatibility

Version Constants:
    - RUNTIME_SPINE_VERSION: Current spine version
    - REPLAY_BUNDLE_SCHEMA_VERSION: Replay bundle schema version
    - MANIFEST_SCHEMA_VERSION: Manifest schema version
    - CONTRACT_FREEZE_DATE: When contracts were frozen
"""

# Contracts
from .contracts import (
    ContractClassification,
    CompatibilityLevel,
    RuntimeContractEntry,
    RuntimeVersionInfo,
    RuntimeSpineManifest,
    RuntimeCompatibilityReport,
)

# Versioning
from .versioning import (
    RUNTIME_SPINE_VERSION,
    REPLAY_BUNDLE_SCHEMA_VERSION,
    MANIFEST_SCHEMA_VERSION,
    CONTRACT_FREEZE_DATE,
    CONTRACT_FREEZE_SPRINT,
    parse_version,
    is_compatible,
    get_version_info,
)

# Manifest builder
from .manifest import (
    RuntimeSpineManifestBuilder,
    build_runtime_spine_manifest,
    manifest_to_json,
    manifest_from_json,
    compute_manifest_hash,
)

# Compatibility
from .compatibility import (
    ContractDiff,
    compare_contracts,
    compare_manifests,
    assert_compatible,
    check_contract_stability,
)

# Exceptions
from .exceptions import (
    RuntimeManifestError,
    VersionMismatchError,
    ContractBreakError,
    ManifestBuildError,
    ContractNotFoundError,
    InvalidContractError,
)

__all__ = [
    # Contracts
    "ContractClassification",
    "CompatibilityLevel",
    "RuntimeContractEntry",
    "RuntimeVersionInfo",
    "RuntimeSpineManifest",
    "RuntimeCompatibilityReport",
    # Versioning
    "RUNTIME_SPINE_VERSION",
    "REPLAY_BUNDLE_SCHEMA_VERSION",
    "MANIFEST_SCHEMA_VERSION",
    "CONTRACT_FREEZE_DATE",
    "CONTRACT_FREEZE_SPRINT",
    "parse_version",
    "is_compatible",
    "get_version_info",
    # Manifest
    "RuntimeSpineManifestBuilder",
    "build_runtime_spine_manifest",
    "manifest_to_json",
    "manifest_from_json",
    "compute_manifest_hash",
    # Compatibility
    "ContractDiff",
    "compare_contracts",
    "compare_manifests",
    "assert_compatible",
    "check_contract_stability",
    # Exceptions
    "RuntimeManifestError",
    "VersionMismatchError",
    "ContractBreakError",
    "ManifestBuildError",
    "ContractNotFoundError",
    "InvalidContractError",
]
