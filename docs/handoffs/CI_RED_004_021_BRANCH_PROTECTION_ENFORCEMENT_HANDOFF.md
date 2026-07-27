# CI-RED-004 / CI-RED-021 Dev Handoff - Branch Protection Enforcement

**Date:** 2026-07-04  
**Lane:** CI / governance enforcement  
**Targets:** `CI-RED-004` and `CI-RED-021`  
**Status:** Dev-ready operational handoff. Requires repo-owner approval and GitHub settings action.  
**Observed base:** local worktree `2c357232` with `SPRINTS.md` entries current through the CI-RED-003/019/020 reconciliation work.

---

## 1. Goal

Turn the repo's repaired checks from advisory instruments into enforced guards on
`main`.

`CI-RED-004` is the specific repaired fence case:

- the fence code is fixed;
- `Fence Checks (Blocking)` is green;
- but GitHub does not require that check before merge.

`CI-RED-021` is the systemic version:

- `main` has no effective branch protection/ruleset enforcement;
- CI checks and CODEOWNERS review can report truth but cannot block a merge;
- a red gate can still be bypassed by an ordinary merge.

This handoff closes the decision gap by making explicit what the repo owner is
approving, which settings must change, how to verify them, and which repo docs
should be updated after the settings are live.

---

## 2. What The Human Is Approving

The approval is not approval of a code diff. It is approval of a repo operating
rule:

> `main` may not accept changes unless the agreed checks and reviews pass.

Precise approval statement:

> I approve enabling active branch protection or ruleset enforcement on `main`,
> requiring agreed CI checks and CODEOWNERS review before merge, with no routine
> bypass and emergency bypass only by documented repo-owner action.

That approval covers these concrete decisions:

1. `main` is protected.
2. Pull requests are required before merge into `main`.
3. Selected status checks are required.
4. CODEOWNERS review is required for owned paths.
5. Stale approvals are dismissed when new commits are pushed.
6. Direct pushes to `main` are disallowed except documented emergency/admin action.
7. Any bypass is exceptional, owner-controlled, and documented in the PR or
   `SPRINTS.md`.

---

## 3. Scope

### In Scope

1. Configure GitHub branch protection or repository ruleset for `main`.
2. Require the fence check that closes `CI-RED-004`:
   - `Fence Checks (Blocking)`
3. Require the minimum CI checks that prevent known CI-RED regressions from
   being merged as advisory-only signals.
4. Require CODEOWNERS review so `.github/CODEOWNERS` becomes active.
5. Add or update docs that record:
   - protected branch policy;
   - required checks;
   - bypass policy;
   - closure witness commands.
6. Update `SPRINTS.md` after enforcement is verified.

### Out Of Scope

- Do not change application code.
- Do not weaken, rename, or delete CI jobs to make enforcement easier.
- Do not close any unrelated CI-RED item.
- Do not treat CI-RED-004 as closed merely because the fence is green.
- Do not change C2 authority, GOV-CONVERGE-007, endpoint consolidation, or
  warning-to-RED behavior.
- Do not merge with pending or red required checks during rollout unless the
  emergency bypass policy is explicitly invoked and documented.

---

## 4. Decisions For This Work

### Decision 1 - Use an active ruleset or branch protection

Either GitHub mechanism is acceptable:

- repository ruleset targeting `main`, or
- classic branch protection on `main`.

Prefer a repository ruleset if the repo is already moving that direction. The
closure bar is behavioral, not tied to a specific GitHub UI:

- active enforcement applies to `main`;
- required checks block merges;
- CODEOWNERS review is enforced.

### Decision 2 - Required checks start with the fence

Minimum required check for `CI-RED-004`:

```text
Fence Checks (Blocking)
```

This exact job name exists in:

```text
.github/workflows/architecture_scan.yml
```

### Decision 3 - Required checks should cover the live CI-RED guard surface

Recommended initial required checks:

```text
Fence Checks (Blocking)
API Tests
api-verify
CBSP21 Patch Manifest Gate
cbsp21-patch-input
routing-truth
router-count-check
debt-gates
artifact-linkage
contract-gate
server-env-check
```

If GitHub shows duplicate names from old runs or matrix jobs, select the current
job name as shown on a fresh green PR. Do not invent names. GitHub required
checks are string-matched.

### Decision 4 - CODEOWNERS review is required

Current CODEOWNERS already assigns governance ownership for:

```text
services/api/app/ci/**
services/api/app/ci/fence_baseline.json
services/api/app/ci/fence_patterns_baseline.json
scripts/architecture/**
```

The setting to enable is:

```text
Require review from Code Owners
```

### Decision 5 - Bypass must be rare and documented

Recommended policy:

- no routine bypass;
- emergency bypass only by repo owner/admin;
- document the bypass reason and follow-up in the PR or `SPRINTS.md`;
- if bypass is used for a red check, open a named follow-up before treating the
  merge as complete.

### Decision 6 - Closing 004 and 021 requires verification after settings change

Do not close by intent. Close only after read-only verification proves:

- `main` is protected or covered by an active ruleset;
- required checks include `Fence Checks (Blocking)`;
- CODEOWNERS review is required;
- direct merge/push bypass is not the normal path.

---

## 5. File-By-File Patch Plan

This is primarily a settings rollout. The repo patch is documentation and ledger
work after the setting is live.

### 5.1 `docs/handoffs/CI_RED_004_021_BRANCH_PROTECTION_ENFORCEMENT_HANDOFF.md`

Add this handoff.

Purpose:

- records the exact approval being requested;
- separates human settings action from code work;
- gives the implementer/verifier a closure checklist.

### 5.2 `SPRINTS.md`

Patch only after enforcement is actually enabled and verified.

Update:

- `CI-RED-004` from `OPEN` to `CLOSED`;
- `CI-RED-021` from `OPEN` to `CLOSED`;
- include date, settings witness, and required check list;
- explicitly state that this is a repo-settings closure, not a code PR closure.

Do not update `SPRINTS.md` before the settings are live.

Suggested closure language:

```text
Closed 2026-07-__: main is protected by an active GitHub branch protection
rule/ruleset. Required checks include Fence Checks (Blocking), API Tests,
api-verify, CBSP21 Patch Manifest Gate/cbsp21-patch-input, routing-truth,
router-count-check, debt-gates, artifact-linkage, contract-gate, and
server-env-check. CODEOWNERS review is required. Emergency bypass is
repo-owner-only and must be documented. This closes the enforcement gap:
the repaired fence and other gates now block merges rather than reporting
advisory truth only.
```

### 5.3 `.github/CODEOWNERS`

Default: no patch.

Patch only if the owner wants broader coverage. Candidate additions:

```text
.github/workflows/**                         @toolbox-governance
.github/CODEOWNERS                           @toolbox-governance
scripts/ci/**                                @toolbox-governance
```

Do not expand CODEOWNERS in this same rollout unless the owner explicitly wants
that policy change. Activating existing CODEOWNERS is enough to close 004/021.

### 5.4 `.github/workflows/*.yml`

Default: no patch.

Do not rename checks during this rollout. Required status checks depend on exact
job names; renaming a job during enforcement setup creates confusion.

Patch only if a selected check does not reliably run on pull requests to `main`.
If that appears, stop and scope a separate workflow fix.

### 5.5 Optional future settings-as-code artifact

Optional follow-up, not required for closure:

```text
docs/governance/MAIN_BRANCH_PROTECTION_POLICY.md
```

Use only if the team wants a durable policy page separate from `SPRINTS.md`.

---

## 6. GitHub Settings Rollout

Owner performs this in GitHub UI or equivalent admin API.

### Ruleset / Branch Protection Target

Target:

```text
main
```

Recommended toggles:

```text
Require a pull request before merging: ON
Require approvals: ON
Required approving reviews: 1
Dismiss stale pull request approvals when new commits are pushed: ON
Require review from Code Owners: ON
Require status checks to pass before merging: ON
Require branches to be up to date before merging: recommended ON
Restrict deletions: ON
Allow force pushes: OFF
Allow bypass: repo-owner/admin emergency only, documented
```

### Required Checks

Start with:

```text
Fence Checks (Blocking)
API Tests
api-verify
CBSP21 Patch Manifest Gate
cbsp21-patch-input
routing-truth
router-count-check
debt-gates
artifact-linkage
contract-gate
server-env-check
```

If GitHub cannot find one of these names, run or inspect a fresh PR and select
the exact check name from the current checks list.

---

## 7. Utilities And Verification Commands

These are read-only witnesses. They do not change settings.

### Check classic branch protection

```powershell
gh api repos/HanzoRazer/luthiers-toolbox/branches/main/protection
```

Expected after rollout:

- command succeeds;
- `required_status_checks` present;
- `required_pull_request_reviews.require_code_owner_reviews` is true.

If using rulesets instead of classic protection, this endpoint may not carry the
whole picture. Also run the ruleset check.

### Check active rulesets

```powershell
gh api repos/HanzoRazer/luthiers-toolbox/rulesets --jq '.[] | {name, enforcement, target}'
```

Expected:

- at least one ruleset targeting branch refs / `main`;
- `enforcement` is `active`, not `disabled`.

### Check rules applying to main

```powershell
gh api repos/HanzoRazer/luthiers-toolbox/rules/branches/main
```

Expected:

- rules list is non-empty;
- includes required status checks and pull request review rules.

### Verify CODEOWNERS file remains present

```powershell
Get-Content .github/CODEOWNERS
```

Expected:

- governance-owned CI/fence paths still map to `@toolbox-governance`.

### Verify check names from latest PR

```powershell
gh pr checks <PR_NUMBER> --watch=false
```

Expected:

- selected required checks appear with exact names;
- required checks are green before merge.

---

## 8. Test Cases / Witnesses

### Witness 1 - Enforcement exists

Use GitHub API or UI to prove:

- `main` has active protection/ruleset;
- required status checks are configured;
- code-owner review is required.

This is the closure witness for `CI-RED-021`.

### Witness 2 - Fence is required

Prove `Fence Checks (Blocking)` appears in the required status-check list.

This is the closure witness for `CI-RED-004`.

### Witness 3 - CODEOWNERS is active

Open or inspect a PR touching one governance-owned path, for example:

```text
services/api/app/ci/fence_baseline.json
```

Expected:

- GitHub requests `@toolbox-governance` review;
- merge is blocked until owner review is satisfied.

This can be a draft/test PR if the owner wants a live witness. Do not merge a
test-only change.

### Witness 4 - Red required check blocks merge

Optional but strongest proof.

Use a draft/test branch or existing red PR. Confirm GitHub marks the PR blocked
because a required check is failing or pending.

Do not intentionally break `main`. Do not merge the witness PR.

### Witness 5 - Normal green PR can still merge

After settings are active, merge a normal green PR through the required path.

Expected:

- no workflow surprise;
- no required check stuck permanently pending;
- merge path remains usable.

---

## 9. Rollout Order

1. Confirm owner approval using the sentence in section 2.
2. Inspect a fresh green PR and list exact check names.
3. Enable active branch protection/ruleset for `main`.
4. Add the initial required checks.
5. Enable PR review and CODEOWNERS review.
6. Enable stale approval dismissal.
7. Disable force pushes and routine bypass.
8. Run read-only verification commands.
9. If any selected required check is missing or permanently pending, remove only
   that broken selection temporarily and open a named follow-up to fix the
   workflow. Do not silently close 004/021 until the fence and core guard set
   are enforced.
10. Update `SPRINTS.md` with the verified settings and closure witness.
11. Commit/push the docs/ledger update as a small PR.
12. Merge only after the new protection settings allow the PR through the
    protected path.

---

## 10. Stop-And-Ask Conditions

Stop before changing settings if:

1. The owner does not approve blocking merges on red required checks.
2. The required-check list is unclear because check names are duplicated or stale.
3. Any required check is known to be permanently red on current `main`.
4. CODEOWNERS review would block all solo development with no practical reviewer.
5. GitHub plan/settings do not support the intended rule shape.
6. A bypass exception is requested without a documented reason and follow-up.

Stop before closing the ledger if:

1. `Fence Checks (Blocking)` is not required.
2. CODEOWNERS review is not required.
3. The ruleset exists but `enforcement` is still `disabled`.
4. Protection only applies to pushes but not pull-request merges.
5. Verification depends on screenshots only and no read-only API/UI witness was
   captured.

---

## 11. Done Definition

`CI-RED-004` is done when:

- `Fence Checks (Blocking)` is green and required on `main`.

`CI-RED-021` is done when:

- `main` has active branch protection or active ruleset enforcement;
- required checks block merge;
- CODEOWNERS review is required;
- direct push/force push/routine bypass are not normal paths;
- `SPRINTS.md` records the settings witness and closure.

This work is not done merely because the checks are green. It is done when the
checks are green and GitHub enforces them.

---

## 12. Follow-Ups After Closure

Optional later work:

1. Expand CODEOWNERS coverage to workflows, `scripts/ci/**`, and governance docs.
2. Add a scheduled read-only governance check that reports whether branch
   protection is still active.
3. Create `docs/governance/MAIN_BRANCH_PROTECTION_POLICY.md` if the team wants a
   durable policy page.
4. Review required-check list quarterly so renamed workflows do not leave stale
   required checks behind.

