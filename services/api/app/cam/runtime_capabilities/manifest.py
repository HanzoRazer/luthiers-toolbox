"""
Capability Manifest.

Sprint: MRP-5V
Status: PROTOTYPE

Deterministic manifest generation for capability inventory.

Design principles:
  - Manifest output is deterministic
  - Stable ordering (namespace, capability_id, version)
  - All required fields present
  - JSON-serializable
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .contracts import (
    CapabilityNamespace,
    FederatedCapability,
    GovernanceClassification,
)
from .exceptions import ManifestGenerationError
from .registry import CapabilityRegistry, get_capability_registry


# -----------------------------------------------------------------------------
# Manifest Entry
# -----------------------------------------------------------------------------

@dataclass
class CapabilityManifestEntry:
    """
    Single entry in the capability manifest.

    Required fields per MRP-5V spec:
      - capability_id
      - capability_type (namespace)
      - version
      - deterministic
      - replay_safe
      - enabled
      - governance_classification
      - compatibility_tags
    """

    capability_id: str
    capability_type: str
    version: str
    deterministic: bool
    replay_safe: bool
    enabled: bool
    governance_classification: str
    compatibility_tags: List[str]

    # Optional fields
    display_name: str = ""
    description: str = ""
    source_name: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "capability_id": self.capability_id,
            "capability_type": self.capability_type,
            "version": self.version,
            "deterministic": self.deterministic,
            "replay_safe": self.replay_safe,
            "enabled": self.enabled,
            "governance_classification": self.governance_classification,
            "compatibility_tags": self.compatibility_tags,
            "display_name": self.display_name,
            "description": self.description,
            "source_name": self.source_name,
        }

    @classmethod
    def from_capability(cls, capability: FederatedCapability) -> "CapabilityManifestEntry":
        """Create manifest entry from federated capability."""
        return cls(
            capability_id=capability.capability_id,
            capability_type=capability.namespace.value,
            version=capability.version,
            deterministic=capability.deterministic,
            replay_safe=capability.replay_safe,
            enabled=capability.enabled,
            governance_classification=capability.governance_classification.value,
            compatibility_tags=sorted(capability.compatibility_tags),
            display_name=capability.display_name,
            description=capability.description,
            source_name=capability.source_name,
        )


# -----------------------------------------------------------------------------
# Manifest
# -----------------------------------------------------------------------------

@dataclass
class CapabilityManifest:
    """
    Complete capability manifest.

    Contains all registered capabilities with deterministic ordering.
    """

    # Metadata
    schema_version: str = "1"
    generated_at: str = ""
    sprint: str = "MRP-5V"

    # Content
    entries: List[CapabilityManifestEntry] = field(default_factory=list)

    # Statistics
    total_count: int = 0
    enabled_count: int = 0
    disabled_count: int = 0
    replay_safe_count: int = 0
    deterministic_count: int = 0

    # Integrity
    content_hash: str = ""

    def __post_init__(self):
        if not self.generated_at:
            self.generated_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "schema_version": self.schema_version,
            "generated_at": self.generated_at,
            "sprint": self.sprint,
            "entries": [e.to_dict() for e in self.entries],
            "statistics": {
                "total_count": self.total_count,
                "enabled_count": self.enabled_count,
                "disabled_count": self.disabled_count,
                "replay_safe_count": self.replay_safe_count,
                "deterministic_count": self.deterministic_count,
            },
            "content_hash": self.content_hash,
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CapabilityManifest":
        """Create manifest from dictionary."""
        stats = data.get("statistics", {})
        entries = [
            CapabilityManifestEntry(**e)
            for e in data.get("entries", [])
        ]
        return cls(
            schema_version=data.get("schema_version", "1"),
            generated_at=data.get("generated_at", ""),
            sprint=data.get("sprint", ""),
            entries=entries,
            total_count=stats.get("total_count", len(entries)),
            enabled_count=stats.get("enabled_count", 0),
            disabled_count=stats.get("disabled_count", 0),
            replay_safe_count=stats.get("replay_safe_count", 0),
            deterministic_count=stats.get("deterministic_count", 0),
            content_hash=data.get("content_hash", ""),
        )

    @classmethod
    def from_json(cls, json_str: str) -> "CapabilityManifest":
        """Create manifest from JSON string."""
        return cls.from_dict(json.loads(json_str))


# -----------------------------------------------------------------------------
# Manifest Builder
# -----------------------------------------------------------------------------

def _sort_key(entry: CapabilityManifestEntry) -> tuple:
    """
    Sort key for deterministic ordering.

    Order: capability_type, capability_id, version
    """
    return (entry.capability_type, entry.capability_id, entry.version)


def _compute_content_hash(entries: List[CapabilityManifestEntry]) -> str:
    """
    Compute deterministic content hash.

    Uses sorted entry data to ensure consistent hash.
    """
    # Build canonical representation
    canonical = []
    for entry in sorted(entries, key=_sort_key):
        canonical.append(
            f"{entry.capability_id}:{entry.version}:{entry.enabled}:{entry.deterministic}:{entry.replay_safe}"
        )

    content = "\n".join(canonical)
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]


def build_capability_manifest(
    registry: Optional[CapabilityRegistry] = None,
) -> CapabilityManifest:
    """
    Build capability manifest from registry.

    Args:
        registry: Capability registry (defaults to global)

    Returns:
        CapabilityManifest with deterministic ordering
    """
    if registry is None:
        registry = get_capability_registry()

    capabilities = registry.list_capabilities()

    # Build entries
    entries = [
        CapabilityManifestEntry.from_capability(cap)
        for cap in capabilities
    ]

    # Sort deterministically
    entries.sort(key=_sort_key)

    # Compute statistics
    total = len(entries)
    enabled = sum(1 for e in entries if e.enabled)
    disabled = total - enabled
    replay_safe = sum(1 for e in entries if e.replay_safe)
    deterministic = sum(1 for e in entries if e.deterministic)

    # Compute content hash
    content_hash = _compute_content_hash(entries)

    return CapabilityManifest(
        entries=entries,
        total_count=total,
        enabled_count=enabled,
        disabled_count=disabled,
        replay_safe_count=replay_safe,
        deterministic_count=deterministic,
        content_hash=content_hash,
    )


def compare_manifests(
    old_manifest: CapabilityManifest,
    new_manifest: CapabilityManifest,
) -> Dict[str, Any]:
    """
    Compare two manifests.

    Returns:
        Comparison report with changes
    """
    old_ids = {e.capability_id for e in old_manifest.entries}
    new_ids = {e.capability_id for e in new_manifest.entries}

    added = new_ids - old_ids
    removed = old_ids - new_ids
    common = old_ids & new_ids

    # Check for changes in common capabilities
    old_by_id = {e.capability_id: e for e in old_manifest.entries}
    new_by_id = {e.capability_id: e for e in new_manifest.entries}

    changed = []
    for cid in common:
        old_entry = old_by_id[cid]
        new_entry = new_by_id[cid]
        if old_entry.to_dict() != new_entry.to_dict():
            changed.append({
                "capability_id": cid,
                "old": old_entry.to_dict(),
                "new": new_entry.to_dict(),
            })

    return {
        "hash_match": old_manifest.content_hash == new_manifest.content_hash,
        "added": sorted(added),
        "removed": sorted(removed),
        "changed": changed,
        "old_count": old_manifest.total_count,
        "new_count": new_manifest.total_count,
    }
