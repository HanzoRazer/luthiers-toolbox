# Remediation Master List — 2026-03-16

> **Last Updated:** 2026-03-16 | **Baseline Commit:** 6d7bbb5d | **CI Status:** PASSING

---

## Executive Summary

| Metric | Baseline (Mar 10) | Current | Target | Status |
|--------|-------------------|---------|--------|--------|
| **Gap Analysis** | 113 total | 84 resolved / 29 remaining | 100+ resolved | 🟢 74% complete |
| **Python Files** | ~1,000 | 1,190 | — | — |
| **Router Files** | 54 | 160 | ≤50 | 🔴 REGRESSED |
| **Files >500 LOC** | 18 | 27 | ≤10 | 🔴 REGRESSED |
| **Skipped Test Files** | 8 | 9 | 0 | 🟡 STABLE |
| **NotImplementedError** | 4 | 2 | 0 | 🟢 IMPROVED |
| **Collection Errors** | 0 | 13 | 0 | 🔴 NEW ISSUE |

---

## Part 1: Gap Analysis Progress (84/113 = 74%)

### Resolved Gaps by Category

| Category | Resolved | Remaining | Key Completions |
|----------|----------|-----------|-----------------|
| 1. DXF & Asset Quality | 7/9 | 2 | DXF validation gate, R12 format |
| 2. CAM Toolpath Generation | 14/17 | 3 | Profiling, binding, carving, f-hole, neck |
| 3. Spec & Data Completeness | 10/10 | 0 | ✅ COMPLETE |
| 4. Geometry & Shape Generators | 9/11 | 2 | Strat/LP body outlines, headstocks |
| 5. API & Endpoint Coverage | 10/10 | 0 | ✅ COMPLETE |
| 6. Integration & Pipeline Bridges | 9/10 | 1 | SVG→DXF, blueprint→CAM |
| 7. Verification & Simulation | 4/6 | 2 | Backplot partial |
| 8. Post-Processor & G-code | 6/7 | 1 | G43/G41/G42, M0/M1 ✅ |
| 9. Frontend & UI | 3/6 | 3 | Strat neck generator |
| 10. Vectorizer Pipeline | 6/8 | 2 | Phase 3/4 endpoints |
| 11. Config & Presets | 4/5 | 1 | Bracing presets |
| 12. Accuracy & Position Validation | 6/8 | 2 | Cavity position validator |
| 13. Physical Component Geometry | 0/6 | 6 | ⏸️ TABLED |

### Remaining HIGH Priority Gaps (5)

| Gap ID | Description | Blocker? |
|--------|-------------|----------|
| INLAY-02 | HeadstockDesignerView.vue non-functional | Frontend |
| INLAY-06 | No unified inlay canvas | Frontend |
| VINE-08 | Bracing endpoints unreachable from UI | Frontend wiring |
| PHYS-02 | Body centerline calculator | Physical dependency |
| PHYS-03 | Pickup cavity-to-coordinate mapper | Physical dependency |

### Recent Completions (Last 48 Hours)

| Date | Commit | Gaps Resolved |
|------|--------|---------------|
| 2026-03-16 | 6d7bbb5d | LP-GAP-06, EX-GAP-13, SG-GAP-14, OM-PURF-07, FV-GAP-07 (post-processor) |
| 2026-03-15 | c7673441 | LP-GAP-05 (asymmetric carved top) |
| 2026-03-15 | — | BEN-GAP-09 (f-hole routing) |
| 2026-03-15 | — | BEN-GAP-08 (3D surface carving) |
| 2026-03-15 | — | LP-GAP-03 (neck CNC pipeline) |
| 2026-03-15 | 51eef4f0 | BEN-GAP-04, BEN-GAP-05, BEN-GAP-07 (binding geometry) |

---

## Part 2: Technical Debt Items (27 Items)

### Priority 1: Critical / Blocking

| # | Item | Current | Target | Owner | Status |
|---|------|---------|--------|-------|--------|
| 1 | Test Collection Errors | 13 errors | 0 | — | 🔴 BLOCKING |
| 2 | PHYS-01: Tap-tone physics | Not started | MVP | — | ⏸️ TABLED |

### Priority 2: High Impact

| # | Item | Current | Target | Status |
|---|------|---------|--------|--------|
| 3 | Router Consolidation | 160 files | ≤50 | 🔴 REGRESSED |
| 4 | Files >500 LOC | 27 files | ≤10 | 🔴 REGRESSED |
| 5 | Dead Endpoint Removal | 9 stub files | 0 | 🟡 PARTIAL |
| 6 | Golden Test Fixtures | Partial | Complete | 🟡 PARTIAL |
| 7 | Skipped Tests | 9 files | 0 | 🟡 STABLE |

### Priority 3: Medium Impact

| # | Item | Current | Target | Status |
|---|------|---------|--------|--------|
| 8 | _experimental/ Cleanup | 7 modules | ≤2 | 🟡 PARTIAL |
| 9 | Frontend TODOs | 15 TODOs | 0 | 🔴 NOT STARTED |
| 10 | Blueprint-import Cleanup | 20 .py files | ≤10 | 🔴 NOT STARTED |
| 11 | DXF Validation Improvements | Partial | Complete | 🟡 PARTIAL |
| 12 | Live Monitor WebSocket | Old impl | Upgrade | 🟡 PARTIAL |
| 13 | Rosette Wheel Registry | Partial | Complete | 🟡 PARTIAL |

### Priority 4: Low Impact / Deferred

| # | Item | Notes |
|---|------|-------|
| 14 | Store Migration (SQLite → Postgres) | Phase 2/3 SaaS |
| 15 | API Rate Limiting | Phase 2/3 SaaS |
| 16 | Score 7 Plan Implementation | ~30% done |
| 17 | Vectorizer Upgrade (3 features) | Phase 2 |

---

## Part 3: Files Over 500 LOC (27 Files)

### Immediate Action Required (Top 10)

| LOC | File | Action |
|-----|------|--------|
| 1241 | `cam/rosette/prototypes/herringbone_embedded_quads.py` | Split or archive |
| 781 | `calculators/binding_geometry.py` | Extract helpers |
| 705 | `calculators/cavity_position_validator.py` | Split validation logic |
| 684 | `router_registry/manifest.py` | Auto-generate? |
| 682 | `cam/rosette/modern_pattern_generator.py` | Modularize |
| 674 | `cam/rosette/prototypes/__archived__/generative_explorer_viewer.py` | DELETE (archived) |
| 661 | `generators/neck_headstock_config.py` | Extract presets to JSON |
| 631 | `core/job_queue/queue.py` | Extract handlers |
| 629 | `instrument_geometry/coordinate_system.py` | OK (core module) |
| 625 | `art_studio/services/generators/inlay_patterns.py` | Extract to presets |

### Already Archived (Can Delete)

| LOC | File |
|-----|------|
| 674 | `cam/rosette/prototypes/__archived__/generative_explorer_viewer.py` |
| 549 | `cam/rosette/prototypes/__archived__/diamond_chevron_viewer.py` |
| 512 | `cam/rosette/prototypes/__archived__/rosette_studio_viewer.py` |

---

## Part 4: Stub Routes to Remove (9 Files)

| File | Endpoints | Action |
|------|-----------|--------|
| `bridge_export_router.py` | 0 real | DELETE |
| `fret_slots_router.py` | stub | DELETE or implement |
| `job_intelligence_router.py` | stub | DELETE |
| `live_monitor_router.py` | partial | Complete or DELETE |
| `mvp_router.py` | legacy | DELETE |
| `rosette_cam_router.py` | stub | Implement or DELETE |
| `safety_router.py` | stub | DELETE |
| `manifest.py` | refs stubs | Update refs |
| `risk_reports_store.py` | stub | DELETE |

---

## Part 5: Test Collection Errors (13 Files)

These prevent full test suite from running:

```
ERROR tests/test_pickup_calculator_smoke.py
ERROR tests/test_relief_vcarve_endpoint_smoke.py
ERROR tests/test_request_id_header_smoke.py
(+ 10 more)
```

**Root Cause:** Likely import errors or missing dependencies.

**Action:** Fix imports → run `pytest --collect-only` → resolve all errors.

---

## Part 6: Session Completions (This Session)

| Item | Description | Commit |
|------|-------------|--------|
| ✅ LP-GAP-06 | Post-processor G43/G41/G42 | 6d7bbb5d |
| ✅ LP-GAP-05 | Asymmetric carved top | c7673441 |
| ✅ 5 related gaps | EX-GAP-13, SG-GAP-14, OM-PURF-07, FV-GAP-07 | 6d7bbb5d |

---

## Part 7: Recommended Next Actions

### Immediate (Today)

1. **Fix Test Collection Errors** — 13 files blocking CI
   - Run `pytest --collect-only 2>&1 | grep ERROR`
   - Fix import errors one by one
   - Target: 0 collection errors

2. **Delete Archived Files** — Quick win, -3 files >500 LOC
   - `rm -rf app/cam/rosette/prototypes/__archived__/`
   - Update any imports
   - Target: 24 files >500 LOC

### This Week

3. **Stub Route Cleanup** — Remove 9 dead endpoints
   - Delete stub files
   - Update manifest.py
   - Target: Clean router registry

4. **Split Large Files** — Top 3 by LOC
   - `herringbone_embedded_quads.py` → extract core logic
   - `binding_geometry.py` → separate validators
   - `cavity_position_validator.py` → per-instrument modules

### Next Sprint

5. **Router Consolidation** — 160 → 50 files
   - Merge related routers
   - Use APIRouter sub-routers
   - Auto-generate from registry

6. **Frontend Gaps** — INLAY-02, INLAY-06, VINE-08
   - Wire HeadstockDesignerView
   - Unified inlay canvas
   - Bracing UI integration

---

## Appendix: Metrics History

| Date | Gaps Resolved | Files >500 | Routers | Tests |
|------|---------------|------------|---------|-------|
| 2026-03-10 | 45/113 | 18 | 54 | ~2800 |
| 2026-03-13 | 67/113 | 22 | 120 | ~3000 |
| 2026-03-15 | 79/113 | 24 | 155 | ~3100 |
| 2026-03-16 | 84/113 | 27 | 160 | 3136 |

---

## Appendix: Source Documents

1. `GAP_ANALYSIS_MASTER.md` — 113 gaps, canonical source
2. `UNFINISHED_REMEDIATION_EFFORTS.md` — 31 efforts
3. `REMEDIATION_STATUS_MARCH_2026.md` — Metrics baseline
4. `REMEDIATION_PLAN.md` — Original 10-item plan
5. `REVIEW_REMEDIATION_PLAN.md` — Updated priorities

---

*This document supersedes all previous remediation status files. Update this file as the single source of truth.*
