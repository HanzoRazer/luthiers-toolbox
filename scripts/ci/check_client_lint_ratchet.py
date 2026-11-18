#!/usr/bin/env python3
"""Regression ratchet for ESLint in packages/client.

Why this exists
---------------
`.github/workflows/client_lint_build.yml` ran the lint step with
`continue-on-error: true`, so ESLint findings rode green indefinitely. The
step's own threshold had also stopped meaning anything: `npm run lint` passes
`--max-warnings=1200` while the tree carries several thousand warnings, so the
step failed on warning count alone on every single run. A gate that always
fails is indistinguishable from a gate that never fails -- both get ignored,
and that is precisely why it was made non-gating.

This is the sibling of `check_client_type_check_ratchet.py`: the counts may
fall freely, but they may not rise.

Errors and warnings are ratcheted SEPARATELY, on purpose. Folding them into
one number lets a new error hide behind a handful of removed warnings -- with
thousands of warnings in the tree, a single combined ceiling would be nearly
blind to the thing that actually matters.

Anti-"bless-the-void"
---------------------
A gate that silently passes when its input is missing is worse than no gate.
A missing, empty, malformed, or zero-file report exits non-zero rather than
reporting a clean run. So does a missing or malformed baseline.

Coverage floor
--------------
`files_linted` is a FLOOR. A run that lints fewer files than the baseline
fails: a narrowed glob, a dropped --ext, or a new ignore can shed hundreds of
files, and with them their warnings, so the totals would fall and the ratchet
would pass while checking less. Deleting client files legitimately lowers the
count too; then lower `files_linted` in the same PR, as for any other gain.

Usage
-----
    check_client_lint_ratchet.py --report <eslint.json> [--baseline <path>]
    check_client_lint_ratchet.py --report <eslint.json> --write-baseline
"""

from __future__ import annotations

import argparse
import collections
import json
import pathlib
import sys

SEV_WARNING = 1
SEV_ERROR = 2

DEFAULT_BASELINE = pathlib.Path(__file__).resolve().parent / "client_lint_baseline.json"

# warnings_by_rule keeps only the top N rules. When the tree has more warning
# rules than this, the map no longer sums to total_warnings.
WARNINGS_BY_RULE_LIMIT = 25

BASELINE_LIMITS = ("total_errors", "total_warnings", "files_linted")

BASELINE_COMMENT = (
    "Regression ratchet for ESLint in packages/client. total_errors and total_warnings are "
    "CEILINGS, not targets, and are enforced INDEPENDENTLY so a new error cannot hide behind "
    "removed warnings. Lower them whenever you fix things; never raise one without saying why "
    "in the PR. Regenerate with scripts/ci/check_client_lint_ratchet.py --report <json> "
    "--write-baseline."
)


def load_report(path: pathlib.Path) -> list:
    if not path.exists():
        sys.exit(
            f"FAIL: ESLint report not found at {path}.\n"
            "      The ratchet cannot confirm ESLint ran, so it will not report success."
        )
    raw = path.read_text(encoding="utf-8", errors="replace").strip()
    if not raw:
        sys.exit(
            f"FAIL: ESLint report at {path} is empty.\n"
            "      Refusing to pass on an empty report (a missing run is not a clean run)."
        )
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        sys.exit(f"FAIL: ESLint report at {path} is not valid JSON ({exc}).")
    if not isinstance(data, list):
        sys.exit(f"FAIL: expected a JSON array from ESLint's json formatter, got {type(data).__name__}.")
    if not data:
        sys.exit(
            f"FAIL: ESLint report at {path} lists zero files.\n"
            "      ESLint linted nothing -- refusing to pass. Check the glob and --ext."
        )
    return data


def rel(file_path: str) -> str:
    """Normalise an absolute ESLint path to a stable packages/client-relative POSIX path."""
    p = file_path.replace("\\", "/")
    marker = "/packages/client/"
    if marker in p:
        return p.split(marker, 1)[1]
    return p.rsplit("/", 1)[-1]


def summarise(data: list) -> dict:
    err_by_rule: collections.Counter = collections.Counter()
    warn_by_rule: collections.Counter = collections.Counter()
    err_by_file: collections.Counter = collections.Counter()
    total_e = total_w = 0
    for entry in data:
        for msg in entry.get("messages", []):
            rule = msg.get("ruleId") or "<parse-error>"
            if msg.get("severity") == SEV_ERROR:
                total_e += 1
                err_by_rule[rule] += 1
                err_by_file[rel(entry.get("filePath", "?"))] += 1
            elif msg.get("severity") == SEV_WARNING:
                total_w += 1
                warn_by_rule[rule] += 1
    return {
        "total_errors": total_e,
        "total_warnings": total_w,
        "files_linted": len(data),
        "errors_by_rule": dict(sorted(err_by_rule.items(), key=lambda kv: (-kv[1], kv[0]))),
        "errors_by_file": dict(sorted(err_by_file.items())),
        "warnings_by_rule": dict(
            sorted(warn_by_rule.items(), key=lambda kv: (-kv[1], kv[0]))[:WARNINGS_BY_RULE_LIMIT]
        ),
    }


def load_baseline(path: pathlib.Path) -> dict:
    if not path.exists():
        sys.exit(f"FAIL: baseline not found at {path}")
    try:
        base = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        sys.exit(f"FAIL: baseline at {path} is not valid JSON ({exc}).")
    if not isinstance(base, dict):
        sys.exit(f"FAIL: baseline at {path} must be a JSON object, got {type(base).__name__}.")
    for key in BASELINE_LIMITS:
        value = base.get(key)
        # bool is an int subclass; true/false is not a count.
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            sys.exit(f"FAIL: baseline at {path} has no usable {key} (got {value!r}).")
    return base


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--report", required=True, type=pathlib.Path)
    ap.add_argument("--baseline", type=pathlib.Path, default=DEFAULT_BASELINE)
    ap.add_argument("--write-baseline", action="store_true")
    args = ap.parse_args()

    s = summarise(load_report(args.report))

    if args.write_baseline:
        payload = {"_comment": BASELINE_COMMENT}
        payload.update(s)
        args.baseline.parent.mkdir(parents=True, exist_ok=True)
        args.baseline.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(
            f"Wrote {args.baseline} (errors={s['total_errors']}, "
            f"warnings={s['total_warnings']}, files={s['files_linted']})"
        )
        return 0

    base = load_baseline(args.baseline)
    max_e, max_w = base["total_errors"], base["total_warnings"]
    min_files = base["files_linted"]

    print(f"ESLint over {s['files_linted']} files (floor {min_files})")
    print(f"  errors:   {s['total_errors']:>5}  (ceiling {max_e})")
    print(f"  warnings: {s['total_warnings']:>5}  (ceiling {max_w})")

    failed = False

    if s["total_errors"] > max_e:
        failed = True
        print(f"\nFAIL: errors rose {max_e} -> {s['total_errors']} (+{s['total_errors'] - max_e}).")
        base_by_file = collections.Counter(base.get("errors_by_file", {}))
        worse = [
            (f, c, base_by_file.get(f, 0))
            for f, c in sorted(s["errors_by_file"].items())
            if c > base_by_file.get(f, 0)
        ]
        if worse:
            print("\nFiles above their error baseline:")
            for f, now, was in worse:
                print(f"  {f}: {was} -> {now}")
        base_rules = base.get("errors_by_rule", {})
        new_rules = [
            (r, c) for r, c in s["errors_by_rule"].items() if c > base_rules.get(r, 0)
        ]
        if new_rules:
            print("\nRules above their error baseline:")
            for r, c in new_rules:
                print(f"  {r}: {base_rules.get(r, 0)} -> {c}")

    if s["total_warnings"] > max_w:
        failed = True
        print(f"\nFAIL: warnings rose {max_w} -> {s['total_warnings']} (+{s['total_warnings'] - max_w}).")

    if s["files_linted"] < min_files:
        failed = True
        print(
            f"\nFAIL: linted files fell {min_files} -> {s['files_linted']} "
            f"(-{min_files - s['files_linted']}). ESLint checked less of the tree, so lower totals "
            "prove nothing. If client files were deleted on purpose, lower files_linted in "
            f"{args.baseline.name} in the same PR; otherwise restore the lint file selection."
        )

    if failed:
        print(
            "\nFix the new findings. Do NOT raise a ceiling to make this pass unless the "
            "increase is intentional and explained in the PR."
        )
        return 1

    if s["total_errors"] < max_e or s["total_warnings"] < max_w:
        print(
            f"\nCounts fell (errors {max_e} -> {s['total_errors']}, "
            f"warnings {max_w} -> {s['total_warnings']}). "
            f"Please lower them in {args.baseline.name} to lock the gain in."
        )
    if s["files_linted"] > min_files:
        print(
            f"\nLinted files rose ({min_files} -> {s['files_linted']}). "
            f"Raise files_linted in {args.baseline.name} to lock the coverage in."
        )

    print("\nPASS: lint ratchet holds.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
