#!/usr/bin/env python3
"""
worktree_reaper.py - safe, targeted git worktree reclamation.

WHY THIS EXISTS
---------------
`git worktree prune` is a repo-global destructive operation. In a shared
checkout with parallel sprints it can de-register a live worktree. The standing
rule is "never global prune"; this tool is the safe alternative. It reclaims
worktrees one explicit path at a time, only after proving the path is safe to
remove, and it never enumerates and destroys.

SAFETY CONTRACT
---------------
1. `reap` acts on exactly one path that you name. There is no "reap all",
   no "reap --merged", and no globbing. The explicit path is consent.
2. It never calls `git worktree prune` or any global destroy operation.
3. It refuses the main worktree and the current worktree.
4. It refuses a path that is not a registered worktree.
5. It refuses a dirty worktree.
6. It refuses unless merged is positively established:
      branch HEAD is an ancestor of the integration ref
   OR the branch's PR is MERGED per `gh`
   If neither can be proven, it fails safe and leaves the worktree in place.
7. On a file-lock failure it does not force. It reports the lock and leaves the
   worktree in place to be reaped later once unlocked.

`scan` is read-only. It classifies every worktree so you can see what is
reclaimable, but it takes no action. You still have to name the path to reap.

stdlib only. Python 3.8+.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from dataclasses import dataclass
from typing import List, Optional, Tuple

LOCK_MARKERS = (
    "permission denied",
    "being used by another process",
    "cannot access the file",
    "resource busy",
    "text file busy",
)

# Common Windows lock culprits from test runs, probed cheaply on lock failure.
SUSPECT_LOCK_GLOBS = (".coverage", "htmlcov", ".pytest_cache", "__pycache__")


def run(cmd: List[str], cwd: Optional[str] = None) -> Tuple[int, str, str]:
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    except FileNotFoundError:
        return 127, "", f"{cmd[0]}: not found"
    return p.returncode, p.stdout.strip(), p.stderr.strip()


def norm(path: str) -> str:
    return os.path.normcase(os.path.normpath(os.path.abspath(path)))


@dataclass
class Worktree:
    path: str
    head: str = ""
    branch: str = ""
    detached: bool = False
    is_main: bool = False


def list_worktrees() -> List[Worktree]:
    """Read-only enumeration for reporting."""
    rc, out, err = run(["git", "worktree", "list", "--porcelain"])
    if rc != 0:
        sys.exit(f"error: not a git repo or git failed: {err}")

    wts: List[Worktree] = []
    cur: Optional[Worktree] = None
    for line in out.splitlines():
        if line.startswith("worktree "):
            if cur:
                wts.append(cur)
            cur = Worktree(path=line[len("worktree "):])
        elif cur is None:
            continue
        elif line.startswith("HEAD "):
            cur.head = line[len("HEAD "):]
        elif line.startswith("branch "):
            ref = line[len("branch "):]
            cur.branch = ref.replace("refs/heads/", "", 1)
        elif line == "detached":
            cur.detached = True

    if cur:
        wts.append(cur)
    if wts:
        wts[0].is_main = True
    return wts


def integration_ref(explicit: Optional[str]) -> str:
    if explicit:
        return explicit
    for ref in ("origin/main", "main", "origin/master", "master"):
        rc, _, _ = run(["git", "rev-parse", "--verify", "--quiet", ref])
        if rc == 0:
            return ref
    sys.exit("error: could not resolve an integration ref (origin/main|main|...)")


def current_toplevel() -> str:
    rc, out, _ = run(["git", "rev-parse", "--show-toplevel"])
    return norm(out) if rc == 0 else ""


def is_clean(path: str) -> bool:
    rc, out, _ = run(["git", "status", "--porcelain"], cwd=path)
    return rc == 0 and out == ""


def merged_signal(wt: Worktree, ref: str) -> Tuple[bool, str]:
    """Return (merged, how). Ancestry first, then gh PR state for squash."""
    if wt.head:
        rc, _, _ = run(["git", "merge-base", "--is-ancestor", wt.head, ref])
        if rc == 0:
            return True, f"HEAD is ancestor of {ref}"

    if wt.branch:
        rc, out, _ = run(
            ["gh", "pr", "view", wt.branch, "--json", "state", "-q", ".state"]
        )
        if rc == 0 and out.strip().upper() == "MERGED":
            return True, "gh: PR MERGED (squash-safe)"
        if rc != 0:
            return False, "not an ancestor; gh unavailable/no PR -> UNPROVEN"

    return False, "not an ancestor; PR not MERGED -> UNPROVEN"


def classify(wt: Worktree, ref: str, here: str) -> Tuple[str, str]:
    if wt.is_main:
        return "MAIN", "primary worktree (protected)"
    if norm(wt.path) == here:
        return "CURRENT", "you are standing in it (protected)"
    if wt.branch and wt.branch == ref.split("/")[-1]:
        return "INTEGRATION", f"holds the integration branch {wt.branch} (protected)"
    if not os.path.isdir(wt.path):
        return "STALE-REG", "registered path missing on disk (manual review; not auto-pruned)"
    if not is_clean(wt.path):
        return "DIRTY", "uncommitted/untracked changes (protected)"

    merged, how = merged_signal(wt, ref)
    if merged:
        return "REAPABLE", how
    return "NOT-MERGED", how


def find_locking_files(path: str, cap: int = 40) -> List[str]:
    locked: List[str] = []
    checked = 0
    for root, _, files in os.walk(path):
        for name in files:
            if checked >= cap:
                return locked
            if not any(s in name or s in root for s in SUSPECT_LOCK_GLOBS):
                continue
            fp = os.path.join(root, name)
            checked += 1
            try:
                with open(fp, "a", encoding="utf-8"):
                    pass
            except (PermissionError, OSError):
                locked.append(fp)
    return locked


def cmd_scan(args: argparse.Namespace) -> int:
    ref = integration_ref(args.integration_ref)
    here = current_toplevel()
    wts = list_worktrees()

    print(f"integration ref: {ref}\n")
    width = max((len(w.path) for w in wts), default=4)
    reapable = []
    for wt in wts:
        status, reason = classify(wt, ref, here)
        br = wt.branch or "(detached)"
        print(f"  {status:<12} {wt.path:<{width}}  {br}")
        print(f"  {'':<12} {'':<{width}}  -> {reason}")
        if status == "REAPABLE":
            reapable.append(wt.path)

    print()
    if reapable:
        print("Reapable (name one explicitly to remove):")
        for path in reapable:
            print(f'  python services/api/scripts/worktree_reaper.py reap "{path}"')
    else:
        print("Nothing reapable. (Scan takes no action regardless.)")
    return 0


def cmd_reap(args: argparse.Namespace) -> int:
    ref = integration_ref(args.integration_ref)
    here = current_toplevel()
    target = norm(args.path)

    wts = list_worktrees()
    match = next((w for w in wts if norm(w.path) == target), None)
    if match is None:
        print(f"REFUSED: {args.path} is not a registered worktree.", file=sys.stderr)
        print("  (This tool never removes an arbitrary directory.)", file=sys.stderr)
        return 2

    status, reason = classify(match, ref, here)
    if status != "REAPABLE":
        print(f"REFUSED [{status}]: {match.path}", file=sys.stderr)
        print(f"  {reason}", file=sys.stderr)
        return 2

    print(f"reaping (merged: {reason})")
    print(f"  path:   {match.path}")
    print(f"  branch: {match.branch or '(detached)'}")

    rc, out, err = run(["git", "worktree", "remove", match.path])
    if rc != 0:
        low = err.lower()
        if any(marker in low for marker in LOCK_MARKERS):
            print(f"LOCKED: could not remove {match.path}", file=sys.stderr)
            print(f"  git: {err}", file=sys.stderr)
            holders = find_locking_files(match.path)
            if holders:
                print("  likely lock holders:", file=sys.stderr)
                for holder in holders:
                    print(f"    {holder}", file=sys.stderr)
            else:
                print(
                    "  (could not pinpoint the file; usual causes: coverage/htmlcov/pytest handles)",
                    file=sys.stderr,
                )
            print("  left inert on purpose. Re-run reap once unlocked.", file=sys.stderr)
            return 3

        print(f"FAILED: {err or out}", file=sys.stderr)
        print("  not forcing; left inert.", file=sys.stderr)
        return 3

    print(f"removed worktree: {match.path}")

    if args.delete_branch and match.branch:
        rc, out, err = run(["git", "branch", "-d", match.branch])
        if rc == 0:
            print(f"deleted merged branch: {match.branch}")
        else:
            print(f"note: kept branch {match.branch} ({err or out})")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Safe, targeted git worktree reclamation. Never global-prunes.",
    )
    p.add_argument(
        "--integration-ref",
        default=None,
        help="ref that means merged (default: origin/main|main|...)",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    scan = sub.add_parser("scan", help="read-only: classify all worktrees")
    scan.set_defaults(func=cmd_scan)

    reap = sub.add_parser("reap", help="remove one explicit, merged, clean worktree")
    reap.add_argument("path", help="exact worktree path to remove")
    reap.add_argument(
        "--delete-branch",
        action="store_true",
        help="also delete the branch afterward (git branch -d; merged-only)",
    )
    reap.set_defaults(func=cmd_reap)
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
