"""
Tests for check_all.py policy support.

Tests verify:
- Policy loading
- Missing active script detection
- Severity-based exit codes
- JSON report generation

Part of Governance Execution Alignment Sprint.
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

# Repository root
REPO_ROOT = Path(__file__).parent.parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "governance" / "check_all.py"
POLICY_PATH = REPO_ROOT / "docs" / "governance" / "ontology" / "ontology_ci_policy.json"


class TestPolicyLoading:
    """Test policy file loading and validation."""

    def test_script_exists(self):
        """check_all.py must exist."""
        assert SCRIPT_PATH.exists(), f"Script not found: {SCRIPT_PATH}"

    def test_policy_exists(self):
        """Default ontology policy file must exist."""
        assert POLICY_PATH.exists(), f"Policy not found: {POLICY_PATH}"

    def test_policy_is_valid_json(self):
        """Policy file must be valid JSON."""
        with open(POLICY_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert "checks" in data
        assert isinstance(data["checks"], dict)

    def test_policy_checks_have_required_fields(self):
        """Each policy check must have required fields."""
        with open(POLICY_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        required_fields = {"script", "description", "severity", "tier", "active"}

        for check_id, check_info in data["checks"].items():
            for field in required_fields:
                assert field in check_info, f"Check '{check_id}' missing field: {field}"


class TestMissingActiveScriptDetection:
    """Test that missing active scripts are properly detected."""

    def test_missing_active_script_fails_strict_mode(self):
        """Missing active script should fail with --fail-on-missing-active-script."""
        # Create a temporary policy with a non-existent active script
        policy = {
            "checks": {
                "nonexistent_check": {
                    "script": "scripts/governance/does_not_exist.py",
                    "description": "A script that doesn't exist",
                    "severity": "blocking",
                    "tier": "ci",
                    "active": True,
                    "missing_script_behavior": "fail"
                }
            }
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(policy, f)
            temp_policy_path = f.name

        try:
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--policy", temp_policy_path,
                    "--strict-policy",
                    "--fail-on-missing-active-script",
                    "--tier", "ci",
                    "--mode", "block",
                ],
                capture_output=True,
                text=True,
                cwd=str(REPO_ROOT),
            )

            assert result.returncode == 2, (
                f"Expected exit code 2 for missing active script, got {result.returncode}\n"
                f"stdout: {result.stdout}\n"
                f"stderr: {result.stderr}"
            )
            assert "Missing active policy scripts" in result.stdout or "does_not_exist" in result.stdout
        finally:
            Path(temp_policy_path).unlink()

    def test_inactive_missing_script_does_not_fail(self):
        """Missing inactive script should not fail."""
        policy = {
            "checks": {
                "inactive_check": {
                    "script": "scripts/governance/does_not_exist.py",
                    "description": "Inactive script",
                    "severity": "blocking",
                    "tier": "ci",
                    "active": False,
                    "missing_script_behavior": "fail"
                }
            }
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(policy, f)
            temp_policy_path = f.name

        try:
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--policy", temp_policy_path,
                    "--strict-policy",
                    "--fail-on-missing-active-script",
                    "--tier", "ci",
                    "--mode", "warn",
                ],
                capture_output=True,
                text=True,
                cwd=str(REPO_ROOT),
                timeout=180,
            )

            # Should not fail due to missing inactive script
            # (may still fail due to other checks, but not with exit code 2)
            assert result.returncode != 2, (
                f"Should not fail with exit code 2 for inactive missing script\n"
                f"stdout: {result.stdout}"
            )
        finally:
            Path(temp_policy_path).unlink()


class TestSeverityBehavior:
    """Test that severity levels are handled correctly."""

    def test_warning_script_failure_does_not_block(self):
        """Warning-severity script failure should not block CI in warn mode."""
        # Create a policy with a warning-severity script that will fail
        policy = {
            "checks": {
                "fail_warning": {
                    "script": "scripts/governance/_test_fail_warning.py",
                    "description": "Always fails (warning)",
                    "severity": "warning",
                    "tier": "ci",
                    "active": True,
                    "missing_script_behavior": "fail"
                }
            }
        }

        # Create a temporary script that always fails
        fail_script = REPO_ROOT / "scripts" / "governance" / "_test_fail_warning.py"
        fail_script.write_text("import sys; sys.exit(1)")

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(policy, f)
            temp_policy_path = f.name

        try:
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--policy", temp_policy_path,
                    "--tier", "ci",
                    "--mode", "warn",  # warn mode
                ],
                capture_output=True,
                text=True,
                cwd=str(REPO_ROOT),
                timeout=180,
            )

            # In warn mode, even failures should exit 0
            assert result.returncode == 0, (
                f"Warn mode should exit 0 even with failures, got {result.returncode}\n"
                f"stdout: {result.stdout}"
            )
        finally:
            Path(temp_policy_path).unlink()
            fail_script.unlink(missing_ok=True)


class TestJsonOutput:
    """Test JSON report generation."""

    def test_json_output_is_valid(self):
        """JSON output should be valid and contain expected fields."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            output_path = f.name

        try:
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--tier", "precommit",
                    "--mode", "warn",
                    "--json-output", output_path,
                ],
                capture_output=True,
                text=True,
                cwd=str(REPO_ROOT),
                timeout=120,
            )

            # Load and validate the JSON report
            with open(output_path, "r", encoding="utf-8") as f:
                report = json.load(f)

            assert "timestamp" in report
            assert "mode" in report
            assert "tier" in report
            assert "checks" in report
            assert "passed" in report
            assert "failed_blocking" in report
            assert "exit_code" in report
            assert isinstance(report["checks"], list)

            # Each check should have expected fields
            if report["checks"]:
                check = report["checks"][0]
                assert "id" in check
                assert "script" in check
                assert "passed" in check
                assert "tier" in check
                assert "severity" in check
        finally:
            Path(output_path).unlink(missing_ok=True)


class TestListCommand:
    """Test --list command."""

    def test_list_shows_checks(self):
        """--list should show available checks."""
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "--list",
            ],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )

        assert result.returncode == 0
        assert "Available governance checks" in result.stdout
        assert "PRECOMMIT" in result.stdout
        assert "CI" in result.stdout

    def test_list_with_policy_shows_policy_checks(self):
        """--list with --policy should show policy checks."""
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "--list",
                "--policy", str(POLICY_PATH),
            ],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )

        assert result.returncode == 0
        assert "POLICY CHECKS" in result.stdout or "policy" in result.stdout.lower()


class TestIntegration:
    """Integration tests with actual governance checks."""

    @pytest.mark.slow
    def test_ci_tier_runs_without_error(self):
        """CI tier should run without script errors."""
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "--tier", "ci",
                "--mode", "warn",
                "--verbose",
            ],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            timeout=180,
        )

        # Should not crash (exit 0 in warn mode)
        assert result.returncode == 0, (
            f"CI tier failed with exit {result.returncode}\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )

    @pytest.mark.slow
    def test_precommit_tier_is_fast(self):
        """Precommit tier should complete in under 30 seconds."""
        import time

        start = time.time()
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "--tier", "precommit",
                "--mode", "warn",
            ],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            timeout=60,
        )
        duration = time.time() - start

        assert result.returncode == 0
        assert duration < 30, f"Precommit tier took {duration:.1f}s, expected <30s"
