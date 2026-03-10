# The Production Shop — Consolidated Gap Analysis

> **Generated:** 2026-03-10
> **Goal:** Narrow down everything until we're forced to get in the Shop and make it happen
> **Score Progress:** 4.7/10 → 6.68/10 → Target 7.0+

---

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
