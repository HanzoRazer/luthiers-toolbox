# Luthier's ToolBox — Remediation Plan

**Date:** 2026-02-05
**Based on:** `luthiers-toolbox-design-review.md` (scored 5.15/10) + `luthiers-toolbox-design-review-factcheck.md` (verified numbers)
**Goal:** Raise the weighted score from ~4.7/10 (corrected) to 7.0+/10

---

## Verified Baseline (current state)

| Metric | Count |
|--------|-------|
| Python files | 1,358 |
| Python LOC | 265,128 |
| TypeScript/Vue LOC | 146,183 |
| API route decorators | 1,060 |
| Router registrations in main.py | 123 |
| try: blocks in main.py | 47 |
| `except Exception` blocks | 1,622 |
| Bare `except:` blocks | 97 |
| Python files > 500 lines | 30+ |
| Vue files > 800 lines | 25+ |
| Test files | 262 |
| Test LOC | 45,141 |
| Docs .md files | 685 (in docs/), 1,100 total |
| Docs size | 12 MB |
| Backup/archive artifacts | 30+ files, 5 stale directories |

---

## Phase 0: Dead Code Purge (zero-risk, immediate impact)

**Impact:** Maintainability +2, Aesthetics +1
**Risk:** None (removing tracked artifacts that should never have been committed)

### 0.1 — Delete backup files from VCS

```
git rm client/src/components/toolbox/SimLab_BACKUP_Enhanced.vue
git rm client/src/labs/ReliefKernelLab_backup_phase24_6.vue
git rm client/src/views/PipelineLabView_backup.vue
git rm packages/client/src/components/toolbox/SimLab_BACKUP_Enhanced.vue
git rm server/sim_validate_BACKUP_I1.py
git rm services/api/app/routers/geometry_router.py.bak
git rm __REFERENCE__/phantom_cleanup_patch/main_original_backup.py
```

### 0.2 — Delete phase-numbered duplicate files

```
git rm packages/client/src/views/art/RiskDashboardCrossLab_Phase28_16.vue
```

Verify no imports reference this file first:
```bash
grep -r "RiskDashboardCrossLab_Phase28_16" packages/client/src/
```

### 0.3 — Delete stale directories

| Directory | Contents | Action |
|-----------|----------|--------|
| `__ARCHIVE__/` | Unknown archive | `git rm -r __ARCHIVE__/` |
| `__REFERENCE__/` | Old PS1 test scripts, guitar plans, cleanup patches | `git rm -r __REFERENCE__/` |
| `services/api/app/.archive_app_app_20251214/` | App snapshot from Dec 14 | `git rm -r services/api/app/.archive_app_app_20251214/` |
| `server/` | Legacy standalone server (5 router files) | `git rm -r server/` |
| `client/` (190 files) | Stale duplicate of `packages/client/` (498 files) | See 0.4 |

### 0.4 — Resolve `client/` vs `packages/client/` duplication

The root `client/` directory has 190 files. `packages/client/` has 498 files and is the active monorepo location (referenced by `pnpm-workspace.yaml`, `docker-compose.yml`).

**Action:**
1. Verify no build config references `client/` directly:
   ```bash
   grep -r '"client/' docker-compose.yml pnpm-workspace.yaml package.json Makefile 2>/dev/null
   ```
2. If clean: `git rm -r client/`
3. If referenced: update references to `packages/client/`, then delete.

### 0.5 — Evaluate `streamlit_demo/` for deletion

- Zero references from docker-compose.yml, package.json, or any config file
- Duplicates functionality already in the Vue frontend
- 2,358-line `app.py` is a maintenance liability

**Action:** `git rm -r streamlit_demo/` — or move to a separate `streamlit-demo` repo if preserving it matters.

### 0.6 — Update .gitignore

Add rules to prevent future backup/archive accumulation:
```
*_BACKUP_*
*_backup_*
*.bak
__ARCHIVE__/
__REFERENCE__/
*.backup
```

**Estimated cleanup:** ~200+ files removed, ~15-20 MB reduction in repo size.

---

## Phase 1: Exception Handling Hardening (safety-critical)

**Impact:** Safety +2, Reliability +2
**Risk:** Medium (changing error handling can expose latent bugs)

### 1.1 — Audit and fix all 97 bare `except:` blocks

Bare `except:` catches `SystemExit`, `KeyboardInterrupt`, and `GeneratorExit` — this is always wrong in application code.

**Priority order:**
1. Safety-critical paths first (feasibility/, gates/, cam/, calculators/)
2. Router/API handlers second
3. Utility/service code third

**Replacement pattern:**
```python
# FROM:
except:
    fallback_value

# TO:
except Exception:
    logger.exception("Context: what was being attempted")
    fallback_value
```

This is a mechanical search-and-replace with manual review of each site.

### 1.2 — Triage the 1,622 `except Exception` blocks

Not all broad exception handling is wrong. Triage into three buckets:

| Bucket | Criteria | Action |
|--------|----------|--------|
| **A: Safety-critical** | In feasibility/, gates/, cam/feedtime, calculators/feeds_speeds | Replace with specific exceptions; fail closed |
| **B: API handlers** | In router files (top-level request handlers) | Keep `except Exception` but add structured logging + return 500 with error ID |
| **C: Utility/internal** | In services, core, tools | Replace with specific exceptions case-by-case |

**Module breakdown (from verified data):**

| Module | `except Exception` count | Priority |
|--------|-------------------------|----------|
| `rmos/` | 197 | **A** (safety-critical) |
| `routers/` | 142 | B |
| `services/` | 45 | C |
| `art_studio/` | 39 | C |
| `cam/` | 35 | **A** (safety-critical) |
| `saw_lab/` | 32 | **A** (safety-critical) |
| `_experimental/` | 20 | C (low priority) |
| `vision/` | 16 | C |
| `ci/` | 15 | C |
| `calculators/` | 14 | **A** (safety-critical) |
| All others | ~1,167 | C |

### 1.3 — Add `@safety_critical` decorator

Create a decorator that enforces fail-closed behavior on annotated functions:

```python
# services/api/app/core/safety.py
import functools, logging

logger = logging.getLogger("safety")

def safety_critical(func):
    """Mark a function as safety-critical.
    Disables broad exception swallowing — any unhandled exception
    propagates to the caller. Logs the failure path."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception:
            logger.critical(f"SAFETY-CRITICAL FAILURE in {func.__qualname__}", exc_info=True)
            raise  # never swallow
    return wrapper
```

Apply to: `compute_feasibility()`, all G-code generation functions, feeds/speeds calculations, risk bucketing.

---

## Phase 2: API Surface Reduction (usability + maintainability)

**Impact:** Usability +2, Maintainability +2, Reliability +1
**Risk:** Medium-High (requires frontend audit to avoid breaking live features)

### 2.1 — Instrument route usage

Before culling routes, add lightweight access logging:

```python
# services/api/app/middleware/route_logger.py
from starlette.middleware.base import BaseHTTPMiddleware
import logging, datetime

route_log = logging.getLogger("route_usage")

class RouteUsageMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        route_log.info(f"{datetime.datetime.utcnow().isoformat()} {request.method} {request.url.path}")
        return await call_next(request)
```

Deploy for 2 weeks. Any route with zero hits is a cull candidate.

### 2.2 — Classify routes by lifecycle

Using the module breakdown (1,060 total routes across 33 modules):

| Tier | Routes | Modules | Action |
|------|--------|---------|--------|
| **Core** (keep) | ~200 | rmos, cam, calculators, art_studio | Stable API, document |
| **Power** (keep behind flag) | ~150 | saw_lab, compare, vision, smart_guitar | Feature-flagged |
| **Internal** (hide) | ~300 | routers (legacy), api, governance, ci, workflow | Move to `/api/internal/` prefix |
| **Cull candidates** | ~400 | _experimental, sandboxes, cost_attribution, cad, meta, redundant legacy routers | Delete after usage audit |

### 2.3 — Replace main.py conditional imports

The 47 try/except blocks in main.py allow the API surface to silently degrade. Replace with explicit feature registration:

```python
# services/api/app/features.py
FEATURES = {
    "rmos": {"enabled": True, "router": "app.rmos.api.rmos_runs_router"},
    "cam": {"enabled": True, "router": "app.cam.routers.cam_main_router"},
    "saw_lab": {"enabled": True, "router": "app.saw_lab.batch_router"},
    # ...
}

def get_enabled_features():
    return {k: v for k, v in FEATURES.items() if v["enabled"]}
```

Add `/api/features` endpoint that reports what's loaded:
```json
{
  "rmos": {"enabled": true, "routes": 193},
  "cam": {"enabled": true, "routes": 43},
  "saw_lab": {"enabled": false, "reason": "missing dependency: sg-spec"}
}
```

### 2.4 — Consolidate the 107 legacy routers

`services/api/app/routers/` contains 107 files — this is a flat directory of legacy routers that predates the domain-organized modules. Many are duplicated by newer routers in `rmos/`, `cam/`, `art_studio/`, etc.

**Action:**
1. For each file in `routers/`, check if an equivalent route exists in a domain module
2. If yes: delete the legacy router, update main.py
3. If no: move it into the appropriate domain module
4. Target: `routers/` directory should contain ≤10 shared utility routers

---

## Phase 3: God-Object Decomposition (maintainability)

**Impact:** Maintainability +2, Aesthetics +1
**Risk:** Medium (refactoring large files can introduce regressions)

### 3.1 — Python files over 500 lines (top 10)

| File | Lines | Decomposition Strategy |
|------|-------|----------------------|
| `saw_lab/batch_router.py` | 2,724 | Split into: batch_crud_router.py, batch_query_router.py, batch_execution_router.py, batch_schemas.py |
| `instrument_geometry/body/detailed_outlines.py` | 2,088 | Extract outline data into JSON/YAML files; keep computation only |
| `rmos/runs_v2/api_runs.py` | 1,845 | Split: run_crud.py, run_query.py, run_lifecycle.py |
| `rmos/runs_v2/store.py` | 1,733 | Split: store_read.py, store_write.py, store_migration.py |
| `cam/rosette/pattern_generator.py` | 1,683 | Extract pattern definitions to data files; keep algorithm |
| `routers/adaptive_router.py` | 1,479 | Move to cam/adaptive/router.py, split CRUD from computation |
| `routers/pipeline_router.py` | 1,380 | Move to rmos/pipeline/router.py |
| `routers/blueprint_router.py` | 1,315 | Move to vision/blueprint/router.py |
| `main.py` | 1,297 | Replace with auto-discovery (see Phase 2.3) |
| `cam/rosette/photo_converter.py` | 1,264 | Extract image processing pipeline stages |

### 3.2 — Vue files over 800 lines (top 10)

| File | Lines | Decomposition Strategy |
|------|-------|----------------------|
| `ManufacturingCandidateList.vue` | 2,987 | Extract: CandidateTable.vue, CandidateFilters.vue, CandidateDetail.vue, useCandidateStore.ts |
| `AdaptivePocketLab.vue` | 2,418 | Extract: PocketCanvas.vue, PocketControls.vue, PocketResults.vue |
| `RiskDashboardCrossLab.vue` | 2,062 | Extract: RiskMatrix.vue, RiskTimeline.vue, RiskFilters.vue |
| `ScaleLengthDesigner.vue` | 1,955 | Extract: ScaleCanvas.vue, FretTable.vue, CompensationPanel.vue |
| `DxfToGcodeView.vue` | 1,846 | Extract: DxfPreview.vue, GcodePreview.vue, MachineSelector.vue, SafetyGate.vue |
| `ScientificCalculator.vue` | 1,609 | Extract: CalcKeypad.vue, CalcDisplay.vue, CalcHistory.vue |
| `DesignFirstWorkflowPanel.vue` | 1,548 | Extract: WorkflowStepper.vue, DesignForm.vue, ExportPanel.vue |
| `SimLab_BACKUP_Enhanced.vue` | 1,477 | **DELETE** (backup file) |
| `PipelineLab.vue` | 1,465 | Extract: PipelineCanvas.vue, StageEditor.vue, PipelineResults.vue |
| `BlueprintLab.vue` | 1,458 | Extract: BlueprintUpload.vue, BlueprintAnnotator.vue, BlueprintResults.vue |

### 3.3 — Enforce file-size limits in CI

Add a CI check that fails on files exceeding limits:

```bash
# ci/check_file_sizes.sh
MAX_PY=500
MAX_VUE=800
violations=0
while IFS= read -r f; do
  lines=$(wc -l < "$f")
  if [ "$lines" -gt "$MAX_PY" ]; then
    echo "VIOLATION: $f ($lines lines, max $MAX_PY)"
    violations=$((violations + 1))
  fi
done < <(find services/api/app -name "*.py" -not -path "*__pycache__*")
# Same for Vue...
exit $violations
```

Use baseline mode (like existing fence architecture) to allow current violations but block new ones.

---

## Phase 4: Documentation Triage (maintainability)

**Impact:** Maintainability +1, Purpose Clarity +1
**Risk:** Low (documentation changes don't affect runtime)

### 4.1 — Categorize docs/ (685 files, 12 MB)

| Category | Count | Action |
|----------|-------|--------|
| Session logs (SESSION_*) | 6 | Move to `dev-journal` repo |
| AI protocol docs (CBSP*, AI_*) | 23 | Move to `dev-journal` repo |
| Audit/governance | 36 | Keep 5 essential, archive rest |
| Handoff/bundle docs | 61 | Move to `dev-journal` repo |
| ADRs | 4 | Keep all |
| docs/ARCHIVE/ | ~100+ | `git rm -r docs/ARCHIVE/` |
| Everything else | ~455 | Triage: keep ≤50 essential user/contributor docs |

### 4.2 — Create essential docs (≤20 files)

| Document | Purpose |
|----------|---------|
| `README.md` | 30-second overview + demo GIF, honest feature status |
| `CONTRIBUTING.md` | Build, test, deploy in 5 minutes |
| `docs/ARCHITECTURE.md` | System overview, module boundaries, data flow |
| `docs/API_REFERENCE.md` | Core API endpoints (≤80 routes) |
| `docs/DEPLOYMENT.md` | Docker, Railway, local dev |
| `docs/SAFETY_MODEL.md` | Feasibility scoring, risk buckets, safety gates |
| `docs/CAM_PIPELINE.md` | DXF → G-code flow, post-processors |
| `docs/RMOS_OVERVIEW.md` | Manufacturing Operating System concepts |
| `docs/MACHINE_PROFILES.md` | Supported machines, configuration |
| `docs/CHANGELOG.md` | Release history |

### 4.3 — Fix README claims

Replace misleading badges:
```markdown
<!-- FROM -->
- **Backend Coverage**: 100% (all routers operational)
- **Frontend Coverage**: 100% (all operations have UI)
- **Test Coverage**: 100% (comprehensive smoke test suites)

<!-- TO -->
- **Backend Test Coverage**: XX% (run `pytest --cov` for current number)
- **Test Files**: 262 across services/api/tests/
- **Smoke Test Coverage**: All critical paths (feasibility, G-code, feeds)
```

---

## Phase 5: Onboarding / Quick Cut Mode (user fit + usability)

**Impact:** User Fit +3, Usability +2, Purpose Clarity +1
**Risk:** Low (additive, doesn't change existing workflows)

### 5.1 — Build "Quick Cut" flow

Three-screen workflow:
1. **Upload** — DXF file upload with inline preview
2. **Configure** — Machine dropdown (auto-selects post-processor), material dropdown (auto-calculates feeds/speeds)
3. **Export** — G-code preview + download button, with safety summary badge

This is a single new Vue view (`QuickCutView.vue`) that calls 3-4 existing API endpoints:
- `POST /api/cam/dxf/upload`
- `GET /api/machines/profiles`
- `POST /api/cam/generate` (with auto-selected parameters)
- `GET /api/cam/gcode/preview`

No RMOS pipeline, no feasibility governance, no workflow sessions. Just DXF → G-code.

### 5.2 — Add "Pro Mode" toggle

Wrap advanced features (RMOS, governance, analytics, AI advisory, saw lab, validation harness) behind a localStorage toggle:

```typescript
// packages/client/src/stores/appModeStore.ts
export const useAppMode = defineStore('appMode', {
  state: () => ({ proMode: false }),
  actions: {
    toggle() { this.proMode = !this.proMode }
  }
})
```

Navigation items for advanced features only render when `proMode` is true.

---

## Phase 6: Health and Observability (reliability)

**Impact:** Reliability +1, Usability +1
**Risk:** Low (additive)

### 6.1 — Add `/api/health/detailed` endpoint

```python
@router.get("/api/health/detailed")
async def detailed_health():
    return {
        "status": "ok",
        "features": get_enabled_features(),  # from Phase 2.3
        "failed_imports": get_failed_imports(),
        "database_status": check_databases(),
        "uptime_seconds": get_uptime(),
        "version": get_version()
    }
```

### 6.2 — Replace silent import failures with tracked failures

```python
# In main.py, replace:
try:
    from .routers import some_router
    app.include_router(some_router.router)
except Exception:
    pass  # silent failure

# With:
try:
    from .routers import some_router
    app.include_router(some_router.router)
    _loaded_features.append("some_router")
except Exception as e:
    _failed_features.append({"name": "some_router", "error": str(e)})
    logger.warning(f"Router some_router failed to load: {e}")
```

---

## Execution Sequence

```
Phase 0 (Dead Code Purge)          ← Do FIRST. Zero risk, immediate maintainability win.
    |                                 Est: single commit, 200+ files removed
    |
Phase 1 (Exception Hardening)     ← SAFETY IMPERATIVE. Do before any feature work.
    |                                 1.1: bare except (97 sites) — mechanical
    |                                 1.2: except Exception triage (1,622 sites) — iterative
    |                                 1.3: @safety_critical decorator — small addition
    |
Phase 4 (Documentation Triage)    ← Can run in parallel with Phase 1.
    |                                 Low risk, reduces cognitive load for all other phases.
    |
Phase 2 (API Surface Reduction)   ← Depends on Phase 0 (stale routers already removed).
    |                                 2.1: instrument first (2 weeks data collection)
    |                                 2.2-2.4: cull after data
    |
Phase 3 (God-Object Decomposition) ← Depends on Phase 2 (know which routers survive).
    |                                  Can be incremental (one file per commit).
    |
Phase 5 (Quick Cut Mode)          ← Independent. Can start anytime.
    |                                 Additive feature, doesn't touch existing code.
    |
Phase 6 (Health/Observability)    ← Depends on Phase 2.3 (feature registry).
```

---

## Projected Score Improvement

| Category | Current (corrected) | After Plan | Key Driver |
|----------|-------------------|------------|------------|
| Purpose Clarity | 5 | 7 | Quick Cut mode, honest README |
| User Fit | 4 | 6 | Quick Cut flow, Pro Mode toggle |
| Usability | 3 | 6 | API reduction (1,060→200), feature flags |
| Reliability | 4 | 6 | Exception hardening, health endpoint |
| Maintainability | 3 | 6 | Dead code purge, god-object decomposition, doc triage |
| Cost / Efficiency | 5 | 6 | Streamlit deletion, lazy loading |
| Safety | 5 (corrected) | 8 | @safety_critical, bare except elimination |
| Scalability | 5 | 5 | (No changes planned — appropriate for current stage) |
| Aesthetics | 4 | 5 | Backup deletion, component decomposition |
| **Weighted Average** | **~4.7** | **~6.3** | |

---

## Success Criteria

Phase 0 is done when:
- [ ] Zero backup/archive files in `git ls-files`
- [ ] No `client/`, `server/`, `streamlit_demo/`, `__ARCHIVE__/`, `__REFERENCE__/` directories
- [ ] .gitignore updated to prevent recurrence

Phase 1 is done when:
- [ ] Zero bare `except:` blocks (`grep -rP '^\s*except\s*:' services/api/app/ | wc -l` == 0)
- [ ] All safety-critical paths use `@safety_critical` decorator
- [ ] `except Exception` in rmos/, cam/, calculators/ replaced with specific types

Phase 2 is done when:
- [ ] main.py < 200 lines (feature auto-discovery)
- [ ] `/api/features` endpoint reports all loaded/failed modules
- [ ] Route count < 300 (from 1,060)
- [ ] `routers/` directory contains ≤10 files (from 107)

Phase 3 is done when:
- [ ] No Python file > 500 lines (or baseline-locked with CI enforcement)
- [ ] No Vue file > 800 lines (or baseline-locked with CI enforcement)

Phase 4 is done when:
- [ ] `docs/` contains ≤50 files (from 685)
- [ ] README has accurate coverage numbers
- [ ] CONTRIBUTING.md exists with <5 minute build instructions

Phase 5 is done when:
- [ ] `/quick-cut` route exists and works: DXF upload → machine select → G-code download
- [ ] Pro Mode toggle hides RMOS/governance/analytics from default view

Phase 6 is done when:
- [ ] `/api/health/detailed` returns feature load status
- [ ] Zero silent `pass` blocks in main.py router registration
