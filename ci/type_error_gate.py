#!/usr/bin/env python3
"""CI gate: ratchet the client TypeScript type-error count (BR-021).

The `packages/client` type-check lane (`vue-tsc --noEmit`) historically ran under
`continue-on-error: true` to tolerate a pile of pre-existing type errors. That made
the lane a HOLLOW GUARANTEE: the step ran, reported errors, and the check went green
anyway - so a type regression (e.g. a TypeScript major-version bump turning 400 errors
into 4,000) sailed through green. This gate replaces that with a ratchet: the known
debt is frozen as a baseline ceiling, and the check FAILS on any INCREASE above it, so
the guard can fail again on exactly what it should catch.

This is deliberately COUNT-BASED, not signature-based: a message/error-code allowlist
would be invalidated by the very toolchain bump it guards against (tsc changes error
text/codes across majors), so it would go stale exactly when it matters. A raw count
survives the migration and still catches a catastrophic regression.

Usage:
    python ci/type_error_gate.py --report tsc_output.txt   # enforce against baseline
    python ci/type_error_gate.py                           # run vue-tsc itself, then enforce
    python ci/type_error_gate.py --report out.txt --update # regenerate the baseline
    python ci/type_error_gate.py --report out.txt --strict # require exact parity (no debt slack)

Exit codes:
    0 - count <= baseline (within the frozen ceiling)   [or --update succeeded]
    1 - count  > baseline (a regression - the guard fires)
    2 - script/measurement error
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BASELINE_FILE = Path(__file__).parent / "type_error_baseline.json"
CLIENT_DIR = REPO_ROOT / "packages" / "client"

# vue-tsc emits one line per error:  path(line,col): error TS####: message
ERROR_LINE = re.compile(r"error TS\d+", re.IGNORECASE)


def count_errors_in_text(text: str) -> int:
    """Count vue-tsc error lines. Robust to the summary 'Found N errors.' line, which
    is cross-checked when present but not used as the primary count."""
    per_line = len(ERROR_LINE.findall(text))
    m = re.search(r"Found (\d+) error", text)
    if m:
        summary = int(m.group(1))
        # Trust the explicit summary when it disagrees only slightly (multiline
        # diagnostics can span >1 line); prefer the larger to avoid under-counting.
        return max(per_line, summary)
    return per_line


def run_vue_tsc() -> str:
    """Run vue-tsc --noEmit in packages/client and return its combined output.
    vue-tsc exits non-zero when errors exist; that is expected and captured."""
    if not (CLIENT_DIR / "node_modules" / ".bin").exists():
        print("ERROR: packages/client dependencies not installed (run npm ci first).",
              file=sys.stderr)
        sys.exit(2)
    proc = subprocess.run(
        ["npm", "run", "type-check"],
        cwd=str(CLIENT_DIR), capture_output=True, text=True, shell=False,
    )
    return proc.stdout + proc.stderr


def load_baseline() -> dict:
    if not BASELINE_FILE.exists():
        return {}
    try:
        return json.loads(BASELINE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"ERROR: cannot read baseline {BASELINE_FILE}: {e}", file=sys.stderr)
        sys.exit(2)


def write_baseline(count: int) -> None:
    data = load_baseline()
    data.update({
        "schema": "type_error_baseline_v1",
        "tool": "vue-tsc --noEmit",
        "scope": "packages/client",
        "max_errors": count,
    })
    data.setdefault(
        "_comment",
        "BR-021 type-error ratchet. Ceiling for `vue-tsc --noEmit` errors in "
        "packages/client; the gate FAILS when the count EXCEEDS max_errors. Ratchet "
        "DOWN as debt is fixed (rerun --update); never raise without justification.",
    )
    BASELINE_FILE.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"[OK] baseline updated: max_errors = {count}  ({BASELINE_FILE.name})")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Client type-error ratchet gate (BR-021)")
    ap.add_argument("--report", type=Path,
                    help="path to captured vue-tsc output; if omitted, runs vue-tsc")
    ap.add_argument("--update", action="store_true", help="regenerate the baseline")
    ap.add_argument("--strict", action="store_true",
                    help="require exact parity with baseline (no debt slack)")
    args = ap.parse_args(argv)

    if args.report:
        try:
            text = args.report.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            print(f"ERROR: cannot read report {args.report}: {e}", file=sys.stderr)
            return 2
    else:
        text = run_vue_tsc()

    count = count_errors_in_text(text)

    if args.update:
        write_baseline(count)
        return 0

    baseline = load_baseline()
    ceiling = baseline.get("max_errors")
    if ceiling is None:
        print("ERROR: baseline has no max_errors; seed it with --update first.",
              file=sys.stderr)
        return 2

    print("=" * 60)
    print(f"Client type-error ratchet (BR-021)")
    print(f"  tool:     vue-tsc --noEmit  (packages/client)")
    print(f"  observed: {count}")
    print(f"  baseline: {ceiling}")
    print("=" * 60)

    if args.strict:
        ok = count == ceiling
        rule = "exact parity required (--strict)"
    else:
        ok = count <= ceiling
        rule = "count must not exceed baseline"

    if ok:
        if count < ceiling:
            print(f"[OK] {count} <= {ceiling}. Debt reduced by {ceiling - count} - "
                  f"consider ratcheting the baseline down (--update).")
        else:
            print(f"[OK] {count} == baseline. {rule}.")
        return 0

    print(f"[FAIL] type-error count INCREASED: {count} > baseline {ceiling} "
          f"(+{count - ceiling}). {rule}.")
    print("       A change added new type errors. This lane can fail again (BR-021):")
    print("       fix the new errors, or - if intentional and justified - regenerate")
    print("       the baseline with: python ci/type_error_gate.py --report <out> --update")
    return 1


if __name__ == "__main__":
    sys.exit(main())
