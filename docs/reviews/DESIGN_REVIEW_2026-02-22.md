# Critical Systems Design Review: luthiers-toolbox

**Date:** 2026-02-22
**Reviewer:** GitHub Copilot (Claude Opus 4.6)
**Project:** Luthier's ToolBox (CNC Guitar Manufacturing Platform)
**Previous Review:** 2026-02-18 (Score: 4.2/10)
**Interim Evaluation:** 2026-02-22 (Score: 7.5/10, Claude Opus 4.5 — overstated)

> **Methodology:** All metrics independently verified via filesystem analysis, grep, and Python scripts against the live codebase. No self-reported numbers are taken at face value. Annotations reference the Feb 18 baseline and note deltas.

---

## Reviewer Assumptions (Unchanged)

1. **Target User**: Professional luthiers, guitar manufacturers, CNC operators needing parametric design + safe G-code generation
2. **Deployment Context**: Workshop/factory, Windows/Linux, connected to CNC machines (GRBL, Mach4, LinuxCNC, PathPilot, MASSO)
3. **Maturity Stage**: Pre-production (zero live CNC tests, zero external users)
4. **Criticality Level**: HIGH — unsafe G-code can damage machinery, waste materials ($200–2,000/billet), or cause injury
5. **Competitive Benchmark**: Fusion 360 CAM ($500/yr), VCarve Pro ($700), custom shop solutions

---

## Evaluation

### 1. Purpose Clarity
**Score: 7/10** *(was 5/10, Δ +2)*

**What improved:**
- `docs/PRODUCT_SCOPE.md` now exists and cleanly separates Core (DXF→G-code + RMOS safety) from Experimental (Smart Guitar IoT, Audio Analyzer)
- Router registry (`app/router_registry/`) provides a declarative manifest of 62 routers by category, replacing the chaotic 47-try/except-block `main.py`
- `main.py` reduced from 915+ LOC to **237 LOC** — clean, readable, well-sectioned

> **Annotation (Feb 18 → Feb 22):** The Feb 18 review flagged "671 routes — what's actually shipped?" The remediation plan reports reducing to 262 routes. Current `@router` decorator count is **672 endpoint decorators** across all files, but the router registry only loads **62 router modules**. The discrepancy suggests many endpoints exist in unloaded (experimental) routers — the registry effectively acts as a feature gate. This is a reasonable architecture but the 672 dormant endpoints should be pruned from source to avoid confusion.

**Remaining gaps:**
- No elevator pitch on README for cold visitors (still engineer-facing)
- 672 total endpoint decorators in source vs 62 loaded — dead endpoints should be deleted
- Smart Guitar / Audio Analyzer scope boundary still fuzzy in practice

---

### 2. User Fit
**Score: 6/10** *(was 4/10, Δ +2)*

**What improved:**
- **Quick Cut workflow implemented** (3-step wizard: Upload DXF → Pick machine → Download G-code)
- RMOS concepts documented in `docs/RMOS_CONCEPTS_GUIDE.md`
- Product scope now distinguishes Core vs Experimental features

**Remaining gaps:**
- No first-run wizard ("What machine do you have?")
- No user personas formally defined (Production shop / Custom builder / Hobbyist)
- Pro Mode vs Standard Mode toggle not implemented
- Tooltips explaining GREEN/YELLOW/RED risk levels to new users not verified

---

### 3. Usability
**Score: 5/10** *(was 3/10, Δ +2)*

**What improved:**
- **Vue god objects eliminated**: 0 components >800 LOC (was 25+). Largest is 680 LOC. Distribution:
  - `<200 LOC`: 215 components
  - `200–500 LOC`: 169 components
  - `500–800 LOC`: 42 components
  - `>800 LOC`: **0** ✅
- 20 composables extracted (including `useSavedViews`, `useUndoStack`, `useBulkDecision`)
- 26 Pinia stores in composition API / setup store syntax
- **Undo/History system implemented**: `useUndoStack` composable, `UndoHistoryPanel.vue`, `UndoRejectButton.vue`, undo in rosetteStore, undo spike detection in agenticDirectiveStore
- **Simulation/Preview system well-established**: `SimLab.vue` with G-code simulation (arcs, modal HUD, time scrub), `SimLabWorker.vue` (worker-based renderer), `CamSimMetricsPanel.vue` (metrics + report export), `CAMPreview.vue` ("Simulate & Preview" button), multiple preview drawers

> **Annotation:** The Feb 22 interim evaluation scored simulation as "MISSING" — this was incorrect. SimLab, SimLabWorker, and CamSimMetricsPanel are fully implemented. The evaluation searched for `simulation_preview` as a compound term rather than checking for actual simulation components. This was a search methodology error.

**Remaining gaps:**
- 42 Vue components in the 500–800 LOC range could benefit from further decomposition
- No Storybook or design system documentation
- No component library catalog for reuse discovery
- Error messages still unclear in some paths (broad exception handlers mask root causes)

---

### 4. Reliability
**Score: 5/10** *(was 4/10, Δ +1)*

**What improved:**
- `@safety_critical` decorator implemented in `app/safety/__init__.py`:
  - Logs `SAFETY_ENTER` / `SAFETY_EXIT` / `SAFETY_FAIL`
  - **Always re-raises** exceptions (fail-closed)
  - Tags functions with `_is_safety_critical = True` for introspection
  - Applied to 6+ critical modules (directional workflow, saw lab G-code emit, toolpath validation, saw/CAM adapters)
- Bare `except:` reduced from 97 to **0** in app code ✅
- Startup validation: `validate_startup()` runs on boot, fails fast if safety modules can't load
- RMOS strict startup mode: `RMOS_STRICT_STARTUP=1` (default) requires safety modules

**Still problematic — `except Exception` debt:**

| Module | `except Exception` Count | Severity |
|--------|-------------------------|----------|
| `app/rmos/` | **147** | CRITICAL — decision authority path |
| `app/saw_lab/` | **27** | HIGH — manufacturing operations |
| `app/cam/` | **14** | HIGH — toolpath generation |
| `app/calculators/` | **3** | MEDIUM — parameter calculations |
| Other `app/` | **260** | MEDIUM — non-safety paths |
| **App total** | **451** | |

> **Annotation (Feb 18 → Feb 22):** Feb 18 reported 1,622 `except Exception` across the full `services/api/` tree including tests. Current app-only count is **451** (excluding tests), with **191 in safety-critical modules**. The reduction from ~1,622 total is partly real cleanup and partly a measurement scope correction. The remediation plan marks Phase 1.2 (exception hardening) as "partial" — confirmed here. The 147 handlers in RMOS alone represent a genuine safety risk: if a feasibility check throws an unexpected exception caught by a broad handler, a RED operation could be silently downgraded to GREEN.

**Remaining gaps:**
- 191 `except Exception` in safety paths — **this is the biggest reliability risk in the entire system**
- No mandatory G-code simulation gate before export (SimLab exists but isn't gated)
- Test coverage not independently measured (no `pytest --cov` run available)
- Test count: 85 test files, 746 test functions (API); 24 test files, 361 test cases (frontend)

---

### 5. Manufacturability / Maintainability
**Score: 6/10** *(was 3/10, Δ +3)*

**What improved:**
- **Dead code purge complete**: Only 2 `.bak` files remain (was 200+), no `__ARCHIVE__` directories
- **`main.py` decomposed**: 915+ LOC → **237 LOC** with declarative router registry
- **Router registry architecture**: `app/router_registry/` package with `models.py`, `manifest.py`, `loader.py`, `health.py` — clean separation of concerns
- **Python god objects nearly eliminated**: Only 4 files >500 LOC in `app/`:
  - `routers/pipeline_router.py` (630)
  - `generators/bezier_body.py` (595)
  - `saw_lab/toolpaths_validate_service.py` (568)
  - `routers/cam_post_v155_router.py` (521)
- **Vue god objects fully eliminated**: 0 files >800 LOC (was 25+)
- **Composable extraction**: 20 `use*.ts` composables, 26 Pinia stores, 31 SDK files
- 8 architectural fence profiles defined in `FENCE_REGISTRY.json`
- Endpoint governance middleware tracks legacy/shadow endpoints
- Route analytics middleware captures usage metrics

**Remaining gaps:**
- 4 Python files still exceed 500 LOC (the god-object target was "0 files >500 lines")
- 1,101 Python files / 186,470 LOC in `services/api` — significant surface area
- 933 frontend files / 165,662 LOC
- No architecture diagram (referenced but not found)
- Test `conftest.py` at 658 LOC is complex (documented but could use decomposition)

---

### 6. Cost
**Score: 6/10** *(was 5/10, Δ +1)*

**What improved:**
- Router registry reduces cognitive load for new contributors
- Route analytics middleware enables data-driven route culling decisions
- Feature flags gate experimental modules at runtime:
  - `RMOS_RUNS_V2_ENABLED` (controls v1/v2 implementation, default `true`)
  - `SAW_LAB_LEARNING_HOOK_ENABLED`
  - `SAW_LAB_EXECUTION_METRICS_AUTOROLLUP_ENABLED`
  - `SAW_LAB_METRICS_ROLLUP_HOOK_ENABLED`
  - `SAW_LAB_APPLY_ACCEPTED_OVERRIDES`
  - `RMOS_STRICT_STARTUP`

**Remaining gaps:**
- 672 endpoint decorators in source (only 62 routers loaded) — dead code maintenance burden
- No BOM or deployment cost documentation
- Route analytics middleware still has a TODO: "Remove before production or gate behind ENABLE_ROUTE_ANALYTICS env var"

---

### 7. Safety
**Score: 6/10** *(was 5/10, Δ +1)*

**What improved:**
- **`@safety_critical` decorator fully implemented** and in active use:
  ```python
  @safety_critical  # Logs enter/exit/fail, always re-raises
  def validate_toolpath(plan: CutPlan) -> FeasibilityResult:
      ...
  ```
- Bare `except:` blocks: 97 → **0** in app code ✅
- Startup safety validation fails fast if critical modules can't load
- 22+ feasibility rules (F001–F029) with RED/YELLOW/GREEN bucketing
- Immutable audit trail for override decisions

**Critical remaining risk:**
- **147 `except Exception` handlers in RMOS** — the decision authority module. The `@safety_critical` decorator is applied to ~6 functions but RMOS has hundreds of functions. A feasibility check that throws an unexpected error caught by a broad handler could return GREEN for a RED operation.
- SimLab simulation exists but is **not gated** — operators can skip it and export G-code directly
- The `@safety_critical` decorator needs to be systematically applied to all functions in the feasibility evaluation chain, not just the 6 currently decorated

> **Annotation:** This is the most important gap in the entire system. The RMOS architecture design is excellent — but 147 broad exception handlers in the implementation can silently undermine it. A single `except Exception: return FeasibilityResult(status="GREEN")` anywhere in the chain defeats the entire safety architecture. Each of the 147 handlers needs manual review to determine if it's in a safety-critical path.

---

### 8. Scalability
**Score: 5/10** *(was 5/10, Δ 0)*

**Unchanged:**
- Appropriate for pre-production single-user stage
- SQLite local + optional PostgreSQL
- Docker deployment ready (docker-compose with API + client + nginx)
- Railway deployment configured

**Same gaps:**
- Multi-user coordination not implemented
- Batch processing for production QC not available
- 10+ concurrent users untested
- No horizontal scaling strategy documented

---

### 9. Aesthetics
**Score: 5/10** *(was 4/10, Δ +1)*

**What improved:**
- Vue component decomposition: cleaner, more focused components
- Only 2 `.bak` files remain in entire repo (was 200+)
- Code organization significantly improved with router registry, composables, stores

**Remaining gaps:**
- No Storybook or design system documentation
- No component library or visual catalog
- Inconsistent naming conventions still present (snake_case vs camelCase in presets)
- No design tokens or theme system documentation

---

## Summary Scorecard

| Category | Feb 18 | Feb 22 | Delta | Priority Fix |
|----------|--------|--------|-------|--------------|
| Purpose Clarity | 5/10 | **7/10** | +2 | Prune 672 dormant endpoints from source |
| User Fit | 4/10 | **6/10** | +2 | First-run wizard, user personas |
| Usability | 3/10 | **5/10** | +2 | Further Vue decomposition (42 files 500–800) |
| Reliability | 4/10 | **5/10** | +1 | **Exception hardening in RMOS (P0)** |
| Maintainability | 3/10 | **6/10** | +3 | Finish 4 remaining Python god objects |
| Cost | 5/10 | **6/10** | +1 | Delete unloaded router code |
| Safety | 5/10 | **6/10** | +1 | **Apply @safety_critical to all feasibility functions** |
| Scalability | 5/10 | **5/10** | 0 | Document scaling limits |
| Aesthetics | 4/10 | **5/10** | +1 | Design system / Storybook |

**Overall: 5.7/10** *(was 4.2/10, Δ +1.5)*

> **Annotation on scoring discrepancy:** The Feb 22 interim evaluation by Claude Opus 4.5 scored this at 7.5/10. This review arrives at **5.7/10**. The 1.8-point gap is attributable to:
> 1. The interim evaluation incorrectly scored simulation preview as "MISSING" (it exists) but then didn't penalize adequately for the real gap (191 `except Exception` in safety paths)
> 2. The interim evaluation used a holistic 1-score rubric rather than the 9-dimension decomposition, which tends to overweight visible improvements (Vue decomposition, dead code) and underweight invisible risks (exception handling in safety paths)
> 3. The 7.5 score would require most dimensions at 7+, which the safety and reliability dimensions clearly don't reach

---

## Top 5 Critical Actions

### 1. RMOS Exception Hardening (P0 — SAFETY)
**Problem:** 147 `except Exception` handlers in `app/rmos/` — the safety decision authority module
**Risk:** A feasibility check throwing an unexpected error could be silently caught, returning GREEN for a RED operation → unsafe G-code exported → machine damage or injury
**Fix:**
1. Audit all 147 handlers: classify as (a) can narrow to specific exception, (b) needs `@safety_critical`, (c) is genuinely correct
2. Apply `@safety_critical` decorator to all functions in the feasibility evaluation chain
3. Add CI gate: `grep -r "except Exception" app/rmos/ | wc -l` must equal 0 (or explicit exemption list)
**Effort:** 2–3 days
**Impact:** Safety score 6→8, Reliability score 5→7

### 2. SAW Lab + CAM Exception Hardening (P0 — SAFETY)
**Problem:** 27 handlers in `saw_lab/`, 14 in `cam/`, 3 in `calculators/`
**Risk:** Same class as #1 but in manufacturing execution and toolpath generation
**Fix:** Same audit process as #1
**Effort:** 1–2 days
**Impact:** Completes safety-path hardening

### 3. Mandatory Simulation Gate Before Export (P1 — SAFETY)
**Problem:** SimLab exists with full toolpath simulation capabilities, but operators can bypass it and export G-code directly
**Fix:**
1. Add `simulation_passed: bool` field to export request model
2. Require simulation completion (or explicit override with audit log) before G-code download
3. Store simulation result hash in export artifact metadata
**Effort:** 1 day
**Impact:** Safety score +1, closes the "simulation exists but isn't enforced" gap

### 4. Prune Dormant Endpoints (P1 — MAINTAINABILITY)
**Problem:** 672 endpoint decorators in source but only 62 routers loaded via registry. ~610 dormant endpoints create confusion and maintenance burden
**Fix:**
1. Use route analytics data to identify never-hit endpoints
2. Archive (git tag) then delete router files not in `ROUTER_MANIFEST`
3. Target: endpoint count ≈ route count in registry
**Effort:** 2–3 days
**Impact:** Purpose +1, Cost +1, Maintainability +1

### 5. Finish Python God Object Decomposition (P2)
**Problem:** 4 files still >500 LOC:
- `pipeline_router.py` (630)
- `bezier_body.py` (595)
- `toolpaths_validate_service.py` (568)
- `cam_post_v155_router.py` (521)
**Fix:** Apply same decomposition pattern used for main.py and Vue components
**Effort:** 2 days
**Impact:** Maintainability +0.5

---

## Projected Remediation Impact

| Dimension | Current | Post-Fix (Actions 1–5) | Delta |
|-----------|---------|----------------------|-------|
| Purpose | 7/10 | 8/10 | +1 |
| User Fit | 6/10 | 6/10 | 0 |
| Usability | 5/10 | 6/10 | +1 |
| Reliability | 5/10 | **7/10** | **+2** |
| Maintainability | 6/10 | **7/10** | **+1** |
| Cost | 6/10 | 7/10 | +1 |
| **Safety** | 6/10 | **8/10** | **+2** |
| Scalability | 5/10 | 5/10 | 0 |
| Aesthetics | 5/10 | 5/10 | 0 |
| **Overall** | **5.7/10** | **6.6/10** | **+0.9** |

---

## Key Metrics (Verified 2026-02-22)

| Metric | Feb 18 | Feb 22 | Delta | Notes |
|--------|--------|--------|-------|-------|
| Backend Python files | 987 | **1,101** | +114 | excl. venv/pycache |
| Backend Python LOC | 51,649 | **186,470** | +134,821 | Different measurement scope* |
| Frontend Vue files | — | **426** | — | |
| Frontend Vue LOC | — | **101,241** | — | |
| Frontend TS files | — | **507** | — | |
| Frontend TS LOC | — | **64,421** | — | |
| Frontend total LOC | 152,076 | **165,662** | +13,586 | |
| `main.py` LOC | 1,500+ | **237** | **−84%** | ✅ Massive improvement |
| `main.py` try/except blocks | 47 | **0** | **−47** | ✅ Eliminated |
| Router manifest entries | — | **62** | — | Declarative registry |
| Total endpoint decorators | 671 | **672** | +1 | Most unloaded |
| API test files | 95 | **85** | −10 | Consolidation |
| API test functions | — | **746** | — | |
| Frontend test files | — | **24** | — | |
| Frontend test cases | — | **361** | — | |
| `except Exception` (app/) | — | **451** | — | Verified, excl. tests |
| `except Exception` (safety) | 278 | **191** | **−87** | Partial improvement |
| Bare `except:` (app/) | 6–97** | **0** | **−97** | ✅ Eliminated |
| Python >500 LOC (app/) | 30+ | **4** | **−87%** | ✅ Near target |
| Vue >800 LOC | 25+ | **0** | **−100%** | ✅ Fully resolved |
| Vue 500–800 LOC | — | **42** | — | Decomposition candidates |
| `.bak` files | 200+ | **2** | **−99%** | ✅ Nearly eliminated |
| `__ARCHIVE__` directories | multiple | **0** | — | ✅ Eliminated |
| Documentation files | 54 | **61** | +7 | New: PRODUCT_SCOPE, ARCHITECTURE, etc. |
| `conftest.py` LOC | 659 | **658** | −1 | Unchanged |
| Composables (`use*.ts`) | — | **20** | — | Extracted from god components |
| Pinia stores | — | **26** | — | Composition API style |
| SDK endpoint files | — | **31** | — | |
| Fence profiles | — | **8** | — | Architectural boundaries |
| Feature flags (env-gated) | 0 | **6+** | +6 | RMOS_RUNS_V2, SAW_LAB_*, etc. |
| `@safety_critical` usage | 0 | **6+ functions** | +6 | Decorator exists and is active |

\* *Feb 18 LOC count excluded test files; Feb 22 includes all `.py` under `services/api/` excluding venv. The per-file counts are not directly comparable.*

\** *Feb 18 review reported 6 bare excepts; REMEDIATION_PLAN reports 97. The discrepancy suggests Feb 18 was counting only `app/` while 97 included tests.*

---

## Remediation Plan Status (Cross-Referenced)

| Phase | REMEDIATION_PLAN Status | Verified |
|-------|------------------------|----------|
| Phase 0 — Dead Code Purge | COMPLETE | ✅ 2 `.bak` remain, 0 `__ARCHIVE__` |
| Phase 1.1 — Bare except elimination | COMPLETE | ✅ 0 bare `except:` in app/ |
| Phase 1.2 — `except Exception` hardening | **PARTIAL** | ⚠️ 451 remain (191 in safety paths) |
| Phase 1.3 — `@safety_critical` decorator | COMPLETE | ✅ Implemented, applied to 6+ functions |
| Phase 2 — API Surface Reduction | COMPLETE | ⚠️ 62 routers loaded, but 672 decorators in source |
| Phase 3 — God-Object Decomposition | COMPLETE | ⚠️ 4 Python files still >500 LOC |
| Phase 4 — Documentation Triage | COMPLETE | ✅ 61 docs, key guides created |
| Phase 5 — Quick Cut Mode | COMPLETE | ✅ 3-step wizard implemented |
| Phase 6 — Health/Observability | COMPLETE | ✅ `/api/health` + router health |

> **Annotation:** Phases 3 and 2 are marked COMPLETE in the plan but have residual items. Phase 3 has 4 files >500 LOC (target was 0). Phase 2 reports 262 routes but 672 endpoint decorators exist in source. These should be reclassified as "COMPLETE with exceptions" or the targets adjusted.

---

## Architecture Highlights

### Router Registry (New since Feb 18)
```
main.py (237 LOC)
  └── router_registry/
        ├── models.py      # RouterSpec dataclass
        ├── manifest.py    # 62 routers, declarative, categorized
        ├── loader.py      # load_all_routers() with error handling
        └── health.py      # get_router_health() for /api/health
```

### Safety Architecture (Improved)
```
Request → Feasibility Engine → Decision (GREEN/YELLOW/RED) → Gated Export
                ↓                    ↓
         22+ Safety Rules    @safety_critical decorator
         Override Audit       (6+ functions decorated)
         Explanation Gen.     Logs ENTER/EXIT/FAIL
                              Always re-raises (fail-closed)
                              
⚠️ GAP: 147 except Exception handlers in RMOS can bypass this chain
```

### Frontend Architecture (Improved)
```
426 Vue components (0 >800 LOC) ✅
 ├── 20 composables (useUndoStack, useSavedViews, useBulkDecision, ...)
 ├── 26 Pinia stores (composition API)
 ├── 31 SDK endpoint files (4 namespaces: cam, rmos, operations, art)
 └── SimLab simulation engine (SimLab.vue + SimLabWorker.vue + metrics)
```

---

## Features Inventory

| Feature | Status | Notes |
|---------|--------|-------|
| DXF → G-code pipeline | ✅ Production | Multi-post: GRBL, Mach4, LinuxCNC, PathPilot, MASSO |
| RMOS decision authority | ✅ Production | 22+ rules, override audit, fail-closed on decorated functions |
| Feasibility engine | ✅ Production | F001–F029, RED/YELLOW/GREEN bucketing |
| Parametric calculators | ✅ Production | Fret, scale length, chipload, neck taper |
| Saw Lab | ✅ Production | Batch sawing, cut plans, G-code linting |
| Quick Cut wizard | ✅ New | 3-step DXF → machine → G-code |
| SimLab simulation | ✅ Exists | G-code sim with arcs, time scrub, metrics — **not gated** |
| Undo/History | ✅ Exists | useUndoStack composable, UndoHistoryPanel, store-level undo |
| Rosette Designer | ✅ Exists | With undo/redo stack |
| Art Studio | ✅ Exists | Bracing, relief, inlay, headstock design |
| Tool library | ✅ Exists | Backend implementation |
| Cost estimation | ✅ Exists | Backend implementation |
| Feature flags | ✅ Exists | 6+ env-gated flags |
| `@safety_critical` | ✅ Exists | Implemented, applied to 6+ functions |
| Endpoint governance | ✅ Exists | Middleware tracking legacy/shadow endpoints |
| Route analytics | ✅ Exists | Usage metrics for consolidation decisions |
| User material library | ❌ Missing | Hardcoded species data, not user-extensible |
| Mandatory sim gate | ❌ Missing | SimLab exists but export isn't gated on it |
| First-run wizard | ❌ Missing | No "What machine do you have?" onboarding |
| Storybook | ❌ Missing | No component documentation system |
| i18n | ❌ Missing | No internationalization |
| Offline/PWA mode | ⚠️ Partial | Service worker references found, not verified as functional |
| Multi-user | ❌ Missing | Single-user only |

---

## Conclusion

**Luthier's ToolBox has made significant, verifiable progress since Feb 18.** The main.py decomposition (915→237 LOC), Vue god object elimination (25→0 files >800 LOC), dead code purge (200→2 `.bak` files), and router registry architecture are genuine improvements backed by measurable data.

**However, the system has one critical safety gap that caps the score:** 191 `except Exception` handlers in safety-critical modules (147 in RMOS alone). The `@safety_critical` decorator exists and works correctly — but it's applied to only ~6 functions while RMOS contains hundreds. Until the exception handling in the feasibility evaluation chain is hardened, the safety architecture's design excellence is undermined by its implementation.

**The corrected score is 5.7/10** — a meaningful +1.5 improvement from 4.2, with a clear path to 6.6 via actions #1–5. The interim 7.5 evaluation was overstated by ~1.8 points due to measurement errors (simulation marked missing when it exists) and insufficient weighting of the exception debt.

**Priority sequence:**
1. **Week 1:** RMOS exception audit + hardening (147 handlers) — highest safety impact
2. **Week 1:** SAW Lab + CAM exception hardening (44 handlers) — completes safety paths
3. **Week 2:** Mandatory simulation gate before export — closes workflow gap
4. **Week 2–3:** Prune 610+ dormant endpoint decorators — reduces confusion
5. **Week 3:** Finish 4 remaining Python god objects — completes Phase 3

**With disciplined execution, the project can reach 6.6/10 within 3 weeks** — crossing the threshold for controlled production deployment with monitored rollout.

---

*Review conducted with independently verified metrics. All file counts, LOC measurements, and exception counts were generated via filesystem analysis against the live codebase, not self-reported documentation.*
