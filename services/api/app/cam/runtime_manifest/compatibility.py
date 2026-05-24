"""
Runtime Manifest Compatibility Utilities.

Sprint: MRP-5T
Status: FROZEN

Provides compatibility checking between manifest versions.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Set

from .contracts import (
    CompatibilityLevel,
    ContractClassification,
    RuntimeContractEntry,
    RuntimeCompatibilityReport,
    RuntimeSpineManifest,
)
from .versioning import is_compatible, parse_version
from .exceptions import VersionMismatchError, ContractBreakError


@dataclass
class ContractDiff:
    """Difference between two contract versions."""

    contract_name: str
    source_version: Optional[str]
    target_version: Optional[str]
    change_type: str  # ADDED, REMOVED, MODIFIED, UNCHANGED
    breaking: bool = False
    details: Optional[str] = None


def compare_contracts(
    source: RuntimeContractEntry,
    target: RuntimeContractEntry,
) -> ContractDiff:
    """Compare two contract entries."""
    if source.contract_name != target.contract_name:
        raise ValueError("Cannot compare contracts with different names")

    # Check for breaking changes
    breaking = False
    details_parts = []

    # Version change
    if source.version != target.version:
        source_parts = parse_version(source.version)
        target_parts = parse_version(target.version)

        if source_parts[0] != target_parts[0]:
            breaking = True
            details_parts.append(f"MAJOR version change: {source.version} -> {target.version}")

    # Classification change
    if source.classification != target.classification:
        # Downgrade from PUBLIC_GOVERNED is breaking
        if source.classification == ContractClassification.PUBLIC_GOVERNED:
            breaking = True
            details_parts.append(
                f"Classification downgrade: {source.classification.value} -> {target.classification.value}"
            )

    # Deprecation added
    if not source.deprecated and target.deprecated:
        details_parts.append("Contract deprecated")

    # Determinism change
    if source.deterministic and not target.deterministic:
        breaking = True
        details_parts.append("Lost determinism guarantee")

    # Replay safety change
    if source.replay_safe and not target.replay_safe:
        breaking = True
        details_parts.append("Lost replay safety guarantee")

    change_type = "MODIFIED" if details_parts else "UNCHANGED"

    return ContractDiff(
        contract_name=source.contract_name,
        source_version=source.version,
        target_version=target.version,
        change_type=change_type,
        breaking=breaking,
        details="; ".join(details_parts) if details_parts else None,
    )


def compare_manifests(
    source: RuntimeSpineManifest,
    target: RuntimeSpineManifest,
) -> RuntimeCompatibilityReport:
    """
    Compare two manifests and produce a compatibility report.

    Checks:
    - Version compatibility
    - Contract additions/removals
    - Contract modifications
    - Breaking changes
    """
    breaking_changes: List[str] = []
    additions: List[str] = []
    deprecations: List[str] = []

    # Build contract maps
    def build_contract_map(manifest: RuntimeSpineManifest) -> dict:
        contracts = {}
        for c in manifest.governed_contracts:
            contracts[c.contract_name] = c
        for c in manifest.developer_apis:
            contracts[c.contract_name] = c
        for c in manifest.internal_contracts:
            contracts[c.contract_name] = c
        return contracts

    source_contracts = build_contract_map(source)
    target_contracts = build_contract_map(target)

    source_names = set(source_contracts.keys())
    target_names = set(target_contracts.keys())

    # Check for removed contracts (only governed ones are breaking)
    removed = source_names - target_names
    for name in removed:
        contract = source_contracts[name]
        if contract.classification == ContractClassification.PUBLIC_GOVERNED:
            breaking_changes.append(f"Removed governed contract: {name}")

    # Check for added contracts
    added = target_names - source_names
    for name in added:
        additions.append(name)

    # Check for modified contracts
    common = source_names & target_names
    for name in common:
        diff = compare_contracts(source_contracts[name], target_contracts[name])
        if diff.breaking:
            breaking_changes.append(f"{name}: {diff.details}")
        if diff.change_type == "MODIFIED" and "deprecated" in (diff.details or "").lower():
            deprecations.append(name)

    # Determine overall compatibility level
    if breaking_changes:
        overall_level = CompatibilityLevel.MAJOR_BREAK
        compatible = False
    elif deprecations:
        overall_level = CompatibilityLevel.MINOR_BREAK
        compatible = True
    else:
        overall_level = CompatibilityLevel.COMPATIBLE
        compatible = True

    return RuntimeCompatibilityReport(
        source_version=source.version_info.spine_version,
        target_version=target.version_info.spine_version,
        compatible=compatible,
        breaking_changes=breaking_changes,
        additions=additions,
        deprecations=deprecations,
        overall_level=overall_level,
    )


def assert_compatible(
    current_version: str,
    required_version: str,
    raise_on_incompatible: bool = True,
) -> bool:
    """
    Assert that current version is compatible with required version.

    Args:
        current_version: The current runtime version
        required_version: The minimum required version
        raise_on_incompatible: If True, raise VersionMismatchError on incompatibility

    Returns:
        True if compatible, False otherwise (only if raise_on_incompatible=False)

    Raises:
        VersionMismatchError: If incompatible and raise_on_incompatible=True
    """
    compatible = is_compatible(current_version, required_version)

    if not compatible and raise_on_incompatible:
        raise VersionMismatchError(current_version, required_version)

    return compatible


def check_contract_stability(
    contract: RuntimeContractEntry,
    require_deterministic: bool = True,
    require_replay_safe: bool = True,
) -> List[str]:
    """
    Check contract stability requirements.

    Returns list of violations (empty if stable).
    """
    violations = []

    if require_deterministic and not contract.deterministic:
        violations.append(f"{contract.contract_name} is not deterministic")

    if require_replay_safe and not contract.replay_safe:
        violations.append(f"{contract.contract_name} is not replay-safe")

    if contract.deprecated:
        violations.append(f"{contract.contract_name} is deprecated: {contract.deprecation_note}")

    return violations
