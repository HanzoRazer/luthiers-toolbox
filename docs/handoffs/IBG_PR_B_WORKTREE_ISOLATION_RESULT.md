# IBG-1 PR B — Repository Worktree Isolation & Proposal Workspace — Result

> **What this is:** the isolated repository workspace layer for IBG repository proposals. It lets a
> governed proposal be assembled inside a disposable, verified worktree **without** granting IBG any
> authority to mutate the canonical repository.

---

## Provenance (state witness — verify, do not assume)

```
BASE:         main
THIS (PR B):  feature/ibg-repository-worktree-isolation
PR A:         repository proposal contracts merged via #213 (03e68a7c)
VERIFY:       gh pr view 216 --json baseRefName,headRefName
```

## Constitutional boundary (what this layer may and may NOT do)

**May:** create / list / remove **disposable worktrees** confined beneath one configured temp root;
read repository state (clean?, current revision, branch exists?, worktree list).

**May NOT — no method exists anywhere in the layer for any of these:** commit · push · merge ·
reset · clean · checkout the active tree · delete a foreign branch or worktree · call GitHub · any
network operation · promote evidence · grant canonical authority · mutate the canonical checkout.

The only sanctioned mutation is a **temp-root-confined `git worktree add` / `git worktree remove`**,
issued only through an explicitly injected, temp-root-scoped runner.

## What shipped

| Module (`services/api/app/ibg_repository/`) | Role |
|---|---|
| `worktree_state.py` | `RepositoryWorktreeState` forward-only lifecycle: NEW→CREATED→READY / FAILED / DISPOSED (descriptive metadata, never authority) |
| `worktree_spec.py` | `RepositoryWorktreeSpec` (frozen) + `derive_workspace_id` / `derive_branch_name` / `normalize_allowed_paths`. Workspace id/branch derived from the content-addressed `rcp-` proposal id — **never a timestamp** |
| `git_runner.py` | `GitRunner` protocol (seven sanctioned read/worktree ops only) + `LocalGitRunner` real adapter: explicit repository root **and** temp root required, git run through an injected command seam with **explicit argv (no shell)**, every worktree path confined beneath temp root, fail-closed on non-zero exit |
| `worktree_validator.py` | Fail-closed pre-flight gate: deterministic-naming, temp-root path confinement, repository reachable, base revision resolves, branch well-formed & absent, no existing worktree, clean tree (override explicit) |
| `worktree_builder.py` | `RepositoryWorktreeBuilder`: `plan_from_proposal` (pure), `create` (validate → materialize one worktree → record ownership; partial create failure attempts registered-worktree cleanup), `dispose` (removes **only** a worktree this builder instance owns) |

Deterministic naming: `rcp-8123ab91` → workspace `wt-8123ab91` → branch `ibg-worktree/wt-8123ab91`.
Worktree path = `<temp_root>/wt-8123ab91`.

## Safety interlocks (fail-closed)

- **No silent root default.** Both `LocalGitRunner` and `RepositoryWorktreeBuilder` require an
  explicit repository root and temp root; neither falls back to a developer/production path.
- **Path confinement.** Any worktree path outside the configured temp root, or containing `..`, is
  rejected before any git command is issued.
- **Ownership interlock.** `dispose()` removes only a worktree recorded as owned by that builder
  instance. A foreign worktree — even one under the same temp root — cannot be removed through the
  builder. Two builders do not share ownership.
- **Argv, not shell.** Real git runs as an explicit token list (`["git","-C",repo,"worktree",…]`);
  there is no shell string and no interpolation surface (asserted by test).

## Verification (witnessed at PR B tip on branch `feature/ibg-repository-worktree-isolation`)

```
python -m pytest tests/ibg_repository/ -q -o addopts=""         -> 148 passed
  (PR A contracts + PR B worktree layer, run together, all green)
new-package coverage (worktree_state/spec/git_runner/validator/builder) -> 98%
  (remaining lines are defensive/unreachable guards; target was >95%)
one bounded real-git integration test (tmp_path init→add→list→remove) -> passed
```

Test environment note: run with the project venv interpreter
(`services/api/.venv/Scripts/python.exe`, Python 3.11.9) and `-o addopts=""` for targeted runs — the
repo's default `addopts` enforce a `--cov-fail-under` on unrelated safety modules that a scoped
subset run cannot satisfy.

## What this sprint did NOT do (non-goals, deferred to later sprints)

Router/API wiring · GitHub API · draft-PR creation/metadata · commit/push/merge · approver seeding ·
canonical authority changes · any repository mutation beyond controlled worktree creation. These
belong to PR C and later IBG proposal-pipeline sprints.

## Acceptance question (answer: **yes**)

> Can IBG now create a deterministic, isolated, and constitutionally safe workspace for repository
> proposals **without** gaining the ability to modify the canonical repository?

Yes — the builder materializes exactly one disposable, temp-root-confined worktree per governed
proposal through a seven-operation git seam that has no commit/push/merge/authority capability, and the
disposal ownership interlock ensures it can only ever tear down what it itself created.
