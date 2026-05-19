# Rosette Frontend/Backend Route Provenance Trace

**Dev Order:** 5G  
**Date:** 2026-05-10  
**Status:** Complete

---

## Frontend Route References

### SDK Endpoints

| File | Function | Route Called | Status |
|------|----------|--------------|--------|
| `sdk/endpoints/rmosRosetteCam.ts` | `segmentRing()` | `/api/rmos/rosette/segment-ring` | VALID |
| `sdk/endpoints/rmosRosetteCam.ts` | `generateSlices()` | `/api/rmos/rosette/generate-slices` | VALID |
| `sdk/endpoints/rmosRosetteCam.ts` | `previewRosette()` | `/api/rmos/rosette/preview` | VALID |
| `sdk/endpoints/rmosRosetteCam.ts` | `exportCnc()` | `/api/rmos/rosette/export-cnc` | VALID |
| `sdk/endpoints/artRosetteWheel.ts` | various | `/api/art/rosette-designer/*` | AMBIGUOUS |
| `sdk/art/snapshots.ts` | `listRecent()` | `/art/rosette/snapshots/recent` | VALID |
| `sdk/art/snapshots.ts` | `getSnapshot()` | `/art/rosette/snapshots/{id}` | VALID |
| `sdk/art/snapshots.ts` | `exportSnapshot()` | `/art/rosette/snapshots/{id}/export` | VALID |
| `sdk/art/snapshots.ts` | `importSnapshot()` | `/art/rosette/snapshots/import` | VALID |

### Store References

| Store | Function | Route Called | Status |
|-------|----------|--------------|--------|
| `useRosetteDesignerStore.ts` | `segmentRing()` | `/api/rmos/rosette/segment-ring` | VALID |
| `useRosetteDesignerStore.ts` | `generateSlices()` | `/api/rmos/rosette/generate-slices` | VALID |
| `useRosetteDesignerStore.ts` | `preview()` | `/api/rmos/rosette/preview` | VALID |
| `useRosetteDesignerStore.ts` | `exportCnc()` | `/api/rmos/rosette/export-cnc` | VALID |
| `useManufacturingPlanStore.ts` | `fetchPlan()` | `/api/rosette/manufacturing-plan` | MISSING PREFIX |
| `rosetteStore.ts` | various | multiple | LEGACY |

### API Client References

| File | Function | Route Called | Status |
|------|----------|--------------|--------|
| `api/artPreviewClient.ts` | `previewSvg()` | `/api/art/rosette/preview/svg` | VALID |
| `api/artFeasibilityClient.ts` | `batch()` | `/api/art/rosette/feasibility/batch` | MISSING |
| `api/art-studio.ts` | `previewRosette()` | `/art-studio/rosette/preview` | MISSING |
| `api/art-studio.ts` | `exportRosetteDxf()` | `/art-studio/rosette/export-dxf` | MISSING |
| `api/art-studio.ts` | `getRosettePresets()` | `/art-studio/rosette/presets` | MISSING |
| `api/art-studio.ts` | `getRosettePreset()` | `/art-studio/rosette/presets/{name}` | MISSING |

### View/Component References

| File | Route Called | Status |
|------|--------------|--------|
| `views/RMOSCncJobDetailView.vue` | `/api/rmos/rosette/cnc-job/{id}` | VALID |
| `views/RMOSCncJobDetailView.vue` | `/api/rmos/rosette/operator-report-pdf/{id}` | VALID |
| `views/RMOSCncHistoryView.vue` | `/api/rmos/rosette/cnc-history` | VALID |
| `components/rosette/RosettePhotoImport.vue` | `/api/cam/rosette/import_photo` | VALID |
| `components/rmos/CNCExportPanel.vue` | `/api/rmos/rosette/operator-report-pdf/{id}` | VALID |
| `components/toolbox/composables/useRosetteDesignerExport.ts` | `/api/export/rosette-pdf` | AMBIGUOUS |
| `utils/api.ts` | `/pipelines/rosette/calculate` | LEGACY |
| `utils/api.ts` | `/pipelines/rosette/export-dxf` | LEGACY |
| `utils/api.ts` | `/pipelines/rosette/export-gcode` | LEGACY |

### Compare Feature References

| File | Route Called | Status |
|------|--------------|--------|
| `views/rosette_compare/useRosetteCompareHistory.ts` | `/api/art/rosette/compare/snapshots` | VALID |
| `views/rosette_compare/useRosetteCompareHistory.ts` | `/api/art/rosette/compare/export_csv` | VALID |
| `views/rosette_compare/useRosetteCompareActions.ts` | `/api/art/rosette/jobs` | VALID |
| `views/rosette_compare/useRosetteCompareActions.ts` | `/api/art/rosette/compare` | VALID |
| `views/rosette_compare/useRosetteCompareActions.ts` | `/api/art/rosette/compare/snapshot` | VALID |

---

## Missing Backend Routes (Frontend Drift)

| Frontend Reference | Expected Backend | Actual Status |
|--------------------|------------------|---------------|
| `/art-studio/rosette/preview` | art_studio router | NOT FOUND |
| `/art-studio/rosette/export-dxf` | art_studio router | NOT FOUND |
| `/art-studio/rosette/presets` | art_studio router | NOT FOUND |
| `/art-studio/rosette/presets/{name}` | art_studio router | NOT FOUND |
| `/api/art/rosette/feasibility/batch` | art_studio router | NOT FOUND |
| `/api/rosette/manufacturing-plan` | ? | AMBIGUOUS PREFIX |

**Root Cause:** Art Studio consolidation left orphaned frontend paths. The `/art-studio/*` prefix is not mounted for rosette endpoints.

---

## Backend Route Inventory

### RMOS Rosette Router (`rmos/rosette_cam_router.py`)

| Route | Method | Generator | Output Type | Classification |
|-------|--------|-----------|-------------|----------------|
| `/rosette/segment-ring` | POST | tile_segmentation | geometry | CANDIDATE_PREVIEW |
| `/rosette/design` | POST | rosette_cnc_wiring | geometry | CANDIDATE_PREVIEW |
| `/rosette/generate-slices` | POST | tile_segmentation | geometry | CANDIDATE_PREVIEW |
| `/rosette/preview` | POST | build_preview_snapshot | preview | CANDIDATE_PREVIEW |
| `/rosette/export-cnc` | POST | generate_gcode_from_toolpaths | G-code | QUARANTINED_EXPORT |
| `/rosette/cnc-history` | GET | art_jobs_store | list | LEGACY |
| `/rosette/cnc-job/{id}` | GET | art_jobs_store | artifact | LEGACY |

**Prefix:** `/api/rmos` (mounted via manifest)

### Art Studio Rosette Routes

| File | Route | Method | Output | Classification |
|------|-------|--------|--------|----------------|
| `rosette_jobs_routes.py` | `/api/art/rosette/preview` | POST | paths+bbox | CANDIDATE_PREVIEW |
| `rosette_jobs_routes.py` | `/api/art/rosette/save` | POST | job | LEGACY |
| `rosette_jobs_routes.py` | `/api/art/rosette/jobs` | GET | list | LEGACY |
| `rosette_jobs_routes.py` | `/api/art/rosette/presets` | GET | list | LEGACY |
| `rosette_compare_routes.py` | `/api/art/rosette/compare` | POST | diff | LEGACY |
| `rosette_compare_routes.py` | `/api/art/rosette/compare/snapshot` | POST | snapshot | LEGACY |
| `preview_routes.py` | `/api/art/rosette/preview/svg` | POST | SVG | CANDIDATE_PREVIEW |
| `rosette_pattern_routes.py` | `/api/art/rosette/pattern/*` | various | patterns | EXPERIMENTAL |
| `rosette_manufacturing_routes.py` | `/api/art/rosette/project` | POST | toolpath | CANDIDATE_PREVIEW |
| `rosette_manufacturing_routes.py` | `/api/art/rosette/manufacturing-plan` | POST | plan | LEGACY |
| `rosette_snapshot_routes.py` | `/rosette/snapshots/*` | various | snapshots | RMOS_INTEGRATED |

### CAM Rosette Routes

| File | Route | Method | Output | Classification |
|------|-------|--------|--------|----------------|
| `rosette_toolpath_router.py` | `/rosette/plan-toolpath` | POST | toolpath | RMOS_INTEGRATED |
| `rosette_toolpath_router.py` | `/rosette/post-gcode` | POST | G-code | GOVERNED_EXPORT |
| `rosette_jobs_router.py` | `/rosette/jobs` | POST | job | LEGACY |
| `rosette_jobs_router.py` | `/rosette/jobs/{id}` | GET | job | LEGACY |

**Prefix:** `/api/cam/rosette` (via aggregator)

---

## Provenance Summary

| Category | Count | Status |
|----------|-------|--------|
| Frontend routes with valid backend | 18 | ALIGNED |
| Frontend routes missing backend | 6 | DRIFT |
| Backend routes without frontend consumer | 8 | ORPHAN |
| Total unique backend routes | 29 | FRAGMENTED |

---

*Trace completed: 2026-05-10*
