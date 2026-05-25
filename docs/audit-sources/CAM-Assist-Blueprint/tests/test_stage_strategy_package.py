"""
Tests for CAM Assist strategy package import staging CLI.

These tests verify that the stager correctly:
- Validates archives before staging
- Stages valid archives into review directories
- Rejects invalid or unsafe archives
- Handles overwrite protection
- Preserves archive-relative paths
- Does not execute or modify package contents
"""

import json
import pytest
from pathlib import Path
import subprocess
import sys
import zipfile


SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
EXAMPLES_DIR = Path(__file__).parent.parent / "examples"
PACKAGES_DIR = EXAMPLES_DIR / "packages"

STAGER_SCRIPT = SCRIPTS_DIR / "stage_strategy_package.py"
ASSEMBLER_SCRIPT = SCRIPTS_DIR / "assemble_strategy_package.py"
ARCHIVER_SCRIPT = SCRIPTS_DIR / "archive_strategy_package.py"


def run_stager(
    archive_path: Path,
    out: Path | None = None,
    force: bool = False,
    quiet: bool = False,
) -> tuple[int, str, str]:
    """Run the package stager and return (exit_code, stdout, stderr)."""
    cmd = [sys.executable, str(STAGER_SCRIPT), str(archive_path)]
    if out:
        cmd.extend(["--out", str(out)])
    if force:
        cmd.append("--force")
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
        "created_at": "2026-05-23T12:00:00Z",
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


def create_archive_with_subdirs(archive_path: Path) -> None:
    """Create a valid archive with subdirectories."""
    strategy = {"strategy_version": "1.2", "strategy_id": "test"}
    review_content = "# Review Packet\n\n" + ("Content line.\n" * 100)
    manifest = {
        "manifest_version": "1.0.0",
        "package_type": "cam_assist_strategy_package",
        "operation_type": "fret_slot_strategy",
        "strategy_file": "strategy.json",
        "review_packet_file": "review_packet.md",
        "source_geometry_files": ["geometry/fret.dxf"],
        "created_at": "2026-05-23T12:00:00Z",
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
        zf.writestr("geometry/fret.dxf", "DXF content")
        zf.writestr("notes/note.txt", "Some notes")
        zf.writestr("attachments/photo.txt", "Photo placeholder")


def create_archive_with_traversal(archive_path: Path) -> None:
    """Create an archive with path traversal entry."""
    with zipfile.ZipFile(archive_path, "w") as zf:
        zf.writestr("../evil.txt", "malicious content")
        zf.writestr("manifest.json", "{}")


def create_archive_exec_authority(archive_path: Path) -> None:
    """Create an archive with execution_authority_claim = true."""
    manifest = {
        "manifest_version": "1.0.0",
        "package_type": "cam_assist_strategy_package",
        "operation_type": "test",
        "strategy_file": "strategy.json",
        "review_packet_file": "review_packet.md",
        "source_geometry_files": [],
        "created_at": "2026-05-23T12:00:00Z",
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


def create_invalid_archive(archive_path: Path) -> None:
    """Create an invalid archive missing required files."""
    with zipfile.ZipFile(archive_path, "w") as zf:
        zf.writestr("manifest.json", "{}")


class TestValidArchiveStaging:
    """Tests for valid archive staging."""

    def test_valid_archive_stages_successfully(self, tmp_path):
        """Valid archive should stage successfully."""
        archive_path = tmp_path / "valid_package.zip"
        create_valid_archive(archive_path)

        staging_root = tmp_path / "staging"
        exit_code, stdout, stderr = run_stager(archive_path, out=staging_root)

        assert exit_code == 0, f"Expected success: {stderr}"
        assert "PASS" in stdout

        staged_dir = staging_root / "valid_package"
        assert staged_dir.exists()

    def test_staged_package_contains_required_files(self, tmp_path):
        """Staged package must contain required files."""
        archive_path = tmp_path / "valid_package.zip"
        create_valid_archive(archive_path)

        staging_root = tmp_path / "staging"
        run_stager(archive_path, out=staging_root)

        staged_dir = staging_root / "valid_package"
        assert (staged_dir / "strategy.json").exists()
        assert (staged_dir / "review_packet.md").exists()
        assert (staged_dir / "manifest.json").exists()

    def test_staged_files_preserve_archive_relative_paths(self, tmp_path):
        """Subdirectories must be preserved."""
        archive_path = tmp_path / "subdir_package.zip"
        create_archive_with_subdirs(archive_path)

        staging_root = tmp_path / "staging"
        exit_code, stdout, stderr = run_stager(archive_path, out=staging_root)

        assert exit_code == 0

        staged_dir = staging_root / "subdir_package"
        assert (staged_dir / "geometry" / "fret.dxf").exists()
        assert (staged_dir / "notes" / "note.txt").exists()
        assert (staged_dir / "attachments" / "photo.txt").exists()

    def test_default_staging_root(self, tmp_path, monkeypatch):
        """Default staging root should be ./staged_packages/."""
        archive_path = tmp_path / "default_test.zip"
        create_valid_archive(archive_path)

        monkeypatch.chdir(tmp_path)

        exit_code, stdout, stderr = run_stager(archive_path)

        assert exit_code == 0
        default_staged = tmp_path / "staged_packages" / "default_test"
        assert default_staged.exists()

    def test_example_package_stages(self, tmp_path):
        """Archiving and staging example package should work."""
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

        staging_root = tmp_path / "staging"
        exit_code, stdout, stderr = run_stager(archive_path, out=staging_root)

        assert exit_code == 0
        assert (staging_root / "example").exists()


class TestInvalidArchiveRejection:
    """Tests for invalid archive rejection."""

    def test_invalid_archive_fails(self, tmp_path):
        """Invalid archive should fail staging."""
        archive_path = tmp_path / "invalid.zip"
        create_invalid_archive(archive_path)

        staging_root = tmp_path / "staging"
        exit_code, stdout, stderr = run_stager(archive_path, out=staging_root)

        assert exit_code == 1
        assert not (staging_root / "invalid").exists()

    def test_unsafe_archive_path_fails(self, tmp_path):
        """Archive with path traversal should fail."""
        archive_path = tmp_path / "traversal.zip"
        create_archive_with_traversal(archive_path)

        staging_root = tmp_path / "staging"
        exit_code, stdout, stderr = run_stager(archive_path, out=staging_root)

        assert exit_code == 1

    def test_execution_authority_violation_fails(self, tmp_path):
        """Archive with execution authority claim should fail."""
        archive_path = tmp_path / "exec_auth.zip"
        create_archive_exec_authority(archive_path)

        staging_root = tmp_path / "staging"
        exit_code, stdout, stderr = run_stager(archive_path, out=staging_root)

        assert exit_code == 1
        assert "FAIL" in stderr or "FAIL" in stdout

    def test_missing_archive_fails(self, tmp_path):
        """Missing archive should fail with exit code 2."""
        fake_path = tmp_path / "nonexistent.zip"

        staging_root = tmp_path / "staging"
        exit_code, stdout, stderr = run_stager(fake_path, out=staging_root)

        assert exit_code == 2


class TestOverwriteBehavior:
    """Tests for overwrite protection."""

    def test_existing_staged_directory_without_force_fails(self, tmp_path):
        """Existing staged directory without --force should fail."""
        archive_path = tmp_path / "overwrite_test.zip"
        create_valid_archive(archive_path)

        staging_root = tmp_path / "staging"
        staged_dir = staging_root / "overwrite_test"
        staged_dir.mkdir(parents=True)
        (staged_dir / "existing_file.txt").write_text("existing content")

        exit_code, stdout, stderr = run_stager(archive_path, out=staging_root)

        assert exit_code == 1
        assert "force" in (stdout + stderr).lower() or "exists" in (stdout + stderr).lower()
        assert (staged_dir / "existing_file.txt").exists()

    def test_existing_staged_directory_with_force_succeeds(self, tmp_path):
        """Existing staged directory with --force should succeed."""
        archive_path = tmp_path / "overwrite_test.zip"
        create_valid_archive(archive_path)

        staging_root = tmp_path / "staging"
        staged_dir = staging_root / "overwrite_test"
        staged_dir.mkdir(parents=True)
        (staged_dir / "old_file.txt").write_text("old content")

        exit_code, stdout, stderr = run_stager(archive_path, out=staging_root, force=True)

        assert exit_code == 0
        assert (staged_dir / "strategy.json").exists()
        assert not (staged_dir / "old_file.txt").exists()


class TestWarnings:
    """Tests for warning handling."""

    def test_warnings_printed_but_do_not_block(self, tmp_path):
        """Warnings should print but not block staging."""
        archive_path = tmp_path / "warn_package.zip"

        strategy = {"strategy_version": "1.2", "strategy_id": "test"}
        review_content = "# Review Packet\n\n" + ("Content line.\n" * 100)
        manifest = {
            "manifest_version": "1.0.0",
            "package_type": "cam_assist_strategy_package",
            "operation_type": "fret_slot_strategy",
            "strategy_file": "strategy.json",
            "review_packet_file": "review_packet.md",
            "source_geometry_files": [],
            "created_at": "2026-05-23T12:00:00Z",
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

        with zipfile.ZipFile(archive_path, "w") as zf:
            zf.writestr("strategy.json", json.dumps(strategy))
            zf.writestr("review_packet.md", review_content)
            zf.writestr("manifest.json", json.dumps(manifest))

        staging_root = tmp_path / "staging"
        exit_code, stdout, stderr = run_stager(archive_path, out=staging_root)

        assert exit_code == 0
        assert "WARN" in stdout


class TestQuietMode:
    """Tests for quiet mode."""

    def test_quiet_mode_success(self, tmp_path):
        """Quiet mode should print minimal output on success."""
        archive_path = tmp_path / "quiet_test.zip"
        create_valid_archive(archive_path)

        staging_root = tmp_path / "staging"
        exit_code, stdout, stderr = run_stager(archive_path, out=staging_root, quiet=True)

        assert exit_code == 0
        assert "PASS" in stdout
        lines = [l for l in stdout.strip().split("\n") if l]
        assert len(lines) == 1

    def test_quiet_mode_failure(self, tmp_path):
        """Quiet mode should print minimal output on failure."""
        archive_path = tmp_path / "invalid.zip"
        create_invalid_archive(archive_path)

        staging_root = tmp_path / "staging"
        exit_code, stdout, stderr = run_stager(archive_path, out=staging_root, quiet=True)

        assert exit_code == 1
        assert "FAIL" in stderr


class TestPackageIntegrity:
    """Tests for package integrity."""

    def test_archive_contents_not_executed(self, tmp_path):
        """Archive contents should not be executed."""
        archive_path = tmp_path / "exec_test.zip"

        strategy = {"strategy_version": "1.2", "strategy_id": "test"}
        review_content = "# Review Packet\n\n" + ("Content line.\n" * 100)
        manifest = {
            "manifest_version": "1.0.0",
            "package_type": "cam_assist_strategy_package",
            "operation_type": "fret_slot_strategy",
            "strategy_file": "strategy.json",
            "review_packet_file": "review_packet.md",
            "source_geometry_files": [],
            "created_at": "2026-05-23T12:00:00Z",
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

        evil_py = "import os; os.system('echo EVIL > /tmp/evil_marker.txt')"

        with zipfile.ZipFile(archive_path, "w") as zf:
            zf.writestr("strategy.json", json.dumps(strategy))
            zf.writestr("review_packet.md", review_content)
            zf.writestr("manifest.json", json.dumps(manifest))
            zf.writestr("evil.py", evil_py)

        staging_root = tmp_path / "staging"
        run_stager(archive_path, out=staging_root)

        evil_marker = Path("/tmp/evil_marker.txt")
        assert not evil_marker.exists(), "Archive content was executed!"

    def test_package_contents_not_repaired(self, tmp_path):
        """Package contents should not be modified or repaired."""
        archive_path = tmp_path / "norepair.zip"

        strategy = {"strategy_version": "1.2", "strategy_id": "test", "custom_field": "original"}
        review_content = "# Review Packet\n\n" + ("Content line.\n" * 100)
        manifest = {
            "manifest_version": "1.0.0",
            "package_type": "cam_assist_strategy_package",
            "operation_type": "fret_slot_strategy",
            "strategy_file": "strategy.json",
            "review_packet_file": "review_packet.md",
            "source_geometry_files": [],
            "created_at": "2026-05-23T12:00:00Z",
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

        strategy_json = json.dumps(strategy)

        with zipfile.ZipFile(archive_path, "w") as zf:
            zf.writestr("strategy.json", strategy_json)
            zf.writestr("review_packet.md", review_content)
            zf.writestr("manifest.json", json.dumps(manifest))

        staging_root = tmp_path / "staging"
        run_stager(archive_path, out=staging_root)

        staged_strategy = staging_root / "norepair" / "strategy.json"
        assert staged_strategy.read_text() == strategy_json


class TestExitCodes:
    """Tests for correct exit codes."""

    def test_exit_code_0_for_success(self, tmp_path):
        """Successful staging should return exit code 0."""
        archive_path = tmp_path / "success.zip"
        create_valid_archive(archive_path)

        staging_root = tmp_path / "staging"
        exit_code, _, _ = run_stager(archive_path, out=staging_root)

        assert exit_code == 0

    def test_exit_code_1_for_validation_failure(self, tmp_path):
        """Validation failure should return exit code 1."""
        archive_path = tmp_path / "invalid.zip"
        create_archive_exec_authority(archive_path)

        staging_root = tmp_path / "staging"
        exit_code, _, _ = run_stager(archive_path, out=staging_root)

        assert exit_code == 1

    def test_exit_code_2_for_file_error(self, tmp_path):
        """File error should return exit code 2."""
        fake_path = tmp_path / "nonexistent.zip"

        staging_root = tmp_path / "staging"
        exit_code, _, _ = run_stager(fake_path, out=staging_root)

        assert exit_code == 2


class TestFullFlow:
    """Tests for full assemble -> archive -> validate -> stage flow."""

    def test_full_assemble_archive_validate_stage_flow(self, tmp_path):
        """Full workflow should work end to end."""
        strategy_path = EXAMPLES_DIR / "valid" / "fret_slot_strategy.json"
        if not strategy_path.exists():
            pytest.skip("Example strategy not found")

        package_dir = tmp_path / "assembled_package"
        archive_path = tmp_path / "package.zip"
        staging_root = tmp_path / "staging"

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

        exit_code, stdout, stderr = run_stager(archive_path, out=staging_root)

        assert exit_code == 0, f"Staging failed: {stdout}"
        assert "PASS" in stdout

        staged_dir = staging_root / "package"
        assert (staged_dir / "strategy.json").exists()
        assert (staged_dir / "review_packet.md").exists()
        assert (staged_dir / "manifest.json").exists()
