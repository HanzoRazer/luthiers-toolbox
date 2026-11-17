#!/usr/bin/env python3
"""Threshold and baseline-consistency tests for the client lint ratchet.

The checker compares total_errors and total_warnings to the ceilings. It prints
the linted-file count and does not fail when that count falls. It also does not
read the per-rule maps when deciding pass or fail. These tests pin the ceiling
boundary with temporary ESLint JSON, and they fail if the committed baseline's
per-rule counts do not sum to its totals.

Stdlib-only. Run:
    python scripts/ci/test_client_lint_ratchet.py
    python -m pytest scripts/ci/test_client_lint_ratchet.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import check_client_lint_ratchet as mod  # noqa: E402

SCRIPT = os.path.join(HERE, "check_client_lint_ratchet.py")
WORKFLOW = os.path.join(HERE, "..", "..", ".github", "workflows", "client_lint_build.yml")

WARNING_CEILING = 6967
ERROR_CEILING = 34
FILES_LINTED = 1486


def rule_sums_match(baseline: dict) -> bool:
    warnings = baseline.get("warnings_by_rule") or {}
    errors = baseline.get("errors_by_rule") or {}
    by_file = baseline.get("errors_by_file") or {}
    return (
        sum(warnings.values()) == baseline.get("total_warnings")
        and sum(errors.values()) == baseline.get("total_errors")
        and sum(by_file.values()) == baseline.get("total_errors")
    )


def _message(rule: str, severity: int, index: int) -> dict:
    return {
        "ruleId": rule,
        "severity": severity,
        "line": index + 1,
        "column": 1,
        "message": f"{rule} #{index}",
    }


def make_report(warnings: int, errors: int, files: int = 1) -> list:
    if files < 1:
        return []
    pending_w = [
        _message("vue/max-attributes-per-line", mod.SEV_WARNING, i) for i in range(warnings)
    ]
    pending_e = [
        _message("no-empty", mod.SEV_ERROR, i) for i in range(errors)
    ]
    chunks = [[] for _ in range(files)]
    for i, msg in enumerate(pending_w + pending_e):
        chunks[i % files].append(msg)
    return [
        {"filePath": f"/packages/client/src/fixture_{n}.ts", "messages": msgs}
        for n, msgs in enumerate(chunks)
    ]


class RatchetCliTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def _write(self, name: str, payload) -> str:
        path = os.path.join(self.tmp.name, name)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            if isinstance(payload, str):
                fh.write(payload)
            else:
                json.dump(payload, fh)
        return path

    def _run(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, SCRIPT, *args],
            capture_output=True, text=True, encoding="utf-8",
        )

    def _ceiling(self, warnings: int = WARNING_CEILING, errors: int = ERROR_CEILING,
                 files: int = FILES_LINTED) -> str:
        return self._write("baseline.json", {
            "total_errors": errors,
            "total_warnings": warnings,
            "files_linted": files,
            "errors_by_rule": {},
            "errors_by_file": {},
            "warnings_by_rule": {},
        })

    def test_warning_ceiling_passes_at_6967(self):
        report = self._write("report.json", make_report(WARNING_CEILING, ERROR_CEILING))
        result = self._run("--report", report, "--baseline", self._ceiling())
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PASS", result.stdout)
        self.assertIn(
            f"warnings: {WARNING_CEILING:>5}  (ceiling {WARNING_CEILING})",
            result.stdout,
        )

    def test_one_warning_over_ceiling_fails(self):
        report = self._write("report.json", make_report(WARNING_CEILING + 1, ERROR_CEILING))
        result = self._run("--report", report, "--baseline", self._ceiling())
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(
            f"warnings rose {WARNING_CEILING} -> {WARNING_CEILING + 1} (+1)",
            result.stdout,
        )

    def test_one_error_over_ceiling_fails(self):
        report = self._write("report.json", make_report(WARNING_CEILING, ERROR_CEILING + 1))
        result = self._run("--report", report, "--baseline", self._ceiling())
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(
            f"errors rose {ERROR_CEILING} -> {ERROR_CEILING + 1} (+1)",
            result.stdout,
        )

    def test_missing_baseline_fails_closed(self):
        report = self._write("report.json", make_report(1, 0))
        missing = os.path.join(self.tmp.name, "absent.json")
        result = self._run("--report", report, "--baseline", missing)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("baseline not found", result.stdout + result.stderr)

    def test_malformed_baseline_fails_closed(self):
        report = self._write("report.json", make_report(1, 0))
        baseline = self._write("baseline.json", "{")
        result = self._run("--report", report, "--baseline", baseline)
        self.assertNotEqual(result.returncode, 0)

    def test_baseline_missing_ceiling_fails_closed(self):
        report = self._write("report.json", make_report(1, 0))
        baseline = self._write("baseline.json", {"files_linted": 1})
        result = self._run("--report", report, "--baseline", baseline)
        self.assertNotEqual(result.returncode, 0)

    def test_missing_report_fails_closed(self):
        missing = os.path.join(self.tmp.name, "absent.json")
        result = self._run("--report", missing, "--baseline", self._ceiling())
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("ESLint report not found", result.stdout + result.stderr)

    def test_empty_report_fails_closed(self):
        report = self._write("report.json", "")
        result = self._run("--report", report, "--baseline", self._ceiling())
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("empty", result.stdout + result.stderr)

    def test_zero_file_report_fails_closed(self):
        report = self._write("report.json", [])
        result = self._run("--report", report, "--baseline", self._ceiling())
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("zero files", result.stdout + result.stderr)

    def test_reduced_file_count_is_printed_and_does_not_fail_on_totals(self):
        # The checker does not compare files_linted. A smaller run stays visible
        # in the summary line. That is the conspicuous signal; it is not a rewrite
        # of the pass/fail rule.
        report = self._write("report.json", make_report(1, 0, files=1))
        baseline = self._ceiling(warnings=1, errors=0, files=5)
        result = self._run("--report", report, "--baseline", baseline)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("ESLint over 1 files", result.stdout)

    def test_write_baseline_rule_counts_sum_to_totals(self):
        report = self._write("report.json", make_report(3, 2, files=2))
        baseline = os.path.join(self.tmp.name, "written.json")
        result = self._run("--report", report, "--baseline", baseline, "--write-baseline")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        with open(baseline, encoding="utf-8") as fh:
            data = json.load(fh)
        self.assertEqual(data["total_warnings"], 3)
        self.assertEqual(data["total_errors"], 2)
        self.assertEqual(data["files_linted"], 2)
        self.assertTrue(rule_sums_match(data))

    def test_checking_does_not_rewrite_the_baseline(self):
        report = self._write("report.json", make_report(1, 0))
        baseline = self._ceiling(warnings=1, errors=0, files=1)
        with open(baseline, "rb") as fh:
            before = fh.read()
        result = self._run("--report", report, "--baseline", baseline)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        with open(baseline, "rb") as fh:
            self.assertEqual(fh.read(), before)


class CommittedBaselineTests(unittest.TestCase):
    def test_committed_baseline_matches_the_measured_ceiling(self):
        with open(mod.DEFAULT_BASELINE, encoding="utf-8") as fh:
            data = json.load(fh)
        self.assertEqual(data["total_warnings"], WARNING_CEILING)
        self.assertEqual(data["total_errors"], ERROR_CEILING)
        self.assertEqual(data["files_linted"], FILES_LINTED)
        self.assertEqual(data["warnings_by_rule"]["@typescript-eslint/no-explicit-any"], 957)
        self.assertEqual(data["warnings_by_rule"]["max-lines-per-function"], 137)
        self.assertTrue(rule_sums_match(data), data)

    def test_inconsistent_rule_count_sum_fails(self):
        with open(mod.DEFAULT_BASELINE, encoding="utf-8") as fh:
            data = json.load(fh)
        data["warnings_by_rule"] = dict(data["warnings_by_rule"])
        rule = next(iter(data["warnings_by_rule"]))
        data["warnings_by_rule"][rule] += 1
        self.assertFalse(rule_sums_match(data))


class WorkflowPathTests(unittest.TestCase):
    def test_baseline_and_ratchet_paths_trigger_lint_build(self):
        with open(WORKFLOW, encoding="utf-8") as fh:
            text = fh.read()
        required = (
            "scripts/ci/client_lint_baseline.json",
            "scripts/ci/check_client_lint_ratchet.py",
        )
        pull_start = text.index("pull_request:")
        push_start = text.index("\n  push:")
        concurrency_start = text.index("\nconcurrency:")
        blocks = {
            "pull_request:": text[pull_start:push_start],
            "push:": text[push_start:concurrency_start],
        }
        for event, block in blocks.items():
            for path in required:
                self.assertIn(path, block, f"{path} missing from {event}")


if __name__ == "__main__":
    unittest.main()
