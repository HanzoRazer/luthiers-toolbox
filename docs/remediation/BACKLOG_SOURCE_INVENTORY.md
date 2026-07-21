# BR-001 — Backlog Source Inventory

> Every backlog input examined for the remediation reconstruction, with its location, rough scale, and
> review status. This catalogues the **sources**; item-level dispositions live in
> [BACKLOG_ADJUDICATION_LEDGER.md](BACKLOG_ADJUDICATION_LEDGER.md).

**Review status vocabulary:** `EXAMINED` (inventoried this pass) · `UNAVAILABLE` (could not be reached)
· `NOT_APPLICABLE` (source type not used by this repo). Scale figures are counts at the `origin/main`
baseline; they size the backlog, they are not item dispositions.

## Source catalogue

Baseline `origin/main` = `d716d16`. Sweep date 2026-07-20. Counts are what discovery actually found.

| # | Source | Location | Scale (found) | Review status | Notes |
| - | ------ | -------- | ------------- | ------------- | ----- |
| 1 | Dev Orders & handoffs | `docs/handoffs/` (142), `docs/handoff/` (1), `docs/specs/`, `docs/audits/`, root, `docs/archive/**` | **~166 md docs**; 7 explicit `*DEV_ORDER*` | `EXAMINED` (subset ~45 inspected) | primary source of unfinished-sprint work; "Dev-ready handoff"/`*_dev_order` = strongest open-work signal |
| 2 | Audit reports | `docs/audit/` (30), `docs/audits/` (10), `docs/audit-sources/` | **~40 audit docs** | `EXAMINED` (~34 headers read) | three overlapping audit dirs = a maintainability signal in itself |
| 3 | Branches (unmerged/abandoned) | `git branch -r` | **157 branches, 107 unmerged** (the ~50 merged include `main`/`gh-pages`/publishing refs; raw `branch -r` also lists the `origin/HEAD` symref) | `EXAMINED` | ~24 `ci-red-*` remediation branches dominate open work; SPINE-002/003/004 + governance/C2 tracks stalled |
| 4 | CI-RED / standing-failure threads | `docs/ci/`, `docs/audit/CI_RED*`, `docs/handoffs/CI_RED*` | **11 CI-RED docs** + ~24 branches | `EXAMINED` | open remediation family; July 2026 cohort is freshest |
| 5 | GitHub Issues | `gh issue list` | **0 open; 2 ever (both closed)**: #165, #20 | `EXAMINED` | repo effectively **does not use Issues**; backlog lives in `docs/` + PRs |
| 6 | GitHub PRs | `gh pr list` | **223 total; 0 open** | `EXAMINED` | work tracked via PRs; recent merges #221–#225 |
| 7 | TODO/FIXME/HACK/XXX markers | codebase (grep) | **173 total / 40 in production code** (31 files) | `EXAMINED` | bulk are in `docs/archive/**`; 40 real code markers |
| 8 | Skipped / xfail / todo tests | test suites (grep) | **145 occurrences / 54 files** | `EXAMINED` | notable unconditional skips + xfail-marked known **production bugs** |
| 9 | Stub / fake / disconnected functionality | codebase (grep) | notable set (art-studio UI→no API, `deps` auth/DB stubs, classifiers) | `EXAMINED` | already partly governed by `scan_stub_endpoints.py` + `api_wiring_gate.yml` |
| 10 | Existing ledgers / indexes | root `Safe Remediation Lane.md`; `docs/INDEX.md`; `docs/investigations/api_verify_standing_failures_triage_2026-06-29.md`; `docs/ci/CI_HYGIENE_DEBT_PATCH_PLAN.md` | — | `EXAMINED` | extended, not duplicated; triage doc = most current red picture |
| 11 | Performance findings | `perf/` branch, audits | limited | `EXAMINED` (limited) | no standalone perf red currently; watch |
| 12 | Deferred migration work | R2000 DXF cluster, `gov-converge-*` branches, `strict=False` markers | R2000 cluster + rmos runs_v2 | `EXAMINED` | `MIGRATION_GAP` candidates |
| 13 | CI workflows / gates | `.github/workflows/` | **58 workflows** | `EXAMINED` | governance/ratchet gates; 2 gates currently non-blocking/`continue-on-error` |

## Current-state red picture (re-verified in the Wave 0 run)

Most recent triage (`docs/investigations/api_verify_standing_failures_triage_2026-06-29.md`) reported
**~12 residual `api-verify` reds on main `0daeab14`** (down from 15), targeting **2 residual** after
planned PRs, both parked on product decisions; **~5 real product bugs**. That triage predated current
`origin/main` (`d716d16`), so BR-001 **re-verified against the current tree** in the Wave 0 run:
**21 failed / 8155 passed** on a local Python 3.14 toolchain — **directional, not the authoritative CI
count** (see [WAVE_0_VERIFICATION.md](WAVE_0_VERIFICATION.md)). The April "40 failures" handoff is
**superseded** (ratchets rebaselined: `TARGET_MAX_ENDPOINTS` 945→1225).

## Method

Discovery was performed by four parallel read-only sweeps (branch inventory; Dev Order/handoff
inventory; audit + code-health + markers; GitHub + test/CI state) against the `origin/main` baseline,
then adjudicated in a single coherent pass. GitHub was reachable this pass (`EXAMINED`); had it been
offline it would have been recorded `UNAVAILABLE` and BR-001 would have proceeded on repository-resident
evidence. Only sources actually present are catalogued.

## Coverage honesty

This inventory is **complete at the source level** (every source category catalogued). Item-level
verification is **tiered** (see [charter §3](BACKLOG_REENTRY_CHARTER.md)): Tier A items are verified
before queue entry; Tier B validated against the current repo; Tier C inventoried only. The adjudication
ledger records each item's tier and verification state so coverage is never overstated.
