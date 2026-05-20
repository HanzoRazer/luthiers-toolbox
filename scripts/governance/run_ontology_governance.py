#!/usr/bin/env python3
"""
Run Ontology Governance

Sprint: MRP-5K
Purpose: Unified ontology governance check runner with formatted reporting

Usage:
    python run_ontology_governance.py [--json] [--output PATH]

Exit codes:
    0 - All checks pass or only advisory/warning findings
    1 - Blocking authority violations found
    2 - Reserved for quarantine (not activated)
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Repository paths
REPO_ROOT = Path(__file__).parent.parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts" / "governance"
ONTOLOGY_DIR = REPO_ROOT / "docs" / "governance" / "ontology"


def run_script(script_name: str) -> Dict:
    """Run a governance script and capture JSON output."""
    script_path = SCRIPTS_DIR / script_name

    if not script_path.exists():
        return {"error": f"Script not found: {script_name}"}

    try:
        result = subprocess.run(
            [sys.executable, str(script_path), "--json"],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(REPO_ROOT)
        )

        if result.stdout.strip():
            return json.loads(result.stdout)
        return {"error": "No output", "stderr": result.stderr}

    except subprocess.TimeoutExpired:
        return {"error": "Timeout"}
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON: {e}", "raw": result.stdout[:500]}
    except Exception as e:
        return {"error": str(e)}


def load_policy() -> Dict:
    """Load ontology CI policy."""
    policy_file = ONTOLOGY_DIR / "ontology_ci_policy.json"
    if policy_file.exists():
        try:
            return json.loads(policy_file.read_text())
        except Exception:
            pass
    return {}


def count_severity(results: Dict) -> Dict:
    """Count findings by severity."""
    counts = {
        "informational": 0,
        "advisory": 0,
        "warning": 0,
        "blocking": 0,
        "quarantine": 0
    }

    # Authority chain results
    authority = results.get("authority_chains", {})
    # Blocking: completeness issues or error-severity violations
    blocking_violations = [
        v for v in authority.get("redefinition_violations", [])
        if v.get("severity") == "error"
    ]
    counts["blocking"] += len(authority.get("completeness_issues", []))
    counts["blocking"] += len(blocking_violations)
    # Warning: other violations
    counts["warning"] += len([
        v for v in authority.get("redefinition_violations", [])
        if v.get("severity") != "error"
    ])
    counts["warning"] += len(authority.get("ordering_violations", []))

    # Lifecycle results
    lifecycle = results.get("lifecycle", {})
    summary = lifecycle.get("summary", {})
    counts["warning"] += summary.get("potential_issues", 0)
    counts["informational"] += summary.get("valid_usages", 0)
    counts["informational"] += summary.get("alias_usages", 0)

    # Drift results
    drift = results.get("drift", {})
    counts["advisory"] += len(drift.get("duplicate_definitions", []))
    counts["advisory"] += len(drift.get("conflicting_meanings", []))
    counts["warning"] += len(drift.get("missing_registrations", []))

    return counts


def generate_report(results: Dict, counts: Dict) -> str:
    """Generate formatted text report."""
    lines = [
        "ONTOLOGY GOVERNANCE REPORT",
        "=" * 26,
        f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "SUMMARY",
        "-" * 7,
        f"Authority Violations: {counts['blocking']}",
        f"Lifecycle Warnings: {counts['warning']}",
        f"Semantic Drift Findings: {counts['advisory']}",
        f"Blocking Failures: {counts['blocking']}",
        f"Advisory Findings: {counts['advisory']}",
        f"Informational: {counts['informational']}",
        "",
    ]

    # Authority details
    authority = results.get("authority_chains", {})
    if authority.get("completeness_issues") or authority.get("redefinition_violations"):
        lines.append("AUTHORITY CHAIN DETAILS")
        lines.append("-" * 23)
        for issue in authority.get("completeness_issues", []):
            lines.append(f"  [BLOCK] {issue}")
        for v in authority.get("redefinition_violations", []):
            severity = "BLOCK" if v.get("severity") == "error" else "WARN"
            lines.append(f"  [{severity}] {v['chain']}: {v['term']}")
        lines.append("")

    # Lifecycle details
    lifecycle = results.get("lifecycle", {})
    if lifecycle.get("python_scan", {}).get("potential_issues"):
        lines.append("LIFECYCLE VOCABULARY DETAILS")
        lines.append("-" * 28)
        issues = lifecycle["python_scan"]["potential_issues"][:5]
        for issue in issues:
            lines.append(f"  [WARN] {issue['file']}:{issue['line']} - '{issue['term']}'")
        remaining = len(lifecycle["python_scan"]["potential_issues"]) - len(issues)
        if remaining > 0:
            lines.append(f"  ... and {remaining} more")
        lines.append("")

    # Drift summary
    drift = results.get("drift", {})
    if drift.get("duplicate_definitions") or drift.get("conflicting_meanings"):
        lines.append("SEMANTIC DRIFT DETAILS")
        lines.append("-" * 22)
        lines.append(f"  [ADVISORY] {len(drift.get('duplicate_definitions', []))} duplicate enum values")
        lines.append(f"  [ADVISORY] {len(drift.get('conflicting_meanings', []))} cross-domain terms")
        for reg in drift.get("missing_registrations", []):
            lines.append(f"  [WARN] {reg}")
        lines.append("")

    # Exit code explanation
    lines.append("EXIT CODE")
    lines.append("-" * 9)
    if counts["blocking"] > 0:
        lines.append("  1 - Blocking authority violations found")
    else:
        lines.append("  0 - No blocking violations (advisory/warnings only)")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Run ontology governance checks")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    parser.add_argument("--output", type=str, help="Write report to file")
    parser.add_argument("--skip-drift", action="store_true",
                       help="Skip drift detection (faster)")
    args = parser.parse_args()

    # Run checks
    results = {
        "timestamp": datetime.now().isoformat(),
        "authority_chains": run_script("audit_authority_chains.py"),
        "lifecycle": run_script("validate_lifecycle_terms.py"),
    }

    if not args.skip_drift:
        results["drift"] = run_script("detect_semantic_drift.py")
    else:
        results["drift"] = {"skipped": True}

    # Count severities
    counts = count_severity(results)

    # Generate output
    if args.json:
        output = json.dumps({
            "results": results,
            "counts": counts,
            "exit_code": 1 if counts["blocking"] > 0 else 0
        }, indent=2)
    else:
        output = generate_report(results, counts)

    # Output handling
    if args.output:
        Path(args.output).write_text(output)
        print(f"Report written to: {args.output}")
    else:
        print(output)

    # Exit code
    if counts["blocking"] > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
