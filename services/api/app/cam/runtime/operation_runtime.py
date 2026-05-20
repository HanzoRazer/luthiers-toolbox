"""
CAM Operation Runtime Protocol

Dev Order 57: Defines the interface that operation-specific runtimes must implement.
Dev Order 58: Updated to use normalized runtime result contracts.

The runtime consumes intent. It does not redefine intent.
"""

from typing import Protocol, runtime_checkable

from app.cam.runtime.runtime_results import (
    RuntimeExportResult,
    RuntimeGeometryResolution,
    RuntimePlanResult,
    RuntimePreviewResult,
    RuntimeValidationResult,
)
from app.rmos.cam.schemas_intent import CamIntentV1

__all__ = [
    "CamOperationRuntime",
    "RuntimeValidationResult",
    "RuntimeGeometryResolution",
    "RuntimePlanResult",
    "RuntimePreviewResult",
    "RuntimeExportResult",
]


@runtime_checkable
class CamOperationRuntime(Protocol):
    """
    Protocol for CAM operation-specific runtimes.

    Each runtime handles a specific operation type and provides:
    - Validation: Check if intent is valid for this operation
    - Geometry resolution: Resolve geometry from intent
    - Planning: Create operation plan (placeholder for now)
    - Preview: Generate preview data (placeholder for now)
    - Export: Export artifacts (placeholder for now)

    All methods return normalized runtime result contracts from runtime_results.py.

    Invariants:
    - Runtime consumes intent; runtime does not redefine intent
    - Runtime does not generate machine output
    - Runtime does not authorize execution
    - Runtime does not mutate geometry
    - Runtime does not persist RMOS runs
    - All results are observational only
    """

    @property
    def operation_type(self) -> str:
        """The operation type this runtime handles."""
        ...

    @property
    def runtime_id(self) -> str:
        """Unique identifier for this runtime instance."""
        ...

    def validate(self, intent: CamIntentV1) -> RuntimeValidationResult:
        """
        Validate intent for this operation type.

        Returns RuntimeValidationResult with:
        - validation_gate: green/yellow/red
        - execution_ready: always False
        - machine_operation_authorized: always False
        """
        ...

    def resolve_geometry(self, intent: CamIntentV1) -> RuntimeGeometryResolution:
        """
        Resolve geometry from intent.

        Returns RuntimeGeometryResolution with:
        - geometry_resolution_status: resolved/partial/placeholder/unsupported
        - geometry_queries: list of geometry lookups performed
        """
        ...

    def plan(self, intent: CamIntentV1) -> RuntimePlanResult:
        """
        Create operation plan from intent.

        Returns RuntimePlanResult with:
        - planning_stage: placeholder/deterministic_stub/unsupported
        - operation_count: number of planned operations
        """
        ...

    def preview(self, intent: CamIntentV1) -> RuntimePreviewResult:
        """
        Generate preview from intent.

        Returns RuntimePreviewResult with:
        - preview_stage: placeholder/preview_stub/unsupported
        - preview_artifacts: list of preview artifact identifiers
        """
        ...

    def export(self, intent: CamIntentV1) -> RuntimeExportResult:
        """
        Export artifacts from intent.

        Returns RuntimeExportResult with:
        - export_stage: placeholder/export_stub/unsupported
        - machine_output_generated: always False
        """
        ...
