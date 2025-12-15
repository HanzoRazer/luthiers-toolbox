# B20 – CNC Preset Manager & JobInt Artifacts

Date: 2025-11-23  \\
Status: ✅ Landed

## Scope
- Extend JobInt JSONL log schema with optional artifacts (geometry loops, plan
  payload, moves/moves_path, baseline lineage) and companion helper
  `extract_jobint_artifacts()`.
- Introduce JSON-backed CNC preset store at `data/presets/presets.json` with
  CRUD API exposed at `/api/cnc/presets/*`.
- Surface presets inside the CAM Production hub via the new
  `PresetManagerPanel.vue`, including tooltip lineage, Compare Lab jump, and
  Adaptive Lab bridge via `preset_id` query parameter (redirect preserves
  query strings now).

## Backend Highlights
- `services/api/app/services/job_int_log.py` now accepts
  `geometry_loops`/`plan_request`/`moves`/`moves_path`/`baseline_id` along with
  optional tags/favorite/notes. Older entries remain valid (fields are optional).
- `services/api/app/services/jobint_artifacts.py` centralizes artifact
  extraction so pipeline/adaptive routers can forward context without duplicate
  heuristics.
- `services/api/app/services/preset_store.py` handles persistence with
  human-readable JSON and resilient load/save helpers.
- `services/api/app/routers/cnc_production/presets_router.py` delivers
  GET/POST/PATCH/DELETE endpoints for CNC presets and is registered under
  `/api/cnc/presets`.

## Frontend Highlights
- `client/src/cnc_production/PresetManagerPanel.vue` lists presets, shows lineage
  tooltips, deletes entries, and links into Compare Lab or Adaptive Lab.
- `client/src/views/CamProductionView.vue` mounts the panel inside the Pipeline
  tab so operators can manage presets even while Pipeline Lab remains disabled.
- Router redirect from `/lab/adaptive` now preserves query strings, allowing the
  Preset Manager to pass `preset_id` into Adaptive Lab (and future CompareLab
  hooks reuse the same mechanism).

## Smoke Test
1. Start FastAPI locally (`uvicorn app.main:app --reload --port 8000`).
2. `Invoke-RestMethod -Method Get http://localhost:8000/api/cnc/presets` → returns `[]` on first run.
3. `Invoke-RestMethod -Method Post` with payload `{ "name": "Preset A" }` → entry stored under `data/presets/presets.json`.
4. Visit `/cam` in the client dev server; the Preset Manager lists "Preset A" and
   lineage tooltip renders fields.
5. Use "Compare…" (disabled without baseline) and "Open in Adaptive Lab" to
   confirm navigation keeps the query string (check URL `/cam?preset_id=...`).
6. Click Delete → preset removed via DELETE API and panel refreshes automatically.

This completes the B20 prerequisites for CompareRunsPanel (B21).
