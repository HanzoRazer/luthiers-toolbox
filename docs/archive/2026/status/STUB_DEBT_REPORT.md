# Stub Debt Report

**Generated**: 2026-02-23
**Summary**: 69 of 73 stub endpoints are actively used by frontend code
**Status**: Frontend has outpaced backend - stubs act as contracts for unimplemented features

---

## Overview

| Category | Stub Endpoints | Actively Used | Priority |
|----------|---------------|---------------|----------|
| RMOS Analytics | 5 | 5 | HIGH |
| RMOS Rosette | 6 | 6 | HIGH |
| RMOS Live Monitor | 2 | 2 | MEDIUM |
| CAM Backup | 2 | 2 | LOW |
| CAM Pocket/Adaptive | 4 | 4 | HIGH |
| CAM Drilling | 2 | 2 | MEDIUM |
| CAM Job Intelligence | 2 | 2 | MEDIUM |
| CAM Blueprint | 3 | 3 | MEDIUM |
| CAM Optimization | 2 | 2 | MEDIUM |
| CAM Relief | 4 | 3 | LOW |
| CAM Machines/Posts | 4 | 4 | MEDIUM |
| CAM Compare/Bridge | 4 | 4 | MEDIUM |
| CAM Risk/Logs | 4 | 4 | HIGH |
| CAM Fret Slots | 2 | 2 | LOW |
| AI Advisory | 3 | 3 | HIGH |
| AI CAM (experimental) | 3 | 3 | HIGH |
| Job Log (experimental) | 7 | 7 | HIGH |
| Art Rosette | 4 | 2 | LOW |
| **TOTAL** | **73** | **69** | - |

---

## HIGH PRIORITY (Core Workflow Blockers)

### 1. RMOS Analytics (`app/rmos/stub_routes.py`)

Frontend: `views/RmosAnalyticsView.vue`, `api/rmosAnalytics.ts`

| Endpoint | Method | Current Response | Backend Work Needed |
|----------|--------|------------------|---------------------|
| `/api/rmos/analytics/lane-analytics` | GET | `{"lanes": [], "total_runs": 0}` | Aggregate run data by operation lane, compute throughput/yield metrics |
| `/api/rmos/analytics/risk-timeline` | GET | `{"timeline": [], "risk_events": []}` | Build time-series of risk decisions, correlate with actual outcomes |
| `/api/rmos/analytics/summary` | GET | `{"total_runs": 0, ...}` | Compute aggregate statistics from run store |
| `/api/rmos/analytics/trends` | GET | `{"trends": []}` | Calculate rolling averages, detect anomalies |
| `/api/rmos/analytics/export` | GET | `{"export_url": null}` | Generate CSV/JSON export of analytics data |

**Implementation Notes**:
- These endpoints need to query `runs_v2/store.py` and aggregate data
- Consider caching for expensive aggregations
- Risk timeline should integrate with feasibility decision history

---

### 2. RMOS Rosette CNC (`app/rmos/stub_routes.py`)

Frontend: `components/rosette/RosetteDesigner.vue`, `api/rmosRosette.ts`

| Endpoint | Method | Current Response | Backend Work Needed |
|----------|--------|------------------|---------------------|
| `/api/rmos/rosette/segment-ring` | POST | `{"segments": [], "preview_svg": ""}` | Generate ring segments from design params |
| `/api/rmos/rosette/generate-slices` | POST | `{"slices": [], "toolpaths": []}` | Convert 2D design to 3D slice data for CNC |
| `/api/rmos/rosette/preview` | POST | `{"preview_url": "", "bounds": {}}` | Render SVG/PNG preview of design |
| `/api/rmos/rosette/export-cnc` | POST | `{"gcode": "", "job_id": ""}` | Generate G-code from rosette design |
| `/api/rmos/rosette/cnc-history` | GET | `{"jobs": []}` | List historical CNC jobs for rosette designs |
| `/api/rmos/rosette/cnc-job/{job_id}` | GET | `{"job": null}` | Get details of specific CNC job |

**Implementation Notes**:
- Rosette geometry engine exists in `art_studio/` - wire it up
- G-code generation should use existing CAM pipeline
- Jobs should persist to run store for traceability

---

### 3. AI CAM Advisory (`app/_experimental/ai_cam_router.py`)

Frontend: `stores/camAdvisorStore.ts`

| Endpoint | Method | Current Response | Backend Work Needed |
|----------|--------|------------------|---------------------|
| `/api/ai-cam/analyze-operation` | POST | `{"analysis": "stub", "suggestions": []}` | Call AI service to analyze CAM operation params |
| `/api/ai-cam/explain-gcode` | POST | `{"explanation": "stub"}` | Parse G-code and generate human-readable explanation |
| `/api/ai-cam/optimize` | POST | `{"optimized_params": {}, "improvements": []}` | Suggest feed/speed optimizations based on material/tool |

**Implementation Notes**:
- Wire to `ai/transport/` clients (OpenAI/Claude)
- Explanation should be deterministic when possible (rule-based first, AI fallback)
- MUST go through RMOS authority for any parameter changes

---

### 4. Job Log / Saw Lab (`app/_experimental/joblog_router.py`)

Frontend: `api/sawLab.ts`, `views/SawLabView.vue`

| Endpoint | Method | Current Response | Backend Work Needed |
|----------|--------|------------------|---------------------|
| `/api/joblog/saw_runs` | GET | `{"runs": []}` | Query saw run store with filters |
| `/api/joblog/saw_runs` | POST | `{"run_id": "stub-id", ...}` | Create new saw run record |
| `/api/joblog/saw_runs/{run_id}` | GET | `{"run_id": run_id, ...}` | Get specific run details |
| `/api/joblog/saw_runs/{run_id}` | PUT | `{"run_id": run_id, "updated": true}` | Update run (add metrics, status) |
| `/api/joblog/saw_runs/{run_id}` | DELETE | `{"deleted": true}` | Soft-delete run |
| `/api/joblog/saw_runs/{run_id}/telemetry` | POST | `{"recorded": true}` | Append telemetry data to run |
| `/api/joblog/saw_runs/batch` | POST | `{"batch_id": "stub", "runs": []}` | Create batch of related runs |

**Implementation Notes**:
- These mirror `runs_v2/` patterns - consider consolidating
- Telemetry ingestion should be append-only, high-throughput
- Batch operations for import/export workflows

---

### 5. CAM Risk & Metrics (`app/cam/routers/stub_routes.py`)

Frontend: `api/camMetrics.ts`, `views/CamRiskView.vue`

| Endpoint | Method | Current Response | Backend Work Needed |
|----------|--------|------------------|---------------------|
| `/api/cam/metrics/tool-wear` | GET | `{"tool_id": ..., "wear_estimate": 0}` | Track tool usage, estimate remaining life |
| `/api/cam/metrics/cycle-time` | GET | `{"job_id": ..., "estimated_minutes": 0}` | Calculate cycle time from toolpaths |
| `/api/cam/risk/assess` | POST | `{"risk_level": "unknown", "factors": []}` | Run feasibility rules on CAM params |
| `/api/cam/logs/run-history` | GET | `{"runs": []}` | Query CAM run history |

**Implementation Notes**:
- Risk assessment should delegate to `rmos/feasibility/engine.py`
- Tool wear tracking needs persistent storage (SQLite or run store)
- Cycle time estimation exists in toolpath module - expose it

---

## MEDIUM PRIORITY (Feature Enhancements)

### 6. CAM Pocket/Adaptive (`app/cam/routers/stub_routes.py`)

Frontend: `views/AdaptivePocketView.vue`, `api/camPocket.ts`

| Endpoint | Method | Current Response | Backend Work Needed |
|----------|--------|------------------|---------------------|
| `/api/cam/pocket/calculate` | POST | `{"toolpaths": [], "stats": {}}` | Generate pocket toolpaths |
| `/api/cam/pocket/preview` | POST | `{"preview_url": "", "bounds": {}}` | Render toolpath preview |
| `/api/cam/adaptive/calculate` | POST | `{"toolpaths": [], "engagement": []}` | Generate adaptive clearing paths |
| `/api/cam/adaptive2/status` | GET | `{"status": "not_implemented"}` | Status of adaptive2 engine |

**Implementation Notes**:
- Core pocket algorithm exists - needs API wrapper
- Adaptive clearing is complex - may require external lib integration

---

### 7. CAM Drilling (`app/cam/routers/stub_routes.py`)

Frontend: `components/cam/DrillingPanel.vue`

| Endpoint | Method | Current Response | Backend Work Needed |
|----------|--------|------------------|---------------------|
| `/api/cam/drilling/calculate` | POST | `{"toolpaths": [], "cycle_type": ""}` | Generate drill cycle G-code |
| `/api/cam/drilling/preview` | POST | `{"preview_url": ""}` | Render drill pattern preview |

---

### 8. CAM Job Intelligence (`app/cam/routers/stub_routes.py`)

Frontend: `views/JobIntelligenceView.vue`

| Endpoint | Method | Current Response | Backend Work Needed |
|----------|--------|------------------|---------------------|
| `/api/cam/job-int/analyze` | POST | `{"insights": [], "warnings": []}` | Analyze job for optimization opportunities |
| `/api/cam/job-int/compare` | POST | `{"differences": [], "recommendations": []}` | Compare two jobs |

---

### 9. CAM Blueprint (`app/cam/routers/stub_routes.py`)

Frontend: `views/BlueprintImportView.vue`

| Endpoint | Method | Current Response | Backend Work Needed |
|----------|--------|------------------|---------------------|
| `/api/cam/blueprint/analyze` | POST | `{"entities": [], "issues": []}` | Parse DXF/SVG and extract geometry |
| `/api/cam/blueprint/convert` | POST | `{"converted": {}, "warnings": []}` | Convert to internal geometry format |
| `/api/cam/blueprint/validate` | POST | `{"valid": true, "errors": []}` | Validate geometry for CAM |

---

### 10. CAM Optimization (`app/cam/routers/stub_routes.py`)

Frontend: `components/cam/OptimizationPanel.vue`

| Endpoint | Method | Current Response | Backend Work Needed |
|----------|--------|------------------|---------------------|
| `/api/cam/optimization/feeds-speeds` | POST | `{"recommended": {}, "rationale": ""}` | Calculate optimal feeds/speeds |
| `/api/cam/optimization/toolpath-order` | POST | `{"optimized_order": [], "savings": {}}` | Optimize toolpath ordering |

---

### 11. RMOS Live Monitor (`app/rmos/stub_routes.py`)

Frontend: `views/LiveMonitorView.vue`

| Endpoint | Method | Current Response | Backend Work Needed |
|----------|--------|------------------|---------------------|
| `/api/rmos/live/status` | GET | `{"active_jobs": [], "machine_states": {}}` | Real-time machine/job status |
| `/api/rmos/live/subscribe` | GET (SSE) | N/A | Server-sent events for live updates |

**Implementation Notes**:
- Requires WebSocket or SSE infrastructure
- May need machine integration layer

---

### 12. Machines & Posts (`app/cam/routers/stub_routes.py`)

Frontend: `views/MachineConfigView.vue`, `api/camMachines.ts`

| Endpoint | Method | Current Response | Backend Work Needed |
|----------|--------|------------------|---------------------|
| `/api/cam/machines` | GET | `{"machines": []}` | List configured machines |
| `/api/cam/machines/{id}` | GET | `{"machine": null}` | Get machine config |
| `/api/cam/posts` | GET | `{"posts": []}` | List post-processors |
| `/api/cam/posts/{id}/preview` | POST | `{"gcode_sample": ""}` | Preview post output |

---

### 13. Compare & Bridge (`app/cam/routers/stub_routes.py`)

Frontend: `views/CompareJobsView.vue`, `components/BridgeCalculator.vue`

| Endpoint | Method | Current Response | Backend Work Needed |
|----------|--------|------------------|---------------------|
| `/api/cam/compare/jobs` | POST | `{"comparison": {}}` | Compare two CAM jobs |
| `/api/cam/compare/toolpaths` | POST | `{"differences": []}` | Diff toolpath geometry |
| `/api/cam/bridge/calculate` | POST | `{"bridge_points": [], "gcode": ""}` | Calculate bridge/tab positions |
| `/api/cam/bridge/preview` | POST | `{"preview_url": ""}` | Preview bridges on geometry |

---

## LOW PRIORITY (Nice-to-Have)

### 14. CAM Backup (`app/cam/routers/stub_routes.py`)

| Endpoint | Method | Current Response | Backend Work Needed |
|----------|--------|------------------|---------------------|
| `/api/cam/backup/create` | POST | `{"backup_id": "", "created": ""}` | Snapshot current CAM state |
| `/api/cam/backup/restore` | POST | `{"restored": true}` | Restore from backup |

---

### 15. CAM Relief (`app/cam/routers/stub_routes.py`)

| Endpoint | Method | Current Response | Backend Work Needed |
|----------|--------|------------------|---------------------|
| `/api/cam/relief/generate` | POST | `{"heightfield": [], "toolpaths": []}` | Generate relief carving paths |
| `/api/cam/relief/preview` | POST | `{"preview_url": ""}` | 3D preview of relief |
| `/api/cam/relief/from-image` | POST | `{"heightfield": []}` | Convert image to heightfield |

**Note**: `/api/cam/relief/heightfield_plan` is UNUSED - candidate for removal.

---

### 16. CAM Probe (`app/cam/routers/stub_routes.py`)

| Endpoint | Method | Current Response | Backend Work Needed |
|----------|--------|------------------|---------------------|
| `/api/cam/probe/generate` | POST | `{"probe_gcode": "", "points": []}` | Generate surface probing routine |
| `/api/cam/probe/apply` | POST | `{"adjusted_gcode": ""}` | Apply probe data to toolpaths |

---

### 17. Fret Slots (`app/cam/routers/stub_routes.py`)

| Endpoint | Method | Current Response | Backend Work Needed |
|----------|--------|------------------|---------------------|
| `/api/cam/fret_slots/calculate` | POST | `{"slots": [], "gcode": ""}` | Calculate fret positions + G-code |
| `/api/cam/fret_slots/preview` | POST | `{"preview_url": ""}` | Visual preview of fret layout |

---

### 18. Art Rosette (`app/routers/misc_stub_routes.py`)

| Endpoint | Method | Current Response | Backend Work Needed |
|----------|--------|------------------|---------------------|
| `/api/art/rosette/analyze` | POST | `{"analysis": {}}` | Analyze rosette design |
| `/api/art/rosette/generate` | POST | `{"design": {}, "svg": ""}` | Generate rosette from params |

**Note**: `/api/art/rosette/presets` and `/api/art/rosette/save` are now WIRED to real implementations in `rosette_jobs_routes.py` (as of 2026-03).

---

## Unused Endpoints (Remediated)

**Status**: All previously identified dead endpoints have been addressed as of 2026-03-15.

| Endpoint | Original File | Status |
|----------|---------------|--------|
| `/api/rmos/presets/{preset_id}/promote` | `stub_routes.py` | REMOVED (file no longer exists) |
| `/api/cam/relief/heightfield_plan` | `stub_routes.py` | REMOVED (file no longer exists) |
| `/api/art/rosette/presets` | `misc_stub_routes.py` | WIRED to `rosette_jobs_routes.py:274` |
| `/api/art/rosette/save` | `misc_stub_routes.py` | WIRED to `rosette_jobs_routes.py:201` |
| `/api/v1/art/rosette/presets` | `api_v1/art_studio.py` | REMOVED 2026-03-15 (dead stub) |

---

## Implementation Strategy

### Phase 1: Core Workflows (Weeks 1-2)
1. **RMOS Analytics** - Wire to existing run store aggregations
2. **Job Log CRUD** - Consolidate with runs_v2 or implement parallel store
3. **CAM Risk Assessment** - Delegate to feasibility engine

### Phase 2: CNC Generation (Weeks 3-4)
1. **Rosette CNC Export** - Wire existing art_studio geometry to CAM pipeline
2. **AI CAM Advisory** - Connect to AI transport layer with RMOS guardrails

### Phase 3: Feature Completion (Weeks 5-8)
1. Pocket/Adaptive toolpath generation
2. Machine/Post configuration management
3. Live monitoring infrastructure

### Phase 4: Polish (Ongoing)
1. Blueprint analysis/conversion
2. Optimization suggestions
3. Relief carving (complex, may defer)

---

## Metrics

- **Total Stub Endpoints**: 72 (was 73, removed 1 dead endpoint)
- **Actively Used**: 72 (100%) - all stubs now have frontend callers or real implementations
- **Safe to Remove**: 0 (remediation complete as of 2026-03-15)
- **Estimated Backend LOC**: ~8,000-12,000 to fully implement
- **Recommended First Sprint**: RMOS Analytics + Job Log (highest frontend usage)
