#!/usr/bin/env python3
"""
CAM Assist Strategy Package Import Staging CLI

Validates a strategy package .zip archive and stages it into a local review directory.

This is non-execution infrastructure. It does not generate G-code,
produce machine output, execute archive contents, or modify package files.

Usage:
    python scripts/stage_strategy_package.py package.zip
    python scripts/stage_strategy_package.py package.zip --out ./custom_staging/
    python scripts/stage_strategy_package.py package.zip --out ./staging/ --force
    python scripts/stage_strategy_package.py package.zip --quiet

Exit codes:
    0 — Package staged
    1 — Validation failure
    2 — File/read/write/extract error
"""

import argparse
import shutil
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from validate_package_archive import validate_archive, check_path_safety

DEFAULT_STAGING_ROOT = Path("staged_packages")


def stage_package(
    archive_path: Path,
    output_root: Path,
    force: bool = False,
) -> tuple[bool, str, list[str]]:
    """
    Validate and stage a strategy package archive.

    Returns (success, message, warnings).
    """
    warnings: list[str] = []

    if not archive_path.exists():
        return False, f"Archive not found: {archive_path}", warnings

    if not archive_path.is_file():
        return False, f"Not a file: {archive_path}", warnings

    validation_result = validate_archive(archive_path)

    if not validation_result.valid:
        errors = []
        errors.extend(validation_result.archive_errors)
        if validation_result.package_result:
            errors.extend(validation_result.package_result.errors)
        error_msg = "; ".join(errors) if errors else "Validation failed"
        return False, f"Archive validation failed: {error_msg}", warnings

    warnings.extend(validation_result.archive_warnings)
    if validation_result.package_result:
        warnings.extend(validation_result.package_result.warnings)

    package_name = archive_path.stem
    staged_dir = output_root / package_name

    if staged_dir.exists():
        if not force:
            return (
                False,
                f"Staged directory already exists: {staged_dir} (use --force to overwrite)",
                warnings,
            )
        try:
            shutil.rmtree(staged_dir)
        except OSError as e:
            return False, f"Failed to remove existing directory: {e}", warnings

    try:
        output_root.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        return False, f"Failed to create output root: {e}", warnings

    try:
        with zipfile.ZipFile(archive_path, "r") as zf:
            for name in zf.namelist():
                safe, error = check_path_safety(name)
                if not safe:
                    return False, f"Unsafe path in archive: {error}", warnings

            zf.extractall(staged_dir)
    except zipfile.BadZipFile as e:
        return False, f"Invalid zip archive: {e}", warnings
    except OSError as e:
        return False, f"Failed to extract archive: {e}", warnings

    required_files = ["manifest.json", "strategy.json", "review_packet.md"]
    for req_file in required_files:
        if not (staged_dir / req_file).exists():
            try:
                shutil.rmtree(staged_dir)
            except OSError:
                pass
            return False, f"Staged package missing required file: {req_file}", warnings

    return True, f"Package staged: {staged_dir}", warnings


def format_terminal_output(
    success: bool,
    message: str,
    warnings: list[str],
    archive_path: Path,
    staged_dir: Path | None,
) -> str:
    """Format staging result for terminal display."""
    lines = []

    if success:
        lines.append(f"PASS: {message}")
    else:
        lines.append(f"FAIL: {message}")

    lines.append("")
    lines.append(f"Archive: {archive_path}")

    if staged_dir and staged_dir.exists():
        lines.append(f"Staged to: {staged_dir}")

        file_count = sum(1 for _ in staged_dir.rglob("*") if _.is_file())
        lines.append(f"Files staged: {file_count}")

    if warnings:
        lines.append("")
        lines.append("Warnings:")
        for warning in warnings:
            lines.append(f"  [WARN] {warning}")

    lines.append("")
    lines.append("-" * 50)
    lines.append("This staging command does not execute package contents.")
    lines.append("Human review is required before downstream use.")

    return "\n".join(lines)


def format_quiet_output(success: bool, message: str) -> str:
    """Format minimal pass/fail output."""
    if success:
        return f"PASS: {message}"
    else:
        return f"FAIL: {message}"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Stage CAM Assist strategy package archive for review",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "archive",
        type=Path,
        help="Path to the .zip archive to stage",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_STAGING_ROOT,
        help=f"Output root directory for staged packages (default: {DEFAULT_STAGING_ROOT})",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing staged directory",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Only print pass/fail summary",
    )

    args = parser.parse_args()
    archive_path: Path = args.archive
    output_root: Path = args.out

    if not archive_path.exists():
        print(f"Error: Archive not found: {archive_path}", file=sys.stderr)
        return 2

    success, message, warnings = stage_package(archive_path, output_root, args.force)

    staged_dir = output_root / archive_path.stem if success else None

    if args.quiet:
        output = format_quiet_output(success, message)
        if success:
            print(output)
        else:
            print(output, file=sys.stderr)
    else:
        output = format_terminal_output(
            success, message, warnings, archive_path, staged_dir
        )
        if success:
            print(output)
        else:
            print(output, file=sys.stderr)

    if not success:
        if "not found" in message.lower() or "not a file" in message.lower():
            return 2
        if "extract" in message.lower() or "create" in message.lower():
            return 2
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
