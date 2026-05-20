"""
Kernel Adapter Registry.

Sprint: MRP-5K
Status: PROTOTYPE

Registry for CAD kernel adapters with capability declarations.
Allows discovery and selection of available adapters.

ARCHITECTURAL PRINCIPLES:

The registry:
    - Declares adapter capabilities (what they CAN do)
    - Reports adapter availability (kernel installed/working)
    - Does NOT make semantic decisions
    - Does NOT select "best" adapter (caller decides)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional, Type

from .interface import KernelAdapterInterface


class AdapterMaturity(str, Enum):
    """Maturity level of an adapter."""

    MOCK = "mock"  # Testing only, no real kernel
    EXPERIMENTAL = "experimental"  # In development, may change
    CANDIDATE = "candidate"  # Feature complete, under validation
    STABLE = "stable"  # Production ready


class AdapterCapability(str, Enum):
    """Capabilities an adapter may support."""

    CREATE_FACE = "create_face"
    EXTRUDE = "extrude"
    LOFT = "loft"
    VALIDATE_CLOSED = "validate_closed"
    VALIDATE_MANIFOLD = "validate_manifold"
    BOUNDING_BOX = "bounding_box"
    EXPORT_STEP = "export_step"


@dataclass
class AdapterDeclaration:
    """
    Declaration of an adapter's capabilities.

    This is metadata ABOUT the adapter, not the adapter itself.
    """

    adapter_id: str
    kernel_name: str
    maturity: AdapterMaturity
    capabilities: List[AdapterCapability]
    description: str = ""
    notes: str = ""

    def supports(self, capability: AdapterCapability) -> bool:
        """Check if adapter supports a capability."""
        return capability in self.capabilities


@dataclass
class AdapterRegistryEntry:
    """Entry in the adapter registry."""

    declaration: AdapterDeclaration
    factory: Callable[[], KernelAdapterInterface]
    _cached_instance: Optional[KernelAdapterInterface] = field(
        default=None, repr=False
    )

    def get_adapter(self, cached: bool = True) -> KernelAdapterInterface:
        """
        Get an adapter instance.

        Args:
            cached: If True, return cached instance. If False, create new.

        Returns:
            Adapter instance
        """
        if cached and self._cached_instance is not None:
            return self._cached_instance

        instance = self.factory()

        if cached:
            self._cached_instance = instance

        return instance

    def is_available(self) -> bool:
        """Check if the adapter's kernel is available."""
        try:
            adapter = self.get_adapter()
            return adapter.is_available
        except Exception:
            return False


class KernelAdapterRegistry:
    """
    Registry for kernel adapters.

    Maintains declarations and factories for all known adapters.
    Does NOT make semantic decisions about adapter selection.
    """

    def __init__(self):
        self._entries: Dict[str, AdapterRegistryEntry] = {}

    def register(
        self,
        declaration: AdapterDeclaration,
        factory: Callable[[], KernelAdapterInterface],
    ) -> None:
        """
        Register an adapter.

        Args:
            declaration: Adapter capability declaration
            factory: Factory function to create adapter instance
        """
        self._entries[declaration.adapter_id] = AdapterRegistryEntry(
            declaration=declaration,
            factory=factory,
        )

    def get(self, adapter_id: str) -> Optional[AdapterRegistryEntry]:
        """Get registry entry by adapter ID."""
        return self._entries.get(adapter_id)

    def get_adapter(self, adapter_id: str) -> Optional[KernelAdapterInterface]:
        """Get adapter instance by ID."""
        entry = self._entries.get(adapter_id)
        if entry:
            return entry.get_adapter()
        return None

    def list_adapters(self) -> List[AdapterDeclaration]:
        """List all registered adapter declarations."""
        return [e.declaration for e in self._entries.values()]

    def list_available(self) -> List[AdapterDeclaration]:
        """List adapters whose kernels are available."""
        return [
            e.declaration
            for e in self._entries.values()
            if e.is_available()
        ]

    def list_by_capability(
        self, capability: AdapterCapability
    ) -> List[AdapterDeclaration]:
        """List adapters supporting a capability."""
        return [
            e.declaration
            for e in self._entries.values()
            if e.declaration.supports(capability)
        ]

    def list_by_maturity(
        self, maturity: AdapterMaturity
    ) -> List[AdapterDeclaration]:
        """List adapters at a maturity level."""
        return [
            e.declaration
            for e in self._entries.values()
            if e.declaration.maturity == maturity
        ]


# Global registry instance
_ADAPTER_REGISTRY: Optional[KernelAdapterRegistry] = None


def get_adapter_registry() -> KernelAdapterRegistry:
    """Get the global adapter registry."""
    global _ADAPTER_REGISTRY
    if _ADAPTER_REGISTRY is None:
        _ADAPTER_REGISTRY = KernelAdapterRegistry()
        _register_default_adapters(_ADAPTER_REGISTRY)
    return _ADAPTER_REGISTRY


def _register_default_adapters(registry: KernelAdapterRegistry) -> None:
    """Register default adapters."""
    from .mock_adapter import MockKernelAdapter

    # Mock adapter (always available for testing)
    registry.register(
        declaration=AdapterDeclaration(
            adapter_id="mock",
            kernel_name="mock",
            maturity=AdapterMaturity.MOCK,
            capabilities=[
                AdapterCapability.CREATE_FACE,
                AdapterCapability.EXTRUDE,
                AdapterCapability.LOFT,
                AdapterCapability.VALIDATE_CLOSED,
                AdapterCapability.VALIDATE_MANIFOLD,
                AdapterCapability.BOUNDING_BOX,
                AdapterCapability.EXPORT_STEP,
            ],
            description="Mock kernel adapter for testing",
            notes="No real CAD kernel. Returns configurable mock results.",
        ),
        factory=MockKernelAdapter,
    )


# Convenience functions


def get_adapter(adapter_id: str) -> Optional[KernelAdapterInterface]:
    """Get adapter instance by ID."""
    return get_adapter_registry().get_adapter(adapter_id)


def list_available_adapters() -> List[AdapterDeclaration]:
    """List all available adapters."""
    return get_adapter_registry().list_available()


def get_mock_adapter(**kwargs) -> "MockKernelAdapter":
    """
    Get a mock adapter with optional configuration.

    Convenience function for testing.
    """
    from .mock_adapter import MockKernelAdapter
    return MockKernelAdapter(**kwargs)
