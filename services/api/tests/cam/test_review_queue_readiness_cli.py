"""CLI tests — exit codes, formats, determinism, and safety."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[4]
_SCRIPT = _REPO_ROOT / "scripts" / "ci" / "check_review_queue_readiness.py"

EXIT_OK = 0
EXIT_NOT_READY = 1
EXIT_EVALUATOR_ERROR = 2


def _run(*args):
    return subprocess.run(
        [sys.executable, str(_SCRIPT), *args],
        capture_output=True, text=True, cwd=str(_REPO_ROOT),
    )


@pytest.mark.skipif(not _SCRIPT.exists(), reason="CLI script not present")
class TestExitCodes:
    def test_enforcement_mode_fails_while_gaps_remain(self):
        """Blocking gaps are open today, so enforcement mode must exit 1."""
        assert _run("--format", "json").returncode == EXIT_NOT_READY

    def test_report_only_does_not_fail_on_known_gaps(self):
        """The CI rollout mode: truthful report, no merge block."""
        result = _run("--report-only")
        assert result.returncode == EXIT_OK
        assert "NOT_READY" in result.stdout
        assert "Enforcement: DISABLED" in result.stdout

    def test_invalid_format_is_a_usage_error_not_a_readiness_verdict(self):
        """argparse exits 2 for usage errors, which shares EXIT_EVALUATOR_ERROR.

        That overlap is intentional and documented in the CLI: both mean "no verdict was
        produced". What must never happen is an invalid argument being reported as a
        readiness result, so the assertion is on that, not on the specific code.
        """
        result = _run("--format", "yaml")
        assert result.returncode not in (EXIT_OK, EXIT_NOT_READY)
        assert "Traceback" not in result.stderr
        assert "invalid choice" in result.stderr


@pytest.mark.skipif(not _SCRIPT.exists(), reason="CLI script not present")
class TestOutputFormats:
    def test_json_is_valid_and_carries_schema_version(self):
        payload = json.loads(_run("--format", "json").stdout)
        assert payload["schema_version"].startswith("review-queue-readiness/")
        assert payload["aggregate"] in ("READY", "READY_WITH_WARNINGS", "NOT_READY")

    def test_json_output_is_byte_identical_across_runs(self):
        assert _run("--format", "json").stdout == _run("--format", "json").stdout

    def test_json_contains_no_host_paths_or_timestamps(self):
        raw = _run("--format", "json").stdout
        assert "C:\\" not in raw and "/home/" not in raw
        payload = json.loads(raw)
        assert "generated_at" not in payload and "timestamp" not in payload

    def test_text_output_leads_with_status_and_ends_with_notice(self):
        out = _run("--format", "text").stdout
        assert "Status:" in out
        assert "does not authorize" in out

    def test_output_file_is_written(self, tmp_path):
        target = tmp_path / "nested" / "report.json"
        assert _run("--format", "json", "--output", str(target)).returncode in (
            EXIT_OK, EXIT_NOT_READY
        )
        assert json.loads(target.read_text(encoding="utf-8"))["schema_version"]

    def test_unwritable_output_is_reported_without_a_traceback(self, tmp_path):
        blocker = tmp_path / "afile"
        blocker.write_text("x", encoding="utf-8")
        result = _run("--format", "json", "--output", str(blocker / "report.json"))
        assert result.returncode == EXIT_EVALUATOR_ERROR
        assert "Traceback" not in result.stderr


@pytest.mark.skipif(not _SCRIPT.exists(), reason="CLI script not present")
class TestSafety:
    def test_no_flag_lets_a_caller_assert_readiness(self):
        help_text = _run("--help").stdout.lower()
        for forbidden in ("--ready", "--satisfied", "--force-ready", "--set-status"):
            assert forbidden not in help_text

    def test_authorization_invariants_are_false_in_output(self):
        payload = json.loads(_run("--format", "json").stdout)
        assert payload["implementation_authorized"] is False
        assert payload["execution_authorized"] is False
        assert payload["machine_output_allowed"] is False

    def test_run_does_not_mutate_the_working_tree(self):
        before = subprocess.run(
            ["git", "status", "--porcelain"], capture_output=True, text=True,
            cwd=str(_REPO_ROOT),
        ).stdout
        _run("--format", "json")
        after = subprocess.run(
            ["git", "status", "--porcelain"], capture_output=True, text=True,
            cwd=str(_REPO_ROOT),
        ).stdout
        assert before == after
