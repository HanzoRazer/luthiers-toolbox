# CI-RED-021-B — Required-Check Policy Follow-Up (READ-ONLY NOTES)

**Date:** 2026-07-05
**Status:** Notes only. NOT a work order. Do not implement, do not change the ruleset,
do not open a PR from this document. Records a future policy decision for the repo owner.

---

## Context (already done — do not redo)

CI-RED-004 is **CLOSED** by enforcement. Ruleset `15875552` ("May 2 2026") is **active**
on `main` with:

- `enforcement: active`, `bypass_actors: []`
- block force-push (`non_fast_forward`) + block `deletion`
- require PR before merge: **approvals = 0, code-owner review = false** (solo-safe, no self-lock)
- required status checks: **`Fence Checks (Blocking)` only**
- require branches up to date (strict): **false**

CODEOWNERS resolves to `@HanzoRazer` (#196) and covers fence plumbing (#197). The
fence-only scope was **intentional** for that pass.

CI-RED-021 remains **OPEN/partial** by design: review-required is deferred (single-collaborator
topology), and the broader required-check policy is not asserted.

---

## The open policy question (for a future owner decision)

Whether to widen the required-check set beyond the fence. Verified facts to inform it:

### Safe to require (run on every PR to main, no path filter, no extra author effort)

- `API Tests` (`api_tests.yml`: `on: [push, pull_request]`)
- `debt-gates` (`technical_debt.yml`: `pull_request: branches:[main]`)
- `server-env-check` (`server-env-check.yml`: `pull_request: branches:[main]`)

Requiring these would make red on them **block** merges (today they are advisory only).

### Require branches up to date (strict) — recommended if the set widens

`strict_required_status_checks_policy: true`. This is the toggle that would have
auto-caught the #193 stale-base CBSP21 coverage false-positive (branch-behind-main).
Low tax (merge main before merging), high value.

### Require with a caveat — imposes a per-PR authoring tax

- `CBSP21 Patch Manifest Gate` + `cbsp21-patch-input` — both run on every PR, but
  requiring `CBSP21 Patch Manifest Gate` means **every future PR must ship a
  `.cbsp21/patches/<id>.json` manifest** or it is hard-blocked (a one-line typo fix
  included). Defensible as coverage discipline; the fence-only pass deliberately
  avoided this tax. Conscious policy choice, not an obvious yes.

### Cannot require as-is (path-filtered → would permanently-pend on off-path PRs)

`api-verify`, `routing-truth`, `router-count-check`, `artifact-linkage`, `contract-gate`.
Each only runs when specific code paths change, so a docs-only PR would leave a required
check eternally "Expected — waiting" → main locked. To require any of these, first give
it the same treatment as the fence: make it run on every PR (remove/broaden the path
filter, confirm it passes on a docs-only PR), THEN require it. Separate scoped change each.

### Review-required (the actual CI-RED-021 remainder)

Requiring CODEOWNER review / approvals ≥ 1 cannot be satisfied on a solo repo (no second
reviewer; self-approval forbidden). Closing this sub-goal needs an account-model change
(org + team, or a second reviewer/bot). Independent of the required-check question above.

---

## If someone picks this up

1. This is an owner settings decision, not agent code work.
2. Widening the required set is a ruleset edit (UI or reviewed `gh api` payload) — the
   owner applies it.
3. Do not require a path-filtered check without first making it run on every PR.
4. Re-verify live ruleset state immediately before any change (this lane has had
   concurrent actors).
