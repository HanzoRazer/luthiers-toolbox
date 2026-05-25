#!/usr/bin/env python3
"""
CAM Assist Strategy Package Index Generator

Scans a directory for strategy packages and generates a Markdown index.

This is a read-only utility. It does not mutate individual package contents.
It may write collection-level metadata (INDEX.md, index.json) to the input directory.

Usage:
    python scripts/index_strategy_packages.py examples/packages/
    python scripts/index_strategy_packages.py examples/packages/ --out /tmp/index.md
    python scripts/index_strategy_packages.py examples/packages/ --json-out index.json

Exit codes:
    0 — Index generated (even if some packages invalid)
    1 — No packages found
    2 — File/read/write error
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import NamedTuple

sys.path.insert(0, str(Path(__file__).parent))

from inspect_strategy_package import inspect_package, InspectionResult


class PackageEntry(NamedTuple):
    path: Path
    name: str
    result: InspectionResult


def discover_packages(root_dir: Path) -> list[Path]:
    """Recursively find all directories containing manifest.json."""
    packages = []
    for manifest_path in root_dir.rglob("manifest.json"):
        packages.append(manifest_path.parent)
    return sorted(packages)


def index_packages(root_dir: Path) -> list[PackageEntry]:
    """Discover and inspect all packages in a directory."""
    package_dirs = discover_packages(root_dir)
    entries = []

    for pkg_dir in package_dirs:
        result = inspect_package(pkg_dir)
        name = pkg_dir.name
        entries.append(PackageEntry(path=pkg_dir, name=name, result=result))

    return entries


def generate_markdown_index(
    entries: list[PackageEntry],
    root_dir: Path,
) -> str:
    """Generate Markdown index content."""
    lines = []
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Header
    lines.append("# CAM Assist Strategy Package Index")
    lines.append("")
    lines.append(f"Generated at: {timestamp}")
    lines.append("")

    # Summary
    total = len(entries)
    valid = sum(1 for e in entries if e.result.valid)
    invalid = total - valid
    warning_count = sum(len(e.result.warnings) for e in entries)

    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Total packages: {total}")
    lines.append(f"- Valid packages: {valid}")
    lines.append(f"- Invalid packages: {invalid}")
    lines.append(f"- Total warnings: {warning_count}")
    lines.append("")

    # Packages table
    lines.append("## Packages")
    lines.append("")

    if entries:
        lines.append("| Package | Operation | Status | Human Review | Warnings |")
        lines.append("|---------|-----------|--------|--------------|----------|")

        for entry in entries:
            name = entry.name
            op_type = entry.result.operation_type or "unknown"
            status = "valid" if entry.result.valid else "INVALID"

            if entry.result.authority:
                human_review = (
                    "required"
                    if entry.result.authority.get("requires_human_review")
                    else "not specified"
                )
            else:
                human_review = "unknown"

            warn_count = len(entry.result.warnings)
            warnings_str = str(warn_count) if warn_count > 0 else "none"

            lines.append(
                f"| {name} | {op_type} | {status} | {human_review} | {warnings_str} |"
            )

        lines.append("")
    else:
        lines.append("No packages found.")
        lines.append("")

    # Non-execution notice
    lines.append("---")
    lines.append("")
    lines.append("## Non-Execution Notice")
    lines.append("")
    lines.append("These packages are advisory only.")
    lines.append("They do not authorize machine execution.")
    lines.append("Human review and downstream CAM verification are required.")
    lines.append("")

    return "\n".join(lines)


def generate_json_index(
    entries: list[PackageEntry],
    root_dir: Path,
) -> dict:
    """Generate JSON index data."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    total = len(entries)
    valid = sum(1 for e in entries if e.result.valid)
    invalid = total - valid
    warning_count = sum(len(e.result.warnings) for e in entries)

    packages = []
    for entry in entries:
        # Make path relative to root_dir
        try:
            rel_path = entry.path.relative_to(root_dir)
        except ValueError:
            rel_path = entry.path

        human_review = None
        if entry.result.authority:
            human_review = entry.result.authority.get("requires_human_review")

        packages.append({
            "path": str(rel_path),
            "name": entry.name,
            "operation_type": entry.result.operation_type,
            "status": "valid" if entry.result.valid else "invalid",
            "requires_human_review": human_review,
            "warnings": entry.result.warnings,
        })

    return {
        "generated_at": timestamp,
        "summary": {
            "total": total,
            "valid": valid,
            "invalid": invalid,
            "warnings": warning_count,
        },
        "packages": packages,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate index of CAM Assist strategy packages",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "packages_dir",
        type=Path,
        help="Directory containing strategy packages",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output path for Markdown index (default: <packages_dir>/INDEX.md)",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=None,
        help="Output path for JSON index",
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Only print summary, not full index",
    )

    args = parser.parse_args()
    packages_dir: Path = args.packages_dir

    if not packages_dir.exists():
        print(f"Error: Directory not found: {packages_dir}", file=sys.stderr)
        return 2

    if not packages_dir.is_dir():
        print(f"Error: Not a directory: {packages_dir}", file=sys.stderr)
        return 2

    # Index packages
    entries = index_packages(packages_dir)

    if not entries:
        print("No packages found.", file=sys.stderr)
        return 1

    # Generate Markdown
    markdown_content = generate_markdown_index(entries, packages_dir)

    # Determine output path
    if args.out:
        md_output_path = args.out
    else:
        md_output_path = packages_dir / "INDEX.md"

    # Write Markdown
    try:
        with open(md_output_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)
    except OSError as e:
        print(f"Error writing index: {e}", file=sys.stderr)
        return 2

    # Write JSON if requested
    if args.json_out:
        json_data = generate_json_index(entries, packages_dir)
        try:
            with open(args.json_out, "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=2)
                f.write("\n")
        except OSError as e:
            print(f"Error writing JSON index: {e}", file=sys.stderr)
            return 2

    # Output summary
    valid = sum(1 for e in entries if e.result.valid)
    invalid = len(entries) - valid

    if args.quiet:
        print(f"Indexed {len(entries)} packages ({valid} valid, {invalid} invalid)")
    else:
        print(f"PASS: Index generated: {md_output_path}")
        print(f"  Packages: {len(entries)} ({valid} valid, {invalid} invalid)")
        if args.json_out:
            print(f"  JSON: {args.json_out}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
