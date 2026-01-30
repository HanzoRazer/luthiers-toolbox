# Legacy Code Status

> **Last Updated:** 2026-01-30
> **Purpose:** Single source of truth for legacy code, technical debt, and migration status.

---

## Executive Summary

| Category | Count | Status |
|----------|-------|--------|
| **Legacy Lane Endpoints** | 17 | UTILITY lane, awaiting OPERATION promotion |
| **Deprecated Routers** | ~~5~~ **0** | ✅ Superseded by Option C, **removed** |
| **Legacy Routers Deleted** | **19** | ✅ Deleted 2026-01-30 (~4,000 lines removed) |
| **Consolidation Candidates** | ~~17~~ **6** | ✅ 17 routers → 6 (completed via CAM/Compare consolidation) |
| **Critical TODOs (P1)** | ~~5~~ **0** | ✅ All P1 stubs resolved (2026-01-26) |
| **Incomplete Features (P2)** | ~~5~~ **0** | ✅ All P2 features completed (2026-01-26) |
| **Enhancement TODOs (P3)** | ~~3~~ **0** | ✅ All P3 items resolved (2026-01-30) |
| **ADR Phases Complete** | 5/5 | ADR-003 fully implemented |
| **RMOS Operations Bundles** | 17/17 | E2E bundle implementation complete |
| **Route Count** | **727** | Down from 804 (Phase 1) → 790 (Phase 2) → 727 (Phase 3) |

---

## 1. Lane Classification Status

### OPERATION Lane (Governed) - Complete

All promoted endpoints have full governance: artifacts, feasibility gates, audit trail.

| Tool Type | Endpoints | Phase | Status |
|-----------|-----------|-------|--------|
| saw | `/api/saw/batch/*` | Reference | Done |
| **operations** | `/api/rmos/operations/*` | **Bundles 01-17** | **Done** |
| rmos | `/api/rmos/toolpaths` | Wave 9 | Done |
| rosette | `/api/cam/rosette/*` | Wave 9 | Done |
| vcarve | `/api/art-studio/vcarve/gcode` | Wave 9 | Done |
| roughing | `/api/cam/toolpath/roughing/*` | Wave 10 | Done |
| drilling | `/api/cam/drilling/*` | Wave 10 | Done |
| biarc | `/api/cam/toolpath/biarc/*` | Wave 10 | Done |
| relief | `/api/art-studio/relief/export-dxf` | Wave 11 | Done |
| adaptive | `/api/cam/pocket/adaptive/*` | Wave 11 | Done |
| helical | `/api/cam/toolpath/helical_entry` | Wave 11 | Done |

### UTILITY Lane (Legacy) - Migration Pending

These endpoints produce G-code but bypass governance. Track usage via `/api/governance/stats`.

| Endpoint | Tool Type | Usage | Migration Priority |
|----------|-----------|-------|-------------------|
| `POST /feasibility` | — | Root-mounted | Low (internal) |
| `POST /toolpaths` | — | Root-mounted | Low (internal) |
| `POST /api/cam/roughing/gcode_intent` | roughing | Intent-native | Medium |
| `POST /api/rmos/workflow/sessions/{id}/toolpaths/request` | rosette | Session-scoped | Medium |
| `POST /api/rmos/workflow/sessions/{id}/toolpaths/store` | rosette | Session-scoped | Medium |
| `POST /api/art-studio/rosette/export-dxf` | rosette | DXF export | Low |
| `POST /api/art/rosette/preview/svg` | rosette | Preview only | N/A |

---

## 2. Router Deprecation Status

### Ready for Removal (Superseded by Option C)

| Router | Lines | Old Path | New Path | Sunset |
|--------|-------|----------|----------|--------|
| `archtop_router.py` | 307 | `/cam/archtop/*` | `/api/instruments/guitar/archtop/*` | Pending |
| `om_router.py` | 517 | `/cam/om/*` | `/api/instruments/guitar/om/*` | Pending |
| `stratocaster_router.py` | 430 | `/cam/stratocaster/*` | `/api/instruments/guitar/stratocaster/*` | Pending |
| `smart_guitar_router.py` | 357 | `/cam/smart-guitar/*` | `/api/instruments/guitar/smart/*` | Pending |
| `temperament_router.py` | 297 | `/temperaments/*` | `/api/music/temperament/*` | Pending |

**Total deprecated lines: 1,908**

### Legacy Tagged Routers (Governance Tracking) ✅ REMOVED

**All 19 legacy-tagged routers removed on 2026-01-30.**

| Category | Removed | Former Routers | Canonical Replacement |
|----------|---------|----------------|----------------------|
| CAM Legacy | 12 | vcarve, relief, helical, svg, fret_slots, drill_pattern, roughing, drilling, risk, biarc, fret_slots_export, risk_aggregate | `/api/cam/*` (consolidated Wave 18) |
| Compare Legacy | 5 | compare, lab, risk_aggregate, risk_bucket_detail, risk_bucket_export | `/api/compare/*` (consolidated Wave 19) |
| Rosette Legacy | 2 | rosette_pattern, art_studio_rosette | `/api/art/rosette/*` (Art Studio v2) |

### Consolidation Candidates ✅ COMPLETED

**Original target: 17 routers → 6. Now complete via Wave 18/19 consolidation.**

| Group | Status | Notes |
|-------|--------|-------|
| Pipeline | ✅ Consolidated | Pipeline presets merged |
| Calculators | ✅ Consolidated | `calculators_consolidated_router` |
| Posts | ✅ Consolidated | `posts_consolidated_router` |
| Machines | ✅ Consolidated | `machines_consolidated_router` |
| Simulation | ✅ Consolidated | `simulation_consolidated_router` |
| CAM | ✅ Consolidated | Wave 18 `cam_router` aggregator |
| Compare | ✅ Consolidated | Wave 19 `compare_router` aggregator |

---

## 3. Technical Debt Items

### Priority 1: Critical Stubs ~~(Production Blockers)~~ ✅ RESOLVED

**ALL P1 STUBS RESOLVED (2026-01-26)** — No safety risks remain.

| File | Line | Issue | Status |
|------|------|-------|--------|
| `rmos/api/rmos_feasibility_router.py` | 115-213 | SAW feasibility | ✅ Wired to `score_design_feasibility()` |
| `rmos/api/rmos_feasibility_router.py` | 220-316 | Rosette feasibility | ✅ Wired to `score_design_feasibility()` |
| `rmos/api/rmos_toolpaths_router.py` | 228-286 | Toolpath dispatcher | ✅ Wired to `generate_toolpaths_server_side()` |
| `rmos/api/rmos_toolpaths_router.py` | 288+ | SAW toolpath generator | ✅ Fallback only, real engine via dispatcher |
| `rmos/api/rmos_toolpaths_router.py` | 320+ | Rosette CAM engine | ✅ Fallback only, real engine via dispatcher |

**Feasibility Engine** (`feasibility_scorer.py`):
- 6 weighted calculators: chipload, heat, deflection, rim speed, geometry, channel
- Worst-case risk propagation (one RED → overall RED)
- Saw mode branching via `get_saw_engine().check_feasibility()`

### Priority 2: Incomplete Features ~~(5)~~ ✅ RESOLVED

**ALL P2 FEATURES COMPLETED (2026-01-26)**

| File | Line | Issue | Status |
|------|------|-------|--------|
| `toolpath/dxf_exporter.py` | 126+ | DXF entity type | ✅ Now emits LWPOLYLINE via `_write_entities_lwpolyline()` |
| `rmos/context.py` | 282-287 | String spacing | ✅ Calls `compute_edge_margin_spacing_mm()` |
| `util/compare_automation_helpers.py` | 116-147 | Compare engine | ✅ Uses `annotate_geometries_with_colors()` |
| `util/compare_automation_helpers.py` | 37-86 | Storage lookup | ✅ `load_svg_by_id()` checks file system + baselines |
| `rmos/context_adapter.py` | 270-286 | DXF parser | ✅ Uses `load_dxf_geometry_by_path()` with R12 parser |

### Priority 3: Enhancements ~~(3)~~ ✅ RESOLVED

| File | Line | Issue | Status |
|------|------|-------|--------|
| `cam_core/saw_lab/saw_blade_validator.py` | 293 | Generic RPM limits | ✅ Fixed - uses blade-specific rpm_min/rpm_max if available |
| `_experimental/cnc_production/learn/live_learn_ingestor.py` | 80 | Learned overrides not wired | ✅ Fixed - wired to LearnedOverridesStore |
| `_experimental/cnc_production/learn/saw_live_learn_dashboard.py` | 184 | tool_id returns None | ✅ Fixed - uses `run.meta.blade_id` |

**All P3 items resolved (2026-01-30)**

---

## 4. ADR Implementation Status

### ADR-003: CAM OPERATION Lane Promotion

| Phase | Description | Status | Date |
|-------|-------------|--------|------|
| Phase 1 | Artifact Wrapper | Done | 2025-12-29 |
| Phase 2 | Feasibility Gate | Done | 2025-12-30 |
| Phase 3 | Move Standardization | Done | 2025-12-31 |
| Phase 4 | Full Pipeline | Done | 2025-12-31 |
| Phase 5 | Feedback Loops | Done | 2025-12-31 |

**Infrastructure Delivered:**
- `rmos/moves.py` - Canonical GCodeMove model
- `rmos/posts/` - PostProcessor protocol + dialects
- `rmos/pipeline/` - SPEC/PLAN/DECISION/EXECUTE pipeline
- `rmos/pipeline/feedback/` - Job logs, learning events, rollups

### ADR-001: Fields and Policy Ownership

| Component | Status |
|-----------|--------|
| Field ownership boundaries | Documented |
| Policy enforcement points | Documented |

### ADR-002: Mesh Pipeline Coupling

| Component | Status |
|-----------|--------|
| Coupling analysis | Documented |
| Decoupling plan | Documented |

---

## 5. Legacy Code Patterns

### Anti-Patterns to Migrate

| Pattern | Location | Replacement |
|---------|----------|-------------|
| Direct G-code string return | Various CAM endpoints | Use `GCodeMove` + `render_gcode()` |
| No artifact persistence | UTILITY lane endpoints | Use `write_artifact()` |
| Hardcoded feasibility | `rmos_feasibility_router.py` | Wire to real scorers |
| Session-scoped toolpaths | `/api/rmos/workflow/sessions/*/toolpaths/*` | Use OPERATION lane pipeline |
| Root-mounted endpoints | `/feasibility`, `/toolpaths` | Move to `/api/` prefix |

### Deprecated Import Patterns

| Pattern | Status | Notes |
|---------|--------|-------|
| `from app.routers.archtop_router import *` | Deprecated | Use `instruments/guitar/` |
| `from app.routers.om_router import *` | Deprecated | Use `instruments/guitar/` |
| `from app.routers.stratocaster_router import *` | Deprecated | Use `instruments/guitar/` |
| `from app.routers.smart_guitar_router import *` | Deprecated | Use `instruments/guitar/` |
| `from app.routers.temperament_router import *` | Deprecated | Use `music/` |

---

## 6. Frontend Legacy Usage

### Current Legacy API Calls (2 usages in 1 file) ✅ MOSTLY MIGRATED

**Migrated (2026-01-30):** 6 usages updated to canonical paths.

| File | Line | Legacy Path | Canonical Path | Status |
|------|------|-------------|----------------|--------|
| `DrillingLab.vue` | 813 | `/api/cam/drill/gcode` | `/api/cam/drilling/gcode` | ✅ Migrated |
| `DrillingLab.vue` | 850 | `/api/cam/drill/gcode/download` | `/api/cam/drilling/gcode/download` | ✅ Migrated |
| `CAMEssentialsLab.vue` | 588 | `/api/cam/roughing/gcode` | `/api/cam/toolpath/roughing/gcode` | ✅ Migrated |
| `CAMEssentialsLab.vue` | 612 | `/api/cam/drill/gcode` | `/api/cam/drilling/gcode` | ✅ Migrated |
| `CAMEssentialsLab.vue` | 675 | `/api/cam/biarc/gcode` | `/api/cam/toolpath/biarc/gcode` | ✅ Migrated |
| `BridgeLabView.vue` | 613 | `/api/cam/roughing_gcode` | `/api/cam/toolpath/roughing/gcode` | ✅ Migrated |
| `useRosettePatternStore.ts` | 21+ | `/api/rosette-patterns` | N/A (CRUD, not preset) | ⏸️ Kept |

**Note:** `useRosettePatternStore.ts` uses CRUD operations for custom patterns, which is different
from the v2 preset pattern endpoints. This legacy path remains intentionally.

### CI Gate

```bash
# Check legacy usage
python -m app.ci.legacy_usage_gate \
  --roots "../../packages/client/src" "../../packages/sdk/src" \
  --budget 10  # Currently 2 usages (rosette-patterns), budget 10
```

---

## 7. Governance Tracking

### Endpoint Usage Stats

Check legacy endpoint usage:

```bash
curl http://localhost:8000/api/governance/stats
```

### Feature Flags

| Flag | Default | Purpose |
|------|---------|---------|
| `RMOS_RUNS_V2_ENABLED` | `true` | v2 governance-compliant runs |
| `{TOOL}_LEARNING_HOOK_ENABLED` | `false` | Auto-emit learning events |
| `{TOOL}_METRICS_ROLLUP_HOOK_ENABLED` | `false` | Auto-persist metrics rollups |
| `{TOOL}_APPLY_ACCEPTED_OVERRIDES` | `false` | Apply learned multipliers |

---

## 8. Migration Roadmap

### Completed (2026-01-30)

| Task | Status | Impact |
|------|--------|--------|
| ~~Wire real SAW feasibility scorer~~ | ✅ Done (2026-01-26) | Safety enforcement |
| ~~Wire real rosette feasibility scorer~~ | ✅ Done (2026-01-26) | Safety enforcement |
| ~~Consolidate pipeline routers~~ | ✅ Done | Cleaner codebase |
| ~~Consolidate calculator routers~~ | ✅ Done | Cleaner codebase |
| ~~Update frontend legacy API calls~~ | ✅ Done (2026-01-30) | Clean slate |
| ~~Remove deprecated instrument routers~~ | ✅ Done | -1,908 lines |
| ~~Delete legacy CAM/Compare/Rosette routers~~ | ✅ Done (2026-01-30) | -4,000 lines |
| ~~Complete DXF LWPOLYLINE support~~ | ✅ Done (2026-01-26) | CAD compliance |

### Remaining (Low Priority)

| Task | Effort | Impact |
|------|--------|--------|
| Migrate session-scoped toolpaths to OPERATION | Medium | Full governance |
| Remove `useRosettePatternStore` legacy path | Low | Only needed if CRUD functionality added to v2 |

---

## 9. Change Log

### 2026-01-30: Aggressive Legacy Cleanup (Phase 2+3) - COMPLETE

**Phase 1 (earlier):** Frontend migrated to canonical API paths (804 → 790 routes)

**Phase 2:** Remove legacy router registrations from main.py

**Phase 3:** Delete legacy router files (~4,000 lines removed)

**19 Legacy Router Files Deleted:**

| Category | Routers Deleted | Canonical Replacement |
|----------|-----------------|----------------------|
| CAM Legacy (12) | vcarve, relief_v160, svg_v160, helical_v161, fret_slots, risk, fret_slots_export, risk_aggregate, drill_pattern, roughing, biarc, drilling | `/api/cam/*` (Wave 18 aggregator) |
| Compare Legacy (5) | compare, compare_lab, compare_risk_aggregate, compare_risk_bucket_detail, compare_risk_bucket_export | `/api/compare/*` (Wave 19 aggregator) |
| Rosette Legacy (2) | rosette_pattern, art_studio/rosette | `/api/art/rosette/*` (Art Studio v2) |

**Supporting Changes:**
- `art_studio/__init__.py` - Removed `rosette_router` import
- `cam_roughing_intent_router.py` - Updated to use consolidated roughing router

**Route Count Progression:**
- 804 routes (before Phase 1)
- 790 routes (after Phase 1 - frontend migration)
- 727 routes (after Phase 2+3 - router deletion)

**Total Lines Removed:** ~4,000 lines

**Note:** `useRosettePatternStore.ts` intentionally kept at `/api/rosette-patterns`
(CRUD for custom patterns ≠ v2 preset patterns endpoint).

---

### 2026-01-03: Adaptive Pocket CI Fixes

**Fixed Adaptive Pocket (API) workflow - now passing:**

| Issue | File(s) | Resolution |
|-------|---------|------------|
| heat_timeseries 404 | `adaptive_pocket.yml` | Changed `machine_profile_id: "default"` → `"GRBL_3018_Default"` (profile didn't exist) |
| Bottleneck CSV CRLF | `adaptive_pocket.yml` | Changed `split('
')` → `splitlines()` to handle CRLF line endings |
| Logs write 500 error | `cam_logs.py` | Quoted `limit` column (SQL reserved keyword), always run DDL on db open |

**Files Modified:**

| File | Change |
|------|--------|
| `.github/workflows/adaptive_pocket.yml` | Fixed machine_profile_id, CRLF handling |
| `services/api/app/telemetry/cam_logs.py` | Quoted `"limit"` column, idempotent DDL |

**CI Status After Fix:**

| Workflow | Status |
|----------|--------|
| Adaptive Pocket (API) | ✅ Pass |

---

### 2026-01-03: Adaptive Pocket (Proxy) CI Fixes

**Fixed Adaptive Pocket (Proxy) workflow - now passing:**

| Issue | File(s) | Resolution |
|-------|---------|------------|
| PermissionError on `runs.json` | `proxy_adaptive.yml` | Docker volume mount permissions - added step to create writable data directory |
| TypeError: list indices | `proxy_adaptive.yml` | Initialized `runs.json` with `{}` (dict) instead of `[]` (list) |

**Files Modified:**

| File | Change |
|------|--------|
| `.github/workflows/proxy_adaptive.yml` | Added data directory setup step, debug logging for API errors |

**Key Pattern - Docker Volume Permissions in CI:**

When Docker mounts a host directory as a volume, the container may not have write permissions. Solution:
```yaml
- name: Ensure data directory is writable
  run: |
    mkdir -p services/api/app/data
    chmod 777 services/api/app/data
    echo "{}" > services/api/app/data/runs.json
    chmod 666 services/api/app/data/runs.json
```

**CI Status After Fix:**

| Workflow | Status |
|----------|--------|
| Adaptive Pocket (Proxy) | ✅ Pass |
| Adaptive Pocket (API) | ✅ Pass |

---

### 2026-01-02: PR #3 CI Fixes (feature/cnc-saw-labs merge)

**Critical CI Fixes:**

| Issue | File(s) | Resolution |
|-------|---------|------------|
| Docker container crashes | Multiple routers | Moved module-level `os.makedirs()` to lazy initialization |
| `safe_stem` TypeError | `util/names.py` | Added `prefix` parameter to function signature |
| 500 on `/api/cam/metrics/energy_csv` | `cam_metrics_router.py` | Fixed by `safe_stem` prefix support |
| 404 on simulate endpoint | `containers.yml` | Changed to `/api/sim/cam/simulate_gcode` |
| SQLite OperationalError | `art_studio_rosette_store.py` | Added `_ensure_db_dir()` helper, use absolute paths |
| Double prefix bugs | `tooling_router.py` | Removed internal prefix (was creating `/api/tooling/tooling/`) |

**Files Modified:**

| File | Change |
|------|--------|
| `services/api/app/util/names.py` | Added `prefix` parameter to `safe_stem()` |
| `services/api/app/art_studio_rosette_store.py` | SQLite path handling with `_ensure_db_dir()` |
| `services/api/app/learn/overrides_learner.py` | Moved `makedirs()` from module-level to function |
| `services/api/app/routers/tooling_router.py` | Removed internal prefix |
| `.github/workflows/containers.yml` | Fixed simulate endpoint path |
| `.github/workflows/proxy_parity.yml` | Added debug logging, case-insensitive grep |
| `.github/workflows/proxy_adaptive.yml` | Added debug logging for container failures |
| `docker-compose.yml` | Added `ART_STUDIO_DB_PATH` env var |

**CI Status After Merge:**

| Workflow | Status |
|----------|--------|
| Containers (Build + Smoke) | ✅ Pass |
| Proxy Parity | ✅ Pass |
| API Tests | ✅ Pass |
| Geometry Parity | ✅ Pass |
| SDK Codegen | ✅ Pass |
| Adaptive Pocket (API/Proxy) | ❌ Pre-existing failure |
| RTL CI | ❌ Pre-existing Pydantic issues |

---

### 2025-12-31 (Bundles 01-17)

- **Implemented** all 17 RMOS E2E bundles with governance compliance
- **Added** `rmos/operations/` module (adapter, router, saw_adapter, cam_adapter, export)
- **Added** `rmos/services/lineage.py` for Plan → Execute tracking
- **Updated** `runs_v2/schemas.py` with `RunLineage`, `RunAttachmentRowV1`
- **Updated** `runs_v2/store.py` with `parent_plan_run_id` filtering
- **Added** frontend SDK: `sdk/rmos/operations.ts`, `sdk/rmos/runs_attachments.ts`
- **Added** Vue components: `RmosOperationE2EPanel.vue`, `PlanAttachmentsInspector.vue`
- **Mounted** operations router at `/api/rmos/operations`

### 2025-12-31

- **Created** LEGACY_CODE_STATUS.md as single source of truth
- ADR-003 Phase 5 complete (feedback loops infrastructure)
- All 5 ADR-003 phases now implemented

### 2025-12-27

- Legacy routes tagged with `"Legacy"` for governance tracking
- Frontend legacy usage gate added to CI (budget: 10)

### 2025-12-21

- Technical debt handoff created (10 TODOs identified)
- Router inventory created (100 routers, 561 endpoints)

---

## Related Documents

| Document | Purpose |
|----------|---------|
| [ROUTER_MAP.md](../ROUTER_MAP.md) | All routers by wave |
| [ENDPOINT_TRUTH_MAP.md](ENDPOINT_TRUTH_MAP.md) | Complete API surface |
| [ADR-003](adr/ADR-003-cam-operation-lane-promotion.md) | CAM lane promotion plan |
| [TECHNICAL_DEBT_HANDOFF_2025-12.md](handoffs/TECHNICAL_DEBT_HANDOFF_2025-12.md) | Detailed TODO analysis |
| [ROUTER_INVENTORY_AND_DEPRECATION_PLAN.md](ROUTER_INVENTORY_AND_DEPRECATION_PLAN.md) | Router deprecation details |

---

*Document maintained by development team. Update when legacy status changes.*
