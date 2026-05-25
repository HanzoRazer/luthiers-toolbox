#!/usr/bin/env python3
"""
CAM Assist Strategy Package Archive CLI

Archives a validated strategy package directory into a portable .zip file.

This is non-execution infrastructure. It does not generate G-code,
produce machine output, or mutate package contents.

Usage:
    python scripts/archive_strategy_package.py examples/packages/fret_slot_strategy_example/
    python scripts/archive_strategy_package.py <package_dir> --out /tmp/archive.zip
    python scripts/archive_strategy_package.py <package_dir> --out /tmp/archive.zip --force

Exit codes:
    0 — Archive created
    1 — Validation failure
    2 — File/read/write/archive error
"""

import argparse
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from inspect_strategy_package import inspect_package


def archive_package(
    package_dir: Path,
    output_path: Path,
    force: bool = False,
) -> tuple[bool, str, list[str]]:
    """
    Archive a validated strategy package to a zip file.

    Returns (success, message, warnings).
    """
    warnings: list[str] = []

    # Check package directory
    if not package_dir.exists():
        return False, f"Package directory not found: {package_dir}", warnings

    if not package_dir.is_dir():
        return False, f"Not a directory: {package_dir}", warnings

    # Check output path
    if output_path.exists() and not force:
        return (
            False,
            f"Archive already exists: {output_path} (use --force to overwrite)",
            warnings,
        )

    # Inspect package
    result = inspect_package(package_dir)

    if not result.valid:
        errors = "; ".join(result.errors)
        return False, f"Package validation failed: {errors}", warnings

    # Collect warnings from inspection
    warnings.extend(result.warnings)

    # Collect all files in package directory
    files_to_archive: list[Path] = []
    for item in package_dir.rglob("*"):
        if item.is_file():
            files_to_archive.append(item)

    if not files_to_archive:
        return False, "No files found in package directory", warnings

    # Create archive
    try:
        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for file_path in files_to_archive:
                # Use package-relative path (flat structure)
                arcname = file_path.relative_to(package_dir)
                zf.write(file_path, arcname)

    except OSError as e:
        return False, f"Failed to create archive: {e}", warnings
    except zipfile.BadZipFile as e:
        return False, f"Archive error: {e}", warnings

    return True, f"Archive created: {output_path}", warnings


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Archive a CAM Assist strategy package to .zip",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "package_dir",
        type=Path,
        help="Path to the strategy package directory",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output path for the archive (default: <package_dir>.zip)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing archive",
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Only print pass/fail summary",
    )

    args = parser.parse_args()
    package_dir: Path = args.package_dir

    if not package_dir.exists():
        print(f"Error: Package directory not found: {package_dir}", file=sys.stderr)
        return 2

    # Determine output path
    if args.out:
        output_path = args.out
    else:
        output_path = package_dir.parent / f"{package_dir.name}.zip"

    success, message, warnings = archive_package(package_dir, output_path, args.force)

    if success:
        if args.quiet:
            print(f"PASS: {output_path}")
        else:
            print(f"PASS: {message}")
            for warning in warnings:
                print(f"  [WARN] {warning}")
        return 0
    else:
        if args.quiet:
            print(f"FAIL: {package_dir}", file=sys.stderr)
        else:
            print(f"FAIL: {message}", file=sys.stderr)
            for warning in warnings:
                print(f"  [WARN] {warning}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
