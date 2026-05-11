"""
Tests for Drilling Export Lifecycle (CAM Dev Order 6G)

Tests drilling integration with the governed export lifecycle pipeline.
Proves the lifecycle architecture is operation-extensible.

Core rule: Orchestration only, no output generation.
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.cam.dxf_translator_boundary import DXFTranslatorProfile
from app.cam.drilling_export import create_drilling_export_object
from app.cam.export_lifecycle_orchestrator import (
    GovernedExportLifecycleRequest,
    PreviewRequestWrapper,
    run_governed_export_lifecycle,
)
from app.cam.cam_operation_registry import list_lifecycle_supported_operations
from app.cam.postprocessor_boundary import MachineProfileValidationOnly
from app.cam.routers.drilling.drilling_preview_router import (
    DrillingPreviewRequest,
    DrillHoleInput,
    generate_drilling_preview,
)


client = TestClient(app)


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------

def create_valid_drilling_holes() -> list:
    """Create valid drilling hole inputs."""
    return [
        {"x_mm": 10.0, "y_mm": 10.0, "diameter_mm": 5.0, "depth_mm": 8.0, "label": "hole_1"},
        {"x_mm": 30.0, "y_mm": 10.0, "diameter_mm": 5.0, "depth_mm": 8.0, "label": "hole_2"},
        {"x_mm": 50.0, "y_mm": 10.0, "diameter_mm": 5.0, "depth_mm": 8.0, "label": "hole_3"},
    ]


def create_drilling_preview_request() -> PreviewRequestWrapper:
    """Create a drilling preview request wrapper."""
    return PreviewRequestWrapper(
        operation="drilling",
        payload={
            "holes": create_valid_drilling_holes(),
            "stock_thickness_mm": 20.0,
            "stock_width_mm": 100.0,
            "stock_height_mm": 50.0,
            "min_edge_distance_mm": 3.0,
        },
    )


def create_compatible_machine_profile() -> MachineProfileValidationOnly:
    """Create a machine profile compatible with drilling."""
    return MachineProfileValidationOnly(
        machine_profile_id="test_3axis_drill",
        controller="none",
        units="mm",
        supported_operations=["drilling", "pocket", "nut_slot"],
        axis_count=3,
        work_envelope_mm={"x": 300, "y": 300, "z": 50},
    )


def create_compatible_translator_profile() -> DXFTranslatorProfile:
    """Create a translator profile compatible with drilling geometry."""
    return DXFTranslatorProfile(
        translator_id="generic_dxf_r14_validation_only",
        supported_geometry_types=["line", "polyline", "arc", "circle"],
        supports_layers=True,
        supports_blocks=False,
        supports_splines=False,
        units="mm",
    )


def create_drilling_lifecycle_request(persist: bool = False) -> GovernedExportLifecycleRequest:
    """Create a full drilling lifecycle request."""
    return GovernedExportLifecycleRequest(
        preview_request=create_drilling_preview_request(),
        machine_profile=create_compatible_machine_profile(),
        translator_profile=create_compatible_translator_profile(),
        persist_to_rmos=persist,
    )


# -----------------------------------------------------------------------------
# Dispatcher Extension Tests
# -----------------------------------------------------------------------------

class TestDrillingInSupportedOperations:
    """Tests verifying drilling is in supported operations."""

    def test_drilling_in_supported_operations(self):
        """Drilling is listed in lifecycle-supported operations."""
        supported = list_lifecycle_supported_operations()
        assert "drilling" in supported

    def test_nut_slot_still_supported(self):
        """Nut slot remains supported (no regression)."""
        supported = list_lifecycle_supported_operations()
        assert "nut_slot" in supported

    def test_unsupported_operation_returns_red(self):
        """Unsupported operation still returns RED."""
        request = create_drilling_lifecycle_request()
        request.preview_request.operation = "unknown_op"

        report = run_governed_export_lifecycle(request)

        assert report.lifecycle_gate == "red"
        assert any("Unsupported lifecycle operation" in issue for issue in report.blocking_issues)


# -----------------------------------------------------------------------------
# Drilling Preview Tests
# -----------------------------------------------------------------------------

class TestDrillingPreview:
    """Tests for drilling preview generation."""

    def test_valid_drilling_preview_returns_green(self):
        """Valid drilling preview returns GREEN gate."""
        request = DrillingPreviewRequest(
            holes=[DrillHoleInput(**h) for h in create_valid_drilling_holes()],
            stock_thickness_mm=20.0,
            stock_width_mm=100.0,
            stock_height_mm=50.0,
        )

        preview = generate_drilling_preview(request)

        assert preview.gate.value == "green"
        assert len(preview.errors) == 0

    def test_overlapping_holes_returns_red(self):
        """Overlapping holes return RED gate."""
        holes = [
            DrillHoleInput(x_mm=10.0, y_mm=10.0, diameter_mm=10.0, depth_mm=5.0),
            DrillHoleInput(x_mm=12.0, y_mm=10.0, diameter_mm=10.0, depth_mm=5.0),
        ]
        request = DrillingPreviewRequest(holes=holes, stock_thickness_mm=20.0)

        preview = generate_drilling_preview(request)

        assert preview.gate.value == "red"
        assert any("overlap" in e.lower() for e in preview.errors)


# -----------------------------------------------------------------------------
# Drilling Export Object Tests
# -----------------------------------------------------------------------------

class TestDrillingExportObject:
    """Tests for drilling export object generation."""

    def test_drilling_export_object_generated(self):
        """Drilling export object is generated from preview."""
        request = DrillingPreviewRequest(
            holes=[DrillHoleInput(**h) for h in create_valid_drilling_holes()],
            stock_thickness_mm=20.0,
            stock_width_mm=100.0,
            stock_height_mm=50.0,
        )
        preview = generate_drilling_preview(request)

        export_obj = create_drilling_export_object(preview, request)

        assert export_obj is not None
        assert export_obj.export_id.startswith("EXP-DRILL-")

    def test_drilling_export_has_hole_entities(self):
        """Drilling export object has hole geometry entities."""
        request = DrillingPreviewRequest(
            holes=[DrillHoleInput(**h) for h in create_valid_drilling_holes()],
            stock_thickness_mm=20.0,
        )
        preview = generate_drilling_preview(request)
        export_obj = create_drilling_export_object(preview, request)

        assert len(export_obj.geometry.entities) == 3
        for entity in export_obj.geometry.entities:
            assert entity.type == "hole"

    def test_drilling_export_has_toolpath_operations(self):
        """Drilling export object has toolpath operations."""
        request = DrillingPreviewRequest(
            holes=[DrillHoleInput(**h) for h in create_valid_drilling_holes()],
            stock_thickness_mm=20.0,
        )
        preview = generate_drilling_preview(request)
        export_obj = create_drilling_export_object(preview, request)

        assert len(export_obj.toolpaths.operations) == 3
        for op in export_obj.toolpaths.operations:
            assert op.operation_type == "drill"

    def test_drilling_intent_is_drilling(self):
        """Drilling export object has drilling intent."""
        request = DrillingPreviewRequest(
            holes=[DrillHoleInput(**h) for h in create_valid_drilling_holes()],
            stock_thickness_mm=20.0,
        )
        preview = generate_drilling_preview(request)
        export_obj = create_drilling_export_object(preview, request)

        assert export_obj.intent.operation_type == "drilling"


# -----------------------------------------------------------------------------
# Drilling Lifecycle Tests
# -----------------------------------------------------------------------------

class TestDrillingLifecycle:
    """Tests for drilling lifecycle orchestration."""

    def test_valid_drilling_lifecycle_returns_green(self):
        """Valid drilling lifecycle request returns GREEN."""
        request = create_drilling_lifecycle_request()
        report = run_governed_export_lifecycle(request)

        assert report.lifecycle_gate == "green"
        assert report.export_ready is True
        assert len(report.blocking_issues) == 0

    def test_drilling_preview_gate_populated(self):
        """Drilling preview gate is populated."""
        request = create_drilling_lifecycle_request()
        report = run_governed_export_lifecycle(request)

        assert report.preview_gate in ["green", "yellow", "red"]
        assert report.preview_operation == "drilling"

    def test_drilling_export_object_summary_populated(self):
        """Drilling export object summary is populated."""
        request = create_drilling_lifecycle_request()
        report = run_governed_export_lifecycle(request)

        assert report.export_object_summary is not None
        assert "drill" in report.export_object_summary.operation.lower()
        assert report.export_object_summary.entity_count == 3

    def test_drilling_machine_validation_populated(self):
        """Machine validation is populated for drilling."""
        request = create_drilling_lifecycle_request()
        report = run_governed_export_lifecycle(request)

        assert report.machine_validation_gate is not None
        assert report.machine_validation_compatible is not None

    def test_drilling_translator_validation_populated(self):
        """Translator validation is populated for drilling."""
        request = create_drilling_lifecycle_request()
        report = run_governed_export_lifecycle(request)

        assert report.translator_validation_gate is not None
        assert report.translator_validation_compatible is not None


# -----------------------------------------------------------------------------
# Compatibility Tests
# -----------------------------------------------------------------------------

class TestDrillingCompatibility:
    """Tests for drilling compatibility validation."""

    def test_machine_without_drilling_returns_red(self):
        """Machine without drilling support returns RED."""
        request = create_drilling_lifecycle_request()
        request.machine_profile.supported_operations = ["pocket", "profile"]

        report = run_governed_export_lifecycle(request)

        assert report.lifecycle_gate == "red"
        assert any("[Machine]" in issue for issue in report.blocking_issues)

    def test_translator_without_circle_returns_red(self):
        """Translator without circle support returns RED for drilling."""
        request = create_drilling_lifecycle_request()
        request.translator_profile.supported_geometry_types = ["line", "polyline"]

        report = run_governed_export_lifecycle(request)

        assert report.lifecycle_gate == "red"
        assert any("[Translator]" in issue for issue in report.blocking_issues)

    def test_preview_red_propagates(self):
        """Preview RED propagates to lifecycle gate."""
        request = create_drilling_lifecycle_request()
        # Create overlapping holes to trigger RED
        request.preview_request.payload["holes"] = [
            {"x_mm": 10.0, "y_mm": 10.0, "diameter_mm": 10.0, "depth_mm": 5.0},
            {"x_mm": 12.0, "y_mm": 10.0, "diameter_mm": 10.0, "depth_mm": 5.0},
        ]

        report = run_governed_export_lifecycle(request)

        assert report.preview_gate == "red"
        assert report.lifecycle_gate == "red"


# -----------------------------------------------------------------------------
# RMOS Persistence Tests
# -----------------------------------------------------------------------------

class TestDrillingRMOSPersistence:
    """Tests for drilling RMOS persistence."""

    @patch("app.cam.export_rmos_artifacts.put_json_attachment")
    def test_drilling_rmos_persistence_works(self, mock_put):
        """RMOS persistence works for drilling artifacts."""
        mock_put.return_value = (
            MagicMock(size_bytes=1000),
            "/fake/path",
            "abc123" + "0" * 58,
        )

        request = create_drilling_lifecycle_request(persist=True)
        report = run_governed_export_lifecycle(request)

        assert report.rmos.persisted is True
        assert report.rmos.run_id is not None
        assert len(report.rmos.artifacts) == 2  # export object + lifecycle report

    def test_drilling_no_persist_by_default(self):
        """Drilling does not persist by default."""
        request = create_drilling_lifecycle_request(persist=False)
        report = run_governed_export_lifecycle(request)

        assert report.rmos.persisted is False


# -----------------------------------------------------------------------------
# Safety Assertion Tests
# -----------------------------------------------------------------------------

class TestDrillingSafetyAssertions:
    """Tests verifying no machine output generated."""

    def test_machine_output_generated_always_false(self):
        """machine_output_generated is always false for drilling."""
        request = create_drilling_lifecycle_request()
        report = run_governed_export_lifecycle(request)

        assert report.machine_output_generated is False

    def test_translator_output_generated_always_false(self):
        """translator_output_generated is always false for drilling."""
        request = create_drilling_lifecycle_request()
        report = run_governed_export_lifecycle(request)

        assert report.translator_output_generated is False

    def test_machine_ready_always_false(self):
        """machine_ready is always false for drilling."""
        request = create_drilling_lifecycle_request()
        report = run_governed_export_lifecycle(request)

        assert report.machine_ready is False

    def test_no_gcode_tokens_in_response(self):
        """Response does not contain G-code tokens."""
        request = create_drilling_lifecycle_request()
        report = run_governed_export_lifecycle(request)

        report_json = report.model_dump_json()
        forbidden = ["G81", "G83", "G0 ", "G1 ", "M3 ", "M5 "]
        for token in forbidden:
            assert token not in report_json, f"Found forbidden G-code token: {token}"

    def test_no_dxf_tokens_in_response(self):
        """Response does not contain DXF tokens."""
        request = create_drilling_lifecycle_request()
        report = run_governed_export_lifecycle(request)

        report_json = report.model_dump_json()
        forbidden = ['"SECTION"', '"ENTITIES"', '"CIRCLE"', '"EOF"']
        for token in forbidden:
            assert token not in report_json, f"Found forbidden DXF token: {token}"


# -----------------------------------------------------------------------------
# Endpoint Tests
# -----------------------------------------------------------------------------

class TestDrillingEndpoint:
    """Tests for drilling lifecycle endpoint."""

    def test_drilling_endpoint_returns_200(self):
        """Drilling lifecycle endpoint returns 200."""
        request = create_drilling_lifecycle_request()

        response = client.post(
            "/api/cam/export/lifecycle/validate",
            json=request.model_dump(),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["lifecycle_gate"] == "green"

    def test_drilling_endpoint_response_structure(self):
        """Drilling endpoint response has correct structure."""
        request = create_drilling_lifecycle_request()

        response = client.post(
            "/api/cam/export/lifecycle/validate",
            json=request.model_dump(),
        )

        data = response.json()
        assert "lifecycle_gate" in data
        assert "export_ready" in data
        assert "preview_operation" in data
        assert data["preview_operation"] == "drilling"
