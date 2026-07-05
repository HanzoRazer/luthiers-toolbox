# CI-RED-004 — Docs-Only Fence Witness

**Date:** 2026-07-05
**Lane:** CI-RED-004 / CI-RED-021 branch-protection enforcement prep
**Prereq merged:** PR #194 (`fa18d72a`) — all-PR fence trigger + hardening

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

---

## Witness record

Fill in after this PR's CI settles:

- Witness PR: `#____`
- `Architecture Scan (Non-Blocking)` started on the docs-only diff: `[ ] yes`
- `architecture-scan` job: `____` — run URL: `____`
- `Fence Checks (Blocking)` job: `____` — run URL: `____`

---

## Only after this is green

1. Add `Fence Checks (Blocking)` to the required status checks on `main`
   (repo branch-protection settings — human/admin action; the check name must
   match **exactly** `Fence Checks (Blocking)`).
2. Then, and only then, CI-RED-004 / CI-RED-021 close in `SPRINTS.md`.

Do **not** require the check until this witness is green.
