"""
Runtime Manifest Contracts.

Sprint: MRP-5T
Status: FROZEN

Defines manifest contracts for runtime spine inventory and compatibility.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from .versioning import (
    RUNTIME_SPINE_VERSION,
    REPLAY_BUNDLE_SCHEMA_VERSION,
    MANIFEST_SCHEMA_VERSION,
    CONTRACT_FREEZE_DATE,
)


class ContractClassification(str, Enum):
    """Classification of runtime contracts."""

    PUBLIC_GOVERNED = "PUBLIC_GOVERNED"
    DEVELOPER_EXPERIMENTAL = "DEVELOPER_EXPERIMENTAL"
    INTERNAL_ONLY = "INTERNAL_ONLY"


class CompatibilityLevel(str, Enum):
    """Compatibility level for contracts."""

    COMPATIBLE = "COMPATIBLE"
    MINOR_BREAK = "MINOR_BREAK"
    MAJOR_BREAK = "MAJOR_BREAK"
    INTERNAL_ONLY = "INTERNAL_ONLY"


@dataclass
class RuntimeContractEntry:
    """Entry for a single runtime contract."""

    contract_name: str
    module_path: str
    classification: ContractClassification
    version: str = RUNTIME_SPINE_VERSION
    compatibility_level: CompatibilityLevel = CompatibilityLevel.COMPATIBLE
    deprecated: bool = False
    deprecation_note: Optional[str] = None
    deterministic: bool = True
    replay_safe: bool = True
    description: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "contract_name": self.contract_name,
            "module_path": self.module_path,
            "classification": self.classification.value,
            "version": self.version,
            "compatibility_level": self.compatibility_level.value,
            "deprecated": self.deprecated,
            "deprecation_note": self.deprecation_note,
            "deterministic": self.deterministic,
            "replay_safe": self.replay_safe,
            "description": self.description,
        }


@dataclass
class RuntimeVersionInfo:
    """Version information for the runtime spine."""

    spine_version: str = RUNTIME_SPINE_VERSION
    replay_schema_version: str = REPLAY_BUNDLE_SCHEMA_VERSION
    manifest_schema_version: str = MANIFEST_SCHEMA_VERSION
    freeze_date: str = CONTRACT_FREEZE_DATE

    def to_dict(self) -> Dict[str, Any]:
        return {
            "spine_version": self.spine_version,
            "replay_schema_version": self.replay_schema_version,
            "manifest_schema_version": self.manifest_schema_version,
            "freeze_date": self.freeze_date,
        }


@dataclass
class RuntimeSpineManifest:
    """
    Complete manifest of the runtime spine.

    Contains:
    - Version information
    - Governed contracts
    - Developer APIs
    - Internal contracts
    - Compatibility status
    """

    version_info: RuntimeVersionInfo
    governed_contracts: List[RuntimeContractEntry] = field(default_factory=list)
    developer_apis: List[RuntimeContractEntry] = field(default_factory=list)
    internal_contracts: List[RuntimeContractEntry] = field(default_factory=list)
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    generator_sprint: str = "MRP-5T"

    @property
    def total_contracts(self) -> int:
        return (
            len(self.governed_contracts)
            + len(self.developer_apis)
            + len(self.internal_contracts)
        )

    @property
    def compatibility_status(self) -> str:
        """Overall compatibility status."""
        if any(c.deprecated for c in self.governed_contracts):
            return "DEPRECATIONS_PENDING"
        return "STABLE_PROTOTYPE"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version_info": self.version_info.to_dict(),
            "governed_contracts": [c.to_dict() for c in self.governed_contracts],
            "developer_apis": [c.to_dict() for c in self.developer_apis],
            "internal_contracts": [c.to_dict() for c in self.internal_contracts],
            "total_contracts": self.total_contracts,
            "compatibility_status": self.compatibility_status,
            "generated_at": self.generated_at,
            "generator_sprint": self.generator_sprint,
        }


@dataclass
class RuntimeCompatibilityReport:
    """Report comparing two manifest versions."""

    source_version: str
    target_version: str
    compatible: bool
    breaking_changes: List[str] = field(default_factory=list)
    additions: List[str] = field(default_factory=list)
    deprecations: List[str] = field(default_factory=list)
    overall_level: CompatibilityLevel = CompatibilityLevel.COMPATIBLE

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_version": self.source_version,
            "target_version": self.target_version,
            "compatible": self.compatible,
            "breaking_changes": self.breaking_changes,
            "additions": self.additions,
            "deprecations": self.deprecations,
            "overall_level": self.overall_level.value,
        }
