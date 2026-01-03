# Legacy Code Status

> **Last Updated:** 2026-01-02
> **Purpose:** Single source of truth for legacy code, technical debt, and migration status.

---

## Executive Summary

| Category | Count | Status |
|----------|-------|--------|
| **Legacy Lane Endpoints** | 17 | UTILITY lane, awaiting OPERATION promotion |
| **Deprecated Routers** | 5 | Superseded by Option C, awaiting removal |
| **Consolidation Candidates** | 10 | Duplicate/overlapping routers |
| **Critical TODOs (P1)** | 5 | Production blockers with stub implementations |
| **Incomplete Features (P2)** | 5 | Reduced functionality |
| **Enhancement TODOs (P3)** | 3 | Nice-to-have improvements |
| **ADR Phases Complete** | 5/5 | ADR-003 fully implemented |
| **RMOS Operations Bundles** | 17/17 | E2E bundle implementation complete |

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

### Legacy Tagged Routers (Governance Tracking)

These routers have `"Legacy"` tag for usage monitoring:

| Category | Count | Routers |
|----------|-------|---------|
| CAM Legacy | 12 | vcarve, relief, helical, svg, fret_slots, drill_pattern, roughing, drilling, risk, biarc |
| Compare Legacy | 5 | compare, lab, risk_aggregate, risk_bucket_detail, risk_bucket_export |
| Rosette Legacy | 2 | rosette_pattern, art_studio_rosette |

### Consolidation Candidates

| Group | Current Routers | Target | Lines Saved |
|-------|-----------------|--------|-------------|
| Pipeline | 5 routers | 2 routers | ~300 |
| Calculators | 2 routers | 1 router | ~280 |
| Posts | 2 routers | 1 router | ~100 |
| Machines | 2 routers | 1 router | ~85 |
| Simulation | 2 routers | 1 router | ~38 |

---

## 3. Technical Debt Items

### Priority 1: Critical Stubs (Production Blockers)

These return fake/stub data and represent **safety risks** if deployed to production.

| File | Line | Issue | Risk |
|------|------|-------|------|
| `rmos/api/rmos_feasibility_router.py` | 97 | Hardcoded `GREEN` for SAW | Could approve unsafe cuts |
| `rmos/api/rmos_feasibility_router.py` | 146 | Hardcoded `GREEN` for rosette | Could approve impossible designs |
| `rmos/api/rmos_toolpaths_router.py` | 216 | Empty toolpath dispatcher | No actual G-code |
| `rmos/api/rmos_toolpaths_router.py` | 238 | Stub SAW toolpath generator | No actual G-code |
| `rmos/api/rmos_toolpaths_router.py` | 259 | Stub rosette CAM engine | No actual G-code |

### Priority 2: Incomplete Features

| File | Line | Issue | Impact |
|------|------|-------|--------|
| `toolpath/dxf_exporter.py` | 133 | LINE entities, not LWPOLYLINE | R14/R18 DXF compat |
| `rmos/context.py` | 282-283 | Empty string spacing arrays | Fretboard calcs incomplete |
| `util/compare_automation_helpers.py` | 89 | Stub compare engine | Compare Lab incomplete |
| `util/compare_automation_helpers.py` | 41 | Stub storage lookup | Cannot retrieve baselines |
| `rmos/context_adapter.py` | 273 | Stub DXF parser | Blueprint import limited |

### Priority 3: Enhancements

| File | Line | Issue | Impact |
|------|------|-------|--------|
| `cam_core/saw_lab/saw_blade_validator.py` | 293 | Generic RPM limits | Enhanced validation |
| `_experimental/cnc_production/learn/live_learn_ingestor.py` | 80 | Learned overrides not wired | ML optimization unavailable |
| `_experimental/cnc_production/learn/saw_live_learn_dashboard.py` | 184 | tool_id returns None | Dashboard incomplete |

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

### Current Legacy API Calls (8 usages in 4 files)

| File | Line | Legacy Path | Canonical Path |
|------|------|-------------|----------------|
| `DrillingLab.vue` | 637 | `/api/cam/drill/gcode` | `/api/cam/drilling/gcode` |
| `DrillingLab.vue` | 674 | `/api/cam/drill/gcode/download` | `/api/cam/drilling/gcode/download` |
| `CAMEssentialsLab.vue` | 364 | `/api/cam/roughing/gcode` | `/api/cam/toolpath/roughing/gcode` |
| `CAMEssentialsLab.vue` | 388 | `/api/cam/drill/gcode` | `/api/cam/drilling/gcode` |
| `CAMEssentialsLab.vue` | 451 | `/api/cam/biarc/gcode` | `/api/cam/toolpath/biarc/gcode` |
| `useRosettePatternStore.ts` | 21 | `/api/rosette-patterns` | `/api/art/rosette/pattern/patterns` |
| `useRosettePatternStore.ts` | 35 | `/api/rosette-patterns` | `/api/art/rosette/pattern/patterns` |
| `BridgeLabView.vue` | 517 | `/api/cam/roughing_gcode` | `/api/cam/toolpath/roughing/gcode` |

### CI Gate

```bash
# Check legacy usage
python -m app.ci.legacy_usage_gate \
  --roots "../../packages/client/src" "../../packages/sdk/src" \
  --budget 10  # Currently 8 usages, budget 10
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

### Immediate (Next Sprint)

| Task | Effort | Impact |
|------|--------|--------|
| Wire real SAW feasibility scorer | High | P1 safety |
| Wire real rosette feasibility scorer | High | P1 safety |
| Add deprecation headers to legacy routers | Low | Tracking |

### Short-term (Next Month)

| Task | Effort | Impact |
|------|--------|--------|
| Consolidate pipeline routers (5 → 2) | Medium | Maintainability |
| Consolidate calculator routers (2 → 1) | Low | Maintainability |
| Update frontend legacy API calls (8) | Medium | Clean slate |

### Medium-term (Next Quarter)

| Task | Effort | Impact |
|------|--------|--------|
| Remove deprecated instrument routers | Low | -1,908 lines |
| Migrate session-scoped toolpaths to OPERATION | High | Full governance |
| Complete DXF LWPOLYLINE support | Medium | Compatibility |

---

## 9. Change Log

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
