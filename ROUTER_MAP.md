# Luthier's ToolBox Router Roadmap

**Last Updated:** 2025-12-20  
**Total Routers:** ~116 working routers organized across 22 waves  
**Status:** All previously-broken routers (9) fixed; 84 phantom imports removed  

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
