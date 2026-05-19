"""
CAD Kernel Adapters.

Sprint: MRP-5H
Status: PROTOTYPE

Provides adapter implementations for CAD kernel operations.
The adapter pattern isolates kernel-specific code from the
topology builder, enabling kernel swapping and testing.

Current adapters:
    - MockKernelAdapter: For testing without real CAD kernel
    - (Future) CadQueryAdapter: CadQuery-based operations
    - (Future) Build123dAdapter: build123d-based operations
"""

from .mock_adapter import MockKernelAdapter

__all__ = [
    "MockKernelAdapter",
]
