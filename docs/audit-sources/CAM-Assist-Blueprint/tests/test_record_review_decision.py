"""
Tests for CAM Assist review decision record CLI.

These tests verify that the decision recorder correctly:
- Records decisions for valid staged packages
- Rejects invalid packages
- Validates decision values
- Requires reviewer identification
- Does not modify package contents
- Does not authorize machine execution
"""

import json
import pytest
from pathlib import Path
import subprocess
import sys


SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
SCHEMAS_DIR = Path(__file__).parent.parent / "schemas"
EXAMPLES_DIR = Path(__file__).parent.parent / "examples"

RECORDER_SCRIPT = SCRIPTS_DIR / "record_review_decision.py"
ASSEMBLER_SCRIPT = SCRIPTS_DIR / "assemble_strategy_package.py"
ARCHIVER_SCRIPT = SCRIPTS_DIR / "archive_strategy_package.py"
STAGER_SCRIPT = SCRIPTS_DIR / "stage_strategy_package.py"


def run_recorder(
    package_dir: Path,
    decision: str,
    reviewer: str,
    notes: str = "",
    out: Path | None = None,
    force: bool = False,
    quiet: bool = False,
) -> tuple[int, str, str]:
    """Run the decision recorder and return (exit_code, stdout, stderr)."""
    cmd = [
        sys.executable,
        str(RECORDER_SCRIPT),
        str(package_dir),
        "--decision",
        decision,
        "--reviewer",
        reviewer,
    ]
    if notes:
        cmd.extend(["--notes", notes])
    if out:
        cmd.extend(["--out", str(out)])
    if force:
        cmd.append("--force")
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
            "source_spec_id": "test-spec-001",
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


class TestValidDecisionRecording:
    """Tests for valid decision recording."""

    def test_valid_staged_package_records_decision(self, tmp_path):
        """Valid staged package should allow decision recording."""
        staging_root = tmp_path / "staging"
        pkg_dir = staging_root / "test_package"
        create_valid_staged_package(pkg_dir)

        exit_code, stdout, stderr = run_recorder(
            pkg_dir,
            decision="approve_for_downstream_cam",
            reviewer="Test Reviewer",
        )

        assert exit_code == 0, f"Expected success: {stderr}"
        decision_file = staging_root / "test_package.review_decision.json"
        assert decision_file.exists()

    def test_decision_record_has_required_fields(self, tmp_path):
        """Decision record should have all required fields."""
        staging_root = tmp_path / "staging"
        pkg_dir = staging_root / "test_package"
        create_valid_staged_package(pkg_dir)

        run_recorder(
            pkg_dir,
            decision="approve_for_downstream_cam",
            reviewer="Test Reviewer",
            notes="Test notes",
        )

        decision_file = staging_root / "test_package.review_decision.json"
        record = json.loads(decision_file.read_text())

        assert record["record_type"] == "cam_assist_review_decision"
        assert record["record_version"] == "1.0.0"
        assert record["package_path"] == str(pkg_dir)
        assert record["package_manifest_id"] == "fret_slot_strategy:test-spec-001"
        assert record["operation_type"] == "fret_slot_strategy"
        assert record["decision"] == "approve_for_downstream_cam"
        assert record["reviewer"] == "Test Reviewer"
        assert "reviewed_at" in record
        assert record["notes"] == "Test notes"

    def test_all_decision_types_work(self, tmp_path):
        """All decision types should work."""
        decisions = ["approve_for_downstream_cam", "reject", "needs_revision"]

        for i, decision in enumerate(decisions):
            staging_root = tmp_path / f"staging_{i}"
            pkg_dir = staging_root / "test_package"
            create_valid_staged_package(pkg_dir)

            exit_code, stdout, stderr = run_recorder(
                pkg_dir,
                decision=decision,
                reviewer="Test Reviewer",
            )

            assert exit_code == 0, f"Decision '{decision}' failed: {stderr}"

    def test_notes_optional(self, tmp_path):
        """Notes should be optional."""
        staging_root = tmp_path / "staging"
        pkg_dir = staging_root / "test_package"
        create_valid_staged_package(pkg_dir)

        exit_code, stdout, stderr = run_recorder(
            pkg_dir,
            decision="approve_for_downstream_cam",
            reviewer="Test Reviewer",
        )

        assert exit_code == 0
        decision_file = staging_root / "test_package.review_decision.json"
        record = json.loads(decision_file.read_text())
        assert record["notes"] == ""

    def test_custom_output_path(self, tmp_path):
        """Custom output path should work."""
        staging_root = tmp_path / "staging"
        pkg_dir = staging_root / "test_package"
        create_valid_staged_package(pkg_dir)

        custom_out = tmp_path / "custom" / "decision.json"
        exit_code, stdout, stderr = run_recorder(
            pkg_dir,
            decision="reject",
            reviewer="Test Reviewer",
            out=custom_out,
        )

        assert exit_code == 0
        assert custom_out.exists()


class TestAuthorityConstraints:
    """Tests for authority constraint enforcement."""

    def test_approval_does_not_claim_machine_execution(self, tmp_path):
        """Approval decision must not authorize machine execution."""
        staging_root = tmp_path / "staging"
        pkg_dir = staging_root / "test_package"
        create_valid_staged_package(pkg_dir)

        run_recorder(
            pkg_dir,
            decision="approve_for_downstream_cam",
            reviewer="Test Reviewer",
        )

        decision_file = staging_root / "test_package.review_decision.json"
        record = json.loads(decision_file.read_text())

        assert record["authority"]["does_not_authorize_machine_execution"] is True
        assert record["authority"]["requires_downstream_cam_verification"] is True
        assert record["authority"]["human_review_recorded"] is True


class TestValidationFailures:
    """Tests for validation failure handling."""

    def test_missing_package_fails(self, tmp_path):
        """Missing package should fail."""
        fake_dir = tmp_path / "nonexistent"

        exit_code, stdout, stderr = run_recorder(
            fake_dir,
            decision="approve_for_downstream_cam",
            reviewer="Test Reviewer",
        )

        assert exit_code == 2

    def test_invalid_package_fails(self, tmp_path):
        """Invalid package should fail decision recording."""
        staging_root = tmp_path / "staging"
        pkg_dir = staging_root / "invalid_package"
        create_invalid_staged_package(pkg_dir)

        exit_code, stdout, stderr = run_recorder(
            pkg_dir,
            decision="approve_for_downstream_cam",
            reviewer="Test Reviewer",
        )

        assert exit_code == 1

    def test_invalid_decision_value_fails(self, tmp_path):
        """Invalid decision value should fail."""
        staging_root = tmp_path / "staging"
        pkg_dir = staging_root / "test_package"
        create_valid_staged_package(pkg_dir)

        cmd = [
            sys.executable,
            str(RECORDER_SCRIPT),
            str(pkg_dir),
            "--decision",
            "invalid_decision",
            "--reviewer",
            "Test Reviewer",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)

        assert result.returncode != 0

    def test_missing_reviewer_fails(self, tmp_path):
        """Missing reviewer should fail."""
        staging_root = tmp_path / "staging"
        pkg_dir = staging_root / "test_package"
        create_valid_staged_package(pkg_dir)

        cmd = [
            sys.executable,
            str(RECORDER_SCRIPT),
            str(pkg_dir),
            "--decision",
            "approve_for_downstream_cam",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)

        assert result.returncode != 0


class TestOverwriteBehavior:
    """Tests for overwrite protection."""

    def test_existing_output_without_force_fails(self, tmp_path):
        """Existing output without --force should fail."""
        staging_root = tmp_path / "staging"
        pkg_dir = staging_root / "test_package"
        create_valid_staged_package(pkg_dir)

        decision_file = staging_root / "test_package.review_decision.json"
        decision_file.write_text('{"existing": true}')

        exit_code, stdout, stderr = run_recorder(
            pkg_dir,
            decision="approve_for_downstream_cam",
            reviewer="Test Reviewer",
        )

        assert exit_code == 1
        assert "force" in (stdout + stderr).lower() or "exists" in (stdout + stderr).lower()

    def test_existing_output_with_force_succeeds(self, tmp_path):
        """Existing output with --force should succeed."""
        staging_root = tmp_path / "staging"
        pkg_dir = staging_root / "test_package"
        create_valid_staged_package(pkg_dir)

        decision_file = staging_root / "test_package.review_decision.json"
        decision_file.write_text('{"existing": true}')

        exit_code, stdout, stderr = run_recorder(
            pkg_dir,
            decision="approve_for_downstream_cam",
            reviewer="Test Reviewer",
            force=True,
        )

        assert exit_code == 0
        record = json.loads(decision_file.read_text())
        assert record["decision"] == "approve_for_downstream_cam"


class TestPackageIntegrity:
    """Tests for package content integrity."""

    def test_package_files_not_modified(self, tmp_path):
        """Package files should not be modified."""
        staging_root = tmp_path / "staging"
        pkg_dir = staging_root / "test_package"
        create_valid_staged_package(pkg_dir)

        original_manifest = (pkg_dir / "manifest.json").read_text()
        original_strategy = (pkg_dir / "strategy.json").read_text()
        original_review = (pkg_dir / "review_packet.md").read_text()
        original_files = set(p.name for p in pkg_dir.iterdir())

        run_recorder(
            pkg_dir,
            decision="approve_for_downstream_cam",
            reviewer="Test Reviewer",
        )

        assert (pkg_dir / "manifest.json").read_text() == original_manifest
        assert (pkg_dir / "strategy.json").read_text() == original_strategy
        assert (pkg_dir / "review_packet.md").read_text() == original_review
        assert set(p.name for p in pkg_dir.iterdir()) == original_files


class TestQuietMode:
    """Tests for quiet mode."""

    def test_quiet_mode_success(self, tmp_path):
        """Quiet mode should print minimal output on success."""
        staging_root = tmp_path / "staging"
        pkg_dir = staging_root / "test_package"
        create_valid_staged_package(pkg_dir)

        exit_code, stdout, stderr = run_recorder(
            pkg_dir,
            decision="approve_for_downstream_cam",
            reviewer="Test Reviewer",
            quiet=True,
        )

        assert exit_code == 0
        assert "PASS" in stdout
        lines = [l for l in stdout.strip().split("\n") if l]
        assert len(lines) == 1

    def test_quiet_mode_failure(self, tmp_path):
        """Quiet mode should print minimal output on failure."""
        staging_root = tmp_path / "staging"
        pkg_dir = staging_root / "invalid_package"
        create_invalid_staged_package(pkg_dir)

        exit_code, stdout, stderr = run_recorder(
            pkg_dir,
            decision="approve_for_downstream_cam",
            reviewer="Test Reviewer",
            quiet=True,
        )

        assert exit_code == 1
        assert "FAIL" in stderr


class TestManifestIdGeneration:
    """Tests for package_manifest_id generation."""

    def test_manifest_id_uses_source_spec_id(self, tmp_path):
        """Manifest ID should use source_spec_id when available."""
        staging_root = tmp_path / "staging"
        pkg_dir = staging_root / "test_package"
        create_valid_staged_package(pkg_dir)

        run_recorder(
            pkg_dir,
            decision="approve_for_downstream_cam",
            reviewer="Test Reviewer",
        )

        decision_file = staging_root / "test_package.review_decision.json"
        record = json.loads(decision_file.read_text())
        assert record["package_manifest_id"] == "fret_slot_strategy:test-spec-001"

    def test_manifest_id_fallback(self, tmp_path):
        """Manifest ID should fallback when source_spec_id missing."""
        staging_root = tmp_path / "staging"
        pkg_dir = staging_root / "test_package"
        pkg_dir.mkdir(parents=True)

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
                "created_by": "test",
                "derivation_notes": "Test package",
            },
        }
        (pkg_dir / "manifest.json").write_text(json.dumps(manifest))

        run_recorder(
            pkg_dir,
            decision="approve_for_downstream_cam",
            reviewer="Test Reviewer",
        )

        decision_file = staging_root / "test_package.review_decision.json"
        record = json.loads(decision_file.read_text())
        assert record["package_manifest_id"] == "fret_slot_strategy:manifest"


class TestFullFlow:
    """Tests for full workflow integration."""

    def test_full_stage_queue_decision_flow(self, tmp_path):
        """Full workflow: stage -> queue -> decision should work."""
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

        staged_pkg = staged_root / "package"
        exit_code, stdout, stderr = run_recorder(
            staged_pkg,
            decision="approve_for_downstream_cam",
            reviewer="Integration Test",
            notes="Full flow test",
        )

        assert exit_code == 0
        decision_file = staged_root / "package.review_decision.json"
        assert decision_file.exists()
