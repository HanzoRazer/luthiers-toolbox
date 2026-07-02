"""
Tests for CAM Operation Capability Registry (CAM Dev Order 6H)

Tests the operation self-description and lifecycle introspection system.

Core principle: Operations are self-describing governed capabilities.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.cam.cam_operation_registry import (
    CAM_OPERATION_REGISTRY,
    CAMOperationCapability,
    get_operation_capability,
    list_supported_operations,
    list_governed_operations,
    list_lifecycle_supported_operations,
    list_exportable_operations,
    get_all_capabilities,
)
from app.cam.export_lifecycle_orchestrator import (
    run_governed_export_lifecycle,
    GovernedExportLifecycleRequest,
    PreviewRequestWrapper,
)
from app.cam.dxf_translator_boundary import DXFTranslatorProfile
from app.cam.postprocessor_boundary import MachineProfileValidationOnly
from app.cam.translator_capability_registry import (
    list_translators_for_operation,
    list_translators_by_output_class,
)
from app.cam.export_object_to_dxf_adapter import validate_translator_registry


client = TestClient(app)


def _registered_translator_id_for(operation: str) -> str:
    """Resolve a real, registry-valid translator id for a lifecycle request.

    7C ``validate_translator_registry`` rejects unregistered ids, so a synthetic
    ``"test_translator"`` fails the lifecycle's translator stage on identity
    rather than exercising the operation. Resolve from the capability registry
    instead of hardcoding one id: prefer a translator that declares ``operation``,
    else fall back to any registry-valid DXF translator (so operation-agnostic
    cases like an unregistered operation still construct a valid request and RED
    for the right reason). This keeps the test resilient to registry churn — a
    rename/disable of any single translator no longer breaks it, because it
    asserts the lifecycle reflects the operation, not one hardcoded identity.
    """
    candidates = list(list_translators_for_operation(operation)) or list(
        list_translators_by_output_class("dxf")
    )
    for cap in candidates:
        _, issues = validate_translator_registry(cap.translator_id)
        if not issues:
            return cap.translator_id
    pytest.skip(
        f"No registry-valid DXF translator available for operation '{operation}'"
    )


# -----------------------------------------------------------------------------
# Registry Contents Tests
# -----------------------------------------------------------------------------

class TestRegistryContents:
    """Tests verifying registry contains expected operations."""

    def test_nut_slot_present(self):
        """nut_slot is registered."""
        assert "nut_slot" in CAM_OPERATION_REGISTRY

    def test_drilling_present(self):
        """drilling is registered."""
        assert "drilling" in CAM_OPERATION_REGISTRY

    def test_unsupported_operation_returns_none(self):
        """Unsupported operation returns None."""
        cap = get_operation_capability("unknown_operation")
        assert cap is None

    def test_list_supported_operations(self):
        """list_supported_operations returns registered operations."""
        ops = list_supported_operations()
        assert "nut_slot" in ops
        assert "drilling" in ops

    def test_list_governed_operations(self):
        """list_governed_operations returns governed/canonical operations."""
        ops = list_governed_operations()
        assert "nut_slot" in ops
        assert "drilling" in ops

    def test_list_lifecycle_supported_operations(self):
        """list_lifecycle_supported_operations returns lifecycle-enabled ops."""
        ops = list_lifecycle_supported_operations()
        assert "nut_slot" in ops
        assert "drilling" in ops

    def test_list_exportable_operations(self):
        """list_exportable_operations returns export-enabled ops."""
        ops = list_exportable_operations()
        assert "nut_slot" in ops
        assert "drilling" in ops

    def test_get_all_capabilities(self):
        """get_all_capabilities returns all registered capabilities."""
        caps = get_all_capabilities()
        assert len(caps) >= 2
        ops = [c.operation for c in caps]
        assert "nut_slot" in ops
        assert "drilling" in ops


# -----------------------------------------------------------------------------
# Safety Assertion Tests
# -----------------------------------------------------------------------------

class TestSafetyAssertions:
    """Tests verifying safety constraints in 6H."""

    def test_machine_ready_always_false(self):
        """machine_ready is False for all operations."""
        for op, cap in CAM_OPERATION_REGISTRY.items():
            assert cap.machine_ready is False, f"{op} has machine_ready=True"

    def test_machine_output_supported_always_false(self):
        """machine_output_supported is False for all operations."""
        for op, cap in CAM_OPERATION_REGISTRY.items():
            assert cap.machine_output_supported is False, f"{op} has machine_output_supported=True"


# -----------------------------------------------------------------------------
# Maturity and Exportability Tests
# -----------------------------------------------------------------------------

class TestMaturityAndExportability:
    """Tests verifying maturity and exportability classifications."""

    def test_maturity_values_valid(self):
        """All maturity values are valid."""
        valid_maturities = {"experimental", "candidate", "governed", "canonical"}
        for op, cap in CAM_OPERATION_REGISTRY.items():
            assert cap.maturity in valid_maturities, f"{op} has invalid maturity: {cap.maturity}"

    def test_exportability_class_values_valid(self):
        """All exportability_class values are valid."""
        valid_classes = {"preview_only", "governed_export", "translator_ready", "machine_candidate"}
        for op, cap in CAM_OPERATION_REGISTRY.items():
            assert cap.exportability_class in valid_classes, f"{op} has invalid exportability_class"

    def test_nut_slot_is_canonical(self):
        """nut_slot has canonical maturity."""
        cap = get_operation_capability("nut_slot")
        assert cap.maturity == "canonical"

    def test_drilling_is_canonical(self):
        """drilling has canonical maturity."""
        cap = get_operation_capability("drilling")
        assert cap.maturity == "canonical"


# -----------------------------------------------------------------------------
# Capability Schema Tests
# -----------------------------------------------------------------------------

class TestCapabilitySchema:
    """Tests verifying capability schema is complete."""

    def test_nut_slot_has_preview_route(self):
        """nut_slot has preview route defined."""
        cap = get_operation_capability("nut_slot")
        assert cap.preview_route is not None
        assert "/preview" in cap.preview_route

    def test_drilling_has_preview_route(self):
        """drilling has preview route defined."""
        cap = get_operation_capability("drilling")
        assert cap.preview_route is not None
        assert "/preview" in cap.preview_route

    def test_lifecycle_route_defined(self):
        """Lifecycle route is defined for lifecycle-supported operations."""
        for op, cap in CAM_OPERATION_REGISTRY.items():
            if cap.lifecycle_supported:
                assert cap.lifecycle_route is not None, f"{op} missing lifecycle_route"

    def test_nut_slot_geometry_types(self):
        """nut_slot declares supported geometry types."""
        cap = get_operation_capability("nut_slot")
        assert "polyline" in cap.supported_geometry_types or "line" in cap.supported_geometry_types

    def test_drilling_geometry_types(self):
        """drilling declares circle geometry type."""
        cap = get_operation_capability("drilling")
        assert "circle" in cap.supported_geometry_types

    def test_required_translator_features_populated(self):
        """Required translator features are populated."""
        for op, cap in CAM_OPERATION_REGISTRY.items():
            if cap.translator_validation_supported:
                assert len(cap.required_translator_features) > 0, f"{op} missing translator features"


# -----------------------------------------------------------------------------
# Endpoint Tests
# -----------------------------------------------------------------------------

class TestCapabilityEndpoints:
    """Tests for capability introspection endpoints."""

    def test_list_capabilities_returns_200(self):
        """GET /api/cam/lifecycle/capabilities returns 200."""
        response = client.get("/api/cam/lifecycle/capabilities")
        assert response.status_code == 200

    def test_list_capabilities_has_operations(self):
        """Capabilities response contains operations list."""
        response = client.get("/api/cam/lifecycle/capabilities")
        data = response.json()
        assert "operations" in data
        assert len(data["operations"]) >= 2

    def test_list_capabilities_has_counts(self):
        """Capabilities response contains count fields."""
        response = client.get("/api/cam/lifecycle/capabilities")
        data = response.json()
        assert "total_count" in data
        assert "lifecycle_supported_count" in data
        assert "governed_count" in data
        assert data["total_count"] >= 2

    def test_get_single_capability_nut_slot(self):
        """GET /api/cam/lifecycle/capabilities/nut_slot returns capability."""
        response = client.get("/api/cam/lifecycle/capabilities/nut_slot")
        assert response.status_code == 200
        data = response.json()
        assert data["operation"] == "nut_slot"
        assert data["lifecycle_supported"] is True

    def test_get_single_capability_drilling(self):
        """GET /api/cam/lifecycle/capabilities/drilling returns capability."""
        response = client.get("/api/cam/lifecycle/capabilities/drilling")
        assert response.status_code == 200
        data = response.json()
        assert data["operation"] == "drilling"
        assert data["lifecycle_supported"] is True

    def test_get_unknown_capability_returns_404(self):
        """GET /api/cam/lifecycle/capabilities/unknown returns 404."""
        response = client.get("/api/cam/lifecycle/capabilities/unknown_op")
        assert response.status_code == 404

    def test_supported_operations_endpoint(self):
        """GET /api/cam/lifecycle/supported-operations returns list."""
        response = client.get("/api/cam/lifecycle/supported-operations")
        assert response.status_code == 200
        data = response.json()
        assert "nut_slot" in data
        assert "drilling" in data

    def test_capabilities_summary_endpoint(self):
        """GET /api/cam/lifecycle/capabilities/summary returns summary."""
        response = client.get("/api/cam/lifecycle/capabilities/summary")
        assert response.status_code == 200
        data = response.json()
        assert "operations" in data
        for op in data["operations"]:
            assert "operation" in op
            assert "maturity" in op
            assert "machine_ready" in op


# -----------------------------------------------------------------------------
# Lifecycle Dispatcher Integration Tests
# -----------------------------------------------------------------------------

class TestLifecycleDispatcherIntegration:
    """Tests verifying lifecycle dispatcher uses registry."""

    def _create_lifecycle_request(self, operation: str) -> GovernedExportLifecycleRequest:
        """Create a lifecycle request for testing."""
        if operation == "nut_slot":
            payload = {
                "nut_width_mm": 50.0,
                "num_strings": 6,
                "edge_offset_bass_mm": 4.0,
                "edge_offset_treble_mm": 4.0,
                "slot_length_mm": 4.5,
                "slot_depth_mm": 1.5,
                "slot_width_mm": 0.70,
                "stock_thickness_mm": 9.5,
                "tool_diameter_mm": 0.56,
                "safe_z_mm": 5.0,
            }
        elif operation == "drilling":
            payload = {
                "holes": [
                    {"x_mm": 10.0, "y_mm": 10.0, "diameter_mm": 5.0, "depth_mm": 8.0},
                ],
                "stock_thickness_mm": 20.0,
            }
        else:
            payload = {}

        return GovernedExportLifecycleRequest(
            preview_request=PreviewRequestWrapper(
                operation=operation,
                payload=payload,
            ),
            machine_profile=MachineProfileValidationOnly(
                machine_profile_id="test_machine",
                controller="none",
                units="mm",
                supported_operations=[operation, "pocket"],
                axis_count=3,
                work_envelope_mm={"x": 300, "y": 300, "z": 50},
            ),
            translator_profile=DXFTranslatorProfile(
                # 7C validate_translator_registry rejects unregistered ids. Resolve
                # a real registered translator from the capability registry (not a
                # hardcoded id) so the lifecycle's translator stage passes and the
                # gate reflects the operation, not a synthetic-id rejection or a
                # single translator's identity. See _registered_translator_id_for.
                translator_id=_registered_translator_id_for(operation),
                supported_geometry_types=["line", "polyline", "circle", "arc"],
                supports_layers=True,
                units="mm",
            ),
        )

    def test_registered_operation_works(self):
        """Registered operation is processed by lifecycle."""
        request = self._create_lifecycle_request("nut_slot")
        report = run_governed_export_lifecycle(request)
        assert report.lifecycle_gate in ["green", "yellow"]

    def test_unregistered_operation_returns_red(self):
        """Unregistered operation returns RED from dispatcher."""
        request = self._create_lifecycle_request("unregistered_op")
        report = run_governed_export_lifecycle(request)
        assert report.lifecycle_gate == "red"
        assert any("not found" in issue for issue in report.blocking_issues)

    def test_dispatcher_checks_registry(self):
        """Dispatcher validates against registry, not hardcoded list."""
        # Both nut_slot and drilling should be in registry
        nut_slot_cap = get_operation_capability("nut_slot")
        drilling_cap = get_operation_capability("drilling")

        assert nut_slot_cap is not None
        assert nut_slot_cap.lifecycle_supported is True

        assert drilling_cap is not None
        assert drilling_cap.lifecycle_supported is True

        # Verify they work in lifecycle
        for op in ["nut_slot", "drilling"]:
            request = self._create_lifecycle_request(op)
            report = run_governed_export_lifecycle(request)
            assert report.preview_operation == op
