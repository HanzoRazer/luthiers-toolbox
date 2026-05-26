"""
Tests for CAM Assist strategy package archive CLI.

These tests verify that the archiver correctly:
- Archives valid packages
- Preserves package-relative paths
- Blocks invalid packages
- Blocks execution authority violations
- Handles overwrite scenarios
- Does not mutate package contents
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

ARCHIVER_SCRIPT = SCRIPTS_DIR / "archive_strategy_package.py"


def run_archiver(
    package_dir: Path,
    out: Path | None = None,
    force: bool = False,
    quiet: bool = False,
) -> tuple[int, str, str]:
    """Run the package archiver and return (exit_code, stdout, stderr)."""
    cmd = [sys.executable, str(ARCHIVER_SCRIPT), str(package_dir)]
    if out:
        cmd.extend(["--out", str(out)])
    if force:
        cmd.append("--force")
    if quiet:
        cmd.append("--quiet")
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr


def create_valid_package(pkg_dir: Path) -> None:
    """Create a valid package in the given directory."""
    pkg_dir.mkdir(parents=True, exist_ok=True)

    strategy = {"strategy_version": "1.2", "strategy_id": "test"}
    (pkg_dir / "strategy.json").write_text(json.dumps(strategy))

    review_content = "# Review Packet\n\n" + ("Content line.\n" * 100)
    (pkg_dir / "review_packet.md").write_text(review_content)

    manifest = {
        "manifest_version": "1.0.0",
        "package_type": "cam_assist_strategy_package",
        "operation_type": "fret_slot_strategy",
        "strategy_file": "strategy.json",
        "review_packet_file": "review_packet.md",
        "source_geometry_files": ["geometry.dxf"],
        "created_at": "2026-05-21T12:00:00Z",
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
    (pkg_dir / "manifest.json").write_text(json.dumps(manifest))
    (pkg_dir / "geometry.dxf").write_text("DXF content")


def create_invalid_package(pkg_dir: Path) -> None:
    """Create an invalid package (missing strategy file)."""
    pkg_dir.mkdir(parents=True, exist_ok=True)

    review_content = "# Review\n" + ("x" * 1100)
    (pkg_dir / "review_packet.md").write_text(review_content)

    manifest = {
        "manifest_version": "1.0.0",
        "package_type": "cam_assist_strategy_package",
        "operation_type": "test_operation",
        "strategy_file": "strategy.json",
        "review_packet_file": "review_packet.md",
        "source_geometry_files": [],
        "created_at": "2026-05-21T12:00:00Z",
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
    (pkg_dir / "manifest.json").write_text(json.dumps(manifest))


def create_exec_authority_package(pkg_dir: Path) -> None:
    """Create a package with execution authority claim."""
    pkg_dir.mkdir(parents=True, exist_ok=True)

    (pkg_dir / "strategy.json").write_text("{}")
    review_content = "# Review\n" + ("x" * 1100)
    (pkg_dir / "review_packet.md").write_text(review_content)

    manifest = {
        "manifest_version": "1.0.0",
        "package_type": "cam_assist_strategy_package",
        "operation_type": "test",
        "strategy_file": "strategy.json",
        "review_packet_file": "review_packet.md",
        "source_geometry_files": [],
        "created_at": "2026-05-21T12:00:00Z",
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
    (pkg_dir / "manifest.json").write_text(json.dumps(manifest))


class TestValidPackageArchive:
    """Tests for valid package archiving."""

    def test_valid_package_archives(self, tmp_path):
        """Valid package should create archive."""
        pkg_dir = tmp_path / "valid_pkg"
        create_valid_package(pkg_dir)

        archive_path = tmp_path / "output.zip"
        exit_code, stdout, stderr = run_archiver(pkg_dir, out=archive_path)

        assert exit_code == 0, f"Expected success: {stderr}"
        assert archive_path.exists()
        assert "PASS" in stdout

    def test_archive_contains_required_files(self, tmp_path):
        """Archive must contain required files."""
        pkg_dir = tmp_path / "valid_pkg"
        create_valid_package(pkg_dir)

        archive_path = tmp_path / "output.zip"
        run_archiver(pkg_dir, out=archive_path)

        with zipfile.ZipFile(archive_path, "r") as zf:
            names = zf.namelist()
            assert "strategy.json" in names
            assert "review_packet.md" in names
            assert "manifest.json" in names

    def test_paths_are_package_relative(self, tmp_path):
        """Archive paths should be package-relative (flat)."""
        pkg_dir = tmp_path / "valid_pkg"
        create_valid_package(pkg_dir)

        archive_path = tmp_path / "output.zip"
        run_archiver(pkg_dir, out=archive_path)

        with zipfile.ZipFile(archive_path, "r") as zf:
            names = zf.namelist()
            # Should not contain nested paths like "valid_pkg/strategy.json"
            for name in names:
                assert "valid_pkg" not in name
                assert not name.startswith("/")

    def test_additional_files_included(self, tmp_path):
        """Additional package files should be included."""
        pkg_dir = tmp_path / "valid_pkg"
        create_valid_package(pkg_dir)

        # Add a README
        (pkg_dir / "README.md").write_text("# Package README")

        archive_path = tmp_path / "output.zip"
        run_archiver(pkg_dir, out=archive_path)

        with zipfile.ZipFile(archive_path, "r") as zf:
            names = zf.namelist()
            assert "README.md" in names

    def test_subdirectories_preserved(self, tmp_path):
        """Subdirectories should be preserved in archive."""
        pkg_dir = tmp_path / "valid_pkg"
        create_valid_package(pkg_dir)

        # Add a subdirectory
        (pkg_dir / "notes").mkdir()
        (pkg_dir / "notes" / "note.txt").write_text("Note content")

        archive_path = tmp_path / "output.zip"
        run_archiver(pkg_dir, out=archive_path)

        with zipfile.ZipFile(archive_path, "r") as zf:
            names = zf.namelist()
            assert any("notes" in name for name in names)

    def test_default_output_path(self, tmp_path):
        """Default output should be <package_dir>.zip."""
        pkg_dir = tmp_path / "my_package"
        create_valid_package(pkg_dir)

        exit_code, stdout, stderr = run_archiver(pkg_dir)

        assert exit_code == 0
        expected_path = tmp_path / "my_package.zip"
        assert expected_path.exists()

    def test_example_package_archives(self):
        """Example package should archive successfully."""
        example_pkg = PACKAGES_DIR / "fret_slot_strategy_example"
        if not example_pkg.exists():
            pytest.skip("Example package not found")

        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            archive_path = Path(tmp) / "example.zip"
            exit_code, stdout, stderr = run_archiver(example_pkg, out=archive_path)

            assert exit_code == 0
            assert archive_path.exists()


class TestInvalidPackageBlocked:
    """Tests for invalid package blocking."""

    def test_missing_manifest_blocks_archive(self, tmp_path):
        """Missing manifest should block archive."""
        pkg_dir = tmp_path / "no_manifest"
        pkg_dir.mkdir()
        (pkg_dir / "strategy.json").write_text("{}")

        archive_path = tmp_path / "output.zip"
        exit_code, stdout, stderr = run_archiver(pkg_dir, out=archive_path)

        assert exit_code == 1
        assert not archive_path.exists()

    def test_missing_strategy_blocks_archive(self, tmp_path):
        """Missing strategy file should block archive."""
        pkg_dir = tmp_path / "no_strategy"
        create_invalid_package(pkg_dir)

        archive_path = tmp_path / "output.zip"
        exit_code, stdout, stderr = run_archiver(pkg_dir, out=archive_path)

        assert exit_code == 1
        assert not archive_path.exists()

    def test_missing_review_packet_blocks_archive(self, tmp_path):
        """Missing review packet should block archive."""
        pkg_dir = tmp_path / "no_review"
        pkg_dir.mkdir()

        (pkg_dir / "strategy.json").write_text("{}")
        manifest = {
            "manifest_version": "1.0.0",
            "package_type": "cam_assist_strategy_package",
            "operation_type": "test",
            "strategy_file": "strategy.json",
            "review_packet_file": "review_packet.md",
            "source_geometry_files": [],
            "created_at": "2026-05-21T12:00:00Z",
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
        (pkg_dir / "manifest.json").write_text(json.dumps(manifest))

        archive_path = tmp_path / "output.zip"
        exit_code, stdout, stderr = run_archiver(pkg_dir, out=archive_path)

        assert exit_code == 1
        assert not archive_path.exists()

    def test_execution_authority_violation_blocks_archive(self, tmp_path):
        """Execution authority violation should block archive."""
        pkg_dir = tmp_path / "exec_auth"
        create_exec_authority_package(pkg_dir)

        archive_path = tmp_path / "output.zip"
        exit_code, stdout, stderr = run_archiver(pkg_dir, out=archive_path)

        assert exit_code == 1
        assert "FAIL" in stderr


class TestOverwriteBehavior:
    """Tests for archive overwrite handling."""

    def test_existing_archive_without_force_fails(self, tmp_path):
        """Existing archive without --force should fail."""
        pkg_dir = tmp_path / "valid_pkg"
        create_valid_package(pkg_dir)

        archive_path = tmp_path / "output.zip"
        archive_path.write_text("existing content")

        exit_code, stdout, stderr = run_archiver(pkg_dir, out=archive_path)

        assert exit_code == 1
        assert "force" in stderr.lower() or "exists" in stderr.lower()

    def test_existing_archive_with_force_succeeds(self, tmp_path):
        """Existing archive with --force should succeed."""
        pkg_dir = tmp_path / "valid_pkg"
        create_valid_package(pkg_dir)

        archive_path = tmp_path / "output.zip"
        archive_path.write_text("existing content")

        exit_code, stdout, stderr = run_archiver(pkg_dir, out=archive_path, force=True)

        assert exit_code == 0
        assert archive_path.exists()

        # Verify it's a valid zip now
        with zipfile.ZipFile(archive_path, "r") as zf:
            assert "strategy.json" in zf.namelist()


class TestWarnings:
    """Tests for warning handling."""

    def test_warnings_print_but_do_not_block(self, tmp_path):
        """Warnings should print but not block archiving."""
        pkg_dir = tmp_path / "warn_pkg"
        create_valid_package(pkg_dir)

        # Remove geometry file and clear list to trigger warning
        (pkg_dir / "geometry.dxf").unlink()
        manifest = json.loads((pkg_dir / "manifest.json").read_text())
        manifest["source_geometry_files"] = []
        (pkg_dir / "manifest.json").write_text(json.dumps(manifest))

        archive_path = tmp_path / "output.zip"
        exit_code, stdout, stderr = run_archiver(pkg_dir, out=archive_path)

        assert exit_code == 0
        assert archive_path.exists()
        assert "[WARN]" in stdout


class TestPackageIntegrity:
    """Tests for package content integrity."""

    def test_package_directory_not_mutated(self, tmp_path):
        """Package directory should not be mutated."""
        pkg_dir = tmp_path / "valid_pkg"
        create_valid_package(pkg_dir)

        # Record original contents
        original_manifest = (pkg_dir / "manifest.json").read_text()
        original_strategy = (pkg_dir / "strategy.json").read_text()
        original_review = (pkg_dir / "review_packet.md").read_text()
        original_files = set(p.name for p in pkg_dir.iterdir())

        # Run archiver
        archive_path = tmp_path / "output.zip"
        run_archiver(pkg_dir, out=archive_path)

        # Verify contents unchanged
        assert (pkg_dir / "manifest.json").read_text() == original_manifest
        assert (pkg_dir / "strategy.json").read_text() == original_strategy
        assert (pkg_dir / "review_packet.md").read_text() == original_review
        assert set(p.name for p in pkg_dir.iterdir()) == original_files

    def test_invalid_package_not_repaired(self, tmp_path):
        """Invalid package should not be repaired."""
        pkg_dir = tmp_path / "invalid_pkg"
        create_invalid_package(pkg_dir)

        original_files = set(p.name for p in pkg_dir.iterdir())

        archive_path = tmp_path / "output.zip"
        run_archiver(pkg_dir, out=archive_path)

        # Verify no new files created
        assert set(p.name for p in pkg_dir.iterdir()) == original_files


class TestQuietMode:
    """Tests for quiet mode."""

    def test_quiet_mode_success(self, tmp_path):
        """Quiet mode should print minimal output on success."""
        pkg_dir = tmp_path / "valid_pkg"
        create_valid_package(pkg_dir)

        archive_path = tmp_path / "output.zip"
        exit_code, stdout, stderr = run_archiver(pkg_dir, out=archive_path, quiet=True)

        assert exit_code == 0
        assert "PASS" in stdout
        lines = [l for l in stdout.strip().split("\n") if l]
        assert len(lines) == 1

    def test_quiet_mode_failure(self, tmp_path):
        """Quiet mode should print minimal output on failure."""
        pkg_dir = tmp_path / "invalid_pkg"
        create_invalid_package(pkg_dir)

        archive_path = tmp_path / "output.zip"
        exit_code, stdout, stderr = run_archiver(pkg_dir, out=archive_path, quiet=True)

        assert exit_code == 1
        assert "FAIL" in stderr


class TestFileErrors:
    """Tests for file error handling."""

    def test_missing_package_directory(self, tmp_path):
        """Missing package directory should return exit code 2."""
        fake_dir = tmp_path / "nonexistent"

        exit_code, stdout, stderr = run_archiver(fake_dir, out=tmp_path / "out.zip")
        assert exit_code == 2
