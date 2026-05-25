"""
Tests for CAM Assist review packet generator.

These tests verify that the generator:
- Produces valid Markdown from valid strategy packages
- Rejects invalid strategies before generating output
- Rejects execution authority claims
- Includes all required sections
- Remains non-executing
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
INVALID_DIR = EXAMPLES_DIR / "invalid"

GENERATOR_SCRIPT = SCRIPTS_DIR / "generate_review_packet.py"


def run_generator(input_path: Path, output_path: Path = None) -> tuple[int, str, str]:
    """Run the generator script and return (exit_code, stdout, stderr)."""
    cmd = [sys.executable, str(GENERATOR_SCRIPT), str(input_path)]
    if output_path:
        cmd.extend(["--out", str(output_path)])

    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr


class TestValidGeneration:
    """Tests for successful review packet generation."""

    def test_valid_example_generates_markdown(self):
        """Valid example should generate a Markdown review packet."""
        input_file = VALID_DIR / "fret_slot_strategy.json"
        if not input_file.exists():
            pytest.skip("Valid example file not found")

        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "review.md"
            exit_code, stdout, stderr = run_generator(input_file, output_file)

            assert exit_code == 0, f"Expected exit code 0, got {exit_code}: {stderr}"
            assert "PASS" in stdout
            assert output_file.exists()

            content = output_file.read_text()
            assert len(content) > 0

    def test_default_output_path(self):
        """Default output should be <input>_review_packet.md."""
        input_file = VALID_DIR / "fret_slot_strategy.json"
        if not input_file.exists():
            pytest.skip("Valid example file not found")

        expected_output = VALID_DIR / "fret_slot_strategy_review_packet.md"

        exit_code, stdout, stderr = run_generator(input_file)

        assert exit_code == 0, f"Expected exit code 0: {stderr}"
        assert expected_output.exists()

    def test_custom_output_path(self):
        """Custom --out path should be respected."""
        input_file = VALID_DIR / "fret_slot_strategy.json"
        if not input_file.exists():
            pytest.skip("Valid example file not found")

        with tempfile.TemporaryDirectory() as tmpdir:
            custom_output = Path(tmpdir) / "custom_name.md"
            exit_code, stdout, stderr = run_generator(input_file, custom_output)

            assert exit_code == 0
            assert custom_output.exists()
            assert "custom_name.md" in stdout


class TestRequiredSections:
    """Tests for required sections in generated review packet."""

    @pytest.fixture
    def generated_content(self):
        """Generate review packet and return content."""
        input_file = VALID_DIR / "fret_slot_strategy.json"
        if not input_file.exists():
            pytest.skip("Valid example file not found")

        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "review.md"
            exit_code, _, _ = run_generator(input_file, output_file)
            assert exit_code == 0
            return output_file.read_text()

    def test_includes_non_execution_notice(self, generated_content):
        """Review packet must include non-execution notice."""
        assert "NON-EXECUTION NOTICE" in generated_content
        assert "advisory only" in generated_content
        assert "does not authorize machine execution" in generated_content
        assert "does not generate G-code" in generated_content

    def test_includes_operator_signoff(self, generated_content):
        """Review packet must include operator sign-off section."""
        assert "Operator Sign-Off" in generated_content
        assert "Operator Name:" in generated_content
        assert "Signature:" in generated_content

    def test_includes_material_context(self, generated_content):
        """Review packet must include material context."""
        assert "Material Context" in generated_content
        assert "Material Class" in generated_content

    def test_includes_coordinate_frame(self, generated_content):
        """Review packet must include coordinate frame."""
        assert "Coordinate Frame" in generated_content
        assert "Origin" in generated_content
        assert "X-Axis" in generated_content

    def test_includes_safety_boundary(self, generated_content):
        """Review packet must include safety boundary."""
        assert "Safety Boundary" in generated_content
        assert "Non-Execution Declaration" in generated_content
        assert "Human Review Required" in generated_content

    def test_includes_fret_slot_summary(self, generated_content):
        """Review packet must include fret slot summary."""
        assert "Fret Slot Summary" in generated_content
        assert "Fret Count" in generated_content
        assert "Scale Length" in generated_content

    def test_includes_human_review_requirements(self, generated_content):
        """Review packet must include human review requirements."""
        assert "Human Review Requirements" in generated_content
        assert "operator must verify" in generated_content

    def test_includes_warnings_section(self, generated_content):
        """Review packet must include warnings section."""
        assert "Warnings and Failure Modes" in generated_content


class TestValidationFailures:
    """Tests for validation failure handling."""

    def test_invalid_strategy_fails(self):
        """Invalid strategy should fail before generating output."""
        invalid_file = INVALID_DIR / "missing_units.json"
        if not invalid_file.exists():
            pytest.skip("Invalid example file not found")

        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "should_not_exist.md"
            exit_code, stdout, stderr = run_generator(invalid_file, output_file)

            assert exit_code == 1
            assert "FAIL" in stderr
            assert not output_file.exists()

    def test_malformed_json_fails(self):
        """Malformed JSON should fail with exit code 2."""
        invalid_file = INVALID_DIR / "malformed_json.json"
        if not invalid_file.exists():
            pytest.skip("Malformed JSON file not found")

        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "should_not_exist.md"
            exit_code, stdout, stderr = run_generator(invalid_file, output_file)

            assert exit_code == 2
            assert not output_file.exists()

    def test_nonexistent_file_fails(self):
        """Nonexistent file should fail with exit code 2."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_input = Path(tmpdir) / "does_not_exist.json"
            output_file = Path(tmpdir) / "output.md"
            exit_code, stdout, stderr = run_generator(fake_input, output_file)

            assert exit_code == 2
            assert not output_file.exists()


class TestExecutionAuthorityRejection:
    """Tests for execution authority claim rejection."""

    def test_execution_authority_claim_fails(self):
        """execution_authority_claim: true should fail."""
        invalid_file = INVALID_DIR / "execution_authority_claim.json"
        if not invalid_file.exists():
            pytest.skip("Execution authority claim file not found")

        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "should_not_exist.md"
            exit_code, stdout, stderr = run_generator(invalid_file, output_file)

            assert exit_code == 1
            assert "FAIL" in stderr
            assert not output_file.exists()

    def test_non_execution_false_in_intent_fails(self):
        """non_execution_declaration: false in operation_intent should fail."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a strategy with non_execution_declaration: false
            bad_strategy = {
                "strategy_version": "1.2",
                "strategy_id": "test-bad-intent",
                "units": "inches",
                "coordinate_frame": {
                    "origin": "nut",
                    "x_axis": "along",
                    "y_axis": "across"
                },
                "provenance": {
                    "cam_assist_version": "0.3.0",
                    "created_at": "2026-05-21T12:00:00Z"
                },
                "operation_intent": {
                    "operation_type": "fret_slots",
                    "target_feature": "fretboard",
                    "cut_intent": "slot",
                    "non_execution_declaration": False  # BAD
                },
                "material_context": {"material_class": "hardwood"},
                "safety_boundary": {
                    "non_execution_declaration": True,
                    "human_review_required": True
                },
                "geometry": {"dxf_file": "test.dxf", "primary_layer": "SLOTS"},
                "operation": {
                    "type": "slot_cut",
                    "tool": {"tool_type": "cutter"},
                    "parameters": {"depth": 0.060}
                },
                "approval_state": "pending"
            }

            input_file = Path(tmpdir) / "bad_intent.json"
            input_file.write_text(json.dumps(bad_strategy))

            output_file = Path(tmpdir) / "output.md"
            exit_code, stdout, stderr = run_generator(input_file, output_file)

            assert exit_code == 1
            assert not output_file.exists()


class TestNonExecution:
    """Tests verifying the generator does not execute anything."""

    def test_generator_produces_only_markdown(self):
        """Generator should only produce Markdown output, no side effects."""
        input_file = VALID_DIR / "fret_slot_strategy.json"
        if not input_file.exists():
            pytest.skip("Valid example file not found")

        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "review.md"
            marker_file = Path(tmpdir) / "marker.txt"

            exit_code, _, _ = run_generator(input_file, output_file)

            assert exit_code == 0
            # Only the output file should exist
            files_created = list(Path(tmpdir).iterdir())
            assert len(files_created) == 1
            assert files_created[0].name == "review.md"
            assert not marker_file.exists()

    def test_output_is_valid_markdown(self):
        """Generated output should be valid Markdown text."""
        input_file = VALID_DIR / "fret_slot_strategy.json"
        if not input_file.exists():
            pytest.skip("Valid example file not found")

        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "review.md"
            exit_code, _, _ = run_generator(input_file, output_file)

            assert exit_code == 0
            content = output_file.read_text(encoding="utf-8")

            # Basic Markdown structure checks
            assert content.startswith("#")  # Starts with heading
            assert "##" in content  # Has sections
            assert "|" in content  # Has tables
            assert "---" in content  # Has horizontal rules
