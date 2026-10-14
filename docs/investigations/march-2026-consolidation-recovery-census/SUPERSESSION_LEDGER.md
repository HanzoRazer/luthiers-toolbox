# Supersession ledger

This records later decisions that **confirmed, changed or contradicted** a March disposition. Conflicting
statements are kept side by side; neither is silently preferred.

| # | March record | Later record | Relation | Current truth (evidence) |
|---|---|---|---|---|
| 1 | `BACKLOG.md` HEADSTOCK-001 "Built in outputs, not yet in repo"; `21fe1b1f` (03-18 19:37) marks it complete | `1fdd5d53` (19:43) puts "HEADSTOCK-001: dxf_export.py (needs locating)" in Next Up; `98c0b58d` (20:03) implements it | **contradicted within one hour** | The router is live and tested; its only UI caller is stranded (`PARTIAL_MIGRATION`). The "needs locating" line is still on `main` at `docs/SPRINT_BOARD.md:126` |
| 2 | VECTORIZER-001 marked complete by `21fe1b1f` | `98c0b58d` implements it 26 min later | **premature, later confirmed** | Live, UI, tests |
| 3 | NECK-001 removed: "neck suite integrated 2026-03-18" (`4741f084`) | CamSpecPanel ×2 never imported; `neck_profile_export` never registered; headstock views (the same suite) never routed; #308 "MERGED" but stranded | **contradicted** | Partial. See `IMPLEMENTATION_RECONCILIATION.md` |
| 4 | CAM-SURVEY-001 removed: "documented in ARCHITECTURE.md" | `docs/ARCHITECTURE.md:7` has one table row; the survey lives in two archive copies | **partially confirmed** | PARTIAL_MIGRATION |
| 5 | GEOMETRY-009 "not present" (`4741f084` message) | The same commit's diff deletes the GEOMETRY-009 section; `back_brace_calc.py` exists | **contradicted by its own diff** | `back_brace_calc.py` present; **no importer, no route** (`STRANDED_IMPLEMENTATION`) |
| 6 | ROOT-CLEANUP-001 complete, cites `e5dae247` | `e5dae247` does not exist in the object store | **unverifiable citation** | `3357c793` (03-17) is the real cleanup commit |
| 7 | 03-18 03:19 orchestrator, self-described "SAFETY FIX" | `73a2703d` (03-21) archives it under "photo-vectorizer patch history"; #398 (09-22) fixes the rapids by another route | **superseded** | Owner ruling 2026-10-14: SUPERSEDED / INCOMPATIBLE / DO_NOT_FORWARD_PORT |
| 8 | Sprint 3 (04-23): 12 DXF-writer migrations `[x]` (`SPRINTS.md:424-434`) | `sprints_audit_2026-04-23.md:88` "10/12 correctly migrated" **vs** `sprints_md_verification_2026-04-25.md` "10/12 **false**" (`414d41dc`); `8a86ae89` reopens | **two contradictory audits retained** | Fixed `9b7630b9` / `d5033799` through the wrapper, **still R2010**: 3 VERIFIED, 7 PARTIAL, 2 STRANDED |
| 9 | `curve_export_router` migration | Unchecked at `SPRINTS.md:390` **and** checked at `:429` | **internal contradiction, both lines live** | PARTIAL (R2010, no tests) |
| 10 | Sprint 1 "exceeded March 6 baseline" (`3db07c62`) | `3db07c62`, `04735bd4` and `4c4f1a52` do not resolve | **unverifiable** | VEC-ANCHOR-001 reproduced the March 6 anchor itself (sandbox PR #104, merged); "exceeded" stays unproven |
| 11 | DXF output standard "R12 only" (04-02 gate) | R2000 lifted 04-28 (CLAUDE.md); ruling 09-14 "R12 only; R2000 = paid-tier vectorizer only"; `DXF_COMPAT_EXEMPTIONS.md:14` uses R2010 as an example | **changed twice; one doc conflicts** | See `R12_R15_CHAIN.md` |
| 12 | #308 "remove orphaned headstock views", shows MERGED | Merged into #306's already-merged branch; never reached `main` | **contradicted** | Owner ruled PRESERVE; #437 / #438 open |
| 13 | Headstock-lineage doc (#437): the 03-18 → 04-05 history "was not preserved" | Tag `v2.4.0-alpha.1` preserves it up to 03-30 | **corrected by this census** | Only 03-30 → 04-05 is unpreserved. #437 needs that correction before merge |
| 14 | Neck rapids "~780 below Z0" (earlier report) | #398 records 702; this replay reproduces 702 on the pre-fix tree | **superseded figure** | 702 |
