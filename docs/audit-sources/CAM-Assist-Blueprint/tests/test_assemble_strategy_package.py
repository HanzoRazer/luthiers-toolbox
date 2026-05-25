"""
Tests for CAM Assist strategy package assembly CLI.

These tests verify that the assembler correctly:
- Assembles valid strategy into package directory
- Creates all required package files
- Generates valid manifest
- Preserves non-execution boundary
- Handles overwrite scenarios safely
- Rejects invalid strategies
"""

import json
import pytest
from pathlib import Path
import subprocess
import sys
import shutil


SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
EXAMPLES_DIR = Path(__file__).parent.parent / "examples"
VALID_DIR = EXAMPLES_DIR / "valid"

ASSEMBLER_SCRIPT = SCRIPTS_DIR / "assemble_strategy_package.py"
MANIFEST_VALIDATOR = SCRIPTS_DIR / "validate_manifest.py"


def run_assembler(
    input_path: Path,
    output_dir: Path | None = None,
    force: bool = False,
) -> tuple[int, str, str]:
    """Run the package assembler and return (exit_code, stdout, stderr)."""
    cmd = [sys.executable, str(ASSEMBLER_SCRIPT), str(input_path)]
    if output_dir:
        cmd.extend(["--out", str(output_dir)])
    if force:
        cmd.append("--force")
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr


def run_manifest_validator(manifest_path: Path) -> tuple[int, str, str]:
    """Run the manifest validator and return (exit_code, stdout, stderr)."""
    cmd = [sys.executable, str(MANIFEST_VALIDATOR), str(manifest_path)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr


@pytest.fixture
def valid_strategy(tmp_path) -> Path:
    """Create a minimal valid strategy JSON matching v1.2 schema."""
    strategy = {
        "strategy_version": "1.2",
        "strategy_id": "test-strategy",
        "units": "inches",
        "coordinate_frame": {
            "origin": "nut_centerline",
            "x_axis": "along_neck_toward_bridge",
            "y_axis": "across_fretboard_treble_positive",
            "z_axis": "into_fretboard",
            "datum_point": {"x": 0, "y": 0, "z": 0},
        },
        "provenance": {
            "source_spec_id": "test-spec",
            "cam_assist_version": "0.5.0",
            "created_by": "test",
            "created_at": "2026-05-21T12:00:00Z",
        },
        "operation_intent": {
            "operation_type": "fret_slots",
            "target_feature": "fretboard",
            "cut_intent": "slot",
            "non_execution_declaration": True,
        },
        "material_context": {
            "material_class": "hardwood",
            "species": "maple",
            "hardness_janka": 1450,
            "grain_direction": "along_fretboard_length",
        },
        "safety_boundary": {
            "non_execution_declaration": True,
            "human_review_required": True,
            "max_depth_inches": 0.060,
            "tool_diameter_inches": 0.023,
        },
        "geometry": {
            "dxf_file": "geometry.dxf",
            "primary_layer": "FRET_SLOTS",
            "reference_layers": [],
        },
        "operation": {
            "type": "slot_cut",
            "tool": {
                "reference_type": "dimension_spec",
                "tool_type": "slot_cutter",
                "diameter": 0.023,
                "description": "Fret slot cutter",
            },
            "parameters": {"depth": 0.060},
            "sequence": "sequential_from_nut",
        },
        "positions": [
            {"fret": 1, "distance_from_nut": 1.4312},
        ],
        "approval_state": "pending",
    }
    strategy_file = tmp_path / "test_strategy.json"
    strategy_file.write_text(json.dumps(strategy, indent=2))
    return strategy_file


@pytest.fixture
def invalid_strategy(tmp_path) -> Path:
    """Create an invalid strategy JSON (missing required fields)."""
    strategy = {"strategy_version": "1.2", "operation": "fret_slot"}
    strategy_file = tmp_path / "invalid_strategy.json"
    strategy_file.write_text(json.dumps(strategy))
    return strategy_file


@pytest.fixture
def execution_authority_strategy(tmp_path) -> Path:
    """Create a strategy that claims execution authority."""
    strategy = {
        "strategy_version": "1.2",
        "strategy_id": "bad-strategy",
        "units": "inches",
        "coordinate_frame": {
            "origin": "nut_centerline",
            "x_axis": "along_neck_toward_bridge",
            "y_axis": "across_fretboard_treble_positive",
            "z_axis": "into_fretboard",
            "datum_point": {"x": 0, "y": 0, "z": 0},
        },
        "provenance": {
            "source_spec_id": "test-spec",
            "cam_assist_version": "0.5.0",
            "created_by": "test",
            "created_at": "2026-05-21T12:00:00Z",
        },
        "operation_intent": {
            "operation_type": "fret_slots",
            "target_feature": "fretboard",
            "cut_intent": "slot",
            "non_execution_declaration": True,
        },
        "material_context": {
            "material_class": "hardwood",
            "species": "maple",
            "hardness_janka": 1450,
            "grain_direction": "along_fretboard_length",
        },
        "safety_boundary": {
            "non_execution_declaration": True,
            "human_review_required": True,
            "max_depth_inches": 0.060,
            "tool_diameter_inches": 0.023,
            "execution_authority_claim": True,
        },
        "geometry": {
            "dxf_file": "geometry.dxf",
            "primary_layer": "FRET_SLOTS",
            "reference_layers": [],
        },
        "operation": {
            "type": "slot_cut",
            "tool": {
                "reference_type": "dimension_spec",
                "tool_type": "slot_cutter",
                "diameter": 0.023,
                "description": "Fret slot cutter",
            },
            "parameters": {"depth": 0.060},
            "sequence": "sequential_from_nut",
        },
        "positions": [
            {"fret": 1, "distance_from_nut": 1.4312},
        ],
        "approval_state": "pending",
    }
    strategy_file = tmp_path / "exec_auth_strategy.json"
    strategy_file.write_text(json.dumps(strategy, indent=2))
    return strategy_file


class TestPackageAssembly:
    """Tests for successful package assembly."""

    def test_valid_strategy_assembles_package(self, valid_strategy, tmp_path):
        """Valid strategy should assemble into a package."""
        output_dir = tmp_path / "output_package"
        exit_code, stdout, stderr = run_assembler(valid_strategy, output_dir)
        assert exit_code == 0, f"Expected success: {stderr}"
        assert "PASS" in stdout
        assert output_dir.exists()

    def test_package_contains_strategy_json(self, valid_strategy, tmp_path):
        """Package must contain strategy.json."""
        output_dir = tmp_path / "output_package"
        run_assembler(valid_strategy, output_dir)
        assert (output_dir / "strategy.json").exists()

    def test_package_contains_review_packet(self, valid_strategy, tmp_path):
        """Package must contain review_packet.md."""
        output_dir = tmp_path / "output_package"
        run_assembler(valid_strategy, output_dir)
        assert (output_dir / "review_packet.md").exists()

    def test_package_contains_manifest(self, valid_strategy, tmp_path):
        """Package must contain manifest.json."""
        output_dir = tmp_path / "output_package"
        run_assembler(valid_strategy, output_dir)
        assert (output_dir / "manifest.json").exists()

    def test_manifest_validates(self, valid_strategy, tmp_path):
        """Generated manifest must pass validation."""
        output_dir = tmp_path / "output_package"
        run_assembler(valid_strategy, output_dir)
        manifest_path = output_dir / "manifest.json"

        exit_code, stdout, stderr = run_manifest_validator(manifest_path)
        assert exit_code == 0, f"Manifest validation failed: {stderr}"

    def test_review_packet_contains_non_execution_notice(self, valid_strategy, tmp_path):
        """Review packet must contain non-execution notice."""
        output_dir = tmp_path / "output_package"
        run_assembler(valid_strategy, output_dir)

        review_content = (output_dir / "review_packet.md").read_text()
        assert "NON-EXECUTION" in review_content or "non-execution" in review_content.lower()

    def test_manifest_paths_are_relative(self, valid_strategy, tmp_path):
        """Manifest paths must be relative to package directory."""
        output_dir = tmp_path / "output_package"
        run_assembler(valid_strategy, output_dir)

        manifest = json.loads((output_dir / "manifest.json").read_text())
        assert manifest["strategy_file"] == "strategy.json"
        assert manifest["review_packet_file"] == "review_packet.md"
        assert "/" not in manifest["strategy_file"]
        assert "\\" not in manifest["strategy_file"]

    def test_valid_example_file_assembles(self):
        """The valid example strategy should assemble successfully."""
        example_strategy = VALID_DIR / "fret_slot_strategy.json"
        if not example_strategy.exists():
            pytest.skip("Valid example strategy not found")

        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "example_package"
            exit_code, stdout, stderr = run_assembler(example_strategy, output_dir)
            assert exit_code == 0, f"Expected success: {stderr}"


class TestValidationFailures:
    """Tests for validation failure handling."""

    def test_invalid_strategy_fails(self, invalid_strategy, tmp_path):
        """Invalid strategy should fail assembly."""
        output_dir = tmp_path / "output_package"
        exit_code, stdout, stderr = run_assembler(invalid_strategy, output_dir)
        assert exit_code == 1
        assert "FAIL" in stderr

    def test_execution_authority_claim_fails(self, execution_authority_strategy, tmp_path):
        """Strategy with execution authority claim should fail."""
        output_dir = tmp_path / "output_package"
        exit_code, stdout, stderr = run_assembler(execution_authority_strategy, output_dir)
        assert exit_code == 1
        assert "FAIL" in stderr


class TestOverwriteBehavior:
    """Tests for output directory overwrite handling."""

    def test_existing_output_without_force_fails(self, valid_strategy, tmp_path):
        """Existing output directory without --force should fail."""
        output_dir = tmp_path / "output_package"
        output_dir.mkdir()
        (output_dir / "existing_file.txt").write_text("existing")

        exit_code, stdout, stderr = run_assembler(valid_strategy, output_dir, force=False)
        assert exit_code == 1
        assert "already exists" in stderr.lower() or "force" in stderr.lower()
        assert (output_dir / "existing_file.txt").exists()

    def test_existing_output_with_force_overwrites(self, valid_strategy, tmp_path):
        """Existing output directory with --force should overwrite."""
        output_dir = tmp_path / "output_package"
        output_dir.mkdir()
        (output_dir / "existing_file.txt").write_text("existing")

        exit_code, stdout, stderr = run_assembler(valid_strategy, output_dir, force=True)
        assert exit_code == 0
        assert not (output_dir / "existing_file.txt").exists()
        assert (output_dir / "strategy.json").exists()


class TestOutputPath:
    """Tests for output path handling."""

    def test_optional_out_path_works(self, valid_strategy, tmp_path):
        """--out should set custom output directory."""
        custom_dir = tmp_path / "custom" / "nested" / "package"
        exit_code, stdout, stderr = run_assembler(valid_strategy, custom_dir)
        assert exit_code == 0
        assert custom_dir.exists()
        assert (custom_dir / "manifest.json").exists()

    def test_default_output_path(self, valid_strategy, tmp_path):
        """Default output should be ./<strategy_stem>_package/."""
        import os
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            exit_code, stdout, stderr = run_assembler(valid_strategy)
            assert exit_code == 0

            expected_dir = tmp_path / "test_strategy_package"
            assert expected_dir.exists(), f"Expected {expected_dir} to exist"
        finally:
            os.chdir(original_cwd)


class TestFileErrors:
    """Tests for file error handling."""

    def test_nonexistent_input_fails(self, tmp_path):
        """Nonexistent input file should return exit code 2."""
        fake_input = tmp_path / "nonexistent.json"
        output_dir = tmp_path / "output"

        exit_code, stdout, stderr = run_assembler(fake_input, output_dir)
        assert exit_code == 2

    def test_malformed_json_fails(self, tmp_path):
        """Malformed JSON input should fail."""
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("{invalid json")
        output_dir = tmp_path / "output"

        exit_code, stdout, stderr = run_assembler(bad_file, output_dir)
        assert exit_code == 1
        assert "FAIL" in stderr


class TestManifestContent:
    """Tests for generated manifest content."""

    def test_manifest_has_authority_block(self, valid_strategy, tmp_path):
        """Manifest must have correct authority block."""
        output_dir = tmp_path / "output_package"
        run_assembler(valid_strategy, output_dir)

        manifest = json.loads((output_dir / "manifest.json").read_text())
        assert manifest["authority"]["non_execution_declaration"] is True
        assert manifest["authority"]["execution_authority_claim"] is False
        assert manifest["authority"]["requires_human_review"] is True

    def test_manifest_has_provenance(self, valid_strategy, tmp_path):
        """Manifest must have provenance fields."""
        output_dir = tmp_path / "output_package"
        run_assembler(valid_strategy, output_dir)

        manifest = json.loads((output_dir / "manifest.json").read_text())
        assert "provenance" in manifest
        assert manifest["provenance"]["created_by"] == "cam-assist-assembly"
        assert "source_spec_id" in manifest["provenance"]
        assert "derivation_notes" in manifest["provenance"]

    def test_manifest_has_version(self, valid_strategy, tmp_path):
        """Manifest must have cam_assist_version."""
        output_dir = tmp_path / "output_package"
        run_assembler(valid_strategy, output_dir)

        manifest = json.loads((output_dir / "manifest.json").read_text())
        assert "cam_assist_version" in manifest
        assert manifest["cam_assist_version"] == "0.5.0"

    def test_manifest_operation_type_derived(self, valid_strategy, tmp_path):
        """Manifest operation_type should be derived from strategy."""
        output_dir = tmp_path / "output_package"
        run_assembler(valid_strategy, output_dir)

        manifest = json.loads((output_dir / "manifest.json").read_text())
        assert manifest["operation_type"] == "fret_slots_strategy"
