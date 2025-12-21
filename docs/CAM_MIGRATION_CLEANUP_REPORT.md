# CAM Router Migration - Cleanup Report

**Generated:** December 20, 2025
**Purpose:** Itemized list of files requiring attention post-migration

---

## 1. Legacy Router Files (29 files)

These files can be removed once the transition period ends. Currently preserved for backward compatibility.

| File | Category | New Location |
|------|----------|--------------|
| `routers/cam_adaptive_benchmark_router.py` | utility | `cam/routers/utility/benchmark_router.py` |
| `routers/cam_backup_router.py` | utility | `cam/routers/utility/backup_router.py` |
| `routers/cam_biarc_router.py` | toolpath | `cam/routers/toolpath/biarc_router.py` |
| `routers/cam_compare_diff_router.py` | utility | `cam/routers/utility/compare_router.py` |
| `routers/cam_drill_pattern_router.py` | drilling | `cam/routers/drilling/pattern_router.py` |
| `routers/cam_drill_router.py` | drilling | `cam/routers/drilling/drill_router.py` |
| `routers/cam_dxf_adaptive_router.py` | export | `cam/routers/export/dxf_router.py` (proxy) |
| `routers/cam_fret_slots_export_router.py` | fret_slots | `cam/routers/fret_slots/` (proxy) |
| `routers/cam_fret_slots_router.py` | fret_slots | `cam/routers/fret_slots/` (proxy) |
| `routers/cam_helical_v161_router.py` | toolpath | `cam/routers/toolpath/helical_router.py` |
| `routers/cam_learn_router.py` | - | Not migrated (standalone) |
| `routers/cam_logs_router.py` | monitoring | `cam/routers/monitoring/logs_router.py` |
| `routers/cam_metrics_router.py` | monitoring | `cam/routers/monitoring/metrics_router.py` |
| `routers/cam_opt_router.py` | utility | `cam/routers/utility/optimization_router.py` |
| `routers/cam_pipeline_preset_run_router.py` | pipeline | `cam/routers/pipeline/` (proxy) |
| `routers/cam_pipeline_router.py` | pipeline | `cam/routers/pipeline/` (proxy) |
| `routers/cam_polygon_offset_router.py` | utility | `cam/routers/utility/polygon_router.py` |
| `routers/cam_post_v155_router.py` | export | `cam/routers/export/post_router.py` (proxy) |
| `routers/cam_relief_router.py` | relief | `cam/routers/relief/` (proxy) |
| `routers/cam_relief_v160_router.py` | relief | `cam/routers/relief/` (proxy) |
| `routers/cam_risk_aggregate_router.py` | risk | `cam/routers/risk/` (proxy) |
| `routers/cam_risk_router.py` | risk | `cam/routers/risk/` (proxy) |
| `routers/cam_roughing_router.py` | toolpath | `cam/routers/toolpath/roughing_router.py` |
| `routers/cam_settings_router.py` | utility | `cam/routers/utility/settings_router.py` |
| `routers/cam_sim_router.py` | simulation | `cam/routers/simulation/gcode_sim_router.py` |
| `routers/cam_simulate_router.py` | simulation | `cam/routers/simulation/upload_router.py` |
| `routers/cam_smoke_v155_router.py` | - | Not migrated (standalone) |
| `routers/cam_svg_v160_router.py` | export | `cam/routers/export/svg_router.py` (proxy) |
| `routers/cam_vcarve_router.py` | toolpath | `cam/routers/toolpath/vcarve_router.py` |

---

## 2. Files with Deprecation Notices (2 files)

These files have DEPRECATED notices added in the docstrings:

| File | Notice |
|------|--------|
| `routers/art_studio_rosette_router.py` | Migrated to `art_studio/api/rosette_jobs_routes.py` and `rosette_compare_routes.py` |
| `routers/rosette_pattern_router.py` | Migrated to `art_studio/api/rosette_pattern_routes.py` |

---

## 3. Client Files Using Legacy API Paths (38 files)

These client files reference `/api/cam/` endpoints and may need updating to use new consolidated paths.

### High Priority (Core API Clients)

| File | Endpoints Used |
|------|----------------|
| `packages/client/src/api/adaptive.ts` | `/api/cam/pocket/adaptive/plan`, `/gcode`, `/sim` |
| `packages/client/src/api/camRisk.ts` | `/api/cam/risk/reports` |
| `packages/client/src/api/job_int.ts` | `/api/cam/job-int/log`, `/favorites` |
| `packages/client/src/api/n15.ts` | `/api/cam/gcode/*` |
| `packages/client/src/stores/fretSlotsCamStore.ts` | `/api/cam/fret_slots/preview` |
| `packages/client/src/stores/instrumentGeometryStore.ts` | `/api/cam/fret_slots/preview` |

### Medium Priority (Lab Components)

| File | Endpoints Used |
|------|----------------|
| `packages/client/src/labs/ReliefKernelLab.vue` | `/api/cam/relief/*`, `/api/cam/jobs/risk_report` |
| `packages/client/src/components/AdaptivePocketLab.vue` | `/api/cam/pocket/adaptive/*`, `/api/cam/opt/*`, `/api/cam/metrics/*`, `/api/cam/logs/*`, `/api/cam/learn/*` |
| `packages/client/src/components/DrillingLab.vue` | `/api/cam/drill/gcode` |
| `packages/client/src/views/AdaptiveLabView.vue` | `/api/cam/pocket/adaptive/plan` |
| `packages/client/src/views/lab/AdaptiveKernelLab.vue` | `/api/cam/pocket/adaptive/plan`, `/plan_from_dxf` |
| `packages/client/src/views/lab/ReliefKernelLab.vue` | `/api/cam/relief/heightfield_plan` |

### Lower Priority (Views & Panels)

| File | Endpoints Used |
|------|----------------|
| `packages/client/src/views/BridgeLabView.vue` | `/api/cam/dxf_adaptive_plan_run`, `/api/cam/posts`, `/api/cam/roughing_gcode`, `/api/cam/simulate_gcode` |
| `packages/client/src/views/CamSettingsView.vue` | `/api/cam/settings/summary`, `/export`, `/import` |
| `packages/client/src/views/PipelineLab.vue` | `/api/cam/blueprint/*` |
| `packages/client/src/views/PipelinePresetRunner.vue` | `/api/cam/pipeline/presets/*/run` |
| `packages/client/src/views/MachineListView.vue` | `/api/cam/machines` |
| `packages/client/src/views/PostListView.vue` | `/api/cam/posts` |
| `packages/client/src/views/PresetHubView.vue` | `/api/cam/job-int/log` |
| `packages/client/src/views/cam/RiskPresetSideBySide.vue` | `/api/cam/jobs/risk_report` |
| `packages/client/src/views/cam/RiskTimelineRelief.vue` | `/api/cam/jobs/risk_report` |
| `packages/client/src/views/labs/CompareLab.vue` | `/api/cam/compare/diff` |
| `packages/client/src/views/labs/CompareLabView.vue` | `/api/cam/compare/diff` |
| `packages/client/src/views/ArtJobTimeline.vue` | `/api/cam/risk/reports_index` |
| `packages/client/src/components/BridgeCalculatorPanel.vue` | `/api/cam/bridge/presets`, `/export_dxf` |
| `packages/client/src/components/CamBackupPanel.vue` | `/api/cam/backup/list`, `/snapshot`, `/download` |
| `packages/client/src/components/CamBridgePreflightPanel.vue` | `/api/cam/blueprint/preflight` |
| `packages/client/src/components/CamBridgeToPipelinePanel.vue` | `/api/cam/pipeline/presets` |
| `packages/client/src/components/CamJobInsightsPanel.vue` | `/api/cam/job_log/insights` |
| `packages/client/src/components/CamJobInsightsSummaryPanel.vue` | `/api/cam/job_log/insights` |
| `packages/client/src/components/cam/JobIntHistoryPanel.vue` | `/api/cam/job-int/log` |
| `packages/client/src/components/CompareAfModes.vue` | `/api/cam/pocket/adaptive/gcode`, `/batch_export` |
| `packages/client/src/components/GeometryOverlay.vue` | `/api/cam/simulate_gcode` |
| `packages/client/src/components/MachinePane.vue` | `/api/cam/pocket/adaptive/plan` |
| `packages/client/src/components/AdaptivePreview.vue` | `/api/cam/adaptive/spiral.svg`, `/trochoid.svg` |
| `packages/client/src/components/RosettePatternLibrary.vue` | `/api/cam/rosette/patterns/*` |
| `packages/client/src/components/RosettePhotoImport.vue` | `/api/cam/rosette/import_photo` |
| `packages/client/src/cnc_production/CompareRunsPanel.vue` | `/api/cam/job-int/log` |

### Toolbox Components

| File | Endpoints Used |
|------|----------------|
| `packages/client/src/components/toolbox/AdaptiveBenchLab.vue` | `/api/cam/adaptive2/*` |
| `packages/client/src/components/toolbox/CAMEssentialsLab.vue` | `/api/cam/roughing/gcode`, `/drill/gcode`, `/biarc/gcode`, `/probe/*`, `/retract/gcode` |
| `packages/client/src/components/toolbox/PolygonOffsetLab.vue` | `/api/cam/polygon_offset.nc` |
| `packages/client/src/components/toolbox/SimLab.vue` | `/api/cam/simulate_gcode` |
| `packages/client/src/components/toolbox/SimLabWorker.vue` | `/api/cam/simulate_gcode` |

---

## 4. Path Migration Reference

When updating client code, use this mapping:

| Old Path | New Path |
|----------|----------|
| `/api/cam/opt/*` | `/api/cam/utility/opt/*` |
| `/api/cam/settings/*` | `/api/cam/utility/settings/*` |
| `/api/cam/backup/*` | `/api/cam/utility/backup/*` |
| `/api/cam/compare/*` | `/api/cam/utility/compare/*` |
| `/api/cam/metrics/*` | `/api/cam/monitoring/metrics/*` |
| `/api/cam/logs/*` | `/api/cam/monitoring/logs/*` |
| `/api/cam/roughing/*` | `/api/cam/toolpath/roughing/*` |
| `/api/cam/biarc/*` | `/api/cam/toolpath/biarc/*` |
| `/api/cam/helical/*` | `/api/cam/toolpath/helical/*` |
| `/api/cam/vcarve/*` | `/api/cam/toolpath/vcarve/*` |
| `/api/cam/drill/*` | `/api/cam/drilling/*` |
| `/api/cam/simulate_gcode` | `/api/cam/simulation/upload` |
| `/api/cam/sim/*` | `/api/cam/simulation/*` |
| `/api/cam/svg/*` | `/api/cam/export/svg/*` |
| `/api/cam/post/*` | `/api/cam/export/post/*` |
| `/api/cam/dxf/*` | `/api/cam/export/dxf/*` |
| `/api/cam/relief/*` | `/api/cam/relief/*` |
| `/api/cam/risk/*` | `/api/cam/risk/*` |
| `/api/cam/fret_slots/*` | `/api/cam/fret_slots/*` |
| `/api/cam/pipeline/*` | `/api/cam/pipeline/*` |
| `/api/cam/rosette/*` | `/api/cam/rosette/*` |

---

## 5. Recommended Cleanup Sequence

### Phase A: Client Migration (Optional)
1. Update API client files in `packages/client/src/api/`
2. Update stores in `packages/client/src/stores/`
3. Update components and views
4. Test all CAM functionality

### Phase B: Remove Legacy Routers
1. Remove imports from `main.py` (Wave 1-13 sections)
2. Delete files in `routers/cam_*.py`
3. Update `cam/routers/` modules to use direct implementations instead of proxies

### Phase C: Final Cleanup
1. Remove deprecation notices from Art Studio routers
2. Update documentation
3. Remove this cleanup report

---

## 6. Notes

- **Backward compatibility is maintained** - all old paths still work
- **No breaking changes** - clients can migrate at their own pace
- **Proxies in place** - new modules delegate to existing routers during transition
- **Feature flag available** - `CAM_ROUTER_V2_ENABLED` can control behavior if needed
