"""
Capability Registry.

Sprint: MRP-5V
Status: PROTOTYPE

The federation layer over domain-local capability sources.

Design principles:
  - Registry is visibility, not authorization
  - Sources are consumed through adapters, not replaced
  - Namespaced IDs prevent collision
  - Duplicate IDs are rejected
"""

from __future__ import annotations

from typing import Dict, List, Optional, Set

from .contracts import (
    CapabilityNamespace,
    CapabilitySource,
    FederatedCapability,
    make_capability_id,
    parse_capability_id,
)
from .exceptions import (
    CapabilityNotFoundError,
    DuplicateCapabilityError,
    InvalidCapabilityIdError,
)


class CapabilityRegistry:
    """
    Federation layer over domain-local capability sources.

    Aggregates capabilities from multiple sources into a unified
    registry with namespaced IDs. Does not modify source registries.

    Registry responsibilities:
      - Capability identity and metadata
      - Deterministic inventory
      - Duplicate detection

    Registry does NOT:
      - Authorize execution
      - Evaluate policies
      - Execute capabilities
    """

    def __init__(self):
        self._sources: Dict[str, CapabilitySource] = {}
        self._capabilities: Dict[str, FederatedCapability] = {}
        self._capability_to_source: Dict[str, str] = {}
        self._frozen = False

    def register_source(self, source: CapabilitySource) -> None:
        """
        Register a capability source.

        Args:
            source: Capability source to register

        Raises:
            DuplicateCapabilityError: If source provides duplicate IDs
            RuntimeError: If registry is frozen
        """
        if self._frozen:
            raise RuntimeError("Cannot register source: registry is frozen")

        source_name = source.source_name

        if source_name in self._sources:
            raise ValueError(f"Source already registered: {source_name}")

        # Collect capabilities from source
        for local_id in source.list_capability_ids():
            full_id = make_capability_id(source.namespace, local_id)

            # Check for duplicates
            if full_id in self._capabilities:
                existing_source = self._capability_to_source[full_id]
                raise DuplicateCapabilityError(full_id, source_name)

            # Get capability from source
            capability = source.get_capability(local_id)
            if capability is not None:
                self._capabilities[full_id] = capability
                self._capability_to_source[full_id] = source_name

        self._sources[source_name] = source

    def freeze(self) -> None:
        """
        Freeze the registry.

        After freezing, no new sources can be registered.
        This ensures deterministic inventory.
        """
        self._frozen = True

    @property
    def is_frozen(self) -> bool:
        """Whether the registry is frozen."""
        return self._frozen

    def get_capability(self, capability_id: str) -> Optional[FederatedCapability]:
        """
        Get a capability by full ID.

        Args:
            capability_id: Full namespaced ID (e.g., "operation:nut_slot")

        Returns:
            FederatedCapability if found, None otherwise

        Raises:
            InvalidCapabilityIdError: If ID format is invalid
        """
        try:
            parse_capability_id(capability_id)
        except ValueError as e:
            raise InvalidCapabilityIdError(capability_id, str(e))

        return self._capabilities.get(capability_id)

    def require_capability(self, capability_id: str) -> FederatedCapability:
        """
        Get a capability, raising if not found.

        Args:
            capability_id: Full namespaced ID

        Returns:
            FederatedCapability

        Raises:
            CapabilityNotFoundError: If capability not registered
            InvalidCapabilityIdError: If ID format is invalid
        """
        capability = self.get_capability(capability_id)
        if capability is None:
            raise CapabilityNotFoundError(
                capability_id,
                list(self._capabilities.keys()),
            )
        return capability

    def has_capability(self, capability_id: str) -> bool:
        """
        Check if a capability is registered.

        Args:
            capability_id: Full namespaced ID

        Returns:
            True if registered, False otherwise
        """
        try:
            return self.get_capability(capability_id) is not None
        except InvalidCapabilityIdError:
            return False

    def list_capability_ids(self) -> List[str]:
        """
        List all registered capability IDs.

        Returns:
            Sorted list of capability IDs
        """
        return sorted(self._capabilities.keys())

    def list_capabilities(self) -> List[FederatedCapability]:
        """
        List all registered capabilities.

        Returns:
            List of capabilities sorted by ID
        """
        return [self._capabilities[cid] for cid in self.list_capability_ids()]

    def list_capabilities_by_namespace(
        self,
        namespace: CapabilityNamespace,
    ) -> List[FederatedCapability]:
        """
        List capabilities in a specific namespace.

        Args:
            namespace: Namespace to filter by

        Returns:
            List of capabilities in that namespace
        """
        prefix = f"{namespace.value}:"
        return [
            cap for cid, cap in sorted(self._capabilities.items())
            if cid.startswith(prefix)
        ]

    def list_enabled_capabilities(self) -> List[FederatedCapability]:
        """
        List all enabled capabilities.

        Returns:
            List of enabled capabilities
        """
        return [
            cap for cap in self.list_capabilities()
            if cap.enabled
        ]

    def list_replay_safe_capabilities(self) -> List[FederatedCapability]:
        """
        List all replay-safe capabilities.

        Returns:
            List of replay-safe capabilities
        """
        return [
            cap for cap in self.list_capabilities()
            if cap.replay_safe
        ]

    def list_deterministic_capabilities(self) -> List[FederatedCapability]:
        """
        List all deterministic capabilities.

        Returns:
            List of deterministic capabilities
        """
        return [
            cap for cap in self.list_capabilities()
            if cap.deterministic
        ]

    def get_source_for_capability(self, capability_id: str) -> Optional[str]:
        """
        Get the source name for a capability.

        Args:
            capability_id: Full namespaced ID

        Returns:
            Source name if found, None otherwise
        """
        return self._capability_to_source.get(capability_id)

    def list_sources(self) -> List[str]:
        """
        List all registered source names.

        Returns:
            List of source names
        """
        return list(self._sources.keys())

    def get_statistics(self) -> Dict:
        """
        Get registry statistics.

        Returns:
            Dictionary of statistics
        """
        capabilities = self.list_capabilities()
        return {
            "total_capabilities": len(capabilities),
            "total_sources": len(self._sources),
            "enabled_count": sum(1 for c in capabilities if c.enabled),
            "disabled_count": sum(1 for c in capabilities if not c.enabled),
            "replay_safe_count": sum(1 for c in capabilities if c.replay_safe),
            "deterministic_count": sum(1 for c in capabilities if c.deterministic),
            "by_namespace": {
                ns.value: len(self.list_capabilities_by_namespace(ns))
                for ns in CapabilityNamespace
            },
            "frozen": self._frozen,
        }


# -----------------------------------------------------------------------------
# Global Registry
# -----------------------------------------------------------------------------

_global_registry: Optional[CapabilityRegistry] = None


def get_capability_registry() -> CapabilityRegistry:
    """
    Get the global capability registry.

    Creates a new registry if none exists.
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = CapabilityRegistry()
    return _global_registry


def reset_capability_registry() -> None:
    """
    Reset the global capability registry.

    For testing purposes only.
    """
    global _global_registry
    _global_registry = None
