#!/usr/bin/env python3
"""
CAM Assist Review Decision Record CLI

Records a human review decision for a staged CAM Assist strategy package.

The decision record is written as a sibling file to the package directory.
Package contents are never modified.

This is non-execution infrastructure. It does not generate G-code,
produce machine output, or authorize machine execution.

Usage:
    python scripts/record_review_decision.py staged_packages/fret_slot_strategy_package \\
        --decision approve_for_downstream_cam \\
        --reviewer "Human Reviewer" \\
        --notes "Reviewed scale, fret count, kerf, and workholding assumptions."

    python scripts/record_review_decision.py <package_dir> \\
        --decision reject \\
        --reviewer "Reviewer Name" \\
        --out /tmp/decision.json

Exit codes:
    0 — Decision record created
    1 — Package validation or decision validation failure
    2 — File/read/write error
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from inspect_strategy_package import inspect_package

ALLOWED_DECISIONS = {"approve_for_downstream_cam", "reject", "needs_revision"}
RECORD_VERSION = "1.0.0"


def get_package_manifest_id(manifest_data: dict, manifest_path: Path) -> str:
    """Generate package manifest ID from manifest data."""
    operation_type = manifest_data.get("operation_type", "unknown")
    provenance = manifest_data.get("provenance", {})
    source_spec_id = provenance.get("source_spec_id")

    if source_spec_id:
        return f"{operation_type}:{source_spec_id}"
    else:
        return f"{operation_type}:{manifest_path.stem}"


def load_manifest(package_dir: Path) -> tuple[dict | None, str | None]:
    """Load manifest from package directory. Returns (data, error)."""
    manifest_path = package_dir / "manifest.json"
    if not manifest_path.exists():
        return None, "manifest.json not found"

    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            return json.load(f), None
    except json.JSONDecodeError as e:
        return None, f"Invalid JSON in manifest: {e}"
    except Exception as e:
        return None, f"Error reading manifest: {e}"


def create_decision_record(
    package_dir: Path,
    decision: str,
    reviewer: str,
    notes: str = "",
) -> tuple[dict | None, str | None]:
    """
    Create a review decision record for a package.

    Returns (record, error).
    """
    if not package_dir.exists():
        return None, f"Package directory not found: {package_dir}"

    if not package_dir.is_dir():
        return None, f"Not a directory: {package_dir}"

    if decision not in ALLOWED_DECISIONS:
        return None, f"Invalid decision: {decision}. Must be one of: {', '.join(sorted(ALLOWED_DECISIONS))}"

    if not reviewer or not reviewer.strip():
        return None, "Reviewer name is required"

    inspection = inspect_package(package_dir)
    if not inspection.valid:
        errors = "; ".join(inspection.errors)
        return None, f"Package validation failed: {errors}"

    manifest_data, manifest_error = load_manifest(package_dir)
    if manifest_error:
        return None, f"Failed to load manifest: {manifest_error}"

    manifest_path = package_dir / "manifest.json"
    package_manifest_id = get_package_manifest_id(manifest_data, manifest_path)
    operation_type = manifest_data.get("operation_type", "unknown")

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    record = {
        "record_type": "cam_assist_review_decision",
        "record_version": RECORD_VERSION,
        "package_path": str(package_dir),
        "package_manifest_id": package_manifest_id,
        "operation_type": operation_type,
        "decision": decision,
        "reviewer": reviewer.strip(),
        "reviewed_at": timestamp,
        "notes": notes,
        "authority": {
            "does_not_authorize_machine_execution": True,
            "requires_downstream_cam_verification": True,
            "human_review_recorded": True,
        },
    }

    return record, None


def write_decision_record(
    record: dict,
    output_path: Path,
    force: bool = False,
) -> tuple[bool, str]:
    """Write decision record to file. Returns (success, message)."""
    if output_path.exists() and not force:
        return False, f"Output file already exists: {output_path} (use --force to overwrite)"

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(record, indent=2),
            encoding="utf-8",
        )
        return True, f"Decision record created: {output_path}"
    except OSError as e:
        return False, f"Failed to write decision record: {e}"


def format_terminal_output(record: dict, output_path: Path) -> str:
    """Format decision record summary for terminal display."""
    lines = []

    lines.append("CAM Assist Review Decision Recorded")
    lines.append("=" * 36)
    lines.append("")
    lines.append(f"Package: {record['package_path']}")
    lines.append(f"Manifest ID: {record['package_manifest_id']}")
    lines.append(f"Operation: {record['operation_type']}")
    lines.append("")
    lines.append(f"Decision: {record['decision']}")
    lines.append(f"Reviewer: {record['reviewer']}")
    lines.append(f"Reviewed at: {record['reviewed_at']}")

    if record.get("notes"):
        lines.append(f"Notes: {record['notes']}")

    lines.append("")
    lines.append(f"Output: {output_path}")
    lines.append("")
    lines.append("-" * 36)
    lines.append("This decision does NOT authorize machine execution.")
    lines.append("Downstream CAM verification is still required.")

    return "\n".join(lines)


def format_quiet_output(success: bool, output_path: Path, decision: str) -> str:
    """Format minimal pass/fail output."""
    if success:
        return f"PASS: Decision '{decision}' recorded: {output_path}"
    else:
        return "FAIL: Decision recording failed"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Record a human review decision for a staged CAM Assist package",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "package_dir",
        type=Path,
        help="Path to the staged package directory",
    )
    parser.add_argument(
        "--decision",
        type=str,
        required=True,
        choices=sorted(ALLOWED_DECISIONS),
        help="Review decision: approve_for_downstream_cam, reject, or needs_revision",
    )
    parser.add_argument(
        "--reviewer",
        type=str,
        required=True,
        help="Name or identifier of the human reviewer",
    )
    parser.add_argument(
        "--notes",
        type=str,
        default="",
        help="Optional reviewer notes",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output path for decision record (default: <package_dir>.review_decision.json)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing decision record",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Only print pass/fail summary",
    )

    args = parser.parse_args()
    package_dir: Path = args.package_dir

    if not package_dir.exists():
        print(f"Error: Package directory not found: {package_dir}", file=sys.stderr)
        return 2

    record, error = create_decision_record(
        package_dir,
        args.decision,
        args.reviewer,
        args.notes,
    )

    if error:
        if args.quiet:
            print(f"FAIL: {error}", file=sys.stderr)
        else:
            print(f"Error: {error}", file=sys.stderr)
        return 1

    if args.out:
        output_path = args.out
    else:
        output_path = package_dir.parent / f"{package_dir.name}.review_decision.json"

    success, message = write_decision_record(record, output_path, args.force)

    if not success:
        if args.quiet:
            print(f"FAIL: {message}", file=sys.stderr)
        else:
            print(f"Error: {message}", file=sys.stderr)
        return 1 if "exists" in message else 2

    if args.quiet:
        print(format_quiet_output(True, output_path, args.decision))
    else:
        print(format_terminal_output(record, output_path))

    return 0


if __name__ == "__main__":
    sys.exit(main())
