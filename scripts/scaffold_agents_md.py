#!/usr/bin/env python3
"""Scaffold AGENTS.md + a PR template into a repo — universal rules verbatim,
repo-specific parts left as explicit human-fill TODOs.

DESIGN PRINCIPLE (the thing that keeps this from becoming overreach):
    This scaffolds a SKELETON. It does NOT write the incident story and does
    NOT invent the verification gates — those are facts only the repo's owner
    knows, and a script that fabricates them recreates the fabricated-anchor
    problem. Universal rules (branch-from-main, merge-don't-rebase, the
    self-check) are written verbatim. Everything repo-specific is a marked
    TODO the human must fill or delete.

    It also NEVER overwrites an existing AGENTS.md or PR template. If one
    exists, it reports and stops for that file — you adapt by hand, because a
    repo that already has agent instructions has context this script can't see.

USAGE:
    python scaffold_agents_md.py /path/to/repo             # write the files
    python scaffold_agents_md.py /path/to/repo --dry-run   # print, write nothing
    python scaffold_agents_md.py /path/to/repo --force --yes  # overwrite

WHAT IT AUTO-DETECTS (safely, from files on disk):
    - default branch name (main vs. other)
    - requires-python from pyproject.toml (to seed the interpreter note)
    - whether AGENTS.md / a PR template (ANY casing) / CLAUDE.md already exist

WHAT IT LEAVES FOR THE HUMAN (never guessed):
    - the incident story (the reason the rule exists in THIS repo)
    - the exact verification gate commands (mypy targets, coverage threshold)
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

# ── universal content (written verbatim — repo-independent) ──────────

_AGENTS_UNIVERSAL = '''\
# Agent instructions — {repo_name}

Read this before creating a branch or opening a pull request. It is read by
Cursor, Codex, and other coding agents; `CLAUDE.md`{claude_note} carries the
project and architecture context and applies too.

## Branch from current `{default_branch}`. Always.

```bash
git fetch origin
git switch -c <branch-name> origin/{default_branch}
```

Not from the workspace's current `HEAD`. Not from another branch. Not from a
branch belonging to a pull request that has not merged yet.

This is not style.

<!-- INCIDENTS ─────────────────────────────────────────────────────────
     Replace this block with THIS repo's actual stale-base failures, in the
     shape below. If this repo has had none yet, delete the block and keep
     just the rule above — but the rule reads as style advice without a
     story, so add the story the first time it bites.

     Example shape (from another repo, DO NOT copy verbatim — use your own):
       Three PRs in a row (#12, #13, #14) were opened off a stale head and
       each had to be reconciled by hand. #14 branched off #12's head; merging
       it as submitted would have reverted #13 and deleted four files. Two
       automated reviews advised "rebase onto main" — which would have
       discarded merged work silently.
──────────────────────────────────────────────────────────────────────── -->

If your branch is not cut from current `{default_branch}`, "make it match
`{default_branch}`" and "keep my changes" start pulling in opposite directions,
and no mechanical resolution is correct any more.

## If `{default_branch}` moves while your branch is open

Merge, do not rebase:

```bash
git fetch origin && git merge origin/{default_branch}
```

A rebase rewrites shas a reviewer has already read, and on a branch that was
cut from unmerged work it drops that work without saying so.

## Before you start

Check whether an open pull request already touches the surface you are about
to change:

```bash
gh pr list --state open --json number,title,headRefName,files
```

If one does, say so and stop rather than implementing the same order twice.
Nothing will catch this for you.

## One dev order per branch

Do not fold an adjacent fix into an open order because it is convenient. If a
governance document names the authorized surfaces for a change, changing
anything else needs an owner ruling first — say so in the PR body rather than
merging it quietly.

## Nothing enforces this. Check it yourself.

There is no bot and no gate for the base rule. This file is the only thing
standing between you and the failure above. Before you open a pull request:

```bash
# The merge base must BE the tip of {default_branch}, not merely an ancestor.
test "$(git merge-base HEAD origin/{default_branch})" = "$(git rev-parse origin/{default_branch})" \\
  && echo "base is current" || echo "STALE — read this file again"
```

If the merge base turns out to be the head of an open pull request rather than
an old commit on `{default_branch}`, you are stacked on unmerged work: do not
rebase, see above.

## Verifying locally

<!-- VERIFICATION GATES ────────────────────────────────────────────────
     Replace with THIS repo's actual gate commands, on the interpreter CI
     uses. Do not guess — copy them from this repo's CI workflow. The
     detected Python hint below is a starting point, not the answer.
{python_hint}
     Typical shape (adapt to reality):
       ruff check .
       mypy <packages> ...
       pytest --cov=<package> --cov-fail-under=<N>
──────────────────────────────────────────────────────────────────────── -->
'''

_PR_TEMPLATE = '''\
## What this changes
<!-- One or two sentences. What is different after this merges. -->

## Base
- [ ] Branched from the current tip of `{default_branch}` (not from another PR's branch)
- [ ] No other open PR touches these files, or the overlap is deliberate and named below
<!--
    git fetch origin && git switch -c <branch> origin/{default_branch}
    gh pr list --state open --json number,title,headRefName,files
If `{default_branch}` moved while this was open, merge it in — do not rebase.
Nothing checks this automatically. AGENTS.md explains what it cost last time.
-->

## Scope
- [ ] Every file changed is within the authorized surface for this dev order
- [ ] Anything outside it is called out below and awaits an owner ruling

## Verification
<!-- Which gates were actually run, on which interpreter. Fill from AGENTS.md. -->
- [ ] lint
- [ ] type checks
- [ ] tests with coverage
'''


def _run(cmd: List[str], cwd: Path) -> Optional[str]:
    try:
        out = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=15)
        return out.stdout.strip() if out.returncode == 0 else None
    except (subprocess.SubprocessError, OSError):
        return None


def detect_default_branch(repo: Path) -> str:
    # origin/HEAD symbolic ref is the truth; fall back to main, but say so.
    ref = _run(["git", "symbolic-ref", "refs/remotes/origin/HEAD"], repo)
    if ref and "/" in ref:
        return ref.rsplit("/", 1)[-1]
    # local guess
    for cand in ("main", "master"):
        if _run(["git", "rev-parse", "--verify", cand], repo):
            return cand
    return "main"  # last resort; the human should confirm


def detect_python_hint(repo: Path) -> str:
    pp = repo / "pyproject.toml"
    if pp.exists():
        text = pp.read_text(encoding="utf-8", errors="replace")
        m = re.search(r'requires-python\s*=\s*["\']([^"\']+)["\']', text)
        if m:
            return f"     Detected requires-python = {m.group(1)} (confirm against CI)."
    return "     No requires-python detected; confirm the interpreter against CI."


def has_claude_md(repo: Path) -> bool:
    return (repo / "CLAUDE.md").exists()


def detect_repo_name(repo: Path) -> str:
    """Repo name from the origin remote, not the directory name.

    A git worktree lives in a directory named for the branch or the task
    (`ltb-sprints`, `cl-033`), so `repo.name` writes the wrong name into the
    heading of every file scaffolded from a worktree. The remote URL is the
    repository's actual identity; fall back to the directory only when there
    is no remote.
    """
    url = _run(["git", "remote", "get-url", "origin"], repo)
    if url:
        tail = url.rstrip("/").rsplit("/", 1)[-1]
        if tail.endswith(".git"):
            tail = tail[:-4]
        if tail:
            return tail
    return repo.name


def _confirm_overwrite(rel: Path) -> bool:
    """Ask, but treat an unreadable stdin as "no" rather than crashing.

    isatty() is not sufficient on its own: in some terminals it reports True
    while stdin still has nothing to read, so input() raises EOFError anyway --
    and it does so *after* the first file has been written. Catching it here
    turns a half-completed overwrite into a clean skip.
    """
    try:
        return input(f"OVERWRITE {rel}? [y/N] ").strip().lower() == "y"
    except (EOFError, KeyboardInterrupt):
        print(f"\nno readable stdin — skipping {rel} (use --yes to overwrite)")
        return False


def find_pr_templates(repo: Path) -> List[Path]:
    """Every existing PR template, in any casing, anywhere GitHub looks.

    An exact-path check for `.github/pull_request_template.md` is wrong twice
    over. On a case-insensitive filesystem it appears to work while silently
    matching a differently-cased file; on Linux it misses
    `PULL_REQUEST_TEMPLATE.md` entirely and writes a SECOND template beside it,
    and GitHub's precedence between two templates is not obvious. So glob and
    compare case-folded, and report everything found.

    GitHub honours the template at the repo root, in `.github/`, and in
    `docs/`, so all three are searched.
    """
    found: List[Path] = []
    for directory in (repo / ".github", repo, repo / "docs"):
        if not directory.is_dir():
            continue
        for entry in directory.iterdir():
            if entry.is_file() and entry.name.casefold() == "pull_request_template.md":
                found.append(entry)
    return found


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("repo", type=Path)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument(
        "--yes",
        action="store_true",
        help="Confirm --force without prompting. Required with --force when "
             "stdin is not a TTY.",
    )
    args = ap.parse_args()

    repo = args.repo.resolve()
    if not (repo / ".git").exists():
        print(f"ERROR: {repo} is not a git repo (no .git). Refusing.", file=sys.stderr)
        return 2

    # Refuse --force headlessly BEFORE writing anything. Calling input() in a
    # non-interactive session raises EOFError, and it would do so only after
    # the first file had already been written -- a half-completed overwrite is
    # worse than a clean refusal.
    if args.force and not args.yes and not sys.stdin.isatty():
        print(
            "ERROR: --force needs --yes when stdin is not a TTY.\n"
            "       Refusing now rather than failing part-way through.",
            file=sys.stderr,
        )
        return 2

    default_branch = detect_default_branch(repo)
    python_hint = detect_python_hint(repo)
    claude_note = "" if has_claude_md(repo) else " (not present in this repo yet)"
    repo_name = detect_repo_name(repo)

    agents = _AGENTS_UNIVERSAL.format(
        repo_name=repo_name,
        default_branch=default_branch,
        python_hint=python_hint,
        claude_note=claude_note,
    )
    pr_template = _PR_TEMPLATE.format(default_branch=default_branch)

    print(f"repo: {repo_name}   default branch: {default_branch}")
    if default_branch not in ("main", "master"):
        print("  note: unusual default branch — confirm it's correct.")

    existing_templates = find_pr_templates(repo)
    if existing_templates:
        print("  PR template(s) already present:")
        for t in existing_templates:
            print(f"    - {t.relative_to(repo)}")
    print()

    targets = [
        (repo / "AGENTS.md", agents, bool((repo / "AGENTS.md").exists())),
        (
            repo / ".github" / "pull_request_template.md",
            pr_template,
            bool(existing_templates),
        ),
    ]

    wrote_any = False
    for path, content, exists in targets:
        rel = path.relative_to(repo)
        if exists and not args.force:
            print(f"SKIP  {rel} — already exists. Adapt by hand (has context this "
                  f"script can't see). Use --force --yes to overwrite.")
            continue
        if args.dry_run:
            print(f"--- would write {rel} ---")
            print(content)
            print()
            continue
        if exists and args.force and not args.yes:
            if not _confirm_overwrite(rel):
                continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        print(f"WROTE {rel}")
        wrote_any = True

    if wrote_any and not args.dry_run:
        print()
        print("NOT DONE — two things only you can fill in AGENTS.md:")
        print("  1. The INCIDENTS block: this repo's own stale-base story "
              "(or delete it if none yet).")
        print("  2. The VERIFICATION GATES block: the real gate commands from "
              "this repo's CI — do not guess them.")
        print("Both are marked with <!-- ... --> in the file.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
