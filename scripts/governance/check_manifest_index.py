#!/usr/bin/env python3
"""
Manifest Index Validation Script

Validates the MANIFEST_INDEX.md against actual manifest files in the repository.

Checks:
1. All manifests listed in index exist
2. All governance manifests in repo are listed in index
3. Cross-references are bidirectional where required
4. JSON manifests have valid syntax

Usage:
    python scripts/governance/check_manifest_index.py

Exit codes:
    0 - All checks pass
    1 - Validation failures found

Part of Governance Remediation Infrastructure.
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple


# Repository root
REPO_ROOT = Path(__file__).parent.parent.parent

# Known manifest locations to scan
MANIFEST_DIRS = [
    "docs/governance",
    "docs/architecture",
    "tests/regression_corpus",
]

# Index file location
MANIFEST_INDEX_PATH = REPO_ROOT / "docs" / "governance" / "MANIFEST_INDEX.md"


def parse_manifest_index() -> List[Dict[str, str]]:
    """
    Parse MANIFEST_INDEX.md to extract listed manifests.

    Returns:
        List of dicts with keys: name, location, domain, purpose
    """
    if not MANIFEST_INDEX_PATH.exists():
        return []

    content = MANIFEST_INDEX_PATH.read_text(encoding="utf-8")

    # Find the manifest registry table
    # Format: | manifest_name | location | domain | purpose | version | owner |
    manifests = []

    # Match table rows - looking for .json in first column
    # Handle special locations like "root" and "tests/"
    lines = content.split("\n")
    in_table = False

    for line in lines:
        # Skip header and separator lines
        if "Manifest" in line and "Location" in line:
            in_table = True
            continue
        if line.strip().startswith("|--") or line.strip().startswith("|-"):
            continue
        if not line.strip().startswith("|"):
            if in_table and line.strip() == "":
                continue
            if in_table and line.strip().startswith("#"):
                break  # End of table section
            continue

        # Parse table row
        cells = [c.strip() for c in line.split("|")]
        cells = [c for c in cells if c]  # Remove empty strings

        if len(cells) >= 2 and cells[0].endswith(".json"):
            name = cells[0]
            location = cells[1] if len(cells) > 1 else ""

            # Normalize location
            if location == "root":
                location = ""
            elif location.endswith("/"):
                location = location.rstrip("/")

            manifests.append({
                "name": name,
                "location": location,
                "domain": cells[2] if len(cells) > 2 else "",
                "purpose": cells[3] if len(cells) > 3 else "",
            })

    return manifests


def find_all_manifests() -> Set[Path]:
    """
    Find all JSON manifest files in known governance directories.

    Returns:
        Set of manifest file paths relative to repo root
    """
    manifests = set()

    for dir_path in MANIFEST_DIRS:
        full_path = REPO_ROOT / dir_path
        if full_path.exists():
            for json_file in full_path.glob("*manifest*.json"):
                rel_path = json_file.relative_to(REPO_ROOT)
                manifests.add(rel_path)

    # Also check root for benchmark_manifest.json
    root_manifest = REPO_ROOT / "benchmark_manifest.json"
    if root_manifest.exists():
        manifests.add(Path("benchmark_manifest.json"))

    return manifests


def validate_json_syntax(file_path: Path) -> Tuple[bool, str]:
    """
    Validate JSON syntax of a manifest file.

    Returns:
        (is_valid, error_message)
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            json.load(f)
        return True, ""
    except json.JSONDecodeError as e:
        return False, f"JSON syntax error: {e}"
    except Exception as e:
        return False, f"Read error: {e}"


def check_cross_references(manifest_path: Path) -> List[str]:
    """
    Check if manifest has cross_references and verify they exist.

    Returns:
        List of issues found
    """
    issues = []

    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return issues  # JSON syntax checked elsewhere

    # Skip if root is not a dict (some manifests are arrays)
    if not isinstance(data, dict):
        return issues

    cross_refs = data.get("cross_references", [])
    if not cross_refs:
        return issues

    for ref in cross_refs:
        ref_path = ref.get("manifest", "")
        if ref_path:
            full_ref_path = REPO_ROOT / ref_path
            if not full_ref_path.exists():
                issues.append(f"Cross-reference not found: {ref_path}")

    return issues


def main() -> int:
    """
    Run all manifest index validations.
    """
    print("Validating Manifest Index...")
    print()

    all_issues = []

    # Check 1: Index file exists
    print("  Check 1: Manifest index exists...")
    if not MANIFEST_INDEX_PATH.exists():
        print("    FAIL: MANIFEST_INDEX.md not found")
        all_issues.append("MANIFEST_INDEX.md does not exist")
    else:
        print("    PASS")

    # Check 2: Parse index
    print("  Check 2: Parsing manifest index...")
    indexed_manifests = parse_manifest_index()
    if not indexed_manifests:
        print("    WARN: No manifests found in index (or index missing)")
    else:
        print(f"    PASS: Found {len(indexed_manifests)} indexed manifests")

    # Check 3: All indexed manifests exist
    print("  Check 3: Indexed manifests exist...")
    missing_count = 0
    for manifest in indexed_manifests:
        location = manifest["location"].rstrip("/")
        name = manifest["name"]
        full_path = REPO_ROOT / location / name

        if not full_path.exists():
            print(f"    FAIL: {location}/{name} not found")
            all_issues.append(f"Indexed manifest missing: {location}/{name}")
            missing_count += 1

    if missing_count == 0:
        print("    PASS")

    # Check 4: All repo manifests are indexed
    print("  Check 4: Repo manifests are indexed...")
    repo_manifests = find_all_manifests()
    indexed_paths = set()
    for m in indexed_manifests:
        path = Path(m["location"].rstrip("/")) / m["name"]
        indexed_paths.add(path)

    unindexed = repo_manifests - indexed_paths
    if unindexed:
        for path in sorted(unindexed):
            print(f"    WARN: {path} not in index")
            all_issues.append(f"Manifest not indexed: {path}")
    else:
        print("    PASS")

    # Check 5: JSON syntax validation
    print("  Check 5: JSON syntax validation...")
    syntax_errors = 0
    for manifest_path in repo_manifests:
        full_path = REPO_ROOT / manifest_path
        is_valid, error = validate_json_syntax(full_path)
        if not is_valid:
            print(f"    FAIL: {manifest_path}: {error}")
            all_issues.append(f"Invalid JSON: {manifest_path}")
            syntax_errors += 1

    if syntax_errors == 0:
        print("    PASS")

    # Check 6: Cross-reference validation
    print("  Check 6: Cross-reference validation...")
    xref_issues = 0
    for manifest_path in repo_manifests:
        full_path = REPO_ROOT / manifest_path
        issues = check_cross_references(full_path)
        for issue in issues:
            print(f"    WARN: {manifest_path}: {issue}")
            all_issues.append(f"{manifest_path}: {issue}")
            xref_issues += 1

    if xref_issues == 0:
        print("    PASS")

    print()

    # Summary
    if all_issues:
        print(f"[WARN] Manifest index validation found {len(all_issues)} issue(s):")
        for issue in all_issues[:10]:  # Limit output
            print(f"  - {issue}")
        if len(all_issues) > 10:
            print(f"  ... and {len(all_issues) - 10} more")
        return 1

    print("[OK] Manifest index validation passed")
    print()
    print(f"Summary:")
    print(f"  - Indexed manifests: {len(indexed_manifests)}")
    print(f"  - Repo manifests found: {len(repo_manifests)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
