"""
Tests for CAM Assist staged package review queue index generator.

These tests verify that the indexer correctly:
- Discovers staged packages
- Indexes valid and invalid packages
- Generates Markdown review queue
- Generates optional JSON output
- Does not mutate package contents
- Continues after invalid packages
"""

import json
import pytest
from pathlib import Path
import subprocess
import sys


SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
EXAMPLES_DIR = Path(__file__).parent.parent / "examples"

INDEXER_SCRIPT = SCRIPTS_DIR / "index_staged_packages.py"
ASSEMBLER_SCRIPT = SCRIPTS_DIR / "assemble_strategy_package.py"
ARCHIVER_SCRIPT = SCRIPTS_DIR / "archive_strategy_package.py"
STAGER_SCRIPT = SCRIPTS_DIR / "stage_strategy_package.py"


def run_indexer(
    staged_root: Path,
    out: Path | None = None,
    json_out: Path | None = None,
    quiet: bool = False,
) -> tuple[int, str, str]:
    """Run the staged package indexer and return (exit_code, stdout, stderr)."""
    cmd = [sys.executable, str(INDEXER_SCRIPT), str(staged_root)]
    if out:
        cmd.extend(["--out", str(out)])
    if json_out:
        cmd.extend(["--json-out", str(json_out)])
    if quiet:
        cmd.append("--quiet")
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr


def create_valid_staged_package(pkg_dir: Path) -> None:
    """Create a valid staged package directory."""
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
    (pkg_dir / "manifest.json").write_text(json.dumps(manifest))


def create_invalid_staged_package(pkg_dir: Path) -> None:
    """Create an invalid staged package (execution authority claim)."""
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
        "source_geometry_files": [],
        "created_at": "2026-05-23T12:00:00Z",
        "authority": {
            "non_execution_declaration": True,
            "execution_authority_claim": True,
            "requires_human_review": True,
        },
        "provenance": {
            "source_spec_id": "test-spec",
            "created_by": "test",
            "derivation_notes": "Test package",
        },
    }
    (pkg_dir / "manifest.json").write_text(json.dumps(manifest))


def create_no_human_review_package(pkg_dir: Path) -> None:
    """Create a package with requires_human_review = false."""
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
        "source_geometry_files": [],
        "created_at": "2026-05-23T12:00:00Z",
        "authority": {
            "non_execution_declaration": True,
            "execution_authority_claim": False,
            "requires_human_review": False,
        },
        "provenance": {
            "source_spec_id": "test-spec",
            "created_by": "test",
            "derivation_notes": "Test package",
        },
    }
    (pkg_dir / "manifest.json").write_text(json.dumps(manifest))


class TestPackageDiscovery:
    """Tests for staged package discovery."""

    def test_valid_staged_package_appears_in_queue(self, tmp_path):
        """Valid staged package should appear in queue."""
        staged_root = tmp_path / "staging"
        create_valid_staged_package(staged_root / "valid_package")

        exit_code, stdout, stderr = run_indexer(staged_root)

        assert exit_code == 0
        queue_file = staged_root / "REVIEW_QUEUE.md"
        assert queue_file.exists()
        content = queue_file.read_text()
        assert "valid_package" in content

    def test_invalid_staged_package_appears_as_invalid(self, tmp_path):
        """Invalid staged package should appear as invalid."""
        staged_root = tmp_path / "staging"
        create_invalid_staged_package(staged_root / "invalid_package")

        exit_code, stdout, stderr = run_indexer(staged_root)

        assert exit_code == 0
        queue_file = staged_root / "REVIEW_QUEUE.md"
        content = queue_file.read_text()
        assert "invalid" in content.lower()

    def test_multiple_staged_packages_indexed(self, tmp_path):
        """Multiple staged packages should all appear in queue."""
        staged_root = tmp_path / "staging"
        create_valid_staged_package(staged_root / "package_a")
        create_valid_staged_package(staged_root / "package_b")
        create_invalid_staged_package(staged_root / "package_c")

        exit_code, stdout, stderr = run_indexer(staged_root)

        assert exit_code == 0
        queue_file = staged_root / "REVIEW_QUEUE.md"
        content = queue_file.read_text()
        assert "package_a" in content
        assert "package_b" in content
        assert "package_c" in content
        assert "Total staged packages: 3" in content

    def test_nested_packages_indexed(self, tmp_path):
        """Nested packages should be indexed with relative paths."""
        staged_root = tmp_path / "staging"
        create_valid_staged_package(staged_root / "nested" / "deep_package")

        exit_code, stdout, stderr = run_indexer(staged_root)

        assert exit_code == 0
        queue_file = staged_root / "REVIEW_QUEUE.md"
        content = queue_file.read_text()
        assert "nested" in content


class TestQueueOutput:
    """Tests for queue output format."""

    def test_markdown_queue_output_created(self, tmp_path):
        """Markdown queue file should be created."""
        staged_root = tmp_path / "staging"
        create_valid_staged_package(staged_root / "test_package")

        exit_code, stdout, stderr = run_indexer(staged_root)

        assert exit_code == 0
        queue_file = staged_root / "REVIEW_QUEUE.md"
        assert queue_file.exists()

    def test_custom_output_path(self, tmp_path):
        """Custom output path should work."""
        staged_root = tmp_path / "staging"
        create_valid_staged_package(staged_root / "test_package")
        custom_out = tmp_path / "custom" / "queue.md"

        exit_code, stdout, stderr = run_indexer(staged_root, out=custom_out)

        assert exit_code == 0
        assert custom_out.exists()

    def test_non_execution_notice_included(self, tmp_path):
        """Non-execution notice should be in queue."""
        staged_root = tmp_path / "staging"
        create_valid_staged_package(staged_root / "test_package")

        run_indexer(staged_root)

        queue_file = staged_root / "REVIEW_QUEUE.md"
        content = queue_file.read_text()
        assert "Non-Execution Notice" in content
        assert "advisory only" in content.lower()

    def test_summary_section_included(self, tmp_path):
        """Summary section should be in queue."""
        staged_root = tmp_path / "staging"
        create_valid_staged_package(staged_root / "pkg1")
        create_invalid_staged_package(staged_root / "pkg2")

        run_indexer(staged_root)

        queue_file = staged_root / "REVIEW_QUEUE.md"
        content = queue_file.read_text()
        assert "## Summary" in content
        assert "Total staged packages: 2" in content
        assert "Valid packages: 1" in content
        assert "Invalid packages: 1" in content

    def test_human_review_column_shows_violation(self, tmp_path):
        """Human review column should show violations."""
        staged_root = tmp_path / "staging"
        create_no_human_review_package(staged_root / "no_review_pkg")

        run_indexer(staged_root)

        queue_file = staged_root / "REVIEW_QUEUE.md"
        content = queue_file.read_text()
        assert "No [INVALID]" in content


class TestJsonOutput:
    """Tests for JSON queue output."""

    def test_json_output_created(self, tmp_path):
        """JSON queue file should be created when requested."""
        staged_root = tmp_path / "staging"
        create_valid_staged_package(staged_root / "test_package")
        json_out = tmp_path / "queue.json"

        exit_code, stdout, stderr = run_indexer(staged_root, json_out=json_out)

        assert exit_code == 0
        assert json_out.exists()

    def test_json_structure(self, tmp_path):
        """JSON output should have correct structure."""
        staged_root = tmp_path / "staging"
        create_valid_staged_package(staged_root / "test_package")
        json_out = tmp_path / "queue.json"

        run_indexer(staged_root, json_out=json_out)

        data = json.loads(json_out.read_text())
        assert "generated_at" in data
        assert "summary" in data
        assert "packages" in data
        assert data["summary"]["total"] == 1
        assert data["summary"]["valid"] == 1

    def test_json_package_entry(self, tmp_path):
        """JSON package entries should have required fields."""
        staged_root = tmp_path / "staging"
        create_valid_staged_package(staged_root / "test_package")
        json_out = tmp_path / "queue.json"

        run_indexer(staged_root, json_out=json_out)

        data = json.loads(json_out.read_text())
        pkg = data["packages"][0]
        assert "path" in pkg
        assert "operation_type" in pkg
        assert "status" in pkg
        assert "requires_human_review" in pkg
        assert "warnings" in pkg


class TestErrorHandling:
    """Tests for error handling."""

    def test_missing_staged_root_fails(self, tmp_path):
        """Missing staged root should fail with exit code 2."""
        fake_path = tmp_path / "nonexistent"

        exit_code, stdout, stderr = run_indexer(fake_path)

        assert exit_code == 2

    def test_no_packages_found_fails(self, tmp_path):
        """No packages found should fail with exit code 1."""
        staged_root = tmp_path / "empty_staging"
        staged_root.mkdir()

        exit_code, stdout, stderr = run_indexer(staged_root)

        assert exit_code == 1

    def test_invalid_packages_do_not_stop_indexing(self, tmp_path):
        """Invalid packages should not prevent indexing others."""
        staged_root = tmp_path / "staging"
        create_valid_staged_package(staged_root / "valid_pkg")
        create_invalid_staged_package(staged_root / "invalid_pkg")

        exit_code, stdout, stderr = run_indexer(staged_root)

        assert exit_code == 0
        queue_file = staged_root / "REVIEW_QUEUE.md"
        content = queue_file.read_text()
        assert "valid_pkg" in content
        assert "invalid_pkg" in content


class TestQuietMode:
    """Tests for quiet mode."""

    def test_quiet_mode_success(self, tmp_path):
        """Quiet mode should print minimal output on success."""
        staged_root = tmp_path / "staging"
        create_valid_staged_package(staged_root / "test_package")

        exit_code, stdout, stderr = run_indexer(staged_root, quiet=True)

        assert exit_code == 0
        assert "PASS" in stdout
        lines = [l for l in stdout.strip().split("\n") if l]
        assert len(lines) == 1

    def test_quiet_mode_failure(self, tmp_path):
        """Quiet mode should print minimal output on failure."""
        staged_root = tmp_path / "empty"
        staged_root.mkdir()

        exit_code, stdout, stderr = run_indexer(staged_root, quiet=True)

        assert exit_code == 1
        assert "FAIL" in stderr


class TestPackageIntegrity:
    """Tests for package content integrity."""

    def test_package_contents_not_mutated(self, tmp_path):
        """Package contents should not be mutated."""
        staged_root = tmp_path / "staging"
        pkg_dir = staged_root / "test_package"
        create_valid_staged_package(pkg_dir)

        original_manifest = (pkg_dir / "manifest.json").read_text()
        original_strategy = (pkg_dir / "strategy.json").read_text()
        original_review = (pkg_dir / "review_packet.md").read_text()

        run_indexer(staged_root)

        assert (pkg_dir / "manifest.json").read_text() == original_manifest
        assert (pkg_dir / "strategy.json").read_text() == original_strategy
        assert (pkg_dir / "review_packet.md").read_text() == original_review


class TestFullFlow:
    """Tests for full assemble -> archive -> validate -> stage -> queue flow."""

    def test_full_assemble_archive_stage_queue_flow(self, tmp_path):
        """Full workflow should work end to end."""
        strategy_path = EXAMPLES_DIR / "valid" / "fret_slot_strategy.json"
        if not strategy_path.exists():
            pytest.skip("Example strategy not found")

        package_dir = tmp_path / "assembled"
        archive_path = tmp_path / "package.zip"
        staged_root = tmp_path / "staging"

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
        assert result1.returncode == 0

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
        assert result2.returncode == 0

        result3 = subprocess.run(
            [
                sys.executable,
                str(STAGER_SCRIPT),
                str(archive_path),
                "--out",
                str(staged_root),
            ],
            capture_output=True,
            text=True,
        )
        assert result3.returncode == 0

        exit_code, stdout, stderr = run_indexer(staged_root)

        assert exit_code == 0
        queue_file = staged_root / "REVIEW_QUEUE.md"
        assert queue_file.exists()
        content = queue_file.read_text()
        assert "package" in content.lower()
