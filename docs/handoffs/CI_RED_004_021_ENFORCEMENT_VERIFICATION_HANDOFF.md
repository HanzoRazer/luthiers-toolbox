# CI-RED-004 / CI-RED-021 Enforcement Verification Handoff

Date: 2026-07-05
Status: Dev-ready handoff
Base observed locally: `origin/main` at `1b09cd58`
Primary objective: close CI-RED-004 and move CI-RED-021 from "settings missing" to "enforcement verified"

## One-line target

Turn the already-green fence from an advisory signal into a real merge guard, then verify that `main` is protected by required status checks, pull requests, CODEOWNER review, and no routine direct-push path.

## Current ground truth

Merged prerequisites already on `origin/main`:

- PR #194, `fa18d72a`: `.github/workflows/architecture_scan.yml` now runs on every PR and every push to `main`; no path filter remains.
- PR #195, `8dac15c2`: docs-only witness proved `Fence Checks (Blocking)` reports green on a docs-only PR instead of staying `Expected - waiting`.
- PR #196, `1b09cd58`: `.github/CODEOWNERS` now points to the real owner `@HanzoRazer`, replacing unresolved `@toolbox-governance`.

Current `origin/main` CODEOWNERS coverage:

```text
services/api/app/ci/fence_baseline.json          @HanzoRazer
services/api/app/ci/fence_patterns_baseline.json @HanzoRazer
services/api/app/ci/**                           @HanzoRazer
scripts/architecture/**                          @HanzoRazer
```

Current exact required-check candidate:

```text
Fence Checks (Blocking)
```

Do not rename this check in the branch-protection settings. GitHub required checks match the reported status-check name.

## Scope

In scope:

- Verify CODEOWNERS resolves cleanly after #196.
- Decide and apply the `main` branch protection/ruleset settings.
- Verify the exact check `Fence Checks (Blocking)` is required and reports on all PRs.
- Verify CODEOWNER review is actually requested/enforced for governance-owned paths.
- Update `SPRINTS.md` and, if desired, add a closure witness handoff after the settings are proven.

Out of scope:

- Changing fence logic or baselines.
- Renaming jobs or workflows.
- Closing unrelated CI-RED items.
- Treating PR #195 as permanent proof after future workflow/job-name changes.
- Calling CI-RED-021 closed if CODEOWNER review cannot be enforced without routine bypass.

## Decisions Needed

### Decision 1: Protection mechanism

Use either a branch ruleset or classic branch protection for `main`, but the result must be observable and active.

Required outcome:

- `main` requires pull requests before merge.
- `main` requires status checks before merge.
- `Fence Checks (Blocking)` is in the required status-check list.
- `main` requires review from CODEOWNERS.
- Routine direct pushes to `main` are not allowed.

Preferred path: GitHub ruleset if the repository already standardizes on rulesets; otherwise classic branch protection is acceptable. Do not maintain two conflicting protection systems.

### Decision 2: Required checks list

Minimum needed to close CI-RED-004:

```text
Fence Checks (Blocking)
```

For CI-RED-021, the owner must decide whether this pass requires only the fence as the first enforced guard, or a broader stable required-check set. If additional checks are selected, list the exact check names in the closure record. Do not use fuzzy names like "Core CI" unless that is the exact status name GitHub reports.

### Decision 3: CODEOWNER topology

Current CODEOWNERS uses `@HanzoRazer`. That fixes the unresolved-owner bug, but there is a solo-repo trap:

- If `@HanzoRazer` opens the PR, GitHub may request `@HanzoRazer` as code owner.
- A PR author normally cannot approve their own PR.
- If no second reviewer or org/team exists, strict CODEOWNER review may require admin bypass to merge.

Before turning on strict CODEOWNER review, choose one:

1. Add at least one second real collaborator/code owner who can approve governance-path PRs.
2. Move to an org/team-backed owner later and keep CI-RED-021 open until then.
3. Accept an explicit, documented solo-owner exception. This may verify some protection, but it should not be called "no routine bypass" unless the bypass path is truly closed.

### Decision 4: CODEOWNERS coverage expansion

Current coverage protects the fence data/scripts, but not all enforcement plumbing. Consider a tiny prep PR before or alongside settings verification to add:

```text
.github/CODEOWNERS                         @HanzoRazer
.github/workflows/architecture_scan.yml    @HanzoRazer
```

Rationale: if CODEOWNER review is meant to protect the fence, the workflow that runs the fence and the CODEOWNERS file itself should be under owner review too.

Do not silently expand to every workflow in this pass unless the owner approves that broader governance surface.

## File-by-file Patch Plan

### Optional prep PR: CODEOWNERS coverage expansion

Only do this if Decision 4 is accepted.

File: `.github/CODEOWNERS`

- Add `.github/CODEOWNERS @HanzoRazer`.
- Add `.github/workflows/architecture_scan.yml @HanzoRazer`.
- Keep existing four governance rules intact.
- Do not change product code or fence logic.

File: `.cbsp21/patches/codeowners-enforcement-surface.json`

- Add a per-PR manifest for the CODEOWNERS coverage change.
- Scope only `.github/CODEOWNERS` and the manifest.
- State that this is review-routing metadata, not runtime behavior.

Tests:

- Validate JSON manifest.
- Run CBSP21 patch input gate.
- Run CBSP21 coverage gate.
- Verify `gh api repos/HanzoRazer/luthiers-toolbox/codeowners/errors` has no errors.

### Required settings witness PR

File: `docs/handoffs/CI_RED_004_021_ENFORCEMENT_WITNESS.md`

- Record the active settings snapshot after branch protection/ruleset is enabled.
- Record the exact required check names.
- Record docs-only PR run ID proving `Fence Checks (Blocking)` reports and blocks if red.
- Record governance-owned PR evidence proving CODEOWNER review is requested/enforced.
- State whether CI-RED-004 is closed and whether CI-RED-021 is fully closed or only moved to enforcement-verified/partially verified.

File: `.cbsp21/patches/ci-red-004-021-enforcement-witness.json`

- Manifest for the docs-only witness and ledger update.
- Scope `docs/handoffs/`, `SPRINTS.md`, and `.cbsp21/patches/` only.

File: `SPRINTS.md`

- CI-RED-004: move to CLOSED only after `Fence Checks (Blocking)` is required and verified.
- CI-RED-021: update from "settings missing" to the exact verified state.
- If CODEOWNER review remains constrained by solo-owner mechanics, do not close CI-RED-021. Mark the remaining blocker explicitly.

Suggested CI-RED-004 closure wording:

```text
CI-RED-004 CLOSED by enforcement witness: Fence Checks (Blocking) is required on main and reports on docs-only PRs; branch protection/ruleset now blocks merge when the fence is absent or red.
```

Suggested CI-RED-021 partial wording if solo-owner review remains unresolved:

```text
CI-RED-021 PARTIALLY VERIFIED: main now requires PRs and Fence Checks (Blocking); CODEOWNERS resolves to @HanzoRazer, but no-routine-bypass CODEOWNER review remains open pending reviewer topology.
```

Suggested CI-RED-021 closure wording only if all bars are proven:

```text
CI-RED-021 CLOSED by enforcement witness: main has active protection/ruleset requiring PRs, required status checks, CODEOWNER review on governance-owned paths, and no routine direct-push/bypass path.
```

## Utilities

Use GitHub UI for the actual settings change. Terminal/API checks are witnesses only unless the owner explicitly chooses API-based configuration.

Useful read-only checks:

```powershell
gh api repos/HanzoRazer/luthiers-toolbox/codeowners/errors
gh api repos/HanzoRazer/luthiers-toolbox/branches/main/protection
gh api repos/HanzoRazer/luthiers-toolbox/rulesets
gh pr checks <PR_NUMBER>
gh run view <RUN_ID> --json status,conclusion,jobs
```

Useful local checks from `services/api`:

```powershell
python -m app.ci.check_all_fences
```

Useful CBSP21 checks:

```powershell
python scripts/ci/check_cbsp21_patch_input.py --base origin/main --head HEAD
python scripts/ci/check_cbsp21_gate.py --changed-files <changed-files-list>
```

If `gh` is not authenticated, do not infer enforcement state from absence of data. Report "unverified" and have the repo owner inspect GitHub settings directly.

## Test Cases

### Test 1: CODEOWNERS resolves

Action:

- Run GitHub CODEOWNERS errors API.

Pass:

- No `Unknown owner` errors for the governance rules.

Fail:

- Any unresolved owner remains.

### Test 2: Required fence reports on docs-only PR

Action:

- Open a docs-only PR touching only `docs/handoffs/...` and its CBSP21 manifest.

Pass:

- `Architecture Scan (Non-Blocking)` starts.
- `Fence Checks (Blocking)` reports success.
- The PR does not show `Expected - waiting` for the fence.

Fail:

- The workflow is skipped.
- The check is pending forever.
- The check reports under a different name than the required setting.

### Test 3: Required fence blocks red

Action:

- Do not intentionally damage main.
- Use either a throwaway PR that makes a reversible, scoped fence-baseline mismatch, or use GitHub's required-check UI state to confirm the check is required before merge.

Pass:

- A red or missing `Fence Checks (Blocking)` prevents merge.

Fail:

- A PR can merge while the required fence is red/missing.

### Test 4: CODEOWNER review is requested

Action:

- Open a PR touching a CODEOWNERS-covered governance path.
- If Decision 4 landed, `.github/workflows/architecture_scan.yml` is the cleanest test path.
- Otherwise use `scripts/architecture/...` with a harmless comment/docstring-only change.

Pass:

- GitHub requests the configured code owner.
- Merge is blocked until valid CODEOWNER review occurs.

Fail:

- No CODEOWNER review is requested.
- PR can merge without owner review.
- The only possible merge path is admin bypass that the project does not intend to treat as routine.

### Test 5: Direct push is blocked

Action:

- Do not test by making a destructive push.
- Inspect the ruleset/protection configuration and, if needed, use a harmless branch attempt in a controlled owner-approved window.

Pass:

- Normal direct push to `main` is disallowed.

Fail:

- `main` remains directly writable in normal operation.

## Rollout Order

1. Preflight:
   - Confirm `origin/main` contains #194, #195, and #196.
   - Confirm current workflow job name is exactly `Fence Checks (Blocking)`.
   - Confirm CODEOWNERS has no unresolved owner errors.

2. Optional but recommended:
   - Expand CODEOWNERS coverage to include `.github/CODEOWNERS` and `.github/workflows/architecture_scan.yml`.
   - Merge that tiny prep PR after CBSP21 and CODEOWNERS checks pass.

3. Human settings action:
   - Enable `main` protection/ruleset.
   - Require pull requests before merge.
   - Require status checks before merge.
   - Add exact check `Fence Checks (Blocking)`.
   - Require CODEOWNER review.
   - Close routine direct-push/bypass paths, or explicitly document any exception.

4. Docs-only witness PR:
   - Open a docs-only PR.
   - Verify `Fence Checks (Blocking)` reports green and is required.
   - Record run ID and check name.

5. Governance-owned path witness PR:
   - Touch a CODEOWNERS-covered governance path.
   - Verify owner review is requested and merge is blocked until review.
   - Record PR number and reviewer behavior.

6. Ledger update:
   - Update `SPRINTS.md`.
   - Close CI-RED-004 if the required fence is proven.
   - Move CI-RED-021 to the strongest truthful state:
     - CLOSED only if PR requirement, required checks, CODEOWNER review, and no routine bypass are all proven.
     - PARTIALLY VERIFIED if solo-owner review or bypass remains unresolved.

7. Post-merge monitoring:
   - Watch the next push-to-main run of `Architecture Scan (Non-Blocking)`.
   - If it fails because of settings or naming drift, reopen the enforcement item immediately.

## Stop-and-Ask Conditions

Stop and ask the repo owner before proceeding if:

- GitHub reports CODEOWNERS errors after #196.
- `Fence Checks (Blocking)` does not appear in the required-check selector.
- The required-check selector shows multiple similar fence names.
- Enabling CODEOWNER review would make solo-owner PRs unmergeable except by admin bypass.
- A broader required-check set is proposed beyond `Fence Checks (Blocking)`.
- Any settings change would disable emergency access without an explicit owner decision.
- The witness PR can merge despite the required fence being missing/red.

## Final Acceptance Bar

CI-RED-004 may close when:

- `Fence Checks (Blocking)` is required on `main`.
- A docs-only PR proves the check reports green and does not hang as `Expected - waiting`.
- A red/missing fence would block merge.

CI-RED-021 may move to enforcement verified when:

- `main` has active protection/ruleset.
- Pull requests are required.
- Required status checks are active.
- CODEOWNER review is active and actually requested on covered governance paths.
- Normal direct pushes/bypasses are closed or explicitly documented as an accepted exception.

CI-RED-021 should close only when every one of those statements is proven and the reviewer topology does not depend on routine self-approval or admin bypass.
