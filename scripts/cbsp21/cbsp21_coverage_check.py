#!/usr/bin/env python
"""
CBSP21 Coverage Check

Calculates how much of the original content has been scanned/captured
and enforces a minimum coverage threshold (default: 95%).

- If both paths are files -> compare file sizes.
- If both paths are directories -> compare total bytes of all files.
- If one is a file and the other is a directory -> fail with an error.

Usage examples:

    # Directories
    python scripts/cbsp21/cbsp21_coverage_check.py \
        --full-path cbsp21/full_source \
        --scanned-path cbsp21/scanned_source \
        --threshold 0.95
"""

import argparse
from pathlib import Path


def total_bytes_in_dir(root: Path) -> int:
    """Sum bytes of all regular files under a directory (recursive)."""
    return sum(
        f.stat().st_size
        for f in root.rglob("*")
        if f.is_file()
    )


def compute_bytes(path: Path) -> int:
    """Return total bytes for a file or a directory."""
    if path.is_file():
        return path.stat().st_size
    if path.is_dir():
        return total_bytes_in_dir(path)
    raise ValueError(f"Path not found: {path}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--full-path", required=True)
    ap.add_argument("--scanned-path", required=True)
    ap.add_argument("--threshold", type=float, default=0.95)
    args = ap.parse_args()

    full = Path(args.full_path)
    scanned = Path(args.scanned_path)

    if not full.exists():
        raise SystemExit(f"Full path does not exist: {full}")
    if not scanned.exists():
        raise SystemExit(f"Scanned path does not exist: {scanned}")

    # Guard: file vs dir mismatch
    if full.is_file() != scanned.is_file():
        raise SystemExit("CBSP21 ERROR: full-path and scanned-path must both be files or both be directories.")

    full_bytes = compute_bytes(full)
    scanned_bytes = compute_bytes(scanned)

    if not full_bytes:
        raise SystemExit("CBSP21 ERROR: full source appears empty - cannot compute coverage.")

    coverage = scanned_bytes / full_bytes
    percent = coverage * 100

    print(f"CBSP21 Coverage: {percent:.2f}%")
    print(f"  full_bytes   = {full_bytes}")
    print(f"  scanned_bytes= {scanned_bytes}")
    print(f"  threshold    = {args.threshold * 100:.2f}%")

    if coverage < args.threshold:
        print("CBSP21 FAIL: Coverage below policy threshold. Output prohibited.")
        return 1

    print("CBSP21 PASS: Coverage requirement satisfied.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
