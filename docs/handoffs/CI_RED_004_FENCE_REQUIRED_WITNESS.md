# CI-RED-004 — Docs-Only Fence Witness

**Date:** 2026-07-05
**Lane:** CI-RED-004 / CI-RED-021 branch-protection enforcement prep
**Prereq merged:** PR #194 (`fa18d72a`) — all-PR fence trigger + hardening
**Witness scope:** time-bound proof for this workflow/commit shape; not a
permanent branch-protection audit.

---

## Why this PR exists

Before `Fence Checks (Blocking)` can be added to the required status checks on
`main`, we must prove that a **docs-only** pull request — one that touches none
of the paths the workflow used to be filtered on — still triggers
`Architecture Scan (Non-Blocking)` and that `Fence Checks (Blocking)` reports a
green result.

If it did not, requiring the check would permanently brick every docs-only PR at:

```text
Expected — waiting for status to be reported
```

This PR is that witness. It changes only:

- `docs/handoffs/CI_RED_004_FENCE_REQUIRED_WITNESS.md` (this file)
- `.cbsp21/patches/fence-docs-witness-cired004.json` (its CBSP21 manifest)

Neither path was in the pre-#194 `paths:` filter
(`services/api`, `packages/client`, `contracts`, `docker`, `scripts`,
`.github/workflows`), so a green fence here proves the filter removal works.

This witness proves only that this docs/metadata-only PR shape triggered and
passed the exact check named `Fence Checks (Blocking)` on 2026-07-05. If
`.github/workflows/architecture_scan.yml` or the job name changes later,
re-run a docs-only witness before relying on this record for branch-protection
settings.

---

## Witness record

Observed 2026-07-05 on this PR:

- Witness PR: **#195**
- `Architecture Scan (Non-Blocking)` started on the docs-only diff: **yes**
  (run `28739849213`, 19s) — this workflow would have been **skipped** under the
  pre-#194 path filter.
- `architecture-scan` job: **success** —
  https://github.com/HanzoRazer/luthiers-toolbox/actions/runs/28739849213/job/85220557656
- `Fence Checks (Blocking)` job: **success** (14s) —
  https://github.com/HanzoRazer/luthiers-toolbox/actions/runs/28739849213/job/85220557669

Witness satisfied for PR #195: this docs-only PR triggered the workflow and the
blocking fence reported green. This removes the known "required check never
reports on docs-only PRs" blocker for requiring the exact check name
`Fence Checks (Blocking)`.

---

## Only after this is green

1. Add `Fence Checks (Blocking)` to the required status checks on `main`
   (repo branch-protection settings — human/admin action; the check name must
   match **exactly** `Fence Checks (Blocking)`).
2. Verify branch protection/ruleset state after the setting is live. Do not use
   this document as the source of truth for current enforcement state.
3. `CI-RED-004` may close once `Fence Checks (Blocking)` is green and required.
4. `CI-RED-021` closes only when the wider enforcement bar is also verified:
   active `main` protection/ruleset, required checks, CODEOWNERS review, and no
   routine bypass/direct-push path.

Do **not** require the check until this witness is green.

## What this does not prove

- It does not enable or verify branch protection.
- It does not prove future workflow revisions still report on docs-only PRs.
- It does not prove every low-touch PR shape behaves identically.
- It does not close CI-RED-004 or CI-RED-021 by itself.
