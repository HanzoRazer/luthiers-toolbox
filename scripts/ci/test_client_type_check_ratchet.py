#!/usr/bin/env python3
"""Unit tests for check_client_type_check_ratchet.py's log parser.

The defect these pin: CI pipes `npm run type-check` through `tee`, so npm's
`> @production-shop/client@1.0.0 type-check` header comes right before the first
diagnostic. The file pattern used to run across line breaks, so the first error
was filed under a key built from the header text. The total was still right,
but every run reported a phantom per-file delta. On PR #430 that showed up as
`src/api/profiling.ts: 0 -> 1` when profiling.ts had not changed.

The fixtures below are copied from the real lint-build log of PR #430
(run 37291225924), including the npm header and an indented continuation line.

Stdlib-only. Run:
    python scripts/ci/test_client_type_check_ratchet.py
    python -m pytest scripts/ci/test_client_type_check_ratchet.py
"""
from __future__ import annotations

import collections
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import check_client_type_check_ratchet as mod  # noqa: E402

SCRIPT = os.path.join(HERE, "check_client_type_check_ratchet.py")

NPM_HEADER = (
    "\n"
    "> @production-shop/client@1.0.0 type-check\n"
    "> vue-tsc --noEmit\n"
    "\n"
)

DIAGNOSTICS = (
    "src/api/profiling.ts(21,19): error TS2352: Conversion of type 'ImportMeta' to type "
    "'Record<string, unknown>' may be a mistake because neither type sufficiently overlaps "
    "with the other. If this was intentional, convert the expression to 'unknown' first.\n"
    "  Index signature for type 'string' is missing in type 'ImportMeta'.\n"
    "src/api/profiling.ts(21,64): error TS2339: Property 'VITE_API_BASE' does not exist on type '{}'.\n"
    "src/components/cam/neck/CamSpecPanel.vue(23,33): error TS2307: Cannot find module "
    "'@/composables/useCamSpec' or its corresponding type declarations.\n"
    "src/components/cam/neck/CamSpecPanel.vue(24,67): error TS2307: Cannot find module "
    "'@/composables/useCamSpec' or its corresponding type declarations.\n"
    "src/views/cam/headstock/WorkspaceView.vue(17,35): error TS2307: Cannot find module "
    "'@/stores/headstock' or its corresponding type declarations.\n"
)

CI_LOG = NPM_HEADER + DIAGNOSTICS

EXPECTED_BY_FILE = {
    "src/api/profiling.ts": 2,
    "src/components/cam/neck/CamSpecPanel.vue": 2,
    "src/views/cam/headstock/WorkspaceView.vue": 1,
}


def by_file(text: str) -> dict[str, int]:
    return dict(collections.Counter(e["file"] for e in mod.parse_log(text)))


class ParseLogTests(unittest.TestCase):
    def test_npm_header_is_not_part_of_any_file_key(self):
        self.assertEqual(by_file(CI_LOG), EXPECTED_BY_FILE)

    def test_header_does_not_change_attribution(self):
        # The same diagnostics with and without npm's header must parse identically.
        self.assertEqual(by_file(CI_LOG), by_file(DIAGNOSTICS))

    def test_continuation_lines_are_not_diagnostics(self):
        self.assertEqual(len(mod.parse_log(CI_LOG)), 5)

    def test_no_key_spans_lines_or_carries_header_text(self):
        for e in mod.parse_log(CI_LOG):
            self.assertNotIn("\n", e["file"])
            self.assertFalse(e["file"].startswith(">"), e["file"])

    def test_crlf_log_parses_identically(self):
        self.assertEqual(by_file(CI_LOG.replace("\n", "\r\n")), EXPECTED_BY_FILE)

    def test_windows_backslash_paths_normalize_to_posix(self):
        win = NPM_HEADER + DIAGNOSTICS.replace("src/api/", "src\\api\\").replace(
            "src/components/cam/neck/", "src\\components\\cam\\neck\\"
        ).replace("src/views/cam/headstock/", "src\\views\\cam\\headstock\\")
        self.assertEqual(by_file(win.replace("\n", "\r\n")), EXPECTED_BY_FILE)


class RatchetReportTests(unittest.TestCase):
    """End-to-end through the CLI: baseline built from one log, checked against another."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def _write(self, name: str, text: str) -> str:
        path = os.path.join(self.tmp.name, name)
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(text)
        return path

    def _run(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, SCRIPT, *args],
            capture_output=True, text=True, encoding="utf-8",
        )

    def _baseline_from(self, log_text: str) -> str:
        baseline = os.path.join(self.tmp.name, "baseline.json")
        r = self._run("--log", self._write("base.log", log_text), "--baseline", baseline,
                      "--write-baseline")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return baseline

    def test_written_baseline_has_no_header_keys(self):
        baseline = self._baseline_from(CI_LOG)
        with open(baseline, encoding="utf-8") as fh:
            data = json.load(fh)
        self.assertEqual(data["by_file"], EXPECTED_BY_FILE)
        self.assertEqual(data["total_errors"], 5)

    def test_unchanged_diagnostics_pass_with_no_file_movement(self):
        baseline = self._baseline_from(DIAGNOSTICS)
        r = self._run("--log", self._write("ci.log", CI_LOG), "--baseline", baseline)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("PASS", r.stdout)
        self.assertNotIn("->", r.stdout)

    def test_real_regression_is_reported_against_the_right_file_only(self):
        baseline = self._baseline_from(DIAGNOSTICS)
        new_error = (
            "src/views/cam/headstock/WorkspaceView.vue(290,331): error TS2339: "
            "Property 'draw' does not exist on type 'GetSet<number, Layer>'.\n"
        )
        r = self._run("--log", self._write("ci.log", CI_LOG + new_error), "--baseline", baseline)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("rose 5 -> 6 (+1)", r.stdout)
        moved = [ln.strip() for ln in r.stdout.splitlines() if "->" in ln and ": " in ln
                 and not ln.startswith("FAIL")]
        self.assertEqual(moved, ["src/views/cam/headstock/WorkspaceView.vue: 1 -> 2"])

    def test_ceiling_is_not_raised_by_checking(self):
        baseline = self._baseline_from(DIAGNOSTICS)
        with open(baseline, "rb") as fh:
            before = fh.read()
        self._run("--log", self._write("ci.log", CI_LOG + DIAGNOSTICS), "--baseline", baseline)
        with open(baseline, "rb") as fh:
            self.assertEqual(fh.read(), before)


class CommittedBaselineTests(unittest.TestCase):
    def test_committed_baseline_has_no_header_or_multiline_keys(self):
        with open(mod.DEFAULT_BASELINE, encoding="utf-8") as fh:
            data = json.load(fh)
        for key in data["by_file"]:
            self.assertNotIn("\n", key)
            self.assertFalse(key.startswith(">"), key)
            self.assertNotIn("\\", key)
        self.assertEqual(sum(data["by_file"].values()), data["total_errors"])


if __name__ == "__main__":
    unittest.main()
