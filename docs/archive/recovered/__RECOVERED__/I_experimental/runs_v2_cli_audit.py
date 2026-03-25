"""
RMOS Delete Audit CLI - Inspect and tail the delete audit log.

H3.6.3: Incident response utility.

Usage:
    cd services/api
    python -m app.rmos.runs_v2.cli_audit tail -n 50
    python -m app.rmos.runs_v2.cli_audit tail -n 50 -f
    python -m app.rmos.runs_v2.cli_audit count --mode soft
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import List, Optional

from .store import _get_store_root
from .delete_audit import read_audit_lines, _get_audit_path


def _get_runs_dir() -> Path:
    return Path(_get_store_root()).resolve()


def cmd_tail(args: argparse.Namespace) -> int:
    """Print last N delete audit events, optionally follow for new events."""
    store_root = _get_runs_dir()

    # Print last N events
    last = read_audit_lines(store_root=store_root, tail=args.lines)
    for e in last:
        if args.json:
            print(json.dumps(e, ensure_ascii=False))
        else:
            # Human-readable format
            ts = e.get("ts_utc", "?")
            run_id = e.get("run_id", "?")
            mode = e.get("mode", "?")
            outcome = e.get("outcome", "ok")
            actor = e.get("actor") or "anonymous"
            reason = e.get("reason", "")[:50]
            print(f"[{ts}] {mode:5} {outcome:12} {run_id} by {actor} - {reason}")

    if not args.follow:
        return 0

    # Follow mode: poll file for new lines
    audit_path = _get_audit_path(store_root)
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.touch(exist_ok=True)

    print(f"\n-- Following {audit_path} (Ctrl+C to stop) --\n", file=sys.stderr)

    last_size = audit_path.stat().st_size if audit_path.exists() else 0

    try:
        while True:
            time.sleep(args.interval)
            if not audit_path.exists():
                continue
            size = audit_path.stat().st_size
            if size < last_size:
                # log rotated or truncated; reprint last N
                for e in read_audit_lines(store_root=store_root, tail=args.lines):
                    if args.json:
                        print(json.dumps(e, ensure_ascii=False))
                    else:
                        ts = e.get("ts_utc", "?")
                        run_id = e.get("run_id", "?")
                        mode = e.get("mode", "?")
                        outcome = e.get("outcome", "ok")
                        actor = e.get("actor") or "anonymous"
                        reason = e.get("reason", "")[:50]
                        print(f"[{ts}] {mode:5} {outcome:12} {run_id} by {actor} - {reason}")
                last_size = size
                continue
            if size == last_size:
                continue

            # read newly appended bytes
            with open(audit_path, "r", encoding="utf-8", errors="replace") as f:
                f.seek(last_size)
                chunk = f.read()
                for ln in chunk.splitlines():
                    if not ln.strip():
                        continue
                    if args.json:
                        print(ln)
                    else:
                        try:
                            e = json.loads(ln)
                            ts = e.get("ts_utc", "?")
                            run_id = e.get("run_id", "?")
                            mode = e.get("mode", "?")
                            outcome = e.get("outcome", "ok")
                            actor = e.get("actor") or "anonymous"
                            reason = e.get("reason", "")[:50]
                            print(f"[{ts}] {mode:5} {outcome:12} {run_id} by {actor} - {reason}")
                        except (json.JSONDecodeError, ValueError, KeyError):  # WP-1: narrowed from except Exception
                            print(ln)
            last_size = size
    except KeyboardInterrupt:
        return 0

    return 0


def cmd_count(args: argparse.Namespace) -> int:
    """Count audit events, optionally filtered."""
    store_root = _get_runs_dir()
    events = read_audit_lines(store_root=store_root, tail=100000)

    # Apply filters
    if args.mode:
        events = [e for e in events if e.get("mode") == args.mode]
    if args.outcome:
        events = [e for e in events if e.get("outcome") == args.outcome]
    if args.actor:
        events = [e for e in events if e.get("actor") == args.actor]

    print(len(events))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="python -m app.rmos.runs_v2.cli_audit",
        description="Inspect RMOS runs_v2 delete audit log",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    # tail command
    t = sub.add_parser("tail", help="Print last N delete audit events")
    t.add_argument("-n", "--lines", type=int, default=50, help="Number of lines to show")
    t.add_argument("-f", "--follow", action="store_true", help="Follow for new events")
    t.add_argument("--interval", type=float, default=0.5, help="Follow poll interval (seconds)")
    t.add_argument(
        "--json",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Output JSON lines (default: true; use --no-json for human-readable)",
    )
    t.set_defaults(fn=cmd_tail)

    # count command
    c = sub.add_parser("count", help="Count audit events")
    c.add_argument("--mode", choices=["soft", "hard"], help="Filter by mode")
    c.add_argument("--outcome", help="Filter by outcome (ok, not_found, error, forbidden, rate_limited)")
    c.add_argument("--actor", help="Filter by actor")
    c.set_defaults(fn=cmd_count)

    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        rc = args.fn(args)
    except KeyboardInterrupt:
        print("\nInterrupted", file=sys.stderr)
        rc = 130
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
