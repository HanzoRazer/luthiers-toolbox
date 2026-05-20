"""
CAD Kernel Adapters.

Sprint: MRP-5H, MRP-5K
Status: PROTOTYPE

Provides adapter implementations for CAD kernel operations.
The adapter pattern isolates kernel-specific code from the
topology builder, enabling kernel swapping and testing.

MRP-5K: Formal KernelAdapterInterface protocol with narrow contract.

ARCHITECTURAL BOUNDARIES (MRP-5K):

Adapters MUST:
    - Execute geometric operations only
    - Return kernel-agnostic result types
    - Remain stateless between operations

Adapters MUST NOT:
    - Infer semantics
    - Repair topology silently
    - Classify runtime feasibility
    - Introduce kernel-native ontology

Current adapters:
    - MockKernelAdapter: For testing without real CAD kernel
    - (Future) OCCAdapter: OpenCASCADE-based operations
    - (Future) CadQueryAdapter: CadQuery-based operations
    - (Future) Build123dAdapter: build123d-based operations
"""

from .interface import (
    AdapterBoundingBox,
    AdapterErrorCode,
    AdapterExportResult,
    AdapterGeometryHandle,
    AdapterOperationType,
    AdapterPoint3D,
    AdapterResult,
    AdapterValidationResult,
    BaseKernelAdapter,
    KernelAdapterInterface,
)
from .mock_adapter import MockKernelAdapter
from .registry import (
    AdapterCapability,
    AdapterDeclaration,
    AdapterMaturity,
    AdapterRegistryEntry,
    KernelAdapterRegistry,
    get_adapter,
    get_adapter_registry,
    get_mock_adapter,
    list_available_adapters,
)

__all__ = [
    # Interface
    "KernelAdapterInterface",
    "BaseKernelAdapter",
    # Data types
    "AdapterPoint3D",
    "AdapterBoundingBox",
    "AdapterGeometryHandle",
    "AdapterResult",
    "AdapterValidationResult",
    "AdapterExportResult",
    # Enums
    "AdapterOperationType",
    "AdapterErrorCode",
    # Implementations
    "MockKernelAdapter",
    # Registry
    "KernelAdapterRegistry",
    "AdapterDeclaration",
    "AdapterCapability",
    "AdapterMaturity",
    "AdapterRegistryEntry",
    "get_adapter_registry",
    "get_adapter",
    "get_mock_adapter",
    "list_available_adapters",
]
