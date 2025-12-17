# Repository Audit Report

**Date:** 2025-12-15 01:08
**Scope:** `services/api/app`

## Summary

| Category | Count |
|----------|-------|
| Phantom Imports | 20 |
| Stub/Placeholder Code | 106 |
| TODO/FIXME Markers | 33 |
| Broken Router Registrations | 2 |
| Missing __init__.py | 13 |
| **Total** | **174** |

---

## 1. Phantom Imports

- `app.core.saw_gcode` in `services\api\app\api\routes\exports.py`
- `app.core.saw_risk` in `services\api\app\api\routes\exports.py`
- `app.schemas.saw_slice_op` in `services\api\app\api\routes\exports.py`
- `app.schemas.saw_tool` in `services\api\app\api\routes\exports.py`
- `app.api.routes.saw_tools` in `services\api\app\api\routes\exports.py`
- `app.api.routes.saw_tools` in `services\api\app\api\routes\saw_ops.py`
- `app.core.saw_gcode` in `services\api\app\api\routes\saw_ops.py`
- `app.core.saw_risk` in `services\api\app\api\routes\saw_ops.py`
- `app.schemas.saw_slice_batch_op` in `services\api\app\api\routes\saw_ops.py`
- `app.schemas.saw_slice_op` in `services\api\app\api\routes\saw_ops.py`
- `app.schemas.saw_tool` in `services\api\app\api\routes\saw_ops.py`
- `app.sim_engines.vericut` in `services\api\app\services\cam_sim_bridge.py`
- `app.cnc_production.feeds_speeds.api.routes` in `services\api\app\_experimental\cnc_production\routers.py`
- `app.cnc_production.feeds_speeds.core.feeds_speeds_resolver` in `services\api\app\_experimental\cnc_production\feeds_speeds\api\routes\feeds_speeds.py`
- `app.cnc_production.feeds_speeds.core.presets_db` in `services\api\app\_experimental\cnc_production\feeds_speeds\api\routes\feeds_speeds.py`
- `app.cnc_production.feeds_speeds.core.chipload_calc` in `services\api\app\_experimental\cnc_production\feeds_speeds\core\feeds_speeds_resolver.py`
- `app.cnc_production.feeds_speeds.core.deflection_model` in `services\api\app\_experimental\cnc_production\feeds_speeds\core\feeds_speeds_resolver.py`
- `app.cnc_production.feeds_speeds.core.heat_model` in `services\api\app\_experimental\cnc_production\feeds_speeds\core\feeds_speeds_resolver.py`
- `app.cnc_production.feeds_speeds.core.presets_db` in `services\api\app\_experimental\cnc_production\feeds_speeds\core\feeds_speeds_resolver.py`
- `app.cnc_production.feeds_speeds.schemas.speed_feed_preset` in `services\api\app\_experimental\cnc_production\feeds_speeds\core\presets_db.py`

---

## 2. Stub/Placeholder Code

- **pass statement** at `services\api\app\post_injection_dropin.py:91`
- **ellipsis (...)** at `services\api\app\api\deps\__init__.py:21`
- **ellipsis (...)** at `services\api\app\api\deps\__init__.py:36`
- **pass statement** at `services\api\app\api\routes\presets_router.py:96`
- **pass statement** at `services\api\app\api\routes\rmos_pattern_api.py:154`
- **ellipsis (...)** at `services\api\app\api\routes\rmos_rosette_api.py:242`
- **pass statement** at `services\api\app\api\routes\rmos_rosette_api.py:1011`
- **pass statement** at `services\api\app\cad\exceptions.py:85`
- **stub comment** at `services\api\app\calculators\alternative_temperaments.py:216`
- **pass statement** at `services\api\app\calculators\service.py:179`
- **pass statement** at `services\api\app\calculators\service.py:183`
- **stub comment** at `services\api\app\calculators\service.py:221`
- **stub comment** at `services\api\app\calculators\service.py:255`
- **stub comment** at `services\api\app\calculators\service.py:347`
- **pass statement** at `services\api\app\calculators\suite\basic_calculator.py:127`
- **ellipsis (...)** at `services\api\app\cam\cam_preview_router.py:137`
- **pass statement** at `services\api\app\cam\contour_reconstructor.py:374`
- **pass statement** at `services\api\app\cam\dxf_advanced_validation.py:397`
- **pass statement** at `services\api\app\cam\dxf_advanced_validation.py:537`
- **pass statement** at `services\api\app\cam\dxf_preflight.py:591`
- **ellipsis (...)** at `services\api\app\cam\energy_model.py:108`
- **pass statement** at `services\api\app\cam\graph_algorithms.py:39`
- **ellipsis (...)** at `services\api\app\cam\heat_timeseries.py:112`
- **ellipsis (...)** at `services\api\app\cam\heat_timeseries.py:132`
- **ellipsis (...)** at `services\api\app\cam\spatial_hash.py:50`
- **ellipsis (...)** at `services\api\app\cam\trochoid_l3.py:56`
- **ellipsis (...)** at `services\api\app\cam\whatif_opt.py:141`
- **pass statement** at `services\api\app\core\pipeline_handoff.py:75`
- **pass statement** at `services\api\app\core\rmos_safety_policy.py:224`
- **pass statement** at `services\api\app\data\validate_tool_library.py:25`
- **pass statement** at `services\api\app\data_registry\registry.py:161`
- **pass statement** at `services\api\app\data_registry\registry.py:166`
- **pass statement** at `services\api\app\data_registry\registry.py:444`
- **pass statement** at `services\api\app\generators\lespaul_body_generator.py:214`
- **stub comment** at `services\api\app\instrument_geometry\dxf_loader.py:113`
- **stub comment** at `services\api\app\instrument_geometry\model_spec.py:214`
- **stub comment** at `services\api\app\instrument_geometry\model_spec.py:224`
- **stub comment** at `services\api\app\instrument_geometry\model_spec.py:249`
- **stub comment** at `services\api\app\instrument_geometry\__init__.py:50`
- **pass statement** at `services\api\app\instrument_geometry\bracing\fan_brace.py:126`
- **pass statement** at `services\api\app\ltb_calculators\basic_calculator.py:127`
- **ellipsis (...)** at `services\api\app\middleware\edition_middleware.py:211`
- **ellipsis (...)** at `services\api\app\middleware\edition_middleware.py:263`
- **ellipsis (...)** at `services\api\app\middleware\edition_middleware.py:295`
- **ellipsis (...)** at `services\api\app\middleware\edition_middleware.py:324`
- **pass statement** at `services\api\app\pipelines\dxf_cleaner\clean_dxf.py:140`
- **pass statement** at `services\api\app\pipelines\dxf_cleaner\clean_dxf.py:142`
- **stub comment** at `services\api\app\pipelines\rosette\__init__.py:23`
- **stub comment** at `services\api\app\rmos\context_adapter.py:280`
- **stub comment** at `services\api\app\rmos\context_adapter.py:281`
- **stub comment** at `services\api\app\rmos\context_adapter.py:282`
- **ellipsis (...)** at `services\api\app\rmos\context_router.py:149`
- **ellipsis (...)** at `services\api\app\rmos\context_router.py:155`
- **ellipsis (...)** at `services\api\app\rmos\context_router.py:311`
- **ellipsis (...)** at `services\api\app\rmos\feasibility_router.py:111`
- **ellipsis (...)** at `services\api\app\rmos\feasibility_router.py:291`
- **pass statement** at `services\api\app\rmos\logging_ai.py:112`
- **pass statement** at `services\api\app\rmos\__init__.py:97`
- **pass statement** at `services\api\app\rmos\__init__.py:106`
- **pass statement** at `services\api\app\rmos\__init__.py:115`
- **pass statement** at `services\api\app\rmos\.backup\constraint_profiles.py:262`
- **ellipsis (...)** at `services\api\app\rmos\.backup\constraint_profiles.py:307`
- **pass statement** at `services\api\app\rmos\api\log_routes.py:171`
- **stub comment** at `services\api\app\routers\art_presets_router.py:20`
- **pass statement** at `services\api\app\routers\art_studio_rosette_router.py:255`
- **pass statement** at `services\api\app\routers\cam_fret_slots_router.py:117`
- **ellipsis (...)** at `services\api\app\routers\cam_risk_aggregate_router.py:289`
- **pass statement** at `services\api\app\routers\cam_vcarve_router.py:51`
- **stub comment** at `services\api\app\routers\compare_automation_router.py:52`
- **ellipsis (...)** at `services\api\app\routers\dxf_plan_router.py:73`
- **pass statement** at `services\api\app\routers\dxf_preflight_router.py:762`
- **stub comment** at `services\api\app\routers\job_insights_router.py:28`
- **NotImplementedError** at `services\api\app\routers\pipeline_router.py:114`
- **pass statement** at `services\api\app\routers\pipeline_router.py:117`
- **pass statement** at `services\api\app\routers\pipeline_router.py:120`
- **pass statement** at `services\api\app\routers\pipeline_router.py:123`
- **NotImplementedError** at `services\api\app\routers\pipeline_router.py:130`
- **pass statement** at `services\api\app\routers\pipeline_router.py:441`
- **pass statement** at `services\api\app\routers\sim_validate.py:44`
- **pass statement** at `services\api\app\routers\sim_validate.py:49`
- **pass statement** at `services\api\app\schemas\strip_family.py:57`
- **pass statement** at `services\api\app\services\cam_backup_service.py:116`
- **pass statement** at `services\api\app\services\cam_backup_service.py:120`
- **pass statement** at `services\api\app\services\cam_backup_service.py:131`
- **stub comment** at `services\api\app\services\cam_sim_bridge.py:313`
- **ellipsis (...)** at `services\api\app\services\compare_risk_bucket_detail.py:44`
- **pass statement** at `services\api\app\services\preset_store.py:30`
- **pass statement** at `services\api\app\stores\sqlite_base.py:46`
- **pass statement** at `services\api\app\stores\sqlite_base.py:52`
- **pass statement** at `services\api\app\stores\sqlite_base.py:65`
- **pass statement** at `services\api\app\stores\sqlite_base.py:78`
- **pass statement** at `services\api\app\toolpath\geometry_engine.py:30`
- **pass statement** at `services\api\app\toolpath\geometry_engine.py:40`
- **stub comment** at `services\api\app\util\compare_automation_helpers.py:53`
- **NotImplementedError** at `services\api\app\util\compare_automation_helpers.py:103`
- **stub comment** at `services\api\app\util\tool_table.py:204`
- **pass statement** at `services\api\app\utils\post_presets.py:404`
- **stub comment** at `services\api\app\_experimental\ai_cam\advisor.py:140`
- **ellipsis (...)** at `services\api\app\_experimental\ai_core\clients.py:17`
- **stub comment** at `services\api\app\_experimental\ai_graphics\services\ai_parameter_suggester.py:49`
- **stub comment** at `services\api\app\_experimental\ai_graphics\services\ai_parameter_suggester.py:98`
- **stub comment** at `services\api\app\_experimental\ai_graphics\services\ai_parameter_suggester.py:99`
- **stub comment** at `services\api\app\_experimental\ai_graphics\services\llm_client.py:38`
- **stub comment** at `services\api\app\_experimental\cnc_production\learn\live_learn_ingestor.py:51`
- **pass statement** at `services\api\app\_experimental\cnc_production\learn\live_learn_ingestor.py:82`
- **pass statement** at `services\api\app\_experimental\cnc_production\learn\live_learn_ingestor.py:137`

---

## 3. TODO/FIXME Markers

- **TODO** `services\api\app\api\deps\__init__.py:23` - TODO: Implement actual database session when SQLAl
- **TODO** `services\api\app\api\deps\__init__.py:38` - TODO: Implement actual auth when user system is co
- **TODO** `services\api\app\api\routes\rmos_safety_api.py:85` - TODO: Add auth check here when auth system is read
- **TODO** `services\api\app\api\routes\rmos_safety_api.py:197` - TODO: Add auth check here when auth system is read
- **TODO** `services\api\app\calculators\fret_slots_export.py:327` - TODO: Add DXF export
- **TODO** `services\api\app\calculators\service.py:579` - TODO: Implement full BOM calculator
- **TODO** `services\api\app\cam\adaptive_core.py:293` - TODO: subtract islands properly; in first cut we j
- **TODO** `services\api\app\cam_core\saw_lab\saw_blade_validator.py:293` - TODO: Add blade-specific RPM limits to SawBladeSpe
- **TODO** `services\api\app\instrument_geometry\specs\selmer_maccaferri_dhole.py:13` - TODO: measure from plans
- **TODO** `services\api\app\instrument_geometry\specs\selmer_maccaferri_dhole.py:14` - TODO
- **TODO** `services\api\app\instrument_geometry\specs\selmer_maccaferri_dhole.py:15` - TODO
- **TODO** `services\api\app\instrument_geometry\specs\selmer_maccaferri_dhole.py:16` - TODO
- **TODO** `services\api\app\instrument_geometry\specs\selmer_maccaferri_dhole.py:17` - TODO
- **TODO** `services\api\app\instrument_geometry\specs\selmer_maccaferri_dhole.py:18` - TODO
- **TODO** `services\api\app\instrument_geometry\specs\selmer_maccaferri_dhole.py:21` - TODO
- **TODO** `services\api\app\instrument_geometry\specs\selmer_maccaferri_dhole.py:22` - TODO
- **TODO** `services\api\app\instrument_geometry\specs\selmer_maccaferri_dhole.py:30` - TODO
- **TODO** `services\api\app\instrument_geometry\specs\selmer_maccaferri_dhole.py:31` - TODO
- **TODO** `services\api\app\instrument_geometry\specs\selmer_maccaferri_dhole.py:33` - TODO
- **TODO** `services\api\app\instrument_geometry\specs\selmer_maccaferri_dhole.py:36` - TODO - appears ~1.5Â° from plans
- **TODO** `services\api\app\instrument_geometry\specs\selmer_maccaferri_dhole.py:37` - TODO
- **TODO** `services\api\app\instrument_geometry\specs\selmer_maccaferri_dhole.py:72` - TODO - should be scale_length / 2 = 335mm
- **TODO** `services\api\app\instrument_geometry\specs\selmer_maccaferri_dhole.py:101` - TODO: extract from plans
- **TODO** `services\api\app\instrument_geometry\specs\selmer_maccaferri_dhole.py:109` - TODO
- **TODO** `services\api\app\rmos\context.py:282` - TODO: compute from nut_spacing
- **TODO** `services\api\app\rmos\context.py:283` - TODO: compute from bridge_spacing
- **TODO** `services\api\app\rmos\context_adapter.py:273` - TODO: Replace with actual DXF parsing
- **TODO** `services\api\app\routers\blueprint_cam_bridge.py:923` - TODO: Use actual boundary area calculation
- **TODO** `services\api\app\routers\compare_automation_router.py:36` - TODO: Replace with the real compare engine.
- **TODO** `services\api\app\routers\unified_presets_router.py:202` - TODO: Add auth context
- **TODO** `services\api\app\toolpath\dxf_exporter.py:133` - TODO: Implement true LWPOLYLINE for R14/R18
- **TODO** `services\api\app\_experimental\cnc_production\learn\live_learn_ingestor.py:80` - TODO: Wire to actual learned overrides system when
- **TODO** `services\api\app\_experimental\cnc_production\learn\saw_live_learn_dashboard.py:184` - TODO: extract from run.meta if available

---

## 4. Broken Router Registrations

- `Import: .routers.ai_cam_router`
- `Import: .routers.joblog_router`

---

## 5. Missing __init__.py

- `services\api\app\core`
- `services\api\app\learn`
- `services\api\app\schemas`
- `services\api\app\telemetry`
- `services\api\app\tests`
- `services\api\app\tools`
- `services\api\app\util`
- `services\api\app\utils`
- `services\api\app\websocket`
- `services\api\app\_experimental`
- `services\api\app\api\routes`
- `services\api\app\cam_core\saw_lab\importers`
- `services\api\app\tests\rmos`

