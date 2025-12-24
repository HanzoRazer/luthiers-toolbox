"""
RMOS Audit CLI - Tail and inspect delete audit logs.

H3.6.3: Incident response utility.

Usage:
    python -m app.rmos.runs_v2.cli_audit tail --lines 50
    python -m app.rmos.runs_v2.cli_audit tail --follow --lines 100
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import Optional

from .store import _get_store_root
from .delete_audit import _get_audit_path


def _tail_lines(path: Path, n: int) -> str:
    if not path.exists():
        return ""

    # Simple, safe tail for JSONL (file sizes should be reasonable; if not, we can optimize later)
    data = path.read_text(encoding="utf-8", errors="replace").splitlines()
    return "\n".join(data[-n:]) + ("\n" if data else "")


def cmd_tail(args: argparse.Namespace) -> int:
    store_root = Path(_get_store_root())
    audit_path = _get_audit_path(store_root)

    if args.follow:
        # print last N, then follow
        out = _tail_lines(audit_path, args.lines)
        if out:
            sys.stdout.write(out)
            sys.stdout.flush()

        last_size = audit_path.stat().st_size if audit_path.exists() else 0

        try:
            while True:
                time.sleep(args.poll_ms / 1000.0)
                if not audit_path.exists():
                    continue
                size = audit_path.stat().st_size
                if size < last_size:
                    # log rotated or truncated; reprint last N
                    sys.stdout.write(_tail_lines(audit_path, args.lines))
                    sys.stdout.flush()
                    last_size = size
                    continue
                if size == last_size:
                    continue

                # read newly appended bytes
                with open(audit_path, "r", encoding="utf-8", errors="replace") as f:
                    f.seek(last_size)
                    chunk = f.read()
                    if chunk:
                        sys.stdout.write(chunk)
                        sys.stdout.flush()
                last_size = size
        except KeyboardInterrupt:
            return 0

    # non-follow: just last N
    out = _tail_lines(audit_path, args.lines)
    sys.stdout.write(out)
    sys.stdout.flush()
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(
        prog="python -m app.rmos.runs_v2.cli_audit",
        description="RMOS runs_v2 audit utilities",
    )
    sp = p.add_subparsers(dest="cmd", required=True)

    t = sp.add_parser("tail", help="Tail the delete audit log")
    t.add_argument("--lines", type=int, default=50, help="Number of lines to show")
    t.add_argument("--follow", action="store_true", help="Follow (like tail -f)")
    t.add_argument("--poll-ms", type=int, default=500, help="Polling interval in ms (follow mode)")
    t.set_defaults(fn=cmd_tail)

    args = p.parse_args(argv)
    return int(args.fn(args))


if __name__ == "__main__":
    raise SystemExit(main())
