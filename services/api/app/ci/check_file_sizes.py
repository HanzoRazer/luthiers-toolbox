#!/usr/bin/env python3
"""
File Size Gate

Fails if any Python file exceeds line count threshold.
Default threshold: 500 lines (can be overridden via --threshold)

Usage:
    python -m app.ci.check_file_sizes [--threshold N] [--baseline FILE]

Exit codes:
    0 = OK (no violations or all in baseline)
    1 = violations found
    2 = runtime error
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List


def _repo_root() -> Path:
    """Find repo root by looking for .git or pyproject.toml."""
    p = Path(__file__).resolve()
    for parent in [p] + list(p.parents):
        if (parent / ".git").exists() or (parent / "pyproject.toml").exists():
            return parent
    return Path.cwd()


def _find_python_files(root: Path) -> List[Path]:
    """Find all Python files under root, excluding venv/cache."""
    files = []
    for pyfile in root.rglob("*.py"):
        rel = str(pyfile.relative_to(root))
        if any(skip in rel for skip in [
            "venv", "__pycache__", ".git", "node_modules",
            "site-packages", ".eggs", "build", "dist"
        ]):
            continue
        files.append(pyfile)
    return files


def check_file_sizes(
    root: Path,
    threshold: int = 500,
    baseline: Dict[str, Any] | None = None,
) -> List[Dict[str, Any]]:
    """
    Check all Python files for exceeding line count threshold.

    Returns list of violations (empty if OK).
    """
    violations = []
    baseline_set = set()

    if baseline:
        for v in baseline.get("violations", []):
            baseline_set.add(v["file"])

    for pyfile in _find_python_files(root):
        try:
            lines = pyfile.read_text(encoding="utf-8").splitlines()
            line_count = len(lines)

            if line_count > threshold:
                rel_path = str(pyfile.relative_to(root))

                if rel_path in baseline_set:
                    continue  # Skip baselined violations

                violations.append({
                    "file": rel_path,
                    "lines": line_count,
                    "over_by": line_count - threshold,
                })
        except (OSError, UnicodeDecodeError):
            pass  # Skip files that can't be read

    # Sort by line count (largest first)
    violations.sort(key=lambda x: -x["lines"])
    return violations


def main():
    parser = argparse.ArgumentParser(description="Check file sizes")
    parser.add_argument("--threshold", type=int, default=500, help="Max allowed lines")
    parser.add_argument("--baseline", type=str, help="Baseline JSON file (ratchet mode)")
    parser.add_argument("--write-baseline", action="store_true", help="Write current violations to baseline")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    root = _repo_root()
    app_root = root / "services" / "api" / "app"

    if not app_root.exists():
        app_root = root / "app"
    if not app_root.exists():
        print(f"ERROR: Cannot find app directory from {root}")
        sys.exit(2)

    baseline = None
    if args.baseline and Path(args.baseline).exists():
        baseline = json.loads(Path(args.baseline).read_text())

    violations = check_file_sizes(app_root.parent, args.threshold, baseline)

    if args.write_baseline:
        baseline_data = {
            "threshold": args.threshold,
            "violation_count": len(violations),
            "violations": violations,
        }
        out_path = Path(args.baseline) if args.baseline else Path("file_sizes_baseline.json")
        out_path.write_text(json.dumps(baseline_data, indent=2))
        print(f"Wrote {len(violations)} violations to {out_path}")
        return 0

    if args.json:
        print(json.dumps(violations, indent=2))
    else:
        if violations:
            print(f"FILE SIZE VIOLATIONS (threshold={args.threshold} lines):")
            print("=" * 60)
            for v in violations[:25]:
                print(f"  {v['lines']:4d} lines (+{v['over_by']:3d})  {v['file']}")
            if len(violations) > 25:
                print(f"  ... and {len(violations) - 25} more")
            print()
            print(f"Total: {len(violations)} files exceed {args.threshold} lines")
        else:
            print(f"OK: No files exceed {args.threshold} lines")

    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
