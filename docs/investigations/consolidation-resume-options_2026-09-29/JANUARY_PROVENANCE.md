# January 2026 provenance

Evidence-only. January is a **search boundary, not a removal criterion** (frozen decision #3). Age alone is never evidence for retirement (§1, out-of-scope).

## Method
```bash
# Volume
git log --since=2026-01-01 --until=2026-02-01 --oneline origin/main    # 670 commits
# First-add events in January under feature roots
git log --diff-filter=A --since=2026-01-01 --until=2026-02-01 --name-only \
  -- services/api/app packages/client/src
# True introduction of a specific path (follows renames)
git log --diff-filter=A --follow --date=short -- <path>
```
Raw logs are not dumped; commands + summarized findings only.

## Key distinction: churn vs first-introduction
January 2026 was high-volume (**670 commits**). A `--diff-filter=A` sweep shows ~350 paths with January add-events under `services/api/app` + `packages/client/src`, but `--follow` shows many of those features were **first introduced in December 2025** and merely continued/renamed in January. Treating January add-events as "January features" would over-count. This report uses **`--follow` earliest date** for candidate provenance.

## January first-add directory volume (add-events, not true introductions)
| Add-events (Jan) | Directory | Note |
|---|---|---|
| 60 | `services/api/app/rmos` | RMOS build-out spans Dec 2025→Feb 2026; core `api_contracts.py` first appears 2025-12-04 |
| 42 | `services/api/app/saw_lab` | Saw Lab; `saw_lab_toolpaths_from_decision_service.py` first appears 2025-12-26 |
| 20 | `services/api/app/sandboxes` | **Directory absent on current `main`** — removed/archived since; nothing to adjudicate (overflow) |
| 14 | `services/api/app/ai_context` | AI advisory context (January-era) |
| 12 | `services/api/app/art_studio` | Art Studio |
| 9 | `services/api/app/ai_context_adapter` | **True January introduction 2026-01-14** (CONS-18) |
| 8 | `services/api/app/cam_core` | cam_core (has a superseded saw_lab duplicate, CONS-03, 2025-12-14) |
| 7 | `services/api/app/vision` | Vision Beta |

## Candidates with confirmed January (`--follow`) provenance still on `main`
| Candidate | Path | Introduced | Disposition |
|---|---|---|---|
| CONS-18 | `services/api/app/ai_context_adapter` | 2026-01-14 | LIVE_INCOMPLETE |
| (overflow) | `services/api/app/routers/legacy_dxf_exports_router.py` | 2026-01-12 | live legacy surface (deferred) |

Other candidates are **not** January-first-introduced (e.g., `api_v1` 2026-02-12; `core/features` 2026-02-09; `agentic` 2026-02-06; `rmos/operations` 2025-12-31; most CF2 handlers Dec 2025 or Mar 2026). They remain in the ledger on **runtime** signals, not age.

## Removed-since-January
- `services/api/app/sandboxes/*` — January add-events but the directory is **absent on current `main`**; already retired. Recorded in `overflow_backlog`; nothing to do on this base.

## Conclusion
Genuine January-era **feature introductions still present** are few (chiefly `ai_context_adapter`, `legacy_dxf_exports_router`). The bulk of "January" activity is churn on subsystems introduced in December 2025 (RMOS, Saw Lab) that later became today's governed/live surfaces. Provenance is recorded per candidate in the ledger; runtime reachability — not January membership — drives every disposition. (CRO-008, CRO-014 satisfied.)
