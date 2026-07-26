# PR #194 Dev Order - Harden All-PR Fence Trigger Rollout

**Date:** 2026-07-05  
**Target PR:** #194  
**Branch:** `ci/fence-runs-every-pr-cired004`  
**Lane:** CI-RED-004 / CI-RED-021 enforcement prep  
**Status:** Dev-ready implementation order  

---

## 1. Purpose

PR #194 removes the `paths:` filters from `.github/workflows/architecture_scan.yml`
so `Fence Checks (Blocking)` runs on every pull request. That is required before
the fence can become a required status check on `main`.

The core PR direction is correct. A required GitHub check must report on every PR;
otherwise docs-only PRs get stuck forever at:

```text
Expected - waiting for status to be reported
```

However, widening the workflow from path-filtered to every PR increases CI
surface area. This dev order adds lightweight hardening so the wider trigger is
less noisy, less privileged, and less likely to block all PRs due to a hung run.

---

## 2. Scope

### In Scope

1. Add explicit read-only workflow permissions.
2. Add PR-only concurrency cancellation for stale in-progress runs.
3. Add finite job timeouts to both workflow jobs.
4. Update the CBSP21 manifest narrative and verification list to describe the
   hardening.
5. Re-run local and CI witnesses.

### Out Of Scope

- Do not restore path filters.
- Do not split the workflow.
- Do not change fence logic.
- Do not change fence baselines.
- Do not make `Fence Checks (Blocking)` required yet.
- Do not close `CI-RED-004` or `CI-RED-021` yet.
- Do not merge without the usual PR checks.

---

## 3. Decisions

### Decision 1 - Keep all-PR trigger

Keep:

```yaml
pull_request:
```

with no `paths:` filter.

Reason: this is the load-bearing change. A future required check must report on
docs-only PRs.

### Decision 2 - Keep push-to-main all-paths

Keep:

```yaml
push:
  branches: [main]
```

with no `paths:` filter.

Reason: every merge commit to `main` should record the fence verdict once the
fence becomes a guard.

### Decision 3 - Use read-only token permissions

Add:

```yaml
permissions:
  contents: read
```

Reason: the workflow only checks out code, scans, and uploads an artifact. It
does not need write access.

### Decision 4 - Cancel stale PR runs, not push-to-main verdicts

Add:

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.event.pull_request.number || github.sha }}
  cancel-in-progress: ${{ github.event_name == 'pull_request' }}
```

Reason:

- on PRs, new commits should cancel stale runs for the same PR;
- on `push` to `main`, each merge commit should keep its own verdict and should
  not cancel another push's evidence.

### Decision 5 - Add finite job timeouts

Add:

```yaml
timeout-minutes: 10
```

to both:

- `architecture-scan`
- `fence-checks`

Reason: if `Fence Checks (Blocking)` becomes required later, a hung job becomes
a global merge blocker. Ten minutes is conservative relative to the expected
short runtime and can be adjusted later with evidence.

---

## 4. File-By-File Patch Plan

### 4.1 `.github/workflows/architecture_scan.yml`

Patch after the `on:` block:

```yaml
permissions:
  contents: read

concurrency:
  group: ${{ github.workflow }}-${{ github.event.pull_request.number || github.sha }}
  cancel-in-progress: ${{ github.event_name == 'pull_request' }}
```

Patch both jobs:

```yaml
jobs:
  architecture-scan:
    runs-on: ubuntu-latest
    continue-on-error: true
    timeout-minutes: 10
```

```yaml
  fence-checks:
    name: Fence Checks (Blocking)
    runs-on: ubuntu-latest
    continue-on-error: false
    timeout-minutes: 10
```

Do not alter job names. In particular, keep exactly:

```text
Fence Checks (Blocking)
```

The future branch-protection rule depends on the exact check name.

### 4.2 `.cbsp21/patches/fence-runs-every-pr-cired004.json`

Update:

- `intent`
- `behavior_change`
- `diff_articulation.what_changed`
- `verification.commands_run`
- file-level `behavior_change`

Required narrative:

- workflow still runs on every PR and every push to `main`;
- no fence/check logic changed;
- read-only permissions added;
- 10-minute job timeouts added;
- stale in-progress PR runs are canceled;
- push-to-main verdicts are not canceled;
- docs-only PR witness remains pending before the check is required.

---

## 5. Implementation Patch

Apply this conceptual diff.

```diff
diff --git a/.github/workflows/architecture_scan.yml b/.github/workflows/architecture_scan.yml
@@
   pull_request:
   workflow_dispatch:
 
+permissions:
+  contents: read
+
+concurrency:
+  group: ${{ github.workflow }}-${{ github.event.pull_request.number || github.sha }}
+  cancel-in-progress: ${{ github.event_name == 'pull_request' }}
+
 jobs:
   architecture-scan:
     runs-on: ubuntu-latest
     continue-on-error: true
+    timeout-minutes: 10
@@
   fence-checks:
     name: Fence Checks (Blocking)
     runs-on: ubuntu-latest
     continue-on-error: false
+    timeout-minutes: 10
```

Then update the CBSP21 manifest text to match.

---

## 6. Local Verification

Run from repo root:

```powershell
python -m json.tool .cbsp21\patches\fence-runs-every-pr-cired004.json
```

Run from `services/api`:

```powershell
python -m app.ci.check_all_fences
```

Expected:

```text
Boundary import check: OK (baseline mode)
Boundary pattern check: OK (baseline mode)
All fence checks passed.
```

Run from repo root:

```powershell
python scripts\ci\check_cbsp21_patch_input.py --base origin/main --head HEAD
$files = git diff --name-only origin/main...HEAD
python scripts\ci\check_cbsp21_gate.py --changed-files $files
```

Expected:

```text
CBSP21 PATCH INPUT GATE: PASS
CBSP21 Gate: PASSED
Coverage: 100.0%
```

Optional YAML structure check if PyYAML is available:

```powershell
python -c "from pathlib import Path; import yaml; d=yaml.safe_load(Path('.github/workflows/architecture_scan.yml').read_text()); print(d['permissions']); print(d['concurrency']); print(d['jobs']['architecture-scan']['timeout-minutes']); print(d['jobs']['fence-checks']['timeout-minutes'])"
```

If PyYAML is not installed locally, rely on GitHub's workflow parser after push.

---

## 7. CI Verification

After pushing the hardening commit to PR #194, wait for:

- `Fence Checks (Blocking)` green;
- CBSP21 manifest gates green;
- workflow parse succeeds;
- no unexpected cancellation of the active PR run.

This verifies the hardening did not break PR #194.

---

## 8. Special Verification Still Required After Merge

Do not make `Fence Checks (Blocking)` required immediately after PR #194 passes.

Required sequence:

1. Merge PR #194.
2. Create a docs-only witness PR from fresh `main`.
3. Change only a docs path, for example:

```text
docs/handoffs/<small-witness-file>.md
```

4. Confirm `Architecture Scan (Non-Blocking)` starts on that docs-only PR.
5. Confirm `Fence Checks (Blocking)` appears and passes.
6. Record the witness PR and job URL.
7. Only then add `Fence Checks (Blocking)` to required checks on `main`.

This is the load-bearing proof that docs-only PRs will not be bricked by the
future required check.

---

## 9. Stop-And-Ask Conditions

Stop before pushing if:

1. The workflow YAML parser rejects the `concurrency` expression.
2. GitHub treats `cancel-in-progress` expression syntax as invalid.
3. `Fence Checks (Blocking)` is renamed or disappears.
4. `check_all_fences` fails locally for a real fence violation.
5. CBSP21 coverage selects the wrong manifest.
6. The branch contains unrelated changes, especially docs handoffs or SPRINTS
   updates not intended for PR #194.

Stop before requiring the check if:

1. A docs-only PR does not start the workflow.
2. A docs-only PR starts the workflow but `Fence Checks (Blocking)` fails.
3. The job becomes flaky or routinely slow.
4. The required-check name in GitHub does not exactly match
   `Fence Checks (Blocking)`.

---

## 10. Done Definition

This dev order is done when:

- PR #194 includes the workflow hardening commit;
- PR #194 checks are green;
- the CBSP21 manifest accurately describes the hardening;
- `python -m app.ci.check_all_fences` passes locally or in CI;
- the docs-only witness requirement remains explicitly recorded as pending.

`CI-RED-004` itself is not closed by this dev order. It closes only after:

- PR #194 lands;
- docs-only witness PR proves the fence runs and passes;
- `Fence Checks (Blocking)` is required on `main`.

