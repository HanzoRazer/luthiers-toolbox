#!/usr/bin/env python3
"""
CAM Assist Staged Package Review Queue Index Generator

Scans a staged package root and generates a review queue index for human operators.

This is a read-only utility. It does not mutate staged package contents.
It writes collection-level queue output (REVIEW_QUEUE.md, review_queue.json).

Usage:
    python scripts/index_staged_packages.py staged_packages/
    python scripts/index_staged_packages.py staged_packages/ --out /tmp/review_queue.md
    python scripts/index_staged_packages.py staged_packages/ --json-out /tmp/review_queue.json
    python scripts/index_staged_packages.py staged_packages/ --quiet

Exit codes:
    0 — Review queue generated
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


class StagedPackageEntry(NamedTuple):
    path: Path
    relative_path: str
    result: InspectionResult


def discover_staged_packages(staged_root: Path) -> list[Path]:
    """Recursively find all directories containing manifest.json."""
    packages = []
    for manifest_path in staged_root.rglob("manifest.json"):
        packages.append(manifest_path.parent)
    return sorted(packages)


def index_staged_packages(staged_root: Path) -> list[StagedPackageEntry]:
    """Discover and inspect all staged packages."""
    package_dirs = discover_staged_packages(staged_root)
    entries = []

    for pkg_dir in package_dirs:
        result = inspect_package(pkg_dir)
        try:
            relative_path = str(pkg_dir.relative_to(staged_root))
        except ValueError:
            relative_path = pkg_dir.name
        entries.append(StagedPackageEntry(
            path=pkg_dir,
            relative_path=relative_path,
            result=result,
        ))

    return entries


def get_human_review_status(result: InspectionResult) -> tuple[bool, str]:
    """Get human review status and display string."""
    if result.authority:
        requires_review = result.authority.get("requires_human_review")
        if requires_review is True:
            return True, "Yes"
        elif requires_review is False:
            return False, "No [INVALID]"
        else:
            return False, "Missing [INVALID]"
    return False, "Missing [INVALID]"


def generate_markdown_queue(
    entries: list[StagedPackageEntry],
    staged_root: Path,
) -> str:
    """Generate Markdown review queue content."""
    lines = []
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    lines.append("# CAM Assist Staged Package Review Queue")
    lines.append("")
    lines.append(f"Generated at: {timestamp}")
    lines.append("")

    total = len(entries)
    valid = sum(1 for e in entries if e.result.valid)
    invalid = total - valid
    requires_review = sum(
        1 for e in entries
        if e.result.authority and e.result.authority.get("requires_human_review") is True
    )
    warning_count = sum(len(e.result.warnings) for e in entries)

    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Total staged packages: {total}")
    lines.append(f"- Valid packages: {valid}")
    lines.append(f"- Invalid packages: {invalid}")
    lines.append(f"- Packages requiring human review: {requires_review}")
    lines.append(f"- Warning count: {warning_count}")
    lines.append("")

    lines.append("## Packages")
    lines.append("")
    lines.append("| Package | Operation | Status | Human Review Required | Warnings |")
    lines.append("|---------|-----------|--------|----------------------|----------|")

    for entry in entries:
        pkg_path = entry.relative_path
        operation = entry.result.operation_type or "unknown"
        status = "valid" if entry.result.valid else "invalid"
        _, review_display = get_human_review_status(entry.result)
        warning_count = len(entry.result.warnings)

        lines.append(
            f"| {pkg_path} | {operation} | {status} | {review_display} | {warning_count} |"
        )

    lines.append("")

    if any(not e.result.valid for e in entries):
        lines.append("## Invalid Package Details")
        lines.append("")
        for entry in entries:
            if not entry.result.valid:
                lines.append(f"### {entry.relative_path}")
                lines.append("")
                for error in entry.result.errors:
                    lines.append(f"- [ERROR] {error}")
                lines.append("")

    if any(e.result.warnings for e in entries):
        lines.append("## Warnings")
        lines.append("")
        for entry in entries:
            if entry.result.warnings:
                lines.append(f"### {entry.relative_path}")
                lines.append("")
                for warning in entry.result.warnings:
                    lines.append(f"- [WARN] {warning}")
                lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## Non-Execution Notice")
    lines.append("")
    lines.append("This review queue is advisory only.")
    lines.append("It does not approve, authorize, execute, or modify packages.")
    lines.append("Human review is required before any downstream CAM use.")

    return "\n".join(lines)


def generate_json_queue(
    entries: list[StagedPackageEntry],
) -> dict:
    """Generate JSON review queue structure."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    total = len(entries)
    valid = sum(1 for e in entries if e.result.valid)
    invalid = total - valid
    requires_review = sum(
        1 for e in entries
        if e.result.authority and e.result.authority.get("requires_human_review") is True
    )
    warning_count = sum(len(e.result.warnings) for e in entries)

    packages = []
    for entry in entries:
        requires_human_review, _ = get_human_review_status(entry.result)
        pkg_data = {
            "path": entry.relative_path,
            "operation_type": entry.result.operation_type or "unknown",
            "status": "valid" if entry.result.valid else "invalid",
            "requires_human_review": requires_human_review,
            "warnings": entry.result.warnings,
        }
        if not entry.result.valid:
            pkg_data["errors"] = entry.result.errors
        packages.append(pkg_data)

    return {
        "generated_at": timestamp,
        "summary": {
            "total": total,
            "valid": valid,
            "invalid": invalid,
            "requires_human_review": requires_review,
            "warnings": warning_count,
        },
        "packages": packages,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate review queue index for staged CAM Assist packages",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "staged_root",
        type=Path,
        help="Path to the staged packages root directory",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output path for Markdown queue (default: <staged_root>/REVIEW_QUEUE.md)",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=None,
        help="Optional output path for JSON queue",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Only print pass/fail summary",
    )

    args = parser.parse_args()
    staged_root: Path = args.staged_root

    if not staged_root.exists():
        print(f"Error: Staged root not found: {staged_root}", file=sys.stderr)
        return 2

    if not staged_root.is_dir():
        print(f"Error: Not a directory: {staged_root}", file=sys.stderr)
        return 2

    entries = index_staged_packages(staged_root)

    if not entries:
        if args.quiet:
            print("FAIL: No staged packages found", file=sys.stderr)
        else:
            print(f"No staged packages found in: {staged_root}", file=sys.stderr)
        return 1

    md_output = args.out if args.out else staged_root / "REVIEW_QUEUE.md"

    try:
        md_content = generate_markdown_queue(entries, staged_root)
        md_output.parent.mkdir(parents=True, exist_ok=True)
        md_output.write_text(md_content, encoding="utf-8")
    except OSError as e:
        print(f"Error writing Markdown queue: {e}", file=sys.stderr)
        return 2

    if args.json_out:
        try:
            json_data = generate_json_queue(entries)
            args.json_out.parent.mkdir(parents=True, exist_ok=True)
            args.json_out.write_text(
                json.dumps(json_data, indent=2),
                encoding="utf-8",
            )
        except OSError as e:
            print(f"Error writing JSON queue: {e}", file=sys.stderr)
            return 2

    valid_count = sum(1 for e in entries if e.result.valid)
    total_count = len(entries)

    if args.quiet:
        print(f"PASS: Review queue generated ({valid_count}/{total_count} valid)")
    else:
        print(f"Review queue generated: {md_output}")
        print(f"  Total packages: {total_count}")
        print(f"  Valid: {valid_count}")
        print(f"  Invalid: {total_count - valid_count}")
        if args.json_out:
            print(f"  JSON output: {args.json_out}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
