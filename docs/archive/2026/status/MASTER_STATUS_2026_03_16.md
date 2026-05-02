# Master Status Report — 2026-03-16

**Unified outstanding items report.** Cross-referenced from: GAP_ANALYSIS_MASTER.md, UNFINISHED_REMEDIATION_EFFORTS.md, REMEDIATION_STATUS_MARCH_2026.md, REMEDIATION_MASTER_2026_03_16.md, REMEDIATION_PLAN.md, REVIEW_REMEDIATION_PLAN.md, ROUTER_CONSOLIDATION_MAP.md, ROUTER_SAFETY_AUDIT.md.

---

## SECTION 1 — GAP ANALYSIS (from GAP_ANALYSIS_MASTER.md)

**Source:** 113 total gaps | **84 resolved** | **29 outstanding**

### Resolved (84) — with commit hash where documented

| Gap ID | Commit / Note |
|--------|----------------|
| LP-GAP-01, EX-GAP-01, EX-GAP-02, EX-GAP-03, SG-GAP-01, SG-GAP-02 | 461caebc, a7a9ee24, 638b7578 |
| VINE-09, SAW-LAB-GAP-01, RMOS-GAP-01, CORRUPT-GAP-01 | 30e50bb3, 6dd8280a, 528f577d, 8f530691 |
| OM-GAP-02, BEN-GAP-03, VINE-07, FV-GAP-03, OM-GAP-03, OM-GAP-04, BEN-GAP-01, OM-PURF-01, OM-PURF-02 | 8f74f599, e60e2df0 |
| BEN-GAP-08, BEN-GAP-09, LP-GAP-03, LP-GAP-05, FV-GAP-06, VINE-03 | 2026-03-15 (carving, f-hole, neck pipeline, asymmetric), ba9574fd, 64f1a87f |
| LP-GAP-06, EX-GAP-13, SG-GAP-14, OM-PURF-07, FV-GAP-07 | 6d7bbb5d (post_processor) |
| GAP-01, NECK-01, GAP-04, GAP-05, GAP-07, GAP-08, NECK-02, NECK-03, NECK-04, NECK-05 | 289b4ac4, 06d28e5c, 0642b77c, 65669faf, etc. |
| BEN-GAP-04, BEN-GAP-05, BEN-GAP-07, OM-GAP-06, BEN-GAP-06, VINE-06 | 51eef4f0, 5cd6c2ba |
| VEC-GAP-01–05, VINE-01, VINE-02, VINE-04, VINE-05, OM-GAP-07, VINE-08 (mount), INLAY-01, INLAY-04, INLAY-05 | 08a7db0d, b8ba05b3, 03acbb4f, 4a0af084, f8e4dded, 6cfe4d12, fe2b4e62, 611addfa, unified coord |
| FV-GAP-04, VINE-11, LP-GAP-02, EX-GAP-04 | ec003681, 703be846, cavity_position_validator |
| SG-GAP-03–12, LP-GAP-10, SG-GAP-11 | 6b947186, 892ed3dd, 6fa4d61b, documented |
| PHYS-01, PHYS-02, PHYS-03, PHYS-04 | pickup_position_calc.py, centerline.py, cavity_placement.py |

### In progress

| Gap ID | Description |
|--------|-------------|
| — | None explicitly marked in progress in GAP_ANALYSIS_MASTER. |

### Outstanding (29) — by severity

| Severity | Count | Gap IDs |
|----------|-------|---------|
| **HIGH** | 3 | INLAY-02 (HeadstockDesignerView.vue non-functional), INLAY-06 (No unified inlay canvas), VINE-08 (Bracing endpoints unreachable from UI) |
| **MEDIUM** | 15 | OM-PURF-05, FV-GAP-05, OM-PURF-03, LP-GAP-04, INLAY-03, VEC-GAP-06, VEC-GAP-07, LP-GAP-08, EX-GAP-12, SG-GAP-13, OM-PURF-08, FV-GAP-10, EX-GAP-05, EX-GAP-06, EX-GAP-07, EX-GAP-08 |
| **LOW** | 11 | VINE-12, OM-PURF-06, FV-GAP-09, LP-GAP-10, SG-GAP-09, EX-GAP-11, EX-GAP-09, EX-GAP-10, VEC-GAP-08 |
| **TABLED** | 2 | PHYS-05 (mounting ring geometry), PHYS-06 (string spread) — require manufacturer data |

### Totals

| Metric | Count |
|--------|-------|
| **Resolved** | 84 |
| **Outstanding** | 29 (3 HIGH, 15 MEDIUM, 11 LOW; 2 TABLED) |
| **Total** | 113 |

---

## SECTION 2 — REMEDIATION EFFORTS (from UNFINISHED_REMEDIATION_EFFORTS.md)

**Source:** 31 efforts | 20 DONE, 8 PARTIAL, 3 NOT STARTED (per doc).

| # | Effort | Status | Current vs target | Owner |
|---|--------|--------|-------------------|-------|
| 1 | Exception hardening (broad catches) | DONE | Bare except 0; broad Exception 315 (target &lt;200) | Claude/Cursor |
| 2 | God-object decomposition (14 files &gt;500 LOC) | PARTIAL | Most decomposed; 27 Python &gt;500 LOC (target ≤10) | Claude/Cursor |
| 3 | Router consolidation (132→&lt;100) | REGRESSED | 160 router files (target ≤50 per REMEDIATION_MASTER) | Deferred |
| 4 | 69 stub endpoints | DONE | Wired to real implementations | Claude/Cursor |
| 5 | 113 instrument build gaps | PARTIAL | 84 resolved, 29 outstanding | Claude/Cursor |
| 6 | Vue component decomposition | PARTIAL | ~90% done; ToolpathPlayer.vue deferred Phase 4 | Deferred |
| 7 | Score 7 plan (9 phases) | PARTIAL | ~30% done | Deferred |
| 8 | Vectorizer upgrade (3 features) | NOT STARTED | Parametric, multi-page, neural — 0/10 | Deferred |
| 9 | Frontend test coverage | DONE | 52 tests added (38038ade) | Claude/Cursor |
| 10 | Bandit security findings | DONE | XML fixed; rest false positives | Claude/Cursor |
| 11 | Vulture dead code | DONE | 15 imports removed, 10 false positives | Claude/Cursor |
| 12 | Radon complexity | DONE | Baselined (avg A, 53 D-grade) | Claude/Cursor |
| 13 | File size baseline violations | PARTIAL | 27 Python &gt;500 (target &lt;10); ratcheted | Claude/Cursor |
| 14 | Singleton store refactor | DONE | c79dd1a7 | Claude/Cursor |
| 15 | Frontend Tailwind/UX fixes | DONE | Tailwind 3.4.19 (bc9042aa) | Claude/Cursor |
| 16 | CNC safety fail-closed | DONE | 6f86018b; DXF gate added 2026-03-15 | Claude/Cursor |
| 17 | Phase 2/3 SaaS plan | PARTIAL | Auth done; payments, sync, multi-tenancy not started | Deferred |
| 18 | Agentic spine | DONE | IMPLEMENTED = True, 773 lines | Claude/Cursor |
| 19 | SAW_LAB learning pipeline | DONE | Disabled by design (documented) | Claude/Cursor |
| 20 | RMOS v1→v2 migration | DONE | v2 default; 5 files use v1 by design | Claude/Cursor |
| 21 | 9 skipped tests for missing features | PARTIAL | 1 fixed (689c3343); others intentional | Claude/Cursor |
| 22 | 7+ NotImplementedError shipping | PARTIAL | pipeline_ops fixed; agentic spine = #18 | Claude/Cursor |
| 23 | 3 broken CI workflows | DONE | Deleted (6d21e96b) | Claude/Cursor |
| 24 | 27 phantom references | DONE | Refs fixed (ba9db4b6) | Claude/Cursor |
| 25 | _experimental/ 8+ modules | PARTIAL | Partial stubs; cnc_production wired (ADR-004) | Deferred |
| 26 | 4 frontend TODOs blocking features | NOT STARTED | PDF export, DXF export, risk override, job nav | Deferred |
| 27 | Abandoned blueprint-import service | PARTIAL | Code exists, not integrated | Deferred |
| 28 | Route analytics middleware in prod | DONE | c4a4788f | Claude/Cursor |
| 29 | rmos/__init__.py bare pass in except | DONE | 75907e0f | Claude/Cursor |
| 30 | Missing secrets documentation | DONE | 4a73ecc4 | Claude/Cursor |
| 31 | data_registry orphaned schema | DONE | Module exists, skip removed (16dec69b) | Claude/Cursor |

---

## SECTION 3 — METRICS DASHBOARD (from REMEDIATION_STATUS_MARCH_2026 + REMEDIATION_MASTER)

**Verified where possible from codebase.**

| Metric | Baseline | Current (verified or doc) | Target | Trend |
|--------|----------|---------------------------|--------|--------|
| Python files (app) | ~1,000 | 1,190 (doc) | — | REGRESSED |
| Router files (all) | 54 | 160 (doc) | ≤50 | REGRESSED |
| Manifest RouterSpec entries | — | **91** (verified) | — | — |
| Files &gt;500 LOC (Python) | 18 | 27 (doc) | ≤10 | REGRESSED |
| Files &gt;500 LOC (Vue) | — | 37 (REMEDIATION_STATUS) | 0 | — |
| Broad exceptions (except Exception / bare) | 725 / 602 | 315 (doc) | &lt;200 | IMPROVING |
| NotImplementedError (code) | 4 | 2 (verified) | 0 | IMPROVING |
| Skipped test files | 8 | 9 (doc) | 0 | UNCHANGED |
| Test collection errors | 0 | 13 (doc) | 0 | REGRESSED |
| Gaps resolved | — | 84/113 | 100+ | IMPROVING |
| @safety_critical sites | 0 | 26 (REVIEW_REMEDIATION_PLAN) | 20+ | IMPROVING |

---

## SECTION 4 — ROUTER CONSOLIDATION STATUS

**Sources:** ROUTER_CONSOLIDATION_MAP.md, ROUTER_SAFETY_AUDIT.md, manifest.py.

### Manifest entries

| When | Count | Note |
|------|-------|------|
| Before 2026-03-16 session | 92 | Duplicate estimator_router removed in Domain 1 |
| After 2026-03-16 session | **91** | Verified: 91 RouterSpec( ) in manifest.py |

### SAFE_MERGE: completed vs remaining

| Status | Count | Detail |
|--------|-------|--------|
| **Verified already aggregated** (Domains 1–7) | 25 | Business (7), Blueprint (5), Blueprint CAM (3), Neck+Music (2), Probe (2), Rosette CAM (3), Guitar CAM (3). No duplicate manifest entries; no code merge needed. |
| **Remaining SAFE_MERGE** | 33 | utility/polygon; instruments (3); art_studio (5); rmos (8); saw_lab (10); cam drilling/toolpath/vcarve/export/utility/profiling/binding (11); tooling (1); compare/lab (1); analytics_materials (1); _experimental cnc_production (1); api_v1 (5). |

### NEEDS_REVIEW (25) — recommended next action

| Router file | Recommended action |
|-------------|---------------------|
| cam/headstock/router.py | Consolidate under cam/guitar or document why separate |
| cam/rosette/photo_batch_router.py | Keep; frontend uses rosette/import_photo. Do not delete. |
| routers/polygon_offset_router.py | Migrate frontend to target path or keep and document |
| routers/dxf_preflight_router.py | Same |
| routers/dxf_adaptive_consolidated_router.py | Same |
| routers/instruments/guitar/headstock_inlay_router.py | In manifest; keep or migrate callers |
| routers/instruments/guitar/pickup_calculator_router.py | Same |
| routers/instruments/guitar/electric_body_router.py | Same |
| instrument_geometry/neck_taper/api_router.py | Same |
| art_studio/bracing_router.py | Wire frontend or document |
| art_studio/inlay_router.py | Same |
| rmos/runs_v2/api_runs_explain.py | Migrate or keep |
| rmos/runs_v2/api_runs_variants.py | Same |
| rmos/validation/router.py | Same |
| routers/strip_family_router.py | Frontend uses strip-families; keep or migrate |
| cam/routers/fret_slots/__init__.py | Not in manifest; add or mount under aggregator |
| routers/cam_post_v155_router.py | Review; no frontend calls in audit |
| routers/legacy_dxf_exports_router.py | Review; legacy paths |
| routers/project_assets_router.py | Stub but frontend (AI Images) calls; migrate or keep |
| routers/misc_stub_routes.py | Review |
| api_v1/__init__.py | Frontend uses v1/frets, v1/dxf, v1/rmos; keep or migrate |
| api_v1/fret_math.py | Frontend uses v1/frets/positions; keep or migrate |
| websocket/router.py | Review |
| analyzer/router.py | Review |
| agentic/router.py | Review |

### Files incorrectly labeled as stubs (per ROUTER_SAFETY_AUDIT)

**Do not delete.** All have real implementations and/or frontend usage:

| File | Implementation | Frontend | Verdict |
|------|----------------|----------|---------|
| cam/routers/bridge_export_router.py | Real (DXF from bridge geometry) | useBridgeExport.ts | KEEP |
| cam/routers/fret_slots_router.py | Real (fret slot preview + calculator) | fretSlotsCamStore, instrumentGeometryStore | KEEP |
| cam/routers/job_intelligence_router.py | Real (job log, insights) | job_int.ts, CamJobInsightsPanel, etc. | KEEP |
| rmos/live_monitor_router.py | Real (drilldown from run artifact) | useLiveMonitorStore | KEEP |
| rmos/mvp_router.py | Real (DXF→GRBL, adaptive plan) | QuickCutView, useDxfToGcode | KEEP |
| rmos/rosette_cam_router.py | Real (segment-ring, export-cnc, cnc-history, etc.) | useRosetteDesignerStore | KEEP |
| rmos/safety_router.py | Real (feasibility, evaluate, override) | useRmosSafetyStore | KEEP |
| services/risk_reports_store.py | Not a router; used by cam_risk_router | — | KEEP |

---

## SECTION 5 — DEPLOYMENT GATE

**Based on all cross-referenced documents.**

### MUST resolve before deployment

| Item | Source | Reason |
|------|--------|--------|
| Test collection errors (13 files) | REMEDIATION_MASTER Part 5 | Full test suite cannot run; blocks CI confidence |
| CNC safety fail-closed / DXF gate | REMEDIATION_MASTER, UNFINISHED #16 | Dangerous G-code risk; DXF gate added, other validations partial |
| HIGH gap frontend blockers (INLAY-02, INLAY-06, VINE-08) | GAP_ANALYSIS | If release promises inlay/bracing UX, these block |

### Can ship as known debt

| Item | Source | Note |
|------|--------|------|
| 29 outstanding gaps (MEDIUM/LOW) | GAP_ANALYSIS | Position validation, verification, frontend polish — document as known limits |
| Router count 160 / manifest 91 | REMEDIATION_MASTER | Structural debt; no functional break if routers load |
| 27 Python files &gt;500 LOC | REMEDIATION_STATUS | Maintainability; ratchet in place |
| 315 broad exceptions | REMEDIATION_STATUS | Target &lt;200; triage in safety paths first |
| NEEDS_REVIEW routers (25) | ROUTER_SAFETY_AUDIT | Keep all; migrate callers or document |
| SAFE_MERGE remaining (33) | ROUTER_SAFETY_AUDIT | Optional consolidation; no path changes required |
| Skipped tests (9 files) | REMEDIATION_MASTER | Intentional for missing features; document |
| _experimental/cnc_production | ADR-004 | Do not delete; promote after GEN-1–GEN-5 and router sprint |
| Phase 2/3 SaaS (payments, sync, multi-tenancy) | UNFINISHED #17 | Roadmap; not required for single-user deploy |
| Score 7 plan residual | UNFINISHED #7 | Quality target; not gate |
| Vectorizer 3 features | UNFINISHED #8 | Enhancement |
| PHYS-05, PHYS-06 (tabled) | GAP_ANALYSIS | Require manufacturer data; document as future |

---

## APPENDIX — Outstanding items touching schemas/instrument_project.py, generators/, or cam/

**Purpose:** Flag any outstanding item that touches these areas. Use when planning changes to project schema, body/neck generators, or CAM pipeline.

**Note:** `schemas/instrument_project.py` does not exist in the repo today; it is the planned canonical project graph (cursorrules, Luthiers_Toolbox_Platform_Architecture.md). Items under that column are those that would create or depend on that schema.

### Outstanding gaps (Section 1) — flagged by area

| Gap ID | Severity | Touches `schemas/instrument_project.py` | Touches `generators/` | Touches `cam/` |
|--------|----------|------------------------------------------|------------------------|----------------|
| INLAY-02 | HIGH | — | — | — |
| INLAY-06 | HIGH | ✓ (unified canvas → single project/canvas model) | — | — |
| VINE-08 | HIGH | — | — | — |
| OM-PURF-05 | MEDIUM | — | — | ✓ (purfling/contour CAM) |
| FV-GAP-05 | MEDIUM | — | ✓ (outline data → body generators) | ✓ (pocket toolpath) |
| OM-PURF-03 | MEDIUM | — | — | ✓ (neck purfling routing) |
| LP-GAP-04 | MEDIUM | — | ✓ (neck build pipeline ↔ fret_slots_cam) | ✓ (fret_slots_cam wiring) |
| INLAY-03 | MEDIUM | — | — | — |
| VEC-GAP-06 | MEDIUM | — | — | ✓ (Phase 2/3/calibration → blueprint→CAM) |
| VEC-GAP-07 | MEDIUM | — | — | ✓ (Phase 3 constants → CAM handoff) |
| LP-GAP-08 | MEDIUM | — | — | ✓ (G-code verification) |
| EX-GAP-12 | MEDIUM | — | — | ✓ (G-code verification) |
| SG-GAP-13 | MEDIUM | — | — | ✓ (G-code verification) |
| OM-PURF-08 | MEDIUM | — | — | ✓ (probe cycle / post-processor) |
| FV-GAP-10 | MEDIUM | — | ✓ (parametric outline → G-code) | ✓ (G-code verification) |
| EX-GAP-05–08 | MEDIUM | — | — | — |
| VINE-12 | LOW | — | — | — |
| OM-PURF-06 | LOW | — | — | ✓ (feed rates in CAM) |
| FV-GAP-09 | LOW | — | ✓ (detailed_outlines / body_outlines) | — |
| LP-GAP-10 | LOW | — | — | — |
| SG-GAP-09 | LOW | — | — | — |
| EX-GAP-11 | LOW | — | ✓ (body_outlines.json ↔ generators/body) | — |
| EX-GAP-09, EX-GAP-10 | LOW | — | — | — |
| VEC-GAP-08 | LOW | — | — | ✓ (OCR dimensions → downstream CAM) |
| PHYS-05, PHYS-06 | TABLED | — | — | — |

### Remediation efforts (Section 2) — flagged by area

| # | Effort | Status | Touches `schemas/instrument_project.py` | Touches `generators/` | Touches `cam/` |
|---|--------|--------|------------------------------------------|------------------------|----------------|
| 2 | God-object decomposition | PARTIAL | — | ✓ (neck_headstock_config, bezier_body, stratocaster_body_generator &gt;500 LOC) | ✓ (many cam/ files &gt;500 LOC) |
| 5 | 113 instrument build gaps | PARTIAL | ✓ (spec/project completeness → project graph) | ✓ (body/neck generators in scope) | ✓ (CAM toolpath/gap resolution) |
| 13 | File size baseline | PARTIAL | — | ✓ (generators in violation list) | ✓ (cam/ in violation list) |
| 17 | Phase 2/3 SaaS plan | PARTIAL | ✓ (project persistence / cloud sync → project schema) | — | — |

### NEEDS_REVIEW routers (Section 4) — flagged by area

| Router file | Touches `schemas/instrument_project.py` | Touches `generators/` | Touches `cam/` |
|-------------|------------------------------------------|------------------------|----------------|
| cam/headstock/router.py | — | — | ✓ |
| cam/rosette/photo_batch_router.py | — | — | ✓ |
| cam/routers/fret_slots/__init__.py | — | — | ✓ |
| routers/instruments/guitar/electric_body_router.py | — | ✓ (electric_body_generator) | — |
| routers/cam_post_v155_router.py | — | — | ✓ |

### Deployment gate (Section 5) — flagged by area

| Item | Touches `schemas/instrument_project.py` | Touches `generators/` | Touches `cam/` |
|------|------------------------------------------|------------------------|----------------|
| Test collection errors (13 files) | — | (possible if tests import generators) | (possible if tests import cam) |
| CNC safety fail-closed / DXF gate | — | — | ✓ |
| HIGH gap frontend blockers | — | — | — |

---

*Generated: 2026-03-16. Single source: cross-reference of the eight listed documents and verified manifest count.*
