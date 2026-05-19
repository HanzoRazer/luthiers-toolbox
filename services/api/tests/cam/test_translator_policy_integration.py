"""
Tests for Translator Policy Integration (CAM Dev Order 7C)

Tests registry-gated validation in the DXF translator boundary.

Core invariants tested:
  - Known DXF translators validate through registry
  - Unknown translators return RED
  - G-code postprocessor does not pass DXF validation
  - Execution flags remain false
  - No DXF/G-code tokens generated
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.cam.dxf_translator_boundary import (
    DXFTranslatorProfile,
    DXFTranslatorValidationRequest,
)
from app.cam.export_object import ExportObject
from app.cam.export_object_to_dxf_adapter import (
    evaluate_dxf_translator_compatibility,
    validate_translator_registry,
)
from app.cam.translator_capability_registry import (
    TRANSLATOR_CAPABILITY_REGISTRY,
    get_translator_capability,
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


def create_dxf_r12_profile() -> DXFTranslatorProfile:
    """Create a DXF R12 translator profile."""
    return DXFTranslatorProfile(
        translator_id="dxf_r12",
        supported_geometry_types=["line", "polyline", "arc", "circle"],
        supports_layers=True,
        supports_blocks=False,
        supports_splines=False,
        units="mm",
    )


def create_dxf_r2000_profile() -> DXFTranslatorProfile:
    """Create a DXF R2000 translator profile."""
    return DXFTranslatorProfile(
        translator_id="dxf_r2000",
        supported_geometry_types=["line", "polyline", "arc", "circle", "lwpolyline"],
        supports_layers=True,
        supports_blocks=True,
        supports_splines=False,
        units="mm",
    )


def create_unknown_translator_profile() -> DXFTranslatorProfile:
    """Create a profile with unknown translator ID."""
    return DXFTranslatorProfile(
        translator_id="unknown_translator_xyz",
        supported_geometry_types=["line", "polyline"],
        supports_layers=True,
        supports_blocks=False,
        supports_splines=False,
        units="mm",
    )


def create_grbl_as_dxf_profile() -> DXFTranslatorProfile:
    """Create a profile using G-code postprocessor ID for DXF validation."""
    return DXFTranslatorProfile(
        translator_id="gcode_grbl_placeholder",
        supported_geometry_types=["line"],
        supports_layers=False,
        supports_blocks=False,
        supports_splines=False,
        units="mm",
    )


# -----------------------------------------------------------------------------
# Registry Validation Tests
# -----------------------------------------------------------------------------

class TestRegistryValidation:
    """Tests for the registry validation function."""

    def test_known_dxf_r12_passes_registry(self):
        """dxf_r12 should pass registry validation."""
        capability, issues = validate_translator_registry("dxf_r12")
        assert capability is not None
        assert issues == []
        assert capability.translator_id == "dxf_r12"

    def test_known_dxf_r2000_passes_registry(self):
        """dxf_r2000 should pass registry validation."""
        capability, issues = validate_translator_registry("dxf_r2000")
        assert capability is not None
        assert issues == []
        assert capability.translator_id == "dxf_r2000"

    def test_unknown_translator_fails_registry(self):
        """Unknown translator should fail with 'not found' error."""
        capability, issues = validate_translator_registry("unknown_xyz")
        assert capability is None
        assert len(issues) == 1
        assert "not found in capability registry" in issues[0]

    def test_grbl_postprocessor_fails_category_check(self):
        """G-code postprocessor should fail category check."""
        capability, issues = validate_translator_registry("gcode_grbl_placeholder")
        assert capability is not None  # It exists
        assert len(issues) >= 1
        # Check for category mismatch
        category_error = [i for i in issues if "postprocessor" in i.lower()]
        assert len(category_error) >= 1

    def test_grbl_postprocessor_fails_output_class_check(self):
        """G-code postprocessor should fail output class check."""
        capability, issues = validate_translator_registry("gcode_grbl_placeholder")
        assert capability is not None
        # Check for output class mismatch
        output_error = [i for i in issues if "gcode" in i.lower() or "output class" in i.lower()]
        assert len(output_error) >= 1

    def test_grbl_postprocessor_fails_execution_state_check(self):
        """G-code postprocessor (execution_disabled) should fail state check."""
        capability, issues = validate_translator_registry("gcode_grbl_placeholder")
        assert capability is not None
        # Check for disabled state error
        disabled_error = [i for i in issues if "disabled" in i.lower()]
        assert len(disabled_error) >= 1


# -----------------------------------------------------------------------------
# Compatibility Evaluation Tests
# -----------------------------------------------------------------------------

class TestCompatibilityEvaluation:
    """Tests for the full compatibility evaluation with registry gating."""

    def test_dxf_r12_validates_successfully(self):
        """DXF R12 translator should validate successfully."""
        export_obj = create_valid_export_object()
        profile = create_dxf_r12_profile()

        report = evaluate_dxf_translator_compatibility(export_obj, profile)

        assert report.gate in ("green", "yellow")
        assert report.compatible is True
        assert report.blocking_issues == []

    def test_dxf_r2000_validates_successfully(self):
        """DXF R2000 translator should validate successfully."""
        export_obj = create_valid_export_object()
        profile = create_dxf_r2000_profile()

        report = evaluate_dxf_translator_compatibility(export_obj, profile)

        assert report.gate in ("green", "yellow")
        assert report.compatible is True
        assert report.blocking_issues == []

    def test_unknown_translator_returns_red(self):
        """Unknown translator should return RED gate."""
        export_obj = create_valid_export_object()
        profile = create_unknown_translator_profile()

        report = evaluate_dxf_translator_compatibility(export_obj, profile)

        assert report.gate == "red"
        assert report.compatible is False
        assert report.translation_ready is False
        assert len(report.blocking_issues) >= 1
        assert "not found" in report.blocking_issues[0].lower()

    def test_grbl_placeholder_returns_red_for_dxf(self):
        """G-code postprocessor should return RED for DXF validation."""
        export_obj = create_valid_export_object()
        profile = create_grbl_as_dxf_profile()

        report = evaluate_dxf_translator_compatibility(export_obj, profile)

        assert report.gate == "red"
        assert report.compatible is False
        assert report.translation_ready is False
        # Should have multiple blocking issues (category, output class, disabled)
        assert len(report.blocking_issues) >= 1


# -----------------------------------------------------------------------------
# Safety Assertion Tests
# -----------------------------------------------------------------------------

class TestSafetyAssertions:
    """Tests that safety assertions are maintained."""

    def test_execution_flags_remain_false(self):
        """All execution flags must remain false."""
        export_obj = create_valid_export_object()
        profile = create_dxf_r12_profile()

        report = evaluate_dxf_translator_compatibility(export_obj, profile)

        assert report.translator_output_generated is False
        assert report.dxf_generated is False
        assert report.metadata.machine_ready is False
        assert report.metadata.validation_only is True

    def test_no_dxf_tokens_in_report(self):
        """Report should not contain DXF file format tokens."""
        export_obj = create_valid_export_object()
        profile = create_dxf_r12_profile()

        report = evaluate_dxf_translator_compatibility(export_obj, profile)
        report_str = report.model_dump_json()

        # DXF file format tokens
        assert "SECTION" not in report_str
        assert "ENTITIES" not in report_str
        assert "ENDSEC" not in report_str
        assert "EOF" not in report_str or "eof" in report_str.lower()

    def test_no_gcode_tokens_in_report(self):
        """Report should not contain G-code tokens."""
        export_obj = create_valid_export_object()
        profile = create_dxf_r12_profile()

        report = evaluate_dxf_translator_compatibility(export_obj, profile)
        report_str = report.model_dump_json()

        # G-code tokens
        assert "G00" not in report_str
        assert "G01" not in report_str
        assert "G90" not in report_str
        assert "M03" not in report_str


# -----------------------------------------------------------------------------
# Endpoint Tests
# -----------------------------------------------------------------------------

class TestDXFTranslatorEndpoint:
    """Tests for the DXF translator validation endpoint."""

    def test_endpoint_with_known_translator(self):
        """Endpoint should accept known DXF translator."""
        export_obj = create_valid_export_object()
        profile = create_dxf_r12_profile()

        request_data = {
            "export_object": export_obj.model_dump(mode="json"),
            "translator_profile": profile.model_dump(mode="json"),
        }

        response = client.post("/api/cam/dxf/translator/validate", json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert data["gate"] in ("green", "yellow")
        assert data["compatible"] is True

    def test_endpoint_with_unknown_translator(self):
        """Endpoint should return RED for unknown translator."""
        export_obj = create_valid_export_object()
        profile = create_unknown_translator_profile()

        request_data = {
            "export_object": export_obj.model_dump(mode="json"),
            "translator_profile": profile.model_dump(mode="json"),
        }

        response = client.post("/api/cam/dxf/translator/validate", json=request_data)
        assert response.status_code == 200  # Returns report, not error

        data = response.json()
        assert data["gate"] == "red"
        assert data["compatible"] is False
        assert "not found" in str(data["blocking_issues"]).lower()

    def test_endpoint_with_grbl_placeholder(self):
        """Endpoint should return RED for G-code postprocessor."""
        export_obj = create_valid_export_object()
        profile = create_grbl_as_dxf_profile()

        request_data = {
            "export_object": export_obj.model_dump(mode="json"),
            "translator_profile": profile.model_dump(mode="json"),
        }

        response = client.post("/api/cam/dxf/translator/validate", json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert data["gate"] == "red"
        assert data["compatible"] is False


# -----------------------------------------------------------------------------
# Registry Isolation Tests
# -----------------------------------------------------------------------------

class TestRegistryIsolation:
    """Tests that registry validation doesn't affect other registries."""

    def test_translator_registry_unchanged(self):
        """Validation should not modify translator registry."""
        initial_count = len(TRANSLATOR_CAPABILITY_REGISTRY)

        export_obj = create_valid_export_object()
        profile = create_dxf_r12_profile()
        evaluate_dxf_translator_compatibility(export_obj, profile)

        assert len(TRANSLATOR_CAPABILITY_REGISTRY) == initial_count

    def test_validation_reads_registry_only(self):
        """Validation should only read from registry, not write."""
        cap_before = get_translator_capability("dxf_r12")

        export_obj = create_valid_export_object()
        profile = create_dxf_r12_profile()
        evaluate_dxf_translator_compatibility(export_obj, profile)

        cap_after = get_translator_capability("dxf_r12")
        assert cap_before == cap_after
