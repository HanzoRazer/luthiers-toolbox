#!/usr/bin/env python3
"""
RMOS Runs v2 Migration CLI

Command-line tool for v1 to v2 migration.

Usage:
    python -m rmos.runs_gov.cli_migrate status
    python -m rmos.runs_gov.cli_migrate migrate --dry-run
    python -m rmos.runs_gov.cli_migrate migrate
    python -m rmos.runs_gov.cli_migrate verify
    python -m rmos.runs_gov.cli_migrate rollback --backup <path>
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from .migration_utils import (
    migrate_v1_to_v2,
    verify_migration,
    rollback_migration,
    get_migration_status,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def cmd_status(args: argparse.Namespace) -> int:
    """Show current migration status."""
    status = get_migration_status(args.v1_path, args.v2_root)

    print("\n=== RMOS Runs Migration Status ===\n")
    print(f"Status: {status['status']}")
    print(f"V1 Path: {status['v1_path']}")
    print(f"V1 Exists: {status['v1_exists']}")
    print(f"V1 Count: {status['v1_count']}")
    print(f"V2 Root: {status['v2_root']}")
    print(f"V2 Exists: {status['v2_exists']}")
    print(f"V2 Count: {status['v2_count']}")

    if status["status"] == "EMPTY":
        print("\n→ No data found. Nothing to migrate.")
    elif status["status"] == "V1_ONLY":
        print(f"\n→ Ready to migrate {status['v1_count']} runs from v1 to v2.")
        print("  Run: python -m rmos.runs_gov.cli_migrate migrate")
    elif status["status"] == "V2_ONLY":
        print("\n→ Migration complete. V2 is active.")
    elif status["status"] == "MIGRATED":
        print("\n→ Migration complete. V1 and V2 counts match.")
    elif status["status"] == "PARTIAL":
        print(f"\n→ Partial migration: {status['v2_count']}/{status['v1_count']} runs migrated.")
        print("  Run: python -m rmos.runs_gov.cli_migrate migrate")

    print()
    return 0


def cmd_migrate(args: argparse.Namespace) -> int:
    """Run migration from v1 to v2."""
    if args.dry_run:
        print("\n=== DRY RUN MODE (no changes will be made) ===\n")

    report = migrate_v1_to_v2(
        v1_path=args.v1_path,
        v2_root=args.v2_root,
        dry_run=args.dry_run,
        skip_backup=args.skip_backup,
    )

    print("\n=== Migration Report ===\n")
    print(f"V1 Path: {report.v1_path}")
    print(f"V2 Root: {report.v2_root}")
    print(f"Backup: {report.backup_path or 'N/A'}")
    print(f"Total V1 Runs: {report.total_v1_runs}")
    print(f"Migrated: {report.migrated_count}")
    print(f"Skipped (already exist): {report.skipped_count}")
    print(f"Errors: {report.error_count}")
    print(f"Success: {report.success}")
    print(f"Duration: {report.completed_at - report.started_at if report.completed_at else 'N/A'}")

    if report.errors:
        print(f"\nFirst {min(10, len(report.errors))} errors:")
        for err in report.errors[:10]:
            print(f"  - {err.get('run_id', 'N/A')}: {err.get('error', 'Unknown')}")

    if args.output:
        output_path = Path(args.output)
        output_path.write_text(json.dumps(report.to_dict(), indent=2))
        print(f"\nFull report saved to: {args.output}")

    print()
    return 0 if report.success else 1


def cmd_verify(args: argparse.Namespace) -> int:
    """Verify migration integrity."""
    result = verify_migration(args.v1_path, args.v2_root)

    print("\n=== Migration Verification ===\n")
    print(f"V1 Count: {result['v1_count']}")
    print(f"V2 Count: {result['v2_count']}")
    print(f"Verified: {result['verified_count']}")
    print(f"Missing in V2: {len(result['missing_in_v2'])}")
    print(f"Mismatched: {len(result['mismatched'])}")
    print(f"Success: {result['success']}")

    if result["missing_in_v2"]:
        print(f"\nMissing runs (first 10):")
        for item in result["missing_in_v2"][:10]:
            print(f"  - {item['run_id']}: {item['reason']}")

    if result["mismatched"]:
        print(f"\nMismatched runs (first 10):")
        for item in result["mismatched"][:10]:
            print(f"  - {item['run_id']}: {item['field']} v1={item['v1']} v2={item['v2']}")

    print()
    return 0 if result["success"] else 1


def cmd_rollback(args: argparse.Namespace) -> int:
    """Rollback migration by restoring v1 backup."""
    if not args.backup:
        print("ERROR: --backup path is required for rollback")
        return 1

    if not args.force:
        print(f"This will restore v1 from: {args.backup}")
        print("V2 data will NOT be automatically removed.")
        response = input("Continue? [y/N]: ")
        if response.lower() != "y":
            print("Rollback cancelled.")
            return 0

    try:
        rollback_migration(args.backup, args.v1_path)
        print(f"Rollback complete. V1 restored from: {args.backup}")
        return 0
    except Exception as e:
        print(f"Rollback failed: {e}")
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="RMOS Runs v2 Migration CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--v1-path",
        default="services/api/app/data/runs.json",
        help="Path to v1 runs.json (default: services/api/app/data/runs.json)",
    )
    parser.add_argument(
        "--v2-root",
        default="data/runs/rmos",
        help="Root directory for v2 storage (default: data/runs/rmos)",
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # status command
    subparsers.add_parser("status", help="Show current migration status")

    # migrate command
    migrate_parser = subparsers.add_parser("migrate", help="Run migration from v1 to v2")
    migrate_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate without writing",
    )
    migrate_parser.add_argument(
        "--skip-backup",
        action="store_true",
        help="Skip backup (use with caution)",
    )
    migrate_parser.add_argument(
        "--output",
        help="Write full report to this file",
    )

    # verify command
    subparsers.add_parser("verify", help="Verify migration integrity")

    # rollback command
    rollback_parser = subparsers.add_parser("rollback", help="Rollback migration")
    rollback_parser.add_argument(
        "--backup",
        required=True,
        help="Path to v1 backup file",
    )
    rollback_parser.add_argument(
        "--force",
        action="store_true",
        help="Skip confirmation prompt",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    if args.command == "status":
        return cmd_status(args)
    elif args.command == "migrate":
        return cmd_migrate(args)
    elif args.command == "verify":
        return cmd_verify(args)
    elif args.command == "rollback":
        return cmd_rollback(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
