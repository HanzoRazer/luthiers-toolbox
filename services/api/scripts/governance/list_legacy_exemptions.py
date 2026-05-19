#!/usr/bin/env python3
"""
Governance Utility: List Legacy Export Exemptions

Scans for modules with LEGACY_EXEMPT governance headers and validates
against the exemption matrix in docs/governance/LEGACY_EXPORT_EXEMPTION_POLICY.md.

Usage:
    python scripts/governance/list_legacy_exemptions.py
    python scripts/governance/list_legacy_exemptions.py --validate

MRP-4B: Translator Registry Integration
"""
import argparse
import re
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional

# Scan these directories for exemption headers
SCAN_DIRS = [
    "app",
    "scripts",
]

EXEMPTION_PATTERN = re.compile(
    r"#\s*GOVERNANCE:.*?"
    r"#\s*STATUS:\s*LEGACY_EXEMPT.*?"
    r"#\s*EXEMPTION:\s*(\w+).*?"
    r"#\s*REASON:\s*(.+?)(?:\n|$).*?"
    r"#\s*SUNSET:\s*(\S+)",
    re.DOTALL | re.IGNORECASE
)


@dataclass
class Exemption:
    """Represents a legacy export exemption."""
    module_path: str
    exemption_type: str
    reason: str
    sunset_date: str


def find_exemptions(base_path: Path) -> List[Exemption]:
    """Scan for modules with LEGACY_EXEMPT governance headers."""
    exemptions = []

    for scan_dir in SCAN_DIRS:
        scan_path = base_path / scan_dir
        if not scan_path.exists():
            continue

        for py_file in scan_path.rglob("*.py"):
            try:
                content = py_file.read_text(encoding="utf-8")
            except Exception:
                continue

            # Check for exemption header
            match = EXEMPTION_PATTERN.search(content)
            if match:
                rel_path = py_file.relative_to(base_path)
                exemptions.append(Exemption(
                    module_path=str(rel_path).replace("\\", "/"),
                    exemption_type=match.group(1).strip().lower(),
                    reason=match.group(2).strip(),
                    sunset_date=match.group(3).strip(),
                ))

    return exemptions


def list_exemptions(base_path: Path, validate: bool = False) -> int:
    """
    List legacy export exemptions.

    Args:
        base_path: Root of services/api
        validate: If True, validate against policy document

    Returns:
        Exit code (0 = success, 1 = validation errors)
    """
    exemptions = find_exemptions(base_path)

    print("\n" + "=" * 80)
    print("LEGACY EXPORT EXEMPTIONS")
    print("=" * 80)
    print(f"\n{'Module':<50} {'Type':<20} {'Sunset':<12}")
    print("-" * 80)

    for e in sorted(exemptions, key=lambda x: x.module_path):
        print(f"{e.module_path:<50} {e.exemption_type:<20} {e.sunset_date:<12}")
        print(f"  Reason: {e.reason}")

    print("-" * 80)
    print(f"Total: {len(exemptions)} exempted modules")

    # Summary by type
    by_type = {}
    for e in exemptions:
        by_type[e.exemption_type] = by_type.get(e.exemption_type, 0) + 1

    print("\nBy Exemption Type:")
    for t, count in sorted(by_type.items()):
        print(f"  {t}: {count}")

    if validate:
        # Load exemptions from policy document
        policy_path = base_path.parent / "docs" / "governance" / "LEGACY_EXPORT_EXEMPTION_POLICY.md"
        if not policy_path.exists():
            print(f"\nWARNING: Policy document not found: {policy_path}")
            return 1

        policy_content = policy_path.read_text(encoding="utf-8")

        # Check each code exemption appears in policy
        errors = []
        for e in exemptions:
            module_name = e.module_path.replace("/", ".").replace(".py", "")
            if module_name not in policy_content and e.module_path not in policy_content:
                errors.append(f"Module not in policy: {e.module_path}")

        if errors:
            print("\nVALIDATION ERRORS:")
            for err in errors:
                print(f"  - {err}")
            return 1

        print("\nValidation: PASSED (all exemptions documented in policy)")

    print()
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="List legacy export exemptions"
    )
    parser.add_argument(
        "--validate", "-v",
        action="store_true",
        help="Validate exemptions against policy document"
    )

    args = parser.parse_args()

    # Find base path (services/api)
    script_path = Path(__file__).resolve()
    base_path = script_path.parent.parent.parent

    try:
        return list_exemptions(base_path, validate=args.validate)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
