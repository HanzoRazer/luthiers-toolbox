#!/usr/bin/env python
"""
CBSP21 Coverage & Audit Logger

Usage:
    python scripts/cbsp21/cbsp21_coverage_with_audit.py \
        --full cbsp21/full_source \
        --scanned cbsp21/scanned_source \
        --threshold 0.95 \
        --log logs/cbsp21_audit.jsonl
"""

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


def total_bytes_in_dir(root: Path) -> int:
    return sum(f.stat().st_size for f in root.rglob("*") if f.is_file())


def compute_bytes(path: Path) -> int:
    if path.is_file():
        return path.stat().st_size
    if path.is_dir():
        return total_bytes_in_dir(path)
    raise ValueError(f"Path not found: {path}")


def audit_record(
    *,
    full: Path,
    scanned: Path,
    full_bytes: int,
    scanned_bytes: int,
    coverage: float,
    threshold: float,
    status: str,
) -> Dict[str, Any]:
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "policy": "CBSP21",
        "full_path": str(full),
        "scanned_path": str(scanned),
        "full_bytes": full_bytes,
        "scanned_bytes": scanned_bytes,
        "coverage_ratio": coverage,
        "coverage_percent": round(coverage * 100, 2),
        "threshold": threshold,
        "status": status,  # "pass" | "fail"
        # Optional CI metadata (GitHub Actions)
        "ci": {
            "github_run_id": os.getenv("GITHUB_RUN_ID"),
            "github_sha": os.getenv("GITHUB_SHA"),
            "github_ref": os.getenv("GITHUB_REF"),
            "github_actor": os.getenv("GITHUB_ACTOR"),
            "github_repo": os.getenv("GITHUB_REPOSITORY"),
        },
    }


def append_jsonl(path: Path, rec: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", required=True)
    ap.add_argument("--scanned", required=True)
    ap.add_argument("--threshold", type=float, default=0.95)
    ap.add_argument("--log", required=True)
    args = ap.parse_args()

    full = Path(args.full)
    scanned = Path(args.scanned)
    log = Path(args.log)

    if not full.exists():
        print(f"CBSP21 FAIL: full path missing: {full}")
        rec = audit_record(full=full, scanned=scanned, full_bytes=0, scanned_bytes=0,
                           coverage=0.0, threshold=args.threshold, status="fail")
        append_jsonl(log, rec)
        return 1

    if not scanned.exists():
        print(f"CBSP21 FAIL: scanned path missing: {scanned}")
        rec = audit_record(full=full, scanned=scanned, full_bytes=compute_bytes(full), scanned_bytes=0,
                           coverage=0.0, threshold=args.threshold, status="fail")
        append_jsonl(log, rec)
        return 1

    # Guard: mismatch
    if full.is_file() != scanned.is_file():
        print("CBSP21 FAIL: full and scanned must both be files or both be directories.")
        rec = audit_record(full=full, scanned=scanned, full_bytes=compute_bytes(full), scanned_bytes=compute_bytes(scanned),
                           coverage=0.0, threshold=args.threshold, status="fail")
        append_jsonl(log, rec)
        return 1

    full_bytes = compute_bytes(full)
    scanned_bytes = compute_bytes(scanned)

    if not full_bytes:
        print("CBSP21 FAIL: full source empty.")
        rec = audit_record(full=full, scanned=scanned, full_bytes=0, scanned_bytes=scanned_bytes,
                           coverage=0.0, threshold=args.threshold, status="fail")
        append_jsonl(log, rec)
        return 1

    coverage = scanned_bytes / full_bytes
    percent = coverage * 100

    print(f"CBSP21 Coverage: {percent:.2f}% (threshold {args.threshold * 100:.2f}%)")

    status = "pass" if coverage >= args.threshold else "fail"
    rec = audit_record(
        full=full,
        scanned=scanned,
        full_bytes=full_bytes,
        scanned_bytes=scanned_bytes,
        coverage=coverage,
        threshold=args.threshold,
        status=status,
    )
    append_jsonl(log, rec)

    if status == "fail":
        print("CBSP21 FAIL: Coverage below policy threshold. Output prohibited.")
        return 1

    print("CBSP21 PASS: Coverage requirement satisfied.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
