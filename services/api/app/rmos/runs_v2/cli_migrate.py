#!/usr/bin/env python3
"""
RMOS Runs Migration CLI

Command-line tool for migrating from v1 (single-file) to v2 (date-partitioned) storage.

Usage:
    # Check migration status
    python -m rmos.runs_v2.cli_migrate status

    # Dry-run migration (validate without writing)
    python -m rmos.runs_v2.cli_migrate migrate --dry-run

    # Run actual migration
    python -m rmos.runs_v2.cli_migrate migrate

    # Verify migration completed successfully
    python -m rmos.runs_v2.cli_migrate verify

    # Rollback migration (restore v1)
    python -m rmos.runs_v2.cli_migrate rollback --backup-path <path>

Environment Variables:
    RMOS_RUN_STORE_PATH: v1 store path (default: services/api/app/data/runs.json)
    RMOS_RUNS_DIR: v2 store root (default: services/api/data/runs/rmos)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def get_v1_path() -> str:
    """Get v1 store path from environment or default."""
    return os.getenv("RMOS_RUN_STORE_PATH", "services/api/app/data/runs.json")


def get_v2_root() -> str:
    """Get v2 store root from environment or default."""
    return os.getenv("RMOS_RUNS_DIR", "services/api/data/runs/rmos")


def cmd_status(args: argparse.Namespace) -> int:
    """Check current migration status."""
    from .migration_utils import migration_status, load_v1_store

    v1_path = get_v1_path()
    v2_root = get_v2_root()

    print("=" * 60)
    print("RMOS Runs Migration Status")
    print("=" * 60)

    # v1 status
    print(f"\n[v1 Store]")
    print(f"  Path: {v1_path}")
    if Path(v1_path).exists():
        try:
            v1_data = load_v1_store(v1_path)
            print(f"  Status: EXISTS")
            print(f"  Artifact count: {len(v1_data)}")
        except (OSError, json.JSONDecodeError, ValueError) as e:  # WP-1: narrowed from except Exception
            print(f"  Status: ERROR - {e}")
    else:
        print(f"  Status: NOT FOUND (no v1 data to migrate)")

    # v2 status
    print(f"\n[v2 Store]")
    print(f"  Root: {v2_root}")
    v2_status = migration_status(v2_root)
    if v2_status.get("exists"):
        print(f"  Status: EXISTS")
        print(f"  Partitions: {v2_status.get('partition_count', 0)}")
        print(f"  Total artifacts: {v2_status.get('total_artifacts', 0)}")
        if v2_status.get("partitions"):
            print(f"  Partition details:")
            for p in v2_status["partitions"][:10]:
                print(f"    {p['date']}: {p['artifact_count']} artifacts")
            if len(v2_status["partitions"]) > 10:
                print(f"    ... and {len(v2_status['partitions']) - 10} more")
    else:
        print(f"  Status: NOT INITIALIZED")

    print("\n" + "=" * 60)
    return 0


def cmd_migrate(args: argparse.Namespace) -> int:
    """Run migration from v1 to v2."""
    from .migration_utils import migrate_v1_to_v2

    v1_path = get_v1_path()
    v2_root = get_v2_root()

    if not Path(v1_path).exists():
        print(f"[INFO] v1 store not found at: {v1_path}")
        print("[INFO] No migration needed - system will use v2 store for new data.")
        return 0

    print("=" * 60)
    print("RMOS Runs Migration: v1 -> v2")
    print("=" * 60)
    print(f"\nSource: {v1_path}")
    print(f"Target: {v2_root}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")

    if not args.dry_run and not args.yes:
        confirm = input("\nProceed with migration? [y/N]: ")
        if confirm.lower() != "y":
            print("Migration cancelled.")
            return 1

    print("\nRunning migration...")
    report = migrate_v1_to_v2(
        v1_path=v1_path,
        v2_root=v2_root,
        dry_run=args.dry_run,
        skip_backup=args.skip_backup,
        stop_on_error=args.stop_on_error,
    )

    print("\n" + "=" * 60)
    print("Migration Report")
    print("=" * 60)
    print(f"  Started: {report.started_at}")
    print(f"  Completed: {report.completed_at}")
    print(f"  Success: {report.success}")
    print(f"  Total v1 artifacts: {report.total_v1}")
    print(f"  Migrated: {report.migrated}")
    print(f"  Skipped (duplicates): {report.skipped}")
    print(f"  Failed: {report.failed}")
    if report.backup_path:
        print(f"  Backup: {report.backup_path}")
    if report.partitions_created:
        print(f"  Partitions created: {', '.join(report.partitions_created)}")
    if report.errors:
        print(f"\n  Errors ({len(report.errors)}):")
        for err in report.errors[:10]:
            print(f"    - {err}")
        if len(report.errors) > 10:
            print(f"    ... and {len(report.errors) - 10} more")

    print("\n" + "=" * 60)

    # Write report to file
    report_path = Path(v2_root) / "_migration_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
    print(f"Report saved to: {report_path}")

    return 0 if report.success else 1


def cmd_verify(args: argparse.Namespace) -> int:
    """Verify migration completed successfully."""
    from .migration_utils import verify_migration

    v1_path = get_v1_path()
    v2_root = get_v2_root()

    if not Path(v1_path).exists():
        print(f"[INFO] v1 store not found - nothing to verify against.")
        return 0

    print("=" * 60)
    print("RMOS Runs Migration Verification")
    print("=" * 60)

    result = verify_migration(v1_path, v2_root)

    if result.get("error"):
        print(f"\nError: {result['error']}")
        return 1

    print(f"\n  v1 artifact count: {result['v1_count']}")
    print(f"  v2 artifacts found: {result['v2_found']}")
    print(f"  Missing: {len(result['missing'])}")
    print(f"  Hash mismatches: {len(result['mismatched'])}")
    print(f"  Complete: {result['complete']}")

    if result["missing"]:
        print(f"\n  Missing artifacts:")
        for run_id in result["missing"][:10]:
            print(f"    - {run_id}")
        if len(result["missing"]) > 10:
            print(f"    ... and {len(result['missing']) - 10} more")

    if result["mismatched"]:
        print(f"\n  Hash mismatches:")
        for m in result["mismatched"][:5]:
            print(f"    - {m['run_id']}: {m['v1_hash'][:16]}... vs {m['v2_hash'][:16]}...")

    print("\n" + "=" * 60)
    return 0 if result["complete"] else 1


def cmd_rollback(args: argparse.Namespace) -> int:
    """Rollback migration by restoring v1 backup."""
    from .migration_utils import rollback_migration

    v1_path = get_v1_path()
    v2_root = get_v2_root()

    if not args.backup_path:
        print("Error: --backup-path is required for rollback")
        return 1

    if not Path(args.backup_path).exists():
        print(f"Error: Backup not found: {args.backup_path}")
        return 1

    print("=" * 60)
    print("RMOS Runs Migration Rollback")
    print("=" * 60)
    print(f"\nBackup: {args.backup_path}")
    print(f"Restore to: {v1_path}")
    print(f"Delete v2: {args.delete_v2}")

    if not args.yes:
        confirm = input("\nProceed with rollback? [y/N]: ")
        if confirm.lower() != "y":
            print("Rollback cancelled.")
            return 1

    result = rollback_migration(
        v1_path=v1_path,
        backup_path=args.backup_path,
        v2_root=v2_root,
        delete_v2=args.delete_v2,
    )

    print("\n" + "=" * 60)
    print("Rollback Result")
    print("=" * 60)
    print(f"  v1 restored: {result['restored_v1']}")
    print(f"  v2 deleted: {result['deleted_v2']}")
    if result["errors"]:
        print(f"  Errors:")
        for e in result["errors"]:
            print(f"    - {e}")

    print("\n" + "=" * 60)
    return 0 if result["restored_v1"] else 1


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="RMOS Runs Migration CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # status command
    status_parser = subparsers.add_parser("status", help="Check migration status")
    status_parser.set_defaults(func=cmd_status)

    # migrate command
    migrate_parser = subparsers.add_parser("migrate", help="Run migration")
    migrate_parser.add_argument("--dry-run", action="store_true", help="Validate without writing")
    migrate_parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation")
    migrate_parser.add_argument("--skip-backup", action="store_true", help="Skip backup creation")
    migrate_parser.add_argument("--stop-on-error", action="store_true", help="Stop on first error")
    migrate_parser.set_defaults(func=cmd_migrate)

    # verify command
    verify_parser = subparsers.add_parser("verify", help="Verify migration")
    verify_parser.set_defaults(func=cmd_verify)

    # rollback command
    rollback_parser = subparsers.add_parser("rollback", help="Rollback migration")
    rollback_parser.add_argument("--backup-path", required=True, help="Path to v1 backup file")
    rollback_parser.add_argument("--delete-v2", action="store_true", help="Also delete v2 data")
    rollback_parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation")
    rollback_parser.set_defaults(func=cmd_rollback)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
