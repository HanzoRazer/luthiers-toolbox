# CI-RED-016 Endpoint Consumer Map

Generated: `2026-07-07T08:27:03.259321Z`
Base commit: `ba3c8565035b1cb35ec988c89d0e9157381f0a0a`

## Purpose

This document turns CI-RED-016 from a raw route-count concern into a structured consumer map. It does not delete, rename, consolidate, or re-baseline any endpoint.

## Summary

| Metric | Value |
| --- | --- |
| Mounted endpoint operations | 1132 |
| OpenAPI operations | 1132 |
| OpenAPI paths | 1073 |
| Route-object unique endpoints | 1138 |
| Static decorator count | 1181 |
| Static baseline | 942 |
| Static delta | 239 |
| Mounted-vs-static gap | 49 |
| Unmatched consumer literals | 568 |

## Methodology Notes

- Source of truth is the live mounted FastAPI surface. The utility flattens FastAPI 0.137 `_IncludedRouter` route objects and cross-checks the result against `app.openapi()` operations.
- Static decorator count is retained as debt context only. It can differ from mounted behavior because it does not resolve router inclusion and generated schema behavior.
- Consumer detection is a first-party string-literal and parameter-prefix scan. It is useful triage evidence, not runtime telemetry.
- Endpoint references are matched over the mounted API roots `/api`, `/health`, `/ws`, `/instrument`, and `/exports`. Root-relative literals (`"/exports/polyline_dxf"`) count as evidence for all of these roots. Template-base suffixes behind an interpolated base (`` `${API_BASE}/exports/polyline_dxf` ``) are recognized for the legacy `/exports` surface only — that compatibility surface was previously invisible to the scan (CI-RED-016-C). Generalizing template-base matching to `/api` routes is a tracked follow-up.
- `no_first_party_consumer_found` is not a deletion verdict. Governance, audit, authority, provenance, and review endpoints are explicitly protected from being interpreted as dead just because they lack a frontend caller.

## Endpoint Lanes

| Lane | Endpoints |
| --- | --- |
| cam_governance | 176 |
| cam_operation | 146 |
| woodworking_instrument_design | 94 |
| music_calculator | 91 |
| art_studio | 81 |
| rmos_runtime | 77 |
| mvp_runtime | 67 |
| machine_posts_tooling | 62 |
| saw_lab | 61 |
| unknown | 53 |
| analytics_registry | 50 |
| blueprint_vectorizer | 47 |
| ai_advisory | 27 |
| compare_lab | 25 |
| acoustics | 24 |
| authority_reference | 16 |
| instrument_geometry | 10 |
| materials_inventory | 8 |
| jobs_runtime | 7 |
| legacy_migration | 6 |
| health_meta | 4 |

## Consumer Classes

| Primary consumer class | Endpoints |
| --- | --- |
| test_only | 614 |
| no_first_party_consumer_found | 290 |
| frontend_product | 178 |
| docs_only | 36 |
| ci_governance | 10 |
| frontend_sdk | 4 |

## No First-Party Consumer Found By Lane

| Lane | Endpoints |
| --- | --- |
| woodworking_instrument_design | 54 |
| cam_operation | 42 |
| music_calculator | 29 |
| cam_governance | 26 |
| mvp_runtime | 22 |
| acoustics | 19 |
| compare_lab | 13 |
| machine_posts_tooling | 13 |
| blueprint_vectorizer | 11 |
| unknown | 11 |
| art_studio | 10 |
| ai_advisory | 8 |
| analytics_registry | 6 |
| rmos_runtime | 6 |
| materials_inventory | 5 |
| saw_lab | 5 |
| authority_reference | 4 |
| instrument_geometry | 3 |
| legacy_migration | 3 |

Protected governance/audit/authority endpoints in this bucket: `31`.

## Sample Review Targets

| Method | Path | Lane | Router modules |
| --- | --- | --- | --- |
| DELETE | /api/cam/pipeline/cam/pipeline/presets/{preset_id} | cam_operation | app.routers.cam_pipeline_preset_run_router |
| DELETE | /api/compare/lab/baselines/{baseline_id} | compare_lab | app.compare.routers.lab |
| GET | /api/acoustics/plate/body-styles | acoustics | app.routers.acoustics.plate_router |
| GET | /api/acoustics/plate/materials | materials_inventory | app.routers.acoustics.plate_router |
| GET | /api/acoustics/plate/status | acoustics | app.routers.acoustics.plate_router |
| GET | /api/acoustics/radius-dish/common-radii | acoustics | app.routers.radius_dish_router |
| GET | /api/agentic/status | unknown | app.agentic.router |
| GET | /api/analyzer/health | ai_advisory | app.analyzer.router |
| GET | /api/analyzer/references | ai_advisory | app.analyzer.router |
| GET | /api/archtop/health | woodworking_instrument_design | app.routers.archtop_router |
| GET | /api/art-studio/bracing/back/body-styles | art_studio | app.art_studio.bracing_router |
| GET | /api/art/rosette/snapshots/ | art_studio | app.art_studio.api.rosette_snapshot_routes |
| GET | /api/art/rosette/traditional/masters | art_studio | app.art_studio.api.rosette_manufacturing_routes |
| GET | /api/art/rosette/traditional/patterns/{pattern_id} | art_studio | app.art_studio.api.rosette_manufacturing_routes |
| GET | /api/blueprint/clean/download/{filename} | blueprint_vectorizer | app.routers.blueprint.clean_router |
| GET | /api/blueprint/clean/info | blueprint_vectorizer | app.routers.blueprint.clean_router |
| GET | /api/blueprint/phase4/info | blueprint_vectorizer | app.routers.blueprint.phase4_router |
| GET | /api/blueprint/static/{filename} | blueprint_vectorizer | app.routers.blueprint.phase2_router |
| GET | /api/business/bom/materials | materials_inventory | app.business.bom_router |
| GET | /api/business/bom/materials/{material_id} | materials_inventory | app.business.bom_router |
| GET | /api/business/templates | mvp_runtime | app.business.bom_router |
| GET | /api/cam/backup/download/{name} | cam_operation | app.cam.routers.utility.backup_router |
| GET | /api/cam/backup/list | cam_operation | app.cam.routers.utility.backup_router |
| GET | /api/cam/binding/info | woodworking_instrument_design | app.cam.routers.binding.binding_router |
| GET | /api/cam/bridge/electric | cam_operation | app.routers.bridge_presets_router |
| GET | /api/cam/bridge/electric/{bridge_id_a}/compat/{bridge_id_b} | cam_operation | app.routers.bridge_presets_router |
| GET | /api/cam/bridge/electric/{bridge_id} | cam_operation | app.routers.bridge_presets_router |
| GET | /api/cam/bridge/floyd-rose/dimensions | cam_operation | app.routers.bridge_presets_router |
| GET | /api/cam/compare/diff | compare_lab | app.cam.routers.utility.compare_router |
| GET | /api/cam/drilling/pattern/info | cam_operation | app.cam.routers.drilling.drill_pattern_router |

## Machine-Readable Artifact

The full endpoint-level map is committed at `services/api/metrics/endpoint_consumer_map.json`.

## Recommended Next Step

Use this map to pick a narrow CI-RED-016-C consolidation candidate. Prioritize endpoints with `no_first_party_consumer_found` only after a human review confirms they are not governance/audit/authority surfaces, not external contract surfaces, and not intentionally retained compatibility endpoints.
