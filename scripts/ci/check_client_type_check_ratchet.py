#!/usr/bin/env python3
"""Regression ratchet for `vue-tsc --noEmit` in packages/client.

Why this exists
---------------
`.github/workflows/client_lint_build.yml` ran the type-check step with
`continue-on-error: true` and a standing TODO to remove it once the
pre-existing errors were fixed. Until then the step could never fail, so
`vue-tsc` reported errors into a log nobody gated on -- a decorative gate.
PR #290 (typescript 5.9.3 -> 6.0.3) made the cost visible: a reviewer read
those masked errors as evidence the bump had broken type-checking, when the
identical 150 errors were already present on `main` under 5.9.3.

Fixing all 150 at once is not in scope for a dependency PR. This ratchet is
the intermediate step the repo already uses elsewhere (`ci/file_size_baseline.json`,
`ci/router_count_baseline.json`): the count may fall freely, but it may not
rise. A PR that adds a type error now fails; a PR that fixes one is asked to
lower the baseline.

Anti-"bless-the-void"
---------------------
A gate that silently passes when its input is missing is worse than no gate.
If the log is absent, empty, or shows no sign that `vue-tsc` actually ran,
this exits non-zero rather than reporting success on an empty error set.

Usage
-----
    check_client_type_check_ratchet.py --log <vue-tsc.log> [--baseline <path>]
    check_client_type_check_ratchet.py --log <vue-tsc.log> --write-baseline
"""

from __future__ import annotations

import argparse
import collections
import json
import pathlib
import re
import sys

# `src/views/x.vue(12,5): error TS2345: ...`
ERROR_RE = re.compile(
    r"^(?P<file>[^\s(][^(]*?)\((?P<line>\d+),(?P<col>\d+)\): error (?P<code>TS\d+)",
    re.MULTILINE,
)
# vue-tsc / tsc summary line, used as proof the tool actually executed.
SUMMARY_RE = re.compile(r"Found \d+ errors?|error TS\d+|\bversion\b", re.IGNORECASE)

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
# NB: deliberately NOT in ci/ -- .gitignore has "/ci/" (only ci/rmos/ is
# negated), so files added there are silently untracked. The baselines that
# do live in ci/ predate that rule and survive only because git ignores do
# not apply to already-tracked files.
DEFAULT_BASELINE = pathlib.Path(__file__).resolve().parent / "client_type_check_baseline.json"

BASELINE_COMMENT = (
    "Regression ratchet for `vue-tsc --noEmit` in packages/client. total_errors is a "
    "CEILING, not a target: CI fails when the count rises above it. Lower it whenever "
    "you fix errors; never raise it without saying why in the PR. Regenerate with "
    "scripts/ci/check_client_type_check_ratchet.py --log <log> --write-baseline."
)


def parse_log(text: str) -> list[dict]:
    return [
        {
            "file": m.group("file").replace("\\", "/").strip(),
            "code": m.group("code"),
        }
        for m in ERROR_RE.finditer(text)
    ]


def load_log(path: pathlib.Path) -> str:
    if not path.exists():
        sys.exit(
            f"FAIL: type-check log not found at {path}.\n"
            "      The ratchet cannot confirm vue-tsc ran, so it will not report success."
        )
    text = path.read_text(encoding="utf-8", errors="replace")
    if not text.strip():
        sys.exit(
            f"FAIL: type-check log at {path} is empty.\n"
            "      Refusing to pass on an empty error set (a missing log is not a clean run)."
        )
    if not SUMMARY_RE.search(text):
        sys.exit(
            f"FAIL: {path} contains no recognizable vue-tsc output.\n"
            "      Refusing to pass -- the type-check step likely did not run.\n"
            f"      First 200 chars: {text[:200]!r}"
        )
    return text


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--log", required=True, type=pathlib.Path)
    ap.add_argument("--baseline", type=pathlib.Path, default=DEFAULT_BASELINE)
    ap.add_argument("--write-baseline", action="store_true")
    args = ap.parse_args()

    errors = parse_log(load_log(args.log))
    by_file = collections.Counter(e["file"] for e in errors)
    by_code = collections.Counter(e["code"] for e in errors)
    total = len(errors)

    if args.write_baseline:
        payload = {
            "_comment": BASELINE_COMMENT,
            "total_errors": total,
            "by_code": dict(sorted(by_code.items(), key=lambda kv: (-kv[1], kv[0]))),
            "by_file": dict(sorted(by_file.items())),
        }
        args.baseline.parent.mkdir(parents=True, exist_ok=True)
        args.baseline.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {args.baseline} (total_errors={total}, files={len(by_file)})")
        return 0

    if not args.baseline.exists():
        sys.exit(f"FAIL: baseline not found at {args.baseline}")
    baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
    allowed = int(baseline["total_errors"])

    print(f"vue-tsc errors: {total} | baseline ceiling: {allowed}")

    if total > allowed:
        print(f"\nFAIL: type errors rose {allowed} -> {total} (+{total - allowed}).")
        base_by_file = collections.Counter(baseline.get("by_file", {}))
        worse = [
            (f, c, base_by_file.get(f, 0))
            for f, c in sorted(by_file.items())
            if c > base_by_file.get(f, 0)
        ]
        if worse:
            print("\nFiles above their baseline:")
            for f, now, was in worse:
                print(f"  {f}: {was} -> {now}")
        print(
            "\nFix the new errors. Do NOT raise the baseline to make this pass "
            "unless the increase is intentional and explained in the PR."
        )
        return 1

    if total < allowed:
        print(
            f"\nType errors fell {allowed} -> {total} ({allowed - total} fixed). "
            f"Please lower total_errors in {args.baseline.name} to lock the gain in."
        )

    print("\nPASS: type-check ratchet holds.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
