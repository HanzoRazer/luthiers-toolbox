#!/usr/bin/env python3
"""
Unified Governance Check Runner

Runs governance validation scripts with enforcement tier filtering and optional
policy-driven configuration.

Usage:
    python scripts/governance/check_all.py [--mode warn|block] [--tier TIER]
    python scripts/governance/check_all.py --policy PATH [--strict-policy]

Options:
    --mode warn   Run checks, report issues, but exit 0 (non-blocking)
    --mode block  Run checks, exit 1 on any failure (default)
    --tier TIER   Run only checks at or below this tier:
                    precommit  - fast checks only (~5s total)
                    ci         - precommit + CI checks (~30s total)
                    nightly    - all checks including heavy validation
                    manual     - explicit invocation only (not run by default)
                  Default: ci
    --policy PATH Load additional checks from policy JSON file
    --strict-policy  Fail if policy file is invalid or missing
    --fail-on-missing-active-script  Fail if an active policy script doesn't exist
    --json-output PATH  Write JSON report to file
    --list        List available checks and exit

Enforcement Tiers:
    precommit     Fast checks suitable for pre-commit hooks (<2s each)
    ci            Checks that run on every CI build (<30s each)
    nightly       Heavy checks that run on nightly/scheduled builds
    manual        Checks requiring explicit invocation

Exit codes:
    0 - All checks pass (or warn mode)
    1 - One or more blocking checks failed (block mode only)
    2 - Policy error (missing active scripts, invalid policy)

Part of Governance Execution Alignment Sprint.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import IntEnum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


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

# Static governance checks with enforcement tiers
# Format: (script_path, description, blocking, tier)
GOVERNANCE_CHECKS: List[Tuple[str, str, bool, EnforcementTier]] = [
    # === PRECOMMIT TIER — fast checks, <2s each ===
    ("scripts/check_protected_paths.py", "Protected paths enforcement", True, EnforcementTier.PRECOMMIT),
    ("scripts/check_sprint_namespace.py", "Sprint namespace conventions", False, EnforcementTier.PRECOMMIT),
    ("scripts/check_dxf_compat.py", "DXF compatibility enforcement", True, EnforcementTier.PRECOMMIT),
    ("scripts/governance/check_manifest_index.py", "Manifest index validation", True, EnforcementTier.PRECOMMIT),
    (
        "scripts/governance/check_semantic_sandbox_imports.py",
        "Semantic sandbox import gate (Tier A cognition/grid)",
        True,
        EnforcementTier.PRECOMMIT,
    ),

    # === CI TIER — moderate checks, <30s each ===
    ("scripts/check_capability_registry.py", "CAM capability registry", True, EnforcementTier.CI),
    ("scripts/check_semantic_leakage.py", "Semantic layer boundaries", False, EnforcementTier.CI),
    ("scripts/governance/check_artifact_linkage_invariants.py", "Artifact linkage invariants", False, EnforcementTier.CI),
    ("scripts/governance/validate_run_artifact_contract.py", "Run artifact contract", False, EnforcementTier.CI),

    # === NIGHTLY TIER — heavy checks requiring full app initialization ===
    ("scripts/governance/check_routing_truth.py", "Routing truth validation", False, EnforcementTier.NIGHTLY),

    # === MRP-5K: Ontology Governance Checks ===
    ("scripts/governance/audit_authority_chains.py", "Authority chain audit", True, EnforcementTier.CI),
    ("scripts/governance/validate_lifecycle_terms.py", "Lifecycle vocabulary validation", False, EnforcementTier.CI),
    ("scripts/governance/detect_semantic_drift.py", "Semantic drift detection", False, EnforcementTier.NIGHTLY),
]


@dataclass
class CheckResult:
    """Result of a governance check."""
    id: str
    name: str
    script: str
    passed: bool
    blocking: bool
    tier: str
    severity: str
    exists: bool
    duration_ms: int
    output: str = ""
    error: str = ""
    source: str = "static"  # "static" or "policy"

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items()}


@dataclass
class GovernanceReport:
    """Complete governance check report."""
    timestamp: str
    mode: str
    tier: str
    policy_file: Optional[str]
    strict_policy: bool
    passed: int
    failed_blocking: int
    failed_warning: int
    missing_active_scripts: List[str]
    checks: List[CheckResult]
    exit_code: int
    duration_ms: int

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["checks"] = [c.to_dict() for c in self.checks]
        return d


def tier_from_string(s: str) -> EnforcementTier:
    """Convert tier string to enum."""
    mapping = {
        "precommit": EnforcementTier.PRECOMMIT,
        "ci": EnforcementTier.CI,
        "nightly": EnforcementTier.NIGHTLY,
        "manual": EnforcementTier.MANUAL,
    }
    return mapping.get(s.lower(), EnforcementTier.CI)


def load_policy_checks(policy_path: Path) -> Tuple[List[Tuple[str, str, bool, EnforcementTier, str]], Optional[str]]:
    """
    Load checks from policy JSON file.

    Returns:
        (list of (script, description, blocking, tier, check_id), error_message or None)
    """
    if not policy_path.exists():
        return [], f"Policy file not found: {policy_path}"

    try:
        with open(policy_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return [], f"Invalid JSON in policy file: {e}"

    checks_data = data.get("checks", {})
    checks = []

    for check_id, check_info in checks_data.items():
        if not check_info.get("active", True):
            continue

        script = check_info.get("script", "")
        description = check_info.get("description", check_id)
        severity = check_info.get("severity", "warning")
        tier_str = check_info.get("tier", "ci")

        blocking = severity.lower() == "blocking"
        tier = tier_from_string(tier_str)

        checks.append((script, description, blocking, tier, check_id))

    return checks, None


def find_missing_active_scripts(
    policy_path: Path,
    root: Path
) -> Tuple[List[str], Optional[str]]:
    """
    Find active policy scripts that don't exist.

    Returns:
        (list of missing script paths, error_message or None)
    """
    if not policy_path.exists():
        return [], f"Policy file not found: {policy_path}"

    try:
        with open(policy_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return [], f"Invalid JSON in policy file: {e}"

    checks_data = data.get("checks", {})
    missing = []

    for check_id, check_info in checks_data.items():
        if not check_info.get("active", True):
            continue

        script = check_info.get("script", "")
        missing_behavior = check_info.get("missing_script_behavior", "fail")

        if missing_behavior == "fail":
            script_path = root / script
            if not script_path.exists():
                missing.append(script)

    return missing, None


def run_check(
    script_path: str,
    description: str,
    blocking: bool,
    tier: EnforcementTier,
    check_id: str = "",
    source: str = "static"
) -> CheckResult:
    """
    Run a single governance check script.

    Args:
        script_path: Path to script relative to repo root
        description: Human-readable description
        blocking: Whether failure should block CI
        tier: Enforcement tier
        check_id: Unique identifier for the check
        source: "static" or "policy"

    Returns:
        CheckResult with pass/fail status and output
    """
    full_path = REPO_ROOT / script_path
    check_id = check_id or script_path.replace("/", "_").replace(".", "_")
    severity = "blocking" if blocking else "warning"

    # Script doesn't exist
    if not full_path.exists():
        return CheckResult(
            id=check_id,
            name=description,
            script=script_path,
            passed=True,  # Missing optional scripts don't fail (policy handles this separately)
            blocking=blocking,
            tier=tier.name.lower(),
            severity=severity,
            exists=False,
            duration_ms=0,
            output="",
            error=f"Script not found: {script_path} (skipped)",
            source=source,
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
            id=check_id,
            name=description,
            script=script_path,
            passed=(result.returncode == 0),
            blocking=blocking,
            tier=tier.name.lower(),
            severity=severity,
            exists=True,
            duration_ms=duration_ms,
            output=result.stdout,
            error=result.stderr if result.returncode != 0 else "",
            source=source,
        )

    except subprocess.TimeoutExpired:
        duration_ms = int((time.time() - start_time) * 1000)
        return CheckResult(
            id=check_id,
            name=description,
            script=script_path,
            passed=False,
            blocking=blocking,
            tier=tier.name.lower(),
            severity=severity,
            exists=True,
            duration_ms=duration_ms,
            output="",
            error="Script timed out (>120s)",
            source=source,
        )

    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        return CheckResult(
            id=check_id,
            name=description,
            script=script_path,
            passed=False,
            blocking=blocking,
            tier=tier.name.lower(),
            severity=severity,
            exists=True,
            duration_ms=duration_ms,
            output="",
            error=f"Execution error: {e}",
            source=source,
        )


def print_result(result: CheckResult, verbose: bool = False) -> None:
    """Print a single check result."""
    if result.passed:
        status = "PASS"
    elif result.blocking:
        status = "FAIL"
    else:
        status = "WARN"

    blocking_marker = " [blocking]" if result.blocking else ""
    source_marker = " (policy)" if result.source == "policy" else ""

    print(f"  [{status}] {result.name} ({result.duration_ms}ms){blocking_marker} [{result.tier}]{source_marker}")

    if not result.passed and verbose:
        if result.error:
            for line in result.error.strip().split("\n")[:5]:
                print(f"         {line}")
        if result.output and not result.error:
            for line in result.output.strip().split("\n")[:5]:
                print(f"         {line}")


def write_json_report(report: GovernanceReport, path: Path) -> None:
    """Write governance report to JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report.to_dict(), f, indent=2)


def list_checks(
    max_tier: EnforcementTier,
    policy_path: Optional[Path] = None
) -> None:
    """List available governance checks."""
    print("Available governance checks:")
    print()

    # Static checks
    print("STATIC CHECKS:")
    for tier in EnforcementTier:
        tier_checks = [(s, d, b, t) for s, d, b, t in GOVERNANCE_CHECKS if t == tier]
        if tier_checks:
            print(f"  {tier.name}:")
            for script, desc, blocking, _ in tier_checks:
                status = "blocking" if blocking else "warn-only"
                exists = "+" if (REPO_ROOT / script).exists() else "-"
                active = "*" if tier <= max_tier else " "
                print(f"   {active}[{exists}] {desc} ({status})")
                print(f"        {script}")
            print()

    # Policy checks
    if policy_path and policy_path.exists():
        policy_checks, err = load_policy_checks(policy_path)
        if not err and policy_checks:
            print(f"POLICY CHECKS (from {policy_path.name}):")
            for tier in EnforcementTier:
                tier_checks = [(s, d, b, t, i) for s, d, b, t, i in policy_checks if t == tier]
                if tier_checks:
                    print(f"  {tier.name}:")
                    for script, desc, blocking, _, check_id in tier_checks:
                        status = "blocking" if blocking else "warn-only"
                        exists = "+" if (REPO_ROOT / script).exists() else "-"
                        active = "*" if tier <= max_tier else " "
                        print(f"   {active}[{exists}] {desc} ({status}) [{check_id}]")
                        print(f"        {script}")
                    print()

    print("Legend: [+] exists, [-] missing, * active at selected tier")


def main() -> int:
    """
    Run all governance checks.
    """
    parser = argparse.ArgumentParser(
        description="Unified governance check runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run CI-tier checks in blocking mode (default)
  python scripts/governance/check_all.py

  # Run with policy file and JSON output
  python scripts/governance/check_all.py --policy docs/governance/ontology/ontology_ci_policy.json --json-output report.json

  # Strict policy enforcement (fail on missing active scripts)
  python scripts/governance/check_all.py --policy PATH --strict-policy --fail-on-missing-active-script
"""
    )
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
    parser.add_argument(
        "--policy",
        type=str,
        metavar="PATH",
        help="Load additional checks from policy JSON file"
    )
    parser.add_argument(
        "--strict-policy",
        action="store_true",
        help="Fail if policy file is invalid or cannot be loaded"
    )
    parser.add_argument(
        "--fail-on-missing-active-script",
        action="store_true",
        help="Fail if an active policy script doesn't exist"
    )
    parser.add_argument(
        "--json-output",
        type=str,
        metavar="PATH",
        help="Write JSON report to file"
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

    # Resolve policy path
    policy_path: Optional[Path] = None
    if args.policy:
        policy_path = Path(args.policy)
        if not policy_path.is_absolute():
            policy_path = REPO_ROOT / policy_path

    # List mode
    if args.list:
        list_checks(max_tier, policy_path)
        return 0

    # Check for missing active scripts (policy validation)
    missing_active_scripts: List[str] = []
    policy_error: Optional[str] = None

    if policy_path:
        if not policy_path.exists():
            policy_error = f"Policy file not found: {policy_path}"
            if args.strict_policy:
                print(f"[ERROR] {policy_error}")
                return 2
            else:
                print(f"[WARN] {policy_error} (continuing without policy)")
                policy_path = None
        elif args.fail_on_missing_active_script:
            missing_active_scripts, err = find_missing_active_scripts(policy_path, REPO_ROOT)
            if err and args.strict_policy:
                print(f"[ERROR] {err}")
                return 2
            if missing_active_scripts:
                print("[ERROR] Missing active policy scripts:")
                for script in missing_active_scripts:
                    print(f"  - {script}")
                return 2

    # Collect all checks
    all_checks: List[Tuple[str, str, bool, EnforcementTier, str, str]] = []
    seen_scripts: Set[str] = set()

    # Add static checks
    for script, desc, blocking, tier in GOVERNANCE_CHECKS:
        check_id = script.replace("/", "_").replace(".", "_")
        all_checks.append((script, desc, blocking, tier, check_id, "static"))
        seen_scripts.add(script)

    # Add policy checks (deduplicate by script path)
    if policy_path and policy_path.exists():
        policy_checks, err = load_policy_checks(policy_path)
        if err:
            if args.strict_policy:
                print(f"[ERROR] {err}")
                return 2
            else:
                print(f"[WARN] {err}")
        else:
            for script, desc, blocking, tier, check_id in policy_checks:
                if script not in seen_scripts:
                    all_checks.append((script, desc, blocking, tier, check_id, "policy"))
                    seen_scripts.add(script)

    # Filter checks by tier
    active_checks = [(s, d, b, t, i, src) for s, d, b, t, i, src in all_checks if t <= max_tier]
    skipped_count = len(all_checks) - len(active_checks)

    # Print header
    print("=" * 60)
    print("UNIFIED GOVERNANCE CHECK")
    print(f"Mode: {args.mode.upper()} | Tier: {args.tier.upper()}")
    if policy_path:
        print(f"Policy: {policy_path.name}")
    if skipped_count > 0:
        print(f"Skipping {skipped_count} check(s) above {args.tier} tier")
    print("=" * 60)
    print()

    # Run checks
    results: List[CheckResult] = []
    start_time = time.time()

    for script, description, blocking, tier, check_id, source in active_checks:
        result = run_check(script, description, blocking, tier, check_id, source)
        results.append(result)
        print_result(result, verbose=args.verbose)

    total_duration_ms = int((time.time() - start_time) * 1000)

    print()
    print("-" * 60)

    # Summary
    passed = sum(1 for r in results if r.passed)
    failed_blocking = sum(1 for r in results if not r.passed and r.blocking)
    failed_warning = sum(1 for r in results if not r.passed and not r.blocking)
    total = len(results)

    print(f"Results: {passed}/{total} passed")
    if failed_blocking > 0:
        print(f"         {failed_blocking} blocking failure(s)")
    if failed_warning > 0:
        print(f"         {failed_warning} warning(s)")
    print(f"Duration: {total_duration_ms}ms")
    print()

    # Determine exit code
    if args.mode == "warn":
        exit_code = 0
        if failed_blocking > 0:
            print("[WARN] Governance checks have failures (warn mode - not blocking)")
        else:
            print("[OK] Governance checks passed")
    else:
        if failed_blocking > 0:
            exit_code = 1
            print("[FAIL] Governance checks failed")
        else:
            exit_code = 0
            print("[OK] Governance checks passed")

    # Write JSON report
    if args.json_output:
        report = GovernanceReport(
            timestamp=datetime.now(timezone.utc).isoformat(),
            mode=args.mode,
            tier=args.tier,
            policy_file=str(policy_path) if policy_path else None,
            strict_policy=args.strict_policy,
            passed=passed,
            failed_blocking=failed_blocking,
            failed_warning=failed_warning,
            missing_active_scripts=missing_active_scripts,
            checks=results,
            exit_code=exit_code,
            duration_ms=total_duration_ms,
        )

        output_path = Path(args.json_output)
        if not output_path.is_absolute():
            output_path = REPO_ROOT / output_path

        write_json_report(report, output_path)
        print(f"\nJSON report written to: {output_path}")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
