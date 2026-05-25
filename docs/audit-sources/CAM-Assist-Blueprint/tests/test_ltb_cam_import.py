"""
Tests for CAM Assist LTB CAM output importer.

These tests verify that the importer:
- Validates LTB output against the contract
- Rejects malformed input with specific error messages
- Transforms LTB output to valid strategy JSON
- Injects CAM-Assist constitutional properties unconditionally
- Never reads non-execution declarations from LTB output
"""

import json
import pytest
from pathlib import Path
import subprocess
import sys

SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
IMPORTER_SCRIPT = SCRIPTS_DIR / "import_ltb_cam_output.py"


def create_valid_ltb_output() -> dict:
    """Create a valid LTB CAM output structure per contract."""
    return {
        "ltb_cam_output_version": "1.0.0",
        "operation": {
            "operation_type": "inlay_pocket",
            "target_feature": "headstock",
            "cut_intent": "pocket",
            "method": "vcarve",
        },
        "geometry": {
            "dxf_file": "geometry.dxf",
            "primary_layer": "INLAY_POCKET",
            "reference_layers": ["OUTLINE"],
        },
        "toolpath": {
            "format": "ltb_toolpath_v1",
            "data": {"paths": []},
        },
        "tool": {
            "tool_type": "vbit",
            "diameter_mm": 6.35,
            "angle_deg": 60,
            "description": "60 degree V-bit",
        },
        "parameters": {
            "depth_mm": 3.0,
            "feed_mm_min": 500,
            "spindle_rpm": 18000,
            "depth_per_pass_mm": 1.5,
        },
        "material": {
            "material_class": "hardwood",
            "species": "Ebony",
            "hardness_janka": 3220,
            "grain_direction": "along_headstock",
        },
        "units": {
            "linear": "mm",
            "angular": "deg",
        },
        "coordinate_frame": {
            "origin": "headstock_center",
            "x_axis": "along_headstock",
            "y_axis": "across_headstock",
            "z_axis": "into_material",
        },
        "provenance": {
            "source_spec_id": "les-paul-custom-2026",
            "ltb_version": "2.1.0",
            "created_at": "2026-05-25T10:00:00Z",
            "created_by": "vcarve_router",
        },
    }


def run_importer(
    input_path: Path,
    output_path: Path,
    units: str = "inches",
    quiet: bool = False,
) -> tuple[int, str, str]:
    """Run the importer and return (exit_code, stdout, stderr)."""
    cmd = [
        sys.executable,
        str(IMPORTER_SCRIPT),
        str(input_path),
        "--out",
        str(output_path),
        "--units",
        units,
    ]
    if quiet:
        cmd.append("--quiet")
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr


class TestLtbOutputValidation:
    """Tests for LTB output validation."""

    def test_valid_ltb_output_imports(self, tmp_path):
        """Valid LTB output should import successfully."""
        ltb_data = create_valid_ltb_output()
        input_file = tmp_path / "cam_output.json"
        input_file.write_text(json.dumps(ltb_data))

        output_file = tmp_path / "strategy.json"
        exit_code, stdout, stderr = run_importer(input_file, output_file)

        assert exit_code == 0
        assert output_file.exists()

    def test_missing_operation_type_rejected(self, tmp_path):
        """Missing operation_type should fail with specific error."""
        ltb_data = create_valid_ltb_output()
        del ltb_data["operation"]["operation_type"]
        input_file = tmp_path / "cam_output.json"
        input_file.write_text(json.dumps(ltb_data))

        output_file = tmp_path / "strategy.json"
        exit_code, stdout, stderr = run_importer(input_file, output_file)

        assert exit_code == 1
        assert "operation.operation_type" in stderr

    def test_missing_tool_diameter_rejected(self, tmp_path):
        """Missing tool diameter should fail with specific error."""
        ltb_data = create_valid_ltb_output()
        del ltb_data["tool"]["diameter_mm"]
        input_file = tmp_path / "cam_output.json"
        input_file.write_text(json.dumps(ltb_data))

        output_file = tmp_path / "strategy.json"
        exit_code, stdout, stderr = run_importer(input_file, output_file)

        assert exit_code == 1
        assert "tool.diameter_mm" in stderr

    def test_missing_depth_rejected(self, tmp_path):
        """Missing depth should fail with specific error."""
        ltb_data = create_valid_ltb_output()
        del ltb_data["parameters"]["depth_mm"]
        input_file = tmp_path / "cam_output.json"
        input_file.write_text(json.dumps(ltb_data))

        output_file = tmp_path / "strategy.json"
        exit_code, stdout, stderr = run_importer(input_file, output_file)

        assert exit_code == 1
        assert "parameters.depth_mm" in stderr

    def test_missing_provenance_rejected(self, tmp_path):
        """Missing provenance fields should fail."""
        ltb_data = create_valid_ltb_output()
        del ltb_data["provenance"]["source_spec_id"]
        input_file = tmp_path / "cam_output.json"
        input_file.write_text(json.dumps(ltb_data))

        output_file = tmp_path / "strategy.json"
        exit_code, stdout, stderr = run_importer(input_file, output_file)

        assert exit_code == 1
        assert "provenance.source_spec_id" in stderr

    def test_empty_operation_type_rejected(self, tmp_path):
        """Empty operation_type string should fail."""
        ltb_data = create_valid_ltb_output()
        ltb_data["operation"]["operation_type"] = ""
        input_file = tmp_path / "cam_output.json"
        input_file.write_text(json.dumps(ltb_data))

        output_file = tmp_path / "strategy.json"
        exit_code, stdout, stderr = run_importer(input_file, output_file)

        assert exit_code == 1
        assert "operation.operation_type" in stderr

    def test_wrong_linear_units_rejected(self, tmp_path):
        """Linear units must be 'mm' per contract."""
        ltb_data = create_valid_ltb_output()
        ltb_data["units"]["linear"] = "inches"
        input_file = tmp_path / "cam_output.json"
        input_file.write_text(json.dumps(ltb_data))

        output_file = tmp_path / "strategy.json"
        exit_code, stdout, stderr = run_importer(input_file, output_file)

        assert exit_code == 1
        assert "mm" in stderr

    def test_malformed_json_rejected(self, tmp_path):
        """Malformed JSON should fail."""
        input_file = tmp_path / "cam_output.json"
        input_file.write_text("{ invalid json }")

        output_file = tmp_path / "strategy.json"
        exit_code, stdout, stderr = run_importer(input_file, output_file)

        assert exit_code == 1

    def test_missing_file_rejected(self, tmp_path):
        """Missing input file should fail with exit code 2."""
        input_file = tmp_path / "nonexistent.json"
        output_file = tmp_path / "strategy.json"

        exit_code, stdout, stderr = run_importer(input_file, output_file)

        assert exit_code == 2


class TestStrategyTransformation:
    """Tests for LTB to strategy transformation."""

    def test_operation_type_passed_through(self, tmp_path):
        """operation_type should be read from LTB output."""
        ltb_data = create_valid_ltb_output()
        ltb_data["operation"]["operation_type"] = "binding_channel"
        input_file = tmp_path / "cam_output.json"
        input_file.write_text(json.dumps(ltb_data))

        output_file = tmp_path / "strategy.json"
        run_importer(input_file, output_file)

        strategy = json.loads(output_file.read_text())
        assert strategy["operation_intent"]["operation_type"] == "binding_channel"

    def test_target_feature_passed_through(self, tmp_path):
        """target_feature should be read from LTB output."""
        ltb_data = create_valid_ltb_output()
        ltb_data["operation"]["target_feature"] = "body"
        input_file = tmp_path / "cam_output.json"
        input_file.write_text(json.dumps(ltb_data))

        output_file = tmp_path / "strategy.json"
        run_importer(input_file, output_file)

        strategy = json.loads(output_file.read_text())
        assert strategy["operation_intent"]["target_feature"] == "body"

    def test_mm_to_inches_conversion(self, tmp_path):
        """Dimensions should convert from mm to inches."""
        ltb_data = create_valid_ltb_output()
        ltb_data["parameters"]["depth_mm"] = 25.4  # 1 inch
        ltb_data["tool"]["diameter_mm"] = 6.35  # 0.25 inch
        input_file = tmp_path / "cam_output.json"
        input_file.write_text(json.dumps(ltb_data))

        output_file = tmp_path / "strategy.json"
        run_importer(input_file, output_file, units="inches")

        strategy = json.loads(output_file.read_text())
        assert strategy["units"] == "inches"
        assert abs(strategy["operation"]["parameters"]["depth"] - 1.0) < 0.001
        assert abs(strategy["operation"]["tool"]["diameter"] - 0.25) < 0.001

    def test_mm_units_no_conversion(self, tmp_path):
        """With --units mm, dimensions should not convert."""
        ltb_data = create_valid_ltb_output()
        ltb_data["parameters"]["depth_mm"] = 3.0
        input_file = tmp_path / "cam_output.json"
        input_file.write_text(json.dumps(ltb_data))

        output_file = tmp_path / "strategy.json"
        run_importer(input_file, output_file, units="mm")

        strategy = json.loads(output_file.read_text())
        assert strategy["units"] == "mm"
        assert strategy["operation"]["parameters"]["depth"] == 3.0

    def test_strategy_version_is_1_2(self, tmp_path):
        """Output should have strategy_version 1.2."""
        ltb_data = create_valid_ltb_output()
        input_file = tmp_path / "cam_output.json"
        input_file.write_text(json.dumps(ltb_data))

        output_file = tmp_path / "strategy.json"
        run_importer(input_file, output_file)

        strategy = json.loads(output_file.read_text())
        assert strategy["strategy_version"] == "1.2"

    def test_provenance_includes_ltb_source(self, tmp_path):
        """Provenance should include LTB version and timestamp."""
        ltb_data = create_valid_ltb_output()
        ltb_data["provenance"]["ltb_version"] = "2.5.0"
        ltb_data["provenance"]["created_at"] = "2026-05-25T12:00:00Z"
        input_file = tmp_path / "cam_output.json"
        input_file.write_text(json.dumps(ltb_data))

        output_file = tmp_path / "strategy.json"
        run_importer(input_file, output_file)

        strategy = json.loads(output_file.read_text())
        assert strategy["provenance"]["ltb_version"] == "2.5.0"
        assert strategy["provenance"]["ltb_created_at"] == "2026-05-25T12:00:00Z"


class TestNonExecutionInvariant:
    """Tests for CAM-Assist constitutional properties."""

    def test_non_execution_declaration_always_true(self, tmp_path):
        """non_execution_declaration must be true regardless of LTB output."""
        ltb_data = create_valid_ltb_output()
        input_file = tmp_path / "cam_output.json"
        input_file.write_text(json.dumps(ltb_data))

        output_file = tmp_path / "strategy.json"
        run_importer(input_file, output_file)

        strategy = json.loads(output_file.read_text())
        assert strategy["operation_intent"]["non_execution_declaration"] is True
        assert strategy["safety_boundary"]["non_execution_declaration"] is True

    def test_human_review_required_always_true(self, tmp_path):
        """human_review_required must be true."""
        ltb_data = create_valid_ltb_output()
        input_file = tmp_path / "cam_output.json"
        input_file.write_text(json.dumps(ltb_data))

        output_file = tmp_path / "strategy.json"
        run_importer(input_file, output_file)

        strategy = json.loads(output_file.read_text())
        assert strategy["safety_boundary"]["human_review_required"] is True

    def test_execution_authority_claim_always_false(self, tmp_path):
        """execution_authority_claim must be false."""
        ltb_data = create_valid_ltb_output()
        input_file = tmp_path / "cam_output.json"
        input_file.write_text(json.dumps(ltb_data))

        output_file = tmp_path / "strategy.json"
        run_importer(input_file, output_file)

        strategy = json.loads(output_file.read_text())
        assert strategy["safety_boundary"]["execution_authority_claim"] is False

    def test_approval_state_always_pending(self, tmp_path):
        """Imported packages must start in pending state."""
        ltb_data = create_valid_ltb_output()
        input_file = tmp_path / "cam_output.json"
        input_file.write_text(json.dumps(ltb_data))

        output_file = tmp_path / "strategy.json"
        run_importer(input_file, output_file)

        strategy = json.loads(output_file.read_text())
        assert strategy["approval_state"] == "pending"

    def test_ltb_non_execution_false_ignored(self, tmp_path):
        """
        If LTB output contains non_execution_declaration: false,
        it must be ignored — CAM-Assist injects true unconditionally.
        """
        ltb_data = create_valid_ltb_output()
        # Attempt to sneak in a false declaration
        ltb_data["non_execution_declaration"] = False
        ltb_data["operation"]["non_execution_declaration"] = False
        input_file = tmp_path / "cam_output.json"
        input_file.write_text(json.dumps(ltb_data))

        output_file = tmp_path / "strategy.json"
        run_importer(input_file, output_file)

        strategy = json.loads(output_file.read_text())
        # CAM-Assist constitutional properties are injected, not read
        assert strategy["operation_intent"]["non_execution_declaration"] is True
        assert strategy["safety_boundary"]["non_execution_declaration"] is True

    def test_ltb_approval_approved_ignored(self, tmp_path):
        """
        If LTB output contains approval_state: approved,
        it must be ignored — imported packages always start pending.
        """
        ltb_data = create_valid_ltb_output()
        ltb_data["approval_state"] = "approved"
        input_file = tmp_path / "cam_output.json"
        input_file.write_text(json.dumps(ltb_data))

        output_file = tmp_path / "strategy.json"
        run_importer(input_file, output_file)

        strategy = json.loads(output_file.read_text())
        assert strategy["approval_state"] == "pending"


class TestDirectoryInput:
    """Tests for directory-based input."""

    def test_directory_with_cam_output_json(self, tmp_path):
        """Should accept directory containing cam_output.json."""
        ltb_data = create_valid_ltb_output()
        input_dir = tmp_path / "ltb_output"
        input_dir.mkdir()
        (input_dir / "cam_output.json").write_text(json.dumps(ltb_data))

        output_file = tmp_path / "strategy.json"
        exit_code, stdout, stderr = run_importer(input_dir, output_file)

        assert exit_code == 0
        assert output_file.exists()

    def test_directory_missing_cam_output_json(self, tmp_path):
        """Should fail if directory lacks cam_output.json."""
        input_dir = tmp_path / "empty_dir"
        input_dir.mkdir()

        output_file = tmp_path / "strategy.json"
        exit_code, stdout, stderr = run_importer(input_dir, output_file)

        assert exit_code == 2


class TestDxfCopy:
    """Tests for DXF file handling."""

    def test_dxf_copied_to_output_directory(self, tmp_path):
        """DXF file should be copied alongside strategy.json."""
        ltb_data = create_valid_ltb_output()
        ltb_data["geometry"]["dxf_file"] = "inlay.dxf"

        input_dir = tmp_path / "ltb_output"
        input_dir.mkdir()
        (input_dir / "cam_output.json").write_text(json.dumps(ltb_data))
        (input_dir / "inlay.dxf").write_text("FAKE DXF CONTENT")

        output_dir = tmp_path / "output"
        output_dir.mkdir()
        output_file = output_dir / "strategy.json"

        exit_code, stdout, stderr = run_importer(input_dir, output_file)

        assert exit_code == 0
        assert (output_dir / "inlay.dxf").exists()

    def test_missing_dxf_does_not_fail(self, tmp_path):
        """Import should succeed even if DXF is missing (just not copied)."""
        ltb_data = create_valid_ltb_output()
        input_file = tmp_path / "cam_output.json"
        input_file.write_text(json.dumps(ltb_data))

        output_file = tmp_path / "strategy.json"
        exit_code, stdout, stderr = run_importer(input_file, output_file)

        assert exit_code == 0


class TestQuietMode:
    """Tests for quiet mode."""

    def test_quiet_mode_success(self, tmp_path):
        """Quiet mode should produce no stdout on success."""
        ltb_data = create_valid_ltb_output()
        input_file = tmp_path / "cam_output.json"
        input_file.write_text(json.dumps(ltb_data))

        output_file = tmp_path / "strategy.json"
        exit_code, stdout, stderr = run_importer(input_file, output_file, quiet=True)

        assert exit_code == 0
        assert stdout.strip() == ""

    def test_quiet_mode_error_still_prints(self, tmp_path):
        """Quiet mode should still print errors to stderr."""
        ltb_data = create_valid_ltb_output()
        del ltb_data["operation"]["operation_type"]
        input_file = tmp_path / "cam_output.json"
        input_file.write_text(json.dumps(ltb_data))

        output_file = tmp_path / "strategy.json"
        exit_code, stdout, stderr = run_importer(input_file, output_file, quiet=True)

        assert exit_code == 1
        assert "operation_type" in stderr
