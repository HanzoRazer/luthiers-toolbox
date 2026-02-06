#!/usr/bin/env python
"""
CBSP21 Patch Packet Format Rule

Validates that patch packets are structured and safe to scan:
- Must include at least one line starting with "FILE: "
- Code fences (```) must be balanced
- Optional: disallow "..." placeholder inside code fences (common truncation)

Usage:
    python scripts/cbsp21/check_patch_packet_format.py --glob "cbsp21/patch_packets/**/*.*"
"""

import argparse
import glob
from pathlib import Path


def balanced_fences(text: str) -> bool:
    return text.count("```") % 2 == 0


def has_file_headers(text: str) -> bool:
    return any(line.startswith("FILE: ") for line in text.splitlines())


def has_ellipsis_inside_code_fence(text: str) -> bool:
    in_fence = False
    for line in text.splitlines():
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence and line.strip() == "...":
            return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--glob", required=True, help="Glob of packet files to validate.")
    ap.add_argument("--disallow-ellipsis-in-code", action="store_true")
    args = ap.parse_args()

    files = [Path(p) for p in glob.glob(args.glob, recursive=True)]
    files = [p for p in files if p.is_file()]

    if not files:
        print("CBSP21 Patch Packet: no files matched; skipping.")
        return 0

    failed = False

    for path in files:
        txt = path.read_text(encoding="utf-8", errors="ignore")

        if not has_file_headers(txt):
            print(f"CBSP21 PATCH FAIL: Missing FILE headers in {path}")
            failed = True

        if not balanced_fences(txt):
            print(f"CBSP21 PATCH FAIL: Unbalanced ``` fences in {path}")
            failed = True

        if args.disallow_ellipsis_in_code and has_ellipsis_inside_code_fence(txt):
            print(f"CBSP21 PATCH FAIL: Found '...' placeholder inside code fence in {path}")
            failed = True

    if failed:
        return 1

    print("CBSP21 Patch Packet: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
