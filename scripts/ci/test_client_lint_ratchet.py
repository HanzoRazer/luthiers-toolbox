#!/usr/bin/env python3
"""Threshold and baseline-consistency tests for the client lint ratchet.

The checker compares total_errors and total_warnings to their ceilings and
files_linted to its floor. It does not read the per-rule maps when deciding pass
or fail. These tests pin the ceiling and floor boundaries with temporary ESLint
JSON, check that a bad baseline fails with a stated reason, and fail if the
committed baseline's per-rule counts do not sum to its totals. The workflow
path filters are read by indentation, so a path mentioned only in a comment or
in another section does not count.

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
    total_w = baseline.get("total_warnings")
    if len(warnings) < mod.WARNINGS_BY_RULE_LIMIT:
        warnings_ok = sum(warnings.values()) == total_w
    else:
        # The writer keeps only the top rules; the map is a lower bound.
        warnings_ok = len(warnings) == mod.WARNINGS_BY_RULE_LIMIT and sum(warnings.values()) <= total_w
    return (
        warnings_ok
        and sum(errors.values()) == baseline.get("total_errors")
        and sum(by_file.values()) == baseline.get("total_errors")
    )


def _strip_comment(line: str) -> str:
    # Workflow path filters here are quoted globs without '#', so a '#' that
    # starts a line or follows whitespace begins a comment.
    for i, ch in enumerate(line):
        if ch == "#" and (i == 0 or line[i - 1].isspace()):
            return line[:i].rstrip()
    return line.rstrip()


def trigger_paths(text: str) -> dict:
    """Map each event under the top-level `on:` key to its `paths:` list."""
    lines = [_strip_comment(raw) for raw in text.splitlines()]
    lines = [ln for ln in lines if ln.strip()]
    out: dict = {}
    in_on = False
    event = None
    in_paths = False
    for ln in lines:
        level, body = len(ln) - len(ln.lstrip(" ")), ln.strip()
        if level == 0:
            in_on = body in ("on:", '"on":', "'on':")
            event, in_paths = None, False
            continue
        if not in_on:
            continue
        if level == 2 and body.endswith(":"):
            event, in_paths = body[:-1], False
            out.setdefault(event, [])
        elif level == 4 and event:
            in_paths = body == "paths:"
        elif level == 6 and in_paths and body.startswith("- "):
            out[event].append(body[2:].strip().strip("\"'"))
    return out


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
                 files: int = 1) -> str:
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
        self.assertEqual(result.returncode, 1)
        self.assertIn("FAIL: baseline", result.stderr)
        self.assertIn("not valid JSON", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_baseline_missing_or_bad_limit_fails_closed(self):
        report = self._write("report.json", make_report(1, 0))
        good = {"total_errors": 0, "total_warnings": 1, "files_linted": 1}
        for key in ("total_errors", "total_warnings", "files_linted"):
            for bad in (None, "1", -1, True, 1.5):
                payload = dict(good)
                if bad is None:
                    del payload[key]
                else:
                    payload[key] = bad
                result = self._run(
                    "--report", report, "--baseline", self._write("baseline.json", payload)
                )
                with self.subTest(key=key, value=bad):
                    self.assertEqual(result.returncode, 1)
                    self.assertIn(f"no usable {key}", result.stderr)
                    self.assertNotIn("Traceback", result.stderr)

    def test_non_object_baseline_fails_closed(self):
        report = self._write("report.json", make_report(1, 0))
        baseline = self._write("baseline.json", [1, 2])
        result = self._run("--report", report, "--baseline", baseline)
        self.assertEqual(result.returncode, 1)
        self.assertIn("must be a JSON object", result.stderr)

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

    def test_file_floor_passes_at_baseline_count(self):
        report = self._write("report.json", make_report(1, 0, files=5))
        result = self._run("--report", report, "--baseline", self._ceiling(1, 0, files=5))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("ESLint over 5 files (floor 5)", result.stdout)

    def test_one_file_under_floor_fails_even_with_totals_under_ceiling(self):
        # Shedding files sheds their warnings: totals fall and the run looks
        # better while checking less. The floor is what catches that.
        report = self._write("report.json", make_report(0, 0, files=4))
        result = self._run("--report", report, "--baseline", self._ceiling(1, 0, files=5))
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("linted files fell 5 -> 4 (-1)", result.stdout)
        self.assertNotIn("PASS", result.stdout)

    def test_more_files_pass_and_ask_to_raise_the_floor(self):
        report = self._write("report.json", make_report(1, 0, files=6))
        result = self._run("--report", report, "--baseline", self._ceiling(1, 0, files=5))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Linted files rose (5 -> 6)", result.stdout)

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

    def test_write_baseline_caps_warning_rules_and_sum_check_allows_it(self):
        n_rules = mod.WARNINGS_BY_RULE_LIMIT + 2
        report = self._write("report.json", [{
            "filePath": "/packages/client/src/many.ts",
            "messages": [_message(f"rule-{i:02d}", mod.SEV_WARNING, i) for i in range(n_rules)],
        }])
        baseline = os.path.join(self.tmp.name, "written.json")
        result = self._run("--report", report, "--baseline", baseline, "--write-baseline")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        with open(baseline, encoding="utf-8") as fh:
            data = json.load(fh)
        self.assertEqual(len(data["warnings_by_rule"]), mod.WARNINGS_BY_RULE_LIMIT)
        self.assertEqual(data["total_warnings"], n_rules)
        self.assertTrue(rule_sums_match(data))
        data["warnings_by_rule"][next(iter(data["warnings_by_rule"]))] += n_rules
        self.assertFalse(rule_sums_match(data))

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
        self.assertTrue(rule_sums_match(data), data)

    def test_inconsistent_rule_count_sum_fails(self):
        with open(mod.DEFAULT_BASELINE, encoding="utf-8") as fh:
            data = json.load(fh)
        data["warnings_by_rule"] = dict(data["warnings_by_rule"])
        rule = next(iter(data["warnings_by_rule"]))
        data["warnings_by_rule"][rule] += 1
        self.assertFalse(rule_sums_match(data))


REQUIRED_TRIGGER_PATHS = (
    "scripts/ci/client_lint_baseline.json",
    "scripts/ci/check_client_lint_ratchet.py",
)


class WorkflowPathTests(unittest.TestCase):
    def test_baseline_and_ratchet_paths_trigger_lint_build(self):
        with open(WORKFLOW, encoding="utf-8") as fh:
            paths = trigger_paths(fh.read())
        for event in ("pull_request", "push"):
            self.assertIn(event, paths)
            for path in REQUIRED_TRIGGER_PATHS:
                self.assertIn(path, paths[event], f"{path} missing from on.{event}.paths")

    def test_reader_ignores_comments_and_other_sections(self):
        planted = "\n".join([
            "name: x",
            "on:",
            "  pull_request:",
            "    paths:",
            '      - "packages/client/**"',
            '      # - "scripts/ci/client_lint_baseline.json"',
            "  push:",
            "    branches: [main]",
            "    paths:",
            '      - "packages/client/**"  # scripts/ci/check_client_lint_ratchet.py',
            "jobs:",
            "  lint:",
            "    steps:",
            "      - run: python scripts/ci/check_client_lint_ratchet.py",
            "",
        ])
        paths = trigger_paths(planted)
        self.assertEqual(paths, {
            "pull_request": ["packages/client/**"],
            "push": ["packages/client/**"],
        })


if __name__ == "__main__":
    unittest.main()
