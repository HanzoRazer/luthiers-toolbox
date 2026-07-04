# ADDENDUM A — CI-RED-020-B dev order

**Amends:** [`CI_RED_020B_dev_order.md`](./CI_RED_020B_dev_order.md) — File-by-File Patch Plan
(`.github/workflows/api_health_and_smoke.yml`, `scripts/smoke/run_api_smoke_posts.sh`, the guard
test) + Stop-and-Ask Conditions.

**Reason:** the dev order is correct on the spine (the failure is a *scope* bug — a workflow named
"Health + Smoke" front-loads the full `api-verify` target and starves the actual witness), but it
undersells three load-bearing details and omits one diagnostic guard. This addendum makes them
pick-up-and-run so the implementer folds them in without re-deriving. It is written against the real
files at `origin/main` `53bbf1a2` — cited by step name and line number so edits are by reference, not
by search.

**Grounded file map (verify these line numbers still hold before editing):**

- `.github/workflows/api_health_and_smoke.yml`
  - job `health-smoke`, `timeout-minutes: 20` (L20), `environment: github-pages` (L21–23)
  - **`Run API health (best-effort)` — L55–63** — the culprit; `continue-on-error: true`, runs
    `make api-verify`. **This is the step to remove.** (`api-verify` = Makefile L56 =
    `check-art-studio-scope check-boundaries api-test` → boundary checks **plus the broad `api-test`
    suite**.)
  - **`Run v15.5 smoke (all presets)` — L66–74** — the real witness; runs `make api-smoke-posts`
    (Makefile L61–64 → `bash scripts/smoke/run_api_smoke_posts.sh`). **Has no step-level timeout.**
  - Everything downstream is `if: always()`: `Upload smoke_posts.json` (L76–82), `Size regression
    check` (L152–218, **note: no `if:` → runs only on `success()`**), `Delta report` (L263, always),
    `Build badge JSONs` (L330, always), `Configure Pages`/`Upload Pages artifact`/`Deploy to GitHub
    Pages` (L406–421, all always).
- `scripts/smoke/run_api_smoke_posts.sh` — **already has** `trap cleanup EXIT` (L22–28) and
  `exit $?` after the smoke call (L55–56). `cleanup` reads the PID once, `kill … 2>/dev/null || true`,
  `rm -f` the pidfile, and makes **no `exit` call** — so it already preserves the smoke exit code
  *implicitly*.

---

## Item 1 — The smoke step-timeout is the load-bearing change; measure it, don't guess it

**Applies to:** `Run v15.5 smoke (all presets)` (L66–74).

The dev order lists `timeout-minutes: 8` as "for example." It is not an example — it is *the*
deliverable. A **step-level** timeout converts the failure class from `cancelled` (ambiguous, what the
board shows today) to `failure` (named, attributable). The job-level `timeout-minutes: 20` cannot do
this: when it fires it cancels the job, which is exactly the unattributable outcome we are removing.
Acceptance criterion "not cancelled by job timeout before smoke executes" depends on this step timeout
existing.

But **do not commit a guessed `8`.** A step timeout below a *healthy* smoke's real wall-time is a
spurious-red — the vacuous-green trap's evil twin: it false-fails slow-but-healthy smokes. Nobody has
measured a healthy smoke's wall-time yet, and it cannot be measured on Windows (local app import
exceeds the smoke's own budget). So measure it on the runner, two-pass:

1. **First dispatch (provisional):** set the smoke step to a deliberately generous provisional value
   that is still safely below the 20-minute job timeout:
   ```yaml
   - name: Run v15.5 smoke (all presets)
     shell: bash
     timeout-minutes: 12   # PROVISIONAL — replaced by ~2x measured green wall-time (Item 1)
     run: |
       if [ -f Makefile ] && make -n api-smoke-posts >/dev/null 2>&1; then
         make api-smoke-posts
       else
         echo "Missing Makefile or 'api-smoke-posts' target."
         exit 1
       fi
   ```
2. **Measure:** run the workflow via `workflow_dispatch` on the branch, let it reach a *green* smoke,
   and read that step's actual duration from `gh run view <id> --json jobs` (or the step timing in the
   run UI). A healthy smoke is boot-uvicorn + `wait_for_api_ready` (≤60s) + posts — expect low
   single-digit minutes, but **use the observed number, not this expectation.**
3. **Set:** replace the provisional with `timeout-minutes: <ceil(~2 × observed green seconds → minutes)>`
   and record the observed value in the PR body (e.g. "green smoke = 2m10s → step timeout 5"). ~2× the
   measured green gives headroom for cold-cache/runner variance without letting a genuine hang run to
   the job timeout.

Keep the job-level `timeout-minutes: 20` as a backstop; it is no longer the primary control.

---

## Item 2 — Harden the EXISTING trap; make exit-code preservation explicit (do not add a naive trap)

**Applies to:** `scripts/smoke/run_api_smoke_posts.sh` `cleanup` (L22–28).

Correction to the original framing: the script does **not** have a naive `trap 'kill $PID' EXIT` that
clobbers the exit code. It already has a well-formed `cleanup` trap that preserves the smoke's exit
code *implicitly* (it makes no `exit` call). The hazard is not present today — it becomes **reachable**
the moment someone adds the TERM→wait→escalate→reap logic the dev order asks for and slips an `exit`
(or a status-leaking final command under some shells) into the trap body. A meaningful smoke
`failure` silently turning back into success/noise directly violates the "meaningful failure, not
cancelled" goal.

So when you add deterministic reaping, **keep the implicit preservation and make it explicit** — capture
the status on entry and restore it on exit:

```bash
cleanup() {
  rc=$?                                   # capture the real smoke/readiness status FIRST
  if [ -f "$UVICORN_PID_FILE" ]; then
    pid="$(cat "$UVICORN_PID_FILE" 2>/dev/null || true)"
    if [ -n "${pid:-}" ]; then
      kill -TERM "$pid" 2>/dev/null || true
      for _ in 1 2 3 4 5 6 7 8 9 10; do   # wait briefly for graceful exit (~5s)
        kill -0 "$pid" 2>/dev/null || break
        sleep 0.5
      done
      kill -0 "$pid" 2>/dev/null && kill -KILL "$pid" 2>/dev/null || true   # escalate only if alive
      wait "$pid" 2>/dev/null || true     # reap so no orphan lingers
    fi
    rm -f "$UVICORN_PID_FILE"
  fi
  exit "$rc"                              # restore the ORIGINAL status; never leak kill/rm status
}
trap cleanup EXIT
```

Rules that make this safe and non-regressing:
- `rc=$?` must be the **first** line of `cleanup`.
- Every signal/reap command keeps `2>/dev/null || true` so a reap failure can never flip a green
  smoke to red (or vice-versa).
- `exit "$rc"` inside the EXIT trap is safe (bash does not re-enter the EXIT trap) and makes the
  preservation explicit rather than shell-dependent.
- `kill -0` / `kill -TERM` / `kill -KILL` are POSIX; this runs on the Ubuntu runner. The existing
  Windows-safety guarding of the script is unaffected (this block only executes when a pidfile exists,
  and all signals are `|| true`).
- Do **not** change readiness semantics, the `router_count>0` require, or endpoint coverage.

This is secondary hygiene (it is **not** the root cause — the root cause is Item's-worth-of api-verify
scope), but it is worth doing correctly while the file is open.

---

## Item 3 — Promote the guard test to REQUIRED, and extend it to assert the step-timeout's presence

**Applies to:** the "New optional guard test" `scripts/ci/test_api_health_and_smoke_workflow.py`.

Change its status from optional to **required for this PR.** It is the ratchet that makes this exact
regression un-reintroducible — the same "fix the class, not the instance" move as the
manifest-discipline bleed-stop. Without it, #020-B gets re-fixed in two months the next time someone
"just adds a quick check" to the smoke workflow.

Extend the recommended assertions with one the original list omits — the step-timeout — because a
ratchet that guards `api-verify`'s *absence* but not the step-timeout's *presence* protects only the
less important half (Item 1 is what makes the fix work). Required assertions (text-level; a policy
guard, not a YAML framework):

1. The workflow contains **no** `make api-verify` (regex, tolerant of whitespace: `make\s+api-verify`).
2. The workflow still invokes `make api-smoke-posts` **or** `scripts/smoke/run_api_smoke_posts.sh`.
3. The workflow still uploads `smoke_posts.json`.
4. The workflow still includes a scheduled trigger (`schedule:` / `cron:`).
5. **The smoke step carries a step-level `timeout-minutes`.** (Assert a `timeout-minutes:` appears on
   the `Run v15.5 smoke (all presets)` step — parse the step block, or at minimum assert
   `timeout-minutes:` appears somewhere other than the job header. Prefer step-scoped if the parser
   allows.)

Keep it a text/lightweight-parse test with no new deps. Run it in the same job the readiness tests run
in so it is a real CI witness, not just a local convenience.

---

## Item 4 — Stop-and-ask: is `api-verify` merely slow, or hanging?

**Adds to:** Stop-and-Ask Conditions.

Removing `api-verify` from this workflow is correct **regardless** of why it was slow — the nightly
witness should not run the full suite either way. That is exactly why this needs a guard: the removal
will make #020-B green **whether or not** `api-verify` has a real hang festering. If `api-verify` is
*hanging* (not merely large), that latent problem still lives wherever else it runs — Core CI's
`api-test` path — and a green #020-B will have quietly laundered the signal into invisibility.

So, while implementing, glance at whether `api-verify` (or its `api-test` component) completes green
elsewhere within a sane wall-time:

    gh run list --workflow "Core CI (Consolidated)" --branch main --limit 5
    gh run view <recent-green-core-ci-id> --json jobs --jq '.jobs[] | {name, conclusion, startedAt, completedAt}'

**Stop and flag separately** if `api-verify`/`api-test` appears to *hang* (runs to a timeout, or shows
a wall-time wildly beyond its historical norm) rather than merely running long. Do not fix it inside
#020-B and do not let the green witness bury it — open a distinct thread. #020-B's job here is to
*notice*, not to fix.

---

## Net

Four items: **(1)** the smoke step-timeout is the deliverable — measure a healthy smoke once and set
`timeout-minutes` to ~2× observed, never a guessed 8; **(2)** make the *existing* trap's exit-code
preservation explicit (`rc=$?` … `exit "$rc"`) when you add TERM→wait→escalate→reap; **(3)** promote
the guard test to required and extend it to assert the step-timeout's presence, not just `api-verify`'s
absence; **(4)** stop-and-ask if `api-verify` looks like it *hangs* rather than merely runs long, so a
green #020-B can't launder a latent Core-CI hang into invisibility. Also: because every downstream step
is `if: always()`, the witness-presence assertion ("fail clearly if `smoke_posts.json` is missing after
smoke") must run in an always()-context and hard-fail on the missing artifact — otherwise the
`always()` badge/Pages steps mask the missing witness with a green-looking deploy. These turn "removes
the detour" into "removes the detour and makes the removal permanent, with honest reds when smoke
actually breaks."
