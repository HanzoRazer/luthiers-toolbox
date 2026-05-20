#!/usr/bin/env python3
"""
Validate Lifecycle Terms

Sprint: MRP-5J / Governance Execution Alignment
Purpose: Validate that lifecycle terms in code and docs match canonical registry

Usage:
    python validate_lifecycle_terms.py [--json] [--strict] [--json-output PATH] [--quiet]
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set

# Repository paths
REPO_ROOT = Path(__file__).parent.parent.parent
GOVERNANCE_DIR = REPO_ROOT / "docs" / "governance"
ONTOLOGY_DIR = GOVERNANCE_DIR / "ontology"
APP_DIR = REPO_ROOT / "services" / "api" / "app"


def load_lifecycle_registry() -> Dict:
    """Load the canonical lifecycle registry."""
    registry_file = ONTOLOGY_DIR / "lifecycle_registry.json"
    if not registry_file.exists():
        return {"error": "Registry file not found"}
    try:
        return json.loads(registry_file.read_text())
    except Exception as e:
        return {"error": str(e)}


def load_alias_registry() -> Dict:
    """Load the alias registry."""
    alias_file = ONTOLOGY_DIR / "ontology_alias_registry.json"
    if not alias_file.exists():
        return {}
    try:
        return json.loads(alias_file.read_text())
    except Exception:
        return {}


def get_canonical_terms(registry: Dict) -> Set[str]:
    """Extract canonical terms from registry."""
    classifications = registry.get("classifications", {})
    return set(classifications.keys())


def get_valid_aliases(alias_registry: Dict) -> Dict[str, str]:
    """Get mapping of valid aliases to canonical terms."""
    aliases = alias_registry.get("aliases", {})
    return {alias: info.get("canonical_term", "") for alias, info in aliases.items()}


def find_lifecycle_terms_in_python(filepath: Path) -> List[Dict]:
    """Find lifecycle-related terms in a Python file."""
    findings = []
    try:
        content = filepath.read_text(encoding="utf-8", errors="ignore")
        lines = content.split("\n")

        for i, line in enumerate(lines, 1):
            # Look for string literals that might be lifecycle terms
            string_pattern = r'["\']([a-z_]+)["\']'
            for match in re.finditer(string_pattern, line, re.IGNORECASE):
                term = match.group(1).lower()
                if len(term) > 3:  # Skip very short strings
                    findings.append({
                        "file": str(filepath.relative_to(REPO_ROOT)),
                        "line": i,
                        "term": term,
                        "context": line.strip()[:80]
                    })
    except Exception:
        pass
    return findings


def validate_findings(
    findings: List[Dict],
    canonical_terms: Set[str],
    valid_aliases: Dict[str, str]
) -> Dict:
    """Validate findings against canonical registry."""
    results = {
        "valid": [],
        "alias_usage": [],
        "unknown": [],
        "potential_issues": []
    }

    # Terms that look like lifecycle terms
    lifecycle_patterns = {
        "supported", "unsupported", "prototype", "production",
        "semantic", "runtime", "blocking", "warning", "experimental",
        "governed", "canonical", "quarantine", "validation"
    }

    for finding in findings:
        term = finding["term"]

        if term in canonical_terms:
            results["valid"].append(finding)
        elif term.upper() in valid_aliases:
            finding["canonical"] = valid_aliases[term.upper()]
            results["alias_usage"].append(finding)
        elif any(p in term for p in lifecycle_patterns):
            # This looks like it might be a lifecycle term but isn't registered
            results["potential_issues"].append(finding)

    return results


def scan_manifests() -> List[Dict]:
    """Scan JSON manifests for lifecycle-related fields."""
    findings = []
    manifest_patterns = ["*manifest*.json", "*registry*.json"]

    for pattern in manifest_patterns:
        for json_file in GOVERNANCE_DIR.glob(f"**/{pattern}"):
            try:
                content = json.loads(json_file.read_text())
                # Look for lifecycle-related keys
                findings.extend(
                    find_lifecycle_in_dict(
                        content,
                        str(json_file.relative_to(REPO_ROOT))
                    )
                )
            except Exception:
                pass

    return findings


def find_lifecycle_in_dict(data: Dict, filepath: str, path: str = "") -> List[Dict]:
    """Recursively find lifecycle-related values in a dict."""
    findings = []
    lifecycle_keys = {"status", "lifecycle", "state", "classification", "tier", "level"}

    if isinstance(data, dict):
        for key, value in data.items():
            current_path = f"{path}.{key}" if path else key
            if key.lower() in lifecycle_keys and isinstance(value, str):
                findings.append({
                    "file": filepath,
                    "path": current_path,
                    "term": value.lower(),
                    "context": f"{key}: {value}"
                })
            findings.extend(find_lifecycle_in_dict(value, filepath, current_path))
    elif isinstance(data, list):
        for i, item in enumerate(data):
            findings.extend(find_lifecycle_in_dict(item, filepath, f"{path}[{i}]"))

    return findings


def write_json_output(data: Dict, path: Path) -> None:
    """Write JSON report to file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Validate lifecycle terms")
    parser.add_argument("--json", action="store_true", help="Output in JSON format to stdout")
    parser.add_argument("--json-output", type=str, metavar="PATH", help="Write JSON report to file")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero on any issues")
    parser.add_argument("--quiet", action="store_true", help="Suppress human-readable output")
    parser.add_argument("--include-timestamp", action="store_true", help="Include generated_at timestamp")
    args = parser.parse_args()

    # Load registries
    registry = load_lifecycle_registry()
    if "error" in registry:
        if not args.quiet:
            print(f"Error loading registry: {registry['error']}")
        sys.exit(1)

    alias_registry = load_alias_registry()
    canonical_terms = get_canonical_terms(registry)
    valid_aliases = get_valid_aliases(alias_registry)

    results = {
        "script": "scripts/governance/validate_lifecycle_terms.py",
        "passed": True,
        "severity": "warning",
        "generated_at": datetime.now(timezone.utc).isoformat() if args.include_timestamp else None,
        "canonical_terms_count": len(canonical_terms),
        "valid_aliases_count": len(valid_aliases),
        "python_scan": {},
        "manifest_scan": {},
        "summary": {},
        "findings": [],
    }

    # Scan Python files (sample key directories)
    key_dirs = [
        APP_DIR / "export",
        APP_DIR / "cam" / "topology_builder",
        APP_DIR / "cam" / "translators",
    ]

    all_py_findings = []
    for dir_path in key_dirs:
        if dir_path.exists():
            for py_file in dir_path.glob("**/*.py"):
                all_py_findings.extend(find_lifecycle_terms_in_python(py_file))

    results["python_scan"] = validate_findings(
        all_py_findings, canonical_terms, valid_aliases
    )

    # Scan manifests
    manifest_findings = scan_manifests()
    results["manifest_scan"] = validate_findings(
        manifest_findings, canonical_terms, valid_aliases
    )

    # Build unified findings list
    for issue in results["python_scan"].get("potential_issues", []):
        results["findings"].append({"category": "python", "severity": "warning", **issue})
    for issue in results["manifest_scan"].get("potential_issues", []):
        results["findings"].append({"category": "manifest", "severity": "warning", **issue})

    # Summary
    results["summary"] = {
        "valid_usages": len(results["python_scan"]["valid"]) + len(results["manifest_scan"]["valid"]),
        "alias_usages": len(results["python_scan"]["alias_usage"]) + len(results["manifest_scan"]["alias_usage"]),
        "potential_issues": len(results["python_scan"]["potential_issues"]) + len(results["manifest_scan"]["potential_issues"]),
    }

    has_issues = results["summary"]["potential_issues"] > 0
    results["passed"] = not has_issues
    results["warnings"] = results["summary"]["potential_issues"]

    # Write JSON to file if requested
    if args.json_output:
        output_path = Path(args.json_output)
        write_json_output(results, output_path)
        if not args.quiet:
            print(f"JSON report written to: {output_path}")

    # Output
    if args.json:
        print(json.dumps(results, indent=2))
    elif not args.quiet:
        print("=" * 60)
        print("LIFECYCLE TERM VALIDATION REPORT")
        print("=" * 60)

        print(f"\nCanonical terms in registry: {results['canonical_terms_count']}")
        print(f"Valid aliases: {results['valid_aliases_count']}")

        print(f"\n--- SUMMARY ---")
        print(f"Valid usages: {results['summary']['valid_usages']}")
        print(f"Alias usages: {results['summary']['alias_usages']}")
        print(f"Potential issues: {results['summary']['potential_issues']}")

        if results["python_scan"]["potential_issues"]:
            print(f"\n--- POTENTIAL ISSUES (Python) ---")
            for issue in results["python_scan"]["potential_issues"][:10]:
                print(f"  {issue['file']}:{issue['line']} - '{issue['term']}'")
            if len(results["python_scan"]["potential_issues"]) > 10:
                print(f"  ... and {len(results['python_scan']['potential_issues']) - 10} more")

        print("\n" + "=" * 60)
        if has_issues:
            print("STATUS: POTENTIAL ISSUES FOUND")
        else:
            print("STATUS: CLEAN")
        print("=" * 60)

    # Exit code - warning only, never blocking in current sprint
    if args.strict and has_issues:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
