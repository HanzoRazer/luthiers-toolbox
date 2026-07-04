# DEV HANDOFF — PR #177 (CI-RED-020-B) Merge Instability

**Date:** 2026-07-03
**Author:** CI-RED-020-B session (review-hardening + ledger pass)
**Subject:** Why PR #177 reads `UNSTABLE`, why that is not a defect, and how to merge safely
**Related:** PR #177, PR #180 (SPRINTS ledger), CI-RED-020, CI-RED-021, `docs/handoffs/CI_RED_020B_dev_order.md` (+ `_addendum.md`)

> **STATUS UPDATE (2026-07-03, same day):** the `UNSTABLE` window described below was
> **transient**. The 3 pending Core CI jobs (`API Tests` ×2, `api-verify`) subsequently
> concluded **green**; `mergeStateStatus` moved `UNSTABLE → CLEAN` and #177 was merged. This
> handoff is retained as the durable explanation of *why* PRs here sit at `UNSTABLE` while
> Core CI runs — a **recurring interpretation hazard** that persists until CI-RED-021 is
> resolved, independent of #177's outcome.

---

## TL;DR

PR #177 (`fix/ci-red-020b-api-health-smoke-nightly-witness`, head `9414af45`) shows
GitHub **`mergeStateStatus: UNSTABLE`** while **`mergeable: MERGEABLE`**. That is **not**
a problem with the PR. `UNSTABLE` here means "mergeable, but not every check has
concluded successfully *yet*" — driven entirely by **3 long-running, non-required Core CI
jobs still in progress** (`API Tests` ×2, `api-verify`; plus `trending` skipped). Every
check that actually exercises this PR's diff is **green**.

Because this repo has **no branch protection on `main`** (CI-RED-021), `UNSTABLE` is the
*default steady state* of any PR here whenever a slow job is still running — it carries **no
merge-blocking meaning**. Interpret status **per-check**, not as a gestalt colour.

---

## What `UNSTABLE` actually is

GitHub's `mergeStateStatus` values:

| State | Meaning |
|-------|---------|
| `CLEAN` | Mergeable; all checks concluded successfully; required reviews satisfied |
| `UNSTABLE` | **Mergeable**, but ≥1 **non-required** check is failing or still pending |
| `BLOCKED` | A **required** status check or review is missing/failing |
| `DIRTY` | Merge conflicts |
| `BEHIND` | Base moved; branch needs update (only enforced if "require up to date" is on) |

The distinction that matters: `UNSTABLE` vs `BLOCKED` turns on whether a check is
**required**. On this repo **nothing is required** — so a PR can never reach `BLOCKED`
for a missing check, and it can never reach `CLEAN` while any advisory job is pending or
red. It settles at `UNSTABLE` by construction.

### Root cause: CI-RED-021 (no branch protection)

Verified 2026-06-16 and still true: classic branch protection returns `404`, active rules
on the `main` ref are `[]`, and the single ruleset (May 2 2026) is `enforcement: disabled`.
Therefore:

- **Zero required status checks** — Core CI / API Tests / api-verify / fence / contract
  checks all **report** but none **block**.
- **Zero required reviews** — `.github/CODEOWNERS` (`@toolbox-governance` over
  `services/api/app/ci/**` and fence baselines) is **inert** with no protection to enforce it.

**Consequence for merging:** `UNSTABLE` ≠ unsafe. Merge is not gated by these checks.
Waiting for green is a **custody courtesy**, not an enforcement. The fix for the *systemic*
issue is USER-only (repo Settings → Branches/Rulesets: enable required status checks +
code-owner review); a terminal cannot do it. See CI-RED-021.

---

## The 3 instability contributors on #177 (and why they're independent of this PR)

| Check | State | Relevance to this PR's diff |
|-------|-------|------------------------------|
| `API Tests` (×2 matrix) | pending (~24 min) | **None** — exercises the API *application* code |
| `api-verify` | pending (~24 min) | **None** — full verify suite over app code |
| `trending` | skipping | Conditional job, not applicable to this event |

**PR #177's diff touches only:**

- `.github/workflows/api_health_and_smoke.yml` (nightly witness workflow)
- `scripts/ci/test_api_health_and_smoke_workflow.py` (text-level workflow guard)
- `scripts/smoke/run_api_smoke_posts.sh` (smoke harness cleanup trap)
- `.cbsp21/patch_input.json` (CBSP21 manifest)
- `docs/handoffs/CI_RED_020B_*.md` (docs)

None of these are imported by the app or by the API test suite. So `API Tests` /
`api-verify` outcomes here **reflect `main`'s state, not this change**. Post-**#176**
(2026-07-02, `53bbf1a2`) the standing-failures triage closed → `main` is **full CI green**,
so those jobs are **expected to pass** on this PR too.

**Everything that does test this diff is already green** (31 checks): `guard`,
`cbsp21-patch-input`, `CBSP21 Patch Manifest Gate`, `debt-gates`, `Fence Checks (Blocking)`,
`workflow_api_base_gate`, `workflow_api_path_gate`, `Containers (Build + Smoke)`,
`geometry-parity`, `Unified Governance Gate`, `api-smoke`, etc.

---

## Important: the fixed workflow does NOT run as a PR check

The workflow this PR repairs — **API Health + Smoke** — triggers only on `schedule` and
`workflow_dispatch`, **not** on `pull_request`. So it is **not** among #177's checks and
cannot contribute to (or clear) the `UNSTABLE` state. Its proof is **out-of-band**:

- **Branch witnesses (already captured):** `workflow_dispatch` runs `28648970970` and
  `28649149183` — `health-smoke` **success**, smoke green ~10s, witness gate passed,
  `pages-deploy` skipped off-`main`, terminal (**not** cancelled).
- **Final proof (post-merge):** the next **scheduled** `main` run must be terminal-green.

---

## How to merge safely (decision guidance)

1. **Preferred:** wait for `API Tests` + `api-verify` to conclude → confirm green →
   **squash-merge** (repo convention) → delete branch.
2. **If they come back red:** confirm the failure is **pre-existing on `main`** (compare
   against a recent `main` Core CI run) and unrelated to this CI-only diff **before**
   merging. A new regression from this PR is not plausible given the diff surface — but
   *verify, don't assume* (gates are claims to check).
3. **Immediate merge is technically safe** for the PR's own correctness (nothing is
   enforced, and the diff can't affect those jobs). The only reason to wait is to avoid
   landing while main-wide signal is still unknown.

---

## Closure bar (do NOT mark 020-B closed at merge)

Per `SPRINTS.md` CI-RED-020 row (reconciled in **PR #180**):

> **020-B closes only when #177 is merged AND the next scheduled `main` run of
> API Health + Smoke is terminal-green** — *not* cancelled-after-smoke. A cancel that
> occurs *after* the smoke step already succeeded is a **Pages/environment follow-up**,
> classified separately, **not** a 020-B relabel.

Until that scheduled run is observed green, 020-B stays **OPEN** in the ledger.

---

## The systemic takeaway (why this recurs, for future sessions)

**Every PR in this repo will read `UNSTABLE`** while slow Core CI runs or any advisory job
is red, because there are **no required checks** to produce a `CLEAN`/`BLOCKED` signal. So:

- Do **not** read `UNSTABLE` as "the PR is broken." Open the check list and read it
  **per-check**: is a check that *actually tests this diff* red, or is it just a slow /
  pre-existing-red advisory job?
- The gestalt merge-state is only as meaningful as the enforcement behind it, and here
  there is none. This is a standing **interpretation hazard**.
- The durable fix is **CI-RED-021** (enable branch protection: required status checks +
  code-owner review). Until then, "green enough to merge" is a **human judgement** made by
  reading the checks that matter, not a state GitHub will compute for you.

---

## Cross-references

- **PR #177** — the fix. Review hardening: `6a3ba413` (witness gate parses
  `smoke_posts.json` + requires `ok`; `.nojekyll` guarantees a non-empty badges artifact so
  the `pages-deploy` handoff can't hard-fail; version-agnostic guard anchor) and `9414af45`
  (CBSP21 manifest reconciled to the shipped 3-min timeout).
- **PR #180** — `SPRINTS.md` ledger reconcile (020-A `#164` logged; 020-B recorded OPEN).
- **CI-RED-021** — no branch protection; the reason `UNSTABLE` is the norm. **USER action.**
- **CI-RED-020** — parent lane (api-smoke reachable-check → readiness harness → nightly
  witness restore).
- `docs/handoffs/CI_RED_020B_dev_order.md` + `_addendum.md` — the 020-B dev order.
