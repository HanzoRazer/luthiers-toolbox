"""
Tests for CAM Assist strategy package index generator.

These tests verify that the indexer correctly:
- Discovers packages recursively
- Indexes valid and invalid packages
- Generates Markdown output
- Generates JSON output
- Preserves non-execution notice
- Does not mutate package contents
"""

import json
import pytest
from pathlib import Path
import subprocess
import sys


SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
EXAMPLES_DIR = Path(__file__).parent.parent / "examples"
PACKAGES_DIR = EXAMPLES_DIR / "packages"

INDEXER_SCRIPT = SCRIPTS_DIR / "index_strategy_packages.py"


def run_indexer(
    packages_dir: Path,
    out: Path | None = None,
    json_out: Path | None = None,
    quiet: bool = False,
) -> tuple[int, str, str]:
    """Run the package indexer and return (exit_code, stdout, stderr)."""
    cmd = [sys.executable, str(INDEXER_SCRIPT), str(packages_dir)]
    if out:
        cmd.extend(["--out", str(out)])
    if json_out:
        cmd.extend(["--json-out", str(json_out)])
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
        "strategy_file": "strategy.json",  # This file doesn't exist
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


class TestPackageDiscovery:
    """Tests for package discovery."""

    def test_finds_single_package(self, tmp_path):
        """Should find a single package."""
        pkg_dir = tmp_path / "packages" / "pkg1"
        create_valid_package(pkg_dir)

        exit_code, stdout, stderr = run_indexer(
            tmp_path / "packages",
            out=tmp_path / "index.md",
        )
        assert exit_code == 0
        assert "1" in stdout  # 1 package

    def test_finds_multiple_packages(self, tmp_path):
        """Should find multiple packages."""
        packages_root = tmp_path / "packages"
        create_valid_package(packages_root / "pkg1")
        create_valid_package(packages_root / "pkg2")
        create_valid_package(packages_root / "pkg3")

        exit_code, stdout, stderr = run_indexer(
            packages_root,
            out=tmp_path / "index.md",
        )
        assert exit_code == 0
        assert "3" in stdout

    def test_recursive_discovery(self, tmp_path):
        """Should discover packages recursively."""
        packages_root = tmp_path / "packages"
        create_valid_package(packages_root / "level1" / "pkg1")
        create_valid_package(packages_root / "level1" / "level2" / "pkg2")

        exit_code, stdout, stderr = run_indexer(
            packages_root,
            out=tmp_path / "index.md",
        )
        assert exit_code == 0
        assert "2" in stdout

    def test_ignores_directories_without_manifest(self, tmp_path):
        """Should silently ignore directories without manifest.json."""
        packages_root = tmp_path / "packages"
        create_valid_package(packages_root / "valid_pkg")

        # Create directory without manifest
        no_manifest_dir = packages_root / "not_a_package"
        no_manifest_dir.mkdir(parents=True)
        (no_manifest_dir / "random.txt").write_text("not a package")

        exit_code, stdout, stderr = run_indexer(
            packages_root,
            out=tmp_path / "index.md",
        )
        assert exit_code == 0
        assert "1" in stdout  # Only the valid package


class TestIndexContent:
    """Tests for index content generation."""

    def test_valid_package_appears_in_index(self, tmp_path):
        """Valid package should appear in index."""
        packages_root = tmp_path / "packages"
        create_valid_package(packages_root / "my_package")

        index_path = tmp_path / "index.md"
        run_indexer(packages_root, out=index_path)

        content = index_path.read_text()
        assert "my_package" in content
        assert "fret_slot_strategy" in content
        assert "valid" in content.lower()

    def test_invalid_package_appears_as_invalid(self, tmp_path):
        """Invalid package should appear with INVALID status."""
        packages_root = tmp_path / "packages"
        create_invalid_package(packages_root / "bad_package")

        index_path = tmp_path / "index.md"
        run_indexer(packages_root, out=index_path)

        content = index_path.read_text()
        assert "bad_package" in content
        assert "INVALID" in content

    def test_warnings_included(self, tmp_path):
        """Warnings should be counted in index."""
        packages_root = tmp_path / "packages"
        # Create package with empty geometry (triggers warning)
        pkg_dir = packages_root / "warn_pkg"
        create_valid_package(pkg_dir)
        # Remove geometry file to trigger warning
        (pkg_dir / "geometry.dxf").unlink()
        manifest = json.loads((pkg_dir / "manifest.json").read_text())
        manifest["source_geometry_files"] = []
        (pkg_dir / "manifest.json").write_text(json.dumps(manifest))

        index_path = tmp_path / "index.md"
        run_indexer(packages_root, out=index_path)

        content = index_path.read_text()
        assert "warnings" in content.lower()

    def test_non_execution_notice_included(self, tmp_path):
        """Non-execution notice should be in index."""
        packages_root = tmp_path / "packages"
        create_valid_package(packages_root / "pkg1")

        index_path = tmp_path / "index.md"
        run_indexer(packages_root, out=index_path)

        content = index_path.read_text()
        assert "advisory only" in content.lower()
        assert "Human review" in content


class TestMarkdownOutput:
    """Tests for Markdown output."""

    def test_markdown_output_created(self, tmp_path):
        """Markdown index should be created."""
        packages_root = tmp_path / "packages"
        create_valid_package(packages_root / "pkg1")

        index_path = tmp_path / "custom_index.md"
        exit_code, stdout, stderr = run_indexer(packages_root, out=index_path)

        assert exit_code == 0
        assert index_path.exists()

    def test_default_output_path(self, tmp_path):
        """Default output should be <packages_dir>/INDEX.md."""
        packages_root = tmp_path / "packages"
        create_valid_package(packages_root / "pkg1")

        exit_code, stdout, stderr = run_indexer(packages_root)

        assert exit_code == 0
        assert (packages_root / "INDEX.md").exists()

    def test_markdown_has_header(self, tmp_path):
        """Markdown should have proper header."""
        packages_root = tmp_path / "packages"
        create_valid_package(packages_root / "pkg1")

        index_path = tmp_path / "index.md"
        run_indexer(packages_root, out=index_path)

        content = index_path.read_text()
        assert "# CAM Assist Strategy Package Index" in content
        assert "Generated at:" in content

    def test_markdown_has_summary(self, tmp_path):
        """Markdown should have summary section."""
        packages_root = tmp_path / "packages"
        create_valid_package(packages_root / "pkg1")

        index_path = tmp_path / "index.md"
        run_indexer(packages_root, out=index_path)

        content = index_path.read_text()
        assert "## Summary" in content
        assert "Total packages:" in content

    def test_markdown_has_table(self, tmp_path):
        """Markdown should have packages table."""
        packages_root = tmp_path / "packages"
        create_valid_package(packages_root / "pkg1")

        index_path = tmp_path / "index.md"
        run_indexer(packages_root, out=index_path)

        content = index_path.read_text()
        assert "## Packages" in content
        assert "| Package |" in content


class TestJsonOutput:
    """Tests for JSON output."""

    def test_json_output_created(self, tmp_path):
        """JSON index should be created when requested."""
        packages_root = tmp_path / "packages"
        create_valid_package(packages_root / "pkg1")

        json_path = tmp_path / "index.json"
        exit_code, stdout, stderr = run_indexer(
            packages_root,
            out=tmp_path / "index.md",
            json_out=json_path,
        )

        assert exit_code == 0
        assert json_path.exists()

    def test_json_structure(self, tmp_path):
        """JSON should have correct structure."""
        packages_root = tmp_path / "packages"
        create_valid_package(packages_root / "pkg1")

        json_path = tmp_path / "index.json"
        run_indexer(packages_root, out=tmp_path / "index.md", json_out=json_path)

        data = json.loads(json_path.read_text())
        assert "generated_at" in data
        assert "summary" in data
        assert "packages" in data
        assert data["summary"]["total"] == 1

    def test_json_package_entry(self, tmp_path):
        """JSON package entries should have correct fields."""
        packages_root = tmp_path / "packages"
        create_valid_package(packages_root / "pkg1")

        json_path = tmp_path / "index.json"
        run_indexer(packages_root, out=tmp_path / "index.md", json_out=json_path)

        data = json.loads(json_path.read_text())
        pkg = data["packages"][0]

        assert "path" in pkg
        assert "name" in pkg
        assert "operation_type" in pkg
        assert "status" in pkg
        assert "requires_human_review" in pkg
        assert "warnings" in pkg


class TestExitCodes:
    """Tests for exit code behavior."""

    def test_no_packages_returns_1(self, tmp_path):
        """No packages found should return exit code 1."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        exit_code, stdout, stderr = run_indexer(empty_dir, out=tmp_path / "index.md")
        assert exit_code == 1
        assert "No packages found" in stderr

    def test_missing_directory_returns_2(self, tmp_path):
        """Missing directory should return exit code 2."""
        fake_dir = tmp_path / "nonexistent"

        exit_code, stdout, stderr = run_indexer(fake_dir, out=tmp_path / "index.md")
        assert exit_code == 2

    def test_invalid_packages_still_returns_0(self, tmp_path):
        """Invalid packages should still return exit code 0."""
        packages_root = tmp_path / "packages"
        create_invalid_package(packages_root / "bad_pkg")

        exit_code, stdout, stderr = run_indexer(
            packages_root,
            out=tmp_path / "index.md",
        )
        assert exit_code == 0


class TestPackageIntegrity:
    """Tests for package content integrity."""

    def test_package_contents_not_mutated(self, tmp_path):
        """Package contents should not be mutated."""
        packages_root = tmp_path / "packages"
        pkg_dir = packages_root / "pkg1"
        create_valid_package(pkg_dir)

        # Record original contents
        original_manifest = (pkg_dir / "manifest.json").read_text()
        original_strategy = (pkg_dir / "strategy.json").read_text()
        original_review = (pkg_dir / "review_packet.md").read_text()

        # Run indexer
        run_indexer(packages_root, out=tmp_path / "index.md")

        # Verify contents unchanged
        assert (pkg_dir / "manifest.json").read_text() == original_manifest
        assert (pkg_dir / "strategy.json").read_text() == original_strategy
        assert (pkg_dir / "review_packet.md").read_text() == original_review


class TestExamplePackages:
    """Tests using example packages."""

    def test_example_packages_index(self):
        """Should successfully index example packages."""
        if not PACKAGES_DIR.exists():
            pytest.skip("Example packages not found")

        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            index_path = Path(tmp) / "index.md"
            exit_code, stdout, stderr = run_indexer(PACKAGES_DIR, out=index_path)

            assert exit_code == 0
            assert index_path.exists()
