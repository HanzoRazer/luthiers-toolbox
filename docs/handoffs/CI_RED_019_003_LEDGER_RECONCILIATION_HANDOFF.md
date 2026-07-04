# CI-RED-019 / CI-RED-003 Ledger Reconciliation Handoff

Status: Dev-ready handoff
Created: 2026-07-04
Baseline: origin/main at e1310768 (#184 merged)
Recommended branch: docs/ci-red-019-003-ledger-reconciliation
Owner lane: CI / CL-RED ledger hygiene

## Purpose

Close two stale-open CL-RED ledger rows in `SPRINTS.md` using current main
evidence:

- `CI-RED-019`: the setuptools editable-install mask has already been removed,
  and routing-truth has produced a terminal green verdict on `main`.
- `CI-RED-003`: the technical-debt complexity ratchet has produced terminal
  green `debt-gates` runs on `main`.

This is a bookkeeping correction with live CI witnesses. It should not create
new code, touch application behavior, or reopen the underlying remediation work.

## Grounding Evidence

Current `origin/main` contains the package-finder stanza that CI-RED-019 named
as its required Unit 2 fix:

```toml
[tool.setuptools.packages.find]
where = ["."]
include = ["app", "app.*"]
exclude = ["data", "data.*", "metrics", "metrics.*", "test_support", "test_support.*"]
```

Latest routing-truth main witnesses:

| Workflow | Run | Head SHA | Event | Result |
| --- | ---: | --- | --- | --- |
| `routing_truth.yml` | `28693530110` | `e13107683f26c7c8bd6773602d54d05b356a8916` | push | success |
| `routing_truth.yml` | `28692937055` | `d40c050fc1e970f5159f1cee8bc62aaad9d20e98` | push | success |
| `routing_truth.yml` | `28690640965` | `869384c23c35022c6daf3a6a35804e5b9d6743fc` | push | success |

Latest technical-debt main witnesses:

| Workflow | Run | Head SHA | Event | Result |
| --- | ---: | --- | --- | --- |
| `technical_debt.yml` | `28693530077` | `e13107683f26c7c8bd6773602d54d05b356a8916` | push | success |
| `technical_debt.yml` | `28692937026` | `d40c050fc1e970f5159f1cee8bc62aaad9d20e98` | push | success |
| `technical_debt.yml` | `28690640982` | `869384c23c35022c6daf3a6a35804e5b9d6743fc` | push | success |

Local witness against the current tree:

```text
py -3.11 -m app.ci.check_complexity --baseline app/ci/complexity_baseline.json
OK: No functions exceed complexity 15
```

## Scope

Update the sprint ledger so it reflects current facts:

- Mark `CI-RED-003` closed because its restore trigger has been met: the
  `technical_debt.yml` / `debt-gates` workflow is green on `main`.
- Mark `CI-RED-019` closed because the editable-install mask is gone and the
  routing-truth workflow is green on `main`.
- Preserve the historical lesson that CI-RED-019 was a mask-peel item: fixing
  packaging did not automatically prove routing-truth green; the later green
  routing-truth run is the closure witness.

## Non-Goals

- Do not edit production code.
- Do not change `services/api/pyproject.toml`; the needed package finder is
  already present on `main`.
- Do not change workflow files.
- Do not close `CI-RED-016`; endpoint consolidation remains open.
- Do not close `CI-RED-021`; branch protection remains a direct repo-owner
  action.
- Do not touch C2 / PR #182 / PR #185, or any canonical geometry authority
  ratification text.
- Do not reinterpret future routing-truth failures as the old CI-RED-019 mask.
  A future failure after the mask is removed is a new routing-truth verdict, not
  the old setup failure.

## Decisions

1. **Close by witness, not by inference.** CI-RED-019 closes only because
   routing-truth is now green on `main`, not merely because the packaging stanza
   exists.
2. **Keep mask-peel discipline in the text.** The ledger should explicitly say
   the old setup mask is removed and the real verdict was then witnessed green.
3. **Keep endpoint consolidation separate.** CI-RED-016 remains open even though
   routing-truth is green. The consolidation work is structural route-surface
   debt, not a routing-truth setup failure.
4. **Keep enforcement separate.** CI-RED-021 remains open because branch
   protection and required checks require human/repo-owner action.
5. **Docs-only PR.** This target should be limited to sprint ledger
   reconciliation and the CBSP21 patch manifest for that docs-only change.

## File-by-File Patch Plan

### `SPRINTS.md`

Primary file.

Update the summary table rows:

- `CI-RED-003`: change status from `OPEN` to `CLOSED`, set date to
  `2026-07-04`, and summarize the green `technical_debt.yml` witness
  `28693530077` at `e1310768`.
- `CI-RED-019`: change status from `OPEN` to `CLOSED`, set date to
  `2026-07-04`, and summarize the green `routing_truth.yml` witness
  `28693530110` at `e1310768`.

Update the detailed `CI-RED-003` section:

- Change status to `CLOSED`.
- Replace the stale SAW batch tail description with the closure witness.
- Mention that the previously listed `batch_router.py` complexity tail no
  longer appears under the ratcheted baseline gate.
- Preserve the distinction between the raw complexity landscape and the
  ratcheted `debt-gates` workflow if needed: this closure is for the enforced
  baseline gate.

Update the detailed `CI-RED-019` section:

- Change status to `CLOSED`.
- Record that `services/api/pyproject.toml` now explicitly limits setuptools
  package discovery to `app` / `app.*` and excludes `data`, `metrics`, and
  `test_support`.
- Record the routing-truth green run `28693530110`.
- State clearly: the old editable-install mask is closed; any future
  routing-truth failure is a new route-truth finding and must be triaged on its
  own evidence.

Do not modify neighboring `CI-RED-016`, `CI-RED-020`, or `CI-RED-021` rows except
for incidental line wrapping required by the edit.

### `.cbsp21/patches/ci-red-019-003-ledger-reconciliation.json`

Add a per-PR manifest for the implementation PR.

Expected scope:

- `SPRINTS.md`
- `.cbsp21/patches/ci-red-019-003-ledger-reconciliation.json`

Set `change_type` to `docs`.
Set `behavior_change` to `none`.
List the verification commands below.

### Optional: `docs/handoffs/CI_RED_019_003_LEDGER_RECONCILIATION_HANDOFF.md`

This document is the scoping artifact. If the implementer lands the ledger
change in the same PR as this handoff, keep this file and include it in the
manifest. If the implementer treats this as a pre-existing handoff and opens a
separate ledger-only PR, do not rewrite it.

## Utilities

Use these commands to re-ground before editing:

```powershell
git fetch origin
git show origin/main:services/api/pyproject.toml
gh run list --workflow routing_truth.yml --branch main --limit 5 --json databaseId,status,conclusion,headSha,event,createdAt,updatedAt
gh run list --workflow technical_debt.yml --branch main --limit 5 --json databaseId,status,conclusion,headSha,event,createdAt,updatedAt
```

Use these commands for local witnesses:

```powershell
cd services/api
py -3.11 -m app.ci.check_complexity --baseline app/ci/complexity_baseline.json
cd ../..
py -3.11 scripts/ci/check_cbsp21_patch_input.py --base origin/main --head HEAD
py -3.11 scripts/ci/check_cbsp21_gate.py
```

If the implementation PR edits only docs and a CBSP21 manifest, no app test suite
is required. The proof is the live workflow history plus manifest validation.

## Test Cases

### CI-RED-003 closure witness

Expected:

- `technical_debt.yml` on `main` is terminal `success`.
- Latest known green witness: run `28693530077`, head
  `e13107683f26c7c8bd6773602d54d05b356a8916`.
- Local ratcheted complexity gate returns:
  `OK: No functions exceed complexity 15`.

Failure handling:

- If `technical_debt.yml` is red on latest `main`, do not close CI-RED-003.
- If the red is unrelated to complexity, record the exact failing sub-gate and
  split the issue rather than forcing this closure.

### CI-RED-019 closure witness

Expected:

- `services/api/pyproject.toml` on `origin/main` includes explicit
  `[tool.setuptools.packages.find]`.
- `routing_truth.yml` on `main` is terminal `success`.
- Latest known green witness: run `28693530110`, head
  `e13107683f26c7c8bd6773602d54d05b356a8916`.

Failure handling:

- If routing-truth is currently red because `pip install -e .` again fails with
  flat-layout package discovery, do not close CI-RED-019.
- If routing-truth is red for an actual route-truth mismatch after installation
  succeeds, CI-RED-019 can still close as a mask, but a new routing-truth
  follow-up must be opened with the real failing lane and witness.

### Ledger safety check

Expected:

- `CI-RED-016` remains `OPEN`.
- `CI-RED-021` remains `OPEN`.
- `CI-RED-020` remains `CLOSED`.
- No C2 / GOV-CONVERGE status is changed.

## Rollout Order

1. Create an isolated docs branch from latest `origin/main`.
2. Re-run the two GitHub workflow history checks.
3. Re-run the local ratcheted complexity command.
4. Patch `SPRINTS.md` table rows and detailed sections for CI-RED-003 and
   CI-RED-019.
5. Add or update the per-PR CBSP21 manifest under `.cbsp21/patches/`.
6. Validate the manifest and markdown diff.
7. Open a docs-only PR.
8. Let the CBSP21/doc checks complete.
9. Merge when checks are green.
10. After merge, do not reopen CI-RED-003 or CI-RED-019 unless a new witness
    proves the same defect returned.

## Acceptance Criteria

Done when:

- `SPRINTS.md` no longer lists CI-RED-003 as open.
- `SPRINTS.md` no longer lists CI-RED-019 as open.
- Both closures cite concrete 2026-07-04 main witnesses.
- The ledger still lists CI-RED-016 and CI-RED-021 as open.
- The PR is docs-only plus CBSP21 manifest.

## Stop-and-Ask Triggers

Stop and ask before editing if:

- The latest `routing_truth.yml` run on `main` is red.
- The latest `technical_debt.yml` run on `main` is red.
- `origin/main:services/api/pyproject.toml` no longer contains the explicit
  setuptools package finder.
- The proposed edit would require changing production code, workflow code, or
  C2 governance status.

