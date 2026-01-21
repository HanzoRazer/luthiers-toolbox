from __future__ import annotations

"""
Boundary Pattern Checker (ToolBox API) — Fence-Aware Edition
-------------------------------------------------------------

Purpose:
  Enforce pattern-based architectural boundaries defined in FENCE_REGISTRY.json.
  Implements 3 pattern-based fences:
    3. operation_lane_boundary - Operation lane isolation
    6. frontend_sdk_boundary   - Frontend SDK contract enforcement
    8. legacy_deprecation      - Legacy API deprecation tracking

Usage:
  cd services/api
  python -m app.ci.check_boundary_patterns
  python -m app.ci.check_boundary_patterns --write-baseline app/ci/fence_patterns_baseline.json
  python -m app.ci.check_boundary_patterns --baseline app/ci/fence_patterns_baseline.json

Exit codes:
  0 = ok
  2 = violations found
  3 = configuration / runtime error

Baseline mode:
  --write-baseline: captures current violations to JSON and exits 0
  --baseline: fails only on NEW violations compared to the baseline
  (This is the recommended posture for brownfield enforcement.)
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple


# --- Configuration: Pattern Definitions ------------------------------------

# Files to skip (generated, vendored, etc.)
SKIP_FILE_PATTERNS: Tuple[str, ...] = (
    "*/__pycache__/*",
    "*/.venv/*",
    "*/site-packages/*",
    "*/tests/*",
)


# --- Fence 3: operation_lane_boundary --------------------------------------
# Pattern-based check for OPERATION lane isolation

OPERATION_LANE_PATHS: Tuple[str, ...] = (
    "app/saw_lab",
)

OPERATION_LANE_FORBIDDEN_PATTERNS: List[Tuple[str, str]] = [
    # (regex, reason)
    (r"from app\.workflow", "OPERATION lane must not import workflow orchestration"),
    (r"import app\.workflow", "OPERATION lane must not import workflow orchestration"),
]


# --- Fence 6: frontend_sdk_boundary ----------------------------------------
# Pattern-based check for frontend SDK contract

FRONTEND_SDK_PATHS: Tuple[str, ...] = (
    "../../packages/client/src",  # Relative to services/api
)

FRONTEND_SDK_FORBIDDEN_PATTERNS: List[Tuple[str, str]] = [
    # (regex, reason)
    (r"/api/rmos/runs\b", "Frontend must use runs_v2 endpoints, not legacy runs"),
    (r"fetchRun\(", "Use fetchRunV2() instead of deprecated fetchRun()"),
]


# --- Fence 8: legacy_deprecation -------------------------------------------
# Track usage of deprecated APIs

LEGACY_SCAN_PATHS: Tuple[str, ...] = (
    "app/routers",
    "app/services",
)

LEGACY_DEPRECATED_PATTERNS: List[Tuple[str, str]] = [
    # (regex, reason)
    (r"from app\.rmos\.runs import", "Use app.rmos.runs_v2 instead of legacy runs"),
    (r"from app\.rmos\.runs\.store import", "Use app.rmos.runs_v2.store instead"),
]

# Budget for legacy deprecation (fail if exceeded)
LEGACY_BUDGET_MAX = 50


# --- Data structures -------------------------------------------------------

@dataclass(frozen=True)
class PatternViolation:
    """Single pattern-based violation."""
    fence: str
    file: Path
    line: int
    pattern: str
    excerpt: str
    reason: str


# --- Helpers ---------------------------------------------------------------

def _repo_root_from_cwd() -> Path:
    """
    Expected execution: services/api as cwd, with app/ present.
    If not, we still try to locate an 'app' directory upward.
    """
    cwd = Path.cwd().resolve()
    for p in [cwd] + list(cwd.parents):
        if (p / "app").is_dir():
            return p
    raise RuntimeError("Could not locate services/api root (missing app/). Run from services/api.")


def _relpath(path: Path) -> str:
    """Convert path to stable relative string for baseline keys."""
    root = _repo_root_from_cwd()
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except Exception:
        return str(path).replace("\\", "/")


def _match_skip(path: Path) -> bool:
    s = str(path).replace("\\", "/")
    for pat in SKIP_FILE_PATTERNS:
        if pat.strip("*") in s:
            return True
    return False


def _iter_python_files(base_dir: Path) -> List[Path]:
    """Iterate Python files in directory, skipping ignored patterns."""
    files = []
    if not base_dir.exists():
        return files
    for p in base_dir.rglob("*.py"):
        if _match_skip(p):
            continue
        files.append(p)
    return files


def _scan_file_for_patterns(
    py_file: Path,
    patterns: List[Tuple[str, str]],
    fence: str,
) -> List[PatternViolation]:
    """Scan a single file for pattern violations."""
    violations = []
    try:
        content = py_file.read_text(encoding="utf-8", errors="ignore")
        lines = content.splitlines()

        for i, line in enumerate(lines, 1):
            for regex, reason in patterns:
                if re.search(regex, line):
                    violations.append(PatternViolation(
                        fence=fence,
                        file=py_file,
                        line=i,
                        pattern=regex,
                        excerpt=line.strip()[:80],
                        reason=reason,
                    ))
    except Exception:
        pass
    return violations


# --- Fence Scanners --------------------------------------------------------

def scan_operation_lane_boundary(repo_root: Path) -> List[PatternViolation]:
    """Fence 3: Check OPERATION lane isolation patterns."""
    violations = []

    for path_prefix in OPERATION_LANE_PATHS:
        scan_dir = repo_root / path_prefix
        for py_file in _iter_python_files(scan_dir):
            violations.extend(_scan_file_for_patterns(
                py_file,
                OPERATION_LANE_FORBIDDEN_PATTERNS,
                "operation_lane_boundary",
            ))

    return violations


def scan_frontend_sdk_boundary(repo_root: Path) -> List[PatternViolation]:
    """Fence 6: Check frontend SDK contract patterns."""
    violations = []

    for path_prefix in FRONTEND_SDK_PATHS:
        scan_dir = repo_root / path_prefix
        if not scan_dir.exists():
            continue

        # Scan TypeScript/JavaScript files for frontend
        for ext in ("*.ts", "*.tsx", "*.js", "*.jsx", "*.vue"):
            for f in scan_dir.rglob(ext):
                if _match_skip(f):
                    continue
                try:
                    content = f.read_text(encoding="utf-8", errors="ignore")
                    lines = content.splitlines()

                    for i, line in enumerate(lines, 1):
                        for regex, reason in FRONTEND_SDK_FORBIDDEN_PATTERNS:
                            if re.search(regex, line):
                                violations.append(PatternViolation(
                                    fence="frontend_sdk_boundary",
                                    file=f,
                                    line=i,
                                    pattern=regex,
                                    excerpt=line.strip()[:80],
                                    reason=reason,
                                ))
                except Exception:
                    pass

    return violations


def scan_legacy_deprecation(repo_root: Path) -> Tuple[List[PatternViolation], int]:
    """Fence 8: Track legacy API deprecation usage.

    Returns:
        Tuple of (violations, total_count)
    """
    violations = []

    for path_prefix in LEGACY_SCAN_PATHS:
        scan_dir = repo_root / path_prefix
        for py_file in _iter_python_files(scan_dir):
            violations.extend(_scan_file_for_patterns(
                py_file,
                LEGACY_DEPRECATED_PATTERNS,
                "legacy_deprecation",
            ))

    return violations, len(violations)


# --- Baseline Support ------------------------------------------------------

def _violation_key(v: PatternViolation) -> str:
    """Stable key for pattern violation."""
    return f"{v.fence}|{_relpath(v.file)}|{v.line}|{v.pattern}|{v.reason}"


def _serialize(violations: List[PatternViolation]) -> dict:
    """Serialize violations to baseline format."""
    return {
        "version": 1,
        "patterns": sorted({_violation_key(v) for v in violations}),
    }


def _load_baseline(path: Path) -> dict:
    """Load baseline JSON file."""
    obj = json.loads(path.read_text(encoding="utf-8"))
    if obj.get("version") != 1:
        raise RuntimeError(f"Unsupported baseline format: {path}")
    obj.setdefault("patterns", [])
    return obj


# --- Reporting -------------------------------------------------------------

def _print_report(violations: List[PatternViolation], legacy_count: int) -> None:
    """Print violation report."""
    print("\n" + "=" * 60)
    print("BOUNDARY PATTERN VIOLATIONS")
    print("=" * 60 + "\n")

    if violations:
        for v in violations:
            rel = _relpath(v.file)
            print(f"  {rel}:{v.line}")
            print(f"    fence:   {v.fence}")
            print(f"    pattern: {v.pattern}")
            print(f"    excerpt: {v.excerpt}")
            print(f"    reason:  {v.reason}")
            print()

    print("-" * 60)
    print(f"Total violations: {len(violations)}")
    if legacy_count > 0:
        print(f"Legacy deprecation count: {legacy_count} (budget: {LEGACY_BUDGET_MAX})")
    print("-" * 60)

    print("\nEnforced fences (pattern-based):")
    print("  3. operation_lane_boundary - OPERATION lane isolation")
    print("  6. frontend_sdk_boundary   - Frontend SDK contract")
    print("  8. legacy_deprecation      - Legacy API tracking")
    print()


# --- CLI -------------------------------------------------------------------

def _parse_args(argv: List[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="python -m app.ci.check_boundary_patterns",
        description="Pattern-based boundary checker for ToolBox API",
    )
    p.add_argument(
        "--baseline",
        type=str,
        default=None,
        help="Path to baseline JSON. If provided, fail only on NEW violations vs baseline.",
    )
    p.add_argument(
        "--write-baseline",
        type=str,
        default=None,
        help="Write current violations to baseline JSON and exit 0.",
    )
    return p.parse_args(argv)


def main() -> int:
    try:
        args = _parse_args(sys.argv[1:])
        repo_root = _repo_root_from_cwd()
    except Exception as e:
        print(f"Pattern scanner error: {e}", file=sys.stderr)
        return 3

    # Run all pattern scans
    violations: List[PatternViolation] = []
    violations.extend(scan_operation_lane_boundary(repo_root))
    violations.extend(scan_frontend_sdk_boundary(repo_root))
    legacy_vs, legacy_count = scan_legacy_deprecation(repo_root)
    violations.extend(legacy_vs)

    current = _serialize(violations)

    # Write-baseline mode (always exit 0)
    if args.write_baseline:
        path = Path(args.write_baseline)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(current, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"Wrote pattern baseline: {path}")
        print(f"  patterns: {len(current['patterns'])}")
        return 0

    # Baseline compare mode (fail only on NEW)
    if args.baseline:
        bpath = Path(args.baseline)
        if not bpath.exists():
            print(f"Baseline not found: {bpath}", file=sys.stderr)
            print("Tip: generate it with --write-baseline <path>", file=sys.stderr)
            return 3

        try:
            baseline = _load_baseline(bpath)
        except Exception as e:
            print(f"Failed to read baseline {bpath}: {e}", file=sys.stderr)
            return 3

        b = set(baseline.get("patterns", []))
        c = set(current.get("patterns", []))

        new = c - b
        resolved = b - c

        if new:
            print("\n" + "=" * 60)
            print("NEW PATTERN VIOLATIONS (since baseline)")
            print("=" * 60 + "\n")
            for s in sorted(new)[:200]:
                print(f"  - {s}")
            if len(new) > 200:
                print(f"  ... ({len(new) - 200} more)")
            print()
            return 2

        print("Boundary pattern check: OK (baseline mode)")
        if resolved:
            print(f"  resolved since baseline: {len(resolved)}")
        return 0

    # Default strict mode
    budget_violation = legacy_count > LEGACY_BUDGET_MAX

    if violations or budget_violation:
        _print_report(violations, legacy_count)
        if budget_violation:
            print(f"ERROR: Legacy deprecation budget exceeded ({legacy_count} > {LEGACY_BUDGET_MAX})")
        return 2

    print("Boundary pattern check: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
