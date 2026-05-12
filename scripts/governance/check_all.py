#!/usr/bin/env python3
"""
Unified Governance Check Runner

Runs governance validation scripts with enforcement tier filtering.

Usage:
    python scripts/governance/check_all.py [--mode warn|block] [--tier TIER]

Options:
    --mode warn   Run checks, report issues, but exit 0 (non-blocking)
    --mode block  Run checks, exit 1 on any failure (default)
    --tier TIER   Run only checks at or below this tier:
                    precommit  - fast checks only (~5s total)
                    ci         - precommit + CI checks (~30s total)
                    nightly    - all checks including heavy validation
                    manual     - explicit invocation only (not run by default)
                  Default: ci

Enforcement Tiers:
    precommit     Fast checks suitable for pre-commit hooks (<2s each)
    ci            Checks that run on every CI build (<30s each)
    nightly       Heavy checks that run on nightly/scheduled builds
    manual        Checks requiring explicit invocation

Exit codes:
    0 - All checks pass (or warn mode)
    1 - One or more checks failed (block mode only)

Part of Governance Remediation Infrastructure.
"""

import argparse
import subprocess
import sys
import time
from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path
from typing import List, Optional


class EnforcementTier(IntEnum):
    """
    Governance check enforcement tiers, ordered by runtime cost.

    Lower tiers run faster and are included in higher tier runs.
    """
    PRECOMMIT = 1  # <2s, runs on every commit
    CI = 2         # <30s, runs on every CI build
    NIGHTLY = 3    # >30s, runs on nightly/scheduled builds
    MANUAL = 4     # explicit invocation only


# Repository root
REPO_ROOT = Path(__file__).parent.parent.parent

# Governance checks with enforcement tiers
# Format: (script_path, description, blocking, tier)
GOVERNANCE_CHECKS = [
    # === PRECOMMIT TIER — fast checks, <2s each ===
    ("scripts/check_protected_paths.py", "Protected paths enforcement", True, EnforcementTier.PRECOMMIT),
    ("scripts/check_sprint_namespace.py", "Sprint namespace conventions", False, EnforcementTier.PRECOMMIT),
    ("scripts/check_dxf_compat.py", "DXF compatibility enforcement", True, EnforcementTier.PRECOMMIT),
    ("scripts/governance/check_manifest_index.py", "Manifest index validation", True, EnforcementTier.PRECOMMIT),

    # === CI TIER — moderate checks, <30s each ===
    ("scripts/check_capability_registry.py", "CAM capability registry", True, EnforcementTier.CI),
    ("scripts/check_semantic_leakage.py", "Semantic layer boundaries", False, EnforcementTier.CI),
    ("scripts/governance/check_artifact_linkage_invariants.py", "Artifact linkage invariants", False, EnforcementTier.CI),
    ("scripts/governance/validate_run_artifact_contract.py", "Run artifact contract", False, EnforcementTier.CI),

    # === NIGHTLY TIER — heavy checks requiring full app initialization ===
    ("scripts/governance/check_routing_truth.py", "Routing truth validation", False, EnforcementTier.NIGHTLY),
]


@dataclass
class CheckResult:
    """Result of a governance check."""
    name: str
    script: str
    passed: bool
    blocking: bool
    tier: EnforcementTier
    duration_ms: int
    output: str
    error: str


def run_check(script_path: str, description: str, blocking: bool,
              tier: EnforcementTier) -> CheckResult:
    """
    Run a single governance check script.

    Args:
        script_path: Path to script relative to repo root
        description: Human-readable description
        blocking: Whether failure should block CI

    Returns:
        CheckResult with pass/fail status and output
    """
    full_path = REPO_ROOT / script_path

    # Skip if script doesn't exist
    if not full_path.exists():
        return CheckResult(
            name=description,
            script=script_path,
            passed=True,  # Don't fail for missing optional scripts
            blocking=blocking,
            tier=tier,
            duration_ms=0,
            output="",
            error=f"Script not found: {script_path} (skipped)"
        )

    start_time = time.time()

    try:
        result = subprocess.run(
            [sys.executable, str(full_path)],
            capture_output=True,
            text=True,
            timeout=120,  # 2 minute timeout
            cwd=str(REPO_ROOT)
        )

        duration_ms = int((time.time() - start_time) * 1000)

        return CheckResult(
            name=description,
            script=script_path,
            passed=(result.returncode == 0),
            blocking=blocking,
            tier=tier,
            duration_ms=duration_ms,
            output=result.stdout,
            error=result.stderr if result.returncode != 0 else ""
        )

    except subprocess.TimeoutExpired:
        duration_ms = int((time.time() - start_time) * 1000)
        return CheckResult(
            name=description,
            script=script_path,
            passed=False,
            blocking=blocking,
            tier=tier,
            duration_ms=duration_ms,
            output="",
            error="Script timed out (>120s)"
        )

    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        return CheckResult(
            name=description,
            script=script_path,
            passed=False,
            blocking=blocking,
            tier=tier,
            duration_ms=duration_ms,
            output="",
            error=f"Execution error: {e}"
        )


def print_result(result: CheckResult, verbose: bool = False) -> None:
    """Print a single check result."""
    status = "PASS" if result.passed else ("FAIL" if result.blocking else "WARN")
    blocking_marker = " [blocking]" if result.blocking else ""
    tier_name = result.tier.name.lower()

    print(f"  [{status}] {result.name} ({result.duration_ms}ms){blocking_marker} [{tier_name}]")

    if not result.passed and verbose:
        if result.error:
            for line in result.error.strip().split("\n")[:5]:
                print(f"         {line}")
        if result.output and not result.error:
            for line in result.output.strip().split("\n")[:5]:
                print(f"         {line}")


def main() -> int:
    """
    Run all governance checks.
    """
    parser = argparse.ArgumentParser(description="Unified governance check runner")
    parser.add_argument(
        "--mode",
        choices=["warn", "block"],
        default="block",
        help="warn: report issues but exit 0; block: exit 1 on failures"
    )
    parser.add_argument(
        "--tier",
        choices=["precommit", "ci", "nightly", "manual"],
        default="ci",
        help="Run checks at or below this tier (default: ci)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed output for failures"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available checks and exit"
    )

    args = parser.parse_args()

    # Map tier name to enum
    tier_map = {
        "precommit": EnforcementTier.PRECOMMIT,
        "ci": EnforcementTier.CI,
        "nightly": EnforcementTier.NIGHTLY,
        "manual": EnforcementTier.MANUAL,
    }
    max_tier = tier_map[args.tier]

    if args.list:
        print("Available governance checks:")
        print()
        for tier in EnforcementTier:
            tier_checks = [(s, d, b, t) for s, d, b, t in GOVERNANCE_CHECKS if t == tier]
            if tier_checks:
                print(f"  {tier.name}:")
                for script, desc, blocking, _ in tier_checks:
                    status = "blocking" if blocking else "warn-only"
                    exists = "+" if (REPO_ROOT / script).exists() else "-"
                    print(f"    [{exists}] {desc} ({status})")
                    print(f"        {script}")
                print()
        return 0

    # Filter checks by tier
    active_checks = [(s, d, b, t) for s, d, b, t in GOVERNANCE_CHECKS if t <= max_tier]
    skipped_checks = [(s, d, b, t) for s, d, b, t in GOVERNANCE_CHECKS if t > max_tier]

    print("=" * 60)
    print("UNIFIED GOVERNANCE CHECK")
    print(f"Mode: {args.mode.upper()} | Tier: {args.tier.upper()}")
    if skipped_checks:
        print(f"Skipping {len(skipped_checks)} check(s) above {args.tier} tier")
    print("=" * 60)
    print()

    results: List[CheckResult] = []
    start_time = time.time()

    for script, description, blocking, tier in active_checks:
        result = run_check(script, description, blocking, tier)
        results.append(result)
        print_result(result, verbose=args.verbose)

    total_duration_ms = int((time.time() - start_time) * 1000)

    print()
    print("-" * 60)

    # Summary
    passed = sum(1 for r in results if r.passed)
    failed_blocking = sum(1 for r in results if not r.passed and r.blocking)
    failed_warn = sum(1 for r in results if not r.passed and not r.blocking)
    total = len(results)

    print(f"Results: {passed}/{total} passed")
    if failed_blocking > 0:
        print(f"         {failed_blocking} blocking failure(s)")
    if failed_warn > 0:
        print(f"         {failed_warn} warning(s)")
    print(f"Duration: {total_duration_ms}ms")
    print()

    # Determine exit code
    if args.mode == "warn":
        if failed_blocking > 0:
            print("[WARN] Governance checks have failures (warn mode - not blocking)")
        else:
            print("[OK] Governance checks passed")
        return 0
    else:
        if failed_blocking > 0:
            print("[FAIL] Governance checks failed")
            return 1
        else:
            print("[OK] Governance checks passed")
            return 0


if __name__ == "__main__":
    sys.exit(main())
