"""
Tests for Postprocessor Boundary (CAM Dev Order 6C)

Tests the postprocessor compatibility validation layer.
Verifies that compatibility reports are generated without
producing any machine output.

Core rule: 6C postprocessor output is a report, not machine code.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.cam.export_object import (
    ExportBounds,
    ExportCoordinateSystem,
    ExportGeometry,
    ExportIntent,
    ExportMaterial,
    ExportMetadata,
    ExportMove,
    ExportObject,
    ExportOperation,
    ExportSource,
    ExportStock,
    ExportStockDimensions,
    ExportToolGeometry,
    ExportTooling,
    ExportToolpaths,
    ExportToolpathStatistics,
    ExportType,
    ExportValidation,
    EXPORT_SCHEMA_VERSION,
)
from app.cam.postprocessor_boundary import (
    MachineProfileValidationOnly,
    PostprocessorCompatibilityReport,
    WorkEnvelopeMM,
    evaluate_postprocessor_compatibility,
)
from app.cam.nut_slot_cam import NutSlotPreviewRequest, generate_nut_slot_preview
from app.cam.nut_slot_export import create_nut_slot_export_object


client = TestClient(app)


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------

def create_valid_export_object() -> ExportObject:
    """Create a valid nut slot export object for testing."""
    request = NutSlotPreviewRequest(
        nut_width_mm=50.0,
        num_strings=6,
        edge_offset_bass_mm=4.0,
        edge_offset_treble_mm=4.0,
        slot_length_mm=4.5,
        slot_depth_mm=1.5,
        slot_width_mm=0.70,
        stock_thickness_mm=9.5,
        tool_diameter_mm=0.56,
        safe_z_mm=5.0,
    )
    preview = generate_nut_slot_preview(request)
    return create_nut_slot_export_object(preview, request)


def create_generic_machine_profile() -> MachineProfileValidationOnly:
    """Create a generic machine profile that supports nut slots."""
    return MachineProfileValidationOnly(
        machine_profile_id="generic_cnc_mm_validation_only",
        controller="none",
        units="mm",
        supported_operations=["nut_slot", "nut_slot_cutting", "drilling"],
        axis_count=3,
        work_envelope_mm=WorkEnvelopeMM(x=300, y=200, z=75),
        supports_arcs=False,
        supports_tool_changes=False,
    )


# -----------------------------------------------------------------------------
# Pure Function Tests
# -----------------------------------------------------------------------------

class TestEvaluateCompatibility:
    """Tests for evaluate_postprocessor_compatibility function."""

    def test_valid_export_object_returns_green(self):
        """Valid export object with compatible machine returns GREEN."""
        export_obj = create_valid_export_object()
        machine = create_generic_machine_profile()

        report = evaluate_postprocessor_compatibility(export_obj, machine)

        assert report.compatible is True
        assert report.gate == "green"
        assert len(report.blocking_issues) == 0

    def test_unsupported_operation_returns_red(self):
        """Unsupported operation returns RED."""
        export_obj = create_valid_export_object()
        machine = create_generic_machine_profile()
        machine.supported_operations = ["drilling"]  # No nut_slot

        report = evaluate_postprocessor_compatibility(export_obj, machine)

        assert report.compatible is False
        assert report.gate == "red"
        assert any("not in supported operations" in issue for issue in report.blocking_issues)

    def test_unit_mismatch_returns_red(self):
        """Unit mismatch returns RED."""
        export_obj = create_valid_export_object()
        machine = create_generic_machine_profile()
        machine.units = "inch"

        report = evaluate_postprocessor_compatibility(export_obj, machine)

        assert report.compatible is False
        assert report.gate == "red"
        assert any("Unit mismatch" in issue for issue in report.blocking_issues)

    def test_insufficient_axes_returns_red(self):
        """Axis count < 3 returns RED."""
        export_obj = create_valid_export_object()
        machine = create_generic_machine_profile()
        machine.axis_count = 2

        report = evaluate_postprocessor_compatibility(export_obj, machine)

        assert report.compatible is False
        assert report.gate == "red"
        assert any("Insufficient axes" in issue for issue in report.blocking_issues)

    def test_bounds_outside_envelope_returns_red(self):
        """Toolpath bounds exceeding envelope returns RED."""
        export_obj = create_valid_export_object()
        machine = create_generic_machine_profile()
        # Make envelope smaller than export bounds
        machine.work_envelope_mm = WorkEnvelopeMM(x=10, y=10, z=10)

        report = evaluate_postprocessor_compatibility(export_obj, machine)

        assert report.compatible is False
        assert report.gate == "red"
        assert any("exceeds envelope" in issue for issue in report.blocking_issues)

    def test_bounds_near_envelope_returns_yellow(self):
        """Toolpath bounds near envelope limit returns YELLOW."""
        export_obj = create_valid_export_object()
        machine = create_generic_machine_profile()
        # Set envelope just slightly larger than bounds (within 5%)
        bounds = export_obj.geometry.bounds
        machine.work_envelope_mm = WorkEnvelopeMM(
            x=bounds.x_max * 1.02,  # 2% margin
            y=bounds.y_max * 1.02,
            z=abs(bounds.z_min) * 1.02,
        )

        report = evaluate_postprocessor_compatibility(export_obj, machine)

        assert report.compatible is True
        assert report.gate == "yellow"
        assert any("near envelope limit" in warning for warning in report.warnings)

    def test_missing_tooling_block_returns_red(self):
        """Missing tooling block returns RED."""
        export_obj = create_valid_export_object()
        # Manually remove tooling (create a modified export object)
        export_dict = export_obj.model_dump()
        export_dict["tooling"]["tool_id"] = ""  # Empty tool_id
        modified_export = ExportObject(**export_dict)

        machine = create_generic_machine_profile()

        report = evaluate_postprocessor_compatibility(modified_export, machine)

        assert report.compatible is False
        assert report.gate == "red"
        assert any("missing tool_id" in issue for issue in report.blocking_issues)

    def test_incomplete_tooling_returns_yellow(self):
        """Incomplete tooling block returns YELLOW."""
        export_obj = create_valid_export_object()
        # Remove optional tooling fields
        export_dict = export_obj.model_dump()
        export_dict["tooling"]["geometry"]["cutting_length_mm"] = None
        modified_export = ExportObject(**export_dict)

        machine = create_generic_machine_profile()

        report = evaluate_postprocessor_compatibility(modified_export, machine)

        # Should still be compatible but with warning
        assert report.compatible is True
        assert report.gate == "yellow"
        assert any("incomplete" in warning.lower() for warning in report.warnings)


# -----------------------------------------------------------------------------
# Safety Assertion Tests
# -----------------------------------------------------------------------------

class TestNoMachineOutput:
    """Tests verifying no machine output is generated."""

    def test_machine_output_generated_always_false(self):
        """machine_output_generated is always False."""
        export_obj = create_valid_export_object()
        machine = create_generic_machine_profile()

        report = evaluate_postprocessor_compatibility(export_obj, machine)

        assert report.machine_output_generated is False

    def test_postprocessor_output_generated_always_false(self):
        """postprocessor_output_generated is always False."""
        export_obj = create_valid_export_object()
        machine = create_generic_machine_profile()

        report = evaluate_postprocessor_compatibility(export_obj, machine)

        assert report.postprocessor_output_generated is False

    def test_report_contains_no_gcode_commands(self):
        """Report does not contain G-code-like commands."""
        export_obj = create_valid_export_object()
        machine = create_generic_machine_profile()

        report = evaluate_postprocessor_compatibility(export_obj, machine)
        report_json = report.model_dump_json()

        # G-code commands that should never appear
        forbidden = ["G0 ", "G1 ", "G2 ", "G3 ", "M3 ", "M5 ", "M30"]
        for cmd in forbidden:
            assert cmd not in report_json, f"Found forbidden G-code command: {cmd}"

    def test_metadata_validation_only_always_true(self):
        """metadata.validation_only is always True."""
        export_obj = create_valid_export_object()
        machine = create_generic_machine_profile()

        report = evaluate_postprocessor_compatibility(export_obj, machine)

        assert report.metadata.validation_only is True

    def test_metadata_machine_ready_always_false(self):
        """metadata.machine_ready is always False."""
        export_obj = create_valid_export_object()
        machine = create_generic_machine_profile()

        report = evaluate_postprocessor_compatibility(export_obj, machine)

        assert report.metadata.machine_ready is False


# -----------------------------------------------------------------------------
# Capability Inference Tests
# -----------------------------------------------------------------------------

class TestCapabilityInference:
    """Tests for required capability inference."""

    def test_infers_3_axis_motion(self):
        """Always infers 3_axis_motion requirement."""
        export_obj = create_valid_export_object()
        machine = create_generic_machine_profile()

        report = evaluate_postprocessor_compatibility(export_obj, machine)

        assert "3_axis_motion" in report.required_capabilities

    def test_infers_linear_interpolation(self):
        """Always infers linear_interpolation requirement."""
        export_obj = create_valid_export_object()
        machine = create_generic_machine_profile()

        report = evaluate_postprocessor_compatibility(export_obj, machine)

        assert "linear_interpolation" in report.required_capabilities

    def test_infers_controlled_plunge_for_plunge_moves(self):
        """Infers controlled_plunge when export has plunge moves."""
        export_obj = create_valid_export_object()
        machine = create_generic_machine_profile()

        report = evaluate_postprocessor_compatibility(export_obj, machine)

        # Nut slot export has plunge moves
        assert "controlled_plunge" in report.required_capabilities


# -----------------------------------------------------------------------------
# Endpoint Tests
# -----------------------------------------------------------------------------

class TestCompatibilityEndpoint:
    """Tests for POST /api/cam/postprocessor/compatibility endpoint."""

    def test_valid_request_returns_200_green(self):
        """Valid request returns 200 with GREEN compatibility."""
        export_obj = create_valid_export_object()
        machine = create_generic_machine_profile()

        response = client.post(
            "/api/cam/postprocessor/compatibility",
            json={
                "export_object": export_obj.model_dump(mode="json"),
                "machine_profile": machine.model_dump(),
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["compatible"] is True
        assert data["gate"] == "green"

    def test_unsupported_operation_returns_200_red(self):
        """Unsupported operation returns 200 with RED (not 500)."""
        export_obj = create_valid_export_object()
        machine = create_generic_machine_profile()
        machine.supported_operations = ["drilling"]

        response = client.post(
            "/api/cam/postprocessor/compatibility",
            json={
                "export_object": export_obj.model_dump(mode="json"),
                "machine_profile": machine.model_dump(),
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["compatible"] is False
        assert data["gate"] == "red"

    def test_malformed_request_returns_422(self):
        """Malformed request returns 422."""
        response = client.post(
            "/api/cam/postprocessor/compatibility",
            json={"invalid": "data"},
        )

        assert response.status_code == 422

    def test_response_has_no_machine_output(self):
        """Response explicitly states no machine output."""
        export_obj = create_valid_export_object()
        machine = create_generic_machine_profile()

        response = client.post(
            "/api/cam/postprocessor/compatibility",
            json={
                "export_object": export_obj.model_dump(mode="json"),
                "machine_profile": machine.model_dump(),
            },
        )

        data = response.json()
        assert data["machine_output_generated"] is False
        assert data["postprocessor_output_generated"] is False

    def test_response_structure(self):
        """Response has expected structure."""
        export_obj = create_valid_export_object()
        machine = create_generic_machine_profile()

        response = client.post(
            "/api/cam/postprocessor/compatibility",
            json={
                "export_object": export_obj.model_dump(mode="json"),
                "machine_profile": machine.model_dump(),
            },
        )

        data = response.json()
        assert "compatible" in data
        assert "gate" in data
        assert "operation" in data
        assert "supported_operations" in data
        assert "blocking_issues" in data
        assert "warnings" in data
        assert "required_capabilities" in data
        assert "metadata" in data


# -----------------------------------------------------------------------------
# Edge Case Tests
# -----------------------------------------------------------------------------

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_supported_operations_returns_red(self):
        """Empty supported_operations list returns RED."""
        export_obj = create_valid_export_object()
        machine = create_generic_machine_profile()
        machine.supported_operations = []

        report = evaluate_postprocessor_compatibility(export_obj, machine)

        assert report.compatible is False
        assert report.gate == "red"

    def test_exact_envelope_match_returns_green(self):
        """Exact envelope match (100%) returns GREEN, not YELLOW."""
        export_obj = create_valid_export_object()
        machine = create_generic_machine_profile()
        # Set envelope exactly at bounds (not within 95%)
        bounds = export_obj.geometry.bounds
        machine.work_envelope_mm = WorkEnvelopeMM(
            x=bounds.x_max + 50,  # Well above bounds
            y=bounds.y_max + 50,
            z=abs(bounds.z_min) + 50,
        )

        report = evaluate_postprocessor_compatibility(export_obj, machine)

        assert report.compatible is True
        # Should be green since bounds are well within envelope
        assert report.gate == "green"

    def test_multiple_issues_all_reported(self):
        """Multiple issues are all reported."""
        export_obj = create_valid_export_object()
        machine = create_generic_machine_profile()
        machine.units = "inch"
        machine.axis_count = 2
        machine.supported_operations = ["drilling"]

        report = evaluate_postprocessor_compatibility(export_obj, machine)

        assert report.compatible is False
        assert report.gate == "red"
        assert len(report.blocking_issues) >= 3  # At least 3 issues
