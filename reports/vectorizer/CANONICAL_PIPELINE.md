# Canonical vectorizer pipeline — file list

Verified against live code at `2646992fc294a904438042d529b939ec6db80662` (`origin/main`).

There is **not** one Python file. There are **two production intakes**. Default blueprint mode is `refined`. Photo mode is a separate endpoint.

`vectorizer-sandbox` is out of scope. This list is `luthiers-toolbox` only.

Do not copy-paste these files. Use the zip (see `HOW_TO_DOWNLOAD.md`).

> **Source of truth.** This document and the zip beside it are a **snapshot**, verified at
> the commit named above. The canonical source is the repository at that commit — not this
> file, and not the zip. Source files keep changing; when they do, this snapshot becomes
> stale and nothing here will announce it. If a path below disagrees with the repository,
> **the repository is right**.
>
> Every path listed here is a real repository path, so any entry can be checked directly
> against `main`.

---

## Path A — Blueprint Reader default (`refined`)

Locked Hostinger intake. `POST /api/blueprint/vectorize/async` default `mode=refined`. Sync twin: `POST /api/blueprint/vectorize`.

```
hostinger/blueprint-reader.html
    → POST /api/blueprint/vectorize/async  (mode defaults to refined)
    → services/api/app/routers/blueprint_async_router.py
    → services/api/app/services/blueprint_orchestrator.py
         extract: services/api/app/services/blueprint_extract.py
                  extract_blueprint_to_dxf()
                  → services/photo-vectorizer/edge_to_dxf.py
                     EdgeToDXF.convert()  isolate_body=True
         cleanup: services/api/app/services/blueprint_clean.py
                  → services/api/app/cam/unified_dxf_cleaner.py
                  → services/api/app/services/contour_scoring.py
```

| File | Role |
|------|------|
| `hostinger/blueprint-reader.html` | Production UI. Blueprint submit does not send `mode`; API default is `refined`. |
| `services/api/app/routers/blueprint_async_router.py` | Async HTTP. `mode: str = Form("refined")`. |
| `services/api/app/routers/blueprint/vectorize_router.py` | Sync HTTP twin. Same orchestrator. |
| `services/api/app/jobs/models.py` | Async job record. |
| `services/api/app/jobs/store.py` | Job store used by the async router. |
| `services/api/app/jobs/__init__.py` | Job module exports. |
| `services/api/app/services/blueprint_orchestrator.py` | Mode switch. Default branch calls `extract_blueprint_to_dxf()`. |
| `services/api/app/services/blueprint_extract.py` | PDF page + raster guardrails + `EdgeToDXF.convert()`. |
| `services/api/app/services/blueprint_limits.py` | Upload / raster caps. |
| `services/photo-vectorizer/edge_to_dxf.py` | Default extraction engine (`EdgeToDXF.convert`). |
| `services/photo-vectorizer/grouping_telemetry.py` | Grouping provenance on extract. |
| `services/photo-vectorizer/contour_debug_overlay.py` | Optional; loaded if present (`DEBUG_CONTOURS`). |
| `services/api/app/services/blueprint_clean.py` | Post-extract cleanup for `refined`. |
| `services/api/app/cam/unified_dxf_cleaner.py` | Chain / filter used by cleanup. |
| `services/api/app/services/contour_scoring.py` | Contour scoring in cleanup. |
| `services/api/app/services/contour_recommendation.py` | Recommendation object on the orchestrator result. |
| `services/photo-vectorizer/contour_plausibility.py` | Imported by `blueprint_clean.py` for body-ownership scoring. |

Open on GitHub (one file at a time):

- https://github.com/HanzoRazer/luthiers-toolbox/blob/main/services/photo-vectorizer/edge_to_dxf.py
- https://github.com/HanzoRazer/luthiers-toolbox/blob/main/services/api/app/services/blueprint_orchestrator.py
- https://github.com/HanzoRazer/luthiers-toolbox/blob/main/services/api/app/services/blueprint_extract.py
- https://github.com/HanzoRazer/luthiers-toolbox/blob/main/services/api/app/services/blueprint_clean.py

---

## Path B — Photo extract (second production intake)

`hostinger/blueprint-reader.html` Photo toggle. `POST /api/vectorizer/extract`.

```
hostinger/blueprint-reader.html (Photo mode)
    → POST /api/vectorizer/extract
    → services/api/app/routers/photo_vectorizer_router.py
    → services/api/app/services/photo_orchestrator.py
    → services/photo-vectorizer/photo_vectorizer_v2.py
       PhotoVectorizerV2.extract()
```

| File | Role |
|------|------|
| `services/api/app/routers/photo_vectorizer_router.py` | HTTP wrapper. |
| `services/api/app/services/photo_orchestrator.py` | Calls `PhotoVectorizerV2.extract()`. |
| `services/photo-vectorizer/photo_vectorizer_v2.py` | Photo / AI / blueprint / silhouette routing. |
| `services/photo-vectorizer/grid_classify.py` | Grid classification. |
| `services/photo-vectorizer/contour_stage.py` | Contour assembly stage. |
| `services/photo-vectorizer/body_isolation_stage.py` | Body isolation. |
| `services/photo-vectorizer/body_isolation_result.py` | Isolation result types. |
| `services/photo-vectorizer/geometry_authority.py` | Geometry authority used in extract. |
| `services/photo-vectorizer/geometry_coach_v2.py` | Retry coach. |
| `services/photo-vectorizer/geometry_coach.py` | Imported by coach v2. |
| `services/photo-vectorizer/body_model.py` | Body model. |
| `services/photo-vectorizer/landmark_extractor.py` | Landmarks (runtime import). |
| `services/photo-vectorizer/light_line_body_extractor.py` | `source_type=blueprint` branch. |
| `services/photo-vectorizer/march_pipeline_restore.py` | Used with the blueprint branch. |
| `services/photo-vectorizer/photo_silhouette_extractor.py` | `source_type=silhouette` branch. |

Open on GitHub:

- https://github.com/HanzoRazer/luthiers-toolbox/blob/main/services/photo-vectorizer/photo_vectorizer_v2.py
- https://github.com/HanzoRazer/luthiers-toolbox/blob/main/services/api/app/services/photo_orchestrator.py

---

## Wired, not the default `refined` path

These are live `CleanupMode` branches on the same orchestrator. They are **not** what Blueprint Reader sends today.

| Mode | Engine |
|------|--------|
| `v2_raw` | `services/blueprint-import/vectorizer_phase3.py` → `Phase3Vectorizer.extract(raw_output=True)` |
| `cam_ready_r2000` | Same file, `extract(cam_ready=True)`, `dxf_version='R2000'` |
| `photo_v2` / `photo_refined` | `edge_to_dxf.py` `convert_enhanced()` / `convert(morph_close_kernel=0)` |
| `enhanced` | `extract_blueprint_enhanced()` → `EdgeToDXF.convert_enhanced()` |
| `restored_baseline` | Same extract as refined, `isolate_body=False` |
| `layered_dual_pass` | Dual-pass + layer builder (separate API services) |

Supporting files for Phase 3 modes:

| File | Role |
|------|------|
| `services/blueprint-import/vectorizer_phase3.py` | Phase 3 / V2_RAW / CAM R2000 engine. |
| `services/blueprint-import/dxf_compat.py` | DXF create/write used by Phase 3. |
| `services/blueprint-import/vectorizer_enhancements.py` | Optional Phase 3.7 import. |

`services/blueprint-import/vectorizer_phase2.py` is not on these two intakes.

---

## Not on either production intake

Left out of the zip on purpose:

- `extract_body_grid_v*.py`
- `cognitive_extractor.py`, `cognitive_extraction_engine.py`
- `calibration_integration.py` (calibration routes, not `BlueprintOrchestrator` default)
- `services/blueprint-import/phase4/`
- `packages/client/src/composables/useBlueprintWorkflow.ts` (dev workflow; not Hostinger MVP)

---

## Zip contents

`canonical_vectorizer_pipeline.zip` has the Path A + Path B files plus the three Phase 3 support files, with repo paths preserved.
