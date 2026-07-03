# CI-RED-020-B — API Health + Smoke Nightly Witness Recovery

Status: Dev-ready handoff
Created: 2026-07-02
Baseline: origin/main at 53bbf1a2 (#176 merged)
Recommended branch: fix/ci-red-020b-api-health-smoke-nightly-witness
Owner lane: CI / smoke-witness hygiene

> This is the durable, tracked copy of the CI-RED-020-B dev order (previously only
> pasted). It is amended by [`CI_RED_020B_addendum.md`](./CI_RED_020B_addendum.md),
> which sharpens four items (measured step-timeout, exit-code-preserving trap,
> promoted+extended guard test, api-verify-hang stop-and-ask). Read the addendum
> before implementing.

## Purpose

Restore the scheduled API Health + Smoke workflow as a real nightly witness.
The current board has no open PRs or issues, and push CI on main is green, but API Health + Smoke
has not produced a successful scheduled witness for many days. The latest observed run on main was:

    Workflow: API Health + Smoke
    Run:      28582967855
    Event:    schedule
    SHA:      53bbf1a2
    Result:   cancelled
    URL:      https://github.com/HanzoRazer/luthiers-toolbox/actions/runs/28582967855

This is CI-RED-020 follow-up work, but it is not the original API-readiness failure. CI-RED-020-A
added the shared readiness harness. CI-RED-020-B is about the nightly workflow failing to reach its
actual smoke witness.

## Grounding Evidence

Recent main runs for API Health + Smoke are persistently non-successful:

    2026-07-02 schedule cancelled 53bbf1a2 run 28582967855
    2026-07-01 schedule cancelled 7a753147 run 28511978582
    2026-06-30 schedule cancelled 0daeab14 run 28438339830
    2026-06-29 schedule cancelled 0daeab14 run 28368134432
    2026-06-28 schedule failure   9c9406f6 run 28319105064
    2026-06-27 schedule cancelled e2d17849 run 28286294456

The latest run did not fail because the smoke post harness reported a bad endpoint result. It timed
out while still in the best-effort API verification step:

    10:24:08 Run API health (best-effort): make api-verify
    10:43:31 The operation was canceled.
    10:43:31 smoke_posts.json missing; no smoke artifact uploaded
    10:43:39 orphan processes cleaned up

The workflow name says health and smoke, but the early step is running the full api-verify target.
That target expands into boundary checks plus the broad API test suite. On the observed run, it used
the entire 20-minute job window and prevented the actual smoke step from starting.

## Scope

Fix the nightly witness path so the scheduled workflow:

- installs dependencies,
- runs the dedicated smoke harness,
- waits for API readiness through `scripts/ci/wait_for_api_ready.py`,
- executes `scripts/smoke/api_smoke_posts.py`,
- uploads `smoke_posts.json`,
- produces badge/report artifacts,
- and exits as success or meaningful failure, not timeout-cancelled.

The target is the workflow's witness shape, not application behavior.

## Non-Goals

- Do not weaken API readiness requirements.
- Do not remove the `router_count>0` readiness assertion from the smoke harness.
- Do not make API Health + Smoke responsible for the full API test suite.
- Do not treat a real smoke endpoint failure as fixed by changing workflow timing.
- Do not reopen CI-RED-019 packaging work, branch protection work, or C2/GAMS governance decisions.
- Do not merge or delete existing user worktree changes from the main checkout.

## Decisions

1. **Nightly smoke is not full API verification.** The full api-verify path belongs to Core CI, API
   Tests, and related push/PR checks. The nightly smoke workflow should prove server readiness plus
   post smoke behavior.
2. **The best-effort health step is currently harmful.** It is labeled best-effort, but it can
   consume the whole job timeout before the smoke witness runs. Remove it or replace it with a small
   preflight that cannot run the broad test suite.
3. **Preserve the CI-RED-020-A readiness harness.** `scripts/smoke/run_api_smoke_posts.sh` should
   remain the entry point for booting uvicorn, waiting for `/api/health` with `router_count>0`, and
   running post smoke.
4. **Make cancellation diagnosable.** A future cancelled workflow should be separable into one of
   these causes: full-suite regression accidentally reintroduced, smoke startup timeout, endpoint
   smoke failure, Pages deployment/environment issue, or external GitHub cancellation.
5. **Keep Pages deployment secondary to the witness.** Badge deployment is useful, but the first
   acceptance condition is a completed smoke artifact. If Pages creates a separate
   cancellation/failure after smoke succeeds, split that into a follow-up.

## File-by-File Patch Plan

### `.github/workflows/api_health_and_smoke.yml`

Primary change. Remove the `Run API health (best-effort)` step that invokes `make api-verify`.
Replace it, if desired, with a cheap preflight such as: verify Makefile has `api-smoke-posts`,
verify `scripts/smoke/run_api_smoke_posts.sh` exists, print the workflow purpose.

Keep `Run v15.5 smoke (all presets)` as the first behavior-bearing check after dependency install.
Add a step-level timeout to the smoke step (e.g. `timeout-minutes: 8` or `10`) so a hung smoke has a
named failure before the job-level timeout. Keep the job-level timeout, but do not rely on it as the
primary control.

Consider making artifact/report/badge steps conditional on smoke output where appropriate:
- `smoke_posts.json` upload: `if: always()`, warn if missing.
- size regression: fail clearly if `smoke_posts.json` is missing after the smoke step.
- badge generation: can still run with an empty failure badge, but should not hide the missing smoke
  witness.

Keep Pages deployment in place for this pass unless it continues to cause cancellation after smoke
succeeds.

### `scripts/smoke/run_api_smoke_posts.sh`

Secondary hardening. Preserve current behavior: boot uvicorn from `services/api`, write `uvicorn.log`,
write `uvicorn.pid`, call `scripts/ci/wait_for_api_ready.py`, run `scripts/smoke/api_smoke_posts.py`.

Improve cleanup so the server is terminated and reaped deterministically: read PID once, send TERM,
wait briefly for exit, escalate only if still alive, remove the PID file after cleanup. Keep cleanup
safe on Windows/local shells by guarding POSIX-only behavior where needed. Do not change readiness
semantics or smoke endpoint coverage.

### `scripts/ci/wait_for_api_ready.py`

No production change expected. Use as-is unless the implementation discovers a readiness diagnostic
gap. If edited, keep it stdlib-only and preserve existing tests.

### `scripts/ci/test_wait_for_api_ready.py`

No required change. Run as a regression witness after any readiness-harness edits.

### New optional guard test: `scripts/ci/test_api_health_and_smoke_workflow.py`

Add only if the implementing sprint wants a local regression guard. Recommended assertions:
- `.github/workflows/api_health_and_smoke.yml` does not contain `make api-verify`.
- The workflow still invokes `make api-smoke-posts` or `scripts/smoke/run_api_smoke_posts.sh`.
- The workflow still uploads `smoke_posts.json`.
- The workflow still includes a scheduled trigger.

This can be a text-level workflow test. It is intentionally a policy guard, not a YAML framework.

### `Makefile`

Likely no change. Keep `api-smoke-posts` as the smoke entry point. Do not make it depend on
`api-verify`.

### `SPRINTS.md` or sprint ledger

Update only after the fix is witnessed. Add/adjust CI-RED-020-B status with the run URL proving the
nightly/manual witness. Do not mark CI-RED-020 fully closed if a separate Pages or endpoint failure
remains.

## Utilities

Existing utilities to use: `scripts/ci/wait_for_api_ready.py`, `scripts/ci/test_wait_for_api_ready.py`,
`scripts/smoke/run_api_smoke_posts.sh`, `scripts/smoke/api_smoke_posts.py`, Makefile target
`api-smoke-posts`, GitHub CLI (`gh run list`, `gh run view`, `gh workflow run`).

Suggested inspection commands:

    gh run list --workflow "API Health + Smoke" --branch main --limit 12
    gh run view <run-id> --log
    gh run view <run-id> --json jobs,conclusion,status,event,createdAt,updatedAt,url

Suggested local smoke command on a Unix-like shell:

    bash scripts/smoke/run_api_smoke_posts.sh "http://127.0.0.1:8000" "127.0.0.1" "8000"

On Windows, validate script syntax and the readiness utility locally, then rely on GitHub's Ubuntu
runner for the final shell/process witness.

## Test Cases

**Unit / local guard.** Run the existing readiness tests
(`python -m pytest scripts/ci/test_wait_for_api_ready.py`). If added, run the workflow guard
(`python -m pytest scripts/ci/test_api_health_and_smoke_workflow.py`) — expected to fail if
`make api-verify` is reintroduced into the workflow.

**Shell smoke witness.** Run the smoke harness on an Ubuntu runner or compatible shell
(`bash scripts/smoke/run_api_smoke_posts.sh "http://127.0.0.1:8000" "127.0.0.1" "8000"`). Expected:
`/api/health` returns HTTP 200 satisfying `router_count>0`; `smoke_posts.json` is created; the script
exits 0 when smoke is healthy; no leftover uvicorn process remains.

**Workflow witness.** Use `workflow_dispatch` on the PR branch after pushing
(`gh workflow run "API Health + Smoke" --ref <branch-name>`). Expected: the workflow reaches
`Run v15.5 smoke (all presets)`; `smoke_posts.json` is uploaded; the job conclusion is `success` if
smoke is healthy, or `failure` with a direct smoke/readiness reason if the API is unhealthy; the job
conclusion is **not** `cancelled`.

**Merge witness.** After merge, watch the next scheduled main run. Expected: scheduled run completes
as `success` or meaningful `failure`. If it still cancels after smoke succeeds, split the remaining
issue as a Pages/environment deployment cancellation follow-up rather than relabeling CI-RED-020-B.

## Rollout Order

1. Create an isolated worktree from current origin/main.
2. Patch `.github/workflows/api_health_and_smoke.yml` to remove the full api-verify detour.
3. Harden `scripts/smoke/run_api_smoke_posts.sh` cleanup if local inspection confirms it can leave
   unreaped uvicorn processes.
4. Add the optional workflow guard test if the sprint wants a permanent ratchet.
5. Run portable local tests (readiness utility tests, workflow guard tests, script syntax checks).
6. Push branch and open PR.
7. Trigger API Health + Smoke manually on the PR branch.
8. Confirm the workflow reaches smoke and uploads `smoke_posts.json`.
9. Merge only after the manual witness is terminal and non-cancelled.
10. Watch the next scheduled main run and update the sprint ledger with the run URL.

## Acceptance Criteria

Done when:
- API Health + Smoke no longer runs `make api-verify`.
- The dedicated smoke harness is the workflow's behavior-bearing check.
- A manual workflow run on the branch reaches the smoke step and uploads `smoke_posts.json`.
- A terminal workflow result is produced: `success` for healthy smoke, or `failure` with a direct
  readiness/smoke reason.
- The run is not cancelled by job timeout before smoke executes.
- Existing push CI remains green.

Not done if the workflow simply increases timeout while still running the full API suite before
smoke.

## Stop-and-Ask Conditions

Stop and ask before continuing if:
- The proposed fix removes or weakens `router_count>0`.
- The workflow begins passing without producing `smoke_posts.json`.
- The smoke endpoint itself fails after the workflow reaches it; classify that separately before
  changing smoke semantics.
- Pages deployment remains the only cancellation/failure after smoke succeeds.
- Fixing this appears to require repository settings or GitHub environment protection changes.

(See the addendum for a fifth stop-and-ask: api-verify appearing to hang rather than merely run long.)
