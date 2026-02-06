#!/usr/bin/env python3
"""viewer_pack_validate.py — Validate viewer pack ZIP structural integrity.

Guarantees the exported ZIP is structurally correct and truthful (Phase L2).

Checks:
1. viewer_pack.json exists in ZIP
2. Manifest validates against contracts/viewer_pack_v1.schema.json
3. Every files[].relpath exists in the ZIP
4. SHA256 and bytes match for each file
5. bundle_sha256 matches recomputed value
6. Required content kinds present (optional strict mode)

Usage:
    python scripts/viewer_pack_validate.py path/to/viewer_pack.zip
    python scripts/viewer_pack_validate.py pack.zip --strict
    python scripts/viewer_pack_validate.py pack.zip --schema custom.schema.json

Exit codes:
    0 = Valid
    1 = Validation failed (errors in report)
    2 = Usage/argument error
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

# Schema validation (optional dependency)
try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tap_tone.viewer_pack.manifest import (
    load_viewer_pack,
    compute_bundle_sha256,
    compute_file_sha256,
    iter_files,
    read_file_from_pack,
    MANIFEST_FILENAME,
)


@dataclass
class ValidationResult:
    """Immutable validation result with categorized errors."""
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    checks_passed: int = 0
    checks_failed: int = 0

    def add_error(self, msg: str) -> None:
        self.errors.append(msg)
        self.checks_failed += 1

    def add_warning(self, msg: str) -> None:
        self.warnings.append(msg)

    def add_pass(self) -> None:
        self.checks_passed += 1

    def finalize(self) -> "ValidationResult":
        return ValidationResult(
            valid=len(self.errors) == 0,
            errors=self.errors,
            warnings=self.warnings,
            checks_passed=self.checks_passed,
            checks_failed=self.checks_failed,
        )


def load_schema(schema_path: Optional[Path]) -> Optional[dict]:
    """Load JSON schema from file."""
    if schema_path is None:
        # Default schema location
        default_path = Path(__file__).resolve().parents[1] / "contracts" / "viewer_pack_v1.schema.json"
        if default_path.exists():
            schema_path = default_path
        else:
            return None

    if not schema_path.exists():
        return None

    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_viewer_pack(
    zip_path: Path,
    schema_path: Optional[Path] = None,
    strict: bool = False,
) -> ValidationResult:
    """Validate a viewer pack ZIP file.

    Args:
        zip_path: Path to viewer_pack_*.zip
        schema_path: Optional path to JSON schema (uses default if None)
        strict: If True, require all content kinds to be present

    Returns:
        ValidationResult with errors and warnings
    """
    result = ValidationResult(valid=True)

    # 1. Check ZIP exists and can be opened
    try:
        handle = load_viewer_pack(zip_path)
    except FileNotFoundError as e:
        result.add_error(f"ZIP not found: {e}")
        return result.finalize()
    except KeyError as e:
        result.add_error(f"Manifest missing: {e}")
        return result.finalize()
    except Exception as e:
        result.add_error(f"Failed to open ZIP: {e}")
        return result.finalize()

    result.add_pass()  # ZIP opened successfully

    try:
        manifest = handle.manifest

        # 2. Validate against JSON schema
        schema = load_schema(schema_path)
        if schema is not None and HAS_JSONSCHEMA:
            try:
                jsonschema.validate(instance=manifest, schema=schema)
                result.add_pass()
            except jsonschema.ValidationError as e:
                result.add_error(f"Schema validation failed: {e.message}")
        elif schema is None:
            result.add_warning("No schema found; skipping schema validation")
        elif not HAS_JSONSCHEMA:
            result.add_warning("jsonschema not installed; skipping schema validation")

        # 3. Verify bundle_sha256
        declared_hash = manifest.get("bundle_sha256", "")
        computed_hash = compute_bundle_sha256(manifest)
        if declared_hash == computed_hash:
            result.add_pass()
        else:
            result.add_error(
                f"bundle_sha256 mismatch: declared={declared_hash[:16]}... "
                f"computed={computed_hash[:16]}..."
            )

        # 4. Verify each file exists and matches
        zip_names = set(handle.zip_handle.namelist())

        for entry in iter_files(manifest):
            # Check file exists in ZIP
            if entry.relpath not in zip_names:
                result.add_error(f"File missing from ZIP: {entry.relpath}")
                continue

            # Read file and verify
            try:
                data = read_file_from_pack(handle, entry.relpath)
            except Exception as e:
                result.add_error(f"Failed to read {entry.relpath}: {e}")
                continue

            # Verify size
            if len(data) != entry.bytes:
                result.add_error(
                    f"Size mismatch for {entry.relpath}: "
                    f"declared={entry.bytes} actual={len(data)}"
                )
            else:
                result.add_pass()

            # Verify SHA256
            actual_sha = compute_file_sha256(data)
            if actual_sha != entry.sha256:
                result.add_error(
                    f"SHA256 mismatch for {entry.relpath}: "
                    f"declared={entry.sha256[:16]}... actual={actual_sha[:16]}..."
                )
            else:
                result.add_pass()

        # 5. Check for orphan files (in ZIP but not in manifest)
        manifest_paths = {f.relpath for f in iter_files(manifest)}
        manifest_paths.add(MANIFEST_FILENAME)

        for name in zip_names:
            if name not in manifest_paths and not name.endswith("/"):
                result.add_warning(f"File in ZIP not listed in manifest: {name}")

        # 6. Strict mode: check required content kinds
        if strict:
            contents = manifest.get("contents", {})
            required_kinds = ["audio", "spectra"]  # Minimum for a valid pack

            for kind in required_kinds:
                if not contents.get(kind, False):
                    result.add_error(f"Strict mode: required content kind missing: {kind}")
                else:
                    result.add_pass()

        # 7. Check points list is non-empty
        points = manifest.get("points", [])
        if len(points) == 0:
            result.add_warning("No points declared in manifest")
        else:
            result.add_pass()

    finally:
        handle.close()

    return result.finalize()


def print_report(result: ValidationResult, zip_path: Path) -> None:
    """Print validation report to stdout."""
    print(f"\n{'='*60}")
    print(f"Viewer Pack Validation: {zip_path.name}")
    print(f"{'='*60}")

    if result.valid:
        print(f"\n✓ VALID ({result.checks_passed} checks passed)")
    else:
        print(f"\n✗ INVALID ({result.checks_failed} errors, {result.checks_passed} passed)")

    if result.errors:
        print(f"\nErrors ({len(result.errors)}):")
        for err in result.errors:
            print(f"  ✗ {err}")

    if result.warnings:
        print(f"\nWarnings ({len(result.warnings)}):")
        for warn in result.warnings:
            print(f"  ⚠ {warn}")

    print()


def main(argv: Optional[List[str]] = None) -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate viewer pack ZIP structural integrity.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python scripts/viewer_pack_validate.py viewer_pack_session123.zip
    python scripts/viewer_pack_validate.py pack.zip --strict
    python scripts/viewer_pack_validate.py pack.zip --schema my_schema.json --json
        """,
    )
    parser.add_argument(
        "zip_path",
        type=Path,
        help="Path to viewer_pack_*.zip file",
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=None,
        help="Path to JSON schema (default: contracts/viewer_pack_v1.schema.json)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Require all content kinds to be present",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output result as JSON instead of human-readable report",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress output; exit code only",
    )

    args = parser.parse_args(argv)

    result = validate_viewer_pack(
        zip_path=args.zip_path,
        schema_path=args.schema,
        strict=args.strict,
    )

    if args.json:
        output = {
            "valid": result.valid,
            "checks_passed": result.checks_passed,
            "checks_failed": result.checks_failed,
            "errors": result.errors,
            "warnings": result.warnings,
        }
        print(json.dumps(output, indent=2))
    elif not args.quiet:
        print_report(result, args.zip_path)

    return 0 if result.valid else 1


if __name__ == "__main__":
    sys.exit(main())
