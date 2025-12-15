🎨 ART STUDIO — DEVELOPMENT ROADMAP
A unified roadmap for Rosette, Adaptive, Relief, and Pipeline integration
Last updated: 2025-11-20

✅ Overview
Art Studio is no longer an isolated sandbox. It is now a first-class subsystem inside Luthier’s ToolBox, with:


Rosette Designer


Rosette Compare Mode


Risk Timeline & Analytics


PipelineLab + AdaptiveLab integration


Deep-link workflow


CI-verified backend endpoints


A foundation for Relief & Adaptive kernels


A roadmap for cross-lab preset analytics


This file tracks what has been completed and what remains, using a clear checkbox structure.

✔️ 1. DELIVERED PHASES
Below is every major piece already completed, organized by subsystem.

1.1 Rosette Lane — MVP
✔ Rosette Preview Engine


File: services/api/app/routers/art_studio_rosette_router.py


Vue: ArtStudioRosette.vue


Features:


pattern_type, segments, inner/outer radius


Full SVG rendering


Accurate bounding-box computation




✔ Rosette Job Save / Load


Endpoint: /api/art/rosette/save


Endpoint: /api/art/rosette/jobs


Persisted via SQLite / file-store



1.2 Rosette Compare Mode
✔ Compare two saved rosette jobs


Endpoint: /api/art/rosette/compare


Outputs:


pattern types


segments & deltas


radii & deltas


units matching


bbox union




✔ Dual Canvas Render (A ↔ B)


Vue: ArtStudioRosetteCompare.vue



1.3 Snapshot → Risk Pipeline
✔ Save snapshot to risk timeline


Endpoint: /api/art/rosette/compare/snapshot


✔ Risk scoring


Integrated scoring model


Saved to rosette_compare_risk table


✔ History Panel


Shows last N snapshots


Each row contains timestamp / delta summary / risk score



1.4 CSV Export + History Analytics
✔ CSV Export


Endpoint: /api/art/rosette/compare/export_csv


File: services/api/app/routers/art_studio_rosette_router.py


✔ Sparkline rendering


Inline SVG polylines


Used in:


Flat history view


Preset groups


Scorecards




✔ Global Risk Metrics Bar


L / M / H counts


Average risk (visibleHistory)



1.5 Preset Analytics
✔ Compare-by-Preset Mode (27.4)


Group snapshots by presetA → presetB


Compute average risk per preset-pair


Render group sparkline


✔ Preset Scorecards (27.6)


Per-preset boxes (Safe, Aggressive…)


L/M/H counts


Avg risk


Per-preset sparkline


Horizontal scroll panel


✔ Scorecard Interactivity (27.7)


Click → Filter history to that preset


Scorecard buttons:


Pipeline


Adaptive




Deep links:


/lab/pipeline?lane=rosette&preset=Safe


/lab/adaptive?lane=rosette&preset=Safe





1.6 PipelineLab & AdaptiveLab Integration
✔ Query Param Preset Consumption


Auto-fill preset based on query


Detect lane=rosette context


✔ Auto-select Most Recent Job for Preset


After job list loads


Select latest job whose metadata.preset matches query


✔ Return to Rosette History Banner


Banner:

“Preset loaded from Rosette: Safe (from job XYZ)”



Link to:
/art/rosette/compare?lane=rosette&preset=Safe



1.7 Repo & CI Infrastructure
✔ Reinstall Helper


New venv


Install from requirements.lock


Validate imports (Shapely, Pyclipper, ezdxf)


✔ API Health + Smoke Test


Boot uvicorn temp server


Hit:


/api/cam_vcarve/preview_infill


/api/cam/pocket/adaptive/plan




✔ CI Integration


Nightly health


Artifacts uploaded


Ready for Slack/email alerts



🟦 2. PLANNED BUNDLES (Not Yet Delivered)
These are the official future tasks to complete the Art Studio vision.

2.1 Rosette → CAM Production Bridge
○ Phase: Rosette CAM Bridge
Files:


art_studio_rosette_router.py


cam_vcarve_router.py


RosetteToCAMBridge.vue


Features:


Feed rosette geometry into V-carve engine


Centerline → v-bit → flat-clear passes


Export G-code via post-preset system


Makes the Rosette lane production ready



2.2 Job Detail View (Cross-Lab)
○ Phase: UnifiedJobDetail.vue


Inspect job: geometry, G-code, diff, risk


Linked from Rosette compare history


Linked from Pipeline/Adaptive jobs too


This brings “git diff for toolpaths”



2.3 Adaptive Kernel Real Implementation
○ Phase: AdaptiveKernel v2
Files:


cam_pocket_adaptive_router.py


AdaptiveKernelLab.vue


Features:


Spiral + lanes strategies


Curvature-aware stepover (Module L.2)


Trochoidal loops (L.3)


Jerk-aware timing


Risk overlays: tight corners, overload zones


Reason:
This becomes the core pocketing engine for guitar bodies, neck pockets, cavities.

2.4 Relief Kernel Real Implementation
○ Phase: ReliefKernelCore
Files:


art_studio_relief_router.py


ReliefKernelLab.vue


Features:


Heightmap → toolpaths


Raster zig-zag + contour passes


Scallop control


Thin floor detection


Z-aware load analytics


Risk snapshots fully integrated


Reason:
This is the missing lane to complete your Relief Carving Suite.

2.5 Cross-Lab Preset Risk Dashboard
○ Phase: PresetRiskDashboard.vue
Backend:


/api/risk/aggregate_by_preset


/api/risk/aggregate_pair


/api/risk/drift


Features:


Compare Safe vs Aggressive vs Custom across labs


Sparklines per lane


L/M/H distribution per lane


Drift badges


Deep links to labs with query params


Reason:
Creates the mission control for the entire CAM ecosystem.

2.6 Blueprint → DXF → Art Studio → Pipeline Integration
○ Phase: BlueprintChainBridge
Files:


blueprint_router.py


BlueprintToArtStudio.vue


BlueprintToPipeline.vue


Features:


Blueprint analyze → vectorize → DXF


DXF → Rosette (inlay)


DXF → Adaptive pocket


DXF → Relief carving


Unified “send to” actions for all lanes


Reason:
Gets you from photo/scan → geometry → toolpath in one pipeline.

2.7 Multi-Lane Job Compare Mode
○ Phase: GlobalCompare.vue


Compare multiple jobs:


Rosette


Adaptive


Relief


Full pipeline




Unified diff viewer (geometry + G-code)


Multi-lane risk overlays



🟩 3. Recommended Next Steps
To maintain velocity, the recommended next 3 bundles are:
#1 – Rosette → CAM Bridge
Turn rosette design into CNC-ready G-code.
#2 – Unified Job Detail View
Makes Rosette history actionable; adds real job introspection.
#3 – AdaptiveKernel v2
Gives you a true pocketing engine — the most important CAM upgrade.

🗂 File Map (Where Things Live)
Backend (FastAPI)
services/
  api/
    app/
      routers/
        art_studio_rosette_router.py
        art_studio_relief_router.py   (stub)
        cam_pocket_adaptive_router.py (stub)
        cam_vcarve_router.py
        cam_sim_router.py
        ...
      services/
      models/
      db/

Frontend (Vue)
packages/
  client/
    src/
      views/
        ArtStudioRosette.vue
        ArtStudioRosetteCompare.vue
        AdaptiveKernelLab.vue
        PipelineLab.vue
        ReliefKernelLab.vue         (planned)
        ...
      components/
      utils/

Tests
services/api/tests/
  test_rosette_compare.py
  test_rosette_csv_export.py
  test_pipeline_smoke.py
  ...


🏁 Summary
Art Studio is no longer a side project — it’s now a core part of the Luthier’s ToolBox ecosystem.


Rosette lane: 95% complete


Pipeline & Adaptive integration: live and linked


Risk analytics backbone: fully operational


CI: supporting the system


Next major milestone: CAM toolpath generation from Art Studio designs



