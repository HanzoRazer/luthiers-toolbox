"""Tests for LTB CAM output import."""

import json
import pytest
import tempfile
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from import_ltb_cam_output import (
    validate_ltb_output,
    transform_to_strategy,
    import_ltb_output,
    get_nested,
    mm_to_inches,
)


FIXTURES_DIR = Path(__file__).parent.parent / "examples" / "ltb_import"


@pytest.fixture
def valid_ltb_output():
    """Load the synthetic V-Carve LTB output fixture."""
    fixture_path = FIXTURES_DIR / "synthetic_vcarve_ltb_output.json"
    with open(fixture_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def minimal_ltb_output():
    """Minimal valid LTB output for testing."""
    return {
        "operation": {
            "operation_type": "v_carve",
            "target_feature": "fretboard",
            "cut_intent": "profile",
            "method": "vcarve",
        },
        "geometry": {
            "dxf_file": "test.dxf",
            "primary_layer": "LAYER0",
        },
        "tool": {
            "tool_type": "vbit",
            "diameter_mm": 6.35,
        },
        "parameters": {
            "depth_mm": 2.5,
            "feed_mm_min": 1200,
        },
        "material": {
            "material_class": "hardwood",
        },
        "units": {
            "linear": "mm",
        },
        "coordinate_frame": {
            "origin": "top_left",
            "x_axis": "along_neck",
            "y_axis": "across",
        },
        "provenance": {
            "source_spec_id": "test-spec-001",
            "ltb_version": "0.42.0",
            "created_at": "2026-05-25T00:00:00Z",
        },
    }


class TestValidation:
    """Tests for LTB output validation."""

    def test_validate_valid_output(self, valid_ltb_output):
        """Valid LTB output passes validation."""
        errors = validate_ltb_output(valid_ltb_output)
        assert errors == []

    def test_validate_minimal_output(self, minimal_ltb_output):
        """Minimal valid output passes validation."""
        errors = validate_ltb_output(minimal_ltb_output)
        assert errors == []

    def test_validate_missing_operation_type(self, minimal_ltb_output):
        """Missing operation_type is caught."""
        del minimal_ltb_output["operation"]["operation_type"]
        errors = validate_ltb_output(minimal_ltb_output)
        assert any("operation_type" in e for e in errors)

    def test_validate_missing_tool_diameter(self, minimal_ltb_output):
        """Missing tool diameter is caught."""
        del minimal_ltb_output["tool"]["diameter_mm"]
        errors = validate_ltb_output(minimal_ltb_output)
        assert any("diameter_mm" in e for e in errors)

    def test_validate_missing_provenance(self, minimal_ltb_output):
        """Missing provenance fields are caught."""
        del minimal_ltb_output["provenance"]["source_spec_id"]
        errors = validate_ltb_output(minimal_ltb_output)
        assert any("source_spec_id" in e for e in errors)

    def test_validate_wrong_units(self, minimal_ltb_output):
        """Non-mm units are rejected."""
        minimal_ltb_output["units"]["linear"] = "inches"
        errors = validate_ltb_output(minimal_ltb_output)
        assert any("mm" in e.lower() for e in errors)

    def test_validate_empty_field_rejected(self, minimal_ltb_output):
        """Empty string in required field is caught."""
        minimal_ltb_output["operation"]["operation_type"] = "   "
        errors = validate_ltb_output(minimal_ltb_output)
        assert any("operation_type" in e for e in errors)


class TestTransformation:
    """Tests for LTB to strategy transformation."""

    def test_transform_preserves_operation_type(self, valid_ltb_output):
        """operation_type passes through to strategy."""
        strategy = transform_to_strategy(valid_ltb_output)
        assert strategy["operation_intent"]["operation_type"] == "v_carve"

    def test_transform_preserves_cut_intent(self, valid_ltb_output):
        """cut_intent passes through to operation.type."""
        strategy = transform_to_strategy(valid_ltb_output)
        assert strategy["operation"]["type"] == "profile"

    def test_transform_injects_non_execution_declaration(self, valid_ltb_output):
        """non_execution_declaration is always injected as true."""
        strategy = transform_to_strategy(valid_ltb_output)
        assert strategy["operation_intent"]["non_execution_declaration"] is True

    def test_transform_injects_execution_authority_claim_false(self, valid_ltb_output):
        """execution_authority_claim is always injected as false."""
        strategy = transform_to_strategy(valid_ltb_output)
        assert strategy["safety_boundary"]["execution_authority_claim"] is False

    def test_transform_injects_human_review_required(self, valid_ltb_output):
        """human_review_required is always injected as true."""
        strategy = transform_to_strategy(valid_ltb_output)
        assert strategy["safety_boundary"]["human_review_required"] is True

    def test_transform_injects_pending_approval_state(self, valid_ltb_output):
        """approval_state is always pending."""
        strategy = transform_to_strategy(valid_ltb_output)
        assert strategy["approval_state"] == "pending"

    def test_transform_ignores_ltb_execution_fields(self, valid_ltb_output):
        """Even if LTB output contains execution fields, they are ignored."""
        valid_ltb_output["execution_authority_claim"] = True
        valid_ltb_output["non_execution_declaration"] = False
        strategy = transform_to_strategy(valid_ltb_output)
        assert strategy["safety_boundary"]["execution_authority_claim"] is False
        assert strategy["operation_intent"]["non_execution_declaration"] is True

    def test_transform_converts_mm_to_inches(self, valid_ltb_output):
        """Dimensions are converted from mm to inches."""
        strategy = transform_to_strategy(valid_ltb_output, target_units="inches")
        assert strategy["units"] == "inches"
        depth = strategy["safety_boundary"]["max_depth_inches"]
        assert depth is not None
        assert 0.09 < depth < 0.11  # 2.5mm ~ 0.098 inches

    def test_transform_preserves_mm_when_requested(self, valid_ltb_output):
        """Units stay mm when requested."""
        strategy = transform_to_strategy(valid_ltb_output, target_units="mm")
        assert strategy["units"] == "mm"

    def test_transform_preserves_material_class(self, valid_ltb_output):
        """material_class passes through."""
        strategy = transform_to_strategy(valid_ltb_output)
        assert strategy["material_context"]["material_class"] == "hardwood"

    def test_transform_preserves_coordinate_frame(self, valid_ltb_output):
        """coordinate_frame passes through."""
        strategy = transform_to_strategy(valid_ltb_output)
        assert strategy["coordinate_frame"]["origin"] == "top_left_corner"


class TestImportRoundTrip:
    """Tests for full import round-trip."""

    def test_import_produces_valid_strategy(self, valid_ltb_output):
        """Import produces a strategy that can be serialized."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "ltb_output.json"
            output_path = Path(tmpdir) / "strategy.json"

            with open(input_path, "w", encoding="utf-8") as f:
                json.dump(valid_ltb_output, f)

            strategy = import_ltb_output(input_path, output_path)

            assert output_path.exists()
            with open(output_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            assert loaded["strategy_version"] == "1.2"

    def test_import_directory_mode(self, valid_ltb_output):
        """Import accepts a directory containing cam_output.json."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = Path(tmpdir) / "ltb_export"
            input_dir.mkdir()
            output_path = Path(tmpdir) / "out" / "strategy.json"

            with open(input_dir / "cam_output.json", "w", encoding="utf-8") as f:
                json.dump(valid_ltb_output, f)

            strategy = import_ltb_output(input_dir, output_path)
            assert output_path.exists()

    def test_import_copies_dxf_file(self, valid_ltb_output):
        """Import copies referenced DXF to output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = Path(tmpdir) / "ltb_export"
            input_dir.mkdir()
            output_path = Path(tmpdir) / "out" / "strategy.json"

            with open(input_dir / "cam_output.json", "w", encoding="utf-8") as f:
                json.dump(valid_ltb_output, f)

            dxf_name = valid_ltb_output["geometry"]["dxf_file"]
            with open(input_dir / dxf_name, "w") as f:
                f.write("0\nEOF\n")

            import_ltb_output(input_dir, output_path)
            assert (output_path.parent / dxf_name).exists()

    def test_import_rejects_missing_file(self):
        """Import raises FileNotFoundError for missing input."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "strategy.json"
            with pytest.raises(FileNotFoundError):
                import_ltb_output(Path("/nonexistent/path.json"), output_path)

    def test_import_rejects_invalid_ltb_output(self):
        """Import raises ValueError for invalid LTB output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "ltb_output.json"
            output_path = Path(tmpdir) / "strategy.json"

            with open(input_path, "w", encoding="utf-8") as f:
                json.dump({"operation": {}}, f)

            with pytest.raises(ValueError) as exc:
                import_ltb_output(input_path, output_path)
            assert "validation failed" in str(exc.value).lower()


class TestHelpers:
    """Tests for helper functions."""

    def test_get_nested_simple(self):
        """get_nested retrieves simple path."""
        data = {"a": {"b": {"c": 42}}}
        assert get_nested(data, "a.b.c") == 42

    def test_get_nested_missing(self):
        """get_nested returns None for missing path."""
        data = {"a": {"b": 1}}
        assert get_nested(data, "a.c.d") is None

    def test_mm_to_inches(self):
        """mm_to_inches converts correctly."""
        assert abs(mm_to_inches(25.4) - 1.0) < 0.001

    def test_mm_to_inches_none(self):
        """mm_to_inches handles None."""
        assert mm_to_inches(None) is None
