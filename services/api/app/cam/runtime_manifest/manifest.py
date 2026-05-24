"""
Runtime Spine Manifest Builder.

Sprint: MRP-5T
Status: FROZEN

Builds complete runtime spine manifest from registered contracts.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set
import hashlib
import json

from .contracts import (
    ContractClassification,
    CompatibilityLevel,
    RuntimeContractEntry,
    RuntimeVersionInfo,
    RuntimeSpineManifest,
)
from .versioning import RUNTIME_SPINE_VERSION, CONTRACT_FREEZE_SPRINT
from .exceptions import ManifestBuildError, ContractNotFoundError, InvalidContractError


class RuntimeSpineManifestBuilder:
    """
    Builder for RuntimeSpineManifest.

    Usage:
        builder = RuntimeSpineManifestBuilder()
        builder.add_governed_contract(...)
        builder.add_developer_api(...)
        manifest = builder.build()
    """

    def __init__(self):
        self._governed: List[RuntimeContractEntry] = []
        self._developer: List[RuntimeContractEntry] = []
        self._internal: List[RuntimeContractEntry] = []
        self._seen_names: Set[str] = set()

    def add_governed_contract(
        self,
        contract_name: str,
        module_path: str,
        description: Optional[str] = None,
        deprecated: bool = False,
        deprecation_note: Optional[str] = None,
        deterministic: bool = True,
        replay_safe: bool = True,
    ) -> "RuntimeSpineManifestBuilder":
        """Add a PUBLIC_GOVERNED contract."""
        self._add_contract(
            contract_name=contract_name,
            module_path=module_path,
            classification=ContractClassification.PUBLIC_GOVERNED,
            description=description,
            deprecated=deprecated,
            deprecation_note=deprecation_note,
            deterministic=deterministic,
            replay_safe=replay_safe,
            target_list=self._governed,
        )
        return self

    def add_developer_api(
        self,
        contract_name: str,
        module_path: str,
        description: Optional[str] = None,
        deprecated: bool = False,
        deprecation_note: Optional[str] = None,
        deterministic: bool = True,
        replay_safe: bool = True,
    ) -> "RuntimeSpineManifestBuilder":
        """Add a DEVELOPER_EXPERIMENTAL contract."""
        self._add_contract(
            contract_name=contract_name,
            module_path=module_path,
            classification=ContractClassification.DEVELOPER_EXPERIMENTAL,
            description=description,
            deprecated=deprecated,
            deprecation_note=deprecation_note,
            deterministic=deterministic,
            replay_safe=replay_safe,
            target_list=self._developer,
        )
        return self

    def add_internal_contract(
        self,
        contract_name: str,
        module_path: str,
        description: Optional[str] = None,
        deterministic: bool = True,
        replay_safe: bool = True,
    ) -> "RuntimeSpineManifestBuilder":
        """Add an INTERNAL_ONLY contract."""
        self._add_contract(
            contract_name=contract_name,
            module_path=module_path,
            classification=ContractClassification.INTERNAL_ONLY,
            description=description,
            deprecated=False,
            deprecation_note=None,
            deterministic=deterministic,
            replay_safe=replay_safe,
            target_list=self._internal,
        )
        return self

    def _add_contract(
        self,
        contract_name: str,
        module_path: str,
        classification: ContractClassification,
        description: Optional[str],
        deprecated: bool,
        deprecation_note: Optional[str],
        deterministic: bool,
        replay_safe: bool,
        target_list: List[RuntimeContractEntry],
    ) -> None:
        """Internal: add a contract entry."""
        if contract_name in self._seen_names:
            raise InvalidContractError(
                contract_name,
                "Duplicate contract name",
            )

        if not module_path:
            raise InvalidContractError(
                contract_name,
                "Module path required",
            )

        entry = RuntimeContractEntry(
            contract_name=contract_name,
            module_path=module_path,
            classification=classification,
            description=description,
            deprecated=deprecated,
            deprecation_note=deprecation_note,
            deterministic=deterministic,
            replay_safe=replay_safe,
        )

        self._seen_names.add(contract_name)
        target_list.append(entry)

    def build(self) -> RuntimeSpineManifest:
        """Build the manifest."""
        if not self._governed and not self._developer and not self._internal:
            raise ManifestBuildError("No contracts registered")

        version_info = RuntimeVersionInfo()

        return RuntimeSpineManifest(
            version_info=version_info,
            governed_contracts=list(self._governed),
            developer_apis=list(self._developer),
            internal_contracts=list(self._internal),
            generator_sprint=CONTRACT_FREEZE_SPRINT,
        )

    def clear(self) -> "RuntimeSpineManifestBuilder":
        """Clear all registered contracts."""
        self._governed.clear()
        self._developer.clear()
        self._internal.clear()
        self._seen_names.clear()
        return self


def build_runtime_spine_manifest() -> RuntimeSpineManifest:
    """
    Build the complete runtime spine manifest.

    This registers all known contracts from the runtime spine modules.
    """
    builder = RuntimeSpineManifestBuilder()

    # topology_validation contracts
    builder.add_governed_contract(
        "CertifiedTopology",
        "app.cam.topology_validation.certified",
        description="Immutable wrapper for validated topology data",
    )
    builder.add_governed_contract(
        "TopologyValidator",
        "app.cam.topology_validation.validator",
        description="Validates topology and produces CertifiedTopology",
    )
    builder.add_developer_api(
        "certify_topology",
        "app.cam.topology_validation",
        description="Convenience function for topology certification",
    )

    # runtime_admission contracts
    builder.add_governed_contract(
        "ExecutionAdmissionController",
        "app.cam.runtime_admission.controller",
        description="Gate controlling runtime execution admission",
    )
    builder.add_governed_contract(
        "ExecutionAdmissionRequest",
        "app.cam.runtime_admission.contracts",
        description="Request contract for admission control",
    )
    builder.add_governed_contract(
        "AdmissionDecision",
        "app.cam.runtime_admission.contracts",
        description="Decision contract from admission control",
    )
    builder.add_internal_contract(
        "AdmissionPolicy",
        "app.cam.runtime_admission.policies",
        description="Base class for admission policies",
    )

    # runtime_provenance contracts
    builder.add_governed_contract(
        "RuntimeReplayBundle",
        "app.cam.runtime_provenance.bundle",
        description="Self-contained serializable provenance package",
    )
    builder.add_governed_contract(
        "ReplayExecutionHarness",
        "app.cam.runtime_provenance.execution",
        description="Executes deterministic mock replay",
    )
    builder.add_governed_contract(
        "ArtifactRegressionComparator",
        "app.cam.runtime_provenance.regression",
        description="Compares reproduced artifacts against baselines",
    )
    builder.add_developer_api(
        "verify_replay_bundle_integrity",
        "app.cam.runtime_provenance",
        description="Verifies bundle integrity for replay",
    )

    # runtime_service contracts
    builder.add_governed_contract(
        "CertifiedRuntimeService",
        "app.cam.runtime_service.service",
        description="Safe internal orchestration boundary",
    )
    builder.add_governed_contract(
        "CertifiedRuntimeRequest",
        "app.cam.runtime_service.contracts",
        description="Request contract for runtime service",
    )
    builder.add_governed_contract(
        "CertifiedRuntimeResult",
        "app.cam.runtime_service.contracts",
        description="Result contract from runtime service",
    )
    builder.add_developer_api(
        "execute_certified_runtime",
        "app.cam.runtime_service",
        description="Convenience function for certified execution",
    )
    builder.add_developer_api(
        "MockRuntimeAdapter",
        "app.cam.runtime_service.adapters",
        description="Deterministic mock adapter for prototype tier",
    )
    builder.add_internal_contract(
        "AdapterRegistry",
        "app.cam.runtime_service.adapters",
        description="Registry for runtime adapters",
    )

    return builder.build()


def manifest_to_json(manifest: RuntimeSpineManifest, indent: int = 2) -> str:
    """Serialize manifest to JSON string."""
    return json.dumps(manifest.to_dict(), indent=indent)


def manifest_from_json(json_str: str) -> RuntimeSpineManifest:
    """Deserialize manifest from JSON string."""
    data = json.loads(json_str)

    version_info = RuntimeVersionInfo(
        spine_version=data["version_info"]["spine_version"],
        replay_schema_version=data["version_info"]["replay_schema_version"],
        manifest_schema_version=data["version_info"]["manifest_schema_version"],
        freeze_date=data["version_info"]["freeze_date"],
    )

    def parse_contract(d: Dict[str, Any]) -> RuntimeContractEntry:
        return RuntimeContractEntry(
            contract_name=d["contract_name"],
            module_path=d["module_path"],
            classification=ContractClassification(d["classification"]),
            version=d["version"],
            compatibility_level=CompatibilityLevel(d["compatibility_level"]),
            deprecated=d["deprecated"],
            deprecation_note=d["deprecation_note"],
            deterministic=d["deterministic"],
            replay_safe=d["replay_safe"],
            description=d["description"],
        )

    return RuntimeSpineManifest(
        version_info=version_info,
        governed_contracts=[parse_contract(c) for c in data["governed_contracts"]],
        developer_apis=[parse_contract(c) for c in data["developer_apis"]],
        internal_contracts=[parse_contract(c) for c in data["internal_contracts"]],
        generated_at=data["generated_at"],
        generator_sprint=data["generator_sprint"],
    )


def compute_manifest_hash(manifest: RuntimeSpineManifest) -> str:
    """Compute deterministic hash of manifest contents."""
    # Exclude generated_at for deterministic hash
    data = manifest.to_dict()
    del data["generated_at"]

    # Sort for determinism
    canonical = json.dumps(data, sort_keys=True)
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]
