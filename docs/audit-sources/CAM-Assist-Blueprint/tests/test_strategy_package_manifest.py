"""
Tests for CAM Assist strategy package manifest validator.

These tests verify that the validator correctly:
- Accepts valid manifests
- Rejects invalid structures
- Rejects execution authority violations
- Validates referenced file existence
- Warns on missing optional fields
"""

import json
import pytest
from pathlib import Path
import tempfile
import subprocess
import sys


SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
EXAMPLES_DIR = Path(__file__).parent.parent / "examples"
VALID_DIR = EXAMPLES_DIR / "valid"

VALIDATOR_SCRIPT = SCRIPTS_DIR / "validate_manifest.py"


def run_validator(input_path: Path) -> tuple[int, str, str]:
    """Run the manifest validator and return (exit_code, stdout, stderr)."""
    cmd = [sys.executable, str(VALIDATOR_SCRIPT), str(input_path)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr


@pytest.fixture
def minimal_valid_manifest(tmp_path) -> dict:
    """Return a minimal valid manifest with required files created."""
    # Create required files
    strategy_file = tmp_path / "strategy.json"
    strategy_file.write_text('{"test": true}')

    review_file = tmp_path / "review.md"
    review_file.write_text("# Review")

    return {
        "manifest_version": "1.0.0",
        "package_type": "cam_assist_strategy_package",
        "operation_type": "fret_slot_strategy",
        "strategy_file": "strategy.json",
        "review_packet_file": "review.md",
        "source_geometry_files": [],
        "created_at": "2026-05-21T12:00:00Z",
        "cam_assist_version": "0.4.0",
        "authority": {
            "non_execution_declaration": True,
            "execution_authority_claim": False,
            "requires_human_review": True,
        },
        "provenance": {
            "source_spec_id": "test-spec",
            "created_by": "test",
            "derivation_notes": "test notes",
        },
    }


class TestValidManifest:
    """Tests for valid manifest acceptance."""

    def test_valid_example_passes(self):
        """The valid example manifest should pass validation."""
        manifest_file = VALID_DIR / "fret_slot_strategy_manifest.json"
        if not manifest_file.exists():
            pytest.skip("Valid example manifest not found")

        exit_code, stdout, stderr = run_validator(manifest_file)
        assert exit_code == 0, f"Expected pass: {stderr}"
        assert "PASS" in stdout

    def test_minimal_valid_manifest(self, minimal_valid_manifest, tmp_path):
        """Minimal valid manifest should pass."""
        manifest_file = tmp_path / "manifest.json"
        manifest_file.write_text(json.dumps(minimal_valid_manifest))

        exit_code, stdout, stderr = run_validator(manifest_file)
        assert exit_code == 0, f"Expected pass: {stderr}"


class TestMissingFields:
    """Tests for missing required fields."""

    def test_missing_strategy_file_field(self, minimal_valid_manifest, tmp_path):
        """Missing strategy_file field should fail."""
        del minimal_valid_manifest["strategy_file"]
        manifest_file = tmp_path / "manifest.json"
        manifest_file.write_text(json.dumps(minimal_valid_manifest))

        exit_code, stdout, stderr = run_validator(manifest_file)
        assert exit_code == 1
        assert "strategy_file" in stderr

    def test_missing_review_packet_field(self, minimal_valid_manifest, tmp_path):
        """Missing review_packet_file field should fail."""
        del minimal_valid_manifest["review_packet_file"]
        manifest_file = tmp_path / "manifest.json"
        manifest_file.write_text(json.dumps(minimal_valid_manifest))

        exit_code, stdout, stderr = run_validator(manifest_file)
        assert exit_code == 1
        assert "review_packet_file" in stderr

    def test_missing_authority_block(self, minimal_valid_manifest, tmp_path):
        """Missing authority block should fail."""
        del minimal_valid_manifest["authority"]
        manifest_file = tmp_path / "manifest.json"
        manifest_file.write_text(json.dumps(minimal_valid_manifest))

        exit_code, stdout, stderr = run_validator(manifest_file)
        assert exit_code == 1
        assert "authority" in stderr

    def test_missing_package_type(self, minimal_valid_manifest, tmp_path):
        """Missing package_type should fail."""
        del minimal_valid_manifest["package_type"]
        manifest_file = tmp_path / "manifest.json"
        manifest_file.write_text(json.dumps(minimal_valid_manifest))

        exit_code, stdout, stderr = run_validator(manifest_file)
        assert exit_code == 1


class TestFileExistence:
    """Tests for referenced file existence validation."""

    def test_missing_strategy_file(self, minimal_valid_manifest, tmp_path):
        """Missing referenced strategy file should fail."""
        # Remove the strategy file created by fixture
        (tmp_path / "strategy.json").unlink()

        manifest_file = tmp_path / "manifest.json"
        manifest_file.write_text(json.dumps(minimal_valid_manifest))

        exit_code, stdout, stderr = run_validator(manifest_file)
        assert exit_code == 1
        assert "not found" in stderr.lower()

    def test_missing_review_packet_file(self, minimal_valid_manifest, tmp_path):
        """Missing referenced review packet file should fail."""
        # Remove the review file created by fixture
        (tmp_path / "review.md").unlink()

        manifest_file = tmp_path / "manifest.json"
        manifest_file.write_text(json.dumps(minimal_valid_manifest))

        exit_code, stdout, stderr = run_validator(manifest_file)
        assert exit_code == 1
        assert "not found" in stderr.lower()

    def test_missing_geometry_file(self, minimal_valid_manifest, tmp_path):
        """Missing referenced geometry file should fail."""
        minimal_valid_manifest["source_geometry_files"] = ["missing.dxf"]

        manifest_file = tmp_path / "manifest.json"
        manifest_file.write_text(json.dumps(minimal_valid_manifest))

        exit_code, stdout, stderr = run_validator(manifest_file)
        assert exit_code == 1
        assert "not found" in stderr.lower()


class TestExecutionAuthorityRejection:
    """Tests for execution authority violation rejection."""

    def test_non_execution_declaration_false(self, minimal_valid_manifest, tmp_path):
        """non_execution_declaration: false should fail."""
        minimal_valid_manifest["authority"]["non_execution_declaration"] = False

        manifest_file = tmp_path / "manifest.json"
        manifest_file.write_text(json.dumps(minimal_valid_manifest))

        exit_code, stdout, stderr = run_validator(manifest_file)
        assert exit_code == 1
        assert "EXECUTION AUTHORITY" in stderr

    def test_execution_authority_claim_true(self, minimal_valid_manifest, tmp_path):
        """execution_authority_claim: true should fail."""
        minimal_valid_manifest["authority"]["execution_authority_claim"] = True

        manifest_file = tmp_path / "manifest.json"
        manifest_file.write_text(json.dumps(minimal_valid_manifest))

        exit_code, stdout, stderr = run_validator(manifest_file)
        assert exit_code == 1
        assert "EXECUTION AUTHORITY" in stderr

    def test_requires_human_review_false(self, minimal_valid_manifest, tmp_path):
        """requires_human_review: false should fail."""
        minimal_valid_manifest["authority"]["requires_human_review"] = False

        manifest_file = tmp_path / "manifest.json"
        manifest_file.write_text(json.dumps(minimal_valid_manifest))

        exit_code, stdout, stderr = run_validator(manifest_file)
        assert exit_code == 1
        assert "AUTHORITY VIOLATION" in stderr


class TestInvalidValues:
    """Tests for invalid field values."""

    def test_wrong_package_type(self, minimal_valid_manifest, tmp_path):
        """Wrong package_type should fail."""
        minimal_valid_manifest["package_type"] = "wrong_type"

        manifest_file = tmp_path / "manifest.json"
        manifest_file.write_text(json.dumps(minimal_valid_manifest))

        exit_code, stdout, stderr = run_validator(manifest_file)
        assert exit_code == 1
        assert "package_type" in stderr

    def test_invalid_version_format(self, minimal_valid_manifest, tmp_path):
        """Invalid manifest_version format should fail."""
        minimal_valid_manifest["manifest_version"] = "invalid"

        manifest_file = tmp_path / "manifest.json"
        manifest_file.write_text(json.dumps(minimal_valid_manifest))

        exit_code, stdout, stderr = run_validator(manifest_file)
        assert exit_code == 1
        assert "version" in stderr.lower()


class TestWarnings:
    """Tests for warning generation."""

    def test_empty_geometry_files_warning(self, minimal_valid_manifest, tmp_path):
        """Empty source_geometry_files should produce warning."""
        manifest_file = tmp_path / "manifest.json"
        manifest_file.write_text(json.dumps(minimal_valid_manifest))

        exit_code, stdout, stderr = run_validator(manifest_file)
        assert exit_code == 0
        assert "WARN" in stdout
        assert "geometry" in stdout.lower()

    def test_missing_provenance_warning(self, minimal_valid_manifest, tmp_path):
        """Missing provenance fields should produce warnings."""
        minimal_valid_manifest["provenance"] = {}

        manifest_file = tmp_path / "manifest.json"
        manifest_file.write_text(json.dumps(minimal_valid_manifest))

        exit_code, stdout, stderr = run_validator(manifest_file)
        assert exit_code == 0
        assert "WARN" in stdout

    def test_missing_cam_assist_version_warning(self, minimal_valid_manifest, tmp_path):
        """Missing cam_assist_version should produce warning."""
        del minimal_valid_manifest["cam_assist_version"]

        manifest_file = tmp_path / "manifest.json"
        manifest_file.write_text(json.dumps(minimal_valid_manifest))

        exit_code, stdout, stderr = run_validator(manifest_file)
        assert exit_code == 0
        assert "WARN" in stdout
        assert "cam_assist_version" in stdout


class TestFileErrors:
    """Tests for file error handling."""

    def test_nonexistent_manifest(self, tmp_path):
        """Nonexistent manifest file should return exit code 2."""
        fake_manifest = tmp_path / "nonexistent.json"

        exit_code, stdout, stderr = run_validator(fake_manifest)
        assert exit_code == 2

    def test_malformed_json(self, tmp_path):
        """Malformed JSON should return exit code 1."""
        manifest_file = tmp_path / "bad.json"
        manifest_file.write_text("{invalid json")

        exit_code, stdout, stderr = run_validator(manifest_file)
        assert exit_code == 1
        assert "FAIL" in stderr
