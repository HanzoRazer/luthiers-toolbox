#!/usr/bin/env python3
"""
Sprint Namespace Check Script

Detects dev order references without proper namespace prefixes
in docs/handoffs/ and docs/governance/ directories.

Usage:
    python scripts/check_sprint_namespace.py

Exit codes:
    0 - No violations found (or warnings only)

Note: This script warns but does not fail for this first pass.

Part of MRP-1A Governance Enforcement Infrastructure.
"""

import re
import sys
from pathlib import Path


# Valid namespace prefixes per SPRINT_NAMESPACE_STANDARD.md
VALID_NAMESPACES = {
    "VECTOR",
    "IBG",
    "BOE",
    "DXF",
    "CAM",
    "RMOS",
    "SPIRAL",
    "MRP",
}

# Pattern for properly namespaced references (e.g., VECTOR-1A, MRP-1A, CAM-6B)
NAMESPACED_PATTERN = re.compile(
    r'\b(' + '|'.join(VALID_NAMESPACES) + r')-\d+[A-Z]?\b'
)

# Pattern for unnamespaced dev order references
UNNAMESPACED_PATTERNS = [
    re.compile(r'\bDev Order \d+\b', re.IGNORECASE),
    re.compile(r'\bOrder \d+[A-Z]?\b'),
    re.compile(r'\bSprint \d+[A-Z]?\b(?!\s*\()'),  # Sprint 5G but not Sprint 9 (date)
]

# Directories to check
CHECK_DIRS = [
    "docs/handoffs/",
    "docs/governance/",
]


def find_unnamespaced_references(file_path: Path) -> list[tuple[int, str, str]]:
    """
    Find unnamespaced dev order references in a file.

    Returns:
        List of (line_number, line_text, matched_pattern) tuples
    """
    violations = []

    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception:
        return violations

    for line_num, line in enumerate(content.split("\n"), start=1):
        # Skip lines that contain properly namespaced references
        if NAMESPACED_PATTERN.search(line):
            continue

        # Check for unnamespaced patterns
        for pattern in UNNAMESPACED_PATTERNS:
            match = pattern.search(line)
            if match:
                violations.append((line_num, line.strip(), match.group()))

    return violations


def check_namespace() -> int:
    """
    Main check function.

    Returns:
        0 always (warn-only mode)
    """
    repo_root = Path(__file__).parent.parent

    all_violations = []

    for check_dir in CHECK_DIRS:
        dir_path = repo_root / check_dir
        if not dir_path.exists():
            continue

        for md_file in dir_path.glob("*.md"):
            violations = find_unnamespaced_references(md_file)
            if violations:
                all_violations.append((md_file, violations))

    if not all_violations:
        return 0

    print("[WARN] Unnamespaced dev order references found:")
    print()

    for file_path, violations in all_violations:
        rel_path = file_path.relative_to(repo_root)
        print(f"  File: {rel_path}")
        for line_num, line_text, matched in violations:
            print(f"    Line {line_num}: '{matched}'")
            if len(line_text) > 80:
                line_text = line_text[:77] + "..."
            print(f"      Context: {line_text}")
        print()

    print("Valid namespace prefixes: " + ", ".join(sorted(VALID_NAMESPACES)))
    print("Example: VECTOR-1A, IBG-1, MRP-1A, CAM-6B")
    print()
    print("Note: This is a warning only. CI will not fail.")

    return 0  # Warn-only for now


if __name__ == "__main__":
    sys.exit(check_namespace())
