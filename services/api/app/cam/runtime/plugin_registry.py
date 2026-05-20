"""
CAM Runtime Plugin Registry

Dev Order 57: Registry for operation-specific runtime plugins.

The registry provides lookup by operation type.
It does not authorize execution or generate machine output.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.cam.runtime.operation_runtime import CamOperationRuntime


class RuntimePluginRegistry:
    """
    Registry for CAM operation runtime plugins.

    Plugins are registered by operation type and retrieved during dispatch.
    """

    def __init__(self) -> None:
        self._plugins: dict[str, CamOperationRuntime] = {}

    def register(self, runtime: CamOperationRuntime) -> None:
        """
        Register a runtime plugin for its operation type.

        Args:
            runtime: The runtime plugin to register

        Raises:
            ValueError: If a plugin is already registered for this operation type
        """
        op_type = runtime.operation_type
        if op_type in self._plugins:
            raise ValueError(
                f"Runtime plugin already registered for operation_type '{op_type}'"
            )
        self._plugins[op_type] = runtime

    def get(self, operation_type: str) -> CamOperationRuntime | None:
        """
        Get the runtime plugin for an operation type.

        Args:
            operation_type: The operation type to look up

        Returns:
            The runtime plugin, or None if not registered
        """
        return self._plugins.get(operation_type)

    def list_operation_types(self) -> list[str]:
        """
        List all registered operation types.

        Returns:
            Sorted list of registered operation type strings
        """
        return sorted(self._plugins.keys())

    def is_registered(self, operation_type: str) -> bool:
        """Check if an operation type has a registered runtime."""
        return operation_type in self._plugins

    def clear(self) -> None:
        """Clear all registered plugins. Useful for testing."""
        self._plugins.clear()

    def __len__(self) -> int:
        """Return the number of registered plugins."""
        return len(self._plugins)


# Default empty registry instance
DEFAULT_RUNTIME_PLUGIN_REGISTRY = RuntimePluginRegistry()
