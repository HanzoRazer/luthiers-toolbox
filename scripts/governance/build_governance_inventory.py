#!/usr/bin/env python3
"""
Build Governance Inventory

Scans docs/governance/ and classifies documents by operational status:
- enforced: run by CI and can fail CI
- consumed: loaded/referenced by code or scripts
- advisory: documented or reported but non-blocking
- orphaned: references missing files/scripts/concepts OR is referenced nowhere

Usage:
    python scripts/governance/build_governance_inventory.py [--json-output PATH] [--md-output PATH]

Part of Governance Execution Alignment Sprint.
"""

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

REPO_ROOT = Path(__file__).parent.parent.parent
GOVERNANCE_DIR = REPO_ROOT / "docs" / "governance"
SCRIPTS_DIR = REPO_ROOT / "scripts"
SERVICES_DIR = REPO_ROOT / "services"
PACKAGES_DIR = REPO_ROOT / "packages"


@dataclass
class DocClassification:
    """Classification result for a governance document."""
    path: str
    filename: str
    category: str  # enforced, consumed, advisory, orphaned
    reasons: List[str] = field(default_factory=list)
    references_from: List[str] = field(default_factory=list)
    references_to: List[str] = field(default_factory=list)
    missing_refs: List[str] = field(default_factory=list)


def load_check_all_scripts() -> Set[str]:
    """Load scripts referenced in check_all.py."""
    check_all = REPO_ROOT / "scripts" / "governance" / "check_all.py"
    scripts = set()

    if not check_all.exists():
        return scripts

    content = check_all.read_text(encoding="utf-8", errors="ignore")

    # Extract script paths from GOVERNANCE_CHECKS tuple
    pattern = r'"(scripts/[^"]+\.py)"'
    for match in re.finditer(pattern, content):
        scripts.add(match.group(1))

    return scripts


def load_policy_checks() -> Dict[str, dict]:
    """Load checks from ontology_ci_policy.json."""
    policy_file = GOVERNANCE_DIR / "ontology" / "ontology_ci_policy.json"

    if not policy_file.exists():
        return {}

    try:
        data = json.loads(policy_file.read_text())
        return data.get("checks", {})
    except Exception:
        return {}


def get_blocking_scripts() -> Set[str]:
    """Get scripts that are blocking in CI."""
    blocking = set()

    # From check_all.py - scripts with blocking=True
    check_all = REPO_ROOT / "scripts" / "governance" / "check_all.py"
    if check_all.exists():
        content = check_all.read_text(encoding="utf-8", errors="ignore")
        # Pattern: ("scripts/...", "description", True, tier)
        pattern = r'\("(scripts/[^"]+\.py)",\s*"[^"]+",\s*True'
        for match in re.finditer(pattern, content):
            blocking.add(match.group(1))

    # From ontology_ci_policy.json - checks with severity=blocking
    policy_checks = load_policy_checks()
    for check_name, check_info in policy_checks.items():
        if check_info.get("severity") == "blocking" and check_info.get("active", False):
            script = check_info.get("script", "")
            if script:
                blocking.add(script)

    return blocking


def get_advisory_scripts() -> Set[str]:
    """Get scripts that are advisory/warning in CI."""
    advisory = set()

    policy_checks = load_policy_checks()
    for check_name, check_info in policy_checks.items():
        severity = check_info.get("severity", "")
        if severity in ("advisory", "warning", "informational") and check_info.get("active", False):
            script = check_info.get("script", "")
            if script:
                advisory.add(script)

    return advisory


def find_references_to_file(filepath: Path) -> List[str]:
    """Find code/script references to a governance file."""
    references = []
    filename = filepath.name
    relative_path = str(filepath.relative_to(REPO_ROOT)).replace("\\", "/")

    # Search patterns
    patterns = [filename, relative_path]

    for pattern in patterns:
        try:
            result = subprocess.run(
                ["git", "grep", "-l", "--", pattern],
                capture_output=True,
                text=True,
                cwd=str(REPO_ROOT),
                timeout=30
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split("\n"):
                    if line and line != str(filepath.relative_to(REPO_ROOT)):
                        references.append(line)
        except Exception:
            pass

    return list(set(references))


def find_missing_references(filepath: Path) -> List[str]:
    """Find references in a doc that point to missing files."""
    missing = []

    if not filepath.suffix == ".md":
        return missing

    try:
        content = filepath.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return missing

    # Find markdown links
    link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    for match in re.finditer(link_pattern, content):
        link_text, link_path = match.groups()

        # Skip external URLs
        if link_path.startswith(("http://", "https://", "mailto:", "#")):
            continue

        # Resolve relative path
        if link_path.startswith("./"):
            target = filepath.parent / link_path[2:]
        elif link_path.startswith("../"):
            target = filepath.parent / link_path
        elif link_path.startswith("/"):
            target = REPO_ROOT / link_path[1:]
        else:
            target = filepath.parent / link_path

        # Remove anchor
        target_str = str(target).split("#")[0]
        target = Path(target_str)

        if not target.exists():
            missing.append(link_path)

    return missing


def classify_governance_doc(filepath: Path,
                            blocking_scripts: Set[str],
                            advisory_scripts: Set[str],
                            all_ci_scripts: Set[str]) -> DocClassification:
    """Classify a governance document."""
    relative_path = str(filepath.relative_to(REPO_ROOT)).replace("\\", "/")

    result = DocClassification(
        path=relative_path,
        filename=filepath.name,
        category="orphaned",
        reasons=[],
        references_from=[],
        references_to=[],
        missing_refs=[]
    )

    # Check for references to this file
    result.references_from = find_references_to_file(filepath)

    # Check for missing references in this file
    result.missing_refs = find_missing_references(filepath)

    # Determine category

    # 1. Check if this is an enforced JSON (policy, registry loaded by blocking scripts)
    if filepath.suffix == ".json":
        # Is this loaded by a blocking script?
        for ref in result.references_from:
            # Normalize path for comparison
            ref_normalized = ref.replace("\\", "/")
            if any(script in ref_normalized for script in blocking_scripts):
                result.category = "enforced"
                result.reasons.append(f"Loaded by blocking script")
                return result
            if any(script in ref_normalized for script in advisory_scripts):
                result.category = "advisory"
                result.reasons.append(f"Loaded by advisory script")
                return result

    # 2. Check if this is governance policy itself
    if filepath.name == "ontology_ci_policy.json":
        result.category = "enforced"
        result.reasons.append("CI policy definition")
        return result

    # 3. Check if referenced by code in services/ or packages/
    code_refs = [r for r in result.references_from
                 if r.startswith(("services/", "packages/"))]
    if code_refs:
        result.category = "consumed"
        result.reasons.append(f"Referenced by {len(code_refs)} code file(s)")
        return result

    # 4. Check if referenced by scripts
    script_refs = [r for r in result.references_from
                   if r.startswith("scripts/")]
    if script_refs:
        result.category = "advisory"
        result.reasons.append(f"Referenced by {len(script_refs)} script(s)")
        return result

    # 5. Check if referenced by other governance docs
    gov_refs = [r for r in result.references_from
                if r.startswith("docs/governance/")]
    if gov_refs:
        result.category = "advisory"
        result.reasons.append(f"Referenced by {len(gov_refs)} governance doc(s)")
        return result

    # 6. Check for missing references (orphan signal)
    if result.missing_refs:
        result.reasons.append(f"{len(result.missing_refs)} broken link(s)")

    # 7. No references at all = orphaned
    if not result.references_from:
        result.reasons.append("No code/script references found")

    return result


def scan_governance_docs() -> List[DocClassification]:
    """Scan all governance docs and classify them."""
    results = []

    blocking_scripts = get_blocking_scripts()
    advisory_scripts = get_advisory_scripts()
    all_ci_scripts = load_check_all_scripts()

    # Scan markdown files
    for md_file in GOVERNANCE_DIR.glob("**/*.md"):
        result = classify_governance_doc(
            md_file, blocking_scripts, advisory_scripts, all_ci_scripts
        )
        results.append(result)

    # Scan JSON files
    for json_file in GOVERNANCE_DIR.glob("**/*.json"):
        result = classify_governance_doc(
            json_file, blocking_scripts, advisory_scripts, all_ci_scripts
        )
        results.append(result)

    return results


def build_summary(results: List[DocClassification]) -> Dict:
    """Build summary statistics."""
    by_category = {}
    for r in results:
        by_category.setdefault(r.category, []).append(r.path)

    return {
        "total_docs": len(results),
        "enforced": len(by_category.get("enforced", [])),
        "consumed": len(by_category.get("consumed", [])),
        "advisory": len(by_category.get("advisory", [])),
        "orphaned": len(by_category.get("orphaned", [])),
        "docs_with_broken_links": sum(1 for r in results if r.missing_refs),
    }


def generate_json_report(results: List[DocClassification]) -> Dict:
    """Generate JSON report."""
    return {
        "generated_at": datetime.now().isoformat(),
        "scan_scope": "docs/governance/",
        "summary": build_summary(results),
        "documents": [
            {
                "path": r.path,
                "filename": r.filename,
                "category": r.category,
                "reasons": r.reasons,
                "referenced_by": r.references_from[:10],  # Limit
                "broken_links": r.missing_refs[:10],
            }
            for r in sorted(results, key=lambda x: (x.category, x.path))
        ]
    }


def generate_markdown_report(results: List[DocClassification]) -> str:
    """Generate markdown report."""
    summary = build_summary(results)

    lines = [
        "# Governance Document Inventory",
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"Scope: `docs/governance/`",
        "",
        "## Summary",
        "",
        f"| Category | Count |",
        f"|----------|-------|",
        f"| Enforced | {summary['enforced']} |",
        f"| Consumed | {summary['consumed']} |",
        f"| Advisory | {summary['advisory']} |",
        f"| Orphaned | {summary['orphaned']} |",
        f"| **Total** | **{summary['total_docs']}** |",
        "",
        f"Documents with broken links: {summary['docs_with_broken_links']}",
        "",
        "## Classification Definitions",
        "",
        "- **Enforced**: Run by CI and can fail CI",
        "- **Consumed**: Loaded/referenced by code or scripts",
        "- **Advisory**: Documented or reported but non-blocking",
        "- **Orphaned**: References missing files OR is referenced nowhere",
        "",
    ]

    # Group by category
    by_category = {}
    for r in results:
        by_category.setdefault(r.category, []).append(r)

    for category in ["enforced", "consumed", "advisory", "orphaned"]:
        docs = by_category.get(category, [])
        if not docs:
            continue

        lines.append(f"## {category.title()} ({len(docs)})")
        lines.append("")

        for doc in sorted(docs, key=lambda x: x.path):
            lines.append(f"### `{doc.filename}`")
            lines.append(f"- Path: `{doc.path}`")
            if doc.reasons:
                lines.append(f"- Reason: {'; '.join(doc.reasons)}")
            if doc.references_from:
                refs = doc.references_from[:5]
                lines.append(f"- Referenced by: {', '.join(f'`{r}`' for r in refs)}")
                if len(doc.references_from) > 5:
                    lines.append(f"  - ... and {len(doc.references_from) - 5} more")
            if doc.missing_refs:
                lines.append(f"- Broken links: {', '.join(doc.missing_refs[:5])}")
            lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Build governance document inventory")
    parser.add_argument(
        "--json-output",
        type=str,
        default="reports/governance/governance_inventory.json",
        help="Path for JSON output (default: reports/governance/governance_inventory.json)"
    )
    parser.add_argument(
        "--md-output",
        type=str,
        default="reports/governance/governance_inventory.md",
        help="Path for Markdown output (default: reports/governance/governance_inventory.md)"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress human-readable output"
    )
    args = parser.parse_args()

    if not args.quiet:
        print("Scanning governance documents...")

    results = scan_governance_docs()
    summary = build_summary(results)

    # Write JSON
    json_path = REPO_ROOT / args.json_output
    json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(generate_json_report(results), f, indent=2)

    # Write Markdown
    md_path = REPO_ROOT / args.md_output
    md_path.parent.mkdir(parents=True, exist_ok=True)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(generate_markdown_report(results))

    if not args.quiet:
        print()
        print("=" * 50)
        print("GOVERNANCE INVENTORY")
        print("=" * 50)
        print(f"  Total documents:  {summary['total_docs']}")
        print(f"  Enforced:         {summary['enforced']}")
        print(f"  Consumed:         {summary['consumed']}")
        print(f"  Advisory:         {summary['advisory']}")
        print(f"  Orphaned:         {summary['orphaned']}")
        print()
        print(f"Reports written to:")
        print(f"  {args.json_output}")
        print(f"  {args.md_output}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
