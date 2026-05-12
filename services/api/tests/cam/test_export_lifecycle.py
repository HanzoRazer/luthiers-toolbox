"""
Tests for Governed Export Lifecycle Orchestrator (CAM Dev Order 6E)

Tests the end-to-end lifecycle validation pipeline:
  Preview → Export Object → Postprocessor → Translator

Core rule: Orchestration only, no output generation.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.cam.dxf_translator_boundary import DXFTranslatorProfile
from app.cam.export_lifecycle_orchestrator import (
    GovernedExportLifecycleRequest,
    GovernedExportLifecycleReport,
    PreviewRequestWrapper,
    propagate_gate,
    run_governed_export_lifecycle,
)
from app.cam.postprocessor_boundary import MachineProfileValidationOnly


client = TestClient(app)


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------

def create_valid_preview_request() -> PreviewRequestWrapper:
    """Create a valid nut slot preview request wrapper."""
    return PreviewRequestWrapper(
        operation="nut_slot",
        payload={
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
        },
    )


def create_compatible_machine_profile() -> MachineProfileValidationOnly:
    """Create a machine profile compatible with nut slot operations."""
    return MachineProfileValidationOnly(
        machine_profile_id="test_3axis_cnc",
        controller="none",
        units="mm",
        supported_operations=["nut_slot", "pocket", "drill"],
        axis_count=3,
        work_envelope_mm={"x": 300, "y": 300, "z": 50},
    )


def create_compatible_translator_profile() -> DXFTranslatorProfile:
    """Create a translator profile compatible with nut slot geometry."""
    return DXFTranslatorProfile(
        translator_id="generic_dxf_r14_validation_only",
        supported_geometry_types=["line", "polyline", "arc", "circle"],
        supports_layers=True,
        supports_blocks=False,
        supports_splines=False,
        units="mm",
    )


def create_full_lifecycle_request() -> GovernedExportLifecycleRequest:
    """Create a full lifecycle request with all compatible profiles."""
    return GovernedExportLifecycleRequest(
        preview_request=create_valid_preview_request(),
        machine_profile=create_compatible_machine_profile(),
        translator_profile=create_compatible_translator_profile(),
    )


# -----------------------------------------------------------------------------
# Gate Propagation Tests
# -----------------------------------------------------------------------------

class TestGatePropagation:
    """Tests for gate propagation logic."""

    def test_all_green_returns_green(self):
        """All green gates return green."""
        assert propagate_gate("green", "green", "green") == "green"

    def test_any_red_returns_red(self):
        """Any red gate returns red."""
        assert propagate_gate("green", "red", "green") == "red"
        assert propagate_gate("red", "green", "yellow") == "red"

    def test_yellow_without_red_returns_yellow(self):
        """Yellow without red returns yellow."""
        assert propagate_gate("green", "yellow", "green") == "yellow"
        assert propagate_gate("yellow", "green", "yellow") == "yellow"

    def test_red_takes_precedence_over_yellow(self):
        """Red takes precedence over yellow."""
        assert propagate_gate("yellow", "red", "yellow") == "red"

    def test_empty_gates_returns_green(self):
        """Empty gates return green (no issues)."""
        assert propagate_gate() == "green"

    def test_single_gate_returned(self):
        """Single gate is returned as-is."""
        assert propagate_gate("green") == "green"
        assert propagate_gate("yellow") == "yellow"
        assert propagate_gate("red") == "red"


# -----------------------------------------------------------------------------
# Lifecycle Orchestration Tests
# -----------------------------------------------------------------------------

class TestLifecycleOrchestration:
    """Tests for run_governed_export_lifecycle function."""

    def test_valid_request_returns_green(self):
        """Valid request with compatible profiles returns GREEN."""
        request = create_full_lifecycle_request()
        report = run_governed_export_lifecycle(request)

        assert report.lifecycle_gate == "green"
        assert report.export_ready is True
        assert report.translator_ready is True
        assert len(report.blocking_issues) == 0

    def test_preview_gate_populated(self):
        """Preview gate is populated in report."""
        request = create_full_lifecycle_request()
        report = run_governed_export_lifecycle(request)

        assert report.preview_gate in ["green", "yellow", "red"]
        assert report.preview_operation == "nut_slot"

    def test_export_object_summary_populated(self):
        """Export object summary is populated for valid request."""
        request = create_full_lifecycle_request()
        report = run_governed_export_lifecycle(request)

        assert report.export_object_summary is not None
        assert "nut_slot" in report.export_object_summary.operation
        assert report.export_object_summary.toolpath_count > 0
        assert report.export_object_summary.entity_count > 0
        assert report.export_object_summary.units == "mm"

    def test_machine_validation_populated(self):
        """Machine validation fields are populated."""
        request = create_full_lifecycle_request()
        report = run_governed_export_lifecycle(request)

        assert report.machine_validation_gate is not None
        assert report.machine_validation_compatible is not None

    def test_translator_validation_populated(self):
        """Translator validation fields are populated."""
        request = create_full_lifecycle_request()
        report = run_governed_export_lifecycle(request)

        assert report.translator_validation_gate is not None
        assert report.translator_validation_compatible is not None

    def test_unsupported_operation_returns_red(self):
        """Unsupported operation returns RED."""
        request = create_full_lifecycle_request()
        request.preview_request.operation = "unsupported_op"

        report = run_governed_export_lifecycle(request)

        assert report.lifecycle_gate == "red"
        assert report.export_ready is False
        assert any("not found" in issue for issue in report.blocking_issues)

    def test_incompatible_machine_propagates_red(self):
        """Incompatible machine profile propagates to RED."""
        request = create_full_lifecycle_request()
        request.machine_profile.supported_operations = ["pocket"]  # No nut_slot

        report = run_governed_export_lifecycle(request)

        assert report.lifecycle_gate == "red"
        assert any("[Machine]" in issue for issue in report.blocking_issues)

    def test_incompatible_translator_propagates_red(self):
        """Incompatible translator profile propagates to RED."""
        request = create_full_lifecycle_request()
        request.translator_profile.supported_geometry_types = ["circle"]  # No polyline
        request.translator_profile.units = "mm"

        report = run_governed_export_lifecycle(request)

        assert report.lifecycle_gate == "red"
        assert any("[Translator]" in issue for issue in report.blocking_issues)

    def test_unit_mismatch_returns_red(self):
        """Unit mismatch in translator returns RED."""
        request = create_full_lifecycle_request()
        request.translator_profile.units = "inch"

        report = run_governed_export_lifecycle(request)

        assert report.lifecycle_gate == "red"
        assert any("unit" in issue.lower() for issue in report.blocking_issues)


# -----------------------------------------------------------------------------
# Safety Assertion Tests
# -----------------------------------------------------------------------------

class TestNoOutputGeneration:
    """Tests verifying no output is generated."""

    def test_machine_output_generated_always_false(self):
        """machine_output_generated is always False."""
        request = create_full_lifecycle_request()
        report = run_governed_export_lifecycle(request)

        assert report.machine_output_generated is False

    def test_translator_output_generated_always_false(self):
        """translator_output_generated is always False."""
        request = create_full_lifecycle_request()
        report = run_governed_export_lifecycle(request)

        assert report.translator_output_generated is False

    def test_machine_ready_always_false(self):
        """machine_ready is always False in 6E."""
        request = create_full_lifecycle_request()
        report = run_governed_export_lifecycle(request)

        assert report.machine_ready is False

    def test_metadata_validation_only_always_true(self):
        """metadata.validation_only is always True."""
        request = create_full_lifecycle_request()
        report = run_governed_export_lifecycle(request)

        assert report.metadata.validation_only is True

    def test_metadata_governed_export_pipeline_true(self):
        """metadata.governed_export_pipeline is True."""
        request = create_full_lifecycle_request()
        report = run_governed_export_lifecycle(request)

        assert report.metadata.governed_export_pipeline is True

    def test_even_red_gate_no_output(self):
        """Even RED gate produces no output."""
        request = create_full_lifecycle_request()
        request.preview_request.operation = "unsupported_op"

        report = run_governed_export_lifecycle(request)

        assert report.lifecycle_gate == "red"
        assert report.machine_output_generated is False
        assert report.translator_output_generated is False


# -----------------------------------------------------------------------------
# Endpoint Tests
# -----------------------------------------------------------------------------

class TestValidateEndpoint:
    """Tests for POST /api/cam/export/lifecycle/validate endpoint."""

    def test_valid_request_returns_200_green(self):
        """Valid request returns 200 with GREEN lifecycle gate."""
        request = create_full_lifecycle_request()

        response = client.post(
            "/api/cam/export/lifecycle/validate",
            json=request.model_dump(),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["lifecycle_gate"] == "green"
        assert data["export_ready"] is True

    def test_response_has_all_fields(self):
        """Response has all expected fields."""
        request = create_full_lifecycle_request()

        response = client.post(
            "/api/cam/export/lifecycle/validate",
            json=request.model_dump(),
        )

        data = response.json()
        assert "lifecycle_gate" in data
        assert "export_ready" in data
        assert "machine_ready" in data
        assert "translator_ready" in data
        assert "preview_gate" in data
        assert "preview_operation" in data
        assert "export_object_summary" in data
        assert "machine_validation_gate" in data
        assert "translator_validation_gate" in data
        assert "blocking_issues" in data
        assert "warnings" in data
        assert "metadata" in data

    def test_response_safety_assertions(self):
        """Response contains safety assertion fields."""
        request = create_full_lifecycle_request()

        response = client.post(
            "/api/cam/export/lifecycle/validate",
            json=request.model_dump(),
        )

        data = response.json()
        assert data["machine_output_generated"] is False
        assert data["translator_output_generated"] is False
        assert data["machine_ready"] is False

    def test_malformed_request_returns_422(self):
        """Malformed request returns 422."""
        response = client.post(
            "/api/cam/export/lifecycle/validate",
            json={"invalid": "data"},
        )

        assert response.status_code == 422

    def test_incompatible_profiles_returns_200_red(self):
        """Incompatible profiles return 200 with RED (not 500)."""
        request = create_full_lifecycle_request()
        request.translator_profile.units = "inch"

        response = client.post(
            "/api/cam/export/lifecycle/validate",
            json=request.model_dump(),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["lifecycle_gate"] == "red"


# -----------------------------------------------------------------------------
# Edge Cases
# -----------------------------------------------------------------------------

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_multiple_issues_all_reported(self):
        """Multiple issues are all reported."""
        request = create_full_lifecycle_request()
        request.machine_profile.supported_operations = ["pocket"]
        request.translator_profile.units = "inch"

        report = run_governed_export_lifecycle(request)

        assert report.lifecycle_gate == "red"
        assert len(report.blocking_issues) >= 2

    def test_warnings_collected_across_stages(self):
        """Warnings are collected from all stages."""
        request = create_full_lifecycle_request()
        request.translator_profile.supports_layers = False

        report = run_governed_export_lifecycle(request)

        # Missing layer support produces YELLOW warning
        assert report.lifecycle_gate == "yellow" or len(report.warnings) > 0

    def test_export_object_summary_none_on_preview_red(self):
        """Export object summary is None when preview is RED."""
        request = create_full_lifecycle_request()
        request.preview_request.operation = "unsupported_op"

        report = run_governed_export_lifecycle(request)

        assert report.preview_gate == "red"
        assert report.export_object_summary is None

    def test_machine_validation_none_on_export_failure(self):
        """Machine validation is None when export object fails."""
        request = create_full_lifecycle_request()
        request.preview_request.operation = "unsupported_op"

        report = run_governed_export_lifecycle(request)

        assert report.machine_validation_gate is None
        assert report.machine_validation_compatible is None

    def test_translator_validation_none_on_export_failure(self):
        """Translator validation is None when export object fails."""
        request = create_full_lifecycle_request()
        request.preview_request.operation = "unsupported_op"

        report = run_governed_export_lifecycle(request)

        assert report.translator_validation_gate is None
        assert report.translator_validation_compatible is None
