"""
Tests for CAM Assist strategy package inspection CLI.

These tests verify that the inspector correctly:
- Inspects valid packages successfully
- Detects missing files
- Detects authority violations
- Produces correct output formats
- Handles edge cases
"""

import json
import pytest
from pathlib import Path
import subprocess
import sys


SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
EXAMPLES_DIR = Path(__file__).parent.parent / "examples"
PACKAGES_DIR = EXAMPLES_DIR / "packages"

INSPECTOR_SCRIPT = SCRIPTS_DIR / "inspect_strategy_package.py"


def run_inspector(
    package_dir: Path,
    json_output: bool = False,
    quiet: bool = False,
) -> tuple[int, str, str]:
    """Run the package inspector and return (exit_code, stdout, stderr)."""
    cmd = [sys.executable, str(INSPECTOR_SCRIPT), str(package_dir)]
    if json_output:
        cmd.append("--json")
    if quiet:
        cmd.append("--quiet")
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr


@pytest.fixture
def valid_package(tmp_path) -> Path:
    """Create a valid package directory."""
    pkg_dir = tmp_path / "valid_package"
    pkg_dir.mkdir()

    # Create strategy.json
    strategy = {"strategy_version": "1.2", "strategy_id": "test"}
    (pkg_dir / "strategy.json").write_text(json.dumps(strategy))

    # Create review_packet.md (over 1KB to avoid warning)
    review_content = "# Review Packet\n\n" + ("Content line.\n" * 100)
    (pkg_dir / "review_packet.md").write_text(review_content)

    # Create manifest.json
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

    # Create geometry file referenced in manifest
    (pkg_dir / "geometry.dxf").write_text("DXF content")

    return pkg_dir


@pytest.fixture
def package_missing_manifest(tmp_path) -> Path:
    """Create a package without manifest.json."""
    pkg_dir = tmp_path / "no_manifest"
    pkg_dir.mkdir()
    (pkg_dir / "strategy.json").write_text("{}")
    (pkg_dir / "review_packet.md").write_text("# Review")
    return pkg_dir


@pytest.fixture
def package_missing_strategy(tmp_path) -> Path:
    """Create a package without strategy.json."""
    pkg_dir = tmp_path / "no_strategy"
    pkg_dir.mkdir()

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
    return pkg_dir


@pytest.fixture
def package_missing_review(tmp_path) -> Path:
    """Create a package without review_packet.md."""
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
    return pkg_dir


@pytest.fixture
def package_exec_authority_violation(tmp_path) -> Path:
    """Create a package with execution_authority_claim=true."""
    pkg_dir = tmp_path / "exec_auth"
    pkg_dir.mkdir()

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
    return pkg_dir


@pytest.fixture
def package_non_exec_false(tmp_path) -> Path:
    """Create a package with non_execution_declaration=false."""
    pkg_dir = tmp_path / "non_exec_false"
    pkg_dir.mkdir()

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
    (pkg_dir / "manifest.json").write_text(json.dumps(manifest))
    return pkg_dir


@pytest.fixture
def package_human_review_false(tmp_path) -> Path:
    """Create a package with requires_human_review=false."""
    pkg_dir = tmp_path / "no_review_required"
    pkg_dir.mkdir()

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
            "execution_authority_claim": False,
            "requires_human_review": False,
        },
        "provenance": {
            "source_spec_id": "test",
            "created_by": "test",
            "derivation_notes": "test",
        },
    }
    (pkg_dir / "manifest.json").write_text(json.dumps(manifest))
    return pkg_dir


class TestValidPackage:
    """Tests for valid package inspection."""

    def test_valid_package_inspects_successfully(self, valid_package):
        """Valid package should inspect successfully."""
        exit_code, stdout, stderr = run_inspector(valid_package)
        assert exit_code == 0, f"Expected success: {stderr}"
        assert "CAM Assist Strategy Package Inspection" in stdout

    def test_valid_example_package(self):
        """The example package should inspect successfully."""
        example_pkg = PACKAGES_DIR / "fret_slot_strategy_example"
        if not example_pkg.exists():
            pytest.skip("Example package not found")

        exit_code, stdout, stderr = run_inspector(example_pkg)
        assert exit_code == 0, f"Expected success: {stderr}"

    def test_shows_package_type(self, valid_package):
        """Output should show package type."""
        exit_code, stdout, stderr = run_inspector(valid_package)
        assert "cam_assist_strategy_package" in stdout

    def test_shows_operation_type(self, valid_package):
        """Output should show operation type."""
        exit_code, stdout, stderr = run_inspector(valid_package)
        assert "fret_slot_strategy" in stdout

    def test_shows_authority_status(self, valid_package):
        """Output should show authority status."""
        exit_code, stdout, stderr = run_inspector(valid_package)
        assert "NON-EXECUTION PACKAGE" in stdout
        assert "Human review required" in stdout

    def test_shows_file_status(self, valid_package):
        """Output should show file status with [OK]."""
        exit_code, stdout, stderr = run_inspector(valid_package)
        assert "[OK]" in stdout

    def test_shows_non_execution_notice(self, valid_package):
        """Output should include non-execution notice."""
        exit_code, stdout, stderr = run_inspector(valid_package)
        assert "advisory only" in stdout
        assert "Human review is required" in stdout


class TestMissingFiles:
    """Tests for missing file detection."""

    def test_missing_manifest_fails(self, package_missing_manifest):
        """Missing manifest.json should fail."""
        exit_code, stdout, stderr = run_inspector(package_missing_manifest)
        assert exit_code == 1
        assert "[MISSING]" in stdout or "missing" in stdout.lower()

    def test_missing_strategy_file_fails(self, package_missing_strategy):
        """Missing strategy file should fail."""
        exit_code, stdout, stderr = run_inspector(package_missing_strategy)
        assert exit_code == 1
        assert "strategy" in stdout.lower()

    def test_missing_review_packet_fails(self, package_missing_review):
        """Missing review packet should fail."""
        exit_code, stdout, stderr = run_inspector(package_missing_review)
        assert exit_code == 1
        assert "review" in stdout.lower()


class TestAuthorityViolations:
    """Tests for authority violation detection."""

    def test_execution_authority_claim_fails(self, package_exec_authority_violation):
        """execution_authority_claim=true should fail."""
        exit_code, stdout, stderr = run_inspector(package_exec_authority_violation)
        assert exit_code == 1
        assert "AUTHORITY VIOLATION" in stdout or "execution_authority" in stdout.lower()

    def test_non_execution_false_fails(self, package_non_exec_false):
        """non_execution_declaration=false should fail."""
        exit_code, stdout, stderr = run_inspector(package_non_exec_false)
        assert exit_code == 1
        assert "AUTHORITY VIOLATION" in stdout or "non_execution" in stdout.lower()

    def test_human_review_false_fails(self, package_human_review_false):
        """requires_human_review=false should fail."""
        exit_code, stdout, stderr = run_inspector(package_human_review_false)
        assert exit_code == 1
        assert "AUTHORITY VIOLATION" in stdout or "human_review" in stdout.lower()


class TestOutputFormats:
    """Tests for output format options."""

    def test_json_output_works(self, valid_package):
        """--json should produce valid JSON output."""
        exit_code, stdout, stderr = run_inspector(valid_package, json_output=True)
        assert exit_code == 0

        data = json.loads(stdout)
        assert data["valid"] is True
        assert data["package_type"] == "cam_assist_strategy_package"
        assert "authority" in data
        assert "files" in data
        assert "provenance" in data

    def test_json_output_has_required_fields(self, valid_package):
        """JSON output should have all required fields."""
        exit_code, stdout, stderr = run_inspector(valid_package, json_output=True)
        data = json.loads(stdout)

        assert "valid" in data
        assert "package_type" in data
        assert "operation_type" in data
        assert "manifest_version" in data
        assert "authority" in data
        assert "files" in data
        assert "provenance" in data
        assert "warnings" in data

    def test_quiet_output_works(self, valid_package):
        """--quiet should produce minimal output."""
        exit_code, stdout, stderr = run_inspector(valid_package, quiet=True)
        assert exit_code == 0
        assert "PASS" in stdout
        assert len(stdout.strip().split("\n")) == 1


class TestWarnings:
    """Tests for warning generation."""

    def test_unknown_manifest_version_warns(self, tmp_path):
        """Unknown manifest version should produce warning."""
        pkg_dir = tmp_path / "unknown_version"
        pkg_dir.mkdir()

        (pkg_dir / "strategy.json").write_text("{}")
        review_content = "# Review\n" + ("x" * 1100)
        (pkg_dir / "review_packet.md").write_text(review_content)

        manifest = {
            "manifest_version": "99.0.0",
            "package_type": "cam_assist_strategy_package",
            "operation_type": "test",
            "strategy_file": "strategy.json",
            "review_packet_file": "review_packet.md",
            "source_geometry_files": ["geo.dxf"],
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
        (pkg_dir / "geo.dxf").write_text("DXF")

        exit_code, stdout, stderr = run_inspector(pkg_dir)
        assert exit_code == 0  # Should pass with warning
        assert "[WARN]" in stdout
        assert "version" in stdout.lower()

    def test_empty_source_geometry_warns(self, tmp_path):
        """Empty source_geometry_files should produce warning."""
        pkg_dir = tmp_path / "no_geometry"
        pkg_dir.mkdir()

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

        exit_code, stdout, stderr = run_inspector(pkg_dir)
        assert "[WARN]" in stdout
        assert "geometry" in stdout.lower()


class TestFileErrors:
    """Tests for file error handling."""

    def test_invalid_package_path_fails(self, tmp_path):
        """Nonexistent package path should return exit code 2."""
        fake_path = tmp_path / "nonexistent"
        exit_code, stdout, stderr = run_inspector(fake_path)
        assert exit_code == 2

    def test_file_instead_of_directory_fails(self, tmp_path):
        """File path instead of directory should fail."""
        file_path = tmp_path / "not_a_dir.txt"
        file_path.write_text("not a directory")

        exit_code, stdout, stderr = run_inspector(file_path)
        assert exit_code == 1
