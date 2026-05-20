"""
Tests for detect_semantic_drift.py

Tests verify:
- Finding categorization
- JSON output format
- Exit code behavior (always 0 for drift)

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
SCRIPT_PATH = REPO_ROOT / "scripts" / "governance" / "detect_semantic_drift.py"


class TestScriptExecution:
    """Test basic script execution."""

    def test_script_exists(self):
        """Script must exist."""
        assert SCRIPT_PATH.exists()

    def test_script_runs_without_error(self):
        """Script should run without crashing."""
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH)],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            timeout=120,
        )
        assert result.returncode == 0


class TestFindingCategorization:
    """Test that findings are properly categorized."""

    def test_findings_have_categories(self):
        """All findings should have a category."""
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--json"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            timeout=120,
        )
        output = json.loads(result.stdout)

        for finding in output.get("findings", []):
            assert "category" in finding
            assert finding["category"] in [
                "duplicate_definition",
                "possible_collision",
                "unknown_semantic_term",
                "canonical_usage",
                "alias_usage",
                "deprecated_alias",
            ]

    def test_summary_has_category_counts(self):
        """Summary should have counts by category."""
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--json"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            timeout=120,
        )
        output = json.loads(result.stdout)
        summary = output.get("summary", {})

        assert "duplicate_definitions" in summary
        assert "possible_collisions" in summary
        assert "unknown_terms" in summary
        assert "total_findings" in summary


class TestJsonOutput:
    """Test JSON output functionality."""

    def test_json_flag_produces_valid_json(self):
        """--json flag should produce valid JSON."""
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--json"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            timeout=120,
        )
        output = json.loads(result.stdout)
        assert "summary" in output
        assert "findings" in output

    def test_json_output_file(self):
        """--json-output should write to file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            output_path = f.name

        try:
            result = subprocess.run(
                [sys.executable, str(SCRIPT_PATH), "--json-output", output_path],
                capture_output=True,
                text=True,
                cwd=str(REPO_ROOT),
                timeout=120,
            )

            with open(output_path, "r", encoding="utf-8") as f:
                output = json.load(f)

            assert "summary" in output
            assert "findings" in output
            assert "passed" in output
        finally:
            Path(output_path).unlink(missing_ok=True)

    def test_json_includes_counts(self):
        """JSON output should include advisory and warning counts."""
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--json"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            timeout=120,
        )
        output = json.loads(result.stdout)

        assert "advisory_count" in output
        assert "warning_count" in output


class TestExitCodes:
    """Test exit code behavior."""

    def test_drift_always_exits_zero(self):
        """Semantic drift detection should always exit 0 (advisory only)."""
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH)],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            timeout=120,
        )
        # Drift detection is advisory-only, never blocking
        assert result.returncode == 0

    def test_passed_flag_is_true(self):
        """Passed flag should be true for advisory-only output."""
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--json"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            timeout=120,
        )
        output = json.loads(result.stdout)

        # Drift detection is advisory, so passed should be true
        # unless there are actual errors (not findings)
        assert output["passed"] is True


class TestQuietMode:
    """Test quiet mode behavior."""

    def test_quiet_suppresses_human_output(self):
        """--quiet should suppress human-readable output."""
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--quiet"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            timeout=120,
        )
        assert "SEMANTIC DRIFT DETECTION REPORT" not in result.stdout

    def test_quiet_with_json_output(self):
        """--quiet with --json-output should produce no human output."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            output_path = f.name

        try:
            result = subprocess.run(
                [sys.executable, str(SCRIPT_PATH), "--quiet", "--json-output", output_path],
                capture_output=True,
                text=True,
                cwd=str(REPO_ROOT),
                timeout=120,
            )

            # With --quiet, no human output is produced
            assert "SEMANTIC DRIFT" not in result.stdout

            # But the JSON file should still be written
            assert Path(output_path).exists()
            with open(output_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            assert "summary" in data
        finally:
            Path(output_path).unlink(missing_ok=True)


class TestSeverityClassification:
    """Test finding severity classification."""

    def test_findings_have_severity(self):
        """All findings should have a severity."""
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--json"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            timeout=120,
        )
        output = json.loads(result.stdout)

        for finding in output.get("findings", []):
            assert "severity" in finding
            assert finding["severity"] in ["advisory", "warning", "error"]

    def test_no_error_severity_findings(self):
        """Drift findings should not have error severity."""
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--json"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            timeout=120,
        )
        output = json.loads(result.stdout)

        error_findings = [f for f in output.get("findings", []) if f.get("severity") == "error"]
        assert len(error_findings) == 0, "Drift findings should be advisory/warning, not error"
