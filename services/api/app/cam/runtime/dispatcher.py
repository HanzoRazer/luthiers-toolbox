"""
CAM Runtime Dispatcher

Dev Order 57: Governed runtime dispatcher skeleton.
Dev Order 58: Updated to use normalized runtime result contracts.

The dispatcher routes intents to operation-specific runtimes.
It does NOT:
- Generate machine output
- Authorize execution
- Mutate geometry
- Persist RMOS runs

Invariants:
- Runtime consumes intent; runtime does not redefine intent
- Dispatcher routes runtime interpretation but does not authorize machine execution
- All runtime results are observational only
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from app.cam.runtime.operation_manifest import (
    OperationManifestV1,
    RuntimeArtifactV1,
    create_runtime_error_manifest,
    create_unsupported_manifest,
)
from app.cam.runtime.plugin_registry import (
    DEFAULT_RUNTIME_PLUGIN_REGISTRY,
    RuntimePluginRegistry,
)
from app.rmos.cam.schemas_intent import CamIntentV1

if TYPE_CHECKING:
    from app.cam.runtime.operation_runtime import CamOperationRuntime

logger = logging.getLogger(__name__)


def resolve_operation_type(intent: CamIntentV1) -> str:
    """
    Resolve the operation type from intent.

    Resolution order:
    1. design.operation if present
    2. mode.value as fallback

    This is temporary dispatcher-resolution behavior until
    operation vocabulary is formally typed in a later order.
    """
    if isinstance(intent.design, dict) and intent.design.get("operation"):
        return str(intent.design["operation"])
    return str(intent.mode.value)


class RuntimeDispatcher:
    """
    Routes CAM intents to operation-specific runtimes.

    The dispatcher is the governed host structure that future runtime
    plugins will use. It preserves provenance and enforces invariants.

    Dev Order 58: Full stage chain execution:
    - validate
    - resolve_geometry
    - plan
    - preview
    - export

    Usage:
        registry = RuntimePluginRegistry()
        registry.register(my_runtime_plugin)
        dispatcher = RuntimeDispatcher(registry)
        manifest = dispatcher.dispatch(intent)

    Invariants enforced:
    - execution_ready is always False
    - machine_operation_authorized is always False
    - machine_output_generated is always False
    - No RMOS runs persisted
    - All results are observational only
    """

    def __init__(self, registry: RuntimePluginRegistry | None = None) -> None:
        """
        Initialize dispatcher with a plugin registry.

        Args:
            registry: Plugin registry to use. Defaults to DEFAULT_RUNTIME_PLUGIN_REGISTRY.
        """
        self._registry = registry or DEFAULT_RUNTIME_PLUGIN_REGISTRY

    @property
    def registry(self) -> RuntimePluginRegistry:
        """The plugin registry used by this dispatcher."""
        return self._registry

    def dispatch(self, intent: CamIntentV1) -> OperationManifestV1:
        """
        Dispatch an intent to the appropriate runtime plugin.

        Full stage chain (Dev Order 58):
        1. Resolve operation_type from intent
        2. Look up runtime plugin in registry
        3. If no plugin, return unsupported manifest (RED)
        4. Call plugin validation
        5. Call geometry resolution
        6. Call planning
        7. Call preview
        8. Call export
        9. Return OperationManifestV1

        Args:
            intent: The CAM intent to dispatch

        Returns:
            OperationManifestV1 with dispatch results

        Note:
            Never raises exceptions for business logic.
            Structural validation errors may still raise.
        """
        operation_type = resolve_operation_type(intent)
        intent_id = intent.intent_id

        logger.debug(
            "Dispatching intent %s with operation_type %s",
            intent_id,
            operation_type,
        )

        # Step 2: Look up runtime plugin
        runtime = self._registry.get(operation_type)

        # Step 3: No plugin = unsupported operation
        if runtime is None:
            logger.info(
                "No runtime plugin for operation_type '%s'",
                operation_type,
            )
            return create_unsupported_manifest(
                operation_type=operation_type,
                intent_id=intent_id,
            )

        # Steps 4-8: Execute runtime pipeline
        return self._execute_runtime_pipeline(runtime, intent, operation_type)

    def _execute_runtime_pipeline(
        self,
        runtime: CamOperationRuntime,
        intent: CamIntentV1,
        operation_type: str,
    ) -> OperationManifestV1:
        """
        Execute the full runtime pipeline for a registered plugin.

        Stages: validate → resolve_geometry → plan → preview → export

        Catches runtime errors and returns error manifest without
        execution authorization.
        """
        intent_id = intent.intent_id
        runtime_id = runtime.runtime_id
        provenance: list[str] = [f"dispatcher:routed:{runtime_id}"]
        diagnostics: list[str] = []
        artifacts: list[RuntimeArtifactV1] = []

        # Result ID tracking for manifest
        validation_result_id: str | None = None
        geometry_result_id: str | None = None
        plan_result_id: str | None = None
        preview_result_id: str | None = None
        export_result_id: str | None = None

        try:
            # Stage 1: Validation
            validation_result = runtime.validate(intent)
            validation_result_id = validation_result.result_id
            provenance.append(f"runtime:validated:{runtime_id}")
            diagnostics.extend(validation_result.diagnostics)

            artifacts.append(
                RuntimeArtifactV1(
                    artifact_type="validation_report",
                    status="available" if validation_result.valid else "error",
                    summary=f"Validation: {validation_result.validation_gate}",
                )
            )

            if validation_result.validation_gate == "red":
                return OperationManifestV1(
                    intent_id=intent_id,
                    operation_type=operation_type,
                    runtime_id=runtime_id,
                    dispatch_status="validated_only",
                    validation_gate="red",
                    validation_result_id=validation_result_id,
                    provenance=provenance,
                    diagnostics=diagnostics + validation_result.errors,
                    artifacts=artifacts,
                )

            # Stage 2: Geometry resolution
            geometry_result = runtime.resolve_geometry(intent)
            geometry_result_id = geometry_result.result_id
            provenance.append(f"runtime:geometry:{runtime_id}")
            diagnostics.extend(geometry_result.diagnostics)

            artifacts.append(
                RuntimeArtifactV1(
                    artifact_type="geometry_resolution",
                    status=geometry_result.status,
                    summary=geometry_result.summary or f"Geometry: {geometry_result.geometry_resolution_status}",
                )
            )

            # Stage 3: Planning
            plan_result = runtime.plan(intent)
            plan_result_id = plan_result.result_id
            provenance.append(f"runtime:planned:{runtime_id}")
            diagnostics.extend(plan_result.diagnostics)

            artifacts.append(
                RuntimeArtifactV1(
                    artifact_type="plan_placeholder",
                    status=plan_result.status,
                    summary=plan_result.summary or f"Planning: {plan_result.planning_stage}",
                )
            )

            # Stage 4: Preview
            preview_result = runtime.preview(intent)
            preview_result_id = preview_result.result_id
            provenance.append(f"runtime:preview:{runtime_id}")
            diagnostics.extend(preview_result.diagnostics)

            artifacts.append(
                RuntimeArtifactV1(
                    artifact_type="preview_placeholder",
                    status=preview_result.status,
                    summary=preview_result.summary or f"Preview: {preview_result.preview_stage}",
                )
            )

            # Stage 5: Export
            export_result = runtime.export(intent)
            export_result_id = export_result.result_id
            provenance.append(f"runtime:export:{runtime_id}")
            diagnostics.extend(export_result.diagnostics)

            artifacts.append(
                RuntimeArtifactV1(
                    artifact_type="export_placeholder",
                    status=export_result.status,
                    summary=export_result.summary or f"Export: {export_result.export_stage}",
                )
            )

            # Determine final dispatch status based on planning stage
            dispatch_status = (
                "planned_placeholder"
                if plan_result.planning_stage == "deterministic_stub"
                else "validated_only"
            )

            return OperationManifestV1(
                intent_id=intent_id,
                operation_type=operation_type,
                runtime_id=runtime_id,
                dispatch_status=dispatch_status,
                validation_gate=validation_result.validation_gate,
                validation_result_id=validation_result_id,
                geometry_result_id=geometry_result_id,
                plan_result_id=plan_result_id,
                preview_result_id=preview_result_id,
                export_result_id=export_result_id,
                provenance=provenance,
                diagnostics=diagnostics,
                artifacts=artifacts,
            )

        except Exception as e:
            logger.exception(
                "Runtime error during dispatch for operation_type '%s': %s",
                operation_type,
                e,
            )
            return create_runtime_error_manifest(
                operation_type=operation_type,
                runtime_id=runtime_id,
                intent_id=intent_id,
                error=str(e),
            )
