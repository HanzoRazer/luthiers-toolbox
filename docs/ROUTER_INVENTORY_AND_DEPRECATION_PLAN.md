# Router Inventory and Deprecation Plan

> Generated: 2025-12-21
> **Updated: 2026-01-30**
> Total Routers: **~95** (down from 114 after legacy cleanup)
> Total Endpoints: **727** (down from ~600 estimate)
> Wave 20: Option C API Restructuring

---

## Status Update (2026-01-30)

### Phase 2+3 Legacy Cleanup COMPLETE

**19 legacy router files deleted** (~4,000 lines removed):

| Category | Count | Routers Deleted |
|----------|-------|-----------------|
| CAM Legacy | 12 | `cam_vcarve_router`, `cam_relief_v160_router`, `cam_svg_v160_router`, `cam_helical_v161_router`, `cam_fret_slots_router`, `cam_fret_slots_export_router`, `cam_risk_router`, `cam_risk_aggregate_router`, `cam_drill_pattern_router`, `cam_roughing_router`, `cam_biarc_router`, `drilling_router` |
| Compare Legacy | 5 | `compare_router`, `compare_lab_router`, `compare_risk_aggregate_router`, `compare_risk_bucket_detail_router`, `compare_risk_bucket_export_router` |
| Rosette Legacy | 2 | `rosette_pattern_router`, `art_studio/rosette_router` |

**All functionality preserved via:**
- `/api/cam/*` - Wave 18 consolidated CAM aggregator
- `/api/compare/*` - Wave 19 consolidated Compare aggregator
- `/api/art/rosette/*` - Art Studio v2 routes

---

## Status Update (2026-01-23)

### Completed Deprecations

All 5 deprecated routers from the original plan have been removed:

| Router | Removed | Replacement | Legacy Redirect |
|--------|---------|-------------|-----------------|
| archtop_router.py | YES | instruments/guitar/archtop_* | legacy/guitar_legacy_router.py |
| om_router.py | YES | instruments/guitar/om_* | legacy/guitar_legacy_router.py |
| stratocaster_router.py | YES | instruments/guitar/stratocaster_* | legacy/guitar_legacy_router.py |
| smart_guitar_router.py | YES | instruments/guitar/smart_* | legacy/smart_guitar_legacy_router.py |
| temperament_router.py | YES | music/temperament_router.py | legacy/temperament_legacy_router.py |

### Governance Structure

Self-executing removal enforcement is now active:

- **Registry**: services/api/app/ci/deprecation_registry.json
- **CI Check**: python -m app.ci.check_deprecation_sunset
- **Workflow**: .github/workflows/deprecation_sunset_guard.yml

CI fails when routes exceed their sunset date. Requires governance label to extend.

### Pending Patches

- **PATCH-001**: Archtop/Smart Guitar design issues (see docs/PENDING_PATCHES.md)

### Sunset Schedule

| Route Category | Sunset Date | Status |
|----------------|-------------|--------|
| Guitar legacy redirects | 2026-03-01 | Active |
| Temperament legacy redirects | 2026-04-01 | Active |
| Compat mounts (/geometry, /cam, etc.) | 2026-06-01 | Active |

---

## Table of Contents

1. [Router Inventory by Domain](#router-inventory-by-domain)
2. [Option C Migration Status](#option-c-migration-status)
3. [Deprecation Candidates](#deprecation-candidates)
4. [Consolidation Opportunities](#consolidation-opportunities)
5. [Recommended Actions](#recommended-actions)

---

## Router Inventory by Domain

### CAM Core (35 routers, ~180 endpoints)

| Router | Path | Lines | Prefix | Status |
|--------|------|-------|--------|--------|
| `pipeline_router.py` | `services/api/app/routers/pipeline_router.py` | 1380 | `/cam` | **KEEP** - Core orchestration |
| `adaptive_router.py` | `services/api/app/routers/adaptive_router.py` | 1283 | `/cam/pocket/adaptive` | **KEEP** - Adaptive pocketing |
| `geometry_router.py` | `services/api/app/routers/geometry_router.py` | 1084 | `/geometry` | **KEEP** - Core geometry |
| `blueprint_cam_bridge.py` | `services/api/app/routers/blueprint_cam_bridge.py` | 965 | `/cam/blueprint` | **KEEP** |
| `dxf_plan_router.py` | `services/api/app/routers/dxf_plan_router.py` | 526 | `/cam` | **KEEP** |
| `cam_metrics_router.py` | `services/api/app/routers/cam_metrics_router.py` | 640 | `/cam/metrics` | **KEEP** |
| `cam_settings_router.py` | `services/api/app/routers/cam_settings_router.py` | 265 | `/cam/settings` | **KEEP** |
| `cam_helical_v161_router.py` | - | - | - | 🗑️ **DELETED** (2026-01-30) → `/api/cam/toolpath/helical` |
| `cam_post_v155_router.py` | `services/api/app/routers/cam_post_v155_router.py` | 362 | `/api/cam_gcode` | **KEEP** |
| `cam_risk_aggregate_router.py` | - | - | - | 🗑️ **DELETED** (2026-01-30) → `/api/cam/risk` |
| `cam_risk_router.py` | - | - | - | 🗑️ **DELETED** (2026-01-30) → `/api/cam/risk` |
| `cam_drill_router.py` | `services/api/app/routers/cam_drill_router.py` | 143 | `/cam/drill` | **KEEP** |
| `cam_drill_pattern_router.py` | - | - | - | 🗑️ **DELETED** (2026-01-30) → `/api/cam/drilling/pattern` |
| `cam_relief_router.py` | - | - | - | 🗑️ **DELETED** (2026-01-30) → `/api/cam/relief` |
| `cam_roughing_router.py` | - | - | - | 🗑️ **DELETED** (2026-01-30) → `/api/cam/toolpath/roughing` |
| `cam_vcarve_router.py` | - | - | - | 🗑️ **DELETED** (2026-01-30) → `/api/cam/toolpath/vcarve` |
| `cam_biarc_router.py` | - | - | - | 🗑️ **DELETED** (2026-01-30) → `/api/cam/toolpath/biarc` |
| `cam_opt_router.py` | `services/api/app/routers/cam_opt_router.py` | 111 | `/cam/opt` | **KEEP** |
| `polygon_offset_router.py` | `services/api/app/routers/polygon_offset_router.py` | 177 | `/cam` | **KEEP** |
| `cam_polygon_offset_router.py` | `services/api/app/routers/cam_polygon_offset_router.py` | 91 | - | ⚠️ **REVIEW** - Duplicate? |
| `cam_sim_router.py` | `services/api/app/routers/cam_sim_router.py` | 38 | `/cam` | **KEEP** |
| `cam_simulate_router.py` | `services/api/app/routers/cam_simulate_router.py` | 72 | `/cam` | ⚠️ **REVIEW** - vs cam_sim |
| `cam_backup_router.py` | `services/api/app/routers/cam_backup_router.py` | 46 | `/cam/backup` | **KEEP** |
| `cam_logs_router.py` | `services/api/app/routers/cam_logs_router.py` | 72 | `/cam/logs` | **KEEP** |
| `cam_learn_router.py` | `services/api/app/routers/cam_learn_router.py` | 55 | `/cam/learn` | **KEEP** |
| `gcode_backplot_router.py` | `services/api/app/routers/gcode_backplot_router.py` | 117 | `/api/cam/gcode` | **KEEP** |

### Instrument Model Routers (8 routers)

| Router | Path | Lines | Prefix | Status |
|--------|------|-------|--------|--------|
| `archtop_router.py` | `services/api/app/routers/archtop_router.py` | 307 | `/cam/archtop` | 🔴 **DEPRECATE** |
| `om_router.py` | `services/api/app/routers/om_router.py` | 517 | `/cam/om` | 🔴 **DEPRECATE** |
| `stratocaster_router.py` | `services/api/app/routers/stratocaster_router.py` | 430 | `/cam/stratocaster` | 🔴 **DEPRECATE** |
| `smart_guitar_router.py` | `services/api/app/routers/smart_guitar_router.py` | 357 | `/cam/smart-guitar` | 🔴 **DEPRECATE** |
| `parametric_guitar_router.py` | `services/api/app/routers/parametric_guitar_router.py` | 465 | `/guitar/design` | ⚠️ **REVIEW** |
| `body_generator_router.py` | `services/api/app/routers/body_generator_router.py` | 426 | - | ⚠️ **REVIEW** |
| `neck_generator_router.py` | `services/api/app/routers/neck_generator_router.py` | 389 | - | ⚠️ **REVIEW** |
| `temperament_router.py` | `services/api/app/routers/temperament_router.py` | 297 | `/temperaments` | 🔴 **DEPRECATE** |

### Option C New Structure (12 routers)

| Router | Path | Lines | Prefix | Status |
|--------|------|-------|--------|--------|
| `instruments/__init__.py` | `services/api/app/routers/instruments/__init__.py` | - | `/api/instruments` | ✅ **NEW** |
| `instruments/guitar/__init__.py` | `services/api/app/routers/instruments/guitar/__init__.py` | - | `/api/instruments/guitar` | ✅ **NEW** |
| `instruments/guitar/registry_router.py` | `services/api/app/routers/instruments/guitar/registry_router.py` | 356 | - | ✅ **NEW** - Dynamic 23 models |
| `instruments/guitar/assets_router.py` | `services/api/app/routers/instruments/guitar/assets_router.py` | 180 | - | ✅ **NEW** - E2E file serving |
| `instruments/guitar/archtop_instrument_router.py` | `services/api/app/routers/instruments/guitar/archtop_instrument_router.py` | 150 | `/archtop` | ✅ **NEW** |
| `instruments/guitar/om_instrument_router.py` | `services/api/app/routers/instruments/guitar/om_instrument_router.py` | 150 | `/om` | ✅ **NEW** |
| `instruments/guitar/stratocaster_instrument_router.py` | `services/api/app/routers/instruments/guitar/stratocaster_instrument_router.py` | 150 | `/stratocaster` | ✅ **NEW** |
| `instruments/guitar/smart_instrument_router.py` | `services/api/app/routers/instruments/guitar/smart_instrument_router.py` | 176 | `/smart` | ✅ **NEW** |
| `cam/guitar/__init__.py` | `services/api/app/routers/cam/guitar/__init__.py` | - | `/api/cam/guitar` | ✅ **NEW** |
| `cam/guitar/registry_cam_router.py` | `services/api/app/routers/cam/guitar/registry_cam_router.py` | 280 | - | ✅ **NEW** - Dynamic CAM |
| `music/temperament_router.py` | `services/api/app/routers/music/temperament_router.py` | 350 | `/api/music/temperament` | ✅ **NEW** |
| `legacy/__init__.py` | `services/api/app/routers/legacy/__init__.py` | - | - | ✅ **NEW** - 308 redirects |

### Fretboard & Neck (3 routers - 2 deleted)

| Router | Path | Lines | Prefix | Status |
|--------|------|-------|--------|--------|
| `fret_router.py` | `services/api/app/routers/fret_router.py` | 696 | `/fret` | **KEEP** |
| `neck_router.py` | `services/api/app/routers/neck_router.py` | 472 | `/neck` | **KEEP** |
| `cam_fret_slots_router.py` | - | - | - | 🗑️ **DELETED** (2026-01-30) → `/api/cam/fret_slots` |
| `cam_fret_slots_export_router.py` | - | - | - | 🗑️ **DELETED** (2026-01-30) → `/api/cam/fret_slots` |
| `bridge_router.py` | `services/api/app/routers/bridge_router.py` | 359 | `/cam/bridge` | **KEEP** |

### DXF & Preflight (3 routers)

| Router | Path | Lines | Prefix | Status |
|--------|------|-------|--------|--------|
| `dxf_preflight_router.py` | `services/api/app/routers/dxf_preflight_router.py` | 786 | `/dxf/preflight` | **KEEP** |
| `cam_dxf_adaptive_router.py` | `services/api/app/routers/cam_dxf_adaptive_router.py` | 143 | `/cam` | **KEEP** |
| `dxf_plan_router.py` | `services/api/app/routers/dxf_plan_router.py` | 526 | `/cam` | **KEEP** |

### Saw Lab (6 routers)

| Router | Path | Lines | Prefix | Status |
|--------|------|-------|--------|--------|
| `saw_telemetry_router.py` | `services/api/app/routers/saw_telemetry_router.py` | 498 | - | **KEEP** |
| `saw_blade_router.py` | `services/api/app/routers/saw_blade_router.py` | 241 | `/saw/blades` | **KEEP** |
| `saw_validate_router.py` | `services/api/app/routers/saw_validate_router.py` | 230 | `/saw/validate` | **KEEP** |
| `rmos_saw_ops_router.py` | `services/api/app/routers/rmos_saw_ops_router.py` | 143 | `/saw-ops` | **KEEP** |
| `saw_gcode_router.py` | `services/api/app/routers/saw_gcode_router.py` | 132 | `/saw_gcode` | **KEEP** |
| `dashboard_router.py` | `services/api/app/routers/dashboard_router.py` | 271 | `/dashboard/saw` | **KEEP** |

### Rosette & Art Studio (2 routers - 2 deleted)

| Router | Path | Lines | Prefix | Status |
|--------|------|-------|--------|--------|
| `art_studio_rosette_router.py` | - | - | - | 🗑️ **DELETED** (2026-01-30) → `/api/art/rosette` |
| `rosette_pattern_router.py` | - | - | - | 🗑️ **DELETED** (2026-01-30) → `/api/art/rosette/pattern` |
| `rosette_photo_router.py` | `services/api/app/routers/rosette_photo_router.py` | 321 | `/cam/rosette` | **KEEP** |
| `rmos_patterns_router.py` | `services/api/app/routers/rmos_patterns_router.py` | 117 | `/rosette-patterns` | **KEEP** |

### Compare Lab (2 routers - 5 deleted)

| Router | Path | Lines | Prefix | Status |
|--------|------|-------|--------|--------|
| `compare_router.py` | - | - | - | 🗑️ **DELETED** (2026-01-30) → `/api/compare` |
| `compare_lab_router.py` | - | - | - | 🗑️ **DELETED** (2026-01-30) → `/api/compare/lab` |
| `compare_automation_router.py` | `services/api/app/routers/compare_automation_router.py` | 71 | `/compare` | **KEEP** |
| `compare_risk_aggregate_router.py` | - | - | - | 🗑️ **DELETED** (2026-01-30) → `/api/compare/risk` |
| `compare_risk_bucket_detail_router.py` | - | - | - | 🗑️ **DELETED** (2026-01-30) → `/api/compare/risk` |
| `compare_risk_bucket_export_router.py` | - | - | - | 🗑️ **DELETED** (2026-01-30) → `/api/compare/risk` |
| `cam_compare_diff_router.py` | `services/api/app/routers/cam_compare_diff_router.py` | 58 | - | **KEEP** |

### Presets & Pipeline (5 routers)

| Router | Path | Lines | Prefix | Status |
|--------|------|-------|--------|--------|
| `unified_presets_router.py` | `services/api/app/routers/unified_presets_router.py` | 662 | `/presets` | **KEEP** - Primary |
| `pipeline_presets_router.py` | `services/api/app/routers/pipeline_presets_router.py` | 173 | `/cam/pipeline` | ⚠️ **CONSOLIDATE** |
| `pipeline_preset_router.py` | `services/api/app/routers/pipeline_preset_router.py` | 73 | `/cam/pipeline/presets` | ⚠️ **CONSOLIDATE** |
| `cam_pipeline_router.py` | `services/api/app/routers/cam_pipeline_router.py` | 79 | `/api/cam/pipeline` | ⚠️ **CONSOLIDATE** |
| `cam_pipeline_preset_run_router.py` | `services/api/app/routers/cam_pipeline_preset_run_router.py` | 82 | `/cam/pipeline` | ⚠️ **CONSOLIDATE** |

### Tooling & Feeds (4 routers)

| Router | Path | Lines | Prefix | Status |
|--------|------|-------|--------|--------|
| `tooling_router.py` | `services/api/app/routers/tooling_router.py` | 512 | `/tooling` | **KEEP** |
| `feeds_router.py` | `services/api/app/routers/feeds_router.py` | 105 | `/tooling` | **KEEP** |
| `learned_overrides_router.py` | `services/api/app/routers/learned_overrides_router.py` | 355 | `/feeds/learned` | **KEEP** |
| `machines_tools_router.py` | `services/api/app/routers/machines_tools_router.py` | 200 | `/machines/tools` | **KEEP** |

### Calculators (3 routers)

| Router | Path | Lines | Prefix | Status |
|--------|------|-------|--------|--------|
| `calculators_router.py` | `services/api/app/routers/calculators_router.py` | 546 | `/calculators` | **KEEP** |
| `ltb_calculator_router.py` | `services/api/app/routers/ltb_calculator_router.py` | 283 | `/api/calculators` | ⚠️ **CONSOLIDATE** |
| `analytics_router.py` | `services/api/app/routers/analytics_router.py` | 354 | - | **KEEP** |

### Other/Utility (16 routers)

| Router | Path | Lines | Prefix | Status |
|--------|------|-------|--------|--------|
| `blueprint_router.py` | `services/api/app/routers/blueprint_router.py` | 1268 | `/blueprint` | **KEEP** |
| `health_router.py` | `services/api/app/routers/health_router.py` | 130 | - | **KEEP** |
| `learn_router.py` | `services/api/app/routers/learn_router.py` | 205 | `/learn` | **KEEP** |
| `probe_router.py` | `services/api/app/routers/probe_router.py` | 424 | - | **KEEP** |
| `vision_router.py` | `services/api/app/routers/vision_router.py` | 330 | `/vision` | **KEEP** |
| `retract_router.py` | `services/api/app/routers/retract_router.py` | 366 | - | **KEEP** |
| `post_router.py` | `services/api/app/routers/post_router.py` | 372 | `/api/posts` | **KEEP** |
| `posts_router.py` | `services/api/app/routers/posts_router.py` | 101 | `/posts` | ⚠️ **CONSOLIDATE** with post_router |
| `machine_router.py` | `services/api/app/routers/machine_router.py` | 107 | `/machine` | **KEEP** |
| `machines_router.py` | `services/api/app/routers/machines_router.py` | 85 | `/cam/machines` | ⚠️ **CONSOLIDATE** |
| `material_router.py` | `services/api/app/routers/material_router.py` | 86 | `/material` | **KEEP** |
| `instrument_router.py` | `services/api/app/routers/instrument_router.py` | 281 | `/api/instrument` | ⚠️ **REVIEW** |
| `instrument_geometry_router.py` | `services/api/app/routers/instrument_geometry_router.py` | 432 | - | ⚠️ **REVIEW** |
| `registry_router.py` | `services/api/app/routers/registry_router.py` | 284 | - | ⚠️ **REVIEW** |
| `sim_metrics_router.py` | `services/api/app/routers/sim_metrics_router.py` | 178 | `/cam/sim` | **KEEP** |
| `websocket_router.py` | `services/api/app/routers/websocket_router.py` | 77 | - | **KEEP** |

---

## Option C Migration Status

### Completed Migrations

| Old Path | New Path | Old Router | New Router |
|----------|----------|------------|------------|
| `/cam/archtop/*` | `/api/instruments/guitar/archtop/*` | `archtop_router.py` | `instruments/guitar/archtop_instrument_router.py` |
| `/cam/archtop/*` | `/api/cam/guitar/archtop/*` | `archtop_router.py` | `cam/guitar/archtop_cam_router.py` |
| `/cam/om/*` | `/api/instruments/guitar/om/*` | `om_router.py` | `instruments/guitar/om_instrument_router.py` |
| `/cam/om/*` | `/api/cam/guitar/om/*` | `om_router.py` | `cam/guitar/om_cam_router.py` |
| `/cam/stratocaster/*` | `/api/instruments/guitar/stratocaster/*` | `stratocaster_router.py` | `instruments/guitar/stratocaster_instrument_router.py` |
| `/cam/stratocaster/*` | `/api/cam/guitar/stratocaster/*` | `stratocaster_router.py` | `cam/guitar/stratocaster_cam_router.py` |
| `/cam/smart-guitar/*` | `/api/instruments/guitar/smart/*` | `smart_guitar_router.py` | `instruments/guitar/smart_instrument_router.py` |
| `/cam/smart-guitar/*` | `/api/cam/guitar/smart/*` | `smart_guitar_router.py` | `cam/guitar/smart_cam_router.py` |
| `/temperaments/*` | `/api/music/temperament/*` | `temperament_router.py` | `music/temperament_router.py` |

### Legacy Compatibility

The `legacy/` directory provides 308 redirects:

```
services/api/app/routers/legacy/
├── __init__.py                    # Aggregates all legacy routers
├── guitar_legacy_router.py        # Redirects /cam/archtop, /cam/om, /cam/stratocaster
└── smart_guitar_legacy_router.py  # Redirects /cam/smart-guitar
```

---

## Deprecation Candidates

### 🔴 Ready for Deprecation (superseded by Option C)

| File | Lines | Reason | Replacement |
|------|-------|--------|-------------|
| `archtop_router.py` | 307 | Superseded by Option C split | `instruments/guitar/archtop_*` + `cam/guitar/archtop_*` |
| `om_router.py` | 517 | Superseded by Option C split | `instruments/guitar/om_*` + `cam/guitar/om_*` |
| `stratocaster_router.py` | 430 | Superseded by Option C split | `instruments/guitar/stratocaster_*` + `cam/guitar/stratocaster_*` |
| `smart_guitar_router.py` | 357 | Superseded by Option C split | `instruments/guitar/smart_*` + `cam/guitar/smart_*` |
| `temperament_router.py` | 297 | Superseded by Option C music axis | `music/temperament_router.py` |

**Total lines to deprecate: 1,908**

### Deprecation Process

1. Add `@deprecated` decorator with sunset date (e.g., 2025-03-01)
2. Add `X-Deprecated-Route: true` header in responses
3. Update frontend to use new paths
4. Remove after sunset date

---

## Consolidation Opportunities

### ⚠️ Pipeline/Presets Consolidation

**Current state:** 5 overlapping routers

```
pipeline_router.py              (1380 lines) /cam
cam_pipeline_router.py          (79 lines)   /api/cam/pipeline
pipeline_presets_router.py      (173 lines)  /cam/pipeline
pipeline_preset_router.py       (73 lines)   /cam/pipeline/presets
cam_pipeline_preset_run_router.py (82 lines) /cam/pipeline
```

**Recommendation:** Consolidate into 2 routers:
- `pipeline_router.py` - Core pipeline orchestration
- `pipeline_presets_router.py` - All preset management

### ⚠️ Calculator Consolidation

**Current state:** 2 overlapping routers

```
calculators_router.py    (546 lines) /calculators
ltb_calculator_router.py (283 lines) /api/calculators
```

**Recommendation:** Merge into single `calculators_router.py`

### ⚠️ Posts Consolidation

**Current state:** 2 overlapping routers

```
post_router.py   (372 lines) /api/posts
posts_router.py  (101 lines) /posts
```

**Recommendation:** Merge into single `post_router.py`

### ⚠️ Machines Consolidation

**Current state:** 2 overlapping routers

```
machine_router.py  (107 lines) /machine
machines_router.py (85 lines)  /cam/machines
```

**Recommendation:** Merge into single `machines_router.py`

### ⚠️ Simulation Consolidation

**Current state:** 2 similar routers

```
cam_sim_router.py      (38 lines)  /cam
cam_simulate_router.py (72 lines)  /cam
```

**Recommendation:** Merge into single `cam_simulation_router.py`

---

## Recommended Actions

### Phase 1: Immediate (Wave 21)

| Action | Files | Effort |
|--------|-------|--------|
| Mark old instrument routers deprecated | 5 files | Low |
| Add deprecation headers | 5 files | Low |
| Update main.py comments | 1 file | Low |

### Phase 2: Short-term (Wave 22)

| Action | Files | Effort |
|--------|-------|--------|
| Consolidate pipeline routers | 5 → 2 files | Medium |
| Consolidate calculator routers | 2 → 1 file | Low |
| Consolidate posts routers | 2 → 1 file | Low |
| Consolidate machines routers | 2 → 1 file | Low |

### Phase 3: Cleanup (Wave 23+)

| Action | Files | Effort |
|--------|-------|--------|
| Remove deprecated instrument routers | 5 files | Low |
| Update frontend to Option C paths | Multiple | High |
| Remove legacy redirect routers | 2 files | Low |

---

## Metrics Summary

| Category | Count |
|----------|-------|
| Total routers | **~95** (down from 114) |
| Total endpoints | **727** (down from 804) |
| ~~Ready for deprecation~~ | ~~5 (1,908 lines)~~ ✅ Done |
| ~~Consolidation candidates~~ | ~~10 (1,540 lines)~~ ✅ Done |
| Option C new routers | 12 |
| Legacy routers deleted | **19** (~4,000 lines) |
| **Net after cleanup** | **~95 routers** |

---

## File Tree Reference

```
services/api/app/routers/
├── __init__.py
├── adaptive_*.py              # Adaptive pocketing (3 files)
├── analytics_router.py        # Analytics
├── archtop_router.py          # 🔴 DEPRECATE
├── art/                       # Art Studio
│   ├── __init__.py
│   └── root_art_router.py
├── art_*.py                   # Art Studio (3 files)
├── blueprint_*.py             # Blueprint Lab (2 files)
├── body_generator_router.py   # Body generation
├── bridge_router.py           # Bridge calculations
├── calculators_router.py      # Calculators
├── cam/                       # ✅ NEW Option C CAM axis
│   ├── __init__.py
│   └── guitar/
│       ├── __init__.py
│       ├── archtop_cam_router.py
│       ├── om_cam_router.py
│       ├── registry_cam_router.py
│       ├── smart_cam_router.py
│       └── stratocaster_cam_router.py
├── cam_*.py                   # CAM operations (25+ files)
├── cnc_production/            # CNC Production
│   ├── __init__.py
│   ├── compare_jobs_router.py
│   └── presets_router.py
├── compare_*.py               # Compare Lab (7 files)
├── dashboard_router.py        # Saw Lab dashboard
├── drilling_router.py         # Drilling
├── dxf_*.py                   # DXF operations (2 files)
├── feeds_router.py            # Feeds & speeds
├── fret_router.py             # Fretboard
├── gcode_backplot_router.py   # G-code visualization
├── geometry_router.py         # Core geometry
├── health_router.py           # Health checks
├── instrument_*.py            # Instrument geometry (2 files)
├── instruments/               # ✅ NEW Option C Instruments axis
│   ├── __init__.py
│   └── guitar/
│       ├── __init__.py
│       ├── archtop_instrument_router.py
│       ├── assets_router.py
│       ├── om_instrument_router.py
│       ├── registry_router.py
│       ├── smart_instrument_router.py
│       └── stratocaster_instrument_router.py
├── job_*.py                   # Job management (3 files)
├── learn_*.py                 # Learning system (2 files)
├── legacy/                    # ✅ NEW Legacy redirects
│   ├── __init__.py
│   ├── guitar_legacy_router.py
│   └── smart_guitar_legacy_router.py
├── live_monitor_drilldown_api.py
├── ltb_calculator_router.py   # ⚠️ CONSOLIDATE
├── machine_router.py          # ⚠️ CONSOLIDATE
├── machines_*.py              # Machines (2 files)
├── material_router.py         # Materials
├── music/                     # ✅ NEW Option C Music axis
│   ├── __init__.py
│   └── temperament_router.py
├── neck_*.py                  # Neck operations (2 files)
├── om_router.py               # 🔴 DEPRECATE
├── parametric_guitar_router.py
├── pipeline_*.py              # Pipeline (4 files) ⚠️ CONSOLIDATE
├── polygon_offset_router.py
├── post_router.py
├── posts_router.py            # ⚠️ CONSOLIDATE
├── probe_router.py
├── registry_router.py
├── retract_router.py
├── rmos_*.py                  # RMOS (2 files)
├── rosette_*.py               # Rosette (2 files)
├── saw_*.py                   # Saw Lab (4 files)
├── sim_*.py                   # Simulation (2 files)
├── smart_guitar_router.py     # 🔴 DEPRECATE
├── stratocaster_router.py     # 🔴 DEPRECATE
├── strip_family_router.py
├── temperament_router.py      # 🔴 DEPRECATE
├── tooling_router.py
├── unified_presets_router.py
├── vision_router.py
└── websocket_router.py
```

---

*Document generated by GitHub Copilot during Wave 20 Option C restructuring*
