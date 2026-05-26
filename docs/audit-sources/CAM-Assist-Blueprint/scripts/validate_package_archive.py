#!/usr/bin/env python3
"""
CAM Assist Strategy Package Archive Validator CLI

Validates an archived CAM Assist strategy package .zip before import or review.

This is non-execution infrastructure. It does not generate G-code,
produce machine output, execute any archive contents, or modify the archive.

Usage:
    python scripts/validate_package_archive.py package.zip
    python scripts/validate_package_archive.py package.zip --json
    python scripts/validate_package_archive.py package.zip --quiet

Exit codes:
    0 — Archive is valid
    1 — Validation failure
    2 — File/read/archive error
"""

import argparse
import json
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

sys.path.insert(0, str(Path(__file__).parent))

from inspect_strategy_package import inspect_package, InspectionResult

CORE_ALLOWED_FILES = {"manifest.json", "strategy.json", "review_packet.md", "README.md"}
SUSPICIOUS_EXTENSIONS = {".py", ".exe", ".sh", ".bat", ".cmd", ".ps1", ".dll", ".so"}


class ArchiveValidationResult:
    def __init__(
        self,
        archive_valid: bool,
        package_valid: bool,
        archive_path: str,
        archive_errors: list[str],
        archive_warnings: list[str],
        package_result: InspectionResult | None = None,
    ):
        self.archive_valid = archive_valid
        self.package_valid = package_valid
        self.archive_path = archive_path
        self.archive_errors = archive_errors
        self.archive_warnings = archive_warnings
        self.package_result = package_result

    @property
    def valid(self) -> bool:
        return self.archive_valid and self.package_valid


def check_path_safety(name: str) -> tuple[bool, str | None]:
    """Check if a zip entry name is safe. Returns (safe, error_message)."""
    posix_path = PurePosixPath(name)

    if posix_path.is_absolute():
        return False, f"Absolute path in archive: {name}"

    if ".." in posix_path.parts:
        return False, f"Path traversal in archive: {name}"

    if name.startswith("/") or name.startswith("\\"):
        return False, f"Absolute path in archive: {name}"

    return True, None


def get_allowed_files(manifest_data: dict | None) -> set[str]:
    """Get set of allowed files based on manifest."""
    allowed = set(CORE_ALLOWED_FILES)

    if manifest_data:
        strategy_file = manifest_data.get("strategy_file")
        if strategy_file:
            allowed.add(strategy_file)

        review_file = manifest_data.get("review_packet_file")
        if review_file:
            allowed.add(review_file)

        geometry_files = manifest_data.get("source_geometry_files", [])
        for gf in geometry_files:
            allowed.add(gf)

    return allowed


def validate_archive(archive_path: Path) -> ArchiveValidationResult:
    """
    Validate a strategy package archive.

    Returns ArchiveValidationResult with validation status and details.
    """
    archive_errors: list[str] = []
    archive_warnings: list[str] = []

    if not archive_path.exists():
        return ArchiveValidationResult(
            archive_valid=False,
            package_valid=False,
            archive_path=str(archive_path),
            archive_errors=["Archive not found"],
            archive_warnings=[],
        )

    if not archive_path.is_file():
        return ArchiveValidationResult(
            archive_valid=False,
            package_valid=False,
            archive_path=str(archive_path),
            archive_errors=["Path is not a file"],
            archive_warnings=[],
        )

    try:
        zf = zipfile.ZipFile(archive_path, "r")
    except zipfile.BadZipFile:
        return ArchiveValidationResult(
            archive_valid=False,
            package_valid=False,
            archive_path=str(archive_path),
            archive_errors=["Not a valid zip file"],
            archive_warnings=[],
        )
    except Exception as e:
        return ArchiveValidationResult(
            archive_valid=False,
            package_valid=False,
            archive_path=str(archive_path),
            archive_errors=[f"Failed to open archive: {e}"],
            archive_warnings=[],
        )

    with zf:
        names = zf.namelist()

        for name in names:
            safe, error = check_path_safety(name)
            if not safe:
                archive_errors.append(error)

        if archive_errors:
            return ArchiveValidationResult(
                archive_valid=False,
                package_valid=False,
                archive_path=str(archive_path),
                archive_errors=archive_errors,
                archive_warnings=archive_warnings,
            )

        base_names = {Path(n).name for n in names if not n.endswith("/")}

        if "manifest.json" not in base_names:
            archive_errors.append("Archive missing manifest.json")

        if "strategy.json" not in base_names:
            archive_errors.append("Archive missing strategy.json")

        if "review_packet.md" not in base_names:
            archive_errors.append("Archive missing review_packet.md")

        if archive_errors:
            return ArchiveValidationResult(
                archive_valid=False,
                package_valid=False,
                archive_path=str(archive_path),
                archive_errors=archive_errors,
                archive_warnings=archive_warnings,
            )

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            try:
                zf.extractall(tmp_path)
            except Exception as e:
                return ArchiveValidationResult(
                    archive_valid=False,
                    package_valid=False,
                    archive_path=str(archive_path),
                    archive_errors=[f"Failed to extract archive: {e}"],
                    archive_warnings=archive_warnings,
                )

            manifest_data = None
            manifest_path = tmp_path / "manifest.json"
            if manifest_path.exists():
                try:
                    with open(manifest_path, "r", encoding="utf-8") as f:
                        manifest_data = json.load(f)
                except Exception:
                    pass

            allowed_files = get_allowed_files(manifest_data)

            for name in names:
                if name.endswith("/"):
                    continue

                file_name = Path(name).name
                path_parts = Path(name).parts

                if len(path_parts) == 1:
                    check_name = file_name
                else:
                    check_name = name

                if check_name not in allowed_files and file_name not in allowed_files:
                    ext = Path(file_name).suffix.lower()
                    if ext in SUSPICIOUS_EXTENSIONS:
                        archive_warnings.append(
                            f"HIGH: Suspicious file in archive: {name}"
                        )
                    else:
                        archive_warnings.append(f"Unexpected file in archive: {name}")

            package_result = inspect_package(tmp_path)

    return ArchiveValidationResult(
        archive_valid=True,
        package_valid=package_result.valid,
        archive_path=str(archive_path),
        archive_errors=archive_errors,
        archive_warnings=archive_warnings,
        package_result=package_result,
    )


def format_json_output(result: ArchiveValidationResult) -> str:
    """Format validation result as JSON."""
    output = {
        "archive_valid": result.archive_valid,
        "package_valid": result.package_valid,
        "archive_path": result.archive_path,
        "archive_errors": result.archive_errors,
        "archive_warnings": result.archive_warnings,
    }

    if result.package_result:
        output["package"] = {
            "package_type": result.package_result.package_type,
            "operation_type": result.package_result.operation_type,
            "manifest_version": result.package_result.manifest_version,
            "authority": result.package_result.authority,
            "files": result.package_result.files,
            "provenance": result.package_result.provenance,
        }
        output["package_warnings"] = result.package_result.warnings
        if result.package_result.errors:
            output["package_errors"] = result.package_result.errors

    return json.dumps(output, indent=2)


def format_terminal_output(result: ArchiveValidationResult) -> str:
    """Format validation result for terminal display."""
    lines = []

    if result.valid:
        lines.append("PASS: archive is a valid CAM Assist strategy package")
    else:
        lines.append("FAIL: archive validation failed")

    lines.append("")
    lines.append(f"Archive: {result.archive_path}")

    if result.archive_errors:
        lines.append("")
        lines.append("Archive Errors:")
        for error in result.archive_errors:
            lines.append(f"  [FAIL] {error}")

    if result.archive_warnings:
        lines.append("")
        lines.append("Archive Warnings:")
        for warning in result.archive_warnings:
            lines.append(f"  [WARN] {warning}")

    if result.package_result:
        if result.package_result.errors:
            lines.append("")
            lines.append("Package Errors:")
            for error in result.package_result.errors:
                lines.append(f"  [FAIL] {error}")

        if result.package_result.warnings:
            lines.append("")
            lines.append("Package Warnings:")
            for warning in result.package_result.warnings:
                lines.append(f"  [WARN] {warning}")

    lines.append("")
    lines.append("-" * 50)
    lines.append("This validator does not execute archive contents.")
    lines.append("Human review is required before import.")

    return "\n".join(lines)


def format_quiet_output(result: ArchiveValidationResult) -> str:
    """Format minimal pass/fail output."""
    if result.valid:
        return "PASS: archive is a valid CAM Assist strategy package"
    else:
        return "FAIL: archive validation failed"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate CAM Assist strategy package archive",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "archive",
        type=Path,
        help="Path to the .zip archive to validate",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output machine-readable JSON",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Only print pass/fail summary",
    )

    args = parser.parse_args()
    archive_path: Path = args.archive

    if not archive_path.exists():
        print(f"Error: Archive not found: {archive_path}", file=sys.stderr)
        return 2

    result = validate_archive(archive_path)

    if args.json:
        print(format_json_output(result))
    elif args.quiet:
        output = format_quiet_output(result)
        if result.valid:
            print(output)
        else:
            print(output, file=sys.stderr)
    else:
        print(format_terminal_output(result))

    if not result.archive_valid:
        return 1 if not any(
            e in ["Archive not found", "Not a valid zip file", "Path is not a file"]
            for e in result.archive_errors
        ) else 2

    return 0 if result.valid else 1


if __name__ == "__main__":
    sys.exit(main())
