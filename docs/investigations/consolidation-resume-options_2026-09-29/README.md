# Consolidation Resume — Options & Evidence (post-CF2)

**Order:** LTB-CONSOLIDATION-RESUME-004. **Base SHA:** `5258d4c6754c122fcdad65df2019c9f7c11eaffe` (Merge PR #418).

This is **post-CF2 consolidation reconnaissance**. It is **evidence-only**: no production behavior changed, no route/UI/store/generator/geometry/G-code was edited, and nothing was deleted or retired. No implementation is authorized by this increment.

## Purpose and boundaries
- Close the Rosette 003R ledger administratively and return to the larger consolidation program.
- Inventory unfinished / dormant / disconnected / duplicate / prototype / dead work, with January 2026 as a **search boundary, not a removal criterion**.
- Reconcile candidates against **live runtime signals first** (routes, manufacturing-output inventory, readiness/governance registries, client routing/stores, tests). Historical docs are cross-referenced selectively; where docs conflict with runtime behavior, **runtime is authoritative**.
- Produce ranked, mutually-exclusive program options and one bounded recommended next increment.

## Classification model (one primary disposition per candidate)
`COMPLETE_LIVE`, `LIVE_INCOMPLETE`, `BUILT_DISCONNECTED`, `DUPLICATE_SUPERSEDED`, `PROTOTYPE_EXPLICIT`, `DORMANT_UNRESOLVED`, `DEAD_CONFIRMED`, `DOC_ONLY`, `DEFERRED_AUTHORIZED`. `DEAD_CONFIRMED` requires route/import/build/test exclusion evidence — never a bare "no imports found".

## Files
- `BASELINE.md` — post-003R base state, SHAs, inventory, open-PR overlap, Rosette classifications (CRO-001..006).
- `JANUARY_PROVENANCE.md` — January archaeology (churn vs first-introduction), surviving January features (CRO-008, CRO-014).
- `CANDIDATE_LEDGER.json` — canonical machine-readable ledger (28 candidates + overflow backlog).
- `CANDIDATE_LEDGER.md` — human-readable mirror, generated from the JSON (identical candidate IDs; CRO-011).
- `CF2_REMAINDER.md` — all 13 remaining `LIVE_UNGOVERNED` rows, grouped by subsystem/shared handler (CRO-012, CRO-013).
- `OPTIONS.md` — mutually-exclusive Options A/B/C (CRO-015).
- `RECOMMENDATION.md` — one bounded next increment (CRO-016).
- `test_consolidation_ledger.py` — validates ledger parity + disposition vocabulary + CF2 accounting + evidence presence (CRO-007..016).

## Ledger scope (as authorized)
Focused, high-signal: all 13 CF2 rows (consolidated by shared handler; each route enumerated in `CF2_REMAINDER.md`) + surviving January feature-bearing path groups + significant dormant/disconnected/duplicate/live-incomplete features from runtime/reachability signals. Target 20–30 candidates (**28** here), hard ceiling 40; lower-signal items are recorded in the ledger's `overflow_backlog` (not adjudicated).

## Recommended next increment (not authorized here)
**Option A** — contain the Saw Lab toolpaths cluster (`/api/saw/batch/toolpaths/from-decision`, `/api/saw/compare/toolpaths`) behind RMOS authority, mirroring the Rosette pattern (inventory 13→11). See `RECOMMENDATION.md`. Requires explicit authorization as a separate dev order.
