#!/usr/bin/env python3
"""
Detect Semantic Drift

Sprint: MRP-5J / Governance Execution Alignment
Purpose: Detect conflicting terminology, duplicate definitions, and vocabulary drift

Finding categories:
- canonical_usage: Term used as registered
- alias_usage: Known alias used
- deprecated_alias: Deprecated alias used (migration suggested)
- unknown_semantic_term: Unregistered lifecycle-like term
- possible_collision: Term appears in conflicting contexts

Usage:
    python detect_semantic_drift.py [--json] [--json-output PATH] [--quiet]
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# Repository paths
REPO_ROOT = Path(__file__).parent.parent.parent
GOVERNANCE_DIR = REPO_ROOT / "docs" / "governance"
ONTOLOGY_DIR = GOVERNANCE_DIR / "ontology"
APP_DIR = REPO_ROOT / "services" / "api" / "app"

# Lifecycle terms to check
LIFECYCLE_TERMS = {
    "canonical", "governed", "experimental", "semantic_only", "prototype",
    "unsupported_runtime", "quarantine", "validation_only", "governed_experimental",
    "machine_candidate", "preview_only", "supported", "partial_prototype",
    "research_required", "blocking", "major", "warning", "unsupported"
}

# Known term variations that are NOT conflicts
KNOWN_ALIASES = {
    "SUPPORTED_PROTOTYPE": "supported_prototype",
    "PARTIAL_PROTOTYPE": "partial_prototype",
    "UNSUPPORTED_RUNTIME": "unsupported_runtime",
    "RESEARCH_REQUIRED": "research_required",
    "SEMANTIC_ONLY": "semantic_only",
    "BLOCKING": "blocking",
    "MAJOR": "major",
    "WARNING": "warning",
}


def find_lifecycle_usage_in_file(filepath: Path) -> Dict[str, List[int]]:
    """Find lifecycle term usage in a file."""
    usage = {}
    try:
        content = filepath.read_text(encoding="utf-8", errors="ignore")
        lines = content.split("\n")
        for i, line in enumerate(lines, 1):
            for term in LIFECYCLE_TERMS:
                # Case-insensitive search but track exact match
                pattern = rf"\b{re.escape(term)}\b"
                if re.search(pattern, line, re.IGNORECASE):
                    if term not in usage:
                        usage[term] = []
                    usage[term].append(i)
    except Exception:
        pass
    return usage


def scan_governance_docs() -> Dict[str, Dict[str, List[int]]]:
    """Scan governance docs for lifecycle term usage."""
    results = {}
    for md_file in GOVERNANCE_DIR.glob("**/*.md"):
        usage = find_lifecycle_usage_in_file(md_file)
        if usage:
            results[str(md_file.relative_to(REPO_ROOT))] = usage
    return results


def scan_python_enums() -> Dict[str, List[str]]:
    """Scan Python files for enum definitions containing lifecycle terms."""
    enum_defs = {}
    for py_file in APP_DIR.glob("**/*.py"):
        try:
            content = py_file.read_text(encoding="utf-8", errors="ignore")
            # Find enum classes
            enum_pattern = r"class\s+(\w+)\s*\([^)]*Enum[^)]*\):"
            for match in re.finditer(enum_pattern, content):
                enum_name = match.group(1)
                # Find values in the enum
                start = match.end()
                # Simple extraction of uppercase values
                value_pattern = r"^\s+([A-Z_]+)\s*="
                lines_after = content[start:start+2000].split("\n")
                values = []
                for line in lines_after:
                    if re.match(r"^class\s+", line):
                        break
                    vm = re.match(value_pattern, line)
                    if vm:
                        values.append(vm.group(1))
                if values:
                    key = f"{py_file.relative_to(REPO_ROOT)}:{enum_name}"
                    enum_defs[key] = values
        except Exception:
            pass
    return enum_defs


def detect_duplicate_definitions(enum_defs: Dict[str, List[str]]) -> List[Tuple[str, str, str]]:
    """Detect duplicate enum value definitions across files."""
    duplicates = []
    value_to_sources: Dict[str, List[str]] = {}

    for source, values in enum_defs.items():
        for value in values:
            if value not in value_to_sources:
                value_to_sources[value] = []
            value_to_sources[value].append(source)

    for value, sources in value_to_sources.items():
        if len(sources) > 1:
            # Check if this is an expected alias
            if value in KNOWN_ALIASES:
                continue
            duplicates.append((value, sources[0], sources[1]))

    return duplicates


def detect_conflicting_meanings(doc_usage: Dict[str, Dict[str, List[int]]]) -> List[Dict]:
    """Detect terms that might have conflicting meanings based on context."""
    conflicts = []

    # Check for terms used in potentially conflicting contexts
    term_contexts: Dict[str, Set[str]] = {}
    for filepath, usage in doc_usage.items():
        for term in usage:
            if term not in term_contexts:
                term_contexts[term] = set()
            # Categorize by document type
            if "TOPOLOGY" in filepath.upper():
                term_contexts[term].add("topology")
            if "CAD" in filepath.upper():
                term_contexts[term].add("cad")
            if "CAM" in filepath.upper():
                term_contexts[term].add("cam")
            if "ACOUSTIC" in filepath.upper():
                term_contexts[term].add("acoustic")
            if "EXPORT" in filepath.upper():
                term_contexts[term].add("export")

    # Flag terms used across multiple distinct domains
    for term, contexts in term_contexts.items():
        if len(contexts) >= 3:
            conflicts.append({
                "term": term,
                "contexts": list(contexts),
                "severity": "potential_conflict",
                "note": f"Term '{term}' appears across {len(contexts)} domains"
            })

    return conflicts


def check_registry_completeness() -> List[str]:
    """Check if all discovered terms are in the registry."""
    missing = []
    registry_file = ONTOLOGY_DIR / "lifecycle_registry.json"

    if not registry_file.exists():
        return ["lifecycle_registry.json not found"]

    try:
        registry = json.loads(registry_file.read_text())
        registered_terms = set(registry.get("classifications", {}).keys())

        for term in LIFECYCLE_TERMS:
            if term not in registered_terms:
                missing.append(f"Term '{term}' not in lifecycle_registry.json")
    except Exception as e:
        missing.append(f"Error reading registry: {e}")

    return missing


def write_json_output(data: Dict, path: Path) -> None:
    """Write JSON report to file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Detect semantic drift in repository")
    parser.add_argument("--json", action="store_true", help="Output in JSON format to stdout")
    parser.add_argument("--json-output", type=str, metavar="PATH", help="Write JSON report to file")
    parser.add_argument("--quiet", action="store_true", help="Suppress human-readable output")
    parser.add_argument("--include-timestamp", action="store_true", help="Include generated_at timestamp")
    args = parser.parse_args()

    results = {
        "script": "scripts/governance/detect_semantic_drift.py",
        "passed": True,
        "severity": "advisory",
        "generated_at": datetime.now(timezone.utc).isoformat() if args.include_timestamp else None,
        "duplicate_definitions": [],
        "conflicting_meanings": [],
        "missing_registrations": [],
        "governance_doc_usage": {},
        "enum_definitions": {},
        "warnings": [],
        "errors": [],
        "summary": {},
        "findings": []
    }

    # Scan governance docs
    results["governance_doc_usage"] = scan_governance_docs()

    # Scan Python enums
    results["enum_definitions"] = scan_python_enums()

    # Detect duplicates
    results["duplicate_definitions"] = detect_duplicate_definitions(results["enum_definitions"])

    # Detect conflicts
    results["conflicting_meanings"] = detect_conflicting_meanings(results["governance_doc_usage"])

    # Check registry completeness
    results["missing_registrations"] = check_registry_completeness()

    # Build categorized findings
    for value, src1, src2 in results["duplicate_definitions"]:
        results["findings"].append({
            "category": "duplicate_definition",
            "term": value,
            "sources": [src1, src2],
            "severity": "advisory"
        })

    for conflict in results["conflicting_meanings"]:
        results["findings"].append({
            "category": "possible_collision",
            "term": conflict["term"],
            "contexts": conflict["contexts"],
            "severity": "advisory"
        })

    for msg in results["missing_registrations"]:
        results["findings"].append({
            "category": "unknown_semantic_term",
            "message": msg,
            "severity": "warning"
        })

    # Categorized summary
    results["summary"] = {
        "canonical_usage": sum(
            sum(len(lines) for lines in usage.values())
            for usage in results["governance_doc_usage"].values()
        ),
        "alias_usage": 0,  # Could be expanded with alias detection
        "deprecated_alias": 0,  # Could be expanded
        "duplicate_definitions": len(results["duplicate_definitions"]),
        "possible_collisions": len(results["conflicting_meanings"]),
        "unknown_terms": len(results["missing_registrations"]),
        "total_findings": len(results["findings"])
    }

    # Determine exit code
    # Semantic drift is advisory only - never blocking
    has_errors = bool(results["errors"])
    has_warnings = len(results["findings"]) > 0

    results["passed"] = not has_errors
    results["advisory_count"] = len([f for f in results["findings"] if f.get("severity") == "advisory"])
    results["warning_count"] = len([f for f in results["findings"] if f.get("severity") == "warning"])

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
        print("SEMANTIC DRIFT DETECTION REPORT")
        print("=" * 60)

        print(f"\nGovernance docs scanned: {len(results['governance_doc_usage'])}")
        print(f"Python enums found: {len(results['enum_definitions'])}")

        print(f"\n--- SUMMARY ---")
        print(f"Duplicate definitions: {results['summary']['duplicate_definitions']}")
        print(f"Cross-domain collisions: {results['summary']['possible_collisions']}")
        print(f"Missing registrations: {results['summary']['unknown_terms']}")
        print(f"Total findings: {results['summary']['total_findings']}")

        if results["duplicate_definitions"]:
            print("\n--- DUPLICATE DEFINITIONS [ADVISORY] ---")
            for value, src1, src2 in results["duplicate_definitions"][:5]:
                print(f"  {value}: {src1} vs {src2}")
            if len(results["duplicate_definitions"]) > 5:
                print(f"  ... and {len(results['duplicate_definitions']) - 5} more")

        if results["conflicting_meanings"]:
            print("\n--- POSSIBLE COLLISIONS [ADVISORY] ---")
            for conflict in results["conflicting_meanings"][:5]:
                print(f"  {conflict['term']}: used in {conflict['contexts']}")
            if len(results["conflicting_meanings"]) > 5:
                print(f"  ... and {len(results['conflicting_meanings']) - 5} more")

        if results["missing_registrations"]:
            print("\n--- MISSING REGISTRATIONS [WARNING] ---")
            for msg in results["missing_registrations"][:5]:
                print(f"  {msg}")
            if len(results["missing_registrations"]) > 5:
                print(f"  ... and {len(results['missing_registrations']) - 5} more")

        print("\n" + "=" * 60)
        if has_errors:
            print("STATUS: ERRORS FOUND")
        elif has_warnings:
            print(f"STATUS: ADVISORY ({results['summary']['total_findings']} findings)")
        else:
            print("STATUS: CLEAN")
        print("=" * 60)

    # Exit with appropriate code
    # Semantic drift is advisory-only - always exit 0 unless hard errors
    sys.exit(1 if has_errors else 0)


if __name__ == "__main__":
    main()
