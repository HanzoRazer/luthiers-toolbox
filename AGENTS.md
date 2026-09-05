# Agent instructions — luthiers-toolbox

Read this before creating a branch or opening a pull request. It is read by
Cursor, Codex, and other coding agents; `CLAUDE.md` carries the
project and architecture context and applies too.

## Branch from current `main`. Always.

```bash
git fetch origin
git switch -c <branch-name> origin/main
```

Not from the workspace's current `HEAD`. Not from another branch. Not from a
branch belonging to a pull request that has not merged yet.

This is not style.

> **Drafted 2026-09-05 from witnessed incidents in a single working session.
> Pending owner review.** Every item below happened in this repository; none is
> illustrative. Correct or delete anything that misstates the record.

**A stale checkout nearly closed a live defect as "already fixed."** The CBSP21
manifest-borrowing defect (later PR #352) was reproduced from the primary
checkout, which sat on a feature branch 318 commits behind `main`. From there
only **8** patch manifests were visible instead of **119**, the gate returned RED,
and the obvious conclusion was that the defect no longer existed. It did. Re-running
the identical reproduction against current `main` showed the borrow live and the
gate passing. Had the first reading been trusted, a real defect would have been
filed as resolved on the strength of a stale tree.

**A branch 318 commits behind nearly deleted 420 lines.** `SPRINTS.md` carried 86
lines of recovered work on that same branch. Committing the *file* would have
carried its 2,543 lines over `main`'s 2,963 — silently dropping 420 lines of
everything merged since July. The risk was never in the recovered text; it was in
the base underneath it. The fix was to recover the *content* onto current `main`,
not the file.

**A stale `origin/main` ref made another session's work look like mine.** Preparing
a PR, `git diff origin/main...HEAD` reported **50 files** including drilling,
profiling and session-store changes belonging to other people. The ref had not been
fetched. After `git fetch`, the true diff was **5 files**. Opening that PR would
have appeared to claim four other sessions' work.

**A branch that predates the merges reads as a revert.** A governance branch pushed
days earlier showed **~120 files** against current `main` — not because it changed
them, but because it was cut before they landed. As a PR it would have read as
reverting the audits, the RMOS work and the report bundles.

If your branch is not cut from current `main`, "make it match
`main`" and "keep my changes" start pulling in opposite directions,
and no mechanical resolution is correct any more.

## If `main` moves while your branch is open

Merge, do not rebase:

```bash
git fetch origin && git merge origin/main
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
# The merge base must BE the tip of main, not merely an ancestor.
test "$(git merge-base HEAD origin/main)" = "$(git rev-parse origin/main)" \
  && echo "base is current" || echo "STALE — read this file again"
```

If the merge base turns out to be the head of an open pull request rather than
an old commit on `main`, you are stacked on unmerged work: do not
rebase, see above.

## Verifying locally

> **Drafted 2026-09-05, copied verbatim from the workflow files. Pending owner
> review.** There is no root `pyproject.toml`; the Python surface lives in
> `services/api`, and **the working directory differs per gate**. Running a gate
> from the wrong directory is its own failure mode — it silently exercises a
> different tree.

**Short list — run these before opening a PR.**

```bash
# 1. CBSP21 manifest gate. This PR must bring its OWN manifest under
#    .cbsp21/patches/ — since PR #352 a manifest belonging to another change
#    can no longer satisfy yours. Run from the repo root.
python scripts/ci/check_cbsp21_gate.py --changed-files $(git diff --name-only origin/main...HEAD)

# 2. The CBSP21 ownership regressions (repo root). Uses -k rather than a glob:
#    CI runs `scripts/ci/test_cbsp21_*.py` inside a bash step, where the shell
#    expands it. PowerShell does not expand globs, so the literal pattern is
#    passed to pytest and it errors with "file or directory not found".
python -m pytest scripts/ci/ -k cbsp21 -v

# 3. Whatever you touched, from services/api — NOT the repo root.
cd services/api && python -m pytest <your test paths> -q --no-cov
```

**Full CI set, with the directory each runs from.**

| Gate | Working directory | Command |
|---|---|---|
| CBSP21 manifest | repo root | `python scripts/ci/check_cbsp21_gate.py --changed-files ...` |
| CBSP21 patch input | repo root | `python3 scripts/ci/check_cbsp21_patch_input.py --base "$BASE" --head "$HEAD"` |
| CBSP21 ownership tests | repo root | `python -m pytest scripts/ci/test_cbsp21_*.py -v` |
| Governance unit tests | repo root | `python -m pytest scripts/ci/test_check_contracts_governance.py -v` |
| Execution-class compliance | `services/api` | `python -m app.ci.check_execution_class_compliance` |
| Complexity ratchet | `services/api` | `python -m app.ci.check_complexity --baseline app/ci/complexity_baseline.json` |
| File-size ratchet | `services/api` | `python -m app.ci.check_file_sizes --baseline app/ci/file_sizes_baseline.json` |
| Bare-except check | `services/api` | `python -m app.ci.check_bare_except` |
| Safety fences | `services/api` | `python -m app.ci.fence_checker_v2` |
| Duplication | `services/api` | `python -m app.ci.check_duplication --threshold 100` |
| API Tests | `services/api` | `python -m pytest -q app/tests/` |
| Core CI suite | `services/api` | `python -m pytest -q` (bare — `testpaths = tests` collects ~8,900 tests) |

**Two traps in that table.** `app/tests/` and `tests/` are *different trees* — "API
Tests" runs the first, Core CI's bare `pytest -q` collects the second. And that
bare invocation takes its scope from `pytest.ini`, not the command line, so
grepping workflows for path arguments will miss it entirely.

**Interpreter:** use `py -3.11`. The default `python` on this machine is a broken
3.14. A local red on the wrong interpreter is a claim about your environment, not
about the code — check the toolchain against `services/api/requirements.txt` before
reporting a failure.
