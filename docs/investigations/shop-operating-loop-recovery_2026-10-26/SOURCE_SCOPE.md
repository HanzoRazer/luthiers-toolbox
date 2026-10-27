# Source scope

## Searched

**Luthier's Toolbox (primary, in depth), at `02032884`:**
- `services/api/app` (routers, router-registry manifests, services, stores, schemas)
- `services/photo-vectorizer`
- `packages/client/src` (router, views, components, stores, SDK)
- `docs/` including `docs/archive/` and `docs/archive/recovered/__RECOVERED__/`
- `archive/code/`
- `SPRINTS.md`
- `docs/investigations/ltb-mvs-*`

**LTB history:**
- deleted-file search with `git log --all --diff-filter=D --name-only` over the five capability patterns
- tag `v2.4.0-alpha.1` (pre-rewrite) via `git grep` and path search

**Secondary repositories, at `origin/main`.** Each was asked only the
LTB-originated question named in its ledger row:
- **CNC-Production-Shop:** who owns commercial job identity? Is a revision-pinned estimate available? Does it capture time? Does a versioned product configuration exist?
- **CAM-Assist-Blueprint:** is there an explicit cross-repo package/ID contract?
- **CAM-Creation-Studio:** does another repo claim the guided job surface?
- **Consolidation Lab:** consulted for no row. No LTB finding needed a recovery ledger from it. The LTB-side March census (`march-2026-consolidation-recovery-census/`) already covers the consolidation-era bundles, and none of its ledger rows names a job, quote, kit, timer or traveler capability.

## Excluded

- Forks, empty repos, and unrelated product experiments:
  - `sg-ai-sandbox*`
  - `vectorizer-sandbox*`
  - `tap_tone_pi`
  - `luthier-acoustics-lab`
  - `CNC-Robotic-Bandsaw`
  - `ltb-woodworking-studio`
- Financial TVM/amortization calculators (`ltb_calculators/financial_calculator.py` and its deleted copies). This is personal-finance math, not job costing.
- AI image-generation cost estimates (`ai/cost/estimate.py`, archived `advisory_schemas.py`).

## Screened out (name-only matches, kept out of the ledger)

The raw candidate list was about 52 rows before screening, over the order's
40-row cap. These items were removed because the matching word names a
different concept, not because they were missing. Recording them here is the
"report the clusters" half of the §4.3 rule.

| Cluster | Item | Why it is not a candidate |
|---|---|---|
| "job" | `art_studio/api/rosette_jobs_routes.py` (SQLite art jobs) | `job_id` names a rosette preview render, not a shop job |
| "job" | `docs/ARCHIVE/2025-12/misc/CAM_JOB_SYSTEM_IMPLEMENTATION.md` (deleted `ae8ccd1f`) | A FreeCAD-style CAM job (toolpath container) spec |
| "job" | `routers/job_intelligence_router.py`, `job_insights_router.py` (deleted `545fccad`) | CAM run analytics; their live successor is SOL-D05 |
| "preset/config" | `routers/cnc_production/presets_router.py` (`/api/presets`) | CAM parameter presets (machine/post/feeds), mutable, not a commercial kit |
| "preset/config" | `views/cam/headstock/ConfiguratorView.vue` (archived) | Geometry configurator |
| "template" | `routers/strip_family_router.py` | Design strip-family template; it instantiates without pinning a revision |
| "BOM" | rosette designer BOM and inlay pattern BOM (`art_studio/api/*`) | Per-design material takeoffs, not reusable kits |
| "review" | `review_ux_router.py`, `translator_readiness_router.py` | Static CAM-review registries with no consumer. `human_review_required` is always true. |
| "time" | `core/job_queue` durations; `rmos/live_monitor_router.py` | Software job timing, and machine events synthesized from planned parameters |
| "time" | `utils/stage_timer.py` | Vectorizer debug timer |
| merged | saw execution lifecycle and saw learning feedback | Same `app/saw_lab` package as SOL-D02, so they are one subsystem row |
| merged | `/estimate/quote` endpoint and client estimator presets | Same estimator subsystem as SOL-B01 |
| merged | PR #456 validation-policy mechanism | An unmerged revision of the SOL-E01 package, noted in that row |

## Limits applied

| Limit (order §4.3) | Actual |
|---|---|
| Candidate rows ≤ 40 | 40 |
| LTB share ≥ 60% | 34 / 40 = 85% |
| Secondary rows (CNC-PS + CAM Assist + CCS) ≤ 15 | 6 |
| Rows per capability ≤ 10 | A 8, B 5, C 8, D 9, E 10 |
| Audit packages / draft PRs | 1 / 1 |
