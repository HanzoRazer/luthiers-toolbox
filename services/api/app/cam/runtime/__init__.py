"""
CAM Runtime Dispatcher Package

Dev Order 57: Governed runtime dispatcher skeleton.
Dev Order 58: Normalized runtime result contracts.

This package provides the structural foundation for CAM runtime plugins.
It does NOT generate machine output, authorize execution, or persist runs.

Core components:
- RuntimeDispatcher: Routes intents to operation runtimes
- CamOperationRuntime: Protocol for operation-specific runtimes
- RuntimePluginRegistry: Registry for runtime plugins
- OperationManifestV1: Governed dispatch result contract
- RuntimeResultBase: Base class for all runtime results
"""

from app.cam.runtime.dispatcher import RuntimeDispatcher
from app.cam.runtime.operation_manifest import (
    OperationManifestV1,
    RuntimeArtifactV1,
)
from app.cam.runtime.operation_runtime import CamOperationRuntime
from app.cam.runtime.plugin_registry import (
    DEFAULT_RUNTIME_PLUGIN_REGISTRY,
    RuntimePluginRegistry,
)
from app.cam.runtime.runtime_results import (
    RuntimeExportResult,
    RuntimeGeometryResolution,
    RuntimePlanResult,
    RuntimePreviewResult,
    RuntimeResultBase,
    RuntimeValidationResult,
    create_unsupported_export_result,
    create_unsupported_geometry_result,
    create_unsupported_plan_result,
    create_unsupported_preview_result,
    create_unsupported_validation_result,
)

__all__ = [
    # Dispatcher
    "RuntimeDispatcher",
    # Protocol
    "CamOperationRuntime",
    # Registry
    "RuntimePluginRegistry",
    "DEFAULT_RUNTIME_PLUGIN_REGISTRY",
    # Manifest
    "OperationManifestV1",
    "RuntimeArtifactV1",
    # Runtime Results
    "RuntimeResultBase",
    "RuntimeValidationResult",
    "RuntimeGeometryResolution",
    "RuntimePlanResult",
    "RuntimePreviewResult",
    "RuntimeExportResult",
    # Result Factories
    "create_unsupported_validation_result",
    "create_unsupported_geometry_result",
    "create_unsupported_plan_result",
    "create_unsupported_preview_result",
    "create_unsupported_export_result",
]
