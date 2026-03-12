# Unfinished Remediation Efforts

> **Generated:** March 10, 2026  
> **Source:** Cross-repo search of docs, CI baselines, reports, and planning files.  
> **Count:** 31 unfinished efforts — 17 from planning documents + 14 found embedded in code.

---

## Summary

| # | Effort | Source Document | Status | Severity |
|---|--------|----------------|--------|----------|
| 1 | Exception Hardening — broad catches | REMEDIATION_PLAN.md / v2 | 🟡 ~60% done | HIGH |
| 2 | God-Object Decomposition — 14 Python files >500 LOC | REMEDIATION_PLAN_v2.md (Phase 13) | ❌ Not started | HIGH |
| 3 | Router Consolidation — 132 → <100 files | ROUTER_CONSOLIDATION_ROADMAP.md | ❌ Not started | MEDIUM |
| 4 | 69 Stub Endpoints — 15+ high-priority | STUB_DEBT_REPORT.md | ❌ Not started | HIGH |
| 5 | 113 Instrument Build Gaps — 4 CRITICAL DXFs | GAP_ANALYSIS_MASTER.md | 🟡 Partial | CRITICAL |
| 6 | Vue Component Decomposition — 2 files remain | VUE_DECOMPOSITION_GUIDE.md | 🟡 ~85% done | MEDIUM |
| 7 | Score 7 Plan — Phases 1.3–4.3 | SCORE_7_PLAN.md | 🟡 ~25% done | HIGH |
| 8 | Vectorizer Upgrade — 3 features not started | VECTORIZER_UPGRADE_PLAN.md | 🟡 Partial | MEDIUM |
| 9 | Frontend Test Coverage | TESTING_STRATEGY.md / SYSTEM_EVALUATION.md | ❌ Minimal | HIGH |
| 10 | Bandit Security Findings | bandit_report.txt | ❌ Not resolved | MEDIUM |
| 11 | Vulture Dead Code | vulture_report.txt | ❌ Not resolved | LOW |
| 12 | Radon Complexity Hotspots | radon_complexity_report.txt | ❌ Not resolved | LOW |
| 13 | File Size Baseline Violations | ci/file_size_baseline.json | 🟡 Ratcheted | MEDIUM |
| 14 | Singleton Store Refactor | SYSTEM_EVALUATION.md | ❌ Not started | CRITICAL |
| 15 | Frontend Tailwind/UX Fixes | SYSTEM_EVALUATION.md | ❌ Not started | CRITICAL |
| 16 | CNC Safety Fail-Closed Mode | SYSTEM_EVALUATION.md | ❌ Not started | HIGH |
| 17 | Phase 2/3 SaaS Implementation Plan | PHASE_2_3_IMPLEMENTATION_PLAN.md | 🟡 ~10% done | CRITICAL |
| | | | | |
| **— Code-Level Findings (not in any planning doc) —** | | | | |
| 18 | Agentic Spine — pure stubs | `agentic/spine/replay.py`, `moments.py` | ❌ `IMPLEMENTED = False` | MEDIUM |
| 19 | SAW_LAB Learning Pipeline — disabled by default | 3 config files, all `_ENABLED=false` | ❌ Shipped but off | HIGH |
| 20 | RMOS Runs v1→v2 migration incomplete | `rmos/__init__.py`, `fix_imports.py` | 🟡 v2 default, v1 still loadable | HIGH |
| 21 | 9 Skipped tests for missing features | `test_cam_fret_slots_export.py`, etc. | ❌ Routes/modules absent | HIGH |
| 22 | 7+ `NotImplementedError` functions shipping | `pipeline_operations.py`, `archtop_cam_router.py` | ❌ Raise at runtime | HIGH |
| 23 | 3 Broken CI workflows (dead paths) | `cam_gcode_smoke.yml`, `helical_badges.yml`, `lpmd-inventory.yml` | ✅ Resolved (6d21e96b) | ~~CRITICAL~~ |
| 24 | 27 Phantom references to deleted code | `__RECOVERED__/README.md` | ✅ Resolved (ba9db4b6) | ~~CRITICAL~~ |
| 25 | `_experimental/` — 8+ half-built modules | `ai_cam/`, `ai_core/`, `infra/`, `analytics/` | 🟡 Partial stubs | MEDIUM |
| 26 | 4 Frontend TODOs blocking features | Rosette PDF export, DXF export, risk override API, job detail nav | ❌ Not started | MEDIUM |
| 27 | Abandoned service (no CI, no tests) | `blueprint-import/` | 🟡 Code exists, not integrated | MEDIUM |
| 28 | Route analytics middleware left in prod | `main.py` TODO comment | ❌ Debug code in production | HIGH |
| 29 | `rmos/__init__.py` — 8+ bare `pass` in except blocks | Lines 145–311 | ❌ Swallowed errors | HIGH |
| 30 | Missing secrets documentation | Railway, SG_SPEC_TOKEN, etc. | ❌ Not documented | MEDIUM |
| 31 | `data_registry` module deleted, schema orphaned | `user_data` table + skipped test | ❌ Dead schema | LOW |

---

## Detailed Breakdown

### 1. Exception Hardening — Broad `except Exception` Triage

**Source:** [REMEDIATION_PLAN.md](REMEDIATION_PLAN.md), [REMEDIATION_PLAN_v2.md](REMEDIATION_PLAN_v2.md) (Phases 1.2 / 15)

| Metric | Starting | Current | Target |
|--------|----------|---------|--------|
| Bare `except:` | 97 | **0** | 0 ✅ |
| Broad `except Exception` | 1,622 | **~602** | <200 |

**What remains:** Triage 602 broad exception blocks into three buckets:
- **A — Safety-critical** (`rmos/`, `cam/`, `saw_lab/`, `calculators/`): replace with specific exceptions, fail-closed with `raise`
- **B — API handlers**: keep but add structured logging + error ID
- **C — Utility/internal**: replace with specific exceptions case-by-case

**Effort estimate:** 8–16 hours

---

### 2. God-Object Decomposition — 14 Python Files >500 LOC

**Source:** [REMEDIATION_PLAN_v2.md](REMEDIATION_PLAN_v2.md) (Phase 13)

| File | Lines | Priority |
|------|-------|----------|
| `adaptive_router.py` | 1,244 | HIGH |
| `blueprint_router.py` | 1,236 | HIGH |
| `geometry_router.py` | 1,100 | MEDIUM |
| `blueprint_cam_bridge.py` | 937 | MEDIUM |
| `dxf_preflight_router.py` | 792 | MEDIUM |
| `probe_router.py` | 782 | MEDIUM |
| `business/router.py` | 546 | LOW |
| `cam/rosette/presets.py` | 578 | LOW |
| `cam/routers/stub_routes.py` | 662 | LOW |
| `routers/neck_router.py` | 683 | LOW |
| *(4 more files 507–611 lines)* | | LOW |

**Strategy:** Extract sub-routers by domain (e.g., `adaptive_pocket_router`, `adaptive_contour_router`).

**Effort estimate:** 8–16 hours

---

### 3. Router Consolidation

**Source:** [ROUTER_CONSOLIDATION_ROADMAP.md](ROUTER_CONSOLIDATION_ROADMAP.md)

| Metric | Current | Target |
|--------|---------|--------|
| Route decorators | 644 | <500 |
| Router files | 132 | <100 |

**Planned consolidation (14 files → 5):**

| Target | Source Files | Reduction |
|--------|-------------|-----------|
| Saw Lab execution lifecycle | 6 files (abort, complete, confirmation, metrics, start, status) | 6→1 |
| Saw Lab toolpath operations | 4 files (download, lint, lookup, validate) | 4→1 |
| Saw Lab metrics lookup | 3 files | 3→1 |
| CAM pipeline | 3 files | 3→1 |
| Machines/Posts deprecation | 2 files | 2→0 (remove) |

**Effort estimate:** 8–16 hours

---

### 4. Stub Endpoints — 69 Stubs, 15+ High Priority

**Source:** [STUB_DEBT_REPORT.md](STUB_DEBT_REPORT.md) (generated 2026-02-23)

**High-priority stubs needing real implementations:**

| Group | Count | Examples |
|-------|-------|---------|
| RMOS Analytics | 5 | lane-analytics, risk-timeline, summary, trends, export |
| RMOS Rosette CNC | 6 | segment-ring, generate-slices, preview, export-cnc, cnc-history, cnc-job |
| AI CAM Advisory | 3 | analyze-operation, explain-gcode, optimize |
| Saw Lab / Job Log | 7 | saw run queries, creates, operational endpoints |
| CAM Adaptive/Pocket | 4 | |
| CAM Risk/Logs | 4 | |
| CAM Drilling/Compare | 6 | |
| Machines/Posts | 4 | |
| Blueprint | 3 | |

**Effort estimate:** 40–60 hours cumulative

---

### 5. Instrument Build Gaps — 113 Total, 4 CRITICAL DXFs

**Source:** [GAP_ANALYSIS_MASTER.md](GAP_ANALYSIS_MASTER.md) (updated 2026-03-09)

**CRITICAL DXF problems — every build blocked:**

| Instrument | Gap |
|-----------|-----|
| Les Paul 1959 | Multi-layer CAM DXF never delivered (8 layers referenced in spec) |
| Smart Guitar | 12.1% narrow, 4.3% short vs spec; X-axis 22.2mm off-center |
| Explorer 1958 | DXF coarse (24 pts), wrong format (AC1024 not R12) |
| J45 Vine | Bracing DXF: 460 scattered entities, 0 closed polylines |

**CAM modules that don't exist yet:**

| Module | Instruments Unblocked |
|--------|----------------------|
| `app/cam/profiling/` — Perimeter profiling w/ tabs + lead-ins | 4 instruments |
| `app/cam/binding/` — Binding/purfling channel routing | 2 instruments |
| `app/cam/neck/` — Neck CNC pipeline (truss rod, profile carving, frets) | 3 instruments |
| `app/cam/carving/` — 3D surface carving (archtop graduation) | 2 instruments |
| `app/cam/drilling/` — G83 peck cycles, parametric holes | 2 instruments |

**Other gap categories:** Spec completeness, geometry generators, API coverage, vectorizer integration, headstock outlines (5 shapes pending), pickup position calculator (blocked on physical measurements).

**Effort estimate:** 120–200 hours total

---

### 6. Vue Component Decomposition

**Source:** [VUE_DECOMPOSITION_GUIDE.md](VUE_DECOMPOSITION_GUIDE.md)

24 components have been decomposed successfully. 2 remain above threshold:

| Component | LOC | Status |
|-----------|-----|--------|
| `ManufacturingCandidateListV2.vue` | 578 | Needs review |
| `GeometryToolbar.vue` | 614 | Documented, no extraction needed (per guide) |

The `AdaptivePocketLab.vue` decomposition is marked "IN PROGRESS" but composables have been extracted — parent file still needs to wire them in.

**Effort estimate:** 4–8 hours

---

### 7. Score 7 Plan (5.9 → 7.0)

**Source:** [SCORE_7_PLAN.md](SCORE_7_PLAN.md)

| Phase | Description | Status |
|-------|-------------|--------|
| 1.1 Dead code purge | Delete stale directories | ✅ Done |
| 1.2 File size gate CI | Create enforcement script | ✅ Done |
| 1.3 Split god files | Extract composables, wire into parents | 🟡 Composables extracted, wiring pending |
| 1.4 Router consolidation | 199 → <100 router files | ❌ Not started |
| 2.1 Curated API v1 | 40 essential endpoints | ❌ Not started |
| 2.2 Guided workflows | Step-by-step wizards for 3 core flows | ❌ Not started |
| 2.3 Error recovery UI | Replace silent failures with actionable modals | ❌ Not started |
| 3.1 Exception hardening | <100 broad `except Exception` in safety paths | ❌ Not started (overlaps with #1 above) |
| 3.2 Coverage push | 80% on safety-critical modules | ❌ Not started |
| 3.3 Async job queue | G-code generation via Redis/RQ | ❌ Not started |
| 4.1 Component library | PrimeVue migration | ❌ Not started |
| 4.2 Design tokens | Already exists (done independently) | ✅ Done |
| 4.3 Dark mode | Audit/fix all components | ❌ Not started |

**Effort estimate:** 3–5 weeks per original plan

---

### 8. Vectorizer Upgrade — 3 Features Not Started

**Source:** [VECTORIZER_UPGRADE_PLAN.md](../services/blueprint-import/docs/VECTORIZER_UPGRADE_PLAN.md)

Current vectorizer version: 4.0.0, rated 8.0/10.

| Feature | Status | Score |
|---------|--------|-------|
| Parametric constraints | ❌ Not started | 0/10 |
| Multi-page extraction | ❌ Not started | 0/10 |
| Neural boost | ❌ Not started | 0/10 |

These are the remaining features to reach the 8.5+ target rating.

**Effort estimate:** 20–40 hours

---

### 9. Frontend Test Coverage

**Source:** [TESTING_STRATEGY.md](TESTING_STRATEGY.md), [SYSTEM_EVALUATION.md](SYSTEM_EVALUATION.md)

| Metric | Current | Target |
|--------|---------|--------|
| Frontend test files | 27 | Not defined |
| Coverage scope | `src/sdk/**` only | Full SPA |
| Coverage threshold | None | Not defined |

**Planned but not started (from TESTING_STRATEGY.md):**

| Component | Status |
|-----------|--------|
| RiskBadge | 🔜 Planned |
| WhyPanel | 🔜 Planned |
| RmosTooltip | 🔜 Planned |
| CamParametersForm | 🔜 Planned |

**Additional gaps:** Route guards, auth flows, store interactions, form validation, error states, empty states, modal behaviors, responsive breakpoints — all untested.

**Effort estimate:** 1–2 weeks

---

### 10. Bandit Security Findings

**Source:** [bandit_report.txt](../bandit_report.txt)

| Finding | Severity | Count | Detail |
|---------|----------|-------|--------|
| B314: XML parsing without `defusedxml` | MEDIUM | 2 | `art_studio/prompts/validators.py` |
| B404: `subprocess` import | LOW | 2 | |
| B607: Partial path execution | LOW | 1 | `ai_context_adapter/routes.py` |
| B105: Hardcoded password string | LOW/FP | 1 | Test validator — likely false positive |

**Actionable:** Install `defusedxml`, migrate 2 XML parsing instances.

**Effort estimate:** 1–2 hours

---

### 11. Vulture Dead Code

**Source:** [vulture_report.txt](../vulture_report.txt)

35+ unused imports, variables, and class attributes detected at 90–100% confidence. Includes: `grace_period_ms`, `moments`, `BOMInstrumentType`, `round_joints`, and others.

**Effort estimate:** 3–4 hours (audit + delete)

---

### 12. Radon Complexity Hotspots

**Source:** [radon_complexity_report.txt](../radon_complexity_report.txt)

| Function | Complexity | Grade |
|----------|-----------|-------|
| `PostInjectionMiddleware.dispatch` | 21–22 | D |
| `BudgetTracker.get_status` | 12 | C |
| *(additional hotspots in critical paths)* | | |

**Status:** Documented, not blocking CI.

**Effort estimate:** 8–16 hours for grade-D functions

---

### 13. File Size Baseline Violations

**Source:** [ci/file_size_baseline.json](../ci/file_size_baseline.json)

11–16 Python files remain above the 500-line limit. The CI gate uses a ratchet baseline — files can't grow, but existing violations aren't yet resolved.

**Target:** <10 files above limit.

**Effort estimate:** Overlaps with #2 (god-object decomposition)

---

### 14. Singleton Store Refactor — Horizontal Scaling Blocker

**Source:** [SYSTEM_EVALUATION.md](SYSTEM_EVALUATION.md)

Module-level `_store = None` globals in:
- `app/rmos/constraint_profiles.py`
- `app/_experimental/cnc_production/feeds_speeds/core/learned_overrides.py`
- `app/advisory/store.py` (multiple singletons)
- `app/api/deps/rmos_stores.py`

**Impact:** Each process gets its own copy. Multi-instance deployment (horizontal scale) is impossible.

**Fix:** Refactor to FastAPI `Depends()` with request-scoped stores backed by shared storage (Redis or PostgreSQL).

**Effort estimate:** 2–3 days

---

### 15. Frontend Tailwind / UX Structural Fixes

**Source:** [SYSTEM_EVALUATION.md](SYSTEM_EVALUATION.md)

| Issue | Severity |
|-------|----------|
| Tailwind classes used without Tailwind installed (10+ components) | 🔴 CRITICAL |
| Duplicate toast systems (custom + vue-toastification) | 🟠 HIGH |
| `window.confirm()` in 10+ places instead of SmallModal | 🟠 HIGH |
| SDK bypass — stores calling `api()` directly | 🟠 HIGH |
| No global error boundary | 🟠 HIGH |
| No auth guards on most routes | 🟠 HIGH |
| Static dashboard with hardcoded placeholder data | 🟡 MEDIUM |

**Effort estimate:** 2–3 days for critical/high items

---

### 16. CNC Safety — Fail-Closed Mode

**Source:** [SYSTEM_EVALUATION.md](SYSTEM_EVALUATION.md)

The CNC toolpath system currently "fails open" — it always produces G-code regardless of parameter safety. Missing validations:

| Gap | Risk |
|-----|------|
| Zero RPM accepted | Tool drags through material without cutting |
| Zero flutes accepted | Division-by-zero in chipload calculation |
| Min > max feed rates not rejected | Nonsensical clamped values |
| DXF validation optional before export | Unchecked geometry → unsafe toolpaths |
| No "refuse to generate" mode | Dangerous configs still produce G-code |

**Effort estimate:** 4–8 hours

---

### 17. Phase 2/3 SaaS Implementation Plan

**Source:** [PHASE_2_3_IMPLEMENTATION_PLAN.md](PHASE_2_3_IMPLEMENTATION_PLAN.md) (dated 2026-03-06)

The largest single planned effort in the repo. Targets converting the single-user tool (7.6/10) into a 3-tier SaaS product (Free/Pro/Shop, 9.0/10 target). Estimated 12+ weeks total.

**Phase 2 — Feature Parity & UX (4–6 weeks):**

| Section | Description | Status |
|---------|-------------|--------|
| 2.1 Missing routes | 24 routes listed; 33→23 stubs remaining after partial remediation | 🟡 ~68% stub reduction |
| 2.2 Beginner UX | Guided mode store, plain-English error messages, `HelpTooltip.vue` | ❌ Not started |
| 2.3 Vectorizer polish | Body outline accuracy 92→96%, OCR extraction 70→85%, false positive 8→3% | ❌ Not started |
| 2.4 Instrument library | 33 models advertised, ~16 implemented. 17 missing (Explorer, Flying V, D-28, Benedetto, etc.) | ❌ Not started |

**Phase 3 — SaaS Infrastructure (8–12 weeks):**

| Section | Description | Status |
|---------|-------------|--------|
| 3.1 Authentication | Clerk or Supabase integration, tier-based feature flags | ❌ Not started |
| 3.2 Payment | Stripe checkout, customer portal, webhooks. Pro $49/mo, Shop $149/mo. | ❌ Not started |
| 3.3 Project persistence | Cloud sync (S3/R2), free tier limited to 5 local projects | ❌ Not started |
| 3.4 Multi-tenancy | Workspace with 10 seats, role-based access (Admin/Builder/Operator) | ❌ Not started |
| 3.5 Business features | Quote generator, invoice manager, customer CRM | ❌ Not started |
| 3.6 Offline mode | Service worker, cache app shell, queue offline operations | ❌ Not started |

**Progress to date (from Progress Log):**
- 11 endpoints proxied to real implementations, 21 smoke tests added
- ~39 dead code stubs removed entirely
- Total stubs: 73 → 23 (68% reduction)
- 23 stubs remain: 13 HIGH (RMOS analytics/rosette), 6 MEDIUM (AI advisories), 4 LOW (CAM misc)

**Effort estimate:** 12–16 weeks remaining

---

---

## Code-Level Findings (Not in Any Planning Document)

These were found by searching the codebase for evidence of abandoned work, disabled features, half-migrations, broken CI, and phantom references — none of them appear in any remediation plan.

### 18. Agentic Spine — Pure Stubs

**Source:** `services/api/app/agentic/spine/replay.py`, `moments.py`

Both files contain `IMPLEMENTED = False` as an explicit flag. Every function raises `NotImplementedError`:
- `load_events()`, `run_shadow_replay()`, `group_by_session()`, `select_moment_with_grace()` — all stubs
- `detect_moments()` — stub

These modules are imported and registered but do nothing. Anyone calling them gets an exception.

### 19. SAW_LAB Learning Pipeline — Shipped but Disabled

**Source:** Three config files, all defaulting to `false`:
- `saw_lab_learning_hook_config.py` → `SAW_LAB_LEARNING_HOOK_ENABLED=false`
- `saw_lab_metrics_rollup_hook_config.py` → `SAW_LAB_METRICS_ROLLUP_HOOK_ENABLED=false`
- `saw_lab_learning_apply_service.py` → `SAW_LAB_APPLY_ACCEPTED_OVERRIDES=false`

This is a three-part learning system (emit events → rollup metrics → apply learned overrides) that was built, tested, but never turned on. The code works — it's just gated off. Either turn it on or document why it's off.

### 20. RMOS Runs v1→v2 Migration Incomplete

**Source:** `services/api/app/rmos/__init__.py` (lines 88–94), `services/api/fix_imports.py`

Both v1 and v2 run store implementations coexist, switched by `RMOS_RUNS_V2_ENABLED` (defaults to `true`). An import migration script (`fix_imports.py`) exists but evidently wasn't run everywhere — old `from app.rmos.run_artifacts.store` imports may still exist. The v1 path is dead weight unless you need rollback capability.

### 21. 9 Skipped Tests for Missing Features

| Test File | What's Missing |
|-----------|----------------|
| `test_data_registry.py` | Module `app.data_registry` deleted |
| `test_pocket_solid_mesh.py` | `build_geom_fixture` never implemented |
| `test_cam_fret_slots_export.py` | `/api/cam/fret_slots/*` routes don't exist |
| `test_art_studio_promotion_intent_export_contract.py` | `/api/art/design-first-workflow/*` routes |
| `test_art_studio_cam_promotion_contract.py` | Same design-first-workflow routes |
| `test_dxf_security_patch.py` | Tests diverged from implementation |
| `test_fret_slots_cam_guard.py` | Same fret slots routes |
| `test_e2e_workflow_integration.py` | References undefined methods |
| `test_llm_client_isolation.py` | `_experimental/ai_graphics/services/` doesn't exist |

These tests were written for features that were never completed, then skipped to keep the suite green. They represent **9 features that were started and abandoned**.

### 22. 7+ Functions Shipping `NotImplementedError`

| Module | Function | What it blocks |
|--------|----------|----------------|
| `agentic/spine/replay.py` | `load_events()` | Agentic replay |
| `agentic/spine/replay.py` | `run_shadow_replay()` | Shadow testing |
| `agentic/spine/replay.py` | `group_by_session()` | Session analysis |
| `agentic/spine/replay.py` | `select_moment_with_grace()` | Grace-period selection |
| `agentic/spine/moments.py` | `detect_moments()` | Moment detection |
| `routers/pipeline_operations.py` | `preflight_dxf_bytes()` | DXF preflight (fallback) |
| `routers/pipeline_operations.py` | `extract_loops_from_dxf()` | DXF loop extraction (fallback) |
| `routers/cam/guitar/archtop_cam_router.py` | Bridge generation | Archtop bridge G-code |
| `routers/cam/guitar/archtop_cam_router.py` | Saddle generation | Archtop saddle G-code |

### 23. 3 Broken CI Workflows

| Workflow | Problem |
|----------|--------|
| `cam_gcode_smoke.yml` | Watches `server/cam_router.py` — no `server/` directory exists. Runs `cd server` which fails. |
| `helical_badges.yml` | Calls `python tools/run_helical_smoke.py` — file does not exist. |
| `lpmd-inventory.yml` | Searches for `server/pipelines` directory — doesn't exist. Will `SystemExit` on every run. |

These workflows will fail if triggered. They reference a legacy `server/` directory structure that was replaced by `services/api/` but the workflows were never updated.

### 24. 27 Phantom References to Deleted Code

**Source:** `__RECOVERED__/README.md`

64,800 lines were deleted across 4 cleanup waves (Dec 2025–Feb 2026). 88 files were recovered and organized in `__RECOVERED__/`. The README documents **27 phantom references** — paths in registry files, spec files, and import statements that point to code that no longer exists.

Categories of recovered code:
- `A_cam_core/` (1,567 lines) — CAM primitives
- `C_archtop_pipeline/` (1,048 lines) — Archtop-specific CAM
- `D_guitar_cam_routers/` (1,440 lines) — Guitar-specific routing
- `E_rosette_fabrication/` (1,747 lines) — Rosette production
- `G_rmos_orchestration/` (2,708 lines) — RMOS workflows
- `I_experimental/` (2,734 lines) — Experimental features

These phantom references mean contracts, docs, and specs claim features exist that were deleted.

### 25. `_experimental/` — 8+ Half-Built Modules

| Directory | Contents | State |
|-----------|----------|-------|
| `ai_cam/` | Advisor, explain-gcode, optimize, models | Stubs with comments like "potential AI-generated suggestions" |
| `ai_core/` | Clients, generators, safety, structured output | Skeletal infrastructure |
| `analytics/` | Risk bucket classification | Partial |
| `cnc_production/learn/` | Risk buckets, learning models | Partial |
| `infra/live_monitor.py` | Live monitoring | Explicitly says "default behavior is to just log to stdout" |
| `joblog_router.py` | Experimental job log API | Partial |

### 26. 4 Frontend TODOs Blocking Real Features

| File | TODO | Impact |
|------|------|--------|
| `useRosetteDesignerExport.ts` | "Generate PDF with annotations" | Rosette export incomplete |
| `useCurveHistory.ts` | "Implement DXF export via API" | Curve lab can't export |
| `useSawRiskActions.ts` | "Call backend API to apply override" | Risk override button does nothing |
| `useJobIntHistoryActions.ts` | "Open detail modal or navigate to detail view" | Job history click handler empty |

### 27. Abandoned Service — `blueprint-import/`

`services/blueprint-import/` has Python analyzer code, docs, and an upgrade plan, but no CI workflow, no integration tests, and is not imported by the main API. It exists as a standalone service with no clear integration path.

> **Note:** `services/photo-vectorizer/` — not viable. This technology will not be utilized and will not be completed.

### 28. Route Analytics Middleware in Production

**Source:** `services/api/app/main.py` line ~162

Contains: `# TODO: Remove before production or gate behind ENABLE_ROUTE_ANALYTICS env var`

This debug middleware is active in production builds. It should be gated behind an env var or removed.

### 29. `rmos/__init__.py` — 8+ Bare `pass` in Exception Handlers

**Source:** `services/api/app/rmos/__init__.py` lines 145, 155, 174, 188, 231, 283, 293, 302, 311

At least 8 exception handlers silently swallow errors with `pass`. This is in the RMOS initialization path — the core manufacturing orchestration module. Failed router loads, missing dependencies, and configuration errors all disappear silently.

### 30. Missing Secrets Documentation

| Secret | Used By | Documented? |
|--------|---------|-------------|
| `SG_SPEC_TOKEN` | Docker build, sg-spec package install | ❌ |
| `RAILWAY_TOKEN` | `railway-deploy.yml` | ❌ |
| `RAILWAY_PROJECT_ID` | `railway-deploy.yml` (hardcoded UUID) | ❌ |
| `OPENAI_API_KEY` | AI transport layer | ❌ (in README? partially) |
| `ANTHROPIC_API_KEY` | LLM client | ❌ |

README doesn't document which GitHub secrets must be created for CI/CD to work. Contributors will hit opaque failures.

### 31. `data_registry` Module Deleted, Schema Orphaned

**Source:** `test_data_registry.py` (skipped), `data_registry/registry.py`

The `user_data` table has a `CREATE TABLE IF NOT EXISTS` statement that still executes on startup, but the module that was supposed to manage this table (`app.data_registry`) was deleted. The table is created but never written to or read from.

---

## Cross-Reference: Overlapping Efforts

Several efforts overlap and should be coordinated:

| Efforts | Overlap |
|---------|---------|
| #1 (Exception hardening) ↔ #7 (Score 7 Plan Phase 3.1) | Same work item in two plans |
| #2 (Python god-objects) ↔ #13 (File size baseline) | Decomposing files resolves baseline violations |
| #3 (Router consolidation) ↔ #7 (Score 7 Plan Phase 1.4) | Same work item in two plans |
| #6 (Vue decomposition) ↔ #7 (Score 7 Plan Phase 1.3) | Same work item in two plans |
| #4 (Stub endpoints) ↔ #17 (Phase 2/3 Plan §2.1) | Stub debt is tracked in both docs |
| #7 (Score 7 Plan §2.2–2.3) ↔ #17 (Phase 2/3 Plan §2.2) | Both plan guided workflows + error recovery |
| #8 (Vectorizer upgrade) ↔ #17 (Phase 2/3 Plan §2.3) | Vectorizer polish appears in both |
| #5 (Instrument gaps) ↔ #17 (Phase 2/3 Plan §2.4) | Missing instruments tracked in both |

---

## Suggested Priority Order

| Priority | Effort | Rationale |
|----------|--------|-----------|
| **P0** | #15 — Tailwind/UX fixes | Styles are visibly broken right now |
| **P0** | #16 — CNC safety fail-closed | Safety-critical — bad G-code risks real harm |
| **P0** | #5 — CRITICAL DXF gaps | 4 instruments entirely blocked |
| **P1** | #1 — Exception hardening | 602 broad catches in safety paths |
| **P1** | #10 — Bandit defusedxml | 2-hour fix removes real security risk |
| **P1** | #14 — Singleton store refactor | Blocks any multi-instance deployment |
| **P2** | #2 — Python god-objects | Code health, overlaps with file size gate |
| **P2** | #4 — Stub endpoints | 15+ high-priority stubs blocking features |
| **P2** | #9 — Frontend test coverage | 27 tests for 75 routes is inadequate |
| **P3** | #3 — Router consolidation | 132 files, target <100 |
| **P3** | #7 — Score 7 Plan residuals | Multiple phases pending |
| **P3** | #8 — Vectorizer upgrades | 3 features at 0/10 |
| **P4** | #6 — Vue decomposition | Nearly done, 2 files remain |
| **P4** | #11 — Dead code cleanup | 35+ items, low risk |
| **P4** | #12 — Complexity hotspots | Documented, not blocking |
| **P4** | #13 — File size baseline | Resolves with #2 |
| **P2** | #17 — Phase 2/3 SaaS plan | Largest single effort; stub remediation started, 90% of plan untouched |
| | | |
| **--- Code-Level (not in any plan) ---** | | |
| **P0** | #23 — 3 broken CI workflows | Will fail if triggered; reference deleted `server/` directory |
| **P0** | #24 — 27 phantom references | Contracts/specs claim deleted features still exist |
| **P1** | #29 — 8+ bare `pass` in RMOS init | Core orchestration module silently swallows errors |
| **P1** | #28 — Route analytics in production | Debug middleware active in prod builds |
| **P1** | #22 — 7+ NotImplementedError functions | Raise at runtime if hit |
| **P1** | #21 — 9 skipped tests for missing features | Represent 9 abandoned features |
| **P1** | #19 — SAW_LAB learning pipeline off | Built and tested but never enabled |
| **P2** | #20 — RMOS v1→v2 migration | Old implementation still loadable; migration script incomplete |
| **P2** | #25 — 8+ experimental stubs | `_experimental/` half-built modules |
| **P2** | #26 — 4 frontend TODOs | Button handlers that do nothing |
| **P3** | #27 — abandoned blueprint-import service | No CI, no integration with main API |
| **P3** | #30 — Missing secrets docs | Contributors can't deploy |
| **P3** | #18 — Agentic spine stubs | `IMPLEMENTED = False` |
| **P4** | #31 — Orphaned data_registry schema | Dead table created on startup |
