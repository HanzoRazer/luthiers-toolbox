"""
Tests for DXF Translator Boundary (CAM Dev Order 6D)

Tests the DXF translator compatibility validation layer.
Verifies that compatibility reports are generated without
producing any DXF output.

Core rule: DXF is a translator target, not the manufacturing representation.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.cam.dxf_translator_boundary import (
    DXFTranslatorCompatibilityReport,
    DXFTranslatorProfile,
)
from app.cam.export_object_to_dxf_adapter import (
    detect_geometry_types,
    detect_required_features,
    evaluate_dxf_translator_compatibility,
)
from app.cam.nut_slot_cam import NutSlotPreviewRequest, generate_nut_slot_preview
from app.cam.nut_slot_export import create_nut_slot_export_object


client = TestClient(app)


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------

def create_valid_export_object():
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


def create_generic_translator_profile() -> DXFTranslatorProfile:
    """Create a generic DXF translator profile."""
    # 7C: Use registered translator ID from TRANSLATOR_CAPABILITY_REGISTRY
    return DXFTranslatorProfile(
        translator_id="dxf_r12",
        supported_geometry_types=["line", "polyline", "arc", "circle"],
        supports_layers=True,
        supports_blocks=False,
        supports_splines=False,
        units="mm",
    )


def create_limited_translator_profile() -> DXFTranslatorProfile:
    """Create a limited translator profile (no polyline support).

    7C: Uses registered translator ID but with limited capabilities
    for testing compatibility failures.
    """
    return DXFTranslatorProfile(
        translator_id="dxf_r12",  # Registered ID with limited capabilities for testing
        supported_geometry_types=["line"],  # Only lines
        supports_layers=False,
        supports_blocks=False,
        supports_splines=False,
        units="mm",
    )


# -----------------------------------------------------------------------------
# Geometry Detection Tests
# -----------------------------------------------------------------------------

class TestGeometryDetection:
    """Tests for geometry type detection."""

    def test_detects_polyline_from_slot_entities(self):
        """Slot entities are detected as polyline geometry."""
        export_obj = create_valid_export_object()
        geometry_types = detect_geometry_types(export_obj)

        assert "polyline" in geometry_types

    def test_detects_line_from_linear_moves(self):
        """Linear toolpath moves are detected as line geometry."""
        export_obj = create_valid_export_object()
        geometry_types = detect_geometry_types(export_obj)

        assert "line" in geometry_types

    def test_returns_sorted_unique_types(self):
        """Returns sorted list of unique geometry types."""
        export_obj = create_valid_export_object()
        geometry_types = detect_geometry_types(export_obj)

        # Should be sorted
        assert geometry_types == sorted(geometry_types)
        # Should have no duplicates
        assert len(geometry_types) == len(set(geometry_types))


class TestFeatureDetection:
    """Tests for required feature detection."""

    def test_detects_polyline_support_requirement(self):
        """Polyline geometry requires polyline_support."""
        export_obj = create_valid_export_object()
        geometry_types = detect_geometry_types(export_obj)
        features = detect_required_features(export_obj, geometry_types)

        assert "polyline_support" in features

    def test_detects_layer_support_requirement(self):
        """Geometry entities require layer_support."""
        export_obj = create_valid_export_object()
        geometry_types = detect_geometry_types(export_obj)
        features = detect_required_features(export_obj, geometry_types)

        assert "layer_support" in features

    def test_detects_multi_entity_support(self):
        """Multiple operations require multi_entity_support."""
        export_obj = create_valid_export_object()
        # Nut slot has 6 operations (one per string)
        geometry_types = detect_geometry_types(export_obj)
        features = detect_required_features(export_obj, geometry_types)

        assert "multi_entity_support" in features


# -----------------------------------------------------------------------------
# Compatibility Evaluation Tests
# -----------------------------------------------------------------------------

class TestEvaluateCompatibility:
    """Tests for evaluate_dxf_translator_compatibility function."""

    def test_valid_export_object_returns_green(self):
        """Valid export object with compatible translator returns GREEN."""
        export_obj = create_valid_export_object()
        translator = create_generic_translator_profile()

        report = evaluate_dxf_translator_compatibility(export_obj, translator)

        assert report.compatible is True
        assert report.gate == "green"
        assert report.translation_ready is True
        assert len(report.blocking_issues) == 0

    def test_unsupported_geometry_type_returns_red(self):
        """Unsupported geometry type returns RED."""
        export_obj = create_valid_export_object()
        translator = create_limited_translator_profile()  # Only supports "line"

        report = evaluate_dxf_translator_compatibility(export_obj, translator)

        assert report.compatible is False
        assert report.gate == "red"
        assert any("polyline" in issue.lower() for issue in report.blocking_issues)

    def test_unit_mismatch_returns_red(self):
        """Unit mismatch returns RED."""
        export_obj = create_valid_export_object()
        translator = create_generic_translator_profile()
        translator.units = "inch"

        report = evaluate_dxf_translator_compatibility(export_obj, translator)

        assert report.compatible is False
        assert report.gate == "red"
        assert any("unit mismatch" in issue.lower() for issue in report.blocking_issues)

    def test_missing_polyline_support_returns_red(self):
        """Missing polyline support when required returns RED."""
        export_obj = create_valid_export_object()
        translator = DXFTranslatorProfile(
            translator_id="dxf_r12",  # 7C: registered ID, limited capabilities for testing
            supported_geometry_types=["line", "arc"],  # No polyline
            supports_layers=True,
            units="mm",
        )

        report = evaluate_dxf_translator_compatibility(export_obj, translator)

        assert report.compatible is False
        assert report.gate == "red"

    def test_missing_layer_support_returns_yellow(self):
        """Missing optional layer support returns YELLOW."""
        export_obj = create_valid_export_object()
        translator = DXFTranslatorProfile(
            translator_id="dxf_r12",  # 7C: registered ID, no layer support test
            supported_geometry_types=["line", "polyline", "arc"],
            supports_layers=False,  # No layer support
            units="mm",
        )

        report = evaluate_dxf_translator_compatibility(export_obj, translator)

        assert report.compatible is True
        assert report.gate == "yellow"
        assert any("layer" in warning.lower() for warning in report.warnings)


# -----------------------------------------------------------------------------
# Safety Assertion Tests
# -----------------------------------------------------------------------------

class TestNoDXFOutput:
    """Tests verifying no DXF output is generated."""

    def test_translator_output_generated_always_false(self):
        """translator_output_generated is always False."""
        export_obj = create_valid_export_object()
        translator = create_generic_translator_profile()

        report = evaluate_dxf_translator_compatibility(export_obj, translator)

        assert report.translator_output_generated is False

    def test_dxf_generated_always_false(self):
        """dxf_generated is always False."""
        export_obj = create_valid_export_object()
        translator = create_generic_translator_profile()

        report = evaluate_dxf_translator_compatibility(export_obj, translator)

        assert report.dxf_generated is False

    def test_report_contains_no_dxf_tokens(self):
        """Report does not contain DXF serialization tokens."""
        export_obj = create_valid_export_object()
        translator = create_generic_translator_profile()

        report = evaluate_dxf_translator_compatibility(export_obj, translator)
        report_json = report.model_dump_json()

        # DXF tokens that should never appear in output
        forbidden = ["SECTION", "ENTITIES", "POLYLINE", "VERTEX", "ENDSEC", "EOF"]
        for token in forbidden:
            # Check for token as standalone word (not as part of other words)
            assert f'"{token}"' not in report_json, f"Found forbidden DXF token: {token}"
            assert f" {token} " not in report_json, f"Found forbidden DXF token: {token}"

    def test_metadata_validation_only_always_true(self):
        """metadata.validation_only is always True."""
        export_obj = create_valid_export_object()
        translator = create_generic_translator_profile()

        report = evaluate_dxf_translator_compatibility(export_obj, translator)

        assert report.metadata.validation_only is True

    def test_metadata_machine_ready_always_false(self):
        """metadata.machine_ready is always False."""
        export_obj = create_valid_export_object()
        translator = create_generic_translator_profile()

        report = evaluate_dxf_translator_compatibility(export_obj, translator)

        assert report.metadata.machine_ready is False

    def test_metadata_translator_class_is_dxf(self):
        """metadata.translator_class is 'DXF'."""
        export_obj = create_valid_export_object()
        translator = create_generic_translator_profile()

        report = evaluate_dxf_translator_compatibility(export_obj, translator)

        assert report.metadata.translator_class == "DXF"


# -----------------------------------------------------------------------------
# Endpoint Tests
# -----------------------------------------------------------------------------

class TestValidateEndpoint:
    """Tests for POST /api/cam/dxf/translator/validate endpoint."""

    def test_valid_request_returns_200_green(self):
        """Valid request returns 200 with GREEN compatibility."""
        export_obj = create_valid_export_object()
        translator = create_generic_translator_profile()

        response = client.post(
            "/api/cam/dxf/translator/validate",
            json={
                "export_object": export_obj.model_dump(mode="json"),
                "translator_profile": translator.model_dump(),
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["compatible"] is True
        assert data["gate"] == "green"

    def test_unsupported_geometry_returns_200_red(self):
        """Unsupported geometry returns 200 with RED (not 500)."""
        export_obj = create_valid_export_object()
        translator = create_limited_translator_profile()

        response = client.post(
            "/api/cam/dxf/translator/validate",
            json={
                "export_object": export_obj.model_dump(mode="json"),
                "translator_profile": translator.model_dump(),
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["compatible"] is False
        assert data["gate"] == "red"

    def test_malformed_request_returns_422(self):
        """Malformed request returns 422."""
        response = client.post(
            "/api/cam/dxf/translator/validate",
            json={"invalid": "data"},
        )

        assert response.status_code == 422

    def test_response_has_no_dxf_output(self):
        """Response explicitly states no DXF output."""
        export_obj = create_valid_export_object()
        translator = create_generic_translator_profile()

        response = client.post(
            "/api/cam/dxf/translator/validate",
            json={
                "export_object": export_obj.model_dump(mode="json"),
                "translator_profile": translator.model_dump(),
            },
        )

        data = response.json()
        assert data["translator_output_generated"] is False
        assert data["dxf_generated"] is False

    def test_response_structure(self):
        """Response has expected structure."""
        export_obj = create_valid_export_object()
        translator = create_generic_translator_profile()

        response = client.post(
            "/api/cam/dxf/translator/validate",
            json={
                "export_object": export_obj.model_dump(mode="json"),
                "translator_profile": translator.model_dump(),
            },
        )

        data = response.json()
        assert "compatible" in data
        assert "gate" in data
        assert "translation_ready" in data
        assert "geometry_types_detected" in data
        assert "required_translator_features" in data
        assert "metadata" in data


# -----------------------------------------------------------------------------
# Edge Case Tests
# -----------------------------------------------------------------------------

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_supported_geometry_returns_red(self):
        """Empty supported_geometry_types list returns RED."""
        export_obj = create_valid_export_object()
        translator = DXFTranslatorProfile(
            translator_id="dxf_r12",  # 7C: registered ID, empty capabilities test
            supported_geometry_types=[],
            units="mm",
        )

        report = evaluate_dxf_translator_compatibility(export_obj, translator)

        assert report.compatible is False
        assert report.gate == "red"

    def test_geometry_types_detected_populated(self):
        """geometry_types_detected is populated."""
        export_obj = create_valid_export_object()
        translator = create_generic_translator_profile()

        report = evaluate_dxf_translator_compatibility(export_obj, translator)

        assert len(report.geometry_types_detected) > 0

    def test_required_features_populated(self):
        """required_translator_features is populated."""
        export_obj = create_valid_export_object()
        translator = create_generic_translator_profile()

        report = evaluate_dxf_translator_compatibility(export_obj, translator)

        assert len(report.required_translator_features) > 0

    def test_multiple_issues_all_reported(self):
        """Multiple issues are all reported."""
        export_obj = create_valid_export_object()
        translator = DXFTranslatorProfile(
            translator_id="dxf_r12",  # 7C: registered ID, problematic capabilities test
            supported_geometry_types=["circle"],  # Wrong types
            supports_layers=False,
            units="inch",  # Wrong units
        )

        report = evaluate_dxf_translator_compatibility(export_obj, translator)

        assert report.compatible is False
        assert report.gate == "red"
        assert len(report.blocking_issues) >= 2  # At least unit + geometry issues
