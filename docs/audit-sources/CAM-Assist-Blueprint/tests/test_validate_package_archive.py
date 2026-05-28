"""
Tests for CAM Assist strategy package archive validator CLI.

These tests verify that the validator correctly:
- Validates safe archives
- Rejects unsafe archive paths (traversal, absolute)
- Rejects missing required files
- Rejects execution authority violations
- Produces warnings for unexpected files
- Cleans up temporary extraction
- Does not execute or modify archive contents
"""

import json
import os
import pytest
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile


SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
EXAMPLES_DIR = Path(__file__).parent.parent / "examples"
PACKAGES_DIR = EXAMPLES_DIR / "packages"

VALIDATOR_SCRIPT = SCRIPTS_DIR / "validate_package_archive.py"
ASSEMBLER_SCRIPT = SCRIPTS_DIR / "assemble_strategy_package.py"
ARCHIVER_SCRIPT = SCRIPTS_DIR / "archive_strategy_package.py"


def run_validator(
    archive_path: Path,
    json_output: bool = False,
    quiet: bool = False,
) -> tuple[int, str, str]:
    """Run the archive validator and return (exit_code, stdout, stderr)."""
    cmd = [sys.executable, str(VALIDATOR_SCRIPT), str(archive_path)]
    if json_output:
        cmd.append("--json")
    if quiet:
        cmd.append("--quiet")
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr


def create_valid_archive(archive_path: Path) -> None:
    """Create a valid strategy package archive."""
    strategy = {"strategy_version": "1.2", "strategy_id": "test"}
    review_content = "# Review Packet\n\n" + ("Content line.\n" * 100)
    manifest = {
        "manifest_version": "1.0.0",
        "package_type": "cam_assist_strategy_package",
        "operation_type": "fret_slot_strategy",
        "strategy_file": "strategy.json",
        "review_packet_file": "review_packet.md",
        "source_geometry_files": ["geometry.dxf"],
        "created_at": "2026-05-22T12:00:00Z",
        "authority": {
            "non_execution_declaration": True,
            "execution_authority_claim": False,
            "requires_human_review": True,
        },
        "provenance": {
            "source_spec_id": "test-spec",
            "created_by": "test",
            "derivation_notes": "Test package",
        },
    }

    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("strategy.json", json.dumps(strategy))
        zf.writestr("review_packet.md", review_content)
        zf.writestr("manifest.json", json.dumps(manifest))
        zf.writestr("geometry.dxf", "DXF content")


def create_archive_with_traversal(archive_path: Path) -> None:
    """Create an archive with path traversal entry."""
    with zipfile.ZipFile(archive_path, "w") as zf:
        zf.writestr("../evil.txt", "malicious content")
        zf.writestr("manifest.json", "{}")


def create_archive_with_absolute_path(archive_path: Path) -> None:
    """Create an archive with absolute path entry."""
    with zipfile.ZipFile(archive_path, "w") as zf:
        zf.writestr("/etc/passwd", "malicious content")
        zf.writestr("manifest.json", "{}")


def create_archive_missing_manifest(archive_path: Path) -> None:
    """Create an archive missing manifest.json."""
    with zipfile.ZipFile(archive_path, "w") as zf:
        zf.writestr("strategy.json", "{}")
        zf.writestr("review_packet.md", "# Review")


def create_archive_missing_strategy(archive_path: Path) -> None:
    """Create an archive missing strategy.json."""
    manifest = {
        "manifest_version": "1.0.0",
        "package_type": "cam_assist_strategy_package",
        "operation_type": "test",
        "strategy_file": "strategy.json",
        "review_packet_file": "review_packet.md",
        "source_geometry_files": [],
        "created_at": "2026-05-22T12:00:00Z",
        "authority": {
            "non_execution_declaration": True,
            "execution_authority_claim": False,
            "requires_human_review": True,
        },
        "provenance": {
            "source_spec_id": "test",
            "created_by": "test",
            "derivation_notes": "test",
        },
    }
    with zipfile.ZipFile(archive_path, "w") as zf:
        zf.writestr("manifest.json", json.dumps(manifest))
        zf.writestr("review_packet.md", "# Review\n" + "x" * 1100)


def create_archive_missing_review(archive_path: Path) -> None:
    """Create an archive missing review_packet.md."""
    manifest = {
        "manifest_version": "1.0.0",
        "package_type": "cam_assist_strategy_package",
        "operation_type": "test",
        "strategy_file": "strategy.json",
        "review_packet_file": "review_packet.md",
        "source_geometry_files": [],
        "created_at": "2026-05-22T12:00:00Z",
        "authority": {
            "non_execution_declaration": True,
            "execution_authority_claim": False,
            "requires_human_review": True,
        },
        "provenance": {
            "source_spec_id": "test",
            "created_by": "test",
            "derivation_notes": "test",
        },
    }
    with zipfile.ZipFile(archive_path, "w") as zf:
        zf.writestr("manifest.json", json.dumps(manifest))
        zf.writestr("strategy.json", "{}")


def create_archive_exec_authority(archive_path: Path) -> None:
    """Create an archive with execution_authority_claim = true."""
    manifest = {
        "manifest_version": "1.0.0",
        "package_type": "cam_assist_strategy_package",
        "operation_type": "test",
        "strategy_file": "strategy.json",
        "review_packet_file": "review_packet.md",
        "source_geometry_files": [],
        "created_at": "2026-05-22T12:00:00Z",
        "authority": {
            "non_execution_declaration": True,
            "execution_authority_claim": True,
            "requires_human_review": True,
        },
        "provenance": {
            "source_spec_id": "test",
            "created_by": "test",
            "derivation_notes": "test",
        },
    }
    with zipfile.ZipFile(archive_path, "w") as zf:
        zf.writestr("manifest.json", json.dumps(manifest))
        zf.writestr("strategy.json", "{}")
        zf.writestr("review_packet.md", "# Review\n" + "x" * 1100)


def create_archive_non_execution_false(archive_path: Path) -> None:
    """Create an archive with non_execution_declaration = false."""
    manifest = {
        "manifest_version": "1.0.0",
        "package_type": "cam_assist_strategy_package",
        "operation_type": "test",
        "strategy_file": "strategy.json",
        "review_packet_file": "review_packet.md",
        "source_geometry_files": [],
        "created_at": "2026-05-22T12:00:00Z",
        "authority": {
            "non_execution_declaration": False,
            "execution_authority_claim": False,
            "requires_human_review": True,
        },
        "provenance": {
            "source_spec_id": "test",
            "created_by": "test",
            "derivation_notes": "test",
        },
    }
    with zipfile.ZipFile(archive_path, "w") as zf:
        zf.writestr("manifest.json", json.dumps(manifest))
        zf.writestr("strategy.json", "{}")
        zf.writestr("review_packet.md", "# Review\n" + "x" * 1100)


def create_archive_human_review_false(archive_path: Path) -> None:
    """Create an archive with requires_human_review = false."""
    manifest = {
        "manifest_version": "1.0.0",
        "package_type": "cam_assist_strategy_package",
        "operation_type": "test",
        "strategy_file": "strategy.json",
        "review_packet_file": "review_packet.md",
        "source_geometry_files": [],
        "created_at": "2026-05-22T12:00:00Z",
        "authority": {
            "non_execution_declaration": True,
            "execution_authority_claim": False,
            "requires_human_review": False,
        },
        "provenance": {
            "source_spec_id": "test",
            "created_by": "test",
            "derivation_notes": "test",
        },
    }
    with zipfile.ZipFile(archive_path, "w") as zf:
        zf.writestr("manifest.json", json.dumps(manifest))
        zf.writestr("strategy.json", "{}")
        zf.writestr("review_packet.md", "# Review\n" + "x" * 1100)


def create_archive_with_unexpected_file(archive_path: Path) -> None:
    """Create an archive with unexpected file."""
    strategy = {"strategy_version": "1.2", "strategy_id": "test"}
    review_content = "# Review Packet\n\n" + ("Content line.\n" * 100)
    manifest = {
        "manifest_version": "1.0.0",
        "package_type": "cam_assist_strategy_package",
        "operation_type": "fret_slot_strategy",
        "strategy_file": "strategy.json",
        "review_packet_file": "review_packet.md",
        "source_geometry_files": [],
        "created_at": "2026-05-22T12:00:00Z",
        "authority": {
            "non_execution_declaration": True,
            "execution_authority_claim": False,
            "requires_human_review": True,
        },
        "provenance": {
            "source_spec_id": "test",
            "created_by": "test",
            "derivation_notes": "test",
        },
    }

    with zipfile.ZipFile(archive_path, "w") as zf:
        zf.writestr("strategy.json", json.dumps(strategy))
        zf.writestr("review_packet.md", review_content)
        zf.writestr("manifest.json", json.dumps(manifest))
        zf.writestr("unexpected_file.txt", "Some extra content")


def create_archive_with_suspicious_file(archive_path: Path) -> None:
    """Create an archive with suspicious executable file."""
    strategy = {"strategy_version": "1.2", "strategy_id": "test"}
    review_content = "# Review Packet\n\n" + ("Content line.\n" * 100)
    manifest = {
        "manifest_version": "1.0.0",
        "package_type": "cam_assist_strategy_package",
        "operation_type": "fret_slot_strategy",
        "strategy_file": "strategy.json",
        "review_packet_file": "review_packet.md",
        "source_geometry_files": [],
        "created_at": "2026-05-22T12:00:00Z",
        "authority": {
            "non_execution_declaration": True,
            "execution_authority_claim": False,
            "requires_human_review": True,
        },
        "provenance": {
            "source_spec_id": "test",
            "created_by": "test",
            "derivation_notes": "test",
        },
    }

    with zipfile.ZipFile(archive_path, "w") as zf:
        zf.writestr("strategy.json", json.dumps(strategy))
        zf.writestr("review_packet.md", review_content)
        zf.writestr("manifest.json", json.dumps(manifest))
        zf.writestr("malware.exe", "not really")


class TestValidArchive:
    """Tests for valid archive validation."""

    def test_valid_archive_passes(self, tmp_path):
        """Valid archive should pass validation."""
        archive_path = tmp_path / "valid.zip"
        create_valid_archive(archive_path)

        exit_code, stdout, stderr = run_validator(archive_path)

        assert exit_code == 0
        assert "PASS" in stdout

    def test_example_package_archive_passes(self, tmp_path):
        """Archiving and validating example package should pass."""
        example_pkg = PACKAGES_DIR / "fret_slot_strategy_example"
        if not example_pkg.exists():
            pytest.skip("Example package not found")

        archive_path = tmp_path / "example.zip"

        result = subprocess.run(
            [
                sys.executable,
                str(ARCHIVER_SCRIPT),
                str(example_pkg),
                "--out",
                str(archive_path),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

        exit_code, stdout, stderr = run_validator(archive_path)

        assert exit_code == 0
        assert "PASS" in stdout


class TestMissingArchive:
    """Tests for missing archive handling."""

    def test_missing_archive_fails(self, tmp_path):
        """Missing archive should fail with exit code 2."""
        fake_path = tmp_path / "nonexistent.zip"

        exit_code, stdout, stderr = run_validator(fake_path)

        assert exit_code == 2

    def test_non_zip_file_fails(self, tmp_path):
        """Non-zip file should fail with exit code 2."""
        not_zip = tmp_path / "notazip.zip"
        not_zip.write_text("this is not a zip file")

        exit_code, stdout, stderr = run_validator(not_zip)

        assert exit_code == 2


class TestPathSafety:
    """Tests for path safety validation."""

    def test_path_traversal_entry_fails(self, tmp_path):
        """Archive with path traversal entry should fail."""
        archive_path = tmp_path / "traversal.zip"
        create_archive_with_traversal(archive_path)

        exit_code, stdout, stderr = run_validator(archive_path)

        assert exit_code == 1
        assert "traversal" in stdout.lower() or "FAIL" in stdout

    def test_absolute_path_entry_fails(self, tmp_path):
        """Archive with absolute path entry should fail."""
        archive_path = tmp_path / "absolute.zip"
        create_archive_with_absolute_path(archive_path)

        exit_code, stdout, stderr = run_validator(archive_path)

        assert exit_code == 1
        assert "absolute" in stdout.lower() or "FAIL" in stdout


class TestMissingRequiredFiles:
    """Tests for missing required files."""

    def test_missing_manifest_fails(self, tmp_path):
        """Archive missing manifest.json should fail."""
        archive_path = tmp_path / "no_manifest.zip"
        create_archive_missing_manifest(archive_path)

        exit_code, stdout, stderr = run_validator(archive_path)

        assert exit_code == 1
        assert "manifest" in stdout.lower()

    def test_missing_strategy_fails(self, tmp_path):
        """Archive missing strategy.json should fail."""
        archive_path = tmp_path / "no_strategy.zip"
        create_archive_missing_strategy(archive_path)

        exit_code, stdout, stderr = run_validator(archive_path)

        assert exit_code == 1
        assert "strategy" in stdout.lower()

    def test_missing_review_packet_fails(self, tmp_path):
        """Archive missing review_packet.md should fail."""
        archive_path = tmp_path / "no_review.zip"
        create_archive_missing_review(archive_path)

        exit_code, stdout, stderr = run_validator(archive_path)

        assert exit_code == 1
        assert "review" in stdout.lower()


class TestAuthorityViolations:
    """Tests for authority violation detection."""

    def test_execution_authority_claim_fails(self, tmp_path):
        """Archive with execution_authority_claim=true should fail."""
        archive_path = tmp_path / "exec_auth.zip"
        create_archive_exec_authority(archive_path)

        exit_code, stdout, stderr = run_validator(archive_path)

        assert exit_code == 1
        assert "FAIL" in stdout

    def test_non_execution_false_fails(self, tmp_path):
        """Archive with non_execution_declaration=false should fail."""
        archive_path = tmp_path / "non_exec.zip"
        create_archive_non_execution_false(archive_path)

        exit_code, stdout, stderr = run_validator(archive_path)

        assert exit_code == 1
        assert "FAIL" in stdout

    def test_human_review_false_fails(self, tmp_path):
        """Archive with requires_human_review=false should fail."""
        archive_path = tmp_path / "no_review_req.zip"
        create_archive_human_review_false(archive_path)

        exit_code, stdout, stderr = run_validator(archive_path)

        assert exit_code == 1
        assert "FAIL" in stdout


class TestWarnings:
    """Tests for warning generation."""

    def test_unexpected_file_warns(self, tmp_path):
        """Unexpected file in archive should produce warning."""
        archive_path = tmp_path / "extra_file.zip"
        create_archive_with_unexpected_file(archive_path)

        exit_code, stdout, stderr = run_validator(archive_path)

        assert exit_code == 0
        assert "WARN" in stdout
        assert "unexpected" in stdout.lower()

    def test_suspicious_file_high_warning(self, tmp_path):
        """Suspicious executable file should produce HIGH warning."""
        archive_path = tmp_path / "suspicious.zip"
        create_archive_with_suspicious_file(archive_path)

        exit_code, stdout, stderr = run_validator(archive_path)

        assert exit_code == 0
        assert "HIGH" in stdout


class TestOutputFormats:
    """Tests for output format options."""

    def test_json_output_works(self, tmp_path):
        """JSON output should be valid JSON."""
        archive_path = tmp_path / "valid.zip"
        create_valid_archive(archive_path)

        exit_code, stdout, stderr = run_validator(archive_path, json_output=True)

        assert exit_code == 0
        data = json.loads(stdout)
        assert data["archive_valid"] is True
        assert data["package_valid"] is True
        assert "package" in data
        assert data["package"]["package_type"] == "cam_assist_strategy_package"

    def test_json_output_on_failure(self, tmp_path):
        """JSON output should work on failure."""
        archive_path = tmp_path / "exec_auth.zip"
        create_archive_exec_authority(archive_path)

        exit_code, stdout, stderr = run_validator(archive_path, json_output=True)

        assert exit_code == 1
        data = json.loads(stdout)
        assert data["package_valid"] is False

    def test_quiet_output_success(self, tmp_path):
        """Quiet mode should print minimal output on success."""
        archive_path = tmp_path / "valid.zip"
        create_valid_archive(archive_path)

        exit_code, stdout, stderr = run_validator(archive_path, quiet=True)

        assert exit_code == 0
        assert "PASS" in stdout
        lines = [l for l in stdout.strip().split("\n") if l]
        assert len(lines) == 1

    def test_quiet_output_failure(self, tmp_path):
        """Quiet mode should print minimal output on failure."""
        archive_path = tmp_path / "exec_auth.zip"
        create_archive_exec_authority(archive_path)

        exit_code, stdout, stderr = run_validator(archive_path, quiet=True)

        assert exit_code == 1
        assert "FAIL" in stderr
        lines = [l for l in stderr.strip().split("\n") if l]
        assert len(lines) == 1


class TestTempCleanup:
    """Tests for temporary directory cleanup."""

    def test_temp_extraction_cleaned_up(self, tmp_path):
        """Temporary extraction directory should be cleaned up."""
        archive_path = tmp_path / "valid.zip"
        create_valid_archive(archive_path)

        temp_dirs_before = set()
        temp_root = tempfile.gettempdir()
        for item in Path(temp_root).iterdir():
            if item.is_dir():
                temp_dirs_before.add(item.name)

        run_validator(archive_path)

        temp_dirs_after = set()
        for item in Path(temp_root).iterdir():
            if item.is_dir():
                temp_dirs_after.add(item.name)

        new_dirs = temp_dirs_after - temp_dirs_before
        for d in new_dirs:
            dir_path = Path(temp_root) / d
            if dir_path.exists():
                contents = list(dir_path.iterdir())
                assert not any(
                    "manifest.json" in str(c) for c in contents
                ), "Temp extraction not cleaned up"


class TestFullFlow:
    """Tests for full assemble -> archive -> validate flow."""

    def test_full_assemble_archive_validate_flow(self, tmp_path):
        """Full workflow: assemble -> archive -> validate should pass."""
        strategy_path = EXAMPLES_DIR / "valid" / "fret_slot_strategy.json"
        if not strategy_path.exists():
            pytest.skip("Example strategy not found")

        package_dir = tmp_path / "assembled_package"
        archive_path = tmp_path / "package.zip"

        result1 = subprocess.run(
            [
                sys.executable,
                str(ASSEMBLER_SCRIPT),
                str(strategy_path),
                "--out",
                str(package_dir),
                "--force",
            ],
            capture_output=True,
            text=True,
        )
        assert result1.returncode == 0, f"Assembly failed: {result1.stderr}"

        result2 = subprocess.run(
            [
                sys.executable,
                str(ARCHIVER_SCRIPT),
                str(package_dir),
                "--out",
                str(archive_path),
                "--force",
            ],
            capture_output=True,
            text=True,
        )
        assert result2.returncode == 0, f"Archiving failed: {result2.stderr}"

        exit_code, stdout, stderr = run_validator(archive_path)

        assert exit_code == 0, f"Validation failed: {stdout}"
        assert "PASS" in stdout


class TestExitCodes:
    """Tests for correct exit codes."""

    def test_exit_code_0_for_valid(self, tmp_path):
        """Valid archive should return exit code 0."""
        archive_path = tmp_path / "valid.zip"
        create_valid_archive(archive_path)

        exit_code, _, _ = run_validator(archive_path)
        assert exit_code == 0

    def test_exit_code_1_for_validation_failure(self, tmp_path):
        """Validation failure should return exit code 1."""
        archive_path = tmp_path / "exec_auth.zip"
        create_archive_exec_authority(archive_path)

        exit_code, _, _ = run_validator(archive_path)
        assert exit_code == 1

    def test_exit_code_2_for_file_error(self, tmp_path):
        """File error should return exit code 2."""
        fake_path = tmp_path / "nonexistent.zip"

        exit_code, _, _ = run_validator(fake_path)
        assert exit_code == 2
