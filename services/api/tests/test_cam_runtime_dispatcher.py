"""
CAM Runtime Dispatcher Tests

Dev Order 57: Tests for the governed runtime dispatcher skeleton.
Dev Order 58: Updated for normalized runtime result contracts.

Test cases:
1. empty registry returns unsupported manifest
2. unsupported manifest is RED
3. execution_ready is always false
4. machine_operation_authorized is always false
5. registered stub plugin is resolved
6. dispatcher preserves intent_id
7. dispatcher preserves operation_type
8. manifest includes provenance
9. registry lists operation types
10. plugin runtime error returns runtime_error manifest without execution authorization
11. dispatcher executes full stage chain (validate, geometry, plan, preview, export)
12. manifest includes result ID references
"""

import pytest
from pydantic import ValidationError

from app.cam.runtime.dispatcher import RuntimeDispatcher, resolve_operation_type
from app.cam.runtime.operation_manifest import (
    OperationManifestV1,
    create_runtime_error_manifest,
    create_unsupported_manifest,
)
from app.cam.runtime.plugin_registry import RuntimePluginRegistry
from app.cam.runtime.runtime_results import (
    RuntimeExportResult,
    RuntimeGeometryResolution,
    RuntimePlanResult,
    RuntimePreviewResult,
    RuntimeValidationResult,
)
from app.rmos.cam.schemas_intent import CamIntentV1, CamModeV1


class StubRuntime:
    """Stub runtime for testing with normalized result contracts."""

    def __init__(
        self,
        operation_type: str = "test_operation",
        runtime_id: str = "stub-runtime-001",
        validation_gate: str = "green",
        raise_on_validate: bool = False,
    ):
        self._operation_type = operation_type
        self._runtime_id = runtime_id
        self._validation_gate = validation_gate
        self._raise_on_validate = raise_on_validate

    @property
    def operation_type(self) -> str:
        return self._operation_type

    @property
    def runtime_id(self) -> str:
        return self._runtime_id

    def validate(self, intent: CamIntentV1) -> RuntimeValidationResult:
        if self._raise_on_validate:
            raise RuntimeError("Simulated runtime error")
        return RuntimeValidationResult(
            status="available" if self._validation_gate != "red" else "error",
            validation_gate=self._validation_gate,
            diagnostics=["Stub validation complete"],
            provenance=[f"stub:{self._runtime_id}:validate"],
        )

    def resolve_geometry(self, intent: CamIntentV1) -> RuntimeGeometryResolution:
        return RuntimeGeometryResolution(
            status="placeholder",
            geometry_resolution_status="placeholder",
            summary="Geometry resolution placeholder",
            diagnostics=["Stub geometry resolution"],
            provenance=[f"stub:{self._runtime_id}:geometry"],
        )

    def plan(self, intent: CamIntentV1) -> RuntimePlanResult:
        return RuntimePlanResult(
            status="placeholder",
            planning_stage="placeholder",
            summary="Planning placeholder",
            diagnostics=["Stub planning"],
            provenance=[f"stub:{self._runtime_id}:plan"],
        )

    def preview(self, intent: CamIntentV1) -> RuntimePreviewResult:
        return RuntimePreviewResult(
            status="placeholder",
            preview_stage="placeholder",
            summary="Preview placeholder",
            diagnostics=["Stub preview"],
            provenance=[f"stub:{self._runtime_id}:preview"],
        )

    def export(self, intent: CamIntentV1) -> RuntimeExportResult:
        return RuntimeExportResult(
            status="placeholder",
            export_stage="placeholder",
            summary="Export placeholder",
            diagnostics=["Stub export"],
            provenance=[f"stub:{self._runtime_id}:export"],
        )


def make_test_intent(
    operation: str | None = None,
    intent_id: str | None = "test-intent-001",
    mode: CamModeV1 = CamModeV1.ROUTER_3AXIS,
) -> CamIntentV1:
    """Create a test intent."""
    design = {"geometry": {"type": "test"}}
    if operation:
        design["operation"] = operation
    return CamIntentV1(
        intent_id=intent_id,
        mode=mode,
        design=design,
    )


class TestResolveOperationType:
    """Tests for operation type resolution."""

    def test_uses_design_operation_if_present(self):
        intent = make_test_intent(operation="custom_operation")
        assert resolve_operation_type(intent) == "custom_operation"

    def test_falls_back_to_mode_value(self):
        intent = make_test_intent(operation=None, mode=CamModeV1.SAW)
        assert resolve_operation_type(intent) == "saw"


class TestRuntimePluginRegistry:
    """Tests for RuntimePluginRegistry."""

    def test_empty_registry_returns_none(self):
        registry = RuntimePluginRegistry()
        assert registry.get("nonexistent") is None

    def test_register_and_retrieve(self):
        registry = RuntimePluginRegistry()
        stub = StubRuntime(operation_type="test_op")
        registry.register(stub)
        assert registry.get("test_op") is stub

    def test_list_operation_types(self):
        registry = RuntimePluginRegistry()
        registry.register(StubRuntime(operation_type="alpha"))
        registry.register(StubRuntime(operation_type="beta", runtime_id="beta-001"))
        types = registry.list_operation_types()
        assert types == ["alpha", "beta"]

    def test_duplicate_registration_raises(self):
        registry = RuntimePluginRegistry()
        registry.register(StubRuntime(operation_type="test_op"))
        with pytest.raises(ValueError, match="already registered"):
            registry.register(StubRuntime(operation_type="test_op", runtime_id="other"))

    def test_clear_removes_all_plugins(self):
        registry = RuntimePluginRegistry()
        registry.register(StubRuntime(operation_type="test_op"))
        assert len(registry) == 1
        registry.clear()
        assert len(registry) == 0


class TestRuntimeDispatcher:
    """Tests for RuntimeDispatcher."""

    def test_empty_registry_returns_unsupported_manifest(self):
        """Test 1: empty registry returns unsupported manifest."""
        registry = RuntimePluginRegistry()
        dispatcher = RuntimeDispatcher(registry)
        intent = make_test_intent(operation="unknown_operation")
        manifest = dispatcher.dispatch(intent)
        assert manifest.dispatch_status == "unsupported_operation"

    def test_unsupported_manifest_is_red(self):
        """Test 2: unsupported manifest is RED."""
        registry = RuntimePluginRegistry()
        dispatcher = RuntimeDispatcher(registry)
        intent = make_test_intent()
        manifest = dispatcher.dispatch(intent)
        assert manifest.validation_gate == "red"

    def test_execution_ready_always_false(self):
        """Test 3: execution_ready is always false."""
        registry = RuntimePluginRegistry()
        registry.register(StubRuntime())
        dispatcher = RuntimeDispatcher(registry)
        intent = make_test_intent(operation="test_operation")
        manifest = dispatcher.dispatch(intent)
        assert manifest.execution_ready is False

    def test_machine_operation_authorized_always_false(self):
        """Test 4: machine_operation_authorized is always false."""
        registry = RuntimePluginRegistry()
        registry.register(StubRuntime())
        dispatcher = RuntimeDispatcher(registry)
        intent = make_test_intent(operation="test_operation")
        manifest = dispatcher.dispatch(intent)
        assert manifest.machine_operation_authorized is False

    def test_registered_stub_plugin_is_resolved(self):
        """Test 5: registered stub plugin is resolved."""
        registry = RuntimePluginRegistry()
        stub = StubRuntime(operation_type="stub_op", runtime_id="stub-001")
        registry.register(stub)
        dispatcher = RuntimeDispatcher(registry)
        intent = make_test_intent(operation="stub_op")
        manifest = dispatcher.dispatch(intent)
        assert manifest.runtime_id == "stub-001"
        assert manifest.dispatch_status != "unsupported_operation"

    def test_dispatcher_preserves_intent_id(self):
        """Test 6: dispatcher preserves intent_id."""
        registry = RuntimePluginRegistry()
        registry.register(StubRuntime(operation_type="test_op"))
        dispatcher = RuntimeDispatcher(registry)
        intent = make_test_intent(operation="test_op", intent_id="my-custom-id")
        manifest = dispatcher.dispatch(intent)
        assert manifest.intent_id == "my-custom-id"

    def test_dispatcher_preserves_operation_type(self):
        """Test 7: dispatcher preserves operation_type."""
        registry = RuntimePluginRegistry()
        registry.register(StubRuntime(operation_type="preserved_op"))
        dispatcher = RuntimeDispatcher(registry)
        intent = make_test_intent(operation="preserved_op")
        manifest = dispatcher.dispatch(intent)
        assert manifest.operation_type == "preserved_op"

    def test_manifest_includes_provenance(self):
        """Test 8: manifest includes provenance."""
        registry = RuntimePluginRegistry()
        registry.register(StubRuntime(runtime_id="provenance-test"))
        dispatcher = RuntimeDispatcher(registry)
        intent = make_test_intent(operation="test_operation")
        manifest = dispatcher.dispatch(intent)
        assert len(manifest.provenance) > 0
        assert any("provenance-test" in p for p in manifest.provenance)

    def test_registry_lists_operation_types(self):
        """Test 9: registry lists operation types."""
        registry = RuntimePluginRegistry()
        registry.register(StubRuntime(operation_type="op_a"))
        registry.register(StubRuntime(operation_type="op_b", runtime_id="b"))
        dispatcher = RuntimeDispatcher(registry)
        types = dispatcher.registry.list_operation_types()
        assert "op_a" in types
        assert "op_b" in types

    def test_plugin_runtime_error_returns_error_manifest(self):
        """Test 10: plugin runtime error returns runtime_error manifest without execution authorization."""
        registry = RuntimePluginRegistry()
        registry.register(
            StubRuntime(
                operation_type="error_op",
                runtime_id="error-runtime",
                raise_on_validate=True,
            )
        )
        dispatcher = RuntimeDispatcher(registry)
        intent = make_test_intent(operation="error_op")
        manifest = dispatcher.dispatch(intent)
        assert manifest.dispatch_status == "runtime_error"
        assert manifest.validation_gate == "red"
        assert manifest.execution_ready is False
        assert manifest.machine_operation_authorized is False

    def test_dispatcher_executes_full_stage_chain(self):
        """Test 11: dispatcher executes full stage chain."""
        registry = RuntimePluginRegistry()
        registry.register(StubRuntime(operation_type="full_chain"))
        dispatcher = RuntimeDispatcher(registry)
        intent = make_test_intent(operation="full_chain")
        manifest = dispatcher.dispatch(intent)

        # Check all stages were executed (via provenance)
        provenance_str = " ".join(manifest.provenance)
        assert "validated" in provenance_str
        assert "geometry" in provenance_str
        assert "planned" in provenance_str
        assert "preview" in provenance_str
        assert "export" in provenance_str

        # Check artifacts for all stages
        artifact_types = [a.artifact_type for a in manifest.artifacts]
        assert "validation_report" in artifact_types
        assert "geometry_resolution" in artifact_types
        assert "plan_placeholder" in artifact_types
        assert "preview_placeholder" in artifact_types
        assert "export_placeholder" in artifact_types

    def test_manifest_includes_result_id_references(self):
        """Test 12: manifest includes result ID references."""
        registry = RuntimePluginRegistry()
        registry.register(StubRuntime(operation_type="result_ids"))
        dispatcher = RuntimeDispatcher(registry)
        intent = make_test_intent(operation="result_ids")
        manifest = dispatcher.dispatch(intent)

        # All result IDs should be populated
        assert manifest.validation_result_id is not None
        assert manifest.validation_result_id.startswith("rr_")
        assert manifest.geometry_result_id is not None
        assert manifest.geometry_result_id.startswith("rr_")
        assert manifest.plan_result_id is not None
        assert manifest.plan_result_id.startswith("rr_")
        assert manifest.preview_result_id is not None
        assert manifest.preview_result_id.startswith("rr_")
        assert manifest.export_result_id is not None
        assert manifest.export_result_id.startswith("rr_")


class TestOperationManifestV1:
    """Tests for OperationManifestV1 invariants."""

    def test_cannot_set_execution_ready_true(self):
        """Verify execution_ready cannot be set to True."""
        with pytest.raises(ValidationError):
            OperationManifestV1(
                operation_type="test",
                dispatch_status="validated_only",
                validation_gate="green",
                execution_ready=True,
            )

    def test_cannot_set_machine_operation_authorized_true(self):
        """Verify machine_operation_authorized cannot be set to True."""
        with pytest.raises(ValidationError):
            OperationManifestV1(
                operation_type="test",
                dispatch_status="validated_only",
                validation_gate="green",
                machine_operation_authorized=True,
            )

    def test_unsupported_manifest_helper(self):
        """Test create_unsupported_manifest helper."""
        manifest = create_unsupported_manifest(
            operation_type="unknown",
            intent_id="test-id",
            reason="Custom reason",
        )
        assert manifest.dispatch_status == "unsupported_operation"
        assert manifest.validation_gate == "red"
        assert manifest.intent_id == "test-id"
        assert "Custom reason" in manifest.diagnostics[0]

    def test_runtime_error_manifest_helper(self):
        """Test create_runtime_error_manifest helper."""
        manifest = create_runtime_error_manifest(
            operation_type="failed",
            runtime_id="failing-runtime",
            intent_id="test-id",
            error="Something broke",
        )
        assert manifest.dispatch_status == "runtime_error"
        assert manifest.validation_gate == "red"
        assert manifest.runtime_id == "failing-runtime"
        assert manifest.execution_ready is False
        assert manifest.machine_operation_authorized is False
