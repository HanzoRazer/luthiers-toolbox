# Luthier's ToolBox Router Roadmap

**Last Updated:** 2026-01-03
**Total Routers:** ~116 working routers organized across 22 waves
**Status:** All previously-broken routers (9) fixed; 84 phantom imports removed
**Governance:** Legacy routes tagged for deprecation tracking (see Canonical vs Legacy section)  

This document maps all FastAPI routers in the Luthier's ToolBox API, organized by deployment waves. Each wave represents a feature rollout with related routers grouped for easier navigation and understanding.

---

## Quick Reference

| Wave | Theme | Router Count | Status |
|------|-------|--------------|--------|
| Core | Basic CAM | 11 | ✅ |
| 1–6 | Foundation (RMOS, Specialty) | 12 | ✅ |
| 7–13 | Feature Expansion | 49 | ✅ |
| 14–15 | Vision & Art Studio | 9 | ✅ |
| 16–17 | Governance & Workflow | 8 | ✅ |
| 18–19 | Consolidation (CAM, Compare) | 5 | ✅ |
| 20–22 | Art Studio Runs & Acoustics | 4 | ✅ |

---

## Canonical vs Legacy Lanes

> **Updated 2025-12-27**: All legacy routes now have `"Legacy"` tag for governance tracking.

The API has evolved through consolidation phases. Legacy routes remain mounted for backwards compatibility but are marked for eventual deprecation. The governance middleware tracks usage of Legacy-tagged routes.

### CAM Routes

| Legacy Route | Prefix | Canonical Replacement | Notes |
|--------------|--------|----------------------|-------|
| `cam_vcarve_router` | `/api/cam/vcarve` | `/api/cam/toolpath/vcarve` | Wave 18 consolidated |
| `cam_relief_router` | `/api/cam/relief` | `/api/cam/relief` | Proxy (same code) |
| `cam_helical_router` | `/api/cam/helical` | `/api/cam/toolpath/helical` | Wave 18 consolidated |
| `cam_svg_router` | `/api/cam/svg` | `/api/cam/export` | Wave 18 consolidated |
| `cam_fret_slots_router` | `/api/cam/fret_slots` | `/api/cam/fret_slots` | Proxy (same code) |
| `cam_fret_slots_export_router` | `/api/cam/fret_slots` | `/api/cam/fret_slots` | Proxy (same code) |
| `cam_drill_pattern_router` | `/api/cam/drilling/pattern` | `/api/cam/drilling/pattern` | Wave 18 consolidated |
| `cam_roughing_router` | `/api/cam/roughing` | `/api/cam/toolpath/roughing` | Wave 18 consolidated |
| `drilling_router` | `/api/cam/drilling` | `/api/cam/drilling` | Wave 18 consolidated |
| `cam_risk_router` | `/api/cam/risk` | `/api/cam/risk` | Wave 18 consolidated |
| `cam_risk_aggregate_router` | `/api/cam/jobs` | `/api/cam/risk` | Wave 18 consolidated |
| `cam_biarc_router` | `/api/cam/biarc` | `/api/cam/toolpath/biarc` | Wave 18 consolidated |

### Compare Routes

| Legacy Route | Prefix | Canonical Replacement | Notes |
|--------------|--------|----------------------|-------|
| `legacy_compare_router` | `/api/compare` | `/api/compare` | Wave 19 consolidated |
| `compare_lab_router` | `/api/compare/lab` | `/api/compare/lab` | Wave 19 consolidated |
| `compare_risk_aggregate_router` | `/api/compare` | `/api/compare/risk` | Wave 19 consolidated |
| `compare_risk_bucket_detail_router` | `/api/compare` | `/api/compare/risk` | Wave 19 consolidated |
| `compare_risk_bucket_export_router` | `/api/compare` | `/api/compare/risk` | Wave 19 consolidated |

### Rosette Routes

| Legacy Route | Prefix | Canonical Replacement | Notes |
|--------------|--------|----------------------|-------|
| `rosette_pattern_router` | `/api/rosette` | `/api/cam/rosette` or `/api/art/rosette` | Multi-lane |
| `art_studio_rosette_router` | `/api/art-studio/rosette` | `/api/art/rosette` | Art Studio v2 |

### Governance Integration

Legacy routes are tracked by:
1. **FastAPI Tags**: All legacy routes have `"Legacy"` in their tags array
2. **Endpoint Middleware**: `EndpointGovernanceMiddleware` detects `"Legacy"` tag and records hits
3. **Metrics**: Usage stats available at `/api/governance/stats`

To migrate off legacy routes:
1. Check governance stats for zero/low usage
2. Update frontend to use canonical endpoints
3. Remove legacy mount from `main.py`

---

## Detailed Wave Breakdown

### Core CAM (11 routers)
*Foundation CAM functionality: simulation, feeds, geometry, tooling, machines, materials.*

- `sim_router` — Simulation endpoints
- `feeds_router` — Feeds & Speeds calculations
- `geometry_router` — Geometry utilities
- `tooling_router` — Tooling database
- `adaptive_router` — Adaptive Pocketing CAM
- `machine_router` — Machine definitions
- `cam_opt_router` — CAM Optimization
- `material_router` — Material properties
- `cam_metrics_router` — CAM Metrics
- `cam_logs_router` — CAM Logging
- `cam_learn_router` — CAM Learning system

**Prefix:** `/api/{component}`  
**Tags:** `Simulation`, `Feeds & Speeds`, `Geometry`, etc.

---

### RMOS 2.0 (4 routers)
*Rosette Manufacturing Orchestration System: AI search, constraint profiles, profile history, and orchestration.*

- `rmos_router` — Core RMOS endpoints
- `rmos_ai_router` — AI Search + Profile Management (Phase B+C)
- `rmos_profiles_router` — Constraint Profiles
- `rmos_history_router` — Profile History

**Prefix:** `/api/rmos`  
**Tags:** `RMOS`, `RMOS AI`, `RMOS Profiles`, `RMOS History`  
**Note:** Feasibility router moved to Wave 16 (governance bundle).

---

### CAM Subsystem (8 routers)
*Specialized CAM operations: V-carve, post-processing, relief, SVG export, helical ramping, backplot.*

- `cam_vcarve_router` — V-Carve operations
- `cam_post_v155_router` — Post-processor v1.55
- `cam_smoke_v155_router` — Smoke/validation tests
- `cam_relief_router` — Relief Carving
- `cam_svg_router` — SVG Export
- `cam_helical_router` — Helical Ramping
- `gcode_backplot_router` — G-Code Backplot visualization
- `adaptive_preview_router` — Adaptive Preview

**Prefix:** `/api/cam/{component}`  
**Tags:** `V-Carve`, `Post Processor`, `Relief Carving`, etc.

---

### Pipeline & Presets (2 routers)
*Workflow management: pipeline presets and DXF planning.*

- `pipeline_presets_router` — Pipeline Presets management
- `dxf_plan_router` — DXF Planning utilities

**Prefix:** `/api/pipeline/presets`, `/api/dxf`  
**Tags:** `Pipeline Presets`, `DXF Planning`

---

### Blueprint CAM Bridge (1 router)
*Import/integration layer for Blueprint instrument designs.*

- `blueprint_cam_bridge_router` — Blueprint → CAM conversion

**Prefix:** `/api/blueprint/cam`  
**Tags:** `Blueprint CAM Bridge`

---

### Machine & Post Configuration (3 routers)
*Machine and tool management, post-processor library.*

- `machines_router` — Machine definitions
- `machines_tools_router` — Machine tool library
- `posts_router` — Post-processor library

**Prefix:** `/api/machines`, `/api/machines/tools`, `/api/posts`  
**Tags:** `Machines`, `Machine Tools`, `Post Processors`

---

### Instrument Geometry (1 router)
*Guitar-specific geometry calculations and utilities.*

- `instrument_geometry_router` — Instrument geometry operations

**Prefix:** `/api/instrument`  
**Tags:** `Instrument Geometry`

---

### Data Registry (1 router)
*Central data registry and discovery.*

- `registry_router` — Data Registry endpoints

**Prefix:** `/api/registry`  
**Tags:** `Data Registry`

---

### Saw Lab (2 routers)
*Saw/blade optimization and debugging.*

- `saw_debug_router` — Saw Lab debug utilities
- `saw_compare_router` — Saw Lab comparison tools

**Prefix:** `/api/saw/debug`, `/api/saw`  
**Tags:** `Saw Lab`, `Debug`

---

### Specialty Modules – Guitar-Specific Calculators (4 routers)
*Domain-specific guitars: archtop, stratocaster, smart guitar, OM.*

- `archtop_router` — Archtop guitar calculations
- `stratocaster_router` — Stratocaster-specific parameters
- `smart_guitar_router` — Smart Guitar system
- `om_router` — OM guitar calculations

**Prefix:** `/api/guitar/{type}`  
**Tags:** `Guitar`, `Archtop`, `Stratocaster`, `Smart Guitar`, `OM`

---

### G-Code Generators (2 routers) – Wave 3
*Automated G-code generation for body and neck.*

- `body_generator_router` — Body G-code generation
- `neck_generator_router` — Neck G-code generation

**Prefix:** `/api/cam/body`, `/api/cam/neck`  
**Tags:** `G-Code Generators`, `Body`, `Neck`

---

### CAD Engine (1 router) – Wave 4
*DXF-based CAD operations and exports.*

- `cad_dxf_router` — CAD/DXF utilities

**Prefix:** `/api/cad`  
**Tags:** `CAD`, `DXF`

---

### Rosette System (2 routers) – Wave 5
*Decorative rosette pattern design and generation.*

- `rosette_pattern_router` — Rosette pattern calculations
- `art_studio_rosette_router` — Art Studio rosette integration

**Prefix:** `/api/rosette`, `/api`  
**Tags:** `Rosette`, `Patterns`, `Art Studio`

---

### Smart Guitar Temperaments (1 router) – Wave 6
*Fret positioning and temperament tuning systems.*

- `temperament_router` — Temperament/fret calculations

**Prefix:** `/api/smart-guitar`  
**Tags:** `Smart Guitar`, `Temperaments`

---

### Wave 7: Calculator Suite + Fret Slots CAM + Bridge Calculator + Fret Design (4 routers)
*Unified calculators, fret slot CAM, bridge design.*

- `calculators_router` — General calculators
- `cam_fret_slots_router` — Fret slot CAM operations
- `bridge_router` — Bridge calculator
- `fret_router` — Fret design utilities

**Prefix:** `/api`, `/api/cam/fret_slots`  
**Tags:** `Calculators`, `CAM`, `Fret Slots`, `Bridge Calculator`, `Fret Design`

---

### Wave 8: Presets + RMOS Extensions + CAM Tools (7 routers)
*Unified presets, RMOS pattern/saw ops, CAM intents, retract patterns.*

- `unified_presets_router` — Unified preset management
- `strip_family_router` — Strip Family patterns (RMOS)
- `rmos_patterns_router` — RMOS pattern library
- `rmos_saw_ops_router` — RMOS saw operation orchestration
- `rmos_cam_intent_router` — RMOS CAM Intent (H7.1.2 schema)
- `sim_metrics_router` — Simulation metrics
- `retract_router` — Retract pattern management
- `rosette_photo_router` — Rosette photo import

**Prefix:** `/api`, `/api/cam/retract`  
**Tags:** `Presets`, `RMOS`, `CAM`, `Simulation`, `Rosette`  
**Note:** Canonical CAM envelope: `app.rmos.cam.CamIntentV1` — do not create alternatives.

---

### Wave 9: AI-CAM + Drill/Roughing + Compare + DXF Preflight + JobLog + Neck (8 routers)
*AI-assisted CAM, drilling, compare workflows, preflight validation, job logging.*

- `ai_cam_router` — AI-assisted CAM (experimental, optional)
- `cam_drill_pattern_router` — Drill pattern generation
- `cam_roughing_router` — Roughing operations
- `compare_router` — Compare baseline workflows
- `dxf_preflight_router` — DXF preflight validation
- `joblog_router` — Job logging/telemetry (experimental)
- `neck_router` — Neck generation
- `parametric_guitar_router` — Parametric guitar design

**Prefix:** `/api`, `/api/compare` (built-in), `/api/cam/drilling`  
**Tags:** `AI-CAM`, `CAM`, `Drill Patterns`, `Roughing`, `Compare`, `DXF`, `JobLog`, `Neck`, `Guitar`  
**Status:** Some routers optional (try/except imports); safe to fail.

---

### Wave 10: Instrument + Compare Lab + Drilling + Risk + Learn + Backup (8 routers)
*Instrument registry, compare lab, drilling optimization, risk assessment, learning systems.*

- `instrument_router` — Instrument management
- `compare_lab_router` — Compare Laboratory workflows
- `drilling_router` — Drilling operations
- `cam_risk_router` — CAM risk analysis (built-in prefix `/api/cam/risk`)
- `job_risk_router` — Job-level risk assessment
- `learn_router` — Learning system (optional)
- `learned_overrides_router` — Learned feed overrides (optional)
- `cam_backup_router` — CAM backup/recovery

**Prefix:** `/api`, `/api/cam/risk` (built-in), `/api/cam/drilling`  
**Tags:** `Instrument`, `Compare`, `Risk`, `Learn`, `CAM`, `Jobs`  
**Status:** Some routers optional; safe to fail gracefully.

---

### Wave 11: Analytics + Probe + LTB Calculator + CAM Tools (8 routers)
*Data analytics, touch-off probe management, advanced calculator, dashboard.*

- `analytics_router` — Analytics endpoints (optional)
- `advanced_analytics_router` — Advanced analytics (optional)
- `probe_router` — Touch-off probe utilities
- `ltb_calculator_router` — LTB calculator suite (built-in prefix `/api/calculators`)
- `dashboard_router` — Dashboard service (optional)
- `cam_settings_router` — CAM settings management
- `cam_biarc_router` — Biarc smoothing
- `job_intelligence_router` — Job intelligence analytics

**Prefix:** `/api`, `/api/calculators` (built-in)  
**Tags:** `Analytics`, `Probe`, `Touch-off`, `Calculator`, `CAM`, `Settings`, `Biarc`, `Intelligence`  
**Status:** Analytics and dashboard are optional.

---

### Wave 12: CAM Extensions + Compare Risk + Fret Export + Polygon (8 routers)
*Advanced CAM benchmarking, fret export, risk aggregation, polygon offset.*

- `cam_adaptive_benchmark_router` — Adaptive CAM benchmarking
- `cam_fret_slots_export_router` — Fret slot export (built-in prefix `/api/cam/fret_slots`)
- `cam_risk_aggregate_router` — CAM risk aggregation (built-in prefix `/api/cam/jobs`)
- `compare_risk_aggregate_router` — Compare risk aggregation (built-in prefix `/api/compare`)
- `compare_risk_bucket_detail_router` — Risk bucket detail view (built-in prefix `/api/compare`)
- `polygon_offset_router` — Polygon offset utilities
- `job_insights_router` — Job insights (built-in prefix `/api/cam/job_log`)
- `pipeline_preset_router` — Pipeline preset operations

**Prefix:** `/api`, `/api/cam/*` (built-in), `/api/compare` (built-in)  
**Tags:** `CAM`, `Compare`, `Risk`, `Polygon`, `Export`, `Insights`, `Pipeline`

---

### Wave 13 (FINAL): Art Presets + CAM Utilities + Compare + Monitor (10 routers)
*Art/design presets, CAM compare/simulate, live monitoring.*

- `art_presets_router` — Art/design presets
- `cam_compare_diff_router` — CAM diff comparison
- `cam_dxf_adaptive_router` — DXF adaptive processing
- `cam_pipeline_preset_run_router` — Pipeline preset execution
- `cam_polygon_offset_router` — Polygon offset (advanced)
- `cam_simulate_router` — CAM simulation
- `compare_automation_router` — Compare automation workflows
- `compare_risk_bucket_export_router` — Risk bucket export (built-in prefix `/api/compare`)
- `health_router_ext` — Extended health checks
- `live_monitor_router` — Live monitoring/drilldown

**Prefix:** `/api`, `/api/system/health`  
**Tags:** `Art`, `CAM`, `Compare`, `Polygon`, `Monitor`, `Health`

---

### CNC Production (1 router)
*CNC production-specific workflows and job comparison.*

- `cnc_compare_jobs_router` — Compare CNC production jobs

**Prefix:** `/api/cnc/compare`  
**Tags:** `CNC Production`

---

### Wave 14: Vision Engine + RMOS Runs + Advisory (3 routers)
*AI graphics, vision processing, run orchestration with feature flags.*

- `rmos_runs_router` — RMOS Runs (v2 governance-compliant by default; v1 legacy fallback via `RMOS_RUNS_V2_ENABLED`)
- `vision_router` — Vision Engine / AI Graphics (optional)
- `advisory_router` — AI-powered advisory (optional)
- `teaching_router` — Teaching loop / training system (optional)

**Prefix:** `/api/rmos` (runs), `/api`, tags only for optional routers  
**Tags:** `RMOS Runs`, `Vision Engine`, `AI Graphics`, `Advisory`, `Teaching Loop`  
**Feature Flag:** `RMOS_RUNS_V2_ENABLED` (default: `true`)  
**Status:** Optional routers; safe to skip.

---

### Wave 15: Art Studio Core Completion – Bundle 31.0 (5 routers)
*Design-first mode: pattern library, generators, preview, snapshots, workflow.*

- `art_patterns_router` — Pattern library management (optional)
- `art_generators_router` — Pattern/design generators (optional)
- `art_preview_router` — Preview rendering (optional)
- `art_snapshots_router` — Snapshot management (optional)
- `art_workflow_router` — Workflow orchestration (optional)

**Prefix:** `/api/art/*` (built-in in routers)  
**Tags:** `Art Studio`, `Patterns`, `Generators`, `Preview`, `Snapshots`, `Workflow`  
**Status:** Optional; safe to fail.

---

### Wave 16: Governance Code Bundle – Canonical Workflow + Run Artifacts (4 routers)
*Governance contracts: server-side feasibility, artifact persistence, run queries, workflow.*

- `rmos_feasibility_router` — Server-side feasibility (optional)
- `rmos_toolpaths_router` — Canonical toolpaths (optional)
- `rmos_runs_api_router` — Run artifacts API (optional)
- `rmos_workflow_router` — Canonical workflow (optional)

**Prefix:** `/api` (tags only)  
**Tags:** `RMOS`, `Feasibility`, `Toolpaths`, `Runs API`, `Workflow`  
**Contracts:**
- `SERVER_SIDE_FEASIBILITY_ENFORCEMENT_CONTRACT_v1.md`
- `RUN_ARTIFACT_PERSISTENCE_CONTRACT_v1.md`
- `RUN_ARTIFACT_INDEX_QUERY_API_CONTRACT_v1.md`
- `RUN_DIFF_VIEWER_CONTRACT_v1.md`

**Status:** Optional; implement contracts if adding run persistence.

---

### Wave 17: Workflow Sessions (1 router)
*SQLite-backed workflow session persistence and recovery.*

- `workflow_sessions_router` — Workflow session management (optional)

**Prefix:** `/api` (tags only)  
**Tags:** `Workflow`, `Sessions`

---

### Wave 18: CAM Router Consolidation – Phase 5+6 (4 routers)
*Single aggregator for organized CAM endpoints + rosette job routes.*

- `cam_router` — Consolidated CAM aggregator (optional; includes drilling, fret_slots, relief, risk, rosette, simulation, toolpath, export, monitoring, pipeline, utility)
- `rosette_jobs_router` — Rosette jobs (Phase 5, optional)
- `rosette_compare_router` — Rosette compare (Phase 5, optional)
- `rosette_pattern_router_v2` — Rosette patterns v2 (Phase 5, optional)

**Prefix:** `/api/cam/{category}/{operation}`, `/api` (rosette routes built-in)  
**Tags:** `CAM Consolidated`, `Art Studio`, `Rosette Jobs`, `Rosette Compare`, `Rosette Patterns v2`  
**Categories (under CAM aggregator):** drilling, fret_slots, relief, risk, rosette, simulation, toolpath, export, monitoring, pipeline, utility  
**Status:** Consolidation phase; optional routers allow gradual migration.

---

### Wave 19: Compare Router Consolidation (1 router)
*Single aggregator for organized Compare endpoints.*

- `compare_router` — Consolidated Compare aggregator (optional; includes baselines, risk, lab, automation)

**Prefix:** `/api/compare/{category}/{operation}`  
**Tags:** `Compare Consolidated`  
**Categories (under Compare aggregator):** baselines, risk, lab, automation  
**Status:** Consolidation phase; optional router.

---

### Wave 20: Art Studio Run Orchestration – Bundle 31.0.27 (3 routers)
*Run artifact persistence for Art Studio + enhanced RMOS logs with runs_v2 integration.*

- `art_feasibility_router` — Art Studio feasibility (optional)
- `art_snapshot_router` — Art Studio snapshots v2 (optional)
- `rmos_logs_v2_router` — RMOS logs with runs_v2 integration (optional)

**Prefix:** `/api/art`, `/api/rmos`  
**Tags:** `Art Studio`, `Feasibility`, `Snapshots v2`, `RMOS Logs v2`  
**Status:** Optional; integrates with Wave 14 runs_v2.

---

### Wave 21: Acoustics Bundle Import (1 router)
*Tap tone measurement ingestion from field captures.*

- `rmos_acoustics_router` — Acoustics import/management (optional)

**Prefix:** `/api/rmos/acoustics` (built-in)  
**Endpoints:** `POST /api/rmos/acoustics/import-zip`, `POST /api/rmos/acoustics/import-path`  
**Tags:** `RMOS`, `Acoustics`

---

### Wave 22: Runs v2 Acoustics Advisory Surface (1 router)
*Advisory surface for acoustic runs in v2 framework.*

- `runs_v2_acoustics_router` — Acoustics advisory (optional)

**Prefix:** `/api/rmos/acoustics`  
**Endpoints:** 
- `GET /api/rmos/acoustics/runs/{run_id}/advisories`
- `GET /api/rmos/acoustics/advisories/{advisory_id}`
- `GET /api/rmos/acoustics/attachments/{sha256}`

**Tags:** `RMOS`, `Acoustics`

---

## Meta / Introspection (3 routers)

*Governance and self-awareness endpoints.*

- `routing_truth_router` — Canonical endpoint registry (confirms mounted routes post-deploy)
- `governance_router` — Governance metrics and legacy usage tracking (H5.1)
- `metrics_router` — Prometheus metrics (no prefix; accessible at `/metrics`)

**Tags:** `_meta`, `Governance`

---

## Health Checks (2 built-in endpoints)

- `GET /health` — Basic health check
- `GET /api/health` — API health with router summary (counts all 116 working routers)

---

## Key Notes for Developers

### Router Import Pattern
Most routers use a safe import pattern to avoid breaking the whole app on missing dependencies:

```python
try:
    from .module import router as name_router
except ImportError as e:
    print(f"Warning: Name router not available: {e}")
    name_router = None

# Later, when registering:
if name_router:
    app.include_router(name_router, prefix="/api/...", tags=[...])
```

### Router Prefix Rules
- **Static prefix:** defined in `main.py` at `include_router()`
- **Built-in prefix:** router defines its own prefix internally; `main.py` passes empty prefix or no prefix argument
- Always check the router module if unsure; grep for `prefix=` in the router file

### Wave Organization Philosophy
Waves are deployment bundles; they represent feature rollouts and conceptual groupings:
- **Waves 0–6:** Foundation and specialty modules
- **Waves 7–13:** Feature expansion (calculators, analytics, automation)
- **Waves 14–15:** Intelligence (vision, art studio)
- **Waves 16–17:** Governance and session management
- **Waves 18–19:** Consolidation (aggregating dispersed routers)
- **Waves 20–22:** Run orchestration and acoustics

### Optional Routers
Routers in `_experimental`, `art_studio`, `rmos.api`, and `workflow` are typically optional:
- Import wrapped in try/except
- Only registered if `if router:` check passes
- Safe to disable via ImportError or missing dependencies
- Document expected failure mode in `main.py` comment

### Feature Flags
- **`RMOS_RUNS_V2_ENABLED`** (default: `true`) — chooses runs v1 (legacy) vs v2 (governance-compliant, date-partitioned)
  - Set to `"false"` in environment to rollback to v1

### Canonical Schemas
- **CAM Intent Envelope:** `app.rmos.cam.CamIntentV1` — do not create alternate top-level envelopes; embed mode-specific `design` shapes under this single envelope
- **CI Validation:** run `python -m app.ci.check_cam_intent_schema_hash` to validate the schema hash

### Deprecated/Shadow Endpoints
- See `governance/` middleware and `meta/router_truth_routes.py` for canonical endpoint registry
- `DeprecationHeadersMiddleware` emits `X-Deprecated` headers for legacy lanes
- Use `EndpointGovernanceMiddleware` (H4) for logging warnings on legacy endpoints

---

## Summary Statistics

```
Core CAM:                          11 routers
RMOS + Specialty (Waves 1–6):      12 routers
Feature Expansion (Waves 7–13):    49 routers
Intelligence (Waves 14–15):         9 routers
Governance & Sessions (Waves 16–17):  8 routers
Consolidation (Waves 18–19):        5 routers
Run Orchestration & Acoustics (Waves 20–22):  4 routers
Meta / Introspection:               3 routers
────────────────────────────────────────
TOTAL WORKING:                     ~116 routers

Previously Broken (Now Fixed):      9 routers
Phantom Imports (Removed):         84 routers
```

---

## See Also

- [.github/copilot-instructions.md](.github/copilot-instructions.md) — AI agent instructions and codebase patterns
- [services/api/app/main.py](services/api/app/main.py) — Full router registration code with inline comments
- [services/api/app/governance/](services/api/app/governance/) — Endpoint governance policies
- [services/api/app/meta/](services/api/app/meta/) — Router truth and self-awareness endpoints
- [docs/ENDPOINT_TRUTH_MAP.md](docs/ENDPOINT_TRUTH_MAP.md) — Complete API surface documentation

---

## H7.2: CAM Intent Implementation

> **Added 2025-12-27**: Intent-native CAM endpoints with strict mode validation.

### Overview

H7.2 introduces intent-native CAM endpoints that use the canonical `CamIntentV1` envelope. These endpoints normalize input, validate constraints, and emit Prometheus metrics.

### New Router

- `cam_roughing_intent_router` — Intent-native roughing G-code generation

**Prefix:** `/api/cam`
**Tags:** `CAM`, `Intent`

### Endpoints

| Method | Endpoint | Query Params | Description |
|--------|----------|--------------|-------------|
| POST | `/api/cam/roughing_gcode_intent` | `strict=bool` | Generate roughing G-code from `CamIntentV1` |

### Strict Mode (H7.2.3)

The `strict` query parameter controls validation behavior:

- `?strict=false` (default): Returns 200 with issues in response body
- `?strict=true`: Returns 422 if normalization produces any issues

```bash
# Non-strict (default) - tolerates issues
curl -X POST http://localhost:8000/api/cam/roughing_gcode_intent \
  -H "Content-Type: application/json" \
  -d '{"design": {...}}'

# Strict - rejects on issues
curl -X POST "http://localhost:8000/api/cam/roughing_gcode_intent?strict=true" \
  -H "Content-Type: application/json" \
  -d '{"design": {...}}'
```

### Prometheus Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `cam_roughing_intent_requests_total` | Counter | Total requests |
| `cam_roughing_intent_issues_total` | Counter | Requests with normalization issues |
| `cam_roughing_intent_strict_rejects_total` | Counter | Strict mode rejections |
| `cam_roughing_intent_latency_ms` | Histogram | Request latency |

### Test Coverage

- `test_cam_roughing_intent_strict.py` — Strict mode behavior tests
- `test_roughing_gcode_intent_metrics.py` — Metrics emission tests
- `test_cam_intent_strict_reject_logs_request_id.py` — Request ID logging tests

---

## ADR-003 Phase 5: Feedback Loop Infrastructure

> **Added 2025-12-31**: Complete feedback loop infrastructure for OPERATION lane.

### Overview

Phase 5 completes the ADR-003 CAM OPERATION Lane Promotion by adding feedback loops for job logging, learning events, and metrics rollups. This enables closed-loop optimization of machining parameters.

### Module Location

```
services/api/app/rmos/pipeline/feedback/
├── __init__.py      # Package exports
├── schemas.py       # Pydantic models for feedback artifacts
├── config.py        # Feature flag configuration
├── job_log.py       # Job logging service
├── learning.py      # Learning event and decision service
└── rollups.py       # Metrics rollup service
```

### Key Components

| Component | Description |
|-----------|-------------|
| `JobLogService` | Records operator feedback, auto-triggers hooks |
| `LearningService` | Emits learning events, manages accept/reject decisions |
| `RollupService` | Aggregates time, yield, and event metrics |
| `FeedbackConfig` | Environment-based feature flag configuration |

### Feature Flags

All hooks default to OFF for safety. Enable per-tool via environment:

```bash
# Enable for roughing tool type
ROUGHING_LEARNING_HOOK_ENABLED=true
ROUGHING_METRICS_ROLLUP_HOOK_ENABLED=true
ROUGHING_APPLY_ACCEPTED_OVERRIDES=false  # Careful: affects future executions
```

### Signal Detection

The learning service detects quality signals from metrics and notes:

| Signal | Detection | Suggested Action |
|--------|-----------|------------------|
| `burn` | `metrics.burn=true` or "burn" in notes | Reduce feed, increase RPM |
| `tearout` | `metrics.tearout=true` or "tear" in notes | Reduce DOC, adjust feed direction |
| `kickback` | `metrics.kickback=true` or "kickback" in notes | Reduce feed rate |
| `chatter` | `metrics.chatter=true` or "chatter" in notes | Adjust RPM, reduce DOC |
| `tool_wear` | `metrics.tool_wear=true` or "wear" in notes | Schedule tool change |
| `excellent` | "excellent" or "perfect" in notes | Mark current params as good |

### Learning Workflow

1. Operator submits job log with status and metrics
2. If `LEARNING_HOOK_ENABLED`, learning event auto-emitted
3. Learning event contains suggested multipliers per signal
4. Operator reviews and accepts/rejects via decision endpoint
5. Accepted decisions stored in JSONL for future context resolution
6. If `APPLY_ACCEPTED_OVERRIDES`, multipliers applied to matching contexts

### Exports

Available from `rmos.pipeline` or `rmos`:

```python
from rmos.pipeline import (
    # Schemas
    JobLogStatus, JobLogMetrics, QualitySignal, LearningMultipliers,
    LearningSuggestion, LearningEvent, LearningDecision, MetricsRollup,
    # Services
    JobLogService, LearningService, RollupService,
    # Convenience functions
    write_job_log, emit_learning_event, create_learning_decision,
    compute_execution_rollup, persist_execution_rollup,
)
```

---

## Change Log

### 2026-01-03: Adaptive Pocket CI Fixes

**Telemetry Router Fix (`cam_logs_router`):**

| Issue | Resolution |
|-------|------------|
| `/api/cam/logs/write` returning 500 | Fixed SQLite schema issues in `cam_logs.py` |
| `limit` column causing SQL errors | Quoted as `"limit"` (SQL reserved keyword) |
| Tables missing if DB file exists | `open_db()` now always runs DDL |

**CI Workflow Fixes (`adaptive_pocket.yml`):**

| Test | Issue | Fix |
|------|-------|-----|
| M.3 heat_timeseries | 404 "profile not found" | Changed `machine_profile_id` from `"default"` to `"GRBL_3018_Default"` |
| M.3 bottleneck CSV | CRLF line endings | Changed `split('
')` to `splitlines()` |
| M.4 logs write | 500 error | Fixed SQLite issues (see above) |

**Valid Machine Profile IDs:**

Tests must use profiles from `assets/machine_profiles.json`:
- `GRBL_3018_Default`
- `Mach4_Router_4x8`
- `LinuxCNC_KneeMill`

---

### 2026-01-02: PR #3 CI Fixes (feature/cnc-saw-labs merge)

**Router Fixes:**

| Router | Issue | Fix |
|--------|-------|-----|
| `tooling_router` | Double prefix (`/api/tooling/tooling/*`) | Removed internal `prefix="/tooling"` |
| `cam_sim_router` | Path confusion | Documented: internal `/cam` prefix means full path is `/api/sim/cam/*` |

**Module-Level Directory Creation Pattern:**

Fixed Docker container crashes caused by module-level `os.makedirs()` calls. Affected files:

- `art_studio_rosette_store.py` - Added `_ensure_db_dir()` helper
- `learn/overrides_learner.py` - Moved mkdir to function scope
- `compare_baseline_store.py` - Lazy directory creation
- `tool_db.py` - Lazy directory creation
- Various routers - Lazy directory creation pattern

**Utility Function Update:**

`util/names.py:safe_stem()` now accepts optional `prefix` parameter:

```python
def safe_stem(filename: str, prefix: str = None) -> str:
    # Returns sanitized stem, optionally prefixed
    # safe_stem("job.nc", prefix="energy") -> "energy_job"
```

**CI Workflow Fixes:**

| Workflow | Fix |
|----------|-----|
| `containers.yml` | Changed simulate endpoint to `/api/sim/cam/simulate_gcode` |
| `proxy_parity.yml` | Added debug logging, case-insensitive grep for post-processor checks |
| `proxy_adaptive.yml` | Added debug logging for container failures |

---

### 2025-12-31

**ADR-003 Phase 5: Feedback Loop Infrastructure**
- Added `rmos/pipeline/feedback/` module with complete feedback loop infrastructure
- New schemas: `JobLogStatus`, `JobLogMetrics`, `QualitySignal`, `LearningMultipliers`, `LearningSuggestion`, `LearningEvent`, `LearningDecision`, `MetricsRollup`
- Feature flag configuration: `{TOOL}_LEARNING_HOOK_ENABLED`, `{TOOL}_METRICS_ROLLUP_HOOK_ENABLED`, `{TOOL}_APPLY_ACCEPTED_OVERRIDES`
- Job log service with auto-triggered hooks for learning and rollups
- Learning service with signal detection, suggestion generation, and accept/reject gate
- Metrics rollup service for time, yield, and event count aggregation
- All hooks default to OFF for safety

**ADR-003 Complete:**
- Phase 1: Artifact Wrapper ✅
- Phase 2: Feasibility Gate ✅
- Phase 3: Move Standardization ✅
- Phase 4: Full Pipeline ✅
- Phase 5: Feedback Loops ✅

See `docs/adr/ADR-003-cam-operation-lane-promotion.md` for full implementation details.

### 2025-12-27

**Routing Fixes:**
- Fixed Compare router variable collision (`legacy_compare_router` vs `compare_router`)
- Added "Legacy" tags to 19 overlapping routes (CAM, Compare, Rosette)
- Enhanced `EndpointGovernanceMiddleware` to auto-detect "Legacy" FastAPI tags

**H7.2 CAM Intent:**
- H7.2.2: Added `roughing_gcode_intent` endpoint with normalization and metrics
- H7.2.3: Added strict mode (`?strict=true`) for validation enforcement
- Added `cam_roughing_intent_strict_rejects_total` Prometheus counter
- Added test coverage for strict mode behavior

**Documentation:**
- Added "Canonical vs Legacy Lanes" section to ROUTER_MAP.md
- Updated ENDPOINT_TRUTH_MAP.md with CAM consolidated and intent endpoints
- Documented governance integration for legacy route tracking

**CI Gate:**
- Added `legacy_usage_gate.py` for frontend legacy usage detection
- Integrated into `.github/workflows/rmos_ci.yml`
- Budget set to 10 during transition period

**Frontend Audit Results:**
- 8 legacy usages found in 4 files
- Files: DrillingLab.vue, CAMEssentialsLab.vue, useRosettePatternStore.ts, BridgeLabView.vue
- See ENDPOINT_TRUTH_MAP.md for full migration list

### 2025-12-20

- Wave 18-19 consolidation (CAM + Compare routers)
- Fixed 9 previously broken routers
- Removed 84 phantom imports

---

## Frontend Legacy Usage CI Gate

> **Added 2025-12-27**: Automated detection of legacy API usage in frontend code.

### How It Works

The `legacy_usage_gate.py` CI script:
1. Scans `packages/client/src` and `packages/sdk/src` for API paths
2. Matches paths against known legacy patterns
3. Reports usage and fails if over budget

### Configuration

In `.github/workflows/rmos_ci.yml`:

```yaml
- name: Frontend legacy usage gate
  env:
    LEGACY_USAGE_BUDGET: "10"  # Adjust as migration progresses
  run: |
    python -m app.ci.legacy_usage_gate \
      --roots "../../packages/client/src" "../../packages/sdk/src" \
      --budget ${LEGACY_USAGE_BUDGET}
```

### Reducing the Budget

As frontend migration progresses:
1. Fix legacy usages in frontend code
2. Reduce `LEGACY_USAGE_BUDGET` in CI workflow
3. Goal: Set to `0` when migration complete

### Adding New Legacy Patterns

Edit `services/api/app/ci/legacy_usage_gate.py`:

```python
LEGACY_ROUTES: List[Tuple[str, str, str]] = [
    # (regex_pattern, canonical_replacement, notes)
    (r"^/api/old/path", "/api/new/path", "Migration notes"),
]
```
