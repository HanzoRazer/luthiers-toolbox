# The Production Shop — Consolidated Gap Analysis

> **Generated:** 2026-03-10
> **Goal:** Narrow down everything until we're forced to get in the Shop and make it happen
> **Score Progress:** 4.7/10 → 6.68/10 → Target 7.0+

---
---

## 🔖 SYSTEM RESET BOOKMARK (2026-03-11)

**Last Session:** GAP_ANALYSIS Remediation Sprint  
**Last Commit:** `c9ac19ec` fix(saw-lab): restore POST /toolpaths/from-decision endpoint (P1-SAW)  
**Branch:** main (pushed to origin)

### Completed This Sprint

| Gap ID | Description | Commit |
|--------|-------------|--------|
| SAW-LAB-GAP-01 | Duplicate artifact helpers across 7 files | `6dd8280a` |
| RMOS-GAP-01 | Duplicate artifact helpers in runs_v2/ (3 files) | `528f577d` |
| CORRUPT-GAP-01 | 8 corrupted Python files in app/services/ | `8f530691` |
| **P1-SAW** | **DECISION → TOOLPATHS pipeline break — restored endpoint + 8 schemas** | `c9ac19ec` |

### Test Status
```
2390 passed, 28 failed (pre-existing), 37 skipped, 19 xfailed
```

### Resume Instructions
```bash
cd "C:/Users/thepr/Downloads/luthiers-toolbox"
git pull origin main
cat docs/GAP_ANALYSIS_MASTER.md | head -100
cd services/api && .venv/Scripts/python.exe -m pytest tests/ --tb=no -q
```

### Next Steps
1. Continue scanning `docs/GAP_ANALYSIS_MASTER.md` for infrastructure gaps
2. Priority: Code duplication, DRY violations, orphaned modules
3. Reference `docs/AGENT_SESSION_BOOKMARK.md` for detailed session state


## P0 — Critical System Blockers

These must be fixed before anything else works in production.

### 1. Frontend Build ✅ WORKING (2026-03-10)
| Issue | File | Status |
|-------|------|--------|
| TypeScript errors blocking build | `instrumentApi.ts` | ✅ **FIXED** - Added "PARTIAL" to status union type |
| Tailwind classes used without Tailwind installed | `packages/client/*` | ⚠️ Build works but CSS may be missing |

**Build verified:** `npm run build` completes in ~16s with 1 warning (large chunk).

### 2. Supabase Auth: 70% Coded, ~40% Operational
| Gap | File | Status |
|-----|------|--------|
| Auth router not registered | `router_registry/manifest.py` | ✅ **FIXED** (already in manifest) |
| `initAuthGuard` not applied | `packages/client/src/router/index.ts` | ✅ **FIXED** (2026-03-10) |
| `requireAuth` not used on any route | `packages/client/src/router/index.ts` | ✅ **FIXED** (guards imported) |
| `requireTier` / `requireFeature` unused | Router + backend routes | ✅ **FIXED** (`/business/estimator` now tier-gated) |
| `AUTH_MODE` defaults to `header` | `.env` / production env | ❌ Set `AUTH_MODE=supabase` |
| Auth store uses raw `fetch()` | `stores/useAuthStore.ts` | ❌ Refactor to use SDK helpers |
| Alembic migration never run | Supabase database | ❌ Run `alembic upgrade head` |
| RLS policies not executed | Supabase SQL Editor | ❌ Execute policies from `SUPABASE_AUTH_SETUP.md` |
| OAuth providers not configured | Supabase dashboard | ❌ Configure Google/GitHub OAuth |

### 3. Singleton Stores Block Horizontal Scaling
| Store | File | Issue |
|-------|------|-------|
| `art_jobs` | `data/art_jobs.json` | File-based, single-process |
| `art_presets` | `data/art_presets.json` | File-based, single-process |
| RMOS run artifacts | `app/rmos/runs_v2/store.py` | Local filesystem |
| Job log | `app/rmos/pipeline/feedback/job_log.py` | Local JSON files |

**Fix:** Migrate to Supabase/PostgreSQL or Redis for multi-instance deployments.

### 4. CNC Safety: Fail-Open Design
| Issue | Impact | Status |
|-------|--------|--------|
| `@safety_critical` decorator coverage | Was ~20 sites | ✅ **+8 sites added** (2026-03-10) |
| No mandatory pre-flight validation | Unsafe G-code could execute | ❌ Add validation gate |
| Emergency stop not wired to UI | Can't halt runaway operations | ❌ Wire e-stop button |

**Safety decorators added to:**
- `export_router.py`: `/export_gcode`, `/export_gcode_governed`
- `retract_router.py`: `/gcode`, `/gcode_governed`, `/gcode/download`, `/gcode/download_governed`
- `drill_router.py`: `/gcode`
- `pattern_router.py`: `/gcode`

---

## P1 — High Priority Wiring Gaps

### Missing Converters (Block Art → CAM Pipelines)
| Converter | Status | Impact |
|-----------|--------|--------|
| SVG → DXF | **Missing** | Rosette designs can't go to CNC |
| Inlay design → G-code | **Missing** | Inlay patterns stuck in preview |
| Relief toolpath → Post-processor | **Partial** | Relief carving incomplete |

### Stub Endpoints Remaining
- **Total stubs:** 73 → 23 (68% reduction achieved)
- **HIGH priority remaining:** 13 endpoints
- **Key missing implementations:**
  - `/api/cam/adaptive/generate` — needs actual adaptive clearing algorithm
  - `/api/cam/vcarve/generate` — needs V-carve toolpath generator
  - `/api/rmos/execute` — needs machine control integration

### SDK Convention Violations
| File | Issue |
|------|-------|
| `useAuthStore.ts` | Uses `fetch()` instead of SDK |
| Several views | Direct API calls instead of SDK wrappers |

---

## P2 — Remediation Plan Status

### From REMEDIATION_PLAN.md
| Item | Status |
|------|--------|
| TypeScript strict mode | ✅ Enabled |
| ESLint configuration | ✅ Fixed |
| Import path aliases | ✅ Working |
| Pinia store migration | ⚠️ Partial |
| Router guards | ❌ Not wired |
| Error boundaries | ❌ Not implemented |

### From SCORE_7_PLAN.md
| Category | Before | After | Target |
|----------|--------|-------|--------|
| Code Quality | 4.2 | 6.1 | 7.0 |
| Test Coverage | 3.8 | 5.9 | 7.0 |
| Documentation | 5.1 | 7.2 | 7.0 ✅ |
| Architecture | 4.5 | 6.8 | 7.0 |
| **Overall** | **4.7** | **6.68** | **7.0** |

---

## P3 — Stub Endpoint Status

### HIGH Priority Stubs (Must Implement)
1. `/api/cam/adaptive/generate`
2. `/api/cam/vcarve/generate`
3. `/api/cam/drilling/pattern`
4. `/api/cam/relief/generate`
5. `/api/rmos/execute`
6. `/api/rmos/status`
7. `/api/instruments/register`
8. `/api/instruments/{id}/build-log`
9. `/api/presets/export`
10. `/api/presets/import`
11. `/api/materials/wood-species`
12. `/api/tools/library`
13. `/api/machines/profiles`

### MEDIUM Priority Stubs (Should Implement)
- 10 additional endpoints in monitoring, analytics, export

---

## P4 — UI Redesign Status (VCarve/Fusion 360 Style)

### From BUILD_CHRONICLE_UI_REDESIGN.md

| Phase | Description | Status |
|-------|-------------|--------|
| Phase 1 | Design system tokens | ✅ Complete |
| Phase 2 | Core components (CadInput, CadCheckbox) | ✅ Complete |
| Phase 3 | Layout components | ✅ Complete |
| Phase 4 | Feature-specific components | ⚠️ Partial |
| Phase 5 | View migration (5 views) | ⚠️ 1/5 migrated |

**Remaining Views to Migrate:**
1. `DxfToGcodeView.vue` — ❌ Not started
2. `PipelineLabView.vue` — ❌ Not started
3. `BlueprintLabView.vue` — ❌ Not started
4. `RosetteEditorView.vue` — ❌ Not started
5. `ToolParametersEditor.vue` — ✅ Migrated

---

## LOW PRIORITY — Instrument Build Gaps

> Per user direction: These highlight real issues but will be addressed when system issues are wired correctly.

### 1959 Les Paul (Most Complete)
- 452,840 lines G-code generated
- **Gaps:** Binding channel depth, fret slot width tolerance

### Smart Guitar v1
- 11,967 lines G-code generated
- **Gaps:** IoT cavity routing, sensor placement

### Stratocaster Neck (5 gaps: NECK-01 through NECK-05)
- Fret slot depth calculation
- Truss rod channel width
- Heel pocket fit tolerance
- Nut slot positioning
- Fretboard radius consistency

### 24-Fret Stratocaster (9 gaps: GAP-01 through GAP-09)
- Extended fretboard geometry
- Neck pocket modification
- Pickup routing adjustment
- Bridge placement compensation

### J45 Vine of Life (12 gaps: VINE-01 through VINE-12)
- Rosette inlay depth
- Binding channel toolpath
- Soundhole reinforcement
- Bracing pattern alignment

---

## WAITING — DXF File Issues

> Per user direction: These must be solved in AutoCAD/Fusion 360 workspace, not in code.

| Issue | Source File | Resolution |
|-------|-------------|------------|
| Unclosed polylines | Various `.dxf` | Fix in CAD software |
| Duplicate entities | Guitar body outlines | Clean in CAD software |
| Layer naming inconsistencies | All instrument DXFs | Standardize in CAD software |
| Unit mismatches (inch vs mm) | Imported files | Verify units in CAD software |
| Spline approximation errors | Complex curves | Re-export from CAD software |

---

## Recommended Execution Sequence

### Week 1: Get It Building
1. ~~Fix TypeScript errors (run `npm run type-check`)~~ ✅ DONE
2. Install Tailwind OR replace Tailwind classes (build works, CSS may be partial)
3. ~~Wire auth router in `main.py`~~ ✅ Already in router_registry
4. ~~Apply `initAuthGuard` in router~~ ✅ DONE
5. Run Alembic migration ← **NEXT**

### Week 2: Wire Safety & Core Paths
1. Add `@safety_critical` to remaining CNC endpoints
2. Implement emergency stop endpoint
3. Implement top 5 stub endpoints
4. Wire SVG → DXF converter

### Week 3: Complete UI Migration
1. Migrate remaining 4 views to CAD theme
2. Fix SDK convention violations
3. Implement remaining HIGH priority stubs

### Week 4: Production Hardening
1. Migrate singleton stores to database
2. Configure OAuth providers
3. Set up RLS policies
4. Deploy to staging environment

---

## Files to Touch First (Highest Impact)

| File | Changes | Status |
|------|---------|--------|
| `services/api/app/router_registry/manifest.py` | Auth router already registered | ✅ DONE |
| `packages/client/src/router/index.ts` | Add `initAuthGuard`, `requireAuth`, `requireTier` | ✅ DONE (2026-03-10) |
| `packages/client/src/services/instrumentApi.ts` | Fix TypeScript status union type | ✅ DONE |
| `services/api/app/rmos/runs_v2/store.py` | Add database adapter | ❌ TODO |
| `packages/client/src/stores/useAuthStore.ts` | Use SDK instead of fetch | ❌ TODO |
| `services/api/app/cam/safety.py` | Add `@safety_critical` decorator calls | ❌ TODO |

---

## Summary

| Category | Status | Blocking Production? |
|----------|--------|---------------------|
| Frontend Build | ✅ Working | **NO** (fixed 2026-03-10) |
| Auth System | 70% coded, ~40% wired | **Partial** (guards wired, need migration) |
| CNC Safety | Fail-open | **YES** |
| Singleton Stores | Local files | **YES** (scaling) |
| Stub Endpoints | 23 remaining | **YES** (13 HIGH) |
| UI Migration | 1/5 views | No |
| Instrument Builds | Gaps documented | No (LOW PRIORITY) |
| DXF Files | Need CAD fixes | No (WAITING) |

**Bottom line:** ~~Fix the frontend build~~, ~~wire auth guards~~, add safety decorators, and migrate stores. Then we're forced into the Shop.

---

## P1-SAW — CNC Saw Lab Pipeline Break: DECISION → EXECUTE

> **Discovered:** 2026-03-10 via live API integration test (parquet herringbone rosette cut job)
> **Severity:** P1 — Blocks all Saw Lab batch production jobs from reaching machine execution
> **Status:** ✅ **FIXED** (2026-03-11) — Commit `c9ac19ec`

### What Was Tested

We ran a full 6-stage Saw Lab pipeline using a real job: cutting the wood pieces for a parquet herringbone rosette (596 ebony tiles, 602 koa tiles, 1 maple disc, 1 green spruce strip).

**Pipeline stages:**
```
SPEC ──→ PLAN ──→ DECISION ──→ TOOLPATHS ──→ EXECUTE ──→ EXPORT/FEEDBACK
  ✅        ✅        ✅           ✅ FIXED       ✅ UNBLOCKED  ✅
```

**API calls that succeeded:**
| Stage | Endpoint | Artifact ID |
|-------|----------|-------------|
| SPEC | `POST /api/saw/batch/spec` | `saw_batch_spec_3dc1f3fdbdf8` |
| PLAN | `POST /api/saw/batch/plan` | `saw_batch_plan_608853bc52bc` |
| DECISION | `POST /api/saw/batch/approve` | `saw_batch_decision_8307d7fa40dd` |

**What broke:** After approval, querying the decision returned `batch_toolpaths_artifact_id: null`. No toolpaths were generated, and the execution stage requires them.

### Root Cause Analysis

The pipeline has a **severed link between stages 3 (DECISION) and 4 (EXECUTE)**. The code to generate toolpaths from a decision *exists* but has no HTTP endpoint wiring it into the batch workflow.

#### The Approval Endpoint Does Not Trigger Toolpath Generation

[batch_router.py](services/api/app/saw_lab/batch_router.py) — The `/approve` endpoint:
1. Reads the plan artifact
2. Creates a `saw_batch_decision` artifact (approved_by, reason, setup_order, op_order)
3. Returns `BatchApproveResponse` with **only** `batch_decision_artifact_id`
4. **STOPS** — no call to any toolpath generation service

[batch_router_schemas.py](services/api/app/saw_lab/batch_router_schemas.py) — The response schema:
```python
class BatchApproveResponse(BaseModel):
    batch_decision_artifact_id: str    # ← This is ALL it returns
```
There is no `batch_toolpaths_artifact_id` field on the approval response.

#### The Toolpath Generation Service Exists But Is Orphaned

**Two copies exist** (neither is called from the batch workflow):

| File | Function | Called By |
|------|----------|-----------|
| [saw_lab/saw_lab_toolpaths_from_decision_service.py](services/api/app/saw_lab/saw_lab_toolpaths_from_decision_service.py) | `generate_toolpaths_from_decision(batch_decision_artifact_id=...)` | **Nothing** (orphaned) |
| [services/saw_lab_toolpaths_from_decision_service.py](services/api/app/services/saw_lab_toolpaths_from_decision_service.py) | `generate_toolpaths_from_decision(decision_artifact_id=...)` | `compare_router.py` only |

The `app/saw_lab/` version (lines 85–232) is the **batch-aware** implementation:
- Takes a `batch_decision_artifact_id`
- Loads decision → plan → spec artifacts
- Builds base context from spec+plan
- Applies decision tuning patches via `apply_decision_to_context()`
- Calls `plan_saw_toolpaths_for_design()` from [saw_lab_run_service.py](services/api/app/saw_lab_run_service.py)
- Persists a `saw_batch_toolpaths` artifact (OK/ERROR) parented to the decision
- Returns `batch_toolpaths_artifact_id` + preview

But **no router endpoint calls this function**. It was written, then never wired.

The `app/services/` version is a separate implementation that only handles `saw_compare_decision` artifacts (the feasibility comparison workflow, not batch production). It is used by [compare_router.py](services/api/app/saw_lab/compare_router.py) at line 123.

#### The Schemas Were Deleted As "Dead Code"

[batch_router_schemas.py](services/api/app/saw_lab/batch_router_schemas.py) lines 92–95 contains this comment:
```python
# NOTE: Removed 2026-02-26 (dead code cleanup):
# - BatchPlanChooseRequest, BatchPlanChooseResponse (no endpoint wired)
# - BatchToolpathsFromDecisionRequest/Response (not imported)
# - BatchToolpathsRequest, BatchOpResult, BatchToolpathsResponse (not imported)
```

The request/response schemas for the toolpath generation endpoint were **deleted on 2026-02-26** because they weren't imported by any router. The schemas were "dead code" only because the endpoint that needed them was never written — a classic chicken-and-egg gap.

#### The Execution Stage Assumes Toolpaths Already Exist

[execution_lifecycle_router.py](services/api/app/saw_lab/execution_lifecycle_router.py) — `POST /api/saw/batch/execution/start-from-toolpaths`:
```python
class ExecutionStartFromToolpathsRequest(BaseModel):
    session_id: str
    batch_label: str
    toolpaths_artifact_id: str      # ← REQUIRED, not Optional
    decision_artifact_id: Optional[str] = None
```
This expects a `toolpaths_artifact_id` that **cannot be produced** by the current batch workflow.

#### The Toolpath Query/Validate/Lint Endpoints Are Read-Only

[toolpaths_router.py](services/api/app/saw_lab/toolpaths_router.py) has:
- `GET /toolpaths/latest` — fetch existing toolpaths
- `GET /toolpaths/latest-by-batch` — fetch by batch label
- `POST /toolpaths/validate` — validate existing toolpaths
- `POST /toolpaths/lint` — lint existing toolpaths

**No POST endpoint generates toolpaths.** All assume artifacts already exist.

#### The Compare Router Has a Working (But Different) Path

[compare_router.py](services/api/app/saw_lab/compare_router.py) line 117:
```python
@router.post("/compare/toolpaths")
def toolpaths_from_decision(req: SawDecisionToolpathsRequest):
    out = generate_toolpaths_from_decision(decision_artifact_id=req.decision_artifact_id)
    return SawDecisionToolpathsResponse(**out)
```
This works, but it uses `saw_compare_decision` artifacts (feasibility workflow), NOT `saw_batch_decision` artifacts (production workflow). Different artifact kinds, different service files.

### Downstream Toolpath Generation Chain

When the endpoint gap is fixed, the generation chain is:

```
[New Endpoint] 
    → saw_lab/saw_lab_toolpaths_from_decision_service.generate_toolpaths_from_decision()
        → decision_apply_service.apply_decision_to_context()     # tuning patches
        → saw_lab_run_service.plan_saw_toolpaths_for_design()    # segment planning
            → saw_lab/path_planner.build_segments_from_plan()    # segment adapter
            → saw_lab/toolpath_builder.SawToolpathBuilder.build()# toolpath math
        → store.persist artifact (kind="saw_batch_toolpaths")    # traceability
```

**Key files in the generation chain:**

| File | Role |
|------|------|
| [saw_lab/saw_lab_toolpaths_from_decision_service.py](services/api/app/saw_lab/saw_lab_toolpaths_from_decision_service.py) | Orchestrator — load decision/plan/spec, apply tuning, call generator, persist artifact |
| [saw_lab/decision_apply_service.py](services/api/app/saw_lab/decision_apply_service.py) | Apply decision intelligence patches to base context |
| [saw_lab_run_service.py](services/api/app/saw_lab_run_service.py) | Single choke point for toolpath generation (boundary-safe) |
| [saw_lab/path_planner.py](services/api/app/saw_lab/path_planner.py) | Convert plan ops to cut segments |
| [saw_lab/toolpath_builder.py](services/api/app/saw_lab/toolpath_builder.py) | Low-level toolpath math (SawToolpathBuilder.build()) |
| [saw_lab/models.py](services/api/app/saw_lab/models.py) | SawContext, SawToolpathPlan data models |

### What Needs to Happen (Fix Plan)

**1. New endpoint: `POST /api/saw/batch/toolpaths/generate`**
- Input: `batch_decision_artifact_id: str`, `include_gcode: bool = True`
- Calls: `saw_lab.saw_lab_toolpaths_from_decision_service.generate_toolpaths_from_decision()`
- Returns: `batch_toolpaths_artifact_id`, `status`, `preview`
- Register in [batch_router.py](services/api/app/saw_lab/batch_router.py) or a new `batch_toolpaths_generate_router.py`

**2. Restore or re-create request/response schemas**
- `BatchToolpathsGenerateRequest(batch_decision_artifact_id: str, include_gcode: bool = True)`
- `BatchToolpathsGenerateResponse(batch_toolpaths_artifact_id: str, status: str, preview: Optional[dict])`
- Add to [batch_router_schemas.py](services/api/app/saw_lab/batch_router_schemas.py)

**3. Verify the generation chain compiles**
- `saw_lab_run_service.plan_saw_toolpaths_for_design()` calls `path_planner.build_segments_from_plan()` via lazy import — confirm this module exists and works
- `SawToolpathBuilder.build()` needs `segments` + `SawContext` — confirm the context is populated correctly from spec/plan payloads

**4. Add integration test**
- Full chain: SPEC → PLAN → APPROVE → GENERATE_TOOLPATHS → START_EXECUTION
- Verify `batch_toolpaths_artifact_id` is non-null after generation
- Verify the toolpaths artifact is persisted with correct parent linkage

**5. Consider auto-generation on approval (optional enhancement)**
- The `/approve` endpoint could optionally trigger toolpath generation inline
- Return both `batch_decision_artifact_id` and `batch_toolpaths_artifact_id`
- Keeps the pipeline one-click for operators

### Why Smoke Tests Didn't Catch This

The smoke test suite (`tests/test_saw_lab_endpoint_smoke.py`) passed **74/74** because it tests:
- ✅ Endpoint existence (routes respond to HTTP methods)
- ✅ Parameter validation (missing params return 422)
- ✅ Individual endpoint behavior in isolation

It does **NOT** test:
- ❌ End-to-end artifact flow across stages
- ❌ Whether stage N's output satisfies stage N+1's input
- ❌ Whether the toolpath generation service is reachable from any endpoint

The `BatchToolpathsByDecisionResponse` schema (lines 97–104 of [batch_router_schemas.py](services/api/app/saw_lab/batch_router_schemas.py)) exists but is defined-not-used — a dead schema referencing the artifact that can never be produced.

### Duplicate Service File Issue

There are **two** `saw_lab_toolpaths_from_decision_service.py` files:
1. `app/saw_lab/saw_lab_toolpaths_from_decision_service.py` — Batch-aware (uses `batch_decision` artifacts)
2. `app/services/saw_lab_toolpaths_from_decision_service.py` — Compare-only (uses `saw_compare_decision` artifacts)

These have **different function signatures** (`batch_decision_artifact_id` vs `decision_artifact_id`) and different internal logic. The `app/services/` version is the only one actively called (by `compare_router.py`). The `app/saw_lab/` version is the one needed for batch production but is completely orphaned.

This duplication should be reconciled during the fix — either merge into one service with a `kind` parameter, or keep them separate but wire both.
