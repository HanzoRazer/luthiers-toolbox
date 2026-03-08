"""
RMOS CLI Delete Tool - H3.5/H3.6

Delete run artifacts with policy enforcement and audit logging.

Usage:
    python -m app.rmos.runs_v2.cli_delete run_abc123 --reason "Cleanup test data"
    python -m app.rmos.runs_v2.cli_delete run_abc123 --mode hard --reason "Purge old data" --yes
    python -m app.rmos.runs_v2.cli_delete run_abc123 --dry-run --reason "Preview delete"

Environment Variables:
    RMOS_DELETE_DEFAULT_MODE: soft|hard (default: soft)
    RMOS_DELETE_ALLOW_HARD: true|false (default: false)
    RMOS_DELETE_RATE_LIMIT_MAX: int (default: 10)
"""
from __future__ import annotations

import argparse
import sys
from typing import Optional

from .store import delete_run, get_run, DeleteRateLimitError
from .delete_policy import get_delete_policy, check_delete_allowed, resolve_effective_mode
from .delete_audit import append_delete_audit, build_delete_audit_event


def cmd_delete(args: argparse.Namespace) -> int:
    """Delete a single run artifact."""
    run_id = args.run_id
    reason = args.reason.strip()
    actor = args.actor.strip() if args.actor else "cli"

    # Resolve policy and mode
    policy = get_delete_policy()
    effective_mode = resolve_effective_mode(args.mode, policy)

    # For CLI, we treat --mode hard as implicit admin (env gating still applies)
    is_admin = effective_mode == "hard"

    # Check policy
    allowed, deny_reason = check_delete_allowed(effective_mode, is_admin, policy)

    if not allowed:
        print(f"ERROR: {deny_reason}", file=sys.stderr)
        print("\nTo enable hard deletes, set RMOS_DELETE_ALLOW_HARD=true", file=sys.stderr)
        return 3

    # Verify run exists
    run = get_run(run_id)
    if run is None:
        print(f"ERROR: Run {run_id} not found", file=sys.stderr)
        return 1

    # Show what would happen
    print("=" * 60)
    print("RMOS Run Delete")
    print("=" * 60)
    print(f"Run ID:     {run_id}")
    print(f"Mode:       {effective_mode}")
    print(f"Reason:     {reason}")
    print(f"Actor:      {actor}")
    print(f"Cascade:    {not args.no_cascade}")
    print()

    if args.dry_run:
        print("[DRY RUN] No changes made.")
        return 0

    # Confirm if not --yes
    if not args.yes:
        confirm = input("Proceed with delete? [y/N]: ")
        if confirm.lower() != "y":
            print("Aborted.")
            return 1

    # Perform delete
    try:
        result = delete_run(
            run_id,
            mode=effective_mode,
            reason=reason,
            actor=actor,
            request_id=None,
            cascade=not args.no_cascade,
        )

        print()
        print("Delete completed:")
        print(f"  deleted:               {result['deleted']}")
        print(f"  index_updated:         {result['index_updated']}")
        print(f"  artifact_deleted:      {result['artifact_deleted']}")
        print(f"  advisory_links_deleted: {result['advisory_links_deleted']}")
        print(f"  partition:             {result.get('partition', 'N/A')}")
        print()

        if effective_mode == "soft":
            print("Run is tombstoned. It will be excluded from listings.")
        else:
            print("Run has been hard-deleted. Files removed.")

        return 0

    except KeyError:
        print(f"ERROR: Run {run_id} not found", file=sys.stderr)
        return 1

    except DeleteRateLimitError as e:
        print(f"ERROR: Rate limit exceeded - {e}", file=sys.stderr)
        return 2

    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


def cmd_status(args: argparse.Namespace) -> int:
    """Show delete policy status."""
    policy = get_delete_policy()

    print("=" * 60)
    print("RMOS Delete Policy Status")
    print("=" * 60)
    print(f"Default Mode:     {policy.default_mode}")
    print(f"Allow Hard:       {policy.allow_hard}")
    print(f"Admin Header:     {policy.admin_header_name}")
    print()

    from .store import DELETE_RATE_LIMIT_MAX, DELETE_RATE_LIMIT_WINDOW_SEC
    print("Rate Limiting:")
    print(f"  Max deletes:    {DELETE_RATE_LIMIT_MAX}")
    print(f"  Window (sec):   {DELETE_RATE_LIMIT_WINDOW_SEC}")
    print()

    return 0


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.rmos.runs_v2.cli_delete",
        description="Delete RMOS run artifacts with audit logging",
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete a run artifact")
    delete_parser.add_argument("run_id", help="Run ID to delete (e.g., run_abc123)")
    delete_parser.add_argument(
        "--mode",
        choices=["soft", "hard"],
        default=None,
        help="Delete mode (default: from policy)",
    )
    delete_parser.add_argument(
        "--reason",
        required=True,
        help="Audit reason for deletion (min 6 chars)",
    )
    delete_parser.add_argument(
        "--actor",
        default="cli",
        help="Actor performing deletion (default: cli)",
    )
    delete_parser.add_argument(
        "--no-cascade",
        action="store_true",
        help="Don't delete advisory links",
    )
    delete_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would happen without making changes",
    )
    delete_parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="Skip confirmation prompt",
    )
    delete_parser.set_defaults(func=cmd_delete)

    # Status command
    status_parser = subparsers.add_parser("status", help="Show delete policy status")
    status_parser.set_defaults(func=cmd_status)

    # Parse args
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
