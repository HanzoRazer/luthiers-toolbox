docs/onboarding/DEV_ONBOARDING_CAM.md
(or anywhere you like). It’s written assuming you’ll keep your CAM docs under docs/cam/…, but you can tweak the relative paths if your layout is slightly different.

markdown
Copy code
# Luthier’s Tool Box — CAM Developer Onboarding Guide  
**Focus:** CAM Pipeline, DXF/Bridge workflows, Simulation, Job Intelligence  
**Last updated:** 2025-11-20

---

## 0. Who this guide is for

This guide is for developers joining the **CAM/CAD side** of Luthier’s Tool Box, specifically:

- CAM **pipeline** (`/cam/pipeline/run`)
- **Bridge DXF** workflows (BridgeLab, preflight, pin spacing sanity)
- **Simulation** + energy/review gate
- **Job Intelligence** (JobInt: logs, notes, favorites, presets)
- Supporting **labs**: BackplotGcode, AdaptiveBench, AdaptivePoly, HelicalRampLab, PipelineLab

Art Studio / dead legacy code is being handled separately and is **out of scope** for this guide.

---

## 1. Key documents (read these first)

These are the “source of truth” documents for the current CAM architecture:

- **ToolBox CAM Developer Handoff**  
  High-level architecture, critical issues, and CAM roadmap.  
  👉 [`docs/cam/TOOLBOX_CAM_DEVELOPER_HANDOFF.md`](../cam/TOOLBOX_CAM_DEVELOPER_HANDOFF.md)

- **N16–N18 Frontend Handoff (Adaptive / Backplot / Poly)**  
  Details about N16 (AdaptiveBench), N17–N18 (AdaptivePoly, polygon offset UI).  
  👉 [`docs/cam/N16_N18_FRONTEND_DEVELOPER_HANDOFF.md`](../cam/N16_N18_FRONTEND_DEVELOPER_HANDOFF.md)

- **Architectural Evolution**  
  Big-picture evolution: ArtStudioCAM, Labs, pipeline integration.  
  👉 [`docs/cam/ARCHITECTURAL_EVOLUTION.md`](../cam/ARCHITECTURAL_EVOLUTION.md)

- **JobInt Roadmap**  
  Everything about Job Intelligence: logs, sim issues, filters, notes, exports, favorites.  
  👉 [`docs/cam/jobint/JobInt_Roadmap.md`](../cam/jobint/JobInt_Roadmap.md)

> 🔧 If your repo paths differ, adjust these links but keep the filenames — they match the project’s internal naming.

---

## 2. Repository layout (CAM-relevant)

Below is the **logical layout** of the parts you’ll touch most as a CAM dev.

### 2.1 Backend (FastAPI)

```text
server/
  app/
    main.py                        # FastAPI app, router registration
    routers/
      cam_pipeline_router.py       # /cam/pipeline/run (DXF→Preflight→Adaptive→Post→Sim)
      cam_dxf_router.py            # DXF upload + preflight + bridge endpoints
      cam_adaptive_router.py       # /cam/pocket/adaptive/plan (adaptive kernel)
      cam_sim_router.py            # /cam/sim/* (simulation, reports)
      cam_jobint_router.py         # /cam/jobint/* (Job Intelligence API)
      cam_posts_router.py          # Post processors listing/config (GRBL, Haas, etc.)
      cam_machines_router.py       # Machine profiles (feeds, gates, limits)
    services/
      job_intel_store.py           # JSON-backed job store (JobInt)
      jobint_sim_issues_summary.py # Sim issues summaries & history
      dxf_preflight_bridge.py      # Bridge DXF preflight & pin checks
      dxf_to_adaptive.py           # DXF→adaptive request builder
      cam_pipeline_engine.py       # PipelineOp, PipelineRun orchestrator
      cam_sim_runner.py            # G-code simulation + energy/review gate
      cam_post_export.py           # roughing_gcode, biarc_gcode, etc. exporting
    data/
      posts/                       # Post processor defs (GRBL, LinuxCNC, Haas, MASSO...)
      machines/                    # Machine profiles
      job_intel/
        jobs.json                  # Job history (JobInt)
2.2 Frontend (Vue 3 + Vite)
text
Copy code
client/
  src/
    main.ts                        # Frontend entry
    router/
      index.ts                     # Routes: /lab/backplot, /lab/pipeline, etc.
    views/
      ArtStudioCAM.vue             # CAM dashboard tile (Backplot, Adaptive, Poly, Pipeline)
      BackplotLabView.vue          # Wraps BackplotGcode lab
      PipelineLabView.vue          # Wraps PipelineLab (pipeline runner)
      BridgeLabView.vue            # DXF/Bridge preflight + pipeline entry
    components/
      BackplotGcode.vue            # N15 – G-code backplot + stub sim
      AdaptiveKernelLab.vue        # N16 – AdaptiveBench Lab
      AdaptivePolyLab.vue          # N17–N18 – polygon offset lab
      CamPipelineRunner.vue        # PipelineLab UI: ops table, statuses, run controls
      CamBackplotViewer.vue        # Shared toolpath viewer (segments colored by severity)
      CamJobLogTable.vue           # JobInt run history table (filters, notes, favorites, tags)
      CamJobInsightsSummaryPanel.vue # JobInt summary (sparkline, best/worst runs)
      BridgePreflightPanel.vue     # Bridge DXF preflight UI
      BridgePipelinePanel.vue      # Bridge pipeline (DXF→Preflight→Adaptive→Post→Sim)
🧭 If you’re unsure where something lives, search by filename from the handoff docs; the names are consistent.

3. Environment setup (backend + frontend)
3.1 Prereqs
Python 3.11+

Node.js 18+ (LTS)

npm or pnpm

Git, VS Code recommended

3.2 Backend setup
From repo root:

bash
Copy code
cd server
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -U pip
pip install -r requirements.txt   # or `uv pip install ...` / `poetry install` depending on your setup
Run the API:

bash
Copy code
uvicorn app.main:app --reload --port 8000
Visit Swagger:

👉 http://localhost:8000/docs
Look for:

/cam/pipeline/run

/cam/pocket/adaptive/plan

/cam/bridge/*

/cam/sim/*

/cam/jobint/*

3.3 Frontend setup
From repo root:

bash
Copy code
cd client
npm install
npm run dev
Default dev URL:

👉 http://localhost:5173

Primary CAM UIs:

/lab/backplot – BackplotGcode lab (N15)

/lab/adaptive – AdaptiveKernelLab (N16)

/lab/poly – AdaptivePolyLab (N17–N18)

/lab/pipeline – PipelineLab

/lab/bridge – BridgeLab

4. Critical flows you must understand
4.1 DXF → Bridge preflight → pipeline
Backend pieces:

app/routers/cam_dxf_router.py

app/services/dxf_preflight_bridge.py

app/routers/cam_pipeline_router.py

app/services/dxf_to_adaptive.py

Frontend pieces:

client/src/views/BridgeLabView.vue

client/src/components/BridgePreflightPanel.vue

client/src/components/BridgePipelinePanel.vue

Flow:

Upload bridge DXF in BridgeLab.

Preflight runs /cam/bridge/preflight:

Checks pin spacing, geometry, units.

If ok === false, pipeline gate fails:

PipelineLab shows “Needs fix”, and we don’t export DXF or generate CAM.

If ok === true, pipeline continues:

DXF → dxf_to_adaptive_request → /cam/pocket/adaptive/plan → post export → /cam/sim/run (or similar).

Sim result includes issues (review_gate_exceeded, travel_too_long) which feed into Backplot + JobInt.

4.2 Adaptive kernel (N16) and AdaptivePoly (N17–N18)
Docs:

docs/cam/N16_N18_FRONTEND_DEVELOPER_HANDOFF.md

Key backend:

app/routers/cam_adaptive_router.py

app/services/dxf_to_adaptive.py

Key frontend:

client/src/components/AdaptiveKernelLab.vue

client/src/components/AdaptivePolyLab.vue

Flow:

Adaptive Lab:

Accepts loops (loops: [{ pts: [[x, y], …] }]).

Sends to /cam/pocket/adaptive/plan.

Displays toolpath + stats + overlays.

Can “Send to PipelineLab”.

DXF → Adaptive:

dxf_to_adaptive_request(dxf_path, tool_d, …) builds PlanIn structure from DXF GEOMETRY layer.

4.3 Backplot G-code (N15) and sim
Key frontend:

client/src/components/BackplotGcode.vue

client/src/components/CamBackplotViewer.vue

Key backend:

app/routers/cam_sim_router.py

app/services/cam_sim_runner.py

Flow:

Paste or load G-code in BackplotLab.

BackplotGcode parses it and:

Sends to sim (/cam/sim/…) or a stub.

Renders XY(Z) path with segments colored by sim issues.

You can save G-code as temp (/cam/gcode/save_temp) and reference gcode_key in PipelineLab to run a full pipeline sim without DXF.

4.4 Job Intelligence (JobInt)
Docs:

docs/cam/jobint/JobInt_Roadmap.md

Backend:

app/services/job_intel_store.py

app/services/jobint_sim_issues_summary.py

app/routers/cam_jobint_router.py

Frontend:

client/src/components/CamJobLogTable.vue

client/src/components/CamJobInsightsSummaryPanel.vue

What JobInt provides:

JSON store: data/job_intel/jobs.json

Each pipeline run -> a job record with:

machine, post, material

sim issues

review % / energy (where available)

notes, tags, favorite

UI:

Quick filters (severity, machine/material tokens).

Favorites + tags.

Export filtered jobs (CSV/Markdown).

Inline notes editor.

Sparks + severity chips + history charts.

5. Typical dev workflows
5.1 Adding a new pipeline step
Define the op in cam_pipeline_engine.py:

Add an enum / string op name.

Implement handler (e.g. _run_export_post, _run_simulate_gcode).

Expose it in the router (cam_pipeline_router.py):

Update op graph building.

Ensure errors are wrapped in PipelineOpResult.

Surface in PipelineLab UI (CamPipelineRunner.vue):

Add row label, status, payload view (JSON).

Update JobInt if needed:

If op affects sim or output quality, log stats/issues.

5.2 Extending preflight rules
Modify dxf_preflight_bridge.py:

Add pin spacing, slot length, body/bridge region checks.

Ensure preflight response is typed and unit-aware:

issues: [{ code, severity, message, location }].

Reflect new issues in:

BridgePreflightPanel display.

BridgePipeline gate logic (if severity == 'error' → block pipeline).

5.3 Adding a new post processor
Add a JSON/YAML definition under data/posts/.

Register post in cam_posts_router.py and cam_post_export.py.

Update Post Manager UI (if present) to list the new post.

Add a small smoke test for /cam/roughing_gcode or relevant routes with that post name.

6. Tests and smoke checks
6.1 Backend tests
Typical (adjust to your tooling):

bash
Copy code
cd server
pytest
Look specifically for:

Test suites around:

cam_pipeline_router

cam_sim_runner

job_intel_store

dxf_preflight_bridge

You may also have small smoke scripts under scripts/:

bash
Copy code
python scripts/smoke_cam_pipeline.py
python scripts/smoke_jobint_summary.py
6.2 Frontend checks
Run dev server:

bash
Copy code
cd client
npm run dev
Quick manual smoke:

/lab/bridge: Upload known-good bridge DXF, confirm:

Preflight passes.

Gate shows green.

Pipeline runs through all ops.

/lab/backplot: Paste a small canned G-code and confirm path rendering.

/lab/pipeline: Run a pipeline from DXF or gcode_key, confirm:

Status chips update.

Simulation issues show.

Job appears in Job log.

7. First tasks for a new CAM dev
If you’re brand new to this codebase, a good first 3 tasks:

Run a bridge pipeline end-to-end

Use a sample DXF.

Confirm preflight → adaptive → post → sim works.

Find the resulting job in JobInt.

Add a new JobInt quick filter

E.g. a new token #rosewood.

Make sure it filters by material name or tag.

Fix or extend one preflight rule

Example: tighten pin spacing rule and update error messaging.

Ensure PipelineLab shows the updated issue clearly.

These will force you to touch backend, frontend, and JobInt in a small, safe way.