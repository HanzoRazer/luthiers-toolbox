# Repository Status Report
**Generated:** December 14, 2025  
**Branch:** `feature/client-migration`  
**Latest Commit:** `4003775`  
**Total Untracked Files:** 1,267

---

## 📋 Last 20 Commits (Most Recent First)

| Commit | Date | Description | Files Changed |
|--------|------|-------------|---------------|
| `4003775` | 2025-12-14 | **feat(api): Wire Waves 7-13 routers - 91 total routers** | 1 |
| `2bef7cf` | 2025-12-13 | docs: Add DATA_REGISTRY_QUICKREF.md (Phase 8) | 1 |
| `9e20c6f` | 2025-12-13 | test: Add data registry tests (Phase 7) | 3 |
| `5020a6f` | 2025-12-13 | feat: Add frontend registry integration (Phase 6) | 3 |
| `2ca1a08` | 2025-12-13 | feat: Add edition middleware for entitlement enforcement (Phase 5) | 3 |
| `3fcf2b1` | 2025-12-13 | feat: Add /api/registry endpoints (Phase 4) | 2 |
| `d5df4a1` | 2025-12-13 | refactor: Rename instrument_geometry/registry.py (Phase 3) | 2 |
| `14266c0` | 2025-12-13 | fix: Update RMOS feasibility modules | 2 |
| `12306ec` | 2025-12-13 | fix: Update CAM core modules | 4 |
| `1b38489` | 2025-12-13 | chore: Update machine and material data assets | 4 |
| `402f66e` | 2025-12-13 | chore: Update CI workflows and project config | 4 |
| `650f9fd` | 2025-12-13 | feat: Update frontend instrument geometry components | 3 |
| `dae38cb` | 2025-12-13 | feat: Update instrument geometry module with model loader | 20 |
| `1b5831c` | 2025-12-13 | feat: Integrate data registry into calculators (Phase 2) | 4 |
| `0a37355` | 2025-12-13 | feat: Add data registry package for edition-based entitlements | 20 |
| `c018747` | 2025-12-13 | refactor: Clean up main.py and fix router imports | 94 |
| `aa75894` | 2025-12-13 | chore: Remove 66 redundant summary/completion docs | 66 |
| `ec44950` | 2025-12-09 | docs: Add comprehensive Wave 15-18 integration summary | 1 |
| `0b49240` | 2025-12-09 | feat(wave15-16): Implement Instrument Geometry Designer Frontend | 6 |
| `25378c1` | 2025-12-09 | feat(wave17-18): Implement Fretboard CAM + Feasibility Fusion | 9 |

---

## 🧪 Test Results Summary

**Test Run:** `services/api/tests/`  
**Results:** 
- ✅ **Passed:** 159
- ❌ **Failed:** 138
- ⏭️ **Skipped:** 1
- **Total:** 298 tests

### Failed Test Categories

| Category | Count | Status |
|----------|-------|--------|
| `test_geometry_router.py` | 19 | Geometry import/export/parity |
| `test_helical_router.py` | 18 | Helical entry/arc/validation |
| `test_dxf_security_patch.py` | ~10 | DXF security rollback |
| `test_adaptive_router.py` | ~15 | Adaptive pocketing |
| `test_art_studio_*.py` | ~20 | Art studio components |
| `test_compare_*.py` | ~15 | Compare lab functions |
| `test_rmos_*.py` | ~10 | RMOS integration |
| Other | ~31 | Various modules |

**Root Causes (Common):**
- Missing pytest-cov plugin (coverage options in pytest.ini)
- Import errors in test fixtures
- Missing mock data/fixtures
- API endpoint changes not reflected in tests

---

## 📁 COMPLETE UNTRACKED FILES LIST (1,267 files)

### 🔴 PRIORITY 1: services/api/ (223 files)

#### services/api/app/ - Core Backend
```
services/api/app/ai_cam/
services/api/app/ai_core/
services/api/app/ai_graphics/
services/api/app/analytics/
services/api/app/api/
services/api/app/app/
services/api/app/art_studio/
services/api/app/art_studio_rosette_store.py
services/api/app/cad/
services/api/app/calculators/__init__.py
services/api/app/calculators/alternative_temperaments.py
services/api/app/calculators/bracing_calc.py
services/api/app/calculators/business/
services/api/app/calculators/fret_slots_export.py
services/api/app/calculators/rosette_calc.py
services/api/app/calculators/saw/
services/api/app/calculators/saw_bridge.py
services/api/app/calculators/suite/
services/api/app/calculators/tool_profiles.py
services/api/app/calculators/wiring/
services/api/app/cam/async_timeout.py
services/api/app/cam/dxf_limits.py
services/api/app/cam/dxf_upload_guard.py
services/api/app/cam/graph_algorithms.py
services/api/app/cam/helical_core.py
services/api/app/cam/modal_cycles.py
services/api/app/cam/polygon_offset_n17.py
services/api/app/cam/probe_patterns.py
services/api/app/cam/probe_svg.py
services/api/app/cam/retract_patterns.py
services/api/app/cam/rosette/
services/api/app/cam/spatial_hash.py
services/api/app/cam_core/
services/api/app/cnc_production/
services/api/app/config/
services/api/app/core/
services/api/app/create_sample_runs.py
services/api/app/data/__init__.py
services/api/app/data/cam_core/
services/api/app/data/cnc_production/
services/api/app/data/compare_risk_log.json
services/api/app/data/compare_risk_log.jsonl
services/api/app/data/pipeline_presets.json
services/api/app/data/posts/custom_posts.json
services/api/app/data/presets.json
services/api/app/data/risk_reports.jsonl
services/api/app/data/rosette_pattern_catalog.json
services/api/app/data/tool_library.json
services/api/app/data/tool_library.py
services/api/app/data/validate_tool_library.py
services/api/app/data_registry/system/tools/
services/api/app/generators/
services/api/app/infra/
services/api/app/instrument_geometry/body/catalog.json
services/api/app/instrument_geometry/body/detailed_outlines.py
services/api/app/instrument_geometry/body/dxf/
services/api/app/instrument_geometry/body/j45_bulge.py
services/api/app/instrument_geometry/specs/
services/api/app/ltb_calculators/
services/api/app/main_backup_20251213_080843.py
services/api/app/models/compare_baseline.py
services/api/app/models/compare_diff.py
services/api/app/models/rmos_subjob_event.py
services/api/app/models/sim_metrics.py
services/api/app/pipelines/
services/api/app/reports/
services/api/app/rmos/ai_policy.py
services/api/app/rmos/api/
services/api/app/rmos/api_ai_snapshots.py
services/api/app/rmos/api_constraint_profiles.py
services/api/app/rmos/api_logs_viewer.py
services/api/app/rmos/api_presets.py
services/api/app/rmos/api_profile_history.py
services/api/app/rmos/constraint_profiles.py
services/api/app/rmos/context.py
services/api/app/rmos/context_adapter.py
services/api/app/rmos/context_router.py
services/api/app/rmos/fret_cam_guard.py
services/api/app/rmos/generator_snapshot.py
services/api/app/rmos/logging_ai.py
services/api/app/rmos/logging_core.py
services/api/app/rmos/logs.py
services/api/app/rmos/messages.py
services/api/app/rmos/models.py
services/api/app/rmos/models/
services/api/app/rmos/presets.py
services/api/app/rmos/profile_history.py
services/api/app/rmos/saw_cam_guard.py
services/api/app/rmos/schemas_logs_ai.py
services/api/app/rmos/services/
services/api/app/routers/body_generator_router.py
services/api/app/routers/neck_generator_router.py
services/api/app/routers/temperament_router.py
services/api/app/schemas/cam_fret_slots.py
services/api/app/schemas/cam_fret_slots_export.py
services/api/app/schemas/cam_profile.py
services/api/app/schemas/cam_risk.py
services/api/app/schemas/dxf_guided_ops.py
services/api/app/schemas/export_requests.py
services/api/app/schemas/jig_template.py
services/api/app/schemas/job_log.py
services/api/app/schemas/manufacturing_plan.py
services/api/app/schemas/pipeline_handoff.py
services/api/app/schemas/relief.py
services/api/app/schemas/relief_sim.py
services/api/app/schemas/rmos_analytics.py
services/api/app/schemas/rmos_safety.py
services/api/app/schemas/rosette_pattern.py
services/api/app/schemas/strip_family.py
services/api/app/services/__init__.py
services/api/app/services/art_job_store.py
services/api/app/services/art_jobs_store.py
services/api/app/services/art_presets_store.py
services/api/app/services/baseline_storage.py
services/api/app/services/cam_backup_service.py
services/api/app/services/compare_baseline_store.py
services/api/app/services/compare_risk_aggregate.py
services/api/app/services/compare_risk_bucket_detail.py
services/api/app/services/compare_risk_log.py
services/api/app/services/geometry_diff.py
services/api/app/services/job_int_favorites.py
services/api/app/services/job_risk_store.py
services/api/app/services/jobint_artifacts.py
services/api/app/services/pipeline_ops_rosette.py
services/api/app/services/pipeline_preset_store.py
services/api/app/services/pipeline_spec_validator.py
services/api/app/services/preset_store.py
services/api/app/services/relief_kernels.py
services/api/app/services/relief_sim.py
services/api/app/services/relief_sim_bridge.py
services/api/app/services/risk_reports_store.py
services/api/app/services/rmos_stores.py
services/api/app/services/rosette_cam_bridge.py
services/api/app/services/sim_energy.py
services/api/app/stores/
services/api/app/telemetry/cam_logs.db
services/api/app/tests/calculators/
services/api/app/tests/instrument_geometry/
services/api/app/tests/rmos/
services/api/app/tests/test_art_studio_vcarve_router.py
services/api/app/tests/test_cam_fret_slots_export.py
services/api/app/tests/test_dxf_exporter_versions.py
services/api/app/tests/test_dxf_r12_roundtrip.py
services/api/app/tests/test_dxf_security_patch.py
services/api/app/tests/test_fan_fret_perpendicular.py
services/api/app/tests/test_tool_library_phase1.py
services/api/app/tests/test_tool_profiles.py
services/api/app/toolpath/__init__.py
services/api/app/toolpath/dxf_exporter.py
services/api/app/toolpath/dxf_io_legacy.py
services/api/app/toolpath/relief_geometry.py
services/api/app/toolpath/rosette_geometry.py
services/api/app/toolpath/saw_engine.py
services/api/app/toolpath/vcarve_toolpath.py
services/api/app/tools/
services/api/app/util/adaptive_geom.py
services/api/app/util/compare_automation_helpers.py
services/api/app/util/dxf_compat.py
services/api/app/util/gcode_emit_advanced.py
services/api/app/util/gcode_emit_basic.py
services/api/app/util/poly_offset_spiral.py
services/api/app/util/post_injection_helpers.py
services/api/app/util/presets_store.py
services/api/app/util/template_engine.py
services/api/app/websocket/
services/api/app/workflow/
```

#### services/api/ - Root Level
```
services/api/.coverage
services/api/None
services/api/art_studio.db
services/api/coverage.json
services/api/data/art_presets.json
services/api/data/backups/
services/api/data/cam_job_favorites.json
services/api/data/cam_job_log.jsonl
services/api/data/presets.json
services/api/data/presets/
services/api/data/rmos.db
services/api/openapi.json
services/api/pytest.ini
services/api/risk_bucket_test.csv
services/api/scripts/
services/api/start_server.bat
services/api/test_ai_integration.py
services/api/test_arch_patch.py
services/api/test_data_load.py
services/api/test_n14_fix.py
services/api/test_parser_fixes.py
services/api/test_rmos_integration.py
services/api/test_wave_e1.py
services/api/verify_n11_schema.py
```

#### services/api/tests/
```
services/api/tests/baseline_n18/
services/api/tests/conftest.py
services/api/tests/debug_adaptive.py
services/api/tests/debug_import_fix.py
services/api/tests/debug_import_format.py
services/api/tests/test_adaptive_router.py
services/api/tests/test_art_job_detail.py
services/api/tests/test_art_namespace.py
services/api/tests/test_art_presets.py
services/api/tests/test_art_presets_delete.py
services/api/tests/test_art_studio_bracing.py
services/api/tests/test_art_studio_inlay.py
services/api/tests/test_art_studio_rosette.py
services/api/tests/test_art_studio_rosette_compare.py
services/api/tests/test_bridge_router.py
services/api/tests/test_cam_compare_diff_router.py
services/api/tests/test_cam_pipeline_rosette_op.py
services/api/tests/test_compare_history_smoke.py
services/api/tests/test_compare_risk_aggregate.py
services/api/tests/test_compare_risk_bucket_detail.py
services/api/tests/test_compare_risk_bucket_export.py
services/api/tests/test_compare_risk_time_window.py
services/api/tests/test_curve_preflight_router.py
services/api/tests/test_dxf_security_patch.py
services/api/tests/test_geometry_router.py
services/api/tests/test_helical_router.py
services/api/tests/test_live_monitor_drilldown.py
services/api/tests/test_log.txt
services/api/tests/test_n18_spiral_gcode.py
services/api/tests/test_pipelines.py
services/api/tests/test_risk_reports_index.py
services/api/tests/test_rmos_safety.py
services/api/tests/test_rosette_cam_bridge.py
```

#### services/blueprint-import/
```
services/blueprint-import/
```

---

### 🔴 PRIORITY 2: packages/client/ (33 files)

```
packages/client/index.html
packages/client/package-lock.json
packages/client/package.json
packages/client/ROUTER_SETUP.md
packages/client/tsconfig.json
packages/client/tsconfig.node.json
packages/client/vite.config.ts
packages/client/src/App.vue
packages/client/src/main.ts
packages/client/src/cam_core/
packages/client/src/components/art/index.ts
packages/client/src/components/RosettePatternLibrary.vue
packages/client/src/components/RosettePhotoImport.vue
packages/client/src/models/
packages/client/src/stores/camAdvisorStore.ts
packages/client/src/stores/fretSlotsCamStore.ts
packages/client/src/stores/sawLearnStore.ts
packages/client/src/stores/toastStore.ts
packages/client/src/stores/useArtStudioEngine.ts
packages/client/src/stores/useDxfSliceStore.ts
packages/client/src/stores/useExportStore.ts
packages/client/src/stores/useJobLogStore.ts
packages/client/src/stores/useLiveMonitorStore.ts
packages/client/src/stores/useManufacturingPlanStore.ts
packages/client/src/stores/useRmosAnalyticsStore.ts
packages/client/src/stores/useRmosSafetyStore.ts
packages/client/src/stores/useRosetteDesignerStore.ts
packages/client/src/stores/useRosettePatternStore.ts
packages/client/src/stores/useStripFamilyStore.ts
packages/client/src/types/curvelab.ts
packages/client/src/types/fretSlots.ts
packages/client/src/types/rmos.ts
packages/client/src/types/sawLab.ts
```

---

### 🟡 PRIORITY 3: docs/ (76 files)

```
docs/B22_10_COMPARE_MODES.md
docs/B22_11_LAYER_AWARE_COMPARE.md
docs/B22_12_EXPORTABLE_DIFF_REPORTS.md
docs/B22_13_COMPARE_AUTOMATION_API.md
docs/B22_16_GOLDEN_REPORT_FUSION.md
docs/B22_16_GOLDEN_REPORT_FUSION_QUICKREF.md
docs/B22_8_IMPLEMENTATION_SUMMARY.md
docs/B22_8_SKELETON_INTEGRATION.md
docs/B22_8_TEST_SETUP.md
docs/B22_9_AUTOSCALE_ZOOM_TO_DIFF.md
docs/B26_BASELINE_MARKING_COMPLETE.md
docs/CAM_Core/
docs/Calculators/
docs/CLONE_PROJECT_DEVELOPER_HANDOFF.md
docs/CNC_PRESET_MANAGER_B20.md
docs/CNC_Saw_Blade_RFQ.md
docs/CNC_Saw_Lab/
docs/CNC_Saw_Lab_Conversation.md
docs/CNC_Saw_Lab_Technical.md
docs/COMPARE_LAB_B22_TEST_PLAN.md
docs/COMPARELAB_B22_8_GUARDRAIL_SYSTEM.md
docs/COMPARELAB_B22_ARC_COMPLETE.md
docs/COMPARELAB_BRANCH_WORKFLOW.md
docs/COMPARELAB_DEV_CHECKLIST.md
docs/COMPARELAB_GOLDEN_SYSTEM.md
docs/COMPARELAB_GUARDRAILS.md
docs/COMPARELAB_REPORTS.md
docs/DEVELOPER_HANDOFF_N16_COMPLETE.md
docs/DEVELOPER_ONBOARDING.md
docs/DEVELOPMENT_CHECKPOINT_GUIDE.md
docs/DEVELOPMENT_REVIEW_2025_11_25.md
docs/FEATURE_DOCUMENTATION_TRACKER.md
docs/GITHUB_ISSUE_TEMPLATES_QUICKSTART.md
docs/governance/
docs/Instrument_Geometry/
docs/Instrument_Geometry_Migration_Plan.md
docs/instrument/
docs/KnowledgeBase/
docs/MM_0_MIXED_MATERIAL_QUICKREF.md
docs/MM_2_CAM_PROFILES_QUICKREF.md
docs/MM_3_PDF_DESIGN_SHEETS_QUICKREF.md
docs/MM_4_MATERIAL_AWARE_ANALYTICS_QUICKREF.md
docs/MM_5_ULTRA_FRAGILITY_POLICY_QUICKREF.md
docs/MM_6_FRAGILITY_AWARE_LIVE_MONITOR_QUICKREF.md
docs/N9_0_ANALYTICS_COMPLETE.md
docs/N9_0_ANALYTICS_QUICKREF.md
docs/N9_1_ADVANCED_ANALYTICS_QUICKREF.md
docs/N9_1_ADVANCED_ANALYTICS_SUMMARY.md
docs/N10_0_REALTIME_MONITORING_QUICKREF.md
docs/N10_1_LIVEMONITOR_DRILLDOWN_QUICKREF.md
docs/N10_2_1_SAFETY_FLOW_INTEGRATION_QUICKREF.md
docs/N10_2_2_MENTOR_OVERRIDE_PANEL_QUICKREF.md
docs/N10_2_APPRENTICESHIP_MODE_QUICKREF.md
docs/N11_1_ROSETTE_SCAFFOLDING_QUICKREF.md
docs/N11_2_ROSETTE_GEOMETRY_SCAFFOLDING_QUICKREF.md
docs/N12_0_CORE_MATH_SKELETON_QUICKREF.md
docs/N12_1_API_WIRING_QUICKREF.md
docs/NECK_PROFILE_BUNDLE_ANALYSIS.md
docs/NECK_PROFILE_QUICKSTART.md
docs/OPTION_B_DAY1_SUMMARY.md
docs/products/
docs/PROJECTS_ON_HOLD_INVENTORY.md
docs/README_CAM_SETTINGS_BACKUP.md
docs/releases/
docs/RMOS/
docs/rmos_bundles.json
docs/RMOS_MASTER_TREE.md
docs/RMOS_N8_N10_ARCHITECTURE.md
docs/RMOS_Onboarding.md
docs/RMOS_PatchN_Consolidated.md
docs/RMOS_STUDIO_DEVELOPER_GUIDE.md
docs/specs/
docs/TEST_SESSION_REPORT_2025_11_25.md
docs/UI_NAVIGATION_AUDIT.md
docs/VALUE_ADDED_CODING_POLICY.md
```

---

### 🟡 PRIORITY 4: scripts/ (41 files)

```
scripts/audit_phantom_imports.py
scripts/cam_settings_roundtrip_smoke.ps1
scripts/clean_csv_encoding.py
scripts/commit_saw_lab_actual.ps1
scripts/convert_vtdb_to_machine_tools.py
scripts/Create-ProductRepos.ps1
scripts/Create-TestDummy.ps1
scripts/Enable-DevFirewall.ps1
scripts/export_vtdb.py
scripts/export_vtdb_full.py
scripts/Extract-Rosette.ps1
scripts/Find-ExpressFeatures.ps1
scripts/import_tools_direct.py
scripts/materials_csv_to_json.py
scripts/materials_json_to_csv.py
scripts/MaterialTools.ps1
scripts/migrate_presets_unified.py
scripts/profile_n17_polygon_offset.py
scripts/README_RMOS_CI.md
scripts/README_RMOS_TEST.md
scripts/release_n18_tag_and_notes.ps1
scripts/rmos_ci_test.py
scripts/setup_machine_with_tools.py
scripts/Setup-DevFirewall.ps1
scripts/split_carveco_records.py
scripts/test_instrument_geometry.py
scripts/test_rmos_full.sh
scripts/test_saw_lab_2_0.ps1
scripts/Test-Advanced-Analytics-N9_1.ps1
scripts/Test-Analytics-N9.ps1
scripts/Test-DirectionalWorkflow.ps1
scripts/Test-ProductRepos.ps1
scripts/Test-RepoHealth.ps1
scripts/Test-RMOS-AI-Core.ps1
scripts/Test-RMOS-AI.ps1
scripts/Test-RMOS-ArtStudio.ps1
scripts/Test-RMOS-Full.ps1
scripts/Test-RMOS-PipelineHandoff.ps1
scripts/Test-RMOS-Sandbox.ps1
scripts/Test-RMOS-SlicePreview.ps1
scripts/verify_import.py
```

---

### 🟡 PRIORITY 5: projects/ (1 directory)

```
projects/
```

---

### 🟢 REVIEW: Root Level Markdown/Documentation (~150 files)

```
ACTIONS_1_2_COMPLETE.md
AGENTS.md
AI_Profile_Tuning_Handoff.md
ARCHITECTURAL_EVOLUTION.md
ARCHITECTURE_DECISION_NODE_SCOPE.md
ARCHITECTURE_DRIFT_LESSONS.md
ART_STUDIO_BUNDLE5_BACKEND_COMPLETE.md
ART_STUDIO_BUNDLE5_QUICKREF.md
ART_STUDIO_CHECKPOINT_EVALUATION.md
ART_STUDIO_COMPLETE_VERIFICATION.md
ART_STUDIO_DEVELOPER_HANDOFF.md
ART_STUDIO_DUMP_BUNDLES_ANALYSIS.md
ART_STUDIO_QUICKREF.md
ART_STUDIO_ROADMAP.md
ART_STUDIO_V16_1_INTEGRATION_STATUS.md
ArtStudio_Bracing_Integration.md
B19_CLONE_AS_PRESET_INTEGRATION.md
B20_ENHANCED_TOOLTIPS_COMPLETE.md
B21_INTEGRATION_TEST_GUIDE.md
B21_MULTI_RUN_COMPARISON_COMPLETE.md
B21_MULTI_RUN_COMPARISON_QUICKREF.md
B21_ROUTE_REGISTRATION_GUIDE.md
BATCH3_UPLOAD_RECONCILIATION.md
BLUEPRINT_STANDALONE_EVALUATION.md
BLUEPRINT_TECTONIC_SHIFT_ANALYSIS.md
BRIDGE_LAB_QUICKREF.md
BUNDLE_10_OPERATOR_REPORT.md
BUNDLE_11_OPERATOR_REPORT_PDF.md
BUNDLE_12_UI_DOWNLOAD_BUTTON.md
BUNDLE_13_CNC_HISTORY_ADVANCED_SAFETY.md
BUNDLE_13_COMPLETE_ANALYSIS.md
CAD_SOFTWARE_EVALUATION.md
CALCULATOR_NAMESPACE_CONFLICT_ANALYSIS.md
Calculator_Spine_Overview.md
CALCULATORS_DIRECTORY_ANALYSIS.md
CAM_ENGINE_ANALYSIS_COMPLETE.md
CAM_ESSENTIALS_N0_N10_INTEGRATION_COMPLETE.md
CAM_ESSENTIALS_N0_N10_QUICKREF.md
CAM_ESSENTIALS_N0_N10_STATUS.md
CAM_ESSENTIALS_V1_0_RELEASE_NOTES.md
CAM_JOB_SYSTEM_IMPLEMENTATION.md
CAM_JobInt_Roadmap.md
CAM_PIPELINE_FINAL_SUMMARY.md
CHANGELOG.md
CNC_Saw_Lab_Handoff.md
CNC_SAW_LAB_MISSING_COMPONENTS_VISUAL.md
CNC_SAW_LAB_RECONCILIATION_REPORT.md
CODE_POLICY_ENFORCEMENT_PLAN.md
CODE_POLICY_VIOLATIONS_REPORT.md
COMPARE_MODE_BUNDLE_ROADMAP.md
COMPARE_MODE_DEVELOPER_HANDOFF.md
COMPLETE_CODE_EXTRACTION.md
COMPLETE_TESTING_STRATEGY.md
CP_S50_SAW_BLADE_REGISTRY.md
CP_S51_SAW_BLADE_VALIDATOR.md
CP_S53_SAW_OPERATION_PANELS.md
CURRENT_INIT_PY_CONTENTS.md
CURRENT_STATE_REALITY_CHECK.md
DASHBOARD_ENHANCEMENT_COMPLETE.md
DASHBOARD_ENHANCEMENT_QUICKREF.md
DATA_REGISTRY_INTEGRATION_PLAN.md
DATA_REGISTRY_PHASE1_COMPLETE.md
DATA_REGISTRY_PHASE2_COMPLETE.md
DEPRECATED_SUBSYSTEMS.md
DEV_CHECKLIST_ART_STUDIO_ROSETTE.md
DEV_ONBOARDING_CAM.md
DEV_QUICKSTART.md
Developer_Handoff_RMOS_AI_Ops_and_Profile_Tuning.md
DEVELOPER_HANDOFF_ROADMAP.md
DIRECTIONAL_WORKFLOW_2_0_QUICKREF.md
DOCUMENTATION_POLISH_SESSION_SUMMARY.md
DXF_SECURITY_PATCH_DEPLOYMENT_COMPLETE.md
DXF_SECURITY_PATCH_DEPLOYMENT_SUMMARY.md
DXF_SECURITY_PATCH_FINAL_REPORT.md
ENERGY_ANALYSIS_VERIFICATION.md
EXECUTION_PLAN.md
EXPORT_DRAWER_INTEGRATION_PHASE1.md
EXPRESS_EXTRACTION_GUIDE.md
EXTENSION_VALIDATION_QUICKREF.md
FINAL_EXTRACTION_SUMMARY.md
FINAL_INTEGRATION_TEST_CHECKLIST.md
FUNCTIONAL_VERIFICATION_MATRIX.md
GCODE_GENERATION_SYSTEMS_ANALYSIS.md
GITHUB_VERIFICATION_CHECKLIST.md
GITHUB_VERIFICATION_GUIDE.md
GLOBAL_GRAPHICS_INGESTION_STANDARD.md
GOLDEN_PATH_DEPLOYMENT_COMPLETE.md
GOLDEN_PATH_DEPLOYMENT_PLAN.md
HELICAL_V161_PRODUCTION_UPGRADE_PLAN.md
HELICAL_V161_STATUS_ASSESSMENT.md
IMPLEMENTATION_COMPLETE.md
instrument_Neck_Taper_DXF_Export.md
Instrument_Geometry_Migration_Plan.md
Instrument_Geometry_Wave_15_Instrument_Geometry_Data_Migration.md
INTEGRATION_AUDIT.md
JOB_INTELLIGENCE_BUNDLES_14_15_16_COMPLETE.md
LEAN_EXTRACTION_STRATEGY.md
LEGACY_ARCHIVE_POLICY.md
Legacy_Pipeline_Migration_Directive.md
LPMD_Checklist.md
LPMD_Migration_Report_Template.md
LTB_CALCULATOR_DEPLOYMENT_SUMMARY.md
MACHINE_ENVELOPE_QUICKREF.md
MAIN_PY_IMPORT_AUDIT_REPORT.md
MASTER_SEGMENTATION_STRATEGY.md
MERGE_VERIFICATION_REPORT.md
MULTI_OP_PIPELINE_PLAN.md
N0_UI_VALIDATION_CHECKLIST.md
N8_7_ARCHITECTURE.md
N8_7_MIGRATION_COMPLETE.md
N11_ROSETTE_SCAFFOLDING_PLAN.md
N12_ROSETTE_ENGINE_PLAN.md
N13_ROSETTE_UI_DEEP_INTEGRATION.md
N14_RMOS_CNC_PIPELINE.md
N14_VALIDATION_FIX_SUMMARY.md
N15_N18_IMPLEMENTATION_COMPLETE.md
N15_N18_SESSION_SUMMARY.md
N15_RMOS_PRODUCTION_PIPELINE.md
N16_N18_FRONTEND_DEVELOPER_HANDOFF.md
N18_DEPLOYMENT_CHECKLIST.md
N18_MISSING_COMPONENTS_ARCHITECTURE.md
N18_QUICKREF.md
N18_SPIRAL_POLYCUT_QUICKREF.md
N18_STATUS_REPORT.md
NECK_CONTEXT_WIRING_COMPLETE.md
NECKLAB_PRESET_LOADING_COMPLETE.md
NEXT_TASK_DECISION.md
OPTION_A_CODE_INVENTORY.md
OPTION_A_VALIDATION_REPORT.md
ORPHANED_CLIENT_FILES_INVENTORY.md
Orphaned_Client_Migration_Plan.md
P0_1_COMPLETION_CHECKLIST.md
P0_1_SHIPPED.md
P1_4_CAM_ESSENTIALS_PRODUCTION_RELEASE.md
P2_1_NECK_GENERATOR_COMPLETE.md
PATCH_N11_SCHEMA_FIX.md
PHANTOM_CLEANUP_CONFIRMATION.md
PHASE_1_2_PROGRESS_SUMMARY.md
PHASE_1_EXECUTION_PLAN.md
PHASE_2_QUICK_WINS_COMPLETE.md
PHASE_24_3_24_4_RELIEF_SIM_BRIDGE.md
PHASE_24_4_QUICKREF.md
PHASE_24_4_RELIEF_SIM_BRIDGE_FRONTEND.md
PHASE_24_5_MACHINE_ENVELOPE_INTEGRATION.md
PHASE_25_0_QUICKREF.md
PHASE_27_28_INTEGRATION_PLAN.md
PHASE_27_BUNDLE_13_COMPLETION.md
PHASE_27_COMPLETE_ANALYSIS.md
PHASE_27_UI_TEST_CHECKLIST.md
PHASE_28_1_INTEGRATION_COMPLETE.md
PHASE_28_2_TIMELINE_COMPLETE.md
PHASE_3_CAM_TYPE_HINTS_COMPLETE.md
PHASE_30_COMPLETION_PATCH.md
PHASE_31_ROSETTE_PARAMETRICS.md
PHASE_32_AI_DESIGN_LANE.md
PHASE_4_BATCH_2_COMPLETE.md
PHASE_4_BATCH_3_COMPLETE.md
PHASE_4_BATCH_3_SUMMARY.md
PHASE_4_BATCH_4_COMPLETE.md
PHASE_4_BATCH_5_COMPLETE.md
PHASE_4_BATCH_6_COMPLETE.md
PHASE_4_ROUTER_TYPE_HINTS_PROGRESS.md
PHASE_7_IMPACT_ANALYSIS.md
PHASE_B_SUMMARY.md
PHASE_D_E_DECISIONS.md
PHASE_E_IMPLEMENTATION_COMPLETE.md
PHASE1_DISCOVERY_TIMELINE.md
PHASE1_EXTRACTION_LOCATION_MISMATCH.md
PHASE1_EXTRACTION_STATUS.md
PHASE1_NEXT_STEPS.md
PHASE1_TYPESCRIPT_DISCOVERY.md
PHASE3_INTEGRATION_COMPLETE.md
PHASE5_PART2_N0_QUICKREF.md
PRIORITY_1_COMPLETE_STATUS.md
PRODUCT_REPO_SETUP.md
PRODUCT_SEGMENTATION_INDEX.md
PROFILE_N17_SANDBOX_PACKAGE.md
PROJECT_COMPLETE_SUMMARY.md
Questions_for_Developer_Review.md
REFORESTATION_PLAN.md
REPO_LAYOUT.md
REPO_STATUS_REPORT_2025-12-14.md
REPO_STRUCTURE_SUMMARY.md
REPOSITORY_ERROR_ANALYSIS.md
RMOS_2.0_Specification.md
RMOS_AI_Profile_Tuning_Handoff.md
RMOS_Developer_Onboarding.md
RMOS_Directional_Workflow_2_0.md
RMOS_MASTER_DEVELOPMENT_TRACKER.md
RMOS_MIGRATION_N8_7_QUICKREF.md
RMOS_STUDIO_ALGORITHMS.md
RMOS_STUDIO_API.md
RMOS_STUDIO_DATA_STRUCTURES.md
RMOS_STUDIO_FAQ.md
RMOS_STUDIO_MANUFACTURING_PLANNER.md
RMOS_STUDIO_SAW_PIPELINE.md
RMOS_STUDIO_SYSTEM_ARCHITECTURE.md
RMOS_STUDIO_TUTORIALS.md
RMOS_STUDIO_UI_LAYOUT.md
RMOS_STUDIO_WORKFLOW.md
RMOS_STUDIO.md
ROSETTE_ART_STUDIO_INTEGRATION.md
ROSETTE_ART_STUDIO_QUICKREF.md
ROSETTE_DESIGNER_REDESIGN_SPEC.md
ROSETTE_PATTERN_GENERATOR_DEPLOYMENT.md
ROSETTE_PHOTO_IMPORT_DEPLOYMENT.md
ROSETTE_REALITY_CHECK.md
ROSETTE_REDESIGN_QUICKREF.md
ROSETTE_ROUTER_TEST_BUNDLE_SUMMARY.md
Rosette_Template_Lab_Overview.md
Saw_Lab_2_0_Integration_Plan.md
SAW_LAB_2_0_QUICKREF.md
SAW_LAB_UNTRACKED_FILES_INVENTORY.md
Saw_Path_Planner_2_1_Upgrade_Plan.md
SawLab_2_0_Test_Hierarchy.md
SawLab_Saw_Physics_Debugger.md
SECURITY_PATCH_DXF_EVALUATION_REPORT.md
Segmentation_Checklist.md
SESSION_5_SUMMARY.md
STATE_PERSISTENCE_QUICKREF.md
TEAM_ASSEMBLY_ROADMAP.md
TECHNICAL_HANDOFF.md
TEMPLATE_ENGINE_QUICKREF.md
TEST_COVERAGE_KNOWN_ISSUES.md
TEST_COVERAGE_NEXT_STEPS.md
TEST_COVERAGE_PROGRESS.md
TEST_COVERAGE_QUICKREF.md
TEST_COVERAGE_SESSION_RESULTS.md
TEST_STATUS_REPORT.md
TESTING_QUICK_REFERENCE.md
Tool_Library_Audit_Checklist.md
Tool_Library_Migration_Plan.md
Tool_Library_Spec.md
TOOLBOX_CAM_ARCHITECTURE_v1.md
TOOLBOX_CAM_DEVELOPER_HANDOFF.md
UNIFIED_PRESET_INTEGRATION_STATUS.md
UNIFIED_PRESET_SYSTEM_PHASE1_COMPLETE.md
UNIT_CONVERSION_VALIDATION_COMPLETE.md
UNRESOLVED_TASKS_INVENTORY.md
UX_NAVIGATION_REDESIGN_TASK.md
VERIFICATION_SMOKE_TEST_RESULTS.md
WAVE_1_6_DEVELOPER_HANDOFF.md
Wave_12_AI_CAM_UI.md
WAVE_E1_CAM_SECTION_ANALYSIS.md
WAVE_E1_COMPLETE_SUMMARY.md
WAVE15_18_FILE_TREE.txt
WAVE16_PHASE_D_GAP_ANALYSIS.md
WAVE17_18_IMPLEMENTATION_PLAN.md
WAVE17_18_INTEGRATION_AUTHORITY.md
WAVE17_18_QUESTIONS_ANSWERED.md
WAVE17_TODO.md
WAVE19_COMPLETE_SUMMARY.md
WAVE19_FAN_FRET_CAM_IMPLEMENTATION.md
WAVE19_FOUNDATION_IMPLEMENTATION.md
WAVE19_QUICKREF.md
```

---

### 🟢 REVIEW: Root Level Python Files (~50 files)

```
ai_core_generator_constraints.py
ai_graphics_schemas.py
ai_graphics_schemas_ai_schemas.py
ai_graphics_sessions.py
ai_rmos_generator_snapshot.py
art_studio___init__.py
art_studio_constraint_search.py
art_studio_directional_workflow.py
art_studio_rmos_logs.py
art_studio_rmos_logs_2.py
art_studio_test_rmos_mode_preview.py
calculators_bracing_calc.py
calculators_router.py
calculators_saw_bite_load.py
calculators_saw_deflection.py
calculators_saw_heat.py
calculators_saw_kickback.py
calculators_saw_rimspeed.py
calculators_service.py
calculators_service_2.py
compare_automation_router.py
constraint_profiles_ai.py
convert-txt-to-csv.py
gcode_reader.py
generate_gallery.py
instrument_geometry__init__.py
instrument_geometry_dxf_registry.py
instrument_geometry_neck_taper_aper_math.py
instrument_geometry_test_instrument_geometry_imports.py
materials_json_to_csv.py
mode_preview_routes.py
parse-tool-library.py
rmos__init__.py
rmos__init__2.py
rmos_ai_analytics.py
rmos_api_contracts.py
rmos_api_routes.py
rmos_feasibility.py
rmos_feasibility_2.py
rmos_feasibility_scorer.py
rmos_logging_ai.py
rmos_logs_helper.py
rmos_presets.py
rmos_profile_history.py
rosette_feasibility_scorer.py
routers_ai_cam_router.py
routers_instrument_router.py
saw_calculators_service.py
saw_lab_debug_schemas.py
saw_lab_path_planner.py
schemas_logs_ai.py
services_api_pp_toolpath_vcarve_toolpath.py
toolpath_geometry_engine.py
toolpath_geometry_engine_2.py
toolpath_geometry_selector_engine.py
toolpath_saw_engine.py
toolpath_service.py
toolpath_vcarve_toolpath.py
upgradecalculators_service.py
validate_saw_blade_library.py
```

---

### 🟢 REVIEW: Test Scripts (~80 files)

```
test_actions_1_2.ps1
test_b19_clone.ps1
test_blueprint_cam_bridge.py
test_blueprint_cam_bridge_ascii.py
test_blueprint_phase1.py
test_blueprint_phase2.py
test_blueprint_pipeline.py
test_body_outline_generator.ps1
test_bridge_calculator.ps1
test_bridge_payload.json
test_bridge3.dxf
test_cam_essentials_n0_n10.ps1
test_comparelab_preset_integration.ps1
test_coverage_quick.ps1
test_cp_s11_machine_profile.py
test_energy_analysis.ps1
test_export.dxf
test_export.svg
test_extension_validation.ps1
test_helical_critical_fixes.ps1
test_helical_direct.py
test_helical_v161_existing.ps1
test_job_intelligence.ps1
test_learned_overrides.ps1
test_ltb_calculators.ps1
test_multi_run_comparison.ps1
test_n0_browser_debug.ps1
test_n0_user_validation.ps1
test_n15_backplot.ps1
test_n15_n18_integration.ps1
test_navigation_consolidation.ps1
test_neck_generator.ps1
test_necklab_preset_loading.ps1
test_output.json
test_patches_i_j_integration.py
test_patches_integration.py
test_phase_27_bundle_13.ps1
test_phase_28_6.ps1
test_phase_28_7.ps1
test_phase_b_context.ps1
test_phase1_dashboards.ps1
test_phase2_helical_v161.ps1
test_phase27.ps1
test_phase28_17.ps1
test_phase28_2.ps1
test_phase28_integration.ps1
test_phase3_polygon_offset.ps1
test_phase4_adaptive_benchmark.ps1
test_phase5_cam_essentials.ps1
test_phase5_part2_n0_posts.ps1
test_phase5_part3_n06_drilling.ps1
test_phase5_part3_n07_ui.ps1
test_phase5_part3_n08_retract.ps1
test_phase5_part3_n09_probing.ps1
test_phase5_part3_n11_machines.ps1
test_phase5_part3_n12_tools.ps1
test_phase5_part3_n13_materials.ps1
test_phase5_part3_n14_unified_cam.ps1
test_phase5_part3_n15_gcode_backplot.ps1
test_phase5_part3_n16_adaptive_benchmark.ps1
test_phase5_part3_n17_polygon_offset.ps1
test_post_loading.py
test_post_presets.py
test_program.nc
test_real_blueprint_gibson_l00.py
test_rmos.py
test_rmos_2_0.py
test_rmos_dashboard.ps1
test_rmos_migration.ps1
test_rmos_sqlite.ps1
test_sample.nc
test_saw_blade_registry.ps1
test_saw_blade_validator.ps1
test_saw_frontend_integration.ps1
test_saw_telemetry.ps1
test_state_persistence.ps1
test_template_engine.ps1
test_unit_conversion.ps1
Test-B22-Export-P0.1.ps1
Test-CompareLab-Guardrails.ps1
Test-MM0-StripFamilies.ps1
Test-N10-WebSocket.ps1
test-parametric-guitar.ps1
test-pipeline-validation.ps1
test-relief-sim-bridge.ps1
test-rosette-redesign.ps1
test-viewer.html
Test-Wave19-FanFretCAM.ps1
Test-Wave19-FanFretMath.ps1
Test-Wave19-PerFretRisk.ps1
Test-Wave19-PhaseD-Frontend.ps1
tests/data/saw_lab_materials.csv
tests/test_compare_automation_api.py
tests/test_n11_rosette_scaffolding.ps1
tests/test_rmos.py
tests_instrument_geomety_test_instrument_geometry_imports.py
```

---

### 🟢 REVIEW: Legacy Directories (DO NOT COMMIT)

```
Archtop/
Bits-Bits-CarveCo-Complete-V1.2/
CAM_Roadmap_AlphaNightingale/
Calculators/
Feature_v16_1_Helical_Ramping/
Integration_Patch_WiringFinish_v1/
Integration_Patch_WiringFinish_v2/
MUST-Be-UNZIPPED-IDC-Woodcraft-Carveco-Tool-Database/
Myers-Woodshop-Set-CarveCo-V1.2/
README_Community_Patch/
README_Community_Patch_Additions/
Stratocaster/
Two-Moose-Set-CarveCo-V1.2/
WiringWorkbench_Docs_Patch_v1/
WiringWorkbench_Enhancements_v1/
__ARCHIVE__/
assets_staging/
blueprint-reader/
client/
data/
guitar_tap/
ltb-bridge-designer/
ltb-enterprise/
ltb-express/
ltb-fingerboard-designer/
ltb-headstock-designer/
ltb-neck-designer/
ltb-parametric-guitar/
ltb-pro/
ltb-test-dummy/
migrations/
phantom_cleanup_patch/
security_patch_dxf/
server/
temp_extract_37/
temp_extract_38/
temp_patch/
templates/
tools/
vibe-blueprintanalyzer-main/
```

---

### 🟢 REVIEW: Data Files & Vendor Resources

```
Amana-Tool-Vectric.tool
Amana-Tool-Vectric.tool.csv
Amana-Tool-Vectric.tool.txt
Amana-Tool-Vectric.tool-parsed.csv
Amana-Tool-Vectric-cleaned.csv
Amana-Tool-Vectric-cleaned_split.csv
ExportedParameters.csv
ExportedParameters_2.csv
FenderNeckParameters.xlsx
IDC-Woodcraft-*.csv (multiple)
IDCWoodcraftFusion360Library.json
Parametric_Fender_neck_v2.f3d
Produktguide-Cirkelklingor_EN.pdf
ROSETTE_STUDIO_ROADMAP.pdf
Starter_tool_library.json
TENRYU_Catalogue_Full_021224.pdf
Updated_material_library.json
Updated_tool_library.json
SpeTool_*.pdf (multiple)
Spray_Nozzle_Citation_Enhancement_Report.pdf
```

---

### 🟢 REVIEW: Misc Config/YAML Files

```
ai_rmos_constraint_profiles.yaml
files.json
index.html
instrument_geometry_instrument_model_registry.json
long_filenames_report.csv
longpaths.csv
lpmd-inventory.yml
lpmd_python_inventory.txt
rmos_pytest.ini
RMOS_2_0_ClassDiagram.puml
svg-viewer.html
[TITLE].inp
```

---

### 🟢 REVIEW: Vue Components (Root Level)

```
art_show_types_rosette.ts
art_studio_types_rmos.ts
art_Studio_toast_Store.ts
Rmos_Ai_Ops_Dashboard.vue
Rmos_Ai_Snapshot_Inspector.vue
Rosette_Ai_Suggestion_Panel.vue
src_stores_useArtStudioEngine.ts
```

---

## 📊 Current State

| Metric | Value |
|--------|-------|
| **Total Routers** | 91 |
| **Committed Files** | ~500+ |
| **Untracked Files** | 1,267 |
| **Test Pass Rate** | 53.4% (159/298) |
| **Branch** | feature/client-migration |

---

## 🎯 Recommended Commit Strategy

### Commit 1: Core Backend (services/api/)
```bash
git add services/api/
git commit -m "feat: Add services/api backend modules and tests"
```

### Commit 2: Frontend (packages/client/)
```bash
git add packages/client/
git commit -m "feat: Add packages/client frontend stores and components"
```

### Commit 3: Documentation (docs/)
```bash
git add docs/
git commit -m "docs: Add documentation and quickrefs"
```

### Commit 4: Scripts (scripts/)
```bash
git add scripts/
git commit -m "chore: Add test and utility scripts"
```

### Commit 5: Projects
```bash
git add projects/
git commit -m "feat: Add projects directory"
```

### Commit 6: Root Level Code (selective)
```bash
# Review and selectively add root-level .py and .md files
```

